#!/usr/bin/env python3
"""
Prepara o Icone do site a partir do simbolo do logo (references/site-icon.md).

O Icone do site do WordPress (Aparencia > Personalizar > Identidade do site)
gera o favicon, o icone do celular e o do manifesto - e continua editavel
pelo administrador. Este script entrega a imagem certa para ele: quadrada,
512x512, simbolo centralizado com respiro e FUNDO SOLIDO (o iPhone pinta de
preto o fundo transparente do icone).

Uso:
    python make_site_icon.py --source logo.png --out site-icon.png \
        [--box x,y,largura,altura] [--background "#FDFDFB"] [--padding 0.14] \
        [--project C:/wamp64/www/meu-site]

  --box       recorta o simbolo de uma imagem maior (ex.: a referencia),
              nas mesmas coordenadas de reference_map.box
  --keep-color  simbolo sobre foto (logo branco no header transparente):
              mantem so os pixels dessa cor - o fundo da foto sai
  --project   importa na Midia e define como Icone do site (WP-CLI)

Use so o SIMBOLO (sem o nome da empresa): em 16-32px texto vira borrao.
"""
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402

try:
    from PIL import Image, ImageChops
except ImportError:
    sys.exit("Pillow ausente: pip install pillow")


def parse_hex(value):
    v = value.lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def trim(im, bg):
    """Corta a margem: transparencia ou a cor do canto (fundo da referencia)."""
    if im.mode == "RGBA" and im.getextrema()[3][0] < 255:
        box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    else:
        rgb = im.convert("RGB")
        corner = rgb.getpixel((0, 0))
        diff = ImageChops.difference(rgb, Image.new("RGB", rgb.size, corner)).convert("L").point(lambda d: 255 if d > 24 else 0)
        box = diff.getbbox()
    return im.crop(box) if box else im


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--box", help="x,y,largura,altura")
    ap.add_argument("--background", default="#FFFFFF", help="cor solida do fundo (use a do logo/fundo do site)")
    ap.add_argument("--padding", type=float, default=0.14, help="respiro em cada lado (fracao, padrao 0.14)")
    ap.add_argument("--keep-color", help="cor do simbolo (ex.: #FFFFFF) quando ele esta sobre foto: o resto e descartado")
    ap.add_argument("--tolerance", type=float, default=60, help="distancia de cor aceita em --keep-color (padrao 60)")
    ap.add_argument("--project", help="pasta do WordPress: importa e define como Icone do site")
    args = ap.parse_args()

    im = Image.open(args.source).convert("RGBA")
    if args.box:
        x, y, w, h = (int(v) for v in args.box.split(","))
        im = im.crop((x, y, x + w, y + h))
    if args.keep_color:
        # Logo sobre foto (header transparente): fica so o que tem a cor do
        # simbolo; o resto vira transparente. Borda suave pela distancia.
        target = parse_hex(args.keep_color)
        px = im.load()
        for yy in range(im.height):
            for xx in range(im.width):
                r, g, b, a = px[xx, yy]
                dist = ((r - target[0]) ** 2 + (g - target[1]) ** 2 + (b - target[2]) ** 2) ** 0.5
                alpha = 255 if dist <= args.tolerance else max(0, 255 - int((dist - args.tolerance) * 4))
                px[xx, yy] = (target[0], target[1], target[2], min(a, alpha))
    im = trim(im, args.background)
    if min(im.size) < 64:
        print(f"Aviso: simbolo pequeno ({im.size[0]}x{im.size[1]}px) - o icone fica borrado; prefira o logo em alta (SVG/PNG do cliente).")
    side = 512
    inner = round(side * (1 - 2 * args.padding))
    scale = inner / max(im.size)
    sym = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (side, side), parse_hex(args.background) + (255,))
    canvas.alpha_composite(sym, ((side - sym.width) // 2, (side - sym.height) // 2))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(out, "PNG", optimize=True)
    print(f"Gerado: {out} (512x512, fundo {args.background})")

    if args.project:
        def wp(*a):
            r = subprocess.run(_wpcli.resolve(["wp", *a]), cwd=args.project, capture_output=True, text=True)
            if r.returncode != 0:
                sys.exit(f"WP-CLI falhou: {(r.stderr or r.stdout).strip()[:300]}")
            return r.stdout.strip()
        att = wp("media", "import", str(out.resolve()), "--title=Ícone do site", "--porcelain")
        wp("option", "update", "site_icon", att)
        print(f"Icone do site definido (anexo {att}) - o administrador troca em Aparencia > Personalizar > Identidade do site.")


if __name__ == "__main__":
    main()
