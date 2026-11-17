#!/usr/bin/env python3
"""
Gera assets/css/tokens.css (variaveis CSS em :root) a partir de
design.tokens do BLUEPRINT.yaml - o Blueprint passa a ser a fonte unica
de verdade tambem para o visual (cores, fontes, escala de espacamento,
raios, sombras, container).

Uso:
    python generate_design_tokens.py <BLUEPRINT.yaml> --out <tema>/assets/css/tokens.css
    python generate_design_tokens.py <BLUEPRINT.yaml> --check   (so valida)

Formato esperado em design.tokens (cada valor pode ser string ou
{value, confidence, evidence}):

    tokens:
      color:       { primary: "#C9872E", background: "#FFFFFF", text: "#1A1A1A" }
      font_family: { heading: "'Montserrat', sans-serif", body: "'Inter', sans-serif" }
      font_size:   { h1: "clamp(2.25rem, 4vw, 3.5rem)", body: "1rem" }
      font_weight: { heading: 700, body: 400 }
      line_height: { heading: 1.15, body: 1.6 }
      space:       { xs: "8px", sm: "16px", md: "24px", lg: "48px", xl: "96px" }
      radius:      { sm: "4px", md: "8px" }
      shadow:      { card: "0 8px 24px rgba(0,0,0,.08)" }
      layout:      { container_max: "1200px", gutter: "24px" }

Breakpoints NAO ficam aqui: vem de responsive.breakpoints e sao emitidos
como comentario (custom properties nao funcionam dentro de @media).

Correcao visual de token (cor, espacamento) nao exige nova versao do
Blueprint (ver references/approval-protocol.md): altere o valor em
design.tokens, rode este script de novo e registre em DECISIONS.md.

Exit code 1 se algum token tiver valor invalido (ex.: descricao em prosa
no lugar de valor CSS) ou se faltar token obrigatorio.
"""
import argparse
import json
import datetime
import re
import sys

try:
    import yaml
except ImportError:
    print("Erro: PyYAML nao esta instalado. Rode: pip install pyyaml")
    sys.exit(2)

# Console do Windows usa cp1252 por padrao e corrompe acentos dos textos do Blueprint.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# grupo do Blueprint -> prefixo da custom property
GROUP_PREFIX = {
    "color": "color",
    "font_family": "font",
    "font_size": "fs",
    "font_weight": "fw",
    "line_height": "lh",
    "space": "space",
    "radius": "radius",
    "shadow": "shadow",
    "layout": "",          # --container-max, --gutter
}

REQUIRED_TOKENS = [
    ("color", "primary"), ("color", "background"), ("color", "text"),
    ("font_family", "heading"), ("font_family", "body"),
    ("layout", "container_max"),
]
MIN_SPACE_STEPS = 3

_NUM = r"-?\d*\.?\d+"
_LENGTH = rf"(0|{_NUM}(px|rem|em|vw|vh|%|ch|svh|dvh))"
_FUNC = r"(clamp|calc|min|max|var)\(.+\)"
COLOR_RE = re.compile(
    r"^(#[0-9a-f]{3,4}|#[0-9a-f]{6}|#[0-9a-f]{8}"
    r"|(rgb|rgba|hsl|hsla|oklch|oklab|lab|lch|color-mix|var)\(.+\)"
    r"|transparent|currentcolor|white|black)$", re.I)
DIMENSION_RE = re.compile(rf"^({_LENGTH}|{_FUNC})$", re.I)
WEIGHT_RE = re.compile(r"^([1-9]00|normal|bold|var\(.+\))$", re.I)
LINE_HEIGHT_RE = re.compile(rf"^({_NUM}|{_LENGTH}|normal|var\(.+\))$", re.I)
SHADOW_RE = re.compile(r"^(none|[-\d.a-z%(),\s#/]+)$", re.I)
FONT_RE = re.compile(r"^[\"'\w\s,-]+$")

VALIDATORS = {
    "color": (COLOR_RE, "cor CSS (#hex, rgb(), hsl(), oklch()...)"),
    "font_size": (DIMENSION_RE, "medida CSS (px/rem/em/vw, clamp())"),
    "space": (DIMENSION_RE, "medida CSS"),
    "radius": (DIMENSION_RE, "medida CSS"),
    "layout": (DIMENSION_RE, "medida CSS"),
    "font_weight": (WEIGHT_RE, "peso 100-900"),
    "line_height": (LINE_HEIGHT_RE, "numero sem unidade ou medida"),
    "shadow": (SHADOW_RE, "box-shadow CSS"),
    "font_family": (FONT_RE, "lista de familias, ex.: 'Inter', sans-serif"),
}


def load_blueprint(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("blueprint", data)


def unwrap(raw):
    """Aceita 'valor' ou {value, confidence, evidence}."""
    if isinstance(raw, dict):
        return raw.get("value"), raw.get("confidence"), raw.get("evidence")
    return raw, None, None


def with_fallback_face(bp, value):
    """'Manrope', sans-serif -> 'Manrope', 'Manrope Fallback', sans-serif
    quando a fonte e hospedada com reserva ajustada (scripts/fetch_fonts.py
    gera a @font-face 'Manrope Fallback'; references/fonts.md)."""
    fonts = bp.get("fonts") or {}
    if fonts.get("delivery") != "self_hosted" or fonts.get("fallback_metrics") is False:
        return value
    hosted = {str(f.get("family", "")).lower() for f in fonts.get("families") or [] if isinstance(f, dict)}
    names = [n.strip() for n in value.split(",")]
    first = names[0].strip("'\"")
    if first.lower() in hosted and not any(n.strip("'\"").lower() == f"{first.lower()} fallback" for n in names):
        names.insert(1, f"'{first} Fallback'")
    return ", ".join(names)


def collect_tokens(bp):
    """Retorna (tokens, errors, warnings). tokens = [(group, name, css_var, value, confidence, evidence)]."""
    errors, warnings, tokens = [], [], []
    declared = set()   # (grupo, nome) declarados, validos ou nao
    design = bp.get("design") or {}
    raw_tokens = design.get("tokens")
    if not raw_tokens:
        warnings.append(
            "design.tokens ausente - sem ele o tema nao tem fonte unica de "
            "verdade visual (rode scripts/generate_design_tokens.py depois de "
            "preencher; ver references/blueprint-schema.md#design)."
        )
        return tokens, errors, warnings

    for group, entries in raw_tokens.items():
        if group not in GROUP_PREFIX:
            errors.append(f"design.tokens.{group}: grupo desconhecido (validos: {', '.join(GROUP_PREFIX)}).")
            continue
        if not isinstance(entries, dict):
            errors.append(f"design.tokens.{group} deve ser um mapa nome -> valor.")
            continue
        for name, raw in entries.items():
            declared.add((group, name))
            value, confidence, evidence = unwrap(raw)
            if value is None or str(value).strip() == "":
                errors.append(f"design.tokens.{group}.{name} sem valor.")
                continue
            value = str(value).strip()
            pattern, expected = VALIDATORS[group]
            if not pattern.match(value):
                errors.append(
                    f"design.tokens.{group}.{name} = {value!r} nao e um valor CSS valido "
                    f"(esperado: {expected}). Descricao em prosa vai nos atributos "
                    "descritivos de design, nao em tokens."
                )
                continue
            if confidence and confidence not in {"high", "medium", "low"}:
                errors.append(f"design.tokens.{group}.{name}.confidence invalido: {confidence!r}.")
            if group == "font_family":
                value = with_fallback_face(bp, value)
            slug = str(name).replace("_", "-")
            prefix = GROUP_PREFIX[group]
            css_var = f"--{prefix}-{slug}" if prefix else f"--{slug}"
            tokens.append((group, name, css_var, value, confidence, evidence))

    for group, name in REQUIRED_TOKENS:
        if (group, name) not in declared:
            errors.append(f"design.tokens.{group}.{name} obrigatorio e ausente.")
    space_steps = sum(1 for g, _ in declared if g == "space")
    if space_steps < MIN_SPACE_STEPS:
        errors.append(
            f"design.tokens.space tem {space_steps} passo(s); defina ao menos "
            f"{MIN_SPACE_STEPS} (ex.: sm, md, lg) medidos na referencia."
        )

    branding = ((bp.get("global_settings") or {}).get("branding") or {})
    by_key = {(g, n): v for g, n, _, v, *_ in tokens}
    for setting, key in (("primary_color", ("color", "primary")), ("secondary_color", ("color", "secondary"))):
        b = branding.get(setting)
        t = by_key.get(key)
        if b and t and str(b).strip().lower() != t.lower():
            warnings.append(
                f"global_settings.branding.{setting} ({b}) difere de design.tokens."
                f"{key[0]}.{key[1]} ({t}) - mantenha um so valor de verdade."
            )
    return tokens, errors, warnings


def render_css(bp, tokens):
    meta = bp.get("metadata") or {}
    version = meta.get("blueprint_version", "?")
    today = datetime.date.today().isoformat()
    breakpoints = ((bp.get("responsive") or {}).get("breakpoints") or {})
    lines = [
        "/*",
        " * Tokens de design - GERADO por scripts/generate_design_tokens.py",
        f" * a partir de BLUEPRINT.yaml (blueprint_version {version}) em {today}.",
        " * NAO edite a mao: altere design.tokens no Blueprint e gere de novo.",
    ]
    if breakpoints:
        lines.append(" *")
        lines.append(" * Breakpoints (use literalmente nas media queries - custom")
        lines.append(" * properties nao funcionam dentro de @media):")
        for name, value in breakpoints.items():
            lines.append(f" *   {name}: {value}")
    lines += [" */", "", ":root {"]
    current = None
    for group, _name, css_var, value, confidence, evidence in tokens:
        if group != current:
            if current is not None:
                lines.append("")
            lines.append(f"    /* {group} */")
            current = group
        note = ""
        if confidence == "low":
            note = f" /* confianca baixa ({evidence or 'inferencia'}) - confirmar na validacao visual */"
        lines.append(f"    {css_var}: {value};{note}")
    lines.append("}")
    return "\n".join(lines) + "\n"


PT_LABELS = {
    "primary": "Principal", "secondary": "Secundária", "accent": "Destaque", "background": "Fundo",
    "surface": "Superfície", "text": "Texto", "text_muted": "Texto suave", "muted": "Suave", "border": "Borda",
    "dark": "Escuro", "light": "Claro", "chip": "Etiqueta", "success": "Sucesso", "error": "Erro",
    "warning": "Atenção", "whatsapp": "WhatsApp", "heading": "Títulos", "body": "Texto", "hero": "Título do topo",
    "page_hero": "Título de página", "lead": "Texto de abertura", "small": "Pequeno", "eyebrow": "Sobretítulo",
    "primary_dark": "Principal escura", "primary_light": "Principal clara", "secondary_dark": "Secundária escura",
    "h1": "Título 1", "h2": "Título 2", "h3": "Título 3", "h4": "Título 4",
}


def _label(name):
    return PT_LABELS.get(name) or str(name).replace("_", " ").capitalize()


def render_theme_json(bp, tokens):
    """theme.json do editor de blocos (references/editor.md): SO settings -
    paleta, fontes, tamanhos e espacos da marca, sem cores/tamanhos livres nem
    paletas padrao do WordPress. Sem 'styles': o visual do site vem do
    style.css; styles do theme.json reescreveria o front-end (espelho)."""
    by_group = {}
    for group, name, css_var, value, _conf, _ev in tokens:
        by_group.setdefault(group, []).append((name, css_var, value))
    slug = lambda n: str(n).replace("_", "-")
    palette = [{"slug": slug(n), "name": _label(n), "color": v} for n, _c, v in by_group.get("color", [])
               if "overlay" not in n and "shadow" not in n]
    families = [{"slug": slug(n), "name": _label(n), "fontFamily": v} for n, _c, v in by_group.get("font_family", [])]
    sizes = [{"slug": slug(n), "name": _label(n), "size": v} for n, _c, v in by_group.get("font_size", [])]
    spacing = [{"slug": slug(n), "name": n.upper(), "size": v} for n, _c, v in by_group.get("space", [])]
    layout = {n: v for n, _c, v in by_group.get("layout", [])}
    settings = {
        "appearanceTools": False,
        "color": {"palette": palette, "custom": False, "customGradient": False, "defaultPalette": False,
                  "defaultGradients": False, "defaultDuotone": False, "duotone": [], "gradients": []},
        "typography": {"fontFamilies": families, "customFontSize": False, "defaultFontSizes": False,
                       "dropCap": False, "fluid": False, **({"fontSizes": sizes} if sizes else {})},
        "spacing": {"units": ["px", "rem", "%"], "defaultSpacingSizes": False,
                    **({"spacingSizes": spacing} if spacing else {})},
    }
    if layout.get("container_max"):
        settings["layout"] = {"contentSize": layout["container_max"], "wideSize": layout["container_max"]}
    meta = bp.get("metadata") or {}
    data = {
        "$schema": "https://schemas.wp.org/wp/6.7/theme.json",
        "version": 3,
        "title": f"GERADO por scripts/generate_design_tokens.py (blueprint_version {meta.get('blueprint_version', '?')}) - nao edite a mao",
        "settings": settings,
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("blueprint")
    ap.add_argument("--out", help="caminho do tokens.css a gerar")
    ap.add_argument("--theme-json", help="tambem gera o theme.json do editor (references/editor.md), ex.: <tema>/theme.json")
    ap.add_argument("--check", action="store_true", help="apenas validar, sem gerar")
    args = ap.parse_args()
    if not args.out and not args.check:
        ap.error("informe --out <tokens.css> ou --check")

    bp = load_blueprint(args.blueprint)
    tokens, errors, warnings = collect_tokens(bp)

    for w in warnings:
        print(f"AVISO: {w}")
    if errors:
        print(f"\nBLOQUEIOS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    low = [t for t in tokens if t[4] == "low"]
    print(f"{len(tokens)} token(s) validos ({len(low)} com confianca baixa).")
    if args.check:
        sys.exit(0)

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_css(bp, tokens))
    print(f"Gerado: {args.out}")
    if args.theme_json:
        with open(args.theme_json, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_theme_json(bp, tokens))
        print(f"Gerado: {args.theme_json} (paleta, fontes e tamanhos da marca no editor)")


if __name__ == "__main__":
    main()
