#!/usr/bin/env python3
"""
Recorta regioes da imagem de referencia para uso como asset PROVISORIO
do tema (media.treatment = crop_from_reference no Blueprint), e informa a
proporcao de cada recorte para preencher media[].aspect_ratio.

Recorte da referencia e sempre provisorio: fica marcado com
replace_before_launch: true e listado no VALIDATION.md como conteudo
demo. Nunca apresente recorte como foto definitiva do cliente.

Uso (um recorte):
    python crop_reference.py <referencia.png> --box X,Y,L,A --out <tema>/assets/img/hero.jpg

Uso (varios recortes de uma vez):
    python crop_reference.py <referencia.png> --spec crops.json

    crops.json:
    [
      {"box": [0, 80, 1536, 520], "out": "tema/assets/img/hero.jpg"},
      {"box": [96, 700, 420, 280], "out": "tema/assets/img/project-1.jpg"}
    ]

As coordenadas (X, Y, largura, altura) sao em pixels DA REFERENCIA. Se a
referencia nao estiver em escala 1:1 com o viewport (ex.: captura 2x),
divida pelo fator antes de transferir medidas para o CSS - o recorte em
si continua usando pixels da imagem.

Opcoes:
    --max-width N   reduz recortes mais largos que N px (padrao 1920)
    --quality Q     qualidade JPEG/WebP (padrao 85)
"""
import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Erro: Pillow nao esta instalado. Rode: pip install pillow")
    sys.exit(2)

# Console do Windows usa cp1252 por padrao e corrompe acentos dos textos do Blueprint.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


COMMON_RATIOS = {
    "1:1": 1.0, "4:3": 4 / 3, "3:2": 1.5, "16:10": 1.6, "16:9": 16 / 9,
    "21:9": 21 / 9, "3:4": 0.75, "2:3": 2 / 3, "9:16": 9 / 16, "4:5": 0.8,
}


def describe_ratio(w, h):
    actual = w / h
    name, ratio = min(COMMON_RATIOS.items(), key=lambda kv: abs(kv[1] - actual))
    if abs(ratio - actual) / actual <= 0.03:
        return name
    frac = Fraction(w, h).limit_denominator(20)
    return f"{frac.numerator}:{frac.denominator}"


def crop_one(img, box, out, max_width, quality):
    x, y, w, h = (int(v) for v in box)
    if w <= 0 or h <= 0:
        raise ValueError(f"box com largura/altura invalida: {box}")
    if x < 0 or y < 0 or x + w > img.width or y + h > img.height:
        raise ValueError(
            f"box {box} sai dos limites da referencia ({img.width}x{img.height})"
        )
    region = img.crop((x, y, x + w, y + h))
    if region.width > max_width:
        new_h = round(region.height * max_width / region.width)
        region = region.resize((max_width, new_h), Image.LANCZOS)

    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fmt_opts = {}
    if out.suffix.lower() in {".jpg", ".jpeg"}:
        region = region.convert("RGB")
        fmt_opts = {"quality": quality, "optimize": True, "progressive": True}
    elif out.suffix.lower() == ".webp":
        fmt_opts = {"quality": quality}
    region.save(out, **fmt_opts)
    return region.size, describe_ratio(w, h)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reference")
    ap.add_argument("--box", help="X,Y,LARGURA,ALTURA em pixels da referencia")
    ap.add_argument("--out", help="arquivo de saida (.jpg, .png, .webp)")
    ap.add_argument("--spec", help="JSON com lista de {box, out}")
    ap.add_argument("--max-width", type=int, default=1920)
    ap.add_argument("--quality", type=int, default=85)
    args = ap.parse_args()

    if args.spec:
        with open(args.spec, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    elif args.box and args.out:
        jobs = [{"box": [int(v) for v in args.box.split(",")], "out": args.out}]
    else:
        ap.error("informe --box e --out, ou --spec")

    img = Image.open(args.reference)
    print(f"Referencia: {args.reference} ({img.width}x{img.height})\n")
    failures = 0
    for job in jobs:
        try:
            size, ratio = crop_one(img, job["box"], job["out"], args.max_width, args.quality)
            print(f"  OK  {job['out']}  {size[0]}x{size[1]}  aspect_ratio: \"{ratio}\"")
        except (ValueError, OSError, KeyError) as exc:
            failures += 1
            print(f"  ERRO {job.get('out', '?')}: {exc}")

    print("\nLembrete: marque cada recorte no Blueprint com "
          "treatment: crop_from_reference e replace_before_launch: true.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
