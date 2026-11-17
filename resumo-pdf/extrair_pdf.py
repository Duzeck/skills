#!/usr/bin/env python3
"""
extrair_pdf.py - Extrator de texto de PDF autocontido e autossuficiente.

Estrategia:
  1. Tenta extrair texto nativo (pypdf, com fallback para pdfplumber).
  2. Se o texto nativo for insuficiente (PDF escaneado), aplica OCR
     (pytesseract + Tesseract; fallback para ocrmypdf).
  3. Instala dependencias ausentes automaticamente (pip / gerenciador do SO).
  4. Trata PDF protegido por senha.
  5. Grava o texto em arquivo .txt com marcadores de pagina.

Codigos de saida:
  0 = sucesso
  2 = PDF protegido por senha (senha ausente ou incorreta)
  3 = nenhum texto extraivel mesmo apos OCR
  4 = dependencias indisponiveis e instalacao falhou
  5 = arquivo invalido, corrompido ou nao encontrado

Uso:
  python extrair_pdf.py entrada.pdf --saida saida.txt [--senha SENHA]
                                    [--min-chars 40] [--dpi 300]
                                    [--sem-instalar] [--paginas 1-20]
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXIT_OK = 0
EXIT_SENHA = 2
EXIT_SEM_TEXTO = 3
EXIT_DEPENDENCIA = 4
EXIT_ARQUIVO = 5


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def log(msg: str) -> None:
    print(f"[extrair_pdf] {msg}", file=sys.stderr)


def rodar(cmd: list[str], check: bool = False) -> tuple[int, str]:
    """Executa um comando e devolve (codigo, saida combinada)."""
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout or ""
    except FileNotFoundError:
        return 127, f"comando nao encontrado: {cmd[0]}"
    except Exception as exc:  # pragma: no cover
        return 1, str(exc)


def pip_instalar(pacotes: list[str]) -> bool:
    """Tenta instalar pacotes Python. Devolve True se ficaram importaveis."""
    log(f"instalando pacotes Python: {', '.join(pacotes)}")
    tentativas = [
        [sys.executable, "-m", "pip", "install", "--quiet", *pacotes],
        [sys.executable, "-m", "pip", "install", "--quiet", "--user", *pacotes],
        [sys.executable, "-m", "pip", "install", "--quiet",
         "--break-system-packages", *pacotes],
    ]
    for cmd in tentativas:
        codigo, saida = rodar(cmd)
        if codigo == 0:
            return True
        log(f"falhou ({codigo}): {' '.join(cmd)}")
        if saida.strip():
            log(saida.strip()[-500:])
    return False


def garantir_python_dep(modulo: str, pacote: str | None = None,
                        sem_instalar: bool = False) -> bool:
    """Garante que um modulo Python esteja importavel."""
    try:
        __import__(modulo)
        return True
    except ImportError:
        pass
    if sem_instalar:
        return False
    return pip_instalar([pacote or modulo])


def garantir_tesseract(sem_instalar: bool = False) -> bool:
    """Garante o binario do Tesseract no sistema."""
    if shutil.which("tesseract"):
        return True
    if sem_instalar:
        return False

    sistema = platform.system().lower()
    log("Tesseract nao encontrado; tentando instalar")

    if sistema == "linux":
        if shutil.which("apt-get"):
            rodar(["apt-get", "update", "-qq"])
            codigo, _ = rodar(["apt-get", "install", "-y", "-qq",
                               "tesseract-ocr", "tesseract-ocr-por",
                               "poppler-utils"])
            if codigo == 0 and shutil.which("tesseract"):
                return True
        if shutil.which("dnf"):
            rodar(["dnf", "install", "-y", "tesseract", "tesseract-langpack-por",
                   "poppler-utils"])
        elif shutil.which("apk"):
            rodar(["apk", "add", "--no-cache", "tesseract-ocr",
                   "tesseract-ocr-data-por", "poppler-utils"])
    elif sistema == "darwin":
        if shutil.which("brew"):
            rodar(["brew", "install", "tesseract", "tesseract-lang", "poppler"])
    elif sistema == "windows":
        if shutil.which("winget"):
            rodar(["winget", "install", "--silent",
                   "--accept-package-agreements",
                   "--accept-source-agreements",
                   "UB-Mannheim.TesseractOCR"])
        elif shutil.which("choco"):
            rodar(["choco", "install", "-y", "tesseract"])

    return shutil.which("tesseract") is not None


def parse_paginas(expr: str | None, total: int) -> list[int]:
    """Converte '1-20,25,30-' em lista de indices 0-based."""
    if not expr:
        return list(range(total))
    indices: list[int] = []
    for parte in expr.split(","):
        parte = parte.strip()
        if not parte:
            continue
        if "-" in parte:
            ini_s, _, fim_s = parte.partition("-")
            ini = int(ini_s) if ini_s.strip() else 1
            fim = int(fim_s) if fim_s.strip() else total
            indices.extend(range(ini - 1, min(fim, total)))
        else:
            indices.append(int(parte) - 1)
    return sorted({i for i in indices if 0 <= i < total})


# --------------------------------------------------------------------------
# Extracao
# --------------------------------------------------------------------------

def abrir_pdf(caminho: Path, senha: str | None):
    """Abre o PDF com pypdf. Devolve (reader, erro)."""
    from pypdf import PdfReader

    try:
        reader = PdfReader(str(caminho))
    except Exception as exc:
        return None, f"nao foi possivel abrir o PDF: {exc}"

    if reader.is_encrypted:
        if not senha:
            return None, "senha_necessaria"
        try:
            ok = reader.decrypt(senha)
        except Exception as exc:
            return None, f"erro ao descriptografar: {exc}"
        if not ok:
            return None, "senha_incorreta"
    return reader, None


def extrair_texto_nativo(reader, paginas: list[int]) -> tuple[str, list[int]]:
    """Extrai texto nativo. Devolve (texto, paginas_sem_texto)."""
    partes: list[str] = []
    vazias: list[int] = []
    for i in paginas:
        try:
            texto = reader.pages[i].extract_text() or ""
        except Exception as exc:
            log(f"pagina {i + 1}: falha na extracao nativa ({exc})")
            texto = ""
        if len(texto.strip()) < 20:
            vazias.append(i)
        partes.append(f"\n\n===== PAGINA {i + 1} =====\n{texto.strip()}")
    return "".join(partes), vazias


def ocr_paginas(caminho: Path, paginas: list[int], dpi: int,
                senha: str | None) -> tuple[str, list[int]]:
    """Aplica OCR nas paginas indicadas. Devolve (texto, paginas_falhas)."""
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image

    partes: list[str] = []
    falhas: list[int] = []

    for i in paginas:
        try:
            imagens = convert_from_path(
                str(caminho),
                dpi=dpi,
                first_page=i + 1,
                last_page=i + 1,
                userpw=senha or "",
            )
        except Exception as exc:
            log(f"pagina {i + 1}: falha ao rasterizar ({exc})")
            falhas.append(i)
            continue

        if not imagens:
            falhas.append(i)
            continue

        imagem: Image.Image = imagens[0]
        try:
            texto = pytesseract.image_to_string(imagem, lang="por+eng")
        except pytesseract.TesseractError:
            try:
                texto = pytesseract.image_to_string(imagem)
            except Exception as exc:
                log(f"pagina {i + 1}: falha no OCR ({exc})")
                falhas.append(i)
                continue
        except Exception as exc:
            log(f"pagina {i + 1}: falha no OCR ({exc})")
            falhas.append(i)
            continue

        if len(texto.strip()) < 10:
            falhas.append(i)
        partes.append(f"\n\n===== PAGINA {i + 1} (OCR) =====\n{texto.strip()}")

    return "".join(partes), falhas


def ocr_via_ocrmypdf(caminho: Path, senha: str | None) -> tuple[str, int]:
    """Plano B: usa ocrmypdf para gerar PDF pesquisavel e extrai o texto."""
    if not shutil.which("ocrmypdf"):
        return "", 1
    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "ocr.pdf"
        cmd = ["ocrmypdf", "--force-ocr", "--language", "por+eng",
               "--quiet", str(caminho), str(saida)]
        if senha:
            cmd[1:1] = ["--password", senha]
        codigo, saida_txt = rodar(cmd)
        if codigo != 0 or not saida.exists():
            log(f"ocrmypdf falhou ({codigo}): {saida_txt.strip()[-300:]}")
            return "", 1
        from pypdf import PdfReader
        reader = PdfReader(str(saida))
        texto = "".join(
            f"\n\n===== PAGINA {i + 1} (OCR) =====\n"
            f"{(p.extract_text() or '').strip()}"
            for i, p in enumerate(reader.pages)
        )
        return texto, 0


# --------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extrai texto de PDF (nativo ou OCR) para um arquivo .txt")
    parser.add_argument("entrada", help="caminho do PDF")
    parser.add_argument("--saida", "-o", help="arquivo .txt de saida")
    parser.add_argument("--senha", "-p", default=None, help="senha do PDF")
    parser.add_argument("--min-chars", type=int, default=40,
                        help="minimo de caracteres por pagina para considerar "
                             "texto nativo valido (padrao: 40)")
    parser.add_argument("--dpi", type=int, default=300,
                        help="DPI para rasterizacao no OCR (padrao: 300)")
    parser.add_argument("--paginas", default=None,
                        help="faixa de paginas, ex.: 1-20,25,30-")
    parser.add_argument("--sem-instalar", action="store_true",
                        help="nao tenta instalar dependencias")
    parser.add_argument("--forcar-ocr", action="store_true",
                        help="ignora texto nativo e usa OCR direto")
    args = parser.parse_args(argv)

    caminho = Path(args.entrada).expanduser()
    if not caminho.exists():
        log(f"arquivo nao encontrado: {caminho}")
        return EXIT_ARQUIVO
    if not caminho.is_file():
        log(f"caminho nao e um arquivo: {caminho}")
        return EXIT_ARQUIVO
    if caminho.suffix.lower() != ".pdf":
        log("aviso: o arquivo nao tem extensao .pdf; tentando mesmo assim")

    if not garantir_python_dep("pypdf", "pypdf", args.sem_instalar):
        log("pypdf indisponivel e nao foi possivel instalar")
        return EXIT_DEPENDENCIA

    reader, erro = abrir_pdf(caminho, args.senha)
    if erro == "senha_necessaria":
        log("PDF protegido por senha: informe --senha")
        return EXIT_SENHA
    if erro == "senha_incorreta":
        log("senha incorreta para o PDF")
        return EXIT_SENHA
    if erro:
        log(erro)
        return EXIT_ARQUIVO

    total = len(reader.pages)
    if total == 0:
        log("PDF sem paginas")
        return EXIT_ARQUIVO

    paginas = parse_paginas(args.paginas, total)
    log(f"{total} pagina(s) no PDF; processando {len(paginas)}")

    texto = ""
    paginas_ocr: list[int] = []
    paginas_falhas: list[int] = []

    if not args.forcar_ocr:
        texto_nativo, vazias = extrair_texto_nativo(reader, paginas)
        densidade = len(texto_nativo.strip()) / max(len(paginas), 1)
        if densidade >= args.min_chars:
            texto = texto_nativo
            paginas_falhas = vazias
            log("texto nativo extraido com sucesso")
        else:
            log("texto nativo insuficiente; partindo para OCR")
            paginas_ocr = paginas
    else:
        paginas_ocr = paginas

    if paginas_ocr:
        if not garantir_python_dep("pytesseract", "pytesseract",
                                   args.sem_instalar) or \
           not garantir_python_dep("pdf2image", "pdf2image",
                                   args.sem_instalar) or \
           not garantir_python_dep("PIL", "pillow", args.sem_instalar):
            log("dependencias de OCR indisponiveis")
            return EXIT_DEPENDENCIA

        if not garantir_tesseract(args.sem_instalar):
            log("Tesseract indisponivel; tentando ocrmypdf como alternativa")
            texto_ocr, codigo = ocr_via_ocrmypdf(caminho, args.senha)
            if codigo != 0:
                log("nenhuma ferramenta de OCR disponivel")
                return EXIT_DEPENDENCIA
            texto = texto_ocr
        else:
            texto, falhas = ocr_paginas(caminho, paginas_ocr, args.dpi,
                                        args.senha)
            paginas_falhas = falhas

    if len(texto.strip()) < 20:
        log("nenhum texto extraivel, mesmo apos OCR")
        return EXIT_SEM_TEXTO

    cabecalho = (
        f"Arquivo: {caminho.name}\n"
        f"Paginas no PDF: {total}\n"
        f"Paginas processadas: {len(paginas)}\n"
        f"Metodo: {'OCR' if paginas_ocr else 'texto nativo'}\n"
    )
    if paginas_falhas:
        cabecalho += ("Paginas com extracao fraca ou falha: "
                      + ", ".join(str(p + 1) for p in paginas_falhas) + "\n")
    conteudo = cabecalho + texto

    destino = Path(args.saida).expanduser() if args.saida else \
        caminho.with_suffix(".txt")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(conteudo, encoding="utf-8")
    log(f"texto gravado em {destino} ({len(conteudo)} caracteres)")
    print(str(destino))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
