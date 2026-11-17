#!/usr/bin/env python3
"""
Checagem tecnica basica de um tema WordPress antes da validacao visual:
- php -l (lint de sintaxe) em todos os arquivos .php
- presenca dos arquivos minimos esperados
- heuristica simples contra logica de CPT/taxonomia/ACF direto em
  functions.php (deveria estar em inc/, ver references/wordpress-architecture.md)
- dado global fixo no codigo (telefone, e-mail, link de WhatsApp, tel:/mailto:)
  fora da fonte unica de verdade (ACF Options Page)
- placeholder esquecido (Lorem Ipsum, {{MARCADOR}} de template)
- saida de campo ACF sem escape (the_field(), echo get_field()/project_field())

Uso:
    python check_theme.py <caminho/para/wp-content/themes/<slug>-theme>

Exit code 1 se houver erro de sintaxe PHP, arquivo minimo ausente, dado
global fixo no codigo, placeholder esquecido ou saida ACF sem escape.
Avisos de organizacao (heuristica de functions.php) nao bloqueiam o exit
code, mas sao impressos.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

# Console do Windows usa cp1252 por padrao e corrompe acentos dos textos do Blueprint.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


EXPECTED_FILES = ["style.css", "functions.php", "index.php"]
SUSPICIOUS_PATTERNS = [
    "register_post_type(", "register_taxonomy(", "acf_add_local_field_group(",
]


# Arquivos que SAO a fonte unica de verdade de dados globais (ou que
# semeiam essa fonte com conteudo demo) - podem conter telefone/e-mail.
GLOBAL_SOURCE_FILES = {"acf-options.php", "demo-content.php", "content-defaults.php"}

GLOBAL_DATA_PATTERNS = [
    ("telefone", re.compile(r"(?<![\w#])\(?\d{2}\)?[\s.-]?9?\d{4}[\s.-]\d{4}(?!\w)")),
    # Exclui nomes de arquivo de asset retina (logo@2x.png etc.).
    ("e-mail", re.compile(
        r"(?<![\w.+-])[\w.+-]+@(?!\d+x\.)[\w-]+\.[a-z]{2,}(?:\.[a-z]{2,})?(?![\w-])", re.I)),
    ("link de WhatsApp", re.compile(r"(wa\.me/|api\.whatsapp\.com/send)\S*\d{8,}", re.I)),
    ("link tel:/mailto:", re.compile(r"""href=["'](tel:\+?\d|mailto:[^<"'?]+@)""", re.I)),
]

PLACEHOLDER_PATTERNS = [
    ("Lorem Ipsum", re.compile(r"lorem\s+ipsum", re.I)),
    ("marcador de template {{...}}", re.compile(r"\{\{\s*[A-Z0-9_ |]+\s*\}\}")),
]

UNESCAPED_OUTPUT = re.compile(
    r"(?<![\w>])the_field\s*\(|(?<!\w)echo\s+(get_field|project_field|get_sub_field)\s*\("
)


# Palavras pt-BR frequentes em sites institucionais que so existem COM
# acento. Encontra-las sem acento em texto visivel indica copia "ASCII por
# seguranca" - proibido (SKILL.md -> Objetivo: espelho da referencia).
UNACCENTED_WORDS = re.compile(
    r"\b(servicos?|orcamentos?|solucoes|solucao|construcao|ampliacao|concepcao|"
    r"voce|voces|nao|rodape|seguranca|experiencia|transparencia|historias?|inicio|"
    r"conheca|goiania|residencia|proposito|satisfacao|duvidas|unico|"
    r"nos(?= somos)|configuracoes|informacoes|endereco|area|politica|"
    r"tambem|ja|ate|apos|agua|pagina|numero|codigo|descricao|"
    r"credito|comercio|negocios?|tecnico|tecnica|projeto e unico)\b",
    re.I,
)
# Texto visivel: nos de texto HTML fora de <?php ?> e strings PHP com espaco
# (frases). Slugs/URLs nao tem espaco e ficam de fora.
HTML_TEXT = re.compile(r">([^<>]*[A-Za-z][^<>]*)<")
PHP_PHRASE = re.compile(r"""(['"])([^'"\n]*\s[^'"\n]*)\1""")


def visible_phrases(code):
    outside_php = re.sub(r"<\?php.*?(\?>|$)", lambda m: "\n" * m.group(0).count("\n"), code, flags=re.S)
    for lineno, line in enumerate(outside_php.splitlines(), 1):
        for m in HTML_TEXT.finditer(line):
            yield lineno, m.group(1)
    for lineno, line in enumerate(code.splitlines(), 1):
        for m in PHP_PHRASE.finditer(line):
            text = m.group(2)
            if "<" not in text and "(" not in text and "$" not in text:
                yield lineno, text


def blank_block_comments(code):
    """Remove comentarios /* */ mantendo a contagem de linhas."""
    return re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), code, flags=re.S)


def strip_php_comments(code):
    """Remove comentarios /* */, // e # mantendo a contagem de linhas."""
    code = blank_block_comments(code)
    # // e # fora de URL (ex.: https://) e fora de atributo PHP 8 (#[...]).
    return re.sub(r"(^|[^:])(//|#(?!\[)).*$", r"\1", code, flags=re.M)


def scan_lines(code, pattern):
    for lineno, line in enumerate(code.splitlines(), 1):
        match = pattern.search(line)
        if match:
            yield lineno, match.group(0).strip()


def check_content_guardrails(theme_dir, php_files, errors):
    for php_file in php_files:
        rel = php_file.relative_to(theme_dir)
        code = strip_php_comments(php_file.read_text(encoding="utf-8", errors="ignore"))

        if php_file.name not in GLOBAL_SOURCE_FILES:
            for label, pattern in GLOBAL_DATA_PATTERNS:
                for lineno, hit in scan_lines(code, pattern):
                    errors.append(
                        f"{rel}:{lineno} tem {label} fixo no codigo ({hit!r}). "
                        "Dado global deve vir da fonte unica de verdade "
                        "(project_get_global_setting() / ACF Options Page)."
                    )

        # Conteudo fixo no template: no de texto HTML com 2+ palavras fora de
        # <?php ?>. Todo conteudo visivel vem do admin (campo/opcao/CPT/menu);
        # mensagens de interface usam __()/esc_html_e(). inc/ fica de fora.
        if "inc" not in rel.parts:
            outside_php = re.sub(r"<\?php.*?(\?>|$)", lambda m: "\n" * m.group(0).count("\n"), code, flags=re.S)
            for lineno, line in enumerate(outside_php.splitlines(), 1):
                for m in HTML_TEXT.finditer(line):
                    text = re.sub(r"&#?\w+;", " ", m.group(1)).strip()  # entidades (&ldquo;) nao sao palavras
                    if len(re.findall(r"[^\W\d_]{2,}", text)) >= 2:
                        errors.append(
                            f"{rel}:{lineno} conteudo fixo no template ({text[:60]!r}). Todo texto "
                            "visivel deve vir do admin (campo ACF, opcao, CPT, menu); mensagem de "
                            "interface vai em esc_html_e()."
                        )

        seen_lines = set()
        for lineno, phrase in visible_phrases(code):
            words = sorted({w.lower() for w in UNACCENTED_WORDS.findall(phrase)})
            if words and lineno not in seen_lines:
                seen_lines.add(lineno)
                errors.append(
                    f"{rel}:{lineno} texto visivel sem acento ({', '.join(words)}): "
                    f"{phrase.strip()[:70]!r}. Copie o texto da referencia literalmente, em UTF-8."
                )

        for lineno, hit in scan_lines(code, UNESCAPED_OUTPUT):
            errors.append(
                f"{rel}:{lineno} imprime campo sem escape ({hit!r}). Use "
                "esc_html()/esc_url()/esc_attr() ou wp_kses_post() para WYSIWYG."
            )

    text_files = [f for f in theme_dir.rglob("*") if f.suffix in {".php", ".css", ".js"}]
    for text_file in text_files:
        rel = text_file.relative_to(theme_dir)
        content = text_file.read_text(encoding="utf-8", errors="ignore")
        if text_file.suffix == ".php":
            content = strip_php_comments(content)
        else:
            content = blank_block_comments(content)
        for label, pattern in PLACEHOLDER_PATTERNS:
            for lineno, hit in scan_lines(content, pattern):
                errors.append(f"{rel}:{lineno} tem placeholder esquecido: {label} ({hit!r}).")


NAV_CONSTANT = re.compile(r"define\('(PROJECT_SITE_STRUCTURE|PROJECT_HEADER_BEHAVIOR)',\s*'([a-z_]+)'\)")
CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
ROOT_SELECTOR = re.compile(r"(^|,)\s*(html|body|:root)\s*(?=,|$)")
OVERFLOW_BREAKS_STICKY = re.compile(r"overflow(-x|-y)?\s*:\s*(hidden|auto|scroll)", re.I)


THIRD_PARTY_SLIDERS = re.compile(
    r"\b(slick|owl\.?carousel|owlCarousel|swiper|flickity|glide(\.js)?|splide|tiny-slider|bxslider)\b", re.I)


HARDCODED_MAP = re.compile(r"<iframe[^>]+(google\.[a-z.]+/maps|openstreetmap\.org)", re.I)
HARDCODED_VIDEO_EMBED = re.compile(r"<iframe[^>]+(youtube(-nocookie)?\.com|youtu\.be|player\.vimeo\.com)", re.I)
AUTOPLAY_VIDEO = re.compile(r"<video\b[^>]*\bautoplay\b", re.I)
HARDCODED_CF7 = re.compile(r"\[contact-form-7[^\]]*\bid=[\"']?[0-9a-f]+", re.I)


def check_form_map_guardrails(theme_dir, errors):
    """Mapa e formulario nunca fixos no template (references/maps.md, forms.md):
    o endereco vem da pagina de opcoes e o mapa carrega pela fachada; o
    formulario vem de project_form() (o id do CF7 muda entre ambientes)."""
    for f in theme_dir.rglob("*.php"):
        code = strip_php_comments(f.read_text(encoding="utf-8", errors="ignore"))
        rel = f.relative_to(theme_dir)
        for lineno, _hit in scan_lines(code, HARDCODED_MAP):
            errors.append(
                f"{rel}:{lineno} iframe de mapa fixo no template - use template-parts/map.php "
                "(endereco da pagina de opcoes, carrega so no clique)."
            )
        for lineno, _hit in scan_lines(code, HARDCODED_VIDEO_EMBED):
            errors.append(
                f"{rel}:{lineno} player de YouTube/Vimeo fixo no template - use template-parts/video.php "
                "(URL editavel no admin, fachada: carrega so no clique, sem cookies)."
            )
        for lineno, _hit in scan_lines(code, AUTOPLAY_VIDEO):
            errors.append(
                f"{rel}:{lineno} <video autoplay> escrito a mao - video de fundo usa template-parts/video.php "
                "(kind background: respeita movimento reduzido, tem pausa e nao baixa no celular)."
            )
        for lineno, hit in scan_lines(code, HARDCODED_CF7):
            errors.append(
                f"{rel}:{lineno} shortcode do CF7 com id fixo ({hit!r}) - use project_form('<campo de opcoes>'); "
                "o id muda entre ambientes."
            )


ICON_FONT_CDN = re.compile(r"(font-?awesome|kit\.fontawesome\.com|use\.fontawesome\.com)", re.I)
UTC_YEAR = re.compile(r"\bdate\(\s*['\"]Y['\"]\s*\)")
THIRD_PARTY_SHARE = re.compile(r"(addthis|sharethis|connect\.facebook\.net|platform\.twitter\.com|addtoany)", re.I)
THIRD_PARTY_COUNTER = re.compile(r"\b(countUp|counterUp|jquery\.counterup|odometer|waypoints)\b", re.I)
THIRD_PARTY_DISCLOSURE = re.compile(
    r"data-bs-toggle=[\"'](collapse|tab)[\"']|\$\([^)]*\)\.(accordion|tabs)\(|role=[\"']tablist[\"']", re.I)


SELF_REVIEW_SCHEMA = re.compile(r"[\"']@type[\"']\s*(=>|:)\s*[\"'](Review|AggregateRating)[\"']", re.I)
HARDCODED_PRICE = re.compile(r"R\$\s*\d")
HAND_TABLE = re.compile(r"<table\b", re.I)


HOVER_SUBMENU = re.compile(r":hover\s*>\s*(ul|\.sub-menu|\.submenu|\.dropdown)", re.I)


VH_100 = re.compile(r"(min-)?height\s*:\s*100vh", re.I)
INLINE_BG_IMAGE = re.compile(r"style=[\"'][^\"']*background(-image)?\s*:[^\"']*url\(", re.I)


def check_hero_guardrails(theme_dir, warnings):
    """Hero (references/hero-banners.md): 100vh some atras da barra do
    navegador no celular; foto de fundo inline em CSS e descoberta tarde
    (nao vira LCP com prioridade, sem srcset)."""
    for css in theme_dir.rglob("*.css"):
        code = blank_block_comments(css.read_text(encoding="utf-8", errors="ignore"))
        for m in VH_100.finditer(code):
            # @supports not (1svh) com reserva em vh e permitido
            before = code[max(0, m.start() - 200):m.start()]
            if "@supports not" in before:
                continue
            lineno = code.count("\n", 0, m.start()) + 1
            warnings.append(f"{css.relative_to(theme_dir)}:{lineno} altura 100vh - no celular fica atras da barra do navegador; use 100svh/100dvh.")
            break
    for f in theme_dir.rglob("*.php"):
        code = strip_php_comments(f.read_text(encoding="utf-8", errors="ignore"))
        for lineno, _hit in scan_lines(code, INLINE_BG_IMAGE):
            warnings.append(
                f"{f.relative_to(theme_dir)}:{lineno} imagem como background-image inline - se for o hero, use <img> "
                "(template-parts/hero.php): descoberta cedo, srcset e fetchpriority high."
            )
            break


HARDCODED_SEO = re.compile(r"<meta\s+(name=[\"']description[\"']|property=[\"']og:)|<link\s+rel=[\"']canonical", re.I)
AUTHOR_LINK = re.compile(r"\b(the_author_posts_link|get_author_posts_url|the_author_link)\s*\(")


def check_seo_security_guardrails(theme_dir, warnings):
    """SEO e seguranca (references/security-seo.md): descricao/og/canonico
    escritos a mao no template duplicam (ou brigam com) inc/seo.php e com
    plugins de SEO; link para a pagina do autor vira 404 com a protecao
    (e revela o login) - so com a excecao author_archives."""
    if (theme_dir / "functions.php").exists() and not (theme_dir / "inc" / "seo.php").exists():
        warnings.append("inc/seo.php ausente - descricao, Open Graph e noindex editaveis nao existem (copie do esqueleto).")
    for f in theme_dir.rglob("*.php"):
        if f.name == "seo.php":
            continue
        code = strip_php_comments(f.read_text(encoding="utf-8", errors="ignore"))
        for lineno, _hit in scan_lines(code, HARDCODED_SEO):
            warnings.append(f"{f.relative_to(theme_dir)}:{lineno} meta description/og:/canonical escrito no template - "
                            "use inc/seo.php (campos do admin, se cala com plugin de SEO).")
            break
        for lineno, _hit in scan_lines(code, AUTHOR_LINK):
            warnings.append(f"{f.relative_to(theme_dir)}:{lineno} link para a pagina do autor - a protecao basica a fecha "
                            "(revela o login); mostre o nome sem link ou aprove a excecao author_archives.")
            break


GOOGLE_FONTS_URL = re.compile(r"fonts\.(googleapis|gstatic)\.com", re.I)
FONT_FACE_BLOCK = re.compile(r"@font-face\s*\{([^}]*)\}", re.I | re.S)
FONT_TOKEN = re.compile(r"--font-[\w-]+\s*:\s*([^;]+);")
SYSTEM_FONTS = {"serif", "sans-serif", "monospace", "system-ui", "ui-sans-serif", "ui-serif", "-apple-system",
                "blinkmacsystemfont", "segoe ui", "roboto", "helvetica", "helvetica neue", "arial", "georgia",
                "times new roman", "times", "verdana", "tahoma", "trebuchet ms", "courier new"}


def check_font_guardrails(theme_dir, warnings):
    """Fontes (references/fonts.md): link para o Google Fonts manda o IP do
    visitante para terceiro (LGPD) e abre conexao extra; @font-face sem
    font-display esconde o texto ate a fonte chegar; ttf/otf/woff pesam o
    dobro do woff2; familia do token sem arquivo cai na reserva."""
    manifest = {}
    mf = theme_dir / "assets" / "fonts" / "manifest.json"
    if mf.exists():
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        except ValueError:
            warnings.append("assets/fonts/manifest.json invalido - rode scripts/fetch_fonts.py de novo.")
    if manifest.get("delivery") != "google_cdn":
        for f in list(theme_dir.rglob("*.php")) + list(theme_dir.rglob("*.css")):
            if f.name == "fonts.php":
                continue
            code = f.read_text(encoding="utf-8", errors="ignore")
            code = strip_php_comments(code) if f.suffix == ".php" else blank_block_comments(code)
            for lineno, _hit in scan_lines(code, GOOGLE_FONTS_URL):
                warnings.append(f"{f.relative_to(theme_dir)}:{lineno} fonte carregada do Google - o navegador do visitante "
                                "envia o IP ao Google (LGPD) e abre conexao extra; hospede com scripts/fetch_fonts.py.")
                break
    declared = set()
    for css in theme_dir.rglob("*.css"):
        code = blank_block_comments(css.read_text(encoding="utf-8", errors="ignore"))
        for m in FONT_FACE_BLOCK.finditer(code):
            body = m.group(1)
            fam = re.search(r"font-family\s*:\s*([^;]+);", body)
            if fam:
                declared.add(fam.group(1).strip().strip("'\"").lower())
            if "font-display" not in body and "local(" not in body:
                lineno = code.count("\n", 0, m.start()) + 1
                warnings.append(f"{css.relative_to(theme_dir)}:{lineno} @font-face sem font-display - o texto fica "
                                "invisivel ate a fonte chegar; use font-display: swap.")
    for f in theme_dir.rglob("*"):
        if f.suffix.lower() in {".ttf", ".otf", ".woff", ".eot"}:
            warnings.append(f"{f.relative_to(theme_dir)}: fonte em {f.suffix} - use woff2 (metade do tamanho, todos os navegadores atuais).")
    tokens = theme_dir / "assets" / "css" / "tokens.css"
    if tokens.exists() and manifest.get("delivery") != "google_cdn":
        loaded = declared | {str(x.get("family", "")).lower() for x in manifest.get("families") or []}
        for value in FONT_TOKEN.findall(blank_block_comments(tokens.read_text(encoding="utf-8", errors="ignore"))):
            first = value.split(",")[0].strip().strip("'\"")
            if first.lower() not in SYSTEM_FONTS and first.lower() not in loaded:
                warnings.append(f"assets/css/tokens.css pede a fonte '{first}', mas nenhum @font-face a carrega - "
                                "o site mostra a reserva; rode scripts/fetch_fonts.py.")


COLOR_TOKEN = re.compile(r"--color-[\w-]+\s*:\s*([^;]+);")


def check_editor_guardrails(theme_dir, warnings):
    """Editor de blocos (references/editor.md): theme.json gerado dos tokens,
    so settings, paleta igual a tokens.css, sem cor livre/paleta padrao."""
    tokens = theme_dir / "assets" / "css" / "tokens.css"
    tj = theme_dir / "theme.json"
    if not tj.exists():
        if tokens.exists():
            warnings.append("theme.json ausente - o editor mostra as cores/fontes padrao do WordPress, nao as do site; "
                            "rode generate_design_tokens.py --theme-json <tema>/theme.json.")
        return
    try:
        data = json.loads(tj.read_text(encoding="utf-8"))
    except ValueError as err:
        warnings.append(f"theme.json invalido ({err}) - o WordPress ignora o arquivo inteiro.")
        return
    if data.get("styles"):
        warnings.append("theme.json com 'styles' - reescreve o front-end (cores de link, fundo, titulos) por cima do "
                        "style.css e quebra o espelho; deixe so 'settings'.")
    color = (data.get("settings") or {}).get("color") or {}
    if color.get("custom", True) or color.get("defaultPalette", True):
        warnings.append("theme.json permite cor livre ou a paleta padrao do WordPress - quem edita pode sair da marca "
                        "(color.custom e color.defaultPalette false).")
    if tokens.exists():
        token_colors = {v.strip().lower() for v in COLOR_TOKEN.findall(blank_block_comments(tokens.read_text(encoding="utf-8")))}
        stale = [p.get("slug") for p in color.get("palette") or [] if str(p.get("color", "")).strip().lower() not in token_colors]
        if stale:
            warnings.append(f"theme.json desatualizado: cor(es) {', '.join(map(str, stale))} diferentes de tokens.css - "
                            "regere os dois juntos (generate_design_tokens.py --out ... --theme-json ...).")


def check_header_guardrails(theme_dir, warnings):
    """Submenu que abre so no :hover nao funciona no teclado nem no toque
    (references/header-menu.md): exige :focus-within junto ou o JS de
    disclosure do esqueleto."""
    for css in theme_dir.rglob("*.css"):
        code = blank_block_comments(css.read_text(encoding="utf-8", errors="ignore"))
        if HOVER_SUBMENU.search(code) and ":focus-within" not in code:
            lineno = code.count("\n", 0, HOVER_SUBMENU.search(code).start()) + 1
            warnings.append(
                f"{css.relative_to(theme_dir)}:{lineno} submenu abre so no :hover - teclado e toque nao alcancam; "
                "use :focus-within + o botao de submenu do main.js."
            )


def check_table_price_guardrails(theme_dir, errors, warnings):
    """Preco nunca fixo no template (dado de negocio, editavel no admin);
    tabela de dados usa template-parts/table.php (references/tables-pricing.md)."""
    for f in theme_dir.rglob("*.php"):
        if f.name in GLOBAL_SOURCE_FILES:
            continue
        code = strip_php_comments(f.read_text(encoding="utf-8", errors="ignore"))
        rel = f.relative_to(theme_dir)
        for lineno, _hit in scan_lines(code, SELF_REVIEW_SCHEMA):
            errors.append(
                f"{rel}:{lineno} dados estruturados Review/AggregateRating - avaliacao autopromocional (a empresa "
                "sobre si mesma) nao gera estrelas no Google e pode ser tratada como spam; remova "
                "(references/social-proof.md)."
            )
        for lineno, hit in scan_lines(code, HARDCODED_PRICE):
            errors.append(
                f"{rel}:{lineno} preco fixo no template ({hit!r}) - preco vem do admin (campo numero) e e "
                "formatado por project_price()/project_money()."
            )
        if f.name != "table.php":
            for lineno, _hit in scan_lines(code, HAND_TABLE):
                warnings.append(
                    f"{rel}:{lineno} <table> escrita a mao - tabela de dados usa template-parts/table.php "
                    "(caption, scope, ✓/✗ com texto, celular)."
                )
                break


def check_disclosure_guardrails(theme_dir, warnings):
    """Acordeao/abas usam template-parts/accordion.php e tabs.php
    (references/disclosures.md): <details> nativo e padrao APG prontos."""
    for f in theme_dir.rglob("*"):
        if f.suffix not in {".php", ".js"} or f.name in {"tabs.php", "disclosure.js"}:
            continue
        code = f.read_text(encoding="utf-8", errors="ignore")
        code = strip_php_comments(code) if f.suffix == ".php" else blank_block_comments(code)
        for lineno, hit in scan_lines(code, ICON_FONT_CDN):
            warnings.append(
                f"{f.relative_to(theme_dir)}:{lineno} fonte de icones inteira ({hit!r}) - centenas de KB por meia duzia "
                "de icones; use os SVG de assets/icons/ (project_social_icon)."
            )
            break
        for lineno, _hit in scan_lines(code, UTC_YEAR):
            warnings.append(
                f"{f.relative_to(theme_dir)}:{lineno} date('Y') usa UTC - as 21h de 31/12 no Brasil ja mostra o ano "
                "seguinte; use wp_date('Y')."
            )
            break
        for lineno, hit in scan_lines(code, THIRD_PARTY_SHARE):
            warnings.append(
                f"{f.relative_to(theme_dir)}:{lineno} compartilhamento por script de terceiro ({hit!r}) - rastreio e "
                "peso; use os links de project_share_links() (inc/blog.php)."
            )
            break
        for lineno, hit in scan_lines(code, THIRD_PARTY_COUNTER):
            warnings.append(
                f"{f.relative_to(theme_dir)}:{lineno} contador de numeros de terceiros ({hit!r}) - use "
                "template-parts/stats.php (valor final no HTML, sem animacao com movimento reduzido)."
            )
            break
        for lineno, hit in scan_lines(code, THIRD_PARTY_DISCLOSURE):
            warnings.append(
                f"{f.relative_to(theme_dir)}:{lineno} acordeao/abas feito a mao ou com biblioteca ({hit!r}) - "
                "use template-parts/accordion.php ou tabs.php, salvo decisao aprovada no Blueprint."
            )
            break


def check_carousel_guardrails(theme_dir, warnings):
    """Carrossel usa o componente do esqueleto (references/carousels.md):
    sem biblioteca de terceiros (peso, CDN, jQuery, acessibilidade a refazer)."""
    for f in theme_dir.rglob("*"):
        if f.suffix not in {".php", ".js"} or f.name == "carousel.js":
            continue
        code = f.read_text(encoding="utf-8", errors="ignore")
        code = strip_php_comments(code) if f.suffix == ".php" else blank_block_comments(code)
        for lineno, hit in scan_lines(code, THIRD_PARTY_SLIDERS):
            warnings.append(
                f"{f.relative_to(theme_dir)}:{lineno} usa biblioteca de carrossel de terceiros ({hit!r}) - "
                "use template-parts/carousel.php + assets/js/carousel.js, salvo decisao aprovada no Blueprint."
            )
            break


def check_navigation_guardrails(theme_dir, errors):
    """Header sticky (single page sempre): ligado no header.php e sem
    overflow em html/body, que faz position: sticky parar de funcionar
    (references/navigation.md)."""
    functions_php = theme_dir / "functions.php"
    if not functions_php.exists():
        return
    consts = dict(NAV_CONSTANT.findall(functions_php.read_text(encoding="utf-8", errors="ignore")))
    structure = consts.get("PROJECT_SITE_STRUCTURE")
    if structure is None:
        errors.append(
            "functions.php sem PROJECT_SITE_STRUCTURE - defina single_page ou multi_page "
            "conforme project.site_structure do Blueprint (references/navigation.md)."
        )
        return
    sticky = structure == "single_page" or consts.get("PROJECT_HEADER_BEHAVIOR") == "sticky"
    if structure == "single_page" and consts.get("PROJECT_HEADER_BEHAVIOR") != "sticky":
        errors.append("functions.php: single_page exige PROJECT_HEADER_BEHAVIOR 'sticky'.")
    if not sticky:
        return
    header = theme_dir / "header.php"
    header_code = header.read_text(encoding="utf-8", errors="ignore") if header.exists() else ""
    if "project_header_is_sticky" not in header_code and "site-header--sticky" not in header_code:
        errors.append(
            "header.php nao liga o header sticky (project_header_is_sticky() / .site-header--sticky) - "
            "em single page o menu precisa acompanhar a rolagem."
        )
    for css in theme_dir.rglob("*.css"):
        code = blank_block_comments(css.read_text(encoding="utf-8", errors="ignore"))
        for match in CSS_RULE.finditer(code):
            selector, body = match.group(1).strip(), match.group(2)
            if ROOT_SELECTOR.search(selector) and OVERFLOW_BREAKS_STICKY.search(body):
                lineno = code.count("\n", 0, match.start(2)) + 1
                errors.append(
                    f"{css.relative_to(theme_dir)}:{lineno} '{selector}' com "
                    f"{OVERFLOW_BREAKS_STICKY.search(body).group(0)} - isso faz o header sticky "
                    "rolar junto com a pagina. Use overflow-x: clip."
                )


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    theme_dir = Path(sys.argv[1])
    if not theme_dir.is_dir():
        print(f"Diretorio nao encontrado: {theme_dir}")
        sys.exit(1)

    errors = []
    warnings = []

    for expected in EXPECTED_FILES:
        if not (theme_dir / expected).exists():
            errors.append(f"Arquivo esperado ausente: {expected}")

    php_files = list(theme_dir.rglob("*.php"))
    print(f"Verificando sintaxe de {len(php_files)} arquivo(s) .php...")
    for php_file in php_files:
        result = subprocess.run(
            ["php", "-l", str(php_file)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            errors.append(f"Erro de sintaxe em {php_file}:\n{result.stdout.strip()}")

    functions_php = theme_dir / "functions.php"
    if functions_php.exists():
        content = functions_php.read_text(encoding="utf-8", errors="ignore")
        hits = [p for p in SUSPICIOUS_PATTERNS if p in content]
        if hits:
            warnings.append(
                "functions.php parece conter logica que deveria estar em "
                f"inc/ (padroes encontrados: {', '.join(hits)}). Ver "
                "references/wordpress-architecture.md."
            )

    # Descoberto rodando o caso Construtora Horizonte de ponta a ponta:
    # 1) get_field() sem guarda de function_exists() causa fatal error
    #    antes do ACF PRO ser instalado/ativado.
    # 2) mesmo guardado, get_field() sempre retorna vazio para conteudo
    #    demo semeado via wp-cli (post meta bruta, sem a meta de
    #    referencia que o ACF espera) - use project_field()/ch_field()
    #    (inc/helpers.php) em vez de get_field() direto nos templates.
    for php_file in php_files:
        if php_file.name == "helpers.php":
            continue
        content = php_file.read_text(encoding="utf-8", errors="ignore")
        if "get_field(" not in content:
            continue
        if "function_exists('get_field')" not in content and 'function_exists("get_field")' not in content:
            warnings.append(
                f"{php_file.relative_to(theme_dir)} chama get_field() sem "
                "guarda function_exists('get_field') - vai dar fatal error "
                "se o ACF PRO nao estiver ativo ainda."
            )
        else:
            warnings.append(
                f"{php_file.relative_to(theme_dir)} chama get_field() diretamente - "
                "considere usar project_field()/ch_field() (inc/helpers.php) para "
                "que conteudo demo semeado via wp-cli tambem apareca antes do ACF "
                "estar configurado."
            )

    check_content_guardrails(theme_dir, php_files, errors)
    check_navigation_guardrails(theme_dir, errors)
    check_carousel_guardrails(theme_dir, warnings)
    check_disclosure_guardrails(theme_dir, warnings)
    check_table_price_guardrails(theme_dir, errors, warnings)
    check_header_guardrails(theme_dir, warnings)
    check_hero_guardrails(theme_dir, warnings)
    check_seo_security_guardrails(theme_dir, warnings)
    check_font_guardrails(theme_dir, warnings)
    check_editor_guardrails(theme_dir, warnings)
    check_form_map_guardrails(theme_dir, errors)

    if warnings:
        print(f"\nAVISOS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"\nBLOQUEIOS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("\nResultado: OK.")
    sys.exit(0)


if __name__ == "__main__":
    main()
