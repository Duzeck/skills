#!/usr/bin/env python3
"""
resumir_video.py — extrai a transcrição de um vídeo do YouTube.

Estratégia, em ordem:
  1. Legenda oficial (manual) via yt-dlp
  2. Legenda automática via yt-dlp
  3. Transcrição local com faster-whisper / openai-whisper sobre o áudio
  4. Gemini (se GEMINI_API_KEY estiver no ambiente)

Uso:
    python resumir_video.py "<URL>" [--idioma pt,en] [--saida transcricao.txt]
                                  [--modelo-whisper small] [--sem-whisper]
                                  [--sem-gemini] [--metadados metadados.json]

Códigos de saída:
    0  sucesso
    2  dependências ausentes e instalação automática falhou
    3  vídeo inacessível (privado, removido, restrito, ao vivo)
    4  nenhuma transcrição obtida
    5  erro de argumento / URL inválida
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

URL_RE = re.compile(
    r"^(https?://)?(www\.|m\.)?"
    r"(youtube\.com/(watch\?|shorts/|live/|embed/)|youtu\.be/)",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# utilidades
# --------------------------------------------------------------------------

def log(msg: str) -> None:
    print(f"[resumir_video] {msg}", file=sys.stderr)


def rodar(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log("executando: " + " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def pip_instalar(*pacotes: str) -> bool:
    """Tenta instalar pacotes Python. Retorna True se conseguiu."""
    for args in (["--user"], []):
        try:
            r = rodar([sys.executable, "-m", "pip", "install", *args, *pacotes])
            if r.returncode == 0:
                return True
        except Exception as exc:  # noqa: BLE001
            log(f"pip falhou: {exc}")
    return False


def garantir_ytdlp() -> bool:
    try:
        import yt_dlp  # noqa: F401
        return True
    except ImportError:
        log("yt-dlp ausente; tentando instalar")
        if pip_instalar("yt-dlp") :
            try:
                import yt_dlp  # noqa: F401
                return True
            except ImportError:
                return False
        return False


def garantir_ffmpeg() -> bool:
    if shutil.which("ffmpeg"):
        return True
    log("ffmpeg ausente; tentando instalar pelo gerenciador do sistema")
    gerenciadores = [
        (["apt-get", "install", "-y", "ffmpeg"], "sudo"),
        (["dnf", "install", "-y", "ffmpeg"], "sudo"),
        (["apk", "add", "ffmpeg"], "sudo"),
        (["brew", "install", "ffmpeg"], None),
        (["winget", "install", "-e", "--id", "Gyan.FFmpeg"], None),
        (["choco", "install", "-y", "ffmpeg"], None),
    ]
    for cmd, elevador in gerenciadores:
        if not shutil.which(cmd[0]):
            continue
        completo = ([elevador] if elevador else []) + cmd
        try:
            if rodar(completo).returncode == 0 and shutil.which("ffmpeg"):
                return True
        except Exception:  # noqa: BLE001
            continue
    return shutil.which("ffmpeg") is not None


# --------------------------------------------------------------------------
# metadados e legendas
# --------------------------------------------------------------------------

def obter_info(url: str) -> dict:
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def metadados_basicos(info: dict) -> dict:
    return {
        "titulo": info.get("title"),
        "canal": info.get("uploader") or info.get("channel"),
        "publicado_em": info.get("upload_date"),
        "duracao_segundos": info.get("duration"),
        "link": info.get("webpage_url"),
        "idioma_original": info.get("language"),
        "ao_vivo": bool(info.get("is_live")),
        "legendas_manuais": sorted((info.get("subtitles") or {}).keys()),
        "legendas_automaticas": sorted((info.get("automatic_captions") or {}).keys()),
    }


def _vtt_para_texto(caminho: Path) -> str:
    """Converte WebVTT em texto com timestamps no formato [MM:SS]."""
    linhas: list[str] = []
    ultimo = ""
    for bruto in caminho.read_text(encoding="utf-8", errors="replace").splitlines():
        linha = bruto.strip()
        if not linha or linha.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")):
            continue
        m = re.match(r"^(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->", linha)
        if m:
            h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
            total = h * 3600 + mi * 60 + s
            marca = f"[{total // 60:02d}:{total % 60:02d}]"
            continue
        if re.match(r"^\d+$", linha):
            continue
        texto = re.sub(r"<[^>]+>", "", linha)
        if texto and texto != ultimo:
            linhas.append(f"{marca} {texto}")
            ultimo = texto
    return "\n".join(linhas)


def baixar_legenda(url: str, idiomas: list[str], tmp: Path) -> tuple[str, str] | None:
    """Baixa a melhor legenda disponível. Retorna (texto, origem)."""
    import yt_dlp

    info = obter_info(url)
    manuais = info.get("subtitles") or {}
    automaticas = info.get("automatic_captions") or {}

    def escolher(disponiveis: dict) -> str | None:
        for idioma in idiomas:
            for chave in disponiveis:
                if chave == idioma or chave.startswith(idioma + "-") or chave.startswith(idioma + "_"):
                    return chave
        for chave in disponiveis:
            if chave.startswith("pt") or chave.startswith("en"):
                return chave
        return next(iter(disponiveis), None)

    for fonte, rotulo in ((manuais, "legenda oficial"), (automaticas, "legenda automática")):
        if not fonte:
            continue
        idioma = escolher(fonte)
        if not idioma:
            continue
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": fonte is manuais,
            "writeautomaticsub": fonte is automaticas,
            "subtitleslangs": [idioma],
            "subtitlesformat": "vtt",
            "outtmpl": str(tmp / "legenda.%(ext)s"),
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
        except Exception as exc:  # noqa: BLE001
            log(f"falha ao baixar {rotulo}: {exc}")
            continue
        arquivos = list(tmp.glob("legenda*.vtt"))
        if arquivos:
            texto = _vtt_para_texto(arquivos[0])
            if texto.strip():
                return texto, f"{rotulo} ({idioma})"
    return None


# --------------------------------------------------------------------------
# transcrição por áudio
# --------------------------------------------------------------------------

def baixar_audio(url: str, tmp: Path) -> Path | None:
    import yt_dlp

    opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": str(tmp / "audio.%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "64"}],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as exc:  # noqa: BLE001
        log(f"falha ao baixar áudio: {exc}")
        return None
    for padrao in ("audio.mp3", "audio.*"):
        achados = list(tmp.glob(padrao))
        if achados:
            return achados[0]
    return None


def transcrever_whisper(audio: Path, modelo: str) -> str | None:
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        log("faster-whisper ausente; tentando instalar")
        if not pip_instalar("faster-whisper"):
            return None
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError:
            return None

    try:
        m = WhisperModel(modelo, device="cpu", compute_type="int8")
        segmentos, _ = m.transcribe(str(audio), vad_filter=True)
        linhas = []
        for seg in segmentos:
            inicio = int(seg.start)
            linhas.append(f"[{inicio // 60:02d}:{inicio % 60:02d}] {seg.text.strip()}")
        return "\n".join(linhas) if linhas else None
    except Exception as exc:  # noqa: BLE001
        log(f"Whisper falhou: {exc}")
        return None


def transcrever_gemini(audio: Path | None, url: str) -> str | None:
    """Transcreve com o Gemini (SDK google-genai).

    Com áudio local, envia o arquivo. Sem áudio, passa o link do YouTube como
    file_data, que o Gemini processa de verdade (vídeos públicos). O modelo vem de
    GEMINI_TRANSCRIBE_MODEL (padrão: gemini-3.8-flash).
    """
    chave = os.environ.get("GEMINI_API_KEY")
    if not chave:
        log("GEMINI_API_KEY não configurada; fallback Gemini indisponível")
        return None
    try:
        from google import genai  # type: ignore
        from google.genai import types  # type: ignore
    except ImportError:
        log("google-genai ausente; tentando instalar")
        if not pip_instalar("google-genai"):
            return None
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except ImportError:
            return None

    modelo = (
        os.environ.get("GEMINI_TRANSCRIBE_MODEL", "").strip()
        or os.environ.get("GEMINI_MODEL", "").strip()
        or "gemini-3.5-flash-lite"
    )
    try:
        timeout_ms = int(float(os.environ.get("GEMINI_TIMEOUT_S", "300")) * 1000)
    except ValueError:
        timeout_ms = 300_000
    instrucao = (
        "Transcreva integralmente a fala deste conteúdo, no idioma original, sem traduzir "
        "e sem resumir. Comece cada trecho com a marcação de tempo no formato [MM:SS], "
        "a cada 30 segundos no máximo. Não invente falas: se um trecho for inaudível, "
        "escreva [inaudível]. Se não houver fala, responda apenas [sem fala]."
    )
    try:
        cliente = genai.Client(api_key=chave, http_options=types.HttpOptions(timeout=timeout_ms))
        if audio and audio.exists():
            arquivo = cliente.files.upload(file=str(audio))
            conteudo = [arquivo, instrucao]
        else:
            conteudo = types.Content(parts=[
                types.Part(file_data=types.FileData(file_uri=url)),
                types.Part(text=instrucao),
            ])
        log(f"Gemini: modelo {modelo}")
        resposta = cliente.models.generate_content(model=modelo, contents=conteudo)
        texto = (getattr(resposta, "text", "") or "").strip()
        if not texto or texto == "[sem fala]":
            return None
        return texto
    except Exception as exc:  # noqa: BLE001
        log(f"Gemini falhou ({modelo}): {exc}")
        return None


# --------------------------------------------------------------------------
# principal
# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Extrai a transcrição de um vídeo do YouTube.")
    ap.add_argument("url")
    ap.add_argument("--idioma", default="pt,en", help="idiomas preferidos, separados por vírgula")
    ap.add_argument("--saida", default="transcricao.txt")
    ap.add_argument("--metadados", default="metadados.json")
    ap.add_argument("--modelo-whisper", default="small")
    ap.add_argument("--sem-whisper", action="store_true")
    ap.add_argument("--sem-gemini", action="store_true")
    args = ap.parse_args()

    if not URL_RE.match(args.url.strip()):
        log("URL não parece ser do YouTube")
        return 5

    if not garantir_ytdlp():
        log("não foi possível obter yt-dlp")
        return 2

    try:
        info = obter_info(args.url)
    except Exception as exc:  # noqa: BLE001
        log(f"não foi possível acessar o vídeo: {exc}")
        return 3

    meta = metadados_basicos(info)
    Path(args.metadados).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    if meta["ao_vivo"]:
        log("AVISO: transmissão ao vivo em andamento; a transcrição cobre apenas o trecho já disponível")

    idiomas = [i.strip() for i in args.idioma.split(",") if i.strip()]
    tmp = Path(tempfile.mkdtemp(prefix="resumo_yt_"))
    texto: str | None = None
    origem = ""

    try:
        achado = baixar_legenda(args.url, idiomas, tmp)
        if achado:
            texto, origem = achado

        if not texto and not args.sem_whisper:
            if garantir_ffmpeg():
                audio = baixar_audio(args.url, tmp)
                if audio:
                    log("transcrevendo com Whisper")
                    texto = transcrever_whisper(audio, args.modelo_whisper)
                    origem = "Whisper"
            else:
                log("ffmpeg indisponível; Whisper não pode ser usado")

        if not texto and not args.sem_gemini:
            log("tentando fallback Gemini")
            audio = next(iter(tmp.glob("audio.*")), None)
            texto = transcrever_gemini(audio, args.url)
            origem = "Gemini"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if not texto:
        log("nenhuma transcrição obtida")
        return 4

    cabecalho = (
        f"# Transcrição — {meta['titulo']}\n"
        f"# Canal: {meta['canal']} | Publicado: {meta['publicado_em']} | "
        f"Duração: {meta['duracao_segundos']}s\n"
        f"# Link: {meta['link']}\n"
        f"# Origem: {origem}\n\n"
    )
    Path(args.saida).write_text(cabecalho + texto, encoding="utf-8")
    log(f"transcrição salva em {args.saida} (origem: {origem})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
