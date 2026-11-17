#!/usr/bin/env python3
"""
processar_midia.py — prepara e transcreve um áudio ou vídeo em uma única chamada.

Etapas: baixa o link (se for URL) → extrai o áudio mono 16 kHz → transcreve em
blocos com faster-whisper (ou openai-whisper), mantendo os tempos do original →
grava a transcrição com timestamps [MM:SS].

O trabalho fica em cache em <WORKSPACE_DIR>/midias/trabalho/<id>/: se o tempo
acabar no meio, rodar de novo com os mesmos argumentos continua do bloco onde
parou, e um novo resumo da mesma mídia não precisa transcrever outra vez.

Uso:
    python processar_midia.py <arquivo-ou-URL> [--modelo small] [--idioma pt]
                              [--bloco-min 10] [--tempo-max-min N]
                              [--filtro-silencio] [--refazer]

Caminhos relativos são procurados no diretório atual e depois em WORKSPACE_DIR.

Saída: transcricao.txt e info.json no diretório atual + resumo JSON no stdout.

Códigos de saída:
    0  transcrição completa
    2  dependência ausente (ffmpeg/ffprobe/Whisper/yt-dlp)
    3  entrada não encontrada, download falhou ou mídia ilegível
    4  nenhuma fala detectada (ou mídia sem faixa de áudio)
    5  argumento inválido
    6  transcrição PARCIAL: o tempo acabou; rode de novo com os mesmos argumentos
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

INICIO = time.monotonic()
# Avisos do huggingface_hub (symlinks no Windows, requisições sem token) só poluem o log.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HUB_DISABLE_IMPLICIT_TOKEN", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
import warnings  # noqa: E402

warnings.filterwarnings("ignore", module="huggingface_hub")
EXT_MIDIA = {".mp3", ".wav", ".m4a", ".ogg", ".oga", ".opus", ".flac", ".aac", ".wma",
             ".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".ts", ".m4v", ".3gp"}


def log(msg: str) -> None:
    print(f"[processar_midia] {msg}", file=sys.stderr, flush=True)


def sair(codigo: int, msg: str) -> int:
    log(msg)
    print(json.dumps({"status": "erro", "codigo": codigo, "mensagem": msg}, ensure_ascii=False))
    return codigo


def rodar(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def fmt(seg: float) -> str:
    seg = int(seg)
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


# --------------------------------------------------------------------------
# entrada
# --------------------------------------------------------------------------

def workspace() -> Path:
    w = os.environ.get("WORKSPACE_DIR")
    return Path(w) if w else Path.cwd()


def resolver_arquivo(caminho: str) -> Path | None:
    p = Path(caminho)
    if p.is_absolute():
        return p if p.is_file() else None
    for base in (Path.cwd(), workspace()):
        if (base / p).is_file():
            return base / p
    return None


def baixar(url: str, pasta: Path) -> tuple[Path, str | None]:
    try:
        import yt_dlp  # type: ignore
    except ImportError:
        raise RuntimeError("yt-dlp não instalado (pip install yt-dlp)")
    existentes = [p for p in pasta.glob("origem.*") if p.suffix != ".part"]
    if existentes:
        meta = pasta / "titulo.txt"
        return existentes[0], meta.read_text(encoding="utf-8") if meta.exists() else None
    opts = {"quiet": True, "no_warnings": True, "format": "bestaudio/best", "noplaylist": True,
            "outtmpl": str(pasta / "origem.%(ext)s")}
    log(f"baixando {url}")
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    titulo = (info or {}).get("title")
    if titulo:
        (pasta / "titulo.txt").write_text(titulo, encoding="utf-8")
    arquivos = [p for p in pasta.glob("origem.*") if p.suffix != ".part"]
    if not arquivos:
        raise RuntimeError("o download não produziu nenhum arquivo")
    return arquivos[0], titulo


# --------------------------------------------------------------------------
# áudio
# --------------------------------------------------------------------------

def duracao(arquivo: Path) -> float:
    r = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(arquivo)])
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def tem_audio(arquivo: Path) -> bool:
    r = rodar(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
               "-of", "csv=p=0", str(arquivo)])
    return bool(r.stdout.strip())


def extrair_audio(origem: Path, destino: Path, filtro_silencio: bool) -> None:
    filtros = ["highpass=f=80", "dynaudnorm=f=250:g=15"]
    if filtro_silencio:
        # Atenção: remove silêncios do meio e DESLOCA os timestamps em relação ao original.
        filtros.append("silenceremove=start_periods=1:start_duration=1:start_threshold=-45dB:"
                       "stop_periods=-1:stop_duration=2:stop_threshold=-45dB")
    tmp = destino.with_suffix(".tmp.wav")
    r = rodar(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(origem),
               "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-af", ",".join(filtros), str(tmp)])
    if r.returncode != 0 or not tmp.exists():
        raise RuntimeError(f"ffmpeg falhou: {r.stderr.strip()[-400:]}")
    tmp.replace(destino)


def cortar_bloco(audio: Path, inicio: float, dur: float, destino: Path) -> None:
    r = rodar(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{inicio:.2f}", "-t", f"{dur:.2f}",
               "-i", str(audio), "-c", "copy", str(destino)])
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg falhou ao cortar bloco: {r.stderr.strip()[-300:]}")


# --------------------------------------------------------------------------
# transcrição
# --------------------------------------------------------------------------

class Motor:
    def __init__(self, modelo: str, idioma: str | None):
        self.modelo, self.idioma = modelo, idioma
        self.nome = ""
        self._m = None

    def carregar(self) -> None:
        if self._m is not None:
            return
        try:
            from faster_whisper import WhisperModel  # type: ignore
            log(f"carregando faster-whisper '{self.modelo}' (CPU/int8; o 1º uso baixa o modelo)")
            self._m = WhisperModel(self.modelo, device="cpu", compute_type="int8")
            self.nome = "faster-whisper"
            return
        except ImportError:
            pass
        try:
            import whisper  # type: ignore
            log(f"faster-whisper ausente; usando openai-whisper '{self.modelo}'")
            self._m = whisper.load_model(self.modelo)
            self.nome = "openai-whisper"
        except ImportError:
            raise RuntimeError("nenhum motor Whisper instalado (pip install faster-whisper)")

    def transcrever(self, audio: Path, offset: float) -> tuple[list[dict], str | None]:
        self.carregar()
        saida: list[dict] = []
        if self.nome == "faster-whisper":
            segs, info = self._m.transcribe(str(audio), language=self.idioma, vad_filter=True,
                                            condition_on_previous_text=False, beam_size=5)
            for s in segs:
                if getattr(s, "no_speech_prob", 0.0) > 0.6:
                    continue
                saida.append({"inicio": round(s.start + offset, 2), "fim": round(s.end + offset, 2),
                              "texto": s.text.strip()})
            return saida, getattr(info, "language", self.idioma)
        r = self._m.transcribe(str(audio), language=self.idioma, condition_on_previous_text=False)
        for s in r.get("segments", []):
            if s.get("no_speech_prob", 0.0) > 0.6:
                continue
            saida.append({"inicio": round(s["start"] + offset, 2), "fim": round(s["end"] + offset, 2),
                          "texto": s["text"].strip()})
        return saida, r.get("language", self.idioma)


def limpar_repeticoes(segmentos: list[dict]) -> list[dict]:
    """Remove alucinações típicas: a mesma frase repetida em sequência."""
    saida: list[dict] = []
    repeticoes = 0
    for s in segmentos:
        if not s["texto"]:
            continue
        if saida and s["texto"].lower() == saida[-1]["texto"].lower():
            repeticoes += 1
            if repeticoes >= 1:
                continue
        else:
            repeticoes = 0
        saida.append(s)
    return saida


# --------------------------------------------------------------------------
# principal
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Prepara e transcreve áudio/vídeo.")
    ap.add_argument("entrada", help="arquivo local (relativo ao workspace) ou URL")
    ap.add_argument("--modelo", default=os.environ.get("MIDIA_WHISPER_MODEL", "small"),
                    choices=["tiny", "base", "small", "medium", "large-v3"])
    ap.add_argument("--idioma", default="pt", help='código do idioma ou "auto"')
    ap.add_argument("--bloco-min", type=float, default=10.0)
    ap.add_argument("--tempo-max-min", type=float, default=None,
                    help="tempo máximo desta execução (padrão: limite da ferramenta menos 3 min)")
    ap.add_argument("--filtro-silencio", action="store_true",
                    help="remove silêncios longos (desloca os timestamps; use só se houver alucinações)")
    ap.add_argument("--refazer", action="store_true", help="ignora o cache e transcreve do zero")
    args = ap.parse_args()

    if args.bloco_min <= 0:
        return sair(5, "--bloco-min precisa ser maior que zero")
    for binario in ("ffmpeg", "ffprobe"):
        if not shutil.which(binario):
            return sair(2, f"'{binario}' não encontrado no PATH")

    if args.tempo_max_min is not None:
        limite_s = args.tempo_max_min * 60
    else:
        try:
            limite_s = int(os.environ.get("SKILL_SCRIPT_TIMEOUT_MS", "900000")) / 1000 - 180
        except ValueError:
            limite_s = 720
        limite_s = max(limite_s, 60)

    eh_url = args.entrada.startswith(("http://", "https://"))
    if eh_url:
        chave = args.entrada.strip()
    else:
        arquivo = resolver_arquivo(args.entrada)
        if not arquivo:
            return sair(3, f"arquivo não encontrado: {args.entrada}")
        if arquivo.suffix.lower() not in EXT_MIDIA:
            log(f"extensão {arquivo.suffix} incomum; tentando mesmo assim")
        chave = f"{arquivo.resolve()}|{arquivo.stat().st_size}"

    ident = hashlib.sha1(f"{chave}|{args.modelo}|{args.idioma}|{args.filtro_silencio}".encode()).hexdigest()[:12]
    pasta = workspace() / "midias" / "trabalho" / ident
    if args.refazer and pasta.exists():
        shutil.rmtree(pasta, ignore_errors=True)
    pasta.mkdir(parents=True, exist_ok=True)
    estado_path = pasta / "estado.json"
    estado = json.loads(estado_path.read_text(encoding="utf-8")) if estado_path.exists() else {}

    # 1. origem
    titulo = None
    try:
        if eh_url:
            origem, titulo = baixar(args.entrada, pasta)
        else:
            origem = arquivo
    except Exception as exc:  # noqa: BLE001
        return sair(3, f"falha ao obter a mídia: {exc}")

    # 2. áudio
    audio = pasta / "audio.wav"
    if not audio.exists():
        if not tem_audio(origem):
            return sair(4, "a mídia não tem faixa de áudio")
        log("extraindo áudio mono 16 kHz")
        try:
            extrair_audio(origem, audio, args.filtro_silencio)
        except Exception as exc:  # noqa: BLE001
            return sair(3, str(exc))
    dur = duracao(audio)
    if dur <= 0.5:
        return sair(4, "áudio vazio ou ilegível")
    bloco_s = args.bloco_min * 60
    total_blocos = max(1, math.ceil(dur / bloco_s))
    estado.update({"origem": args.entrada, "titulo": titulo, "duracao_s": round(dur, 2),
                   "duracao_original_s": round(duracao(origem), 2), "blocos_total": total_blocos,
                   "modelo": args.modelo, "idioma_pedido": args.idioma,
                   "filtro_silencio": args.filtro_silencio})

    # 3. transcrição em blocos
    motor = Motor(args.modelo, None if args.idioma in ("", "auto") else args.idioma)
    feitos = sorted(int(p.stem.split("_")[1]) for p in pasta.glob("bloco_*.json"))
    razao = estado.get("segundos_por_segundo_audio")  # custo medido de transcrição
    parcial = False
    for i in range(total_blocos):
        if i in feitos:
            continue
        inicio = i * bloco_s
        tam = min(bloco_s, dur - inicio)
        decorrido = time.monotonic() - INICIO
        estimativa = (razao or 1.0) * tam + (30 if motor._m is None else 0)
        if feitos and decorrido + estimativa > limite_s:
            parcial = True
            break
        log(f"transcrevendo bloco {i + 1}/{total_blocos} ({fmt(inicio)} a {fmt(inicio + tam)})")
        trecho = pasta / f"trecho_{i:03d}.wav"
        t0 = time.monotonic()
        try:
            if total_blocos == 1:
                segs, idioma_det = motor.transcrever(audio, 0.0)
            else:
                cortar_bloco(audio, inicio, tam, trecho)
                segs, idioma_det = motor.transcrever(trecho, inicio)
        except RuntimeError as exc:
            return sair(2, str(exc))
        except Exception as exc:  # noqa: BLE001
            return sair(3, f"falha na transcrição do bloco {i + 1}: {exc}")
        finally:
            trecho.unlink(missing_ok=True)
        gasto = time.monotonic() - t0
        razao = gasto / max(tam, 1.0)
        estado.update({"segundos_por_segundo_audio": round(razao, 3), "motor": motor.nome,
                       "idioma_detectado": idioma_det})
        (pasta / f"bloco_{i:03d}.json").write_text(json.dumps(segs, ensure_ascii=False), encoding="utf-8")
        feitos.append(i)
        estado_path.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

    estado["blocos_concluidos"] = len(feitos)
    estado_path.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. montagem
    segmentos: list[dict] = []
    for i in sorted(feitos):
        segmentos += json.loads((pasta / f"bloco_{i:03d}.json").read_text(encoding="utf-8"))
    segmentos = limpar_repeticoes(segmentos)
    ate = min(len(feitos) * bloco_s, dur)

    cabecalho = [
        f"# Transcrição — {titulo or Path(args.entrada).name}",
        f"# Origem: {args.entrada}",
        f"# Duração: {fmt(estado['duracao_original_s'] or dur)} | Motor: {estado.get('motor', '?')} "
        f"({args.modelo}) | Idioma: {estado.get('idioma_detectado') or args.idioma}",
    ]
    if args.filtro_silencio:
        cabecalho.append("# AVISO: filtro de silêncio ativo; os timestamps não batem com o original")
    if parcial:
        cabecalho.append(f"# PARCIAL: transcrito até {fmt(ate)} de {fmt(dur)}")
    linhas = [f"[{fmt(s['inicio'])}] {s['texto']}" for s in segmentos]
    texto = "\n".join(cabecalho) + "\n\n" + "\n".join(linhas) + "\n"
    (pasta / "transcricao.txt").write_text(texto, encoding="utf-8")
    Path("transcricao.txt").write_text(texto, encoding="utf-8")

    resumo = {
        "status": "parcial" if parcial else "completo",
        "titulo": titulo,
        "duracao": fmt(estado["duracao_original_s"] or dur),
        "transcrito_ate": fmt(ate),
        "blocos": f"{len(feitos)}/{total_blocos}",
        "motor": estado.get("motor"),
        "modelo": args.modelo,
        "idioma": estado.get("idioma_detectado") or args.idioma,
        "segmentos": len(segmentos),
        "cache": str(pasta.relative_to(workspace())).replace("\\", "/") if pasta.is_relative_to(workspace()) else str(pasta),
    }
    if parcial:
        resumo["proximo_passo"] = "Rode de novo com os MESMOS argumentos para continuar de onde parou."
    Path("info.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))

    if not segmentos and not parcial:
        return sair(4, "nenhuma fala detectada na mídia")
    return 6 if parcial else 0


if __name__ == "__main__":
    sys.exit(main())
