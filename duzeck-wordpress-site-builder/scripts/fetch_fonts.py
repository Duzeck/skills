#!/usr/bin/env python3
"""
Hospeda as fontes do Blueprint no proprio tema (references/fonts.md).

Le BLUEPRINT.yaml -> fonts e, para cada familia de source google_fonts:
  1. baixa so os pesos/estilos declarados, em woff2, so o subconjunto
     latin (cobre todo o portugues: a-z, acentos, cedilha). Fonte variavel
     servida num arquivo so para varios pesos = um arquivo, peso em faixa;
  2. grava <tema>/assets/fonts/*.woff2 + a licenca (OFL/Apache) da familia;
  3. gera <tema>/assets/css/fonts.css: @font-face com font-display: swap e
     unicode-range, mais a fonte de RESERVA ajustada ("<Familia> Fallback",
     local Arial/Times com size-adjust/ascent/descent/line-gap calculados
     das metricas reais da fonte) - o texto nao "pula" quando a fonte chega;
  4. gera <tema>/assets/fonts/manifest.json (arquivos a pre-carregar),
     lido por inc/fonts.php.
Familias source provided (arquivo do cliente): copie os .woff2 para
assets/fonts/ e declare em fonts.css a mao; o script so valida.

Depois rode scripts/generate_design_tokens.py: ele insere a reserva
("'Manrope', 'Manrope Fallback', sans-serif") nos tokens de fonte.

Uso:
    python fetch_fonts.py BLUEPRINT.yaml --theme <pasta-do-tema> [--no-fallback-metrics]

A unica chamada externa e para fonts.googleapis.com/fonts.gstatic.com e o
GitHub do google/fonts (licenca), com o nome das familias - nada do
projeto ou do usuario e enviado. O SITE nao chama o Google: o visitante
baixa as fontes do proprio dominio (LGPD, sem conexao extra).
"""
import argparse
import json
import re
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

# woff2 so e servido para navegadores modernos; sem UA o Google devolve TTF
# (usado so para ler as metricas, nunca publicado).
WOFF2_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
TTF_UA = "fetch-fonts/1.0"
KEEP_SUBSET = "latin"

# Frequencia das letras no portugues (%), + espaco: largura media "real" de
# um texto em portugues - melhor que a media de todos os glifos (xAvgCharWidth).
PT_FREQ = {
    " ": 17.0, "a": 14.6, "e": 12.6, "o": 10.7, "s": 7.8, "r": 6.5, "i": 6.2, "n": 5.0,
    "d": 5.0, "m": 4.7, "u": 4.6, "t": 4.3, "c": 3.9, "l": 2.8, "p": 2.5, "v": 1.7,
    "g": 1.3, "h": 1.3, "q": 1.2, "b": 1.0, "f": 1.0, "z": 0.5, "j": 0.4, "x": 0.2,
    "ã": 0.7, "ç": 0.5, "é": 0.5, "á": 0.4, "ê": 0.4, "ó": 0.3, "í": 0.3, "õ": 0.2,
}

# Largura media ponderada (PT_FREQ, em fracao do em) e metricas verticais das
# fontes de reserva do sistema, medidas dos arquivos do Windows (arial.ttf,
# arialbd.ttf, times.ttf, timesbd.ttf) com o mesmo parser deste script.
SYSTEM_FALLBACKS = {
    ("sans-serif", "regular"): {"local": ["Arial", "ArialMT"], "avg": 0.4696},
    ("sans-serif", "bold"): {"local": ["Arial Bold", "Arial-BoldMT"], "avg": 0.5033},
    ("serif", "regular"): {"local": ["Times New Roman", "TimesNewRomanPSMT"], "avg": 0.4160},
    ("serif", "bold"): {"local": ["Times New Roman Bold", "TimesNewRomanPS-BoldMT"], "avg": 0.4433},
}


# --------------------------------------------------------------- SFNT (TTF)

def _tables(data):
    num = struct.unpack(">H", data[4:6])[0]
    out = {}
    for i in range(num):
        rec = data[12 + 16 * i: 28 + 16 * i]
        tag = rec[:4].decode("latin-1")
        offset, length = struct.unpack(">II", rec[8:16])
        out[tag] = (offset, length)
    return out


def _cmap(data, offset):
    """Mapa codepoint -> glifo (subtabelas formato 4 e 12, Unicode)."""
    _ver, n = struct.unpack(">HH", data[offset:offset + 4])
    subs = []
    for i in range(n):
        pid, eid, off = struct.unpack(">HHI", data[offset + 4 + 8 * i: offset + 12 + 8 * i])
        subs.append(((pid, eid), offset + off))
    by = dict(subs)
    pick = by.get((3, 10)) or by.get((0, 4)) or by.get((3, 1)) or by.get((0, 3)) or (subs[0][1] if subs else None)
    if pick is None:
        return lambda c: 0
    fmt = struct.unpack(">H", data[pick:pick + 2])[0]
    if fmt == 12:
        ngroups = struct.unpack(">I", data[pick + 12:pick + 16])[0]
        groups = [struct.unpack(">III", data[pick + 16 + 12 * g: pick + 28 + 12 * g]) for g in range(ngroups)]

        def lookup(c):
            for start, end, gid in groups:
                if start <= c <= end:
                    return gid + (c - start)
            return 0
        return lookup
    if fmt == 4:
        seg2 = struct.unpack(">H", data[pick + 6:pick + 8])[0]
        seg = seg2 // 2
        base = pick + 14
        ends = struct.unpack(f">{seg}H", data[base:base + seg2])
        starts = struct.unpack(f">{seg}H", data[base + seg2 + 2: base + 2 * seg2 + 2])
        deltas = struct.unpack(f">{seg}h", data[base + 2 * seg2 + 2: base + 3 * seg2 + 2])
        ro_pos = base + 3 * seg2 + 2
        ranges = struct.unpack(f">{seg}H", data[ro_pos: ro_pos + seg2])

        def lookup(c):
            for i in range(seg):
                if starts[i] <= c <= ends[i]:
                    if ranges[i] == 0:
                        return (c + deltas[i]) & 0xFFFF
                    addr = ro_pos + 2 * i + ranges[i] + 2 * (c - starts[i])
                    gid = struct.unpack(">H", data[addr:addr + 2])[0]
                    return (gid + deltas[i]) & 0xFFFF if gid else 0
            return 0
        return lookup
    return lambda c: 0


def font_metrics(data):
    """upm, ascent, descent (positivo), lineGap e largura media PT (fracao do em)."""
    t = _tables(data)
    head = t["head"][0]
    upm = struct.unpack(">H", data[head + 18: head + 20])[0]
    hhea = t["hhea"][0]
    asc, desc, gap = struct.unpack(">hhh", data[hhea + 4: hhea + 10])
    n_metrics = struct.unpack(">H", data[hhea + 34: hhea + 36])[0]
    if "OS/2" in t:
        os2 = t["OS/2"][0]
        fs_selection = struct.unpack(">H", data[os2 + 62: os2 + 64])[0]
        if fs_selection & (1 << 7):   # USE_TYPO_METRICS: o navegador usa as tipograficas
            asc, desc, gap = struct.unpack(">hhh", data[os2 + 68: os2 + 74])
    hmtx = t["hmtx"][0]
    advances = struct.unpack(f">{n_metrics * 2}H", data[hmtx: hmtx + 4 * n_metrics])[0::2]
    gid_of = _cmap(data, t["cmap"][0])
    total = weight = 0.0
    for ch, freq in PT_FREQ.items():
        gid = gid_of(ord(ch))
        if not gid:
            continue
        adv = advances[gid] if gid < len(advances) else advances[-1]
        total += freq * adv
        weight += freq
    avg = (total / weight / upm) if weight else 0.5
    return {"upm": upm, "ascent": asc / upm, "descent": abs(desc) / upm, "line_gap": gap / upm, "avg": avg}


# --------------------------------------------------------------- Google Fonts

def http_get(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read()


def css2_url(family, weights, styles):
    ital = "italic" in styles
    if ital:
        axis = ";".join(f"{1 if s == 'italic' else 0},{w}" for s in sorted(set(styles), key=lambda s: s != "normal")
                        for w in sorted(weights))
        spec = f"{family}:ital,wght@{axis}"
    else:
        spec = f"{family}:wght@{';'.join(str(w) for w in sorted(weights))}"
    return "https://fonts.googleapis.com/css2?family=" + urllib.parse.quote(spec, safe=":@;,") + "&display=swap"


FACE_RE = re.compile(r"(?:/\*\s*([\w-]+)\s*\*/\s*)?@font-face\s*\{([^}]*)\}", re.S)


def parse_faces(css):
    faces = []
    for subset, body in FACE_RE.findall(css):
        prop = dict((k.strip(), v.strip()) for k, v in re.findall(r"([\w-]+)\s*:\s*([^;]+);", body))
        url = re.search(r"url\(([^)]+)\)", prop.get("src", ""))
        faces.append({"subset": subset or None, "style": prop.get("font-style", "normal"),
                      "weight": prop.get("font-weight", "400"), "url": url.group(1).strip("'\"") if url else None,
                      "unicode_range": prop.get("unicode-range")})
    return faces


def slugify(family):
    return re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")


def fetch_license(family, dest):
    slug = re.sub(r"[^a-z0-9]", "", family.lower())
    for folder, name in (("ofl", "OFL.txt"), ("apache", "LICENSE.txt"), ("ufl", "UFL.txt")):
        try:
            text = http_get(f"https://raw.githubusercontent.com/google/fonts/main/{folder}/{slug}/{name}", TTF_UA)
            (dest / f"LICENSE-{slugify(family)}.txt").write_bytes(text)
            return folder.upper()
        except urllib.error.URLError:
            continue
    (dest / f"LICENSE-{slugify(family)}.txt").write_text(
        f"{family}: licenca em https://fonts.google.com/specimen/{family.replace(' ', '+')}/license\n", encoding="utf-8")
    return None


def generic_of(bp, family):
    """sans-serif | serif, pelo token de fonte que comeca com a familia."""
    tokens = (((bp.get("design") or {}).get("tokens") or {}).get("font_family") or {})
    for raw in tokens.values():
        value = raw.get("value") if isinstance(raw, dict) else raw
        names = [n.strip().strip("'\"") for n in str(value or "").split(",")]
        if names and names[0].lower() == family.lower():
            return "serif" if "serif" in names and "sans-serif" not in names else "sans-serif"
    return "sans-serif"


def pct(x):
    return f"{x * 100:.2f}%"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("blueprint")
    ap.add_argument("--theme", required=True, help="pasta do tema (wp-content/themes/<slug>-theme)")
    ap.add_argument("--no-fallback-metrics", action="store_true", help="nao gera a reserva ajustada (so para comparacao)")
    args = ap.parse_args()

    raw = yaml.safe_load(Path(args.blueprint).read_text(encoding="utf-8")) or {}
    bp = raw.get("blueprint", raw)
    fonts = bp.get("fonts") or {}
    delivery = fonts.get("delivery")
    theme = Path(args.theme)
    font_dir = theme / "assets" / "fonts"
    css_path = theme / "assets" / "css" / "fonts.css"
    if delivery == "system":
        print("fonts.delivery system: nenhuma fonte web - nada a baixar.")
        font_dir.mkdir(parents=True, exist_ok=True)
        (font_dir / "manifest.json").write_text(json.dumps({"delivery": "system", "preload": []}, indent=2), encoding="utf-8")
        return
    if delivery == "google_cdn":
        families = fonts.get("families") or []
        url = "https://fonts.googleapis.com/css2?" + "&".join(
            css2_url(f["family"], f.get("weights") or [400], f.get("styles") or ["normal"]).split("?", 1)[1].split("&display")[0]
            for f in families) + "&display=swap"
        font_dir.mkdir(parents=True, exist_ok=True)
        (font_dir / "manifest.json").write_text(json.dumps({"delivery": "google_cdn", "css_url": url, "preload": []}, indent=2),
                                                encoding="utf-8")
        print(f"fonts.delivery google_cdn (excecao aprovada): {url}")
        return
    if delivery != "self_hosted":
        sys.exit(f"fonts.delivery invalido: {delivery!r} (self_hosted | system | google_cdn).")

    fallback_metrics = fonts.get("fallback_metrics", True) and not args.no_fallback_metrics
    font_dir.mkdir(parents=True, exist_ok=True)
    css_path.parent.mkdir(parents=True, exist_ok=True)
    faces_css, fallback_css, manifest_fams, preload = [], [], [], []
    total_bytes = 0

    for fam in fonts.get("families") or []:
        family = fam["family"]
        weights = sorted(int(w) for w in fam.get("weights") or [400])
        styles = fam.get("styles") or ["normal"]
        if fam.get("source", "google_fonts") != "google_fonts":
            print(f"{family}: source {fam.get('source')} - arquivos do cliente em assets/fonts/ (declare em fonts.css).")
            continue
        url = css2_url(family, weights, styles)
        try:
            css = http_get(url, WOFF2_UA).decode("utf-8")
        except urllib.error.HTTPError as err:
            sys.exit(f"{family}: Google Fonts recusou ({err.code}) - nome da familia ou peso inexistente? {url}")
        faces = [f for f in parse_faces(css) if f["subset"] == KEEP_SUBSET and f["url"]]
        if not faces:
            sys.exit(f"{family}: nenhum arquivo do subconjunto '{KEEP_SUBSET}' na resposta do Google Fonts.")
        # Fonte variavel: varios pesos, mesmo arquivo -> um arquivo, peso em faixa.
        groups = {}
        for f in faces:
            groups.setdefault((f["style"], f["url"]), []).append(int(f["weight"]))
        files = []
        for (style, furl), ws in groups.items():
            ws = sorted(set(ws))
            wtxt = str(ws[0]) if len(ws) == 1 else f"{ws[0]}-{ws[-1]}"
            name = f"{slugify(family)}-{wtxt}{'-italic' if style == 'italic' else ''}.woff2"
            blob = http_get(furl, WOFF2_UA)
            (font_dir / name).write_bytes(blob)
            total_bytes += len(blob)
            unicode_range = next(f["unicode_range"] for f in faces if f["url"] == furl)
            faces_css.append(
                "@font-face {\n"
                f"    font-family: '{family}';\n"
                f"    font-style: {style};\n"
                f"    font-weight: {ws[0] if len(ws) == 1 else f'{ws[0]} {ws[-1]}'};\n"
                "    font-display: swap;\n"
                f"    src: url('../fonts/{name}') format('woff2');\n"
                f"    unicode-range: {unicode_range};\n"
                "}"
            )
            files.append({"file": name, "style": style, "weights": ws, "bytes": len(blob)})
            print(f"  {name}  ({len(blob) // 1024} KB, pesos {ws})")
        for w in fam.get("preload") or []:
            hit = next((f["file"] for f in files if f["style"] == "normal" and f["weights"][0] <= int(w) <= f["weights"][-1]), None)
            if hit and hit not in preload:
                preload.append(hit)
        lic = fetch_license(family, font_dir)
        manifest_fams.append({"family": family, "role": fam.get("role"), "files": files, "license": lic or fam.get("license")})

        if fallback_metrics:
            generic = generic_of(bp, family)
            ttf_faces = [f for f in parse_faces(http_get(url, TTF_UA).decode("utf-8")) if f["url"] and f["style"] == "normal"]
            for group, target, wrange in (("regular", 400, "100 599"), ("bold", 700, "600 900")):
                in_group = [w for w in weights if (w < 600) == (group == "regular")]
                if not in_group:
                    continue
                rep = min(in_group, key=lambda w: abs(w - target))
                ttf = next((f for f in ttf_faces if int(f["weight"].split()[0]) == rep), None) or (ttf_faces[0] if ttf_faces else None)
                if not ttf:
                    print(f"  aviso: sem TTF para medir {family} {rep} - reserva nao ajustada.")
                    continue
                m = font_metrics(http_get(ttf["url"], TTF_UA))
                sys_fb = SYSTEM_FALLBACKS[(generic, group)]
                size_adjust = m["avg"] / sys_fb["avg"]
                local = ", ".join(f"local('{n}')" for n in sys_fb["local"])
                fallback_css.append(
                    "@font-face {\n"
                    f"    font-family: '{family} Fallback';\n"
                    f"    src: {local};\n"
                    f"    font-weight: {wrange};\n"
                    f"    size-adjust: {pct(size_adjust)};\n"
                    f"    ascent-override: {pct(m['ascent'] / size_adjust)};\n"
                    f"    descent-override: {pct(m['descent'] / size_adjust)};\n"
                    f"    line-gap-override: {pct(m['line_gap'] / size_adjust)};\n"
                    "}"
                )
                print(f"  reserva {family} {group}: {sys_fb['local'][0]} size-adjust {pct(size_adjust)}")

    if len(preload) > 2:
        print(f"Aviso: {len(preload)} arquivos para pre-carregar - mais de 2 atrasa o resto da pagina. Mantidos os 2 primeiros.")
        preload = preload[:2]
    header = ("/*\n * Fontes - GERADO por scripts/fetch_fonts.py a partir de BLUEPRINT.yaml -> fonts.\n"
              " * NAO edite a mao. Arquivos em ../fonts/ (hospedados no proprio site: sem\n"
              " * conexao com o Google, o IP do visitante nao sai do dominio - LGPD).\n */\n\n")
    body = "\n\n".join(faces_css)
    if fallback_css:
        body += ("\n\n/* Reserva com metricas ajustadas: ate a fonte chegar, o texto ocupa o\n"
                 "   mesmo espaco (sem salto de layout na troca - CLS). */\n" + "\n\n".join(fallback_css))
    css_path.write_text(header + body + "\n", encoding="utf-8", newline="\n")
    (font_dir / "manifest.json").write_text(json.dumps({
        "delivery": "self_hosted", "fallback_metrics": bool(fallback_css), "preload": preload,
        "families": manifest_fams, "total_bytes": total_bytes}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGerado: {css_path} ({len(faces_css)} arquivo(s), {total_bytes // 1024} KB no total)")
    print(f"Pre-carregar: {', '.join(preload) or 'nenhum'}")
    print("Proximo passo: python scripts/generate_design_tokens.py <BLUEPRINT> --out <tema>/assets/css/tokens.css")


if __name__ == "__main__":
    main()
