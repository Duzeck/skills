#!/usr/bin/env python3
"""
Pagina VISUAL de aprovacao do Blueprint (references/approval-protocol.md).

O cliente aprova vendo, nao lendo codigos: cores como amostras, fontes ja
renderizadas com os arquivos reais, escala de tamanhos, botoes no estilo
do site, cada secao ao lado do recorte da referencia, as decisoes visuais
desenhadas (menu no celular) e as pendencias numeradas. Tudo sai do
Blueprint - nao existe um layout paralelo para manter.

Uso:
    python render_approval_page.py BLUEPRINT.yaml --out documentation/APROVACAO.html \
        [--refs <pasta das imagens de referencia>] [--no-fonts]

Arquivo unico (CSS, fontes e recortes embutidos): abre com dois cliques,
pode ser enviado ao cliente. As fontes vem do Google Fonts no momento de
gerar (so o nome das familias e enviado); --no-fonts usa a reserva.
"""
import argparse
import base64
import contextlib
import datetime
import html
import io
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_blueprint_summary as summary  # noqa: E402
from generate_design_tokens import _label, unwrap  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

E = html.escape
MOBILE_MENU = {
    "dropdown": ("Lista abaixo do topo", "O menu abre logo abaixo da barra, empurrando ou cobrindo o conteúdo."),
    "offcanvas": ("Gaveta lateral", "O menu desliza da lateral e cobre parte da tela."),
    "fullscreen": ("Tela cheia", "O menu ocupa a tela inteira, com os itens grandes."),
}


def tokens_of(bp, group):
    raw = (((bp.get("design") or {}).get("tokens") or {}).get(group) or {})
    out = []
    for name, value in raw.items():
        v, conf, _ev = unwrap(value)
        if v is not None:
            out.append((name, str(v), conf))
    return out


def hex_rgb(value):
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", value.strip())
    return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)) if m else None


def luminance(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def first_family(stack):
    return stack.split(",")[0].strip().strip("'\"")


def embed_fonts(bp):
    """@font-face com os woff2 reais (base64). (css, aviso)."""
    families = (bp.get("fonts") or {}).get("families") or []
    if not families:
        return "", None
    try:
        import fetch_fonts as ff
        faces = []
        for fam in families:
            if fam.get("source", "google_fonts") != "google_fonts":
                continue
            weights = sorted(int(w) for w in fam.get("weights") or [400])
            css = ff.http_get(ff.css2_url(fam["family"], weights, fam.get("styles") or ["normal"]), ff.WOFF2_UA).decode("utf-8")
            seen = set()
            for f in ff.parse_faces(css):
                if f["subset"] != ff.KEEP_SUBSET or not f["url"] or f["url"] in seen:
                    continue
                seen.add(f["url"])
                ws = sorted({int(x["weight"]) for x in ff.parse_faces(css) if x["url"] == f["url"]})
                data = base64.b64encode(ff.http_get(f["url"], ff.WOFF2_UA)).decode("ascii")
                faces.append(f"@font-face{{font-family:'{fam['family']}';font-style:{f['style']};"
                             f"font-weight:{ws[0]}{' ' + str(ws[-1]) if len(ws) > 1 else ''};font-display:swap;"
                             f"src:url(data:font/woff2;base64,{data}) format('woff2');unicode-range:{f['unicode_range']}}}")
        return "\n".join(faces), None
    except Exception as err:  # sem internet / familia inexistente
        return "", f"Fontes nao embutidas ({err}); a pagina mostra a fonte de reserva."


def crop(refs, entry, max_w=560):
    """Recorte da referencia (reference_map.box = [x, y, largura, altura]) em JPEG base64."""
    try:
        from PIL import Image
    except ImportError:
        return None
    path = Path(refs, str(entry.get("file") or ""))
    box = entry.get("box")
    if not path.is_file() or not (isinstance(box, list) and len(box) == 4):
        return None
    x, y, w, h = (int(v) for v in box)
    with Image.open(path) as im:
        part = im.convert("RGB").crop((x, y, x + w, y + h))
        if part.width > max_w:
            part = part.resize((max_w, round(part.height * max_w / part.width)))
        buf = io.BytesIO()
        part.save(buf, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def md_to_html(md):
    """Markdown minimo do resumo (titulos, tabelas, listas, paragrafos)."""
    out, table, items = [], [], []

    def inline(text):
        text = E(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        return re.sub(r"`(.+?)`", r"<code>\1</code>", text)

    def flush():
        if table:
            rows = [r for r in table if not re.fullmatch(r"\|[\s|:-]+\|", r)]
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            head = "".join(f"<th>{inline(c)}</th>" for c in cells[0])
            body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in cells[1:])
            out.append(f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            table.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in md.splitlines():
        s = line.rstrip()
        if s.startswith("|"):
            table.append(s)
            continue
        if s.lstrip().startswith("- "):
            items.append(s.lstrip()[2:])
            continue
        flush()
        if s.startswith("# "):
            continue  # o titulo ja esta no topo da pagina
        if s.startswith("## "):
            out.append(f"<h3>{inline(s[3:])}</h3>")
        elif s.strip():
            out.append(f"<p>{inline(s)}</p>")
    flush()
    return "\n".join(out)


def phone(kind, chosen):
    """Mini celular desenhando um tipo de menu."""
    items = "".join("<i></i>" for _ in range(4))
    menu = {"dropdown": f'<div class="m-drop">{items}</div>',
            "offcanvas": f'<div class="m-shade"></div><div class="m-side">{items}</div>',
            "fullscreen": f'<div class="m-full">{items}</div>'}[kind]
    title, text = MOBILE_MENU[kind]
    return (f'<figure class="phone{" is-chosen" if chosen else ""}"><div class="screen"><div class="m-bar"><b></b><span>☰</span></div>'
            f'<div class="m-page"><i></i><i></i><i></i></div>{menu}</div>'
            f'<figcaption><strong>{E(title)}</strong>{" ✓ proposto" if chosen else ""}<br>{E(text)}</figcaption></figure>')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("blueprint")
    ap.add_argument("--out", required=True)
    ap.add_argument("--refs", help="pasta das imagens de reference_map[].file (padrao: pasta do Blueprint)")
    ap.add_argument("--no-fonts", action="store_true")
    args = ap.parse_args()

    bp = summary.load(args.blueprint)
    refs = Path(args.refs) if args.refs else Path(args.blueprint).resolve().parent
    project = bp.get("project") or {}
    meta = bp.get("metadata") or {}
    colors = [(n, v, c) for n, v, c in tokens_of(bp, "color") if hex_rgb(v) or v.startswith(("rgb", "#"))]
    families = dict((n, v) for n, v, _c in tokens_of(bp, "font_family"))
    sizes = tokens_of(bp, "font_size")
    weights = dict((n, v) for n, v, _c in tokens_of(bp, "font_weight"))
    radius = dict((n, v) for n, v, _c in tokens_of(bp, "radius"))
    color = dict((n, v) for n, v, _c in colors)
    font_css, font_note = ("", "Fontes nao embutidas (--no-fonts).") if args.no_fonts else embed_fonts(bp)
    heading = families.get("heading", "sans-serif")
    body = families.get("body", "sans-serif")
    pending = []

    # 1. Cores
    swatches = []
    for name, value, conf in colors:
        rgb = hex_rgb(value)
        ink = "#000" if rgb and contrast(rgb, (0, 0, 0)) >= contrast(rgb, (255, 255, 255)) else "#fff"
        ratio = ""
        if rgb and hex_rgb(color.get("background", "#ffffff")):
            ratio = f"{contrast(rgb, hex_rgb(color.get('background', '#ffffff'))):.1f}:1 sobre o fundo"
        swatches.append(f'<li><span class="sw" style="background:{E(value)};color:{ink}">Aa</span>'
                        f'<b>{E(_label(name))}</b><code>{E(value)}</code><small>{E(ratio)}</small>'
                        f'{"<em>estimada - confirmar</em>" if conf == "low" else ""}</li>')
        if conf == "low":
            pending.append(f"Cor <b>{E(_label(name))}</b> ({E(value)}) foi estimada da imagem.")

    # 2. Fontes e tamanhos
    font_rows = []
    for fam in (bp.get("fonts") or {}).get("families") or []:
        role = {"heading": heading, "body": body}.get(fam.get("role"), f"'{fam['family']}', sans-serif")
        samples = "".join(f'<p style="font-family:{E(role)};font-weight:{int(w)}">{w} — Construímos o seu projeto com prazo e qualidade. Ação, ç, ã, é.</p>'
                          for w in fam.get("weights") or [400])
        font_rows.append(f'<div class="fontcard"><h4>{E(fam["family"])} <small>{E(_label(fam.get("role", "")))}</small></h4>{samples}</div>')
    conf_fonts = [n for n, _v, c in tokens_of(bp, "font_family") if c == "low"]
    if conf_fonts:
        pending.append("Fontes <b>" + ", ".join(E(first_family(families[n])) for n in conf_fonts) +
                       "</b> foram estimadas pela forma das letras - confirme ou envie o nome usado no design.")
    scale = "".join(f'<div class="scale"><small>{E(_label(n))}<br><code>{E(v)}</code></small>'
                    f'<span style="font-size:{E(v)};font-family:{E(heading if n not in ("body", "small", "lead") else body)};'
                    f'font-weight:{E(weights.get("heading" if n not in ("body", "small", "lead") else "body", "400"))}">Construa com a gente</span></div>'
                    for n, v, _c in sizes)

    # 3. Botoes (mesmo padrao do style.css do esqueleto: principal cheio, secundario contorno)
    btn_radius = radius.get("pill") or radius.get("md") or radius.get("sm") or "6px"
    labels = []
    for h in bp.get("heroes") or []:
        labels += [b.get("label") for b in h.get("buttons") or [] if isinstance(b, dict)]
    labels = list(dict.fromkeys([l for l in labels if l]))[:2] or ["Botão principal", "Botão secundário"]
    buttons = (f'<a class="btn" style="background:{E(color.get("primary", "#333"))};color:{E(color.get("background", "#fff"))};'
               f'border-radius:{E(btn_radius)};font-family:{E(body)}">{E(labels[0])}</a>')
    if len(labels) > 1:
        buttons += (f'<a class="btn" style="border:2px solid currentColor;color:{E(color.get("text", "#222"))};'
                    f'border-radius:{E(btn_radius)};font-family:{E(body)}">{E(labels[1])}</a>')

    # 4. Paginas e secoes ao lado do recorte da referencia
    ref_map = {(r.get("page"), r.get("section")): r for r in bp.get("reference_map") or [] if isinstance(r, dict)}
    editable = {e.get("target"): e for e in bp.get("editable_content") or [] if isinstance(e, dict)}
    kind_pt = {"static": "fixa (textos editáveis no painel)", "dynamic": "lista do painel (itens cadastrados)",
               "global": "repetida em várias páginas", "functional": "funcional"}
    page_html = []
    for p in bp.get("pages") or []:
        rows = []
        for sec in p.get("sections") or []:
            ref = ref_map.get((p.get("id"), sec.get("id"))) or ref_map.get((p.get("id"), sec.get("component")))
            img = crop(refs, ref) if ref else None
            where = (editable.get(sec.get("id")) or {}).get("where")
            sec_id = E(sec.get("id") or "")
            ref_html = (f'<img src="{img}" alt="Recorte da referência: {sec_id}">' if img
                        else "<span>sem recorte na referência</span>")
            info = [f"<b>{sec_id}</b>", f'<span>{E(str(sec.get("component") or ""))}</span>',
                    f'<small>{E(kind_pt.get(sec.get("type"), str(sec.get("type") or "")))}</small>']
            if where:
                info.append(f"<small>Onde editar: {E(where)}</small>")
            if ref and ref.get("note"):
                info.append(f'<small>{E(ref["note"])}</small>')
            rows.append(f'<div class="sec"><div class="ref">{ref_html}</div><div class="what">{"".join(info)}</div></div>')
        slug = p.get("slug") or ""
        page_html.append(f'<details open><summary>{E(p.get("name") or p.get("title") or p.get("id"))} <code>/{E(slug)}</code> — {len(rows)} seção(ões)</summary>{"".join(rows)}</details>')

    # 5. Decisao visual: menu no celular
    header = bp.get("header") or {}
    mobile = header.get("mobile_menu")
    phones = "".join(phone(k, k == mobile) for k in MOBILE_MENU) if header else ""
    if header:
        pending.append(f"Menu no celular: proposta <b>{E(MOBILE_MENU.get(mobile, (str(mobile), ''))[0])}</b> "
                       "(a referência só mostra o computador) - confirme ou escolha outro desenho.")

    # 6. Pendencias do Blueprint
    for d in bp.get("decisions") or []:
        if d.get("status") == "pending_user_approval":
            pending.append(f"Decisão: <b>{E(d.get('subject') or '')}</b> - {E(d.get('decision') or '')}")
    for u in bp.get("uncertainties") or []:
        if u.get("status") == "pending":
            pending.append(f"{'<b>[bloqueia]</b> ' if u.get('blocking') else ''}{E(u.get('subject') or u.get('question') or u.get('id') or '')}"
                           f"{(' - ' + E(u.get('question'))) if u.get('question') and u.get('subject') else ''}")
    seo = bp.get("seo") or {}
    if seo.get("ai_crawlers_source") == "default":
        pending.append("Robôs de inteligência artificial: padrão <b>liberar</b> aplicado - confirme a escolha.")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        sys.argv = ["render_blueprint_summary.py", args.blueprint]
        try:
            summary.main()
        except SystemExit:
            pass
    details_html = md_to_html(buf.getvalue())

    bg, ink, accent = color.get("background", "#fff"), color.get("text", "#1d1d1f"), color.get("primary", "#444")
    page = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aprovação - {E(project.get('name') or '')}</title>
<style>
{font_css}
:root{{--bg:#f6f6f4;--card:#fff;--ink:#1d1d1f;--muted:#5f6368;--line:#e3e3df;--accent:{E(accent)}}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
main{{max-width:1080px;margin:0 auto;padding:32px 16px 80px}} h1{{font-size:1.9rem;margin:0 0 4px}} h2{{margin:48px 0 12px;font-size:1.35rem}}
h3{{margin:28px 0 8px;font-size:1.05rem}} .lead{{color:var(--muted);margin:0 0 20px}} code{{font-size:.85em;background:#0000000d;padding:1px 5px;border-radius:4px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:20px}}
.how{{border-left:4px solid var(--accent)}} ol.pend li{{margin:6px 0}} .note{{color:#8a5300;font-size:.9rem}}
.swatches{{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}}
.swatches li{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px;display:flex;flex-direction:column;gap:3px}}
.sw{{height:64px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-weight:700;border:1px solid #0000001a}}
.swatches small,.swatches em{{color:var(--muted);font-size:.78rem}} .swatches em{{color:#8a5300}}
.fontcard{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin-bottom:12px}} .fontcard h4{{margin:0 0 6px}}
.fontcard p{{margin:4px 0;font-size:1.15rem;overflow-wrap:anywhere}} .fontcard small{{color:var(--muted);font-weight:400}}
.preview{{background:{E(bg)};color:{E(ink)};border-radius:12px;border:1px solid var(--line);padding:20px;overflow:hidden}}
.scale{{display:grid;grid-template-columns:150px 1fr;gap:12px;align-items:baseline;padding:8px 0;border-bottom:1px solid #0000000f}}
.scale span{{line-height:1.15;overflow-wrap:anywhere}} .scale small{{color:var(--muted)}}
.btn{{display:inline-flex;align-items:center;min-height:44px;padding:0 22px;margin:6px 10px 6px 0;font-weight:600;text-decoration:none}}
details{{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:12px 0;padding:6px 16px}} summary{{cursor:pointer;font-weight:700;padding:8px 0}}
.sec{{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:16px;padding:12px 0;border-top:1px solid var(--line)}}
.ref img{{width:100%;height:auto;border-radius:6px;border:1px solid var(--line)}} .ref span{{color:var(--muted);font-size:.85rem}}
.what{{display:flex;flex-direction:column;gap:4px}} .what span{{font-size:.95rem}} .what small{{color:var(--muted)}}
.phones{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px}}
.phone{{margin:0;background:var(--card);border:2px solid var(--line);border-radius:14px;padding:12px}} .phone.is-chosen{{border-color:var(--accent)}}
.screen{{position:relative;height:240px;border-radius:18px;border:6px solid #222;overflow:hidden;background:{E(bg)}}}
.m-bar{{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:{E(color.get('secondary', '#222'))};color:#fff}}
.m-bar b{{width:56px;height:10px;background:#fff9;border-radius:3px}} .m-page i,.m-drop i,.m-side i,.m-full i{{display:block;height:9px;margin:9px 10px;background:#0002;border-radius:3px}}
.m-drop{{position:absolute;top:34px;left:0;right:0;background:#fff;box-shadow:0 6px 12px #0003;padding:2px 0}}
.m-shade{{position:absolute;inset:0;background:#0005}} .m-side{{position:absolute;top:0;bottom:0;right:0;width:70%;background:#fff;padding-top:30px}}
.m-full{{position:absolute;inset:34px 0 0;background:#fff;padding-top:14px}} .m-full i{{height:14px;margin:16px 18px}}
figcaption{{font-size:.85rem;color:var(--muted);margin-top:8px}} figcaption strong{{color:var(--ink)}}
.scroll{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;background:var(--card);font-size:.9rem}} th,td{{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}
@media (max-width:700px){{.sec{{grid-template-columns:1fr}} .scale{{grid-template-columns:1fr}}}}
@media print{{details{{break-inside:avoid}} body{{background:#fff}}}}
</style></head><body><main>
<h1>{E(project.get('name') or 'Projeto')} — aprovação</h1>
<p class="lead">Blueprint {E(str(meta.get('blueprint_version', '?')))} · gerado em {datetime.date.today().strftime('%d/%m/%Y')}</p>
<section class="card how"><b>Como aprovar:</b> confira as cores, as fontes, os botões e cada seção ao lado do recorte da sua referência.
Responda <b>"aprovado"</b>, ou diga o número do item que quer mudar. Nada abaixo foi construído ainda — mudar agora não custa retrabalho.
{f'<p class="note">{E(font_note)}</p>' if font_note else ''}</section>

<h2>1. Pontos para você confirmar ({len(pending)})</h2>
<section class="card"><ol class="pend">{''.join(f'<li>{p}</li>' for p in pending) or '<li>Nenhum.</li>'}</ol></section>

<h2>2. Cores</h2>
<ul class="swatches">{''.join(swatches)}</ul>

<h2>3. Fontes</h2>
{''.join(font_rows) or '<p>Fontes do sistema (sem fonte web).</p>'}
<h3>Tamanhos dos textos</h3>
<div class="preview">{scale}</div>

<h2>4. Botões</h2>
<div class="preview">{buttons}</div>

<h2>5. Páginas e seções (à esquerda, a sua referência)</h2>
{''.join(page_html)}

{f'<h2>6. Menu no celular</h2><p class="lead">A referência mostra só o computador. Estes são os desenhos possíveis:</p><div class="phones">{phones}</div>' if phones else ''}

<h2>7. Detalhes completos</h2>
<section class="card">{details_html}</section>
</main></body></html>
"""
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"Gerado: {out} ({out.stat().st_size // 1024} KB, {len(pending)} ponto(s) para confirmar)")


if __name__ == "__main__":
    main()
