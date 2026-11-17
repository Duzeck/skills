#!/usr/bin/env python3
"""
Captura deterministica do site local para o portao de QA visual
(references/validation-playbook.md): cada pagina em desktop 1440,
tablet 834 e mobile 390, com checagens tecnicas automaticas, e monta
imagens LADO A LADO referencia x implementacao para a comparacao.

Uso:
    python capture_site.py --base http://localhost/<slug>/ \
        --blueprint <projeto>/documentation/BLUEPRINT.yaml \
        --out <projeto>/documentation/qa/rodada-1 \
        [--extra projetos/residencia-alphaville] \
        [--ref home=refs/home-desktop.png --ref home@mobile=refs/home-mobile.png]

    --pages "home,sobre"  alternativa a --blueprint (slugs; "home" = raiz).
                          No Git Bash evite caminhos com barra inicial: o
                          MSYS converte "/" em "C:/Program Files/Git/".
    --viewports desktop,mobile   subconjunto (padrao: os tres)
    --no-axe / --no-links        pula acessibilidade / checagem de links

Saidas em --out:
    <pagina>-<viewport>.png         captura full-page
    compare-<pagina>-<viewport>-NN.png  referencia | implementacao, em
                                        fatias legiveis (use Read nelas)
    report.json / report.md         evidencia tecnica por pagina x viewport

--ref mapeia a pagina (pages[].id OU slug, ex.: about ou sobre) para a imagem de
referencia daquele breakpoint; sem "@viewport" vale para desktop. Se a
referencia for uma colagem de varias paginas, recorte antes com
scripts/crop_reference.py.

Exit code:
    0  capturas feitas e nenhum candidato a P0 tecnico
    1  capturas feitas, mas ha candidato a P0 (rolagem horizontal, HTTP de
       erro na pagina, erro de JS, imagem quebrada) - ver report.md
    2  captura impossivel (site fora do ar, Playwright ausente) - o portao
       de QA fica `blocked`, nunca "validado"

Isto NAO substitui o julgamento visual: as checagens automaticas pegam
quebras tecnicas; fidelidade a referencia continua sendo a comparacao
das imagens compare-*.png registrada no ledger do VALIDATION.md.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

# Console do Windows usa cp1252 por padrao e corrompe acentos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).resolve().parent
RUNNER = SCRIPT_DIR / "capture_site.mjs"
VIEWPORTS = {
    "desktop": (1440, 900),
    "tablet": (834, 1112),
    "mobile": (390, 844),
}
COMPARE_PANEL_WIDTH = 720      # largura de cada lado na imagem comparativa
COMPARE_SLICE_HEIGHT = 1400    # altura maxima de cada fatia comparativa


def page_id_from_path(path):
    slug = path.strip("/").replace("/", "-")
    return slug or "home"


def normalize_path(raw):
    """Aceita '/', 'home', 'sobre', '/sobre/', 'projetos/casa-x'."""
    p = raw.strip()
    if re.match(r"^[A-Za-z]:[\\/]", p):
        print(f"Erro: caminho '{p}' parece ter sido convertido pelo Git Bash (MSYS). "
              "Use slugs sem barra inicial (ex.: --pages \"home,sobre\"), "
              "--blueprint, ou prefixe o comando com MSYS_NO_PATHCONV=1.")
        sys.exit(2)
    if p in ("", "/", "home"):
        return "/"
    return "/" + p.strip("/") + "/"


def load_blueprint(path):
    try:
        import yaml
    except ImportError:
        print("Erro: PyYAML nao esta instalado. Rode: pip install pyyaml")
        sys.exit(2)
    with open(path, "r", encoding="utf-8") as f:
        bp = yaml.safe_load(f) or {}
    return bp.get("blueprint", bp)


def norm_text(s):
    return re.sub(r"\s+", " ", str(s)).strip().casefold()


def check_copy(bp, report):
    """Cada texto real do inventario copy tem de aparecer LITERALMENTE
    (acentos inclusos) na pagina renderizada em desktop. Retorna lista de
    (pagina, id, texto) ausentes."""
    texts = {c["page"]: norm_text(c.get("text", "")) for c in report["captures"]
             if c["viewport"] == "desktop" and c.get("text")}
    if not texts:
        return []
    missing = []
    for entry in bp.get("copy") or []:
        if entry.get("source") not in {"reference_file", "user"}:
            continue
        page = entry.get("page")
        target = "home" if page in (None, "global") else page
        if target not in texts:
            continue
        parts = [p for p in re.split(r"\s+·\s+", str(entry.get("text", ""))) if p.strip()]
        absent = [p for p in parts if norm_text(p) not in texts[target]]
        if absent:
            missing.append((target, entry.get("id", "?"), " · ".join(absent)))
    return missing


def header_is_sticky(bp):
    """single_page sempre tem header sticky (references/navigation.md)."""
    return ((bp.get("project") or {}).get("site_structure") == "single_page"
            or (bp.get("theme") or {}).get("header_behavior") == "sticky")


def pages_from_blueprint(path):
    bp = load_blueprint(path)
    pages = []
    for p in bp.get("pages") or []:
        # capture_path: exemplo concreto para templates com slug variavel
        # (ex.: slug "servicos/<servico>" + capture_path "servicos/cabelos").
        slug = str(p.get("capture_path") or p.get("slug") or "").strip("/")
        if "<" in slug or "{" in slug:
            print(f"Aviso: pagina '{p.get('id')}' tem slug variavel ({slug}) e nao tem "
                  "capture_path - nao sera capturada.", file=sys.stderr)
            continue
        section_ids = {s.get("id") for s in (p.get("sections") or [])}
        carousels = {c["id"]: {k: c.get(k) for k in ("slide_count", "autoplay", "controls")}
                     for c in (bp.get("carousels") or []) if c.get("id") and c.get("section") in section_ids}
        forms = {f["id"]: {"submit_label": f.get("submit_label"),
                           "fields": [{k: fld.get(k) for k in ("name", "type", "required", "placeholder")}
                                      for fld in f.get("fields") or [] if isinstance(fld, dict)]}
                 for f in (bp.get("forms") or []) if isinstance(f, dict) and f.get("id")
                 and f.get("section") in section_ids and isinstance((f.get("fields") or [None])[0], dict)}
        maps = {m["id"]: {"load": m.get("load", "click"), "directions_link": m.get("directions_link")}
                for m in (bp.get("maps") or []) if m.get("id") and m.get("section") in section_ids}
        galleries = {g["id"]: {k: g.get(k) for k in ("visible_count", "total_count", "lightbox")}
                     for g in (bp.get("galleries") or []) if g.get("id") and g.get("section") in section_ids}
        videos = {v["id"]: {k: v.get(k) for k in ("kind", "captions")}
                  for v in (bp.get("videos") or []) if v.get("id") and v.get("section") in section_ids}
        accordions = {a["id"]: {k: a.get(k) for k in ("item_count", "open_in_reference", "exclusive", "faq", "structured_data")}
                      for a in (bp.get("accordions") or []) if a.get("id") and a.get("section") in section_ids}
        tabs = {t["id"]: {k: t.get(k) for k in ("tab_count", "active_in_reference", "mobile")}
                for t in (bp.get("tabs") or []) if t.get("id") and t.get("section") in section_ids}
        seo_page = next((s for s in (bp.get("seo") or {}).get("pages") or []
                         if isinstance(s, dict) and s.get("page") == p.get("id")), {})
        pages.append({"id": p.get("id") or page_id_from_path(slug), "path": f"/{slug}/" if slug else "/",
                      "seo": {"description": seo_page.get("description"), "noindex": seo_page.get("noindex") is True},
                      "carousels": carousels, "forms": forms, "maps": maps,
                      "galleries": galleries, "videos": videos, "accordions": accordions, "tabs": tabs,
                      "tables": {t["id"]: {k: t.get(k) for k in ("row_count", "columns", "mobile")}
                                 for t in (bp.get("tables") or []) if t.get("id") and t.get("section") in section_ids},
                      "pricing": {x["id"]: {k: x.get(k) for k in ("plan_count", "billing", "default_billing", "featured_plan")}
                                  for x in (bp.get("pricing") or []) if x.get("id") and x.get("section") in section_ids},
                      "testimonials": {x["id"]: {k: x.get(k) for k in ("item_count", "fields_shown")}
                                       for x in (bp.get("testimonials") or []) if x.get("id") and x.get("section") in section_ids},
                      "client_logos": {x["id"]: {k: x.get(k) for k in ("logo_count", "layout")}
                                       for x in (bp.get("client_logos") or []) if x.get("id") and x.get("section") in section_ids},
                      "hero": next(({"buttons": [b.get("label") for b in h.get("buttons") or [] if isinstance(b, dict)],
                                     "breadcrumb": h.get("breadcrumb")}
                                    for h in (bp.get("heroes") or []) if h.get("section") in section_ids), None),
                      "team": {x["id"]: {k: x.get(k) for k in ("member_count", "fields_shown")}
                               for x in (bp.get("team") or []) if x.get("id") and x.get("section") in section_ids},
                      "stats": {x["id"]: {k: x.get(k) for k in ("item_count", "count_up")}
                                for x in (bp.get("stats") or []) if x.get("id") and x.get("section") in section_ids}})
    return pages


def ref_for(refs, cap):
    """--ref aceita o id da pagina (pages[].id) ou o slug do caminho."""
    for name in (cap["page"], page_id_from_path(cap.get("path", ""))):
        if (name, cap["viewport"]) in refs:
            return refs[(name, cap["viewport"])]
    return None


def check_prereqs(base):
    if not shutil.which("node"):
        print("BLOQUEADO: Node.js nao encontrado no PATH.")
        sys.exit(2)
    npm = shutil.which("npm")
    root = subprocess.run([npm, "root", "-g"], capture_output=True, text=True).stdout.strip() if npm else ""
    if not root or not (Path(root) / "playwright").exists() or not (Path(root) / "axe-core").exists():
        print("BLOQUEADO: Playwright/axe-core globais ausentes. Rode:\n"
              "  npm i -g playwright axe-core && playwright install chromium")
        sys.exit(2)
    try:
        urllib.request.urlopen(base, timeout=15)
    except urllib.error.HTTPError:
        pass  # o servidor respondeu; o status por pagina vai para o relatorio
    except (urllib.error.URLError, OSError) as exc:
        print(f"BLOQUEADO: {base} nao responde ({exc}). O WAMP esta ligado?")
        sys.exit(2)
    return root


def parse_refs(values):
    refs = {}
    for item in values or []:
        key, _, path = item.partition("=")
        page, _, vp = key.partition("@")
        if not path or not Path(path).exists():
            print(f"Aviso: referencia ignorada (arquivo inexistente): {item}")
            continue
        refs[(page, vp or "desktop")] = Path(path)
    return refs


def build_compare(ref_path, shot_path, out_dir, stem):
    """Referencia | implementacao na mesma largura, fatiadas para leitura."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("Aviso: Pillow ausente - comparativos nao gerados (pip install pillow).")
        return []

    def fit(img):
        img = img.convert("RGB")
        h = round(img.height * COMPARE_PANEL_WIDTH / img.width)
        return img.resize((COMPARE_PANEL_WIDTH, h), Image.LANCZOS)

    ref, shot = fit(Image.open(ref_path)), fit(Image.open(shot_path))
    header, gap = 28, 16
    total_h = max(ref.height, shot.height)
    outputs = []
    for n, top in enumerate(range(0, total_h, COMPARE_SLICE_HEIGHT), 1):
        h = min(COMPARE_SLICE_HEIGHT, total_h - top)
        canvas = Image.new("RGB", (COMPARE_PANEL_WIDTH * 2 + gap, h + header), "white")
        draw = ImageDraw.Draw(canvas)
        draw.text((8, 8), f"REFERENCIA  ({ref_path.name})", fill="black")
        draw.text((COMPARE_PANEL_WIDTH + gap + 8, 8), f"IMPLEMENTACAO  ({shot_path.name})", fill="black")
        for x, img in ((0, ref), (COMPARE_PANEL_WIDTH + gap, shot)):
            if top < img.height:
                canvas.paste(img.crop((0, top, COMPARE_PANEL_WIDTH, min(top + h, img.height))), (x, header))
        draw.line([(COMPARE_PANEL_WIDTH + gap // 2, 0), (COMPARE_PANEL_WIDTH + gap // 2, h + header)], fill="red", width=2)
        name = f"compare-{stem}-{n:02d}.png"
        canvas.save(out_dir / name)
        outputs.append(name)
    return outputs


def write_visual_approval(report, out_dir, compares):
    """aprovacao-visual.html: a fatia critica (ou o site) ao lado da referencia,
    para o CLIENTE aprovar antes de propagar o sistema (references/approval-protocol.md).
    Imagens por caminho relativo: envie a pasta da rodada inteira."""
    import html as _html
    blocks = []
    for cap in report["captures"]:
        imgs = compares.get((cap["page"], cap["viewport"])) or []
        if not imgs:
            continue
        pend = [i for i in p0_candidates(cap) if not i.startswith("(P2)")]
        state = (f'<p class="warn">{len(pend)} ajuste(s) técnico(s) ainda em correção - não precisa avaliá-los.</p>'
                 if pend else '<p class="ok">Sem pendência técnica.</p>')
        blocks.append(f'<section><h2>{_html.escape(cap["page"])} — {_html.escape(cap["viewport"])} ({cap["width"]}px)</h2>{state}'
                      + "".join(f'<img src="{_html.escape(i)}" alt="Referência à esquerda, site à direita">' for i in imgs)
                      + "</section>")
    if not blocks:
        return None
    import datetime as _dt
    try:
        when = _dt.datetime.fromisoformat(report["generatedAt"].replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
    except ValueError:
        when = report["generatedAt"]
    page = ("<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            "<title>Aprovação visual</title><style>body{margin:0;background:#f6f6f4;color:#1d1d1f;font:16px/1.5 system-ui,sans-serif}"
            "main{max-width:1200px;margin:0 auto;padding:24px 16px 64px}section{background:#fff;border:1px solid #e3e3df;border-radius:12px;"
            "padding:16px;margin:16px 0}img{display:block;width:100%;height:auto;margin:8px 0;border:1px solid #e3e3df}"
            ".ok{color:#1b6e2a}.warn{color:#8a5300}.how{border-left:4px solid #8a5300}</style></head><body><main>"
            f"<h1>Aprovação visual</h1><p>{_html.escape(report['base'])} · {_html.escape(when)}</p>"
            "<section class=\"how\"><b>Como aprovar:</b> à esquerda, a sua referência; à direita, o site já funcionando no WordPress "
            "(textos e imagens vêm do painel). Responda <b>\"aprovado\"</b> ou descreva o que está diferente. Depois da sua "
            "aprovação, o mesmo padrão é aplicado às demais seções e páginas.</section>"
            + "".join(blocks) + "</main></body></html>")
    path = out_dir / "aprovacao-visual.html"
    path.write_text(page, encoding="utf-8")
    return path


def p0_candidates(cap):
    issues = []
    if cap.get("captureError"):
        issues.append(f"captura falhou: {cap['captureError']}")
    if cap.get("status") and cap["status"] >= 400:
        issues.append(f"pagina respondeu HTTP {cap['status']}")
    if cap.get("horizontalOverflow"):
        issues.append(f"rolagem horizontal ({cap['scrollWidth']}px > {cap['viewportWidth']}px): "
                      + ", ".join(cap.get("overflowOffenders") or []))
    if cap.get("brokenImages"):
        issues.append(f"{len(cap['brokenImages'])} imagem(ns) quebrada(s)")
    nav_empty = [l["text"] or "?" for l in cap.get("emptyLinks") or [] if l.get("inNav")]
    if nav_empty:
        issues.append(f"{len(nav_empty)} link(s) de menu/cabecalho sem destino: " + ", ".join(sorted(set(nav_empty))))
    nav = cap.get("navigation") or {}
    if nav.get("stickyFailures"):
        issues.append("header sticky some ao rolar: " + ", ".join(nav["stickyFailures"]))
    if nav.get("missingAnchors"):
        issues.append(f"{len(nav['missingAnchors'])} ancora(s) do menu sem secao: " + ", ".join(nav["missingAnchors"]))
    if nav.get("obscuredAnchors"):
        issues.append("(P1) destino de ancora encoberto pelo header: " + ", ".join(nav["obscuredAnchors"]))
    for kind, label in (("forms", "formulario"), ("maps", "mapa"), ("galleries", "galeria"), ("videos", "video"),
                        ("accordions", "acordeao"), ("tabs", "abas"), ("tables", "tabela"), ("pricing", "precos"),
                        ("testimonials", "depoimentos"), ("client_logos", "logos"),
                        ("team", "equipe"), ("stats", "numeros"), ("blog", "blog"), ("footer", "rodape"),
                        ("header", "header"), ("hero", "hero"), ("seo", "seo"), ("fonts", "fontes"),
                        ("layout_shift", "estabilidade"), ("performance", "desempenho"), ("images", "imagens")):
        for item in cap.get(kind) or []:
            for issue in item.get("issues") or []:
                prefix = "" if issue.startswith(("ausente", "envio nao concluido")) else "(P1) "
                issues.append(f"{prefix}{label} {item['id']}: {issue}")
    for car in cap.get("carousels") or []:
        for issue in car.get("issues") or []:
            prefix = "" if issue.startswith("ausente") else "(P1) "
            issues.append(f"{prefix}carrossel {car['id']}: {issue}")
    js = [e for e in cap.get("consoleErrors") or [] if e.startswith("[pageerror]")]
    if js:
        issues.append(f"{len(js)} erro(s) de JavaScript")
    return issues


# Mesma lista de project_ai_bots() (theme-skeleton/inc/seo.php).
AI_TRAINING_BOTS = ["GPTBot", "ClaudeBot", "anthropic-ai", "Google-Extended", "Applebot-Extended", "CCBot",
                    "Bytespider", "meta-externalagent", "cohere-training-data-crawler", "Diffbot"]
AI_SEARCH_BOTS = ["OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User", "PerplexityBot",
                  "Perplexity-User", "DuckAssistBot", "meta-externalfetcher"]


def parse_robots(text):
    """{user-agent (minusculo): [(diretiva, caminho)]} - grupos RFC 9309."""
    groups, current, last_was_ua = {}, [], False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (x.strip() for x in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if not last_was_ua:
                current = []
            current.append(value.lower())
            groups.setdefault(value.lower(), [])
            last_was_ua = True
        elif key in ("allow", "disallow"):
            for ua in current:
                groups[ua].append((key, value))
            last_was_ua = False
    return groups


def blocked_root(rules):
    return any(k == "disallow" and v == "/" for k, v in rules)


def check_robots(base, policy):
    """robots.txt real x Blueprint (references/security-seo.md secao 4).
    Retorna (issues, texto). Issue sem '(P1)'/'(P2)' = P0."""
    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "qa-capture"})
        with urllib.request.urlopen(req, timeout=20) as res:
            body = res.read(200_000).decode("utf-8", "replace")
            return body if "<html" not in body[:500].lower() else None

    issues = []
    try:
        text = get(base.rstrip("/") + "/robots.txt")
    except (urllib.error.URLError, OSError):
        text = None
    if text is None:
        # WordPress em subpasta (localhost/<slug>/) nao responde /robots.txt -
        # so na raiz do dominio, onde o robots.txt vale. Mesmo conteudo via ?robots=1.
        try:
            text = get(base.rstrip("/") + "/?robots=1")
        except (urllib.error.URLError, OSError) as err:
            return [f"(P1) robots.txt nao abre ({err})"], ""
        if text is None:
            return ["(P1) robots.txt nao abre (nem /robots.txt nem ?robots=1)"], ""
        issues.append("(P2) robots.txt lido via ?robots=1: instalacao em subpasta - o robots.txt so vale na raiz do dominio (producao)")
    groups = parse_robots(text)
    star = groups.get("*", [])
    if blocked_root(star):
        issues.append("robots.txt bloqueia o site inteiro (User-agent: * / Disallow: /) - Configuracoes > Leitura "
                      "'Evitar mecanismos de busca' ligado ou robots.txt fisico errado")
    for bot in ("googlebot", "bingbot"):
        if blocked_root(groups.get(bot, [])):
            issues.append(f"robots.txt bloqueia o {bot} - o site some da busca")
    if "sitemap:" not in text.lower():
        issues.append("(P2) robots.txt sem a linha Sitemap:")
    if policy:
        want_train = policy in ("block_training", "block_all")
        want_search = policy == "block_all"
        for bots, want, label in ((AI_TRAINING_BOTS, want_train, "treino"), (AI_SEARCH_BOTS, want_search, "busca")):
            wrong = [b for b in bots if blocked_root(groups.get(b.lower(), [])) != want]
            if wrong:
                verb = "deveria bloquear" if want else "bloqueia"
                issues.append(f"(P1) robots.txt {verb} robos de IA de {label} (Blueprint: {policy}): {', '.join(wrong)}")
        m = re.search(r"^content-signal:\s*(.+)$", text, re.I | re.M)
        want_sig = {"search": "yes", "ai-input": "no" if want_search else "yes", "ai-train": "no" if want_train else "yes"}
        if not m:
            issues.append("(P2) robots.txt sem Content-Signal (a politica de IA dita em palavras)")
        else:
            got = dict(p.strip().split("=", 1) for p in m.group(1).split(",") if "=" in p)
            diff = [f"{k}={got.get(k, '?')} (esperado {v})" for k, v in want_sig.items() if got.get(k) != v]
            if diff:
                issues.append(f"(P1) Content-Signal contradiz o Blueprint ({policy}): {', '.join(diff)}")
    return issues, text


def add_seo_issues(report):
    """Titulo/descricao repetidos entre paginas indexaveis: o Google trata
    como a mesma pagina e escolhe uma (references/security-seo.md)."""
    seen = {"title": {}, "description": {}}
    for cap in report["captures"]:
        for s in cap.get("seo") or []:
            if s.get("noindex"):
                continue
            for key in seen:
                value = (s.get(key) or "").strip().lower()
                if value:
                    seen[key].setdefault(value, []).append((cap, s))
    for key, label in (("title", "titulo repetido"), ("description", "descricao repetida")):
        for value, hits in seen[key].items():
            if len(hits) > 1:
                pages = ", ".join(c["page"] for c, _ in hits)
                for _cap, s in hits:
                    s.setdefault("issues", []).append(f"{label} em {len(hits)} paginas ({pages})")


def _luminance(rgb):
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def add_contrast_issues(report, out_dir):
    """Contraste do texto sobre a foto (WCAG 1.4.3), medido nos recortes que o
    executor salvou com o texto escondido. Pior caso: para texto claro, o
    trecho MAIS CLARO do fundo (percentil 90); para texto escuro, o mais escuro
    (percentil 10). Minimo 4,5:1; 3:1 para texto grande (>=24px, ou >=18,66px
    em negrito)."""
    try:
        from PIL import Image
    except ImportError:
        return
    for cap in report["captures"]:
        for check in cap.get("hero") or []:
            for t in check.get("contrast") or []:
                path = out_dir / t["file"]
                nums = re.findall(r"[\d.]+", t.get("color", ""))
                if not path.exists() or len(nums) < 3:
                    continue
                text_l = _luminance(tuple(float(n) for n in nums[:3]))
                img = Image.open(path).convert("RGB")
                img.thumbnail((200, 200))
                lums = sorted(_luminance(px) for px in img.getdata())
                if not lums:
                    continue
                median = lums[len(lums) // 2]
                bg = lums[int(len(lums) * 0.9)] if text_l > median else lums[int(len(lums) * 0.1)]
                ratio = (max(text_l, bg) + 0.05) / (min(text_l, bg) + 0.05)
                large = t.get("size", 0) >= 24 or (t.get("size", 0) >= 18.66 and t.get("weight", 400) >= 700)
                minimum = 3.0 if large else 4.5
                t["ratio"] = round(ratio, 2)
                if ratio < minimum:
                    check["issues"].append(
                        f"contraste {ratio:.1f}:1 do texto \"{t.get('label', '')}\" sobre a imagem (minimo {minimum:g}:1) - "
                        "aumente a camada (overlay) ou mude a cor"
                    )


def check_mail_log(args, report, mail_dir, before):
    """Com --submit-forms + --mail-log: cada envio 'sent' gerou um e-mail
    para o destinatario do Blueprint (mu-plugin project-local-mail)."""
    if not (args.submit_forms and mail_dir):
        return None
    sent = [(c["page"], f["id"]) for c in report["captures"] for f in c.get("forms") or [] if f.get("status") == "sent"]
    if not sent:
        return []
    if not mail_dir.is_dir():
        return [f"pasta do log de e-mail nao existe: {mail_dir} (mu-plugin project-local-mail ativo? WP_ENVIRONMENT_TYPE=local?)"]
    new = sorted(set(mail_dir.glob("*.json")) - before)
    issues = []
    if len(new) < len(sent):
        issues.append(f"{len(sent)} envio(s) com sucesso, mas so {len(new)} e-mail(s) no log")
    if args.blueprint:
        bp = load_blueprint(args.blueprint)
        dests = {f.get("id"): str(f.get("destination") or "").lower() for f in bp.get("forms") or [] if isinstance(f, dict)}
        recipients = set()
        for mail in new:
            try:
                data = json.loads(mail.read_text(encoding="utf-8"))
                recipients |= {str(t).lower() for t in data.get("to") or []}
            except (OSError, ValueError):
                issues.append(f"e-mail ilegivel no log: {mail.name}")
        for _page, fid in sent:
            if dests.get(fid) and not any(dests[fid] in r for r in recipients):
                issues.append(f"formulario {fid}: nenhum e-mail para {dests[fid]} (destinatario no CF7 difere do Blueprint?)")
    return issues


def write_markdown(report, out_dir, compares, missing_copy=None, mail_issues=None):
    lines = [f"# Captura de QA - {report['base']}", "", f"Gerado em {report['generatedAt']}.", ""]
    lines += ["## Evidencia por pagina x viewport", "",
              "| Pagina | Viewport | HTTP | Captura | Comparativo | Candidatos a P0 |",
              "|---|---|---|---|---|---|"]
    total_p0 = 0
    for cap in report["captures"]:
        issues = p0_candidates(cap)
        total_p0 += len(issues)
        comp = ", ".join(compares.get((cap["page"], cap["viewport"]), [])) or "-"
        lines.append(f"| {cap['page']} | {cap['viewport']} ({cap['width']}) | {cap.get('status', '-')} | "
                     f"{cap.get('screenshot', '-')} | {comp} | {'; '.join(issues) or 'nenhum'} |")

    if missing_copy is not None:
        lines += ["", "## Textos da referencia (inventario copy) ausentes ou alterados", ""]
        if missing_copy:
            lines.append("Cada item e candidato a **P1** (texto reescrito, sem acento ou elemento ausente):")
            lines.append("")
            lines += [f"- **{page}** `{cid}`: \"{text}\"" for page, cid, text in missing_copy]
        else:
            lines.append("Todos os textos da referencia aparecem literalmente nas paginas.")
        total_p0 += len(missing_copy)

    if mail_issues is not None:
        lines += ["", "## Envio de formularios (log de e-mail local)", ""]
        lines += [f"- **P0** {i}" for i in mail_issues] or ["Cada envio gerou e-mail para o destinatario do Blueprint."]
        total_p0 += len(mail_issues)

    seo_rows = [(cap, s) for cap in report["captures"] for s in cap.get("seo") or []]
    if seo_rows:
        lines += ["", "## SEO por pagina (titulo, descricao, recomendacoes P2)", "",
                  "| Pagina | Titulo | Descricao | Recomendacoes |", "|---|---|---|---|"]
        for cap, s in seo_rows:
            desc = s.get("description") or ""
            lines.append(f"| {cap['page']}{' (noindex)' if s.get('noindex') else ''} | {s.get('title') or '-'} ({len(s.get('title') or '')}) | "
                         f"{desc[:70]}{'...' if len(desc) > 70 else ''} ({len(desc)}) | {'; '.join(s.get('notes') or []) or '-'} |")

    if "robots" in report:
        lines += ["", f"## robots.txt (robos de IA no Blueprint: {report.get('robotsPolicy') or 'nao declarado'})", ""]
        robots = report["robots"]
        lines += [f"- {'**P0** ' if not i.startswith('(P') else ''}{i}" for i in robots] or \
            ["Conforme: buscadores liberados, Sitemap presente e robos de IA como o Blueprint decide."]
        total_p0 += sum(1 for i in robots if not i.startswith("(P2)"))

    perf_rows = [(cap, p, (cap.get("images") or [{}])[0]) for cap in report["captures"] for p in cap.get("performance") or []]
    if perf_rows:
        lines += ["", "## Desempenho e imagens (medido no ambiente local - para achar excessos e comparar antes/depois)", "",
                  "| Pagina | TTFB | FCP | LCP | Peso | Arquivos | HTML | JS/CSS/img/fonte (KB) | Imagens | Recomendacoes |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for cap, p, img in perf_rows:
            t = p.get("byType") or {}
            recs = (p.get("notes") or []) + (img.get("notes") or [])
            lines.append(f"| {cap['page']}@{cap['viewport']} | {p.get('ttfb')} ms | {p.get('fcp')} ms | {p.get('lcp')} ms | "
                         f"{p.get('kb')} KB | {p.get('requests')} | {p.get('dom')} el. | "
                         f"{t.get('js', 0)}/{t.get('css', 0)}/{t.get('img', 0)}/{t.get('font', 0)} | "
                         f"{img.get('count', 0)} ({img.get('kb', 0)} KB) | {'; '.join(recs[:6]) or '-'} |")

    font_rows = [(cap, f) for cap in report["captures"] for f in cap.get("fonts") or []]
    cls_rows = [(cap, c) for cap in report["captures"] for c in cap.get("layout_shift") or []]
    if font_rows or cls_rows:
        lines += ["", "## Fontes e estabilidade do layout", "",
                  "| Pagina | Fontes usadas | Arquivos | KB | Preload | Recomendacoes |", "|---|---|---|---|---|---|"]
        for cap, f in font_rows:
            lines.append(f"| {cap['page']} | {', '.join(f.get('used') or []) or '-'} | {f.get('files', 0)} | {f.get('kb', 0)} | "
                         f"{f.get('preloads', 0)} | {'; '.join(f.get('notes') or []) or '-'} |")
        if cls_rows:
            lines += ["", "CLS ao carregar (bom: ate 0,1): " + ", ".join(
                f"{cap['page']}@{cap['viewport']} {c.get('cls', 0):.3f}" for cap, c in cls_rows)]
        for swap in report.get("fontSwap") or []:
            if swap.get("error"):
                lines.append(f"\nTroca de fonte ({swap['page']} @ {swap['viewport']}): falhou - {swap['error']}")
                continue
            detail = ", ".join(f"{i['el']} {i['bottomDelta']:+d}px ({i['linesFallback']}->{i['linesWeb']} linhas, largura {i['widthDeltaPct']:+d}%)"
                               for i in swap.get("items") or [])
            lines.append(f"\nTroca de fonte ({swap['page']} @ {swap['viewport']}, reserva -> fonte): {detail}; "
                         f"pagina {swap.get('docDelta', 0):+d}px. {'; '.join(swap.get('notes') or []) or 'Sem salto perceptivel.'}")

    lines += ["", "## Erros de console e requisicoes com falha", ""]
    any_err = False
    for cap in report["captures"]:
        errs = (cap.get("consoleErrors") or []) + (cap.get("httpErrors") or [])
        if errs:
            any_err = True
            lines.append(f"- **{cap['page']} @ {cap['viewport']}**")
            lines += [f"  - `{e[:200]}`" for e in errs[:10]]
    if not any_err:
        lines.append("Nenhum.")

    lines += ["", "## Acessibilidade (axe, WCAG 2 A/AA)", ""]
    any_axe = False
    for cap in report["captures"]:
        for v in cap.get("axe") or []:
            any_axe = True
            lines.append(f"- **{cap['page']} @ {cap['viewport']}** [{v['impact']}] `{v['id']}`: "
                         f"{v['help']} ({v['nodes']} elemento(s), ex.: `{v['example']}`)")
    if not any_axe:
        lines.append("Nenhuma violacao (ou axe desativado).")

    other_empty = sorted({l["text"] or "?" for c in report["captures"] if c["viewport"] == "desktop"
                          for l in c.get("emptyLinks") or [] if not l.get("inNav")})
    lines += ["", "## Links sem destino fora do menu (href vazio ou #)", ""]
    lines += [f"- {t} (registre como provisorio ou defina o destino)" for t in other_empty] or ["Nenhum."]

    lines += ["", f"## Links internos ({report.get('linksChecked', 0)} checados)", ""]
    lines += [f"- {b}" for b in report.get("brokenLinks") or []] or ["Nenhum link quebrado."]
    if report.get("errors"):
        lines += ["", "## Falhas do executor", ""] + [f"```\n{e}\n```" for e in report["errors"]]
    lines += ["", "> Checagens automaticas pegam quebras tecnicas. Fidelidade visual exige "
              "comparar as imagens compare-*.png e registrar no ledger do VALIDATION.md."]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return total_p0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="URL base do site local")
    ap.add_argument("--out", required=True, help="pasta de saida (ex.: documentation/qa/rodada-1)")
    ap.add_argument("--blueprint", help="BLUEPRINT.yaml para ler pages[].slug")
    ap.add_argument("--pages", help="lista de caminhos separados por virgula")
    ap.add_argument("--extra", action="append", default=[], help="caminho adicional (repetivel)")
    ap.add_argument("--viewports", default="desktop,tablet,mobile")
    ap.add_argument("--ref", action="append", help="pagina[@viewport]=imagem de referencia (repetivel)")
    ap.add_argument("--no-axe", action="store_true")
    ap.add_argument("--no-links", action="store_true")
    ap.add_argument("--submit-forms", action="store_true",
                    help="preenche e envia cada formulario do Blueprint (desktop) e le o status do CF7")
    ap.add_argument("--mail-log", help="pasta do log de e-mail local (wp-content/local-mail) para conferir o envio")
    ap.add_argument("--sticky-header", action="store_true",
                    help="checar header sticky sem --blueprint (com --blueprint vem de site_structure/header_behavior)")
    args = ap.parse_args()

    sticky_header = args.sticky_header
    if args.blueprint:
        pages = pages_from_blueprint(args.blueprint)
        sticky_header = sticky_header or header_is_sticky(load_blueprint(args.blueprint))
    elif args.pages:
        paths = [normalize_path(p) for p in args.pages.split(",") if p.strip()]
        pages = [{"id": page_id_from_path(p), "path": p} for p in paths]
    else:
        ap.error("informe --blueprint ou --pages")
    pages += [{"id": page_id_from_path(p), "path": p} for p in map(normalize_path, args.extra)]

    unknown = [v for v in args.viewports.split(",") if v not in VIEWPORTS]
    if unknown:
        ap.error(f"viewport(s) desconhecido(s): {unknown} (validos: {list(VIEWPORTS)})")
    viewports = [{"name": v, "width": VIEWPORTS[v][0], "height": VIEWPORTS[v][1]}
                 for v in args.viewports.split(",")]

    npm_root = check_prereqs(args.base)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    config = {"base": args.base, "out": str(out_dir.resolve()), "pages": pages, "viewports": viewports,
              "axe": not args.no_axe, "checkLinks": not args.no_links, "maxLinks": 200,
              "stickyHeader": sticky_header, "submitForms": args.submit_forms}
    if args.blueprint:
        bp_full = load_blueprint(args.blueprint)
        seo = bp_full.get("seo") or {}
        config["seo"] = {"plugin": seo.get("plugin") or "none", "organization_type": seo.get("organization_type")}
        fonts = bp_full.get("fonts") or {}
        if fonts.get("delivery"):
            config["fonts"] = {"delivery": fonts.get("delivery"), "fallback_metrics": fonts.get("fallback_metrics") is True,
                               "families": [{"family": f.get("family"), "weights": f.get("weights") or []}
                                            for f in fonts.get("families") or [] if isinstance(f, dict) and f.get("family")]}
        announcement = next((b for b in bp_full.get("banners") or [] if isinstance(b, dict) and b.get("kind") == "announcement"), None)
        if announcement:
            config["announcement"] = {"dismissible": announcement.get("dismissible") is True}
        header = bp_full.get("header") or {}
        if header.get("layout"):
            primary = next((m for m in bp_full.get("menus") or [] if isinstance(m, dict)
                            and (m.get("location") == "primary" or m.get("id") == "primary")), {})
            config["header"] = {
                "menu_labels": [i.get("label") for i in primary.get("items") or [] if isinstance(i, dict)],
                "cta": (header.get("cta") or {}).get("label") if isinstance(header.get("cta"), dict) else None,
                "top_bar": header.get("top_bar") or [],
                "actions": header.get("actions") or [],
                "transparent": header.get("transparent") is True,
                "sticky": header_is_sticky(bp_full),
            }
        footer = bp_full.get("footer") or {}
        if footer.get("columns"):
            config["footer"] = {
                "columns": [{"id": c.get("id"), "title": c.get("title")} for c in footer["columns"] if isinstance(c, dict)],
                "privacy_link": (footer.get("legal") or {}).get("privacy_link") is True,
                "dynamic_year": "{ano}" in str(footer.get("copyright") or "{ano}"),
                "networks": (bp_full.get("social") or {}).get("networks") or [],
            }
        blog = bp_full.get("blog") or {}
        if blog.get("enabled"):
            config["blog"] = {"card_fields": blog.get("card_fields") or [],
                              "posts_per_page": blog.get("posts_per_page"),
                              "home_count": (blog.get("home_section") or {}).get("count")}
    mail_dir = Path(args.mail_log) if args.mail_log else None
    mail_before = set(mail_dir.glob("*.json")) if mail_dir and mail_dir.is_dir() else set()
    if sticky_header:
        print("Header sticky: checando visibilidade ao rolar e ancoras encobertas.")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(config, tmp)
    print(f"Capturando {len(pages)} pagina(s) x {len(viewports)} viewport(s)...")
    result = subprocess.run([shutil.which("node"), str(RUNNER), tmp.name],
                            env={**os.environ, "NPM_GLOBAL_ROOT": npm_root})
    Path(tmp.name).unlink(missing_ok=True)

    report_path = out_dir / "report.json"
    if result.returncode != 0 or not report_path.exists():
        print("BLOQUEADO: o executor Playwright falhou - veja a saida acima.")
        sys.exit(2)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    refs = parse_refs(args.ref)
    compares = {}
    for cap in report["captures"]:
        ref = ref_for(refs, cap)
        if ref and cap.get("screenshot"):
            compares[(cap["page"], cap["viewport"])] = build_compare(
                ref, out_dir / cap["screenshot"], out_dir, f"{cap['page']}-{cap['viewport']}")

    missing_copy = check_copy(load_blueprint(args.blueprint), report) if args.blueprint else None
    for cap in report["captures"]:
        cap.pop("text", None)   # nao inflar o report.json com o texto das paginas
    add_contrast_issues(report, out_dir)   # antes de gravar: as razoes medidas entram no report.json
    add_seo_issues(report)
    ai_policy = ((load_blueprint(args.blueprint).get("seo") or {}).get("ai_crawlers")) if args.blueprint else None
    report["robots"], _robots_text = check_robots(args.base, ai_policy)
    report["robotsPolicy"] = ai_policy
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    mail_issues = check_mail_log(args, report, mail_dir, mail_before)
    total_p0 = write_markdown(report, out_dir, compares, missing_copy, mail_issues)
    if missing_copy:
        print(f"{len(missing_copy)} texto(s) da referencia ausente(s) ou alterado(s) - ver report.md.")
    failed = [c for c in report["captures"] if c.get("captureError")]
    print(f"\nRelatorio: {out_dir / 'report.md'}")
    if compares:
        print(f"Comparativos gerados: {sum(len(v) for v in compares.values())} imagem(ns) compare-*.png")
        approval = write_visual_approval(report, out_dir, compares)
        if approval:
            print(f"Aprovacao visual para o cliente: {approval}")
    if failed and len(failed) == len(report["captures"]):
        print("BLOQUEADO: nenhuma captura foi concluida.")
        sys.exit(2)
    if total_p0:
        print(f"{total_p0} candidato(s) a P0 tecnico - registre no ledger e corrija antes de comparar detalhes.")
        sys.exit(1)
    print("Nenhum candidato a P0 tecnico. Proximo passo: comparar os compare-*.png e preencher o ledger.")
    sys.exit(0)


if __name__ == "__main__":
    main()
