#!/usr/bin/env python3
"""
Valida um arquivo BLUEPRINT.yaml contra as regras estruturais de
references/blueprint-schema.md.

Uso:
    python validate_blueprint.py <caminho/para/BLUEPRINT.yaml>

Saida: relatorio no stdout. Exit code 1 se houver problema bloqueante
(secao obrigatoria ausente, enum invalido, incerteza bloqueante nao
resolvida). Exit code 0 caso contrario (avisos nao bloqueantes ainda
podem ser impressos).

Isto NAO substitui revisao humana/do agente: cobre apenas o que e
verificavel mecanicamente. Julgamento sobre "esse CPT faz sentido?"
continua sendo responsabilidade de quem monta o Blueprint.
"""
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Erro: PyYAML nao esta instalado. Rode: pip install pyyaml")
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_design_tokens import collect_tokens  # noqa: E402

# Console do Windows usa cp1252 por padrao e corrompe acentos dos textos do Blueprint.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


VALID_COPY_ROLES = {
    "nav", "heading", "subheading", "body", "cta", "label", "footer",
    "form", "other",
}
VALID_COPY_SOURCES = {"reference_file", "user", "demo"}
VALID_LEGIBILITY = {"clear", "partial", "illegible"}

VALID_MEDIA_TYPES = {
    "photo", "illustration", "logo", "icon", "texture", "background", "video",
}
VALID_MEDIA_TREATMENTS = {
    "provided", "crop_from_reference", "placeholder", "icon_library", "css",
}
RASTER_MEDIA = {"photo", "illustration", "background", "texture"}
PROVISIONAL_TREATMENTS = {"crop_from_reference", "placeholder"}

# Nomes de campo genericos demais: perdem sentido fora de um template e
# colidem entre content_types (ver references/content-modeling.md).
GENERIC_FIELD_NAMES = {
    "title", "image", "link", "text", "description", "cta", "copy", "url",
    "content", "icon", "photo", "name", "label", "subtitle", "gallery",
}

REQUIRED_SECTIONS = [
    "metadata", "project", "requirements", "design", "pages", "components",
    "content_types", "taxonomies", "global_settings", "menus", "forms",
    "media", "seo", "plugins", "theme", "responsive", "accessibility",
    "integrations", "decisions", "uncertainties", "dependencies",
    "implementation", "validation", "generation",
]

VALID_METADATA_STATUS = {
    "draft", "analysis", "awaiting_review", "approved", "generating",
    "generated", "testing", "completed", "blocked", "revision_required",
}

VALID_DECISION_STATUS = {"pending_user_approval", "approved", "superseded"}
VALID_UNCERTAINTY_STATUS = {"pending", "resolved"}
VALID_IMPACT = {"low", "medium", "high"}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "blueprint" in data:
        data = data["blueprint"]
    return data


def check(bp):
    errors = []
    warnings = []

    for section in REQUIRED_SECTIONS:
        if section not in bp:
            errors.append(f"Secao obrigatoria ausente: '{section}'")

    metadata = bp.get("metadata", {}) or {}
    status = metadata.get("status")
    if status and status not in VALID_METADATA_STATUS:
        errors.append(
            f"metadata.status invalido: '{status}' "
            f"(esperado um de {sorted(VALID_METADATA_STATUS)})"
        )

    decisions = bp.get("decisions") or []
    for d in decisions:
        did = d.get("id", "<sem id>")
        if d.get("status") not in VALID_DECISION_STATUS:
            errors.append(
                f"decisions[{did}].status invalido: '{d.get('status')}'"
            )
        if not d.get("reason"):
            warnings.append(f"decisions[{did}] sem 'reason' preenchido.")

    uncertainties = bp.get("uncertainties") or []
    blocking_pending = []
    for u in uncertainties:
        uid = u.get("id", "<sem id>")
        if u.get("status") not in VALID_UNCERTAINTY_STATUS:
            errors.append(
                f"uncertainties[{uid}].status invalido: '{u.get('status')}'"
            )
        if u.get("impact") and u.get("impact") not in VALID_IMPACT:
            errors.append(
                f"uncertainties[{uid}].impact invalido: '{u.get('impact')}'"
            )
        if u.get("blocking") and u.get("status") == "pending":
            blocking_pending.append(u)

    if blocking_pending:
        errors.append(
            f"{len(blocking_pending)} incerteza(s) bloqueante(s) ainda "
            "pendente(s)  -  implementacao da parte afetada deve ficar em "
            "espera ate resolver ou o usuario autorizar explicitamente:"
        )
        for u in blocking_pending:
            errors.append(
                f"    - [{u.get('id')}] {u.get('subject')}: {u.get('question')}"
            )

    content_types = bp.get("content_types") or []
    for ct in content_types:
        cid = ct.get("id", "<sem id>")
        if not ct.get("fields"):
            warnings.append(
                f"content_types[{cid}] nao tem campos definidos  -  "
                "confirme se isso e intencional (CPT so com titulo/conteudo)."
            )
    # Regras do schema 1.1 (tokens, copy, media.treatment, nomes de campo).
    # Blueprints 1.0 ja aprovados nao sao bloqueados retroativamente: os
    # bloqueios viram avisos com indicacao de migracao.
    new_errors = []
    for ct in content_types:
        check_fields(ct.get("id", "<sem id>"), ct.get("fields") or [], new_errors, warnings)
    check_design_tokens(bp, new_errors, warnings)
    check_reference_map(bp, new_errors, warnings)
    check_copy_inventory(bp, new_errors, warnings)
    check_media(bp, new_errors, warnings)

    schema_version = str(metadata.get("schema_version", "1.0"))
    if schema_version == "1.0" and new_errors:
        warnings.append(
            f"Blueprint em schema 1.0: {len(new_errors)} regra(s) do schema 1.1 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao do Blueprint, migre "
            "para 1.1 (design.tokens, copy, media.treatment, campos prefixados)."
        )
        warnings.extend(f"[1.1] {e}" for e in new_errors)
    else:
        errors.extend(new_errors)

    # Regra do schema 1.2: todo conteudo visivel tem destino de edicao no admin.
    editable_errors = []
    check_editable_content(bp, editable_errors)
    version = tuple(int(x) for x in schema_version.split(".")[:2] if x.isdigit())
    if version >= (1, 2):
        errors.extend(editable_errors)
    elif editable_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: sem mapa 'editable_content' completo "
            f"({len(editable_errors)} item(ns)). No schema 1.2 isso bloqueia: todo texto/imagem "
            "visivel precisa ter onde ser editado no admin."
        )
        warnings.extend(f"[1.2] {e}" for e in editable_errors)

    # Regra do schema 1.3: single page x multipaginas (references/navigation.md).
    nav_errors = []
    check_navigation(bp, nav_errors, warnings)
    if version >= (1, 3):
        errors.extend(nav_errors)
    elif nav_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(nav_errors)} regra(s) de navegacao do "
            "schema 1.3 rebaixada(s) a aviso. Ao gerar a proxima versao, declare "
            "project.site_structure e theme.header_behavior."
        )
        warnings.extend(f"[1.3] {e}" for e in nav_errors)

    # Regra do schema 1.4: carrosseis/banners rotativos (references/carousels.md).
    carousel_errors = []
    check_carousels(bp, carousel_errors, warnings)
    if version >= (1, 4):
        errors.extend(carousel_errors)
    elif carousel_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(carousel_errors)} regra(s) de carrossel do "
            "schema 1.4 rebaixada(s) a aviso. Ao gerar a proxima versao, declare carousels "
            "(lista vazia se a referencia nao tiver carrossel)."
        )
        warnings.extend(f"[1.4] {e}" for e in carousel_errors)

    # Regra do schema 1.5: formularios estruturados e mapas (references/forms.md, maps.md).
    fm_errors = []
    check_forms(bp, fm_errors, warnings)
    check_maps(bp, fm_errors, warnings)
    if version >= (1, 5):
        errors.extend(fm_errors)
    elif fm_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(fm_errors)} regra(s) de formulario/mapa do "
            "schema 1.5 rebaixada(s) a aviso. Ao gerar a proxima versao, estruture forms[].fields "
            "e declare maps (lista vazia se nao houver)."
        )
        warnings.extend(f"[1.5] {e}" for e in fm_errors)

    # Regra do schema 1.6: galerias e videos (references/galleries.md, videos.md).
    gv_errors = []
    check_galleries(bp, gv_errors, warnings)
    check_videos(bp, gv_errors, warnings)
    if version >= (1, 6):
        errors.extend(gv_errors)
    elif gv_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(gv_errors)} regra(s) de galeria/video do "
            "schema 1.6 rebaixada(s) a aviso. Ao gerar a proxima versao, declare galleries e videos "
            "(listas vazias se nao houver)."
        )
        warnings.extend(f"[1.6] {e}" for e in gv_errors)

    # Regra do schema 1.7: acordeoes/FAQ e abas (references/disclosures.md).
    ui_errors = []
    check_accordions(bp, ui_errors, warnings)
    check_tabs(bp, ui_errors, warnings)
    if version >= (1, 7):
        errors.extend(ui_errors)
    elif ui_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(ui_errors)} regra(s) de acordeao/abas do "
            "schema 1.7 rebaixada(s) a aviso. Ao gerar a proxima versao, declare accordions e tabs "
            "(listas vazias se nao houver)."
        )
        warnings.extend(f"[1.7] {e}" for e in ui_errors)

    # Regra do schema 1.8: tabelas e precos (references/tables-pricing.md).
    tp_errors = []
    check_tables(bp, tp_errors, warnings)
    check_pricing(bp, tp_errors, warnings)
    if version >= (1, 8):
        errors.extend(tp_errors)
    elif tp_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(tp_errors)} regra(s) de tabela/preco do "
            "schema 1.8 rebaixada(s) a aviso. Ao gerar a proxima versao, declare tables e pricing "
            "(listas vazias se nao houver)."
        )
        warnings.extend(f"[1.8] {e}" for e in tp_errors)

    # Regra do schema 1.9: depoimentos e logos de clientes (references/social-proof.md).
    sp_errors = []
    check_testimonials(bp, sp_errors, warnings)
    check_client_logos(bp, sp_errors, warnings)
    if version >= (1, 9):
        errors.extend(sp_errors)
    elif sp_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(sp_errors)} regra(s) de depoimento/logo do "
            "schema 1.9 rebaixada(s) a aviso. Ao gerar a proxima versao, declare testimonials e "
            "client_logos (listas vazias se nao houver)."
        )
        warnings.extend(f"[1.9] {e}" for e in sp_errors)

    # Regra do schema 1.10: equipe e numeros em destaque (references/team-stats.md).
    ts_errors = []
    check_team(bp, ts_errors, warnings)
    check_stats(bp, ts_errors, warnings)
    if version >= (1, 10):
        errors.extend(ts_errors)
    elif ts_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(ts_errors)} regra(s) de equipe/numeros do "
            "schema 1.10 rebaixada(s) a aviso. Ao gerar a proxima versao, declare team e stats "
            "(listas vazias se nao houver)."
        )
        warnings.extend(f"[1.10] {e}" for e in ts_errors)

    # Regra do schema 1.11: blog/noticias (references/blog.md).
    blog_errors = []
    check_blog(bp, blog_errors, warnings)
    if version >= (1, 11):
        errors.extend(blog_errors)
    elif blog_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(blog_errors)} regra(s) de blog do schema 1.11 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare blog (enabled: false se nao houver)."
        )
        warnings.extend(f"[1.11] {e}" for e in blog_errors)

    # Regra do schema 1.12: rodape e redes sociais (references/footer-social.md).
    fs_errors = []
    check_footer(bp, fs_errors, warnings)
    check_social(bp, fs_errors, warnings)
    if version >= (1, 12):
        errors.extend(fs_errors)
    elif fs_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(fs_errors)} regra(s) de rodape/redes do schema 1.12 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare footer e social."
        )
        warnings.extend(f"[1.12] {e}" for e in fs_errors)

    # Regra do schema 1.13: header (references/header-menu.md).
    header_errors = []
    check_header(bp, header_errors, warnings)
    if version >= (1, 13):
        errors.extend(header_errors)
    elif header_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(header_errors)} regra(s) de header do schema 1.13 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare header."
        )
        warnings.extend(f"[1.13] {e}" for e in header_errors)

    # Regra do schema 1.14: hero e banners (references/hero-banners.md).
    hb_errors = []
    check_heroes(bp, hb_errors, warnings)
    check_banners(bp, hb_errors, warnings)
    if version >= (1, 14):
        errors.extend(hb_errors)
    elif hb_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(hb_errors)} regra(s) de hero/banner do schema 1.14 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare heroes e banners."
        )
        warnings.extend(f"[1.14] {e}" for e in hb_errors)

    # Regra do schema 1.15: SEO e seguranca (references/security-seo.md).
    ss_errors = []
    check_seo(bp, ss_errors, warnings)
    check_security(bp, ss_errors, warnings)
    if version >= (1, 15):
        errors.extend(ss_errors)
    elif ss_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(ss_errors)} regra(s) de SEO/seguranca do schema 1.15 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare seo e security."
        )
        warnings.extend(f"[1.15] {e}" for e in ss_errors)

    # Regra do schema 1.16: fontes (references/fonts.md).
    font_errors = []
    check_fonts(bp, font_errors, warnings)
    if version >= (1, 16):
        errors.extend(font_errors)
    elif font_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(font_errors)} regra(s) de fontes do schema 1.16 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare fonts."
        )
        warnings.extend(f"[1.16] {e}" for e in font_errors)

    # Regra do schema 1.17: robos de IA no robots.txt (references/security-seo.md).
    ai_errors = []
    check_ai_crawlers(bp, ai_errors, warnings)
    if version >= (1, 17):
        errors.extend(ai_errors)
    elif ai_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(ai_errors)} regra(s) de robos de IA do schema 1.17 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare seo.ai_crawlers."
        )
        warnings.extend(f"[1.17] {e}" for e in ai_errors)

    # Regra do schema 1.18: publicacao, icone do site e redirecionamentos.
    launch_errors = []
    check_launch(bp, launch_errors, warnings)
    if version >= (1, 18):
        errors.extend(launch_errors)
    elif launch_errors:
        warnings.append(
            f"Blueprint em schema {schema_version}: {len(launch_errors)} regra(s) de publicacao do schema 1.18 "
            "rebaixada(s) a aviso. Ao gerar a proxima versao, declare launch, branding.site_icon e redirects."
        )
        warnings.extend(f"[1.18] {e}" for e in launch_errors)

    taxonomies = bp.get("taxonomies") or []
    for tx in taxonomies:
        tid = tx.get("id", "<sem id>")
        if not tx.get("post_types"):
            errors.append(
                f"taxonomies[{tid}] nao esta associada a nenhum post_type  -  "
                "taxonomia orfa nao deveria existir."
            )

    plugins = (bp.get("plugins") or {}).get("required") or []
    for p in plugins:
        if not p.get("reason"):
            warnings.append(
                f"plugin obrigatorio '{p.get('name')}' sem 'reason' "
                "justificando a dependencia."
            )

    # deteccao simples de dado global duplicado dentro do proprio blueprint
    # (duplicacao real no codigo do tema nao e verificavel aqui)
    company = (bp.get("global_settings") or {}).get("company") or {}
    seen_values = {}
    for key, value in company.items():
        if value and value in seen_values:
            warnings.append(
                f"global_settings.company: valor '{value}' repetido em "
                f"'{key}' e '{seen_values[value]}'  -  confirme se nao e "
                "copia/cola indevido."
            )
        elif value:
            seen_values[value] = key

    return errors, warnings


def check_fields(cid, fields, errors, warnings):
    """Nomes estaveis com prefixo de dominio; repeaters com limites e subcampos."""
    seen = set()
    unprefixed, generic, no_instructions = [], [], []
    for field in fields:
        fid = str(field.get("id", "")).strip()
        if not fid:
            errors.append(f"content_types[{cid}] tem campo sem 'id'.")
            continue
        if fid in seen:
            errors.append(f"content_types[{cid}].fields: id duplicado '{fid}'.")
        seen.add(fid)
        if fid.startswith("field_"):
            errors.append(
                f"content_types[{cid}].fields[{fid}]: use o NOME estavel do campo, "
                "nao a field key do ACF (field_...)."
            )
        if fid in GENERIC_FIELD_NAMES:
            generic.append(fid)
        elif not fid.startswith(f"{cid}_"):
            unprefixed.append(fid)
        if not field.get("description"):
            no_instructions.append(fid)

        if field.get("type") == "repeater":
            if not field.get("sub_fields"):
                errors.append(
                    f"content_types[{cid}].fields[{fid}]: repeater sem 'sub_fields'."
                )
            if field.get("min") is None or field.get("max") is None:
                warnings.append(
                    f"content_types[{cid}].fields[{fid}]: repeater sem 'min'/'max' - "
                    "defina limites coerentes com o layout para o editor nao quebra-lo."
                )
            warnings.append(
                f"content_types[{cid}].fields[{fid}]: confirme que os itens do repeater "
                "NAO precisam de URL propria, filtro, reuso em outras paginas ou ciclo de "
                "vida independente - se precisarem, e CPT (ver content-modeling.md)."
            )

    if generic:
        errors.append(
            f"content_types[{cid}]: nome(s) de campo generico(s) {generic} - use "
            f"prefixo de dominio (ex.: '{cid}_{generic[0]}')."
        )
    if unprefixed:
        warnings.append(
            f"content_types[{cid}]: campo(s) sem prefixo '{cid}_': {unprefixed}. "
            "Prefixo de dominio evita colisao entre CPTs e facilita busca/migracao."
        )
    if no_instructions:
        warnings.append(
            f"content_types[{cid}]: campo(s) sem 'description' (vira a instrucao "
            f"do ACF para o editor): {no_instructions}."
        )


def check_design_tokens(bp, errors, warnings):
    _tokens, token_errors, token_warnings = collect_tokens(bp)
    errors.extend(token_errors)
    warnings.extend(token_warnings)


VALID_STORAGE = {"options_page", "page_fields", "post_type", "taxonomy", "menu", "form", "editor"}


def check_editable_content(bp, errors):
    """Toda secao de pagina, o header e o footer tem destino de edicao no admin."""
    entries = bp.get("editable_content") or []
    if not entries:
        errors.append(
            "Secao 'editable_content' ausente - sem ela o Blueprint nao diz onde o "
            "administrador edita cada texto/imagem, e o resultado tende a ter conteudo "
            "fixo no template (ver references/content-modeling.md -> 'Todo conteudo "
            "visivel e editavel')."
        )
        return
    targets = set()
    for i, e in enumerate(entries):
        target = e.get("target")
        if not target:
            errors.append(f"editable_content[{i}] sem 'target'.")
            continue
        targets.add(target)
        if e.get("storage") not in VALID_STORAGE:
            errors.append(f"editable_content[{target}].storage invalido: {e.get('storage')!r} (validos: {sorted(VALID_STORAGE)}).")
        if not e.get("where"):
            errors.append(f"editable_content[{target}] sem 'where' (caminho no admin, ex.: 'Páginas > Início > Hero').")
        if e.get("storage") in {"options_page", "page_fields"} and not e.get("fields"):
            errors.append(f"editable_content[{target}]: storage {e.get('storage')} exige a lista 'fields'.")
    required = {"header", "footer"}
    for page in bp.get("pages") or []:
        required |= {s.get("id") for s in (page.get("sections") or []) if s.get("id")}
    for missing in sorted(required - targets):
        errors.append(
            f"'{missing}' nao tem destino em editable_content - onde o administrador "
            "edita os textos e imagens dessa parte?"
        )


VALID_SITE_STRUCTURES = {"single_page", "multi_page"}
VALID_HEADER_BEHAVIORS = {"sticky", "static"}
VALID_MENU_ITEM_TYPES = {"page", "archive", "anchor", "custom"}
VALID_PAGE_ROLES = {"main", "auxiliary"}
ANCHOR_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_ANCHORS = {"conteudo", "site-nav"}   # skip link e menu do header.php


def iter_menu_items(items):
    for item in items or []:
        yield item
        yield from iter_menu_items(item.get("children"))


def primary_menu(menus):
    for m in menus:
        if m.get("location") == "primary" or m.get("id") == "primary":
            return m
    return menus[0] if menus else None


def check_navigation(bp, errors, warnings):
    """Single page: uma pagina main, header sticky, menu de ancoras que
    batem com sections[].anchor. Multipaginas: header conforme a referencia."""
    project = bp.get("project") or {}
    theme = bp.get("theme") or {}
    structure = project.get("site_structure")
    behavior = theme.get("header_behavior")
    menus = [m for m in (bp.get("menus") or []) if isinstance(m, dict)]
    pages = [p for p in (bp.get("pages") or []) if isinstance(p, dict)]

    if structure not in VALID_SITE_STRUCTURES:
        errors.append(
            f"project.site_structure ausente ou invalido: {structure!r} (validos: "
            f"{sorted(VALID_SITE_STRUCTURES)}). Decida no passo 1; na duvida, registre "
            "uncertainty bloqueante (references/navigation.md)."
        )
    if behavior not in VALID_HEADER_BEHAVIORS:
        errors.append(
            f"theme.header_behavior ausente ou invalido: {behavior!r} (validos: "
            f"{sorted(VALID_HEADER_BEHAVIORS)})."
        )

    for page in pages:
        role = page.get("role", "main")
        if role not in VALID_PAGE_ROLES:
            errors.append(f"pages[{page.get('id')}].role invalido: {role!r} (validos: {sorted(VALID_PAGE_ROLES)}).")

    for m in menus:
        for item in iter_menu_items(m.get("items")):
            label = item.get("label", "?")
            itype = item.get("type")
            target = str(item.get("target") or "").strip()
            if itype and itype not in VALID_MENU_ITEM_TYPES:
                errors.append(f"menus[{m.get('id')}] item '{label}': type invalido {itype!r} (validos: {sorted(VALID_MENU_ITEM_TYPES)}).")
            if target in ("", "#"):
                errors.append(f"menus[{m.get('id')}] item '{label}' sem destino (target vazio ou '#').")
            if itype == "anchor" and not target.startswith("#"):
                errors.append(f"menus[{m.get('id')}] item '{label}': type anchor exige target '#<anchor>' (recebido {target!r}).")

    main_pages = [p for p in pages if p.get("role", "main") == "main"]

    if structure == "single_page":
        if behavior != "sticky":
            errors.append(
                "single_page exige theme.header_behavior: sticky - o menu tem de acompanhar a "
                "rolagem e ficar sempre visivel (references/navigation.md)."
            )
        if len(main_pages) != 1:
            errors.append(
                f"single_page exige exatamente 1 pagina com role main (encontradas {len(main_pages)}: "
                f"{[p.get('id') for p in main_pages]}). Politica de privacidade, 404 etc. usam role: auxiliary."
            )
        anchors = {}
        for page in main_pages[:1]:
            for sec in page.get("sections") or []:
                anchor = sec.get("anchor")
                if not anchor:
                    continue
                anchor = str(anchor)
                if not ANCHOR_RE.match(anchor):
                    errors.append(f"sections[{sec.get('id')}].anchor {anchor!r}: use slug minusculo sem acento (ex.: 'servicos').")
                if anchor in RESERVED_ANCHORS:
                    errors.append(f"sections[{sec.get('id')}].anchor {anchor!r} e reservado pelo tema ({sorted(RESERVED_ANCHORS)}).")
                if anchor in anchors:
                    errors.append(f"anchor {anchor!r} repetido em {anchors[anchor]} e {sec.get('id')} - ids precisam ser unicos.")
                anchors[anchor] = sec.get("id")
        menu = primary_menu(menus)
        if not menu:
            errors.append("single_page sem menu principal em menus[] - o header precisa levar as secoes.")
        else:
            items = list(iter_menu_items(menu.get("items")))
            anchor_items = [i for i in items if i.get("type") == "anchor"]
            if not anchor_items:
                errors.append(
                    f"menus[{menu.get('id')}]: single_page sem nenhum item type anchor - os itens "
                    "devem levar as secoes da pagina ('#servicos')."
                )
            for item in anchor_items:
                frag = str(item.get("target") or "").lstrip("#")
                if frag and frag not in anchors:
                    errors.append(
                        f"menus[{menu.get('id')}] item '{item.get('label')}' aponta para '#{frag}', "
                        f"mas nenhuma secao da pagina tem anchor '{frag}' (ancoras: {sorted(anchors)})."
                    )
            others = [i.get("label") for i in items if i.get("type") in ("page", "archive")]
            if others:
                warnings.append(
                    f"menus[{menu.get('id')}]: single_page com itens que levam a outra pagina {others} - "
                    "confirme que sao paginas auxiliares e nao secoes da Home."
                )
    elif structure == "multi_page":
        anchors = {str(s.get("anchor")) for p in pages for s in (p.get("sections") or []) if s.get("anchor")}
        for m in menus:
            for item in iter_menu_items(m.get("items")):
                target = str(item.get("target") or "")
                if item.get("type") == "anchor" and target.lstrip("#") not in anchors:
                    errors.append(
                        f"menus[{m.get('id')}] item '{item.get('label')}' aponta para {target!r}, "
                        "mas nenhuma secao tem esse anchor."
                    )
        if len(main_pages) == 1 and pages:
            warnings.append(
                "multi_page com uma unica pagina main - se o menu leva a secoes da mesma pagina, "
                "a estrutura e single_page (header sticky obrigatorio)."
            )


VALID_CAROUSEL_KINDS = {"hero_banner", "cards", "testimonials", "logos", "gallery", "other"}
VALID_CAROUSEL_EVIDENCE = {"dots", "arrows", "counter", "progress_bar", "cut_item", "user"}
VALID_SLIDES_CONTENT = {"reference", "user", "demo"}


def check_carousels(bp, errors, warnings):
    """Todo carrossel identificado na referencia tem comportamento decidido
    (nada de autoplay "talvez"), pausa quando gira sozinho, slides editaveis
    e evidencia visual registrada."""
    if "carousels" not in bp:
        errors.append(
            "Secao 'carousels' ausente - registre cada carrossel/banner rotativo da referencia, "
            "ou 'carousels: []' depois de conferir que nao ha nenhum (references/carousels.md)."
        )
        return
    entries = bp.get("carousels") or []
    sections = {s.get("id"): p for p in (bp.get("pages") or []) for s in (p.get("sections") or []) if s.get("id")}
    editable = {e.get("target"): e for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    blocking = {u.get("subject") for u in (bp.get("uncertainties") or [])
                if u.get("blocking") and u.get("status") == "pending"}
    seen = set()
    for i, c in enumerate(entries):
        cid = c.get("id") or f"<carousels[{i}]>"
        where = f"carousels[{cid}]"
        if cid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(cid)
        if c.get("section") not in sections:
            errors.append(f"{where}.section {c.get('section')!r} nao e id de pages[].sections.")
        elif c.get("section") not in editable:
            errors.append(f"{where}: a secao {c.get('section')!r} nao tem destino em editable_content (slides editaveis no admin).")
        if c.get("kind") not in VALID_CAROUSEL_KINDS:
            errors.append(f"{where}.kind invalido: {c.get('kind')!r} (validos: {sorted(VALID_CAROUSEL_KINDS)}).")
        evidence = c.get("evidence") or []
        bad_evidence = [e for e in evidence if e not in VALID_CAROUSEL_EVIDENCE]
        if not evidence or bad_evidence:
            errors.append(
                f"{where}.evidence: informe o que na referencia indica carrossel "
                f"({sorted(VALID_CAROUSEL_EVIDENCE)}){' - invalidos: ' + str(bad_evidence) if bad_evidence else ''}."
            )
        count = c.get("slide_count")
        if not isinstance(count, int) or count < 2:
            errors.append(f"{where}.slide_count deve ser inteiro >= 2 (com bolinhas, e o numero de bolinhas).")
        autoplay = c.get("autoplay")
        if not isinstance(autoplay, bool):
            if cid in blocking or c.get("section") in blocking:
                warnings.append(f"{where}.autoplay pendente de resposta do usuario (uncertainty bloqueante).")
            else:
                errors.append(
                    f"{where}.autoplay e {autoplay!r}: a imagem nao mostra se gira sozinho - decida com o "
                    "usuario (true/false) ou registre uncertainty bloqueante com subject igual ao id."
                )
        controls = c.get("controls") or {}
        if autoplay is True:
            if controls.get("pause") is not True:
                errors.append(f"{where}: autoplay exige controls.pause: true (WCAG 2.2.2 - pausar, parar, ocultar).")
            interval = c.get("interval_ms")
            if not isinstance(interval, int) or interval < 3000:
                errors.append(f"{where}.interval_ms deve ser inteiro >= 3000 com autoplay (recomendado >= 5000).")
            elif interval < 5000:
                warnings.append(f"{where}.interval_ms {interval} < 5000: pouco tempo para ler o slide.")
        if not controls.get("arrows") and not controls.get("dots"):
            warnings.append(f"{where}: sem setas nem bolinhas - so arrastar; confirme que a referencia e assim.")
        per_view = c.get("per_view") or {}
        for bp_name in ("desktop", "tablet", "mobile"):
            value = per_view.get(bp_name)
            if not isinstance(value, int) or value < 1:
                errors.append(f"{where}.per_view.{bp_name} deve ser inteiro >= 1.")
        if c.get("kind") == "hero_banner" and per_view.get("desktop") not in (None, 1):
            errors.append(f"{where}: hero_banner mostra 1 slide por vez (per_view.desktop: 1).")
        if not c.get("storage"):
            errors.append(f"{where}.storage: onde os slides sao editados (ex.: 'repeater:home_banner_slides' ou 'post_type:testimonial').")
        content = c.get("slides_content")
        if content not in VALID_SLIDES_CONTENT:
            errors.append(f"{where}.slides_content invalido: {content!r} (validos: {sorted(VALID_SLIDES_CONTENT)}).")
        elif content == "demo":
            warnings.append(
                f"{where}: slides alem do primeiro sao DEMO - liste em 'Conteudo demo identificado' do "
                "VALIDATION.md e peca o conteudo real antes de publicar."
            )


VALID_FORM_PURPOSES = {"contact", "quote", "newsletter", "booking", "job_application", "other"}
VALID_FIELD_TYPES = {"text", "email", "tel", "url", "number", "date", "textarea", "select",
                     "checkbox", "radio", "file"}
VALID_FIELD_WIDTHS = {"full", "half"}
VALID_PRIVACY_NOTICE = {"checkbox", "text"}
VALID_ANTI_SPAM = {"akismet", "recaptcha_v3", "turnstile", "none_local"}
FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", re.I)
# Termos reservados do WordPress: campo com esse nome, enviado sem JS (o
# CF7 cai para POST na propria pagina), faz a pagina responder 404.
WP_RESERVED_TERMS = {
    "attachment", "attachment_id", "author", "author_name", "calendar", "cat", "category",
    "category_name", "cpage", "day", "debug", "error", "exact", "feed", "hour", "m",
    "minute", "monthnum", "more", "name", "nav_menu", "nonce", "offset", "order",
    "orderby", "p", "page", "page_id", "paged", "pagename", "pb", "perm", "post",
    "post_format", "post_status", "post_tag", "post_type", "posts", "preview", "robots",
    "s", "search", "second", "sentence", "static", "tag", "tag_id", "taxonomy", "tb",
    "term", "theme", "type", "w", "year",
}
AUTOCOMPLETE_HINT = {"email": "email", "tel": "tel", "url": "url"}


def _pending_blocking_subjects(bp):
    return {u.get("subject") for u in (bp.get("uncertainties") or [])
            if u.get("blocking") and u.get("status") == "pending"}


def _section_ids(bp):
    return {s.get("id") for p in (bp.get("pages") or []) for s in (p.get("sections") or []) if s.get("id")}


def check_forms(bp, errors, warnings):
    """Formulario estruturado: cada campo com tipo, rotulo literal e nome
    seguro; destino real (nunca inventado); aviso de privacidade; anti-spam."""
    forms = bp.get("forms") or []
    if not isinstance(forms, list):
        errors.append("forms deve ser uma lista.")
        return
    sections = _section_ids(bp)
    editable = {e.get("target"): e for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    blocking = _pending_blocking_subjects(bp)
    for i, form in enumerate(forms):
        if not isinstance(form, dict):
            errors.append(f"forms[{i}] deve ser um objeto.")
            continue
        fid = form.get("id") or f"<forms[{i}]>"
        where = f"forms[{fid}]"
        if form.get("section") not in sections:
            errors.append(f"{where}.section {form.get('section')!r} nao e id de pages[].sections.")
        elif (editable.get(form.get("section")) or {}).get("storage") != "form":
            warnings.append(f"{where}: editable_content[{form.get('section')}] deveria ter storage: form (Contato > Formularios).")
        if form.get("purpose") not in VALID_FORM_PURPOSES:
            errors.append(f"{where}.purpose invalido: {form.get('purpose')!r} (validos: {sorted(VALID_FORM_PURPOSES)}).")
        dest = str(form.get("destination") or "")
        if not EMAIL_RE.match(dest):
            if fid in blocking:
                warnings.append(f"{where}.destination pendente de resposta do usuario (uncertainty bloqueante).")
            else:
                errors.append(
                    f"{where}.destination {dest!r}: informe o e-mail real que recebe as mensagens, ou registre "
                    "uncertainty bloqueante com subject igual ao id do formulario - nunca invente."
                )
        if not form.get("submit_label"):
            errors.append(f"{where}.submit_label: texto literal do botao na referencia.")
        anti_spam = form.get("anti_spam")
        if anti_spam not in VALID_ANTI_SPAM:
            errors.append(f"{where}.anti_spam invalido: {anti_spam!r} (validos: {sorted(VALID_ANTI_SPAM)}).")
        elif anti_spam == "none_local":
            warnings.append(f"{where}: anti_spam none_local - defina Akismet, reCAPTCHA v3 ou Turnstile antes de publicar.")

        fields = form.get("fields") or []
        if not fields:
            errors.append(f"{where}.fields vazio - liste cada campo visivel na referencia.")
        names = set()
        email_fields = []
        for f in fields:
            if not isinstance(f, dict):
                errors.append(f"{where}.fields: item {f!r} deve ser objeto (name, type, label...) - schema 1.5.")
                continue
            name = str(f.get("name") or "")
            fw = f"{where}.fields[{name or '?'}]"
            if not FIELD_NAME_RE.match(name):
                errors.append(f"{fw}: name deve ser minusculo, sem acento nem espaco (ex.: contato_nome).")
            elif name in WP_RESERVED_TERMS:
                errors.append(f"{fw}: '{name}' e termo reservado do WordPress (envio sem JS da 404) - use prefixo, ex.: contato_{name}.")
            if name in names:
                errors.append(f"{fw}: name repetido.")
            names.add(name)
            ftype = f.get("type")
            if ftype not in VALID_FIELD_TYPES:
                errors.append(f"{fw}.type invalido: {ftype!r} (validos: {sorted(VALID_FIELD_TYPES)}).")
            if not f.get("label"):
                errors.append(
                    f"{fw}.label obrigatorio - texto literal da referencia; se ela so mostra placeholder, "
                    "repita-o aqui com label_visible: false (rotulo para leitor de tela)."
                )
            if f.get("width") is not None and f.get("width") not in VALID_FIELD_WIDTHS:
                errors.append(f"{fw}.width invalido: {f.get('width')!r} (full | half).")
            if ftype in {"select", "checkbox", "radio"} and not f.get("options"):
                errors.append(f"{fw}: {ftype} exige options (textos literais da referencia).")
            if ftype == "file" and (not f.get("accept") or not f.get("max_size")):
                errors.append(f"{fw}: file exige accept (ex.: [pdf, docx]) e max_size (ex.: 5mb).")
            if ftype == "email":
                email_fields.append(name)
            hint = AUTOCOMPLETE_HINT.get(ftype)
            if hint and not f.get("autocomplete"):
                warnings.append(f"{fw}: sem autocomplete (sugestao: {hint}) - WCAG 1.3.5.")
        reply = form.get("reply_to_field")
        if email_fields and reply not in email_fields:
            warnings.append(f"{where}.reply_to_field deveria ser o campo de e-mail ({email_fields[0]}) - responder a mensagem cai no visitante.")
        if form.get("subject_field") and form.get("subject_field") not in names:
            errors.append(f"{where}.subject_field {form.get('subject_field')!r} nao e um dos campos.")

        privacy = form.get("privacy") or {}
        if privacy.get("notice") not in VALID_PRIVACY_NOTICE:
            errors.append(
                f"{where}.privacy.notice: checkbox | text - formulario coleta dado pessoal e precisa de aviso "
                "com link para a politica de privacidade (LGPD)."
            )
        else:
            if not privacy.get("policy_page"):
                errors.append(f"{where}.privacy.policy_page: slug da pagina da politica de privacidade.")
            elif privacy.get("policy_page") not in {str(p.get("slug") or "").strip("/") for p in (bp.get("pages") or [])}:
                warnings.append(f"{where}: a pagina '{privacy.get('policy_page')}' nao esta em pages[] (role: auxiliary).")
            if not privacy.get("text"):
                errors.append(f"{where}.privacy.text: texto do aviso (literal da referencia, ou proposto e aprovado).")
            if privacy.get("shown_in_reference") is False:
                warnings.append(f"{where}: aviso de privacidade nao aparece na referencia - registre como desvio intencional aprovado.")


VALID_MAP_PROVIDERS = {"google", "openstreetmap"}
VALID_MAP_EVIDENCE = {"tiles", "pin", "zoom_controls", "provider_logo", "view_larger_link", "user"}
VALID_MAP_LOAD = {"click", "auto"}


def check_maps(bp, errors, warnings):
    """Mapa: identificado por sinais visuais, endereco da fonte unica,
    fachada com proporcao fixa e carregamento so no clique (padrao)."""
    if "maps" not in bp:
        errors.append(
            "Secao 'maps' ausente - registre cada mapa da referencia, ou 'maps: []' depois de conferir "
            "que nao ha nenhum (references/maps.md)."
        )
        return
    sections = _section_ids(bp)
    media_ids = {m.get("id") for m in (bp.get("media") or []) if isinstance(m, dict)}
    global_fields = set()
    for e in bp.get("editable_content") or []:
        if isinstance(e, dict) and e.get("storage") == "options_page":
            global_fields |= set(e.get("fields") or [])
    seen = set()
    for i, m in enumerate(bp.get("maps") or []):
        mid = m.get("id") or f"<maps[{i}]>"
        where = f"maps[{mid}]"
        if mid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(mid)
        if m.get("section") not in sections:
            errors.append(f"{where}.section {m.get('section')!r} nao e id de pages[].sections.")
        evidence = m.get("evidence") or []
        if not evidence or any(e not in VALID_MAP_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica mapa ({sorted(VALID_MAP_EVIDENCE)}).")
        provider = m.get("provider")
        if provider not in VALID_MAP_PROVIDERS:
            errors.append(f"{where}.provider invalido: {provider!r} (validos: {sorted(VALID_MAP_PROVIDERS)}).")
        address_field = m.get("address_field")
        if not address_field:
            errors.append(f"{where}.address_field: campo da pagina de opcoes com o endereco (fonte unica, ex.: company_address).")
        elif global_fields and address_field not in global_fields:
            errors.append(f"{where}.address_field {address_field!r} nao esta em nenhum editable_content com storage options_page.")
        if provider == "openstreetmap" and not (m.get("lat_field") and m.get("lng_field")):
            errors.append(f"{where}: openstreetmap exige lat_field e lng_field (coordenadas editaveis no admin).")
        load = m.get("load")
        if load not in VALID_MAP_LOAD:
            errors.append(f"{where}.load: click (padrao: so carrega ao clicar) | auto.")
        elif load == "auto":
            warnings.append(
                f"{where}: load auto carrega script e cookies do provedor sem o visitante pedir - so com "
                "decisao aprovada (ex.: banner de consentimento) registrada em decisions."
            )
        if not m.get("aspect_ratio"):
            errors.append(f"{where}.aspect_ratio obrigatorio (proporcao da regiao na referencia, ex.: '16:9').")
        facade = m.get("facade_media")
        if load == "click" and not facade:
            errors.append(f"{where}.facade_media: id em media[] da imagem estatica mostrada antes do clique.")
        elif facade and facade not in media_ids:
            errors.append(f"{where}.facade_media {facade!r} nao existe em media[].")
        if m.get("directions_link") is not True:
            warnings.append(f"{where}: sem link 'Como chegar' - o mapa embutido nao e acessivel; garanta o endereco em texto na pagina.")


VALID_GALLERY_LAYOUTS = {"grid", "masonry", "featured_thumbs"}
VALID_GALLERY_EVIDENCE = {"photo_grid", "thumbnails", "more_overlay", "zoom_icon", "view_all_link", "user"}
VALID_VIDEO_KINDS = {"embed", "file", "background"}
VALID_VIDEO_SOURCES = {"youtube", "vimeo", "file"}
VALID_VIDEO_EVIDENCE = {"play_button", "duration_badge", "progress_bar", "provider_logo", "watch_cta", "user"}


def _decided(value, item_id, blocking, where, field, errors, warnings, question):
    """Booleano que a imagem nao responde: true/false, ou uncertainty bloqueante."""
    if isinstance(value, bool):
        return True
    if item_id in blocking:
        warnings.append(f"{where}.{field} pendente de resposta do usuario (uncertainty bloqueante).")
    else:
        errors.append(f"{where}.{field} e {value!r}: {question} Decida com o usuario (true/false) ou registre "
                      "uncertainty bloqueante com subject igual ao id.")
    return False


def check_galleries(bp, errors, warnings):
    """Galeria: sinais visuais, quantidade, lightbox decidido, fotos editaveis."""
    if "galleries" not in bp:
        errors.append(
            "Secao 'galleries' ausente - registre cada galeria de fotos da referencia, ou 'galleries: []' "
            "depois de conferir que nao ha nenhuma (references/galleries.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    blocking = _pending_blocking_subjects(bp)
    seen = set()
    for i, g in enumerate(bp.get("galleries") or []):
        gid = g.get("id") or f"<galleries[{i}]>"
        where = f"galleries[{gid}]"
        if gid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(gid)
        if g.get("section") not in sections:
            errors.append(f"{where}.section {g.get('section')!r} nao e id de pages[].sections.")
        elif g.get("section") not in editable:
            errors.append(f"{where}: a secao {g.get('section')!r} nao tem destino em editable_content (fotos editaveis no admin).")
        if g.get("layout") not in VALID_GALLERY_LAYOUTS:
            errors.append(f"{where}.layout invalido: {g.get('layout')!r} (validos: {sorted(VALID_GALLERY_LAYOUTS)}; "
                          "galeria em carrossel vai em carousels[] com kind gallery).")
        evidence = g.get("evidence") or []
        if not evidence or any(e not in VALID_GALLERY_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica galeria ({sorted(VALID_GALLERY_EVIDENCE)}).")
        visible = g.get("visible_count")
        if not isinstance(visible, int) or visible < 1:
            errors.append(f"{where}.visible_count: quantas fotos aparecem na referencia (inteiro >= 1).")
        total = g.get("total_count")
        if total is not None and (not isinstance(total, int) or (isinstance(visible, int) and total < visible)):
            errors.append(f"{where}.total_count deve ser inteiro >= visible_count (ou omitido se igual).")
        if "more_overlay" in evidence and total is None:
            errors.append(f"{where}: a referencia mostra '+N' - registre total_count (visible_count + N).")
        _decided(g.get("lightbox"), gid, blocking, where, "lightbox", errors, warnings,
                 "a imagem nao mostra se clicar amplia a foto.")
        if g.get("layout") != "masonry" and not g.get("aspect_ratio"):
            errors.append(f"{where}.aspect_ratio obrigatorio (proporcao das fotos na referencia, ex.: '4:3').")
        per_row = g.get("per_row") or {}
        for name in ("desktop", "tablet", "mobile"):
            if not isinstance(per_row.get(name), int) or per_row.get(name) < 1:
                errors.append(f"{where}.per_row.{name} deve ser inteiro >= 1.")
        if not g.get("storage"):
            errors.append(f"{where}.storage: onde as fotos sao editadas (ex.: 'acf_gallery:project_gallery').")
        if not isinstance(g.get("captions"), bool):
            errors.append(f"{where}.captions: true/false (legenda visivel na referencia?).")


def check_videos(bp, errors, warnings):
    """Video: sinais visuais (ou confirmacao do usuario para fundo), fonte
    editavel, capa, legendas decididas, carregamento so no clique."""
    if "videos" not in bp:
        errors.append(
            "Secao 'videos' ausente - registre cada video da referencia, ou 'videos: []' depois de conferir "
            "que nao ha nenhum (references/videos.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    media_ids = {m.get("id") for m in (bp.get("media") or []) if isinstance(m, dict)}
    blocking = _pending_blocking_subjects(bp)
    seen = set()
    for i, v in enumerate(bp.get("videos") or []):
        vid = v.get("id") or f"<videos[{i}]>"
        where = f"videos[{vid}]"
        if vid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(vid)
        if v.get("section") not in sections:
            errors.append(f"{where}.section {v.get('section')!r} nao e id de pages[].sections.")
        elif v.get("section") not in editable:
            errors.append(f"{where}: a secao {v.get('section')!r} nao tem destino em editable_content (video editavel no admin).")
        kind = v.get("kind")
        source = v.get("source")
        if kind not in VALID_VIDEO_KINDS:
            errors.append(f"{where}.kind invalido: {kind!r} (validos: {sorted(VALID_VIDEO_KINDS)}).")
        if source not in VALID_VIDEO_SOURCES:
            errors.append(f"{where}.source invalido: {source!r} (validos: {sorted(VALID_VIDEO_SOURCES)}).")
        if kind in {"file", "background"} and source != "file":
            errors.append(f"{where}: kind {kind} usa arquivo proprio (source: file); YouTube/Vimeo so com kind embed.")
        if kind == "embed" and source == "file":
            errors.append(f"{where}: kind embed e para YouTube/Vimeo; arquivo proprio usa kind file.")
        evidence = v.get("evidence") or []
        if not evidence or any(e not in VALID_VIDEO_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica video ({sorted(VALID_VIDEO_EVIDENCE)}).")
        if kind == "background" and "user" not in evidence:
            errors.append(
                f"{where}: video de fundo nao aparece numa imagem estatica (e indistinguivel de foto) - "
                "so com confirmacao do usuario (evidence: [user])."
            )
        if source in {"youtube", "vimeo"} and not v.get("url_field"):
            errors.append(f"{where}.url_field: campo do admin com a URL do video (o tema aceita qualquer formato do provedor).")
        if source == "file" and not v.get("file_field"):
            errors.append(f"{where}.file_field: campo do admin com o arquivo (Biblioteca de Midia).")
        if not v.get("poster_media"):
            errors.append(f"{where}.poster_media: id em media[] da capa (o frame que aparece na referencia).")
        elif v.get("poster_media") not in media_ids:
            errors.append(f"{where}.poster_media {v.get('poster_media')!r} nao existe em media[].")
        if not v.get("aspect_ratio") and kind != "background":
            errors.append(f"{where}.aspect_ratio obrigatorio (ex.: '16:9').")
        if kind != "background":
            if not v.get("title_field") and not v.get("title"):
                errors.append(f"{where}: title_field (ou title) - nome acessivel do video ('Reproduzir video: <titulo>').")
            if _decided(v.get("captions"), vid, blocking, where, "captions", errors, warnings,
                        "o video tem fala/informacao? Precisa de legenda (WCAG 1.2.2)."):
                if v.get("captions") and source == "file" and not v.get("captions_field"):
                    errors.append(f"{where}: legenda em arquivo proprio exige captions_field (anexo .vtt).")
                if v.get("captions") is False:
                    warnings.append(f"{where}: sem legenda - so se o video nao tiver fala nem informacao so em audio.")
        if kind == "embed" and v.get("load", "click") != "click":
            warnings.append(f"{where}: load auto carrega o player e cookies do provedor sem pedido - so com decisao aprovada.")


VALID_ACCORDION_EVIDENCE = {"plus_minus", "chevron", "expanded_item", "question_list", "user"}
VALID_TABS_EVIDENCE = {"tab_row", "active_indicator", "segmented_control", "user"}
VALID_TABS_MOBILE = {"scroll", "stack"}
VALID_ITEMS_CONTENT = {"reference", "user", "demo"}


def _check_disclosure_common(item, where, sections, editable, errors, warnings):
    if item.get("section") not in sections:
        errors.append(f"{where}.section {item.get('section')!r} nao e id de pages[].sections.")
    elif item.get("section") not in editable:
        errors.append(f"{where}: a secao {item.get('section')!r} nao tem destino em editable_content (itens editaveis no admin).")
    if not item.get("storage"):
        errors.append(f"{where}.storage: onde os itens sao editados (ex.: 'repeater:home_faq_items' ou 'post_type:faq').")
    content = item.get("items_content")
    if content not in VALID_ITEMS_CONTENT:
        errors.append(f"{where}.items_content invalido: {content!r} (validos: {sorted(VALID_ITEMS_CONTENT)}).")
    elif content == "demo":
        warnings.append(f"{where}: conteudo dos itens fechados e DEMO - liste no VALIDATION.md e peca o texto real.")
    level = item.get("heading_level", 3)
    if not isinstance(level, int) or not 2 <= level <= 6:
        errors.append(f"{where}.heading_level deve ser 2..6 (nivel do titulo de cada item na hierarquia da pagina).")


def check_accordions(bp, errors, warnings):
    """Acordeao/FAQ: sinais visuais, quantidade, o que esta aberto na
    referencia, 'um por vez' decidido, conteudo dos fechados de onde vem."""
    if "accordions" not in bp:
        errors.append(
            "Secao 'accordions' ausente - registre cada acordeao/FAQ da referencia, ou 'accordions: []' "
            "depois de conferir que nao ha nenhum (references/disclosures.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    blocking = _pending_blocking_subjects(bp)
    seen = set()
    for i, acc in enumerate(bp.get("accordions") or []):
        aid = acc.get("id") or f"<accordions[{i}]>"
        where = f"accordions[{aid}]"
        if aid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(aid)
        _check_disclosure_common(acc, where, sections, editable, errors, warnings)
        evidence = acc.get("evidence") or []
        if not evidence or any(e not in VALID_ACCORDION_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica acordeao ({sorted(VALID_ACCORDION_EVIDENCE)}).")
        count = acc.get("item_count")
        if not isinstance(count, int) or count < 1:
            errors.append(f"{where}.item_count: quantos itens a referencia mostra (inteiro >= 1).")
        opened = acc.get("open_in_reference")
        if not isinstance(opened, list) or any(not isinstance(n, int) or n < 1 or (isinstance(count, int) and n > count) for n in opened):
            errors.append(f"{where}.open_in_reference: lista dos itens abertos na referencia (1 = primeiro; [] se todos fechados).")
        exclusive = acc.get("exclusive")
        if _decided(exclusive, aid, blocking, where, "exclusive", errors, warnings,
                    "a imagem nao mostra se abrir um fecha o outro."):
            if exclusive and isinstance(opened, list) and len(opened) > 1:
                errors.append(f"{where}: exclusive true com {len(opened)} itens abertos na referencia - contraditorio.")
        if not isinstance(acc.get("faq"), bool):
            errors.append(f"{where}.faq: true se os itens sao pergunta/resposta (FAQ), false se nao.")
        if acc.get("faq") and acc.get("structured_data") is not False and not acc.get("structured_data"):
            warnings.append(f"{where}: FAQ sem structured_data declarado - o padrao e gerar o JSON-LD FAQPage (sem prometer resultado rico do Google).")


def check_tabs(bp, errors, warnings):
    """Abas: sinais, quantidade, aba ativa na referencia, comportamento no
    celular decidido, conteudo dos paineis nao visiveis."""
    if "tabs" not in bp:
        errors.append(
            "Secao 'tabs' ausente - registre cada conjunto de abas da referencia, ou 'tabs: []' depois de "
            "conferir que nao ha nenhum (references/disclosures.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    seen = set()
    for i, t in enumerate(bp.get("tabs") or []):
        tid = t.get("id") or f"<tabs[{i}]>"
        where = f"tabs[{tid}]"
        if tid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(tid)
        _check_disclosure_common(t, where, sections, editable, errors, warnings)
        evidence = t.get("evidence") or []
        if not evidence or any(e not in VALID_TABS_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica abas ({sorted(VALID_TABS_EVIDENCE)}).")
        count = t.get("tab_count")
        if not isinstance(count, int) or count < 2:
            errors.append(f"{where}.tab_count: quantas abas a referencia mostra (inteiro >= 2).")
        active = t.get("active_in_reference")
        if not isinstance(active, int) or active < 1 or (isinstance(count, int) and active > count):
            errors.append(f"{where}.active_in_reference: qual aba esta ativa na referencia (1 = primeira).")
        if t.get("mobile") not in VALID_TABS_MOBILE:
            errors.append(
                f"{where}.mobile: scroll (abas rolam na horizontal) | stack (paineis empilhados) - "
                "da referencia mobile ou decisao aprovada."
            )


VALID_TABLE_KINDS = {"data", "comparison"}
VALID_TABLE_EVIDENCE = {"grid_lines", "header_row", "zebra_rows", "aligned_numbers", "check_marks", "user"}
VALID_COLUMN_TYPES = {"text", "number", "currency", "check"}
VALID_COLUMN_ALIGN = {"start", "end", "center"}
VALID_TABLE_MOBILE = {"scroll", "cards"}
VALID_PRICING_EVIDENCE = {"currency_symbol", "period_suffix", "plan_cards", "featured_badge", "strikethrough",
                          "billing_toggle", "installments", "user"}
VALID_BILLING = {"monthly", "quarterly", "semiannual", "yearly", "once"}
VALID_PRICE_SOURCE = {"user", "demo"}


def check_tables(bp, errors, warnings):
    """Tabela de dados: sinais, colunas tipadas com rotulo literal, legenda
    (caption) para leitor de tela, comportamento no celular decidido."""
    if "tables" not in bp:
        errors.append(
            "Secao 'tables' ausente - registre cada tabela de dados da referencia, ou 'tables: []' depois "
            "de conferir que nao ha nenhuma (references/tables-pricing.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    seen = set()
    for i, t in enumerate(bp.get("tables") or []):
        tid = t.get("id") or f"<tables[{i}]>"
        where = f"tables[{tid}]"
        if tid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(tid)
        _check_disclosure_common(t, where, sections, editable, errors, warnings)
        if t.get("kind") not in VALID_TABLE_KINDS:
            errors.append(f"{where}.kind invalido: {t.get('kind')!r} (validos: {sorted(VALID_TABLE_KINDS)}).")
        evidence = t.get("evidence") or []
        if not evidence or any(e not in VALID_TABLE_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica tabela ({sorted(VALID_TABLE_EVIDENCE)}).")
        if not t.get("caption"):
            errors.append(
                f"{where}.caption: nome da tabela (literal da referencia; se ela nao mostra, proponha e use "
                "caption_visible: false) - leitor de tela anuncia a tabela por ele."
            )
        columns = t.get("columns") or []
        if len(columns) < 2:
            errors.append(f"{where}.columns: ao menos 2 colunas (key, label literal, type).")
        keys = set()
        for col in columns:
            if not isinstance(col, dict) or not col.get("key") or not col.get("label"):
                errors.append(f"{where}.columns: cada coluna precisa de key e label (literal) - recebido {col!r}.")
                continue
            if col["key"] in keys:
                errors.append(f"{where}.columns: key {col['key']!r} repetida.")
            keys.add(col["key"])
            if col.get("type", "text") not in VALID_COLUMN_TYPES:
                errors.append(f"{where}.columns[{col['key']}].type invalido: {col.get('type')!r} (validos: {sorted(VALID_COLUMN_TYPES)}).")
            if col.get("align") is not None and col.get("align") not in VALID_COLUMN_ALIGN:
                errors.append(f"{where}.columns[{col['key']}].align invalido: {col.get('align')!r}.")
        if t.get("kind") == "comparison" and not any(c.get("type") == "check" for c in columns if isinstance(c, dict)):
            warnings.append(f"{where}: comparativo sem coluna type check (✓/✗) - confirme.")
        if not isinstance(t.get("row_count"), int) or t.get("row_count") < 1:
            errors.append(f"{where}.row_count: quantas linhas a referencia mostra (inteiro >= 1).")
        if not isinstance(t.get("row_header"), bool):
            errors.append(f"{where}.row_header: true se a primeira coluna nomeia a linha (vira <th scope=row>).")
        if t.get("mobile") not in VALID_TABLE_MOBILE:
            errors.append(f"{where}.mobile: scroll (rola dentro da regiao) | cards (cada linha vira card) - decida.")
        if any(isinstance(c, dict) and c.get("type") == "currency" for c in columns):
            if t.get("price_source") not in VALID_PRICE_SOURCE:
                errors.append(f"{where}.price_source: user (confirmado) | demo - valores em R$ da referencia podem ser ficticios.")


def check_pricing(bp, errors, warnings):
    """Planos/precos: preco e dado de negocio - real so com confirmacao."""
    if "pricing" not in bp:
        errors.append(
            "Secao 'pricing' ausente - registre cada bloco de planos/precos da referencia, ou 'pricing: []' "
            "depois de conferir que nao ha nenhum (references/tables-pricing.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    table_ids = {t.get("id") for t in (bp.get("tables") or []) if isinstance(t, dict)}
    seen = set()
    for i, p in enumerate(bp.get("pricing") or []):
        pid = p.get("id") or f"<pricing[{i}]>"
        where = f"pricing[{pid}]"
        if pid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(pid)
        if p.get("section") not in sections:
            errors.append(f"{where}.section {p.get('section')!r} nao e id de pages[].sections.")
        elif p.get("section") not in editable:
            errors.append(f"{where}: a secao {p.get('section')!r} nao tem destino em editable_content (precos editaveis no admin).")
        if not p.get("storage"):
            errors.append(f"{where}.storage: onde os planos sao editados (ex.: 'repeater:home_pricing_plans' ou 'post_type:plan').")
        evidence = p.get("evidence") or []
        if not evidence or any(e not in VALID_PRICING_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica precos ({sorted(VALID_PRICING_EVIDENCE)}).")
        count = p.get("plan_count")
        if not isinstance(count, int) or count < 1:
            errors.append(f"{where}.plan_count: quantos planos/precos a referencia mostra (inteiro >= 1).")
        source = p.get("price_source")
        if source not in VALID_PRICE_SOURCE:
            errors.append(
                f"{where}.price_source {source!r}: user (o usuario confirmou os valores) | demo (ficticio, marcado). "
                "Preco visto na referencia pode ser mockup do designer - nunca vai ao ar como real sem confirmacao."
            )
        elif source == "demo":
            warnings.append(f"{where}: precos DEMO - liste em 'Conteudo demo identificado' do VALIDATION.md; nao publique sem os valores reais.")
        if p.get("currency", "BRL") != "BRL":
            warnings.append(f"{where}.currency {p.get('currency')!r}: o esqueleto formata BRL; outra moeda exige ajuste em inc/pricing.php.")
        billing = p.get("billing") or []
        if not billing or any(b not in VALID_BILLING for b in billing):
            errors.append(f"{where}.billing: periodos de cobranca ({sorted(VALID_BILLING)}), ex.: [monthly] ou [monthly, yearly].")
        elif len(billing) > 1:
            if p.get("default_billing") not in billing:
                errors.append(f"{where}.default_billing: qual periodo aparece selecionado na referencia (um de {billing}).")
            if "billing_toggle" not in evidence and "user" not in evidence:
                warnings.append(f"{where}: varios periodos sem seletor na referencia (evidence billing_toggle) - confirme.")
        elif "billing_toggle" in evidence:
            errors.append(f"{where}: a referencia mostra seletor de periodo (billing_toggle), mas billing tem um periodo so.")
        featured = p.get("featured_plan")
        if featured is not None and (not isinstance(featured, int) or not isinstance(count, int) or not 1 <= featured <= count):
            errors.append(f"{where}.featured_plan: plano em destaque (1 = primeiro) ou omitido.")
        if "featured_badge" in evidence and featured is None:
            errors.append(f"{where}: a referencia mostra selo de destaque - registre featured_plan.")
        comparison = p.get("comparison_table")
        if comparison and comparison not in table_ids:
            errors.append(f"{where}.comparison_table {comparison!r} nao existe em tables[].")


VALID_TESTIMONIAL_LAYOUTS = {"grid", "list", "single", "carousel"}
VALID_TESTIMONIAL_EVIDENCE = {"quote_marks", "quote_text", "author_name", "author_photo", "rating_stars",
                              "source_badge", "user"}
VALID_TESTIMONIAL_FIELDS = {"photo", "role", "company", "city", "rating", "source"}
VALID_CONTENT_SOURCE = {"user", "demo"}
VALID_LOGO_LAYOUTS = {"grid", "row", "marquee", "carousel"}
VALID_LOGO_EVIDENCE = {"logo_row", "grayscale_logos", "section_title", "marquee", "certification_badges", "user"}
VALID_LOGO_PERMISSION = {"confirmed", "demo"}
VALID_LOGO_FILES = {"provided", "pending"}


def check_testimonials(bp, errors, warnings):
    """Depoimento: real so com conteudo fornecido pelo usuario e autorizacao;
    o da referencia e mockup ate prova em contrario."""
    if "testimonials" not in bp:
        errors.append(
            "Secao 'testimonials' ausente - registre cada bloco de depoimentos da referencia, ou "
            "'testimonials: []' depois de conferir que nao ha nenhum (references/social-proof.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    carousel_ids = {c.get("id") for c in (bp.get("carousels") or []) if isinstance(c, dict)}
    seen = set()
    for i, t in enumerate(bp.get("testimonials") or []):
        tid = t.get("id") or f"<testimonials[{i}]>"
        where = f"testimonials[{tid}]"
        if tid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(tid)
        if t.get("section") not in sections:
            errors.append(f"{where}.section {t.get('section')!r} nao e id de pages[].sections.")
        elif t.get("section") not in editable:
            errors.append(f"{where}: a secao {t.get('section')!r} nao tem destino em editable_content.")
        if not t.get("storage"):
            errors.append(f"{where}.storage: onde os depoimentos sao editados (ex.: 'post_type:testimonial').")
        if t.get("layout") not in VALID_TESTIMONIAL_LAYOUTS:
            errors.append(f"{where}.layout invalido: {t.get('layout')!r} (validos: {sorted(VALID_TESTIMONIAL_LAYOUTS)}).")
        elif t.get("layout") == "carousel" and t.get("carousel") not in carousel_ids:
            errors.append(f"{where}: layout carousel exige 'carousel' com o id em carousels[] (kind testimonials).")
        evidence = t.get("evidence") or []
        if not evidence or any(e not in VALID_TESTIMONIAL_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica depoimento ({sorted(VALID_TESTIMONIAL_EVIDENCE)}).")
        if not isinstance(t.get("item_count"), int) or t.get("item_count") < 1:
            errors.append(f"{where}.item_count: quantos depoimentos a referencia mostra (inteiro >= 1).")
        shown = t.get("fields_shown") or []
        if any(f not in VALID_TESTIMONIAL_FIELDS for f in shown):
            errors.append(f"{where}.fields_shown: so {sorted(VALID_TESTIMONIAL_FIELDS)} (o que aparece em cada depoimento).")
        if "rating_stars" in evidence and "rating" not in shown:
            errors.append(f"{where}: a referencia mostra estrelas - inclua 'rating' em fields_shown.")
        source = t.get("content_source")
        if source not in VALID_CONTENT_SOURCE:
            errors.append(
                f"{where}.content_source {source!r}: user (depoimentos reais fornecidos pelo cliente) | demo. "
                "Os da referencia sao mockup - publica-los como reais e propaganda enganosa (CDC/CONAR)."
            )
        elif source == "user":
            if t.get("consent") is not True:
                errors.append(f"{where}.consent: true - autorizacao dos clientes para publicar nome/foto/fala (LGPD).")
        else:
            warnings.append(f"{where}: depoimentos DEMO - o tema os oculta em producao; peca os depoimentos reais.")
        if t.get("structured_data"):
            errors.append(
                f"{where}.structured_data: nao use Review/AggregateRating para depoimentos da propria empresa - "
                "o Google nao mostra estrelas para avaliacao autopromocional (2019)."
            )


def check_client_logos(bp, errors, warnings):
    """Logo de cliente: so com permissao confirmada e arquivo da propria
    empresa; o da referencia e marca de mockup ate prova em contrario."""
    if "client_logos" not in bp:
        errors.append(
            "Secao 'client_logos' ausente - registre cada faixa/grade de logos da referencia, ou "
            "'client_logos: []' depois de conferir que nao ha nenhuma (references/social-proof.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    carousel_ids = {c.get("id") for c in (bp.get("carousels") or []) if isinstance(c, dict)}
    seen = set()
    for i, c in enumerate(bp.get("client_logos") or []):
        cid = c.get("id") or f"<client_logos[{i}]>"
        where = f"client_logos[{cid}]"
        if cid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(cid)
        if c.get("section") not in sections:
            errors.append(f"{where}.section {c.get('section')!r} nao e id de pages[].sections.")
        elif c.get("section") not in editable:
            errors.append(f"{where}: a secao {c.get('section')!r} nao tem destino em editable_content.")
        if not c.get("storage"):
            errors.append(f"{where}.storage: onde os logos sao editados (ex.: 'repeater:home_clients').")
        if c.get("layout") not in VALID_LOGO_LAYOUTS:
            errors.append(f"{where}.layout invalido: {c.get('layout')!r} (validos: {sorted(VALID_LOGO_LAYOUTS)}).")
        elif c.get("layout") == "carousel" and c.get("carousel") not in carousel_ids:
            errors.append(f"{where}: layout carousel exige 'carousel' com o id em carousels[] (kind logos).")
        evidence = c.get("evidence") or []
        if not evidence or any(e not in VALID_LOGO_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica logos ({sorted(VALID_LOGO_EVIDENCE)}).")
        if "marquee" in evidence and c.get("layout") != "marquee":
            warnings.append(f"{where}: a referencia sugere faixa rolando (marquee) mas layout e {c.get('layout')!r} - confirme.")
        if not isinstance(c.get("logo_count"), int) or c.get("logo_count") < 1:
            errors.append(f"{where}.logo_count: quantos logos a referencia mostra (inteiro >= 1).")
        permission = c.get("permission")
        if permission not in VALID_LOGO_PERMISSION:
            errors.append(
                f"{where}.permission {permission!r}: confirmed (clientes reais que autorizaram o uso da marca) | demo. "
                "Logo de outra empresa sugere endosso; os da referencia costumam ser marcas de mockup."
            )
        elif permission == "confirmed":
            if c.get("files") not in VALID_LOGO_FILES:
                errors.append(f"{where}.files: provided (arquivos da propria empresa recebidos) | pending.")
            elif c.get("files") == "pending":
                warnings.append(f"{where}: arquivos dos logos pendentes - nunca redesenhe nem recorte da referencia para publicar.")
        else:
            warnings.append(f"{where}: logos DEMO - o tema os oculta em producao; confirme clientes e permissao.")


VALID_TEAM_LAYOUTS = {"grid", "list", "carousel"}
VALID_TEAM_EVIDENCE = {"headshots", "name_role", "social_icons", "section_title", "hover_bio", "user"}
VALID_TEAM_FIELDS = {"photo", "role", "bio", "social", "registration"}
VALID_REGISTRATIONS = {"none", "crm", "cro", "crp", "crn", "crefito", "coren", "oab", "crea", "cau", "crc", "creci", "other"}
VALID_BIO_MODES = {"visible", "collapsed", "hidden"}
VALID_STATS_EVIDENCE = {"big_number", "prefix_suffix", "label_below", "icon", "user"}


def check_team(bp, errors, warnings):
    """Equipe: pessoas reais so com nomes, fotos e autorizacao de imagem;
    registro profissional nunca inventado; bio nunca so no hover."""
    if "team" not in bp:
        errors.append(
            "Secao 'team' ausente - registre cada bloco de equipe da referencia, ou 'team: []' depois de "
            "conferir que nao ha nenhum (references/team-stats.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    carousel_ids = {c.get("id") for c in (bp.get("carousels") or []) if isinstance(c, dict)}
    blocking = _pending_blocking_subjects(bp)
    seen = set()
    for i, t in enumerate(bp.get("team") or []):
        tid = t.get("id") or f"<team[{i}]>"
        where = f"team[{tid}]"
        if tid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(tid)
        if t.get("section") not in sections:
            errors.append(f"{where}.section {t.get('section')!r} nao e id de pages[].sections.")
        elif t.get("section") not in editable:
            errors.append(f"{where}: a secao {t.get('section')!r} nao tem destino em editable_content.")
        if not t.get("storage"):
            errors.append(f"{where}.storage: onde a equipe e editada (ex.: 'post_type:team_member').")
        if t.get("layout") not in VALID_TEAM_LAYOUTS:
            errors.append(f"{where}.layout invalido: {t.get('layout')!r} (validos: {sorted(VALID_TEAM_LAYOUTS)}).")
        elif t.get("layout") == "carousel" and t.get("carousel") not in carousel_ids:
            errors.append(f"{where}: layout carousel exige 'carousel' com o id em carousels[].")
        evidence = t.get("evidence") or []
        if not evidence or any(e not in VALID_TEAM_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica equipe ({sorted(VALID_TEAM_EVIDENCE)}).")
        count = t.get("member_count")
        if not isinstance(count, int) or count < 1:
            errors.append(f"{where}.member_count: quantas pessoas a referencia mostra (inteiro >= 1).")
        total = t.get("total_count")
        if total is not None and (not isinstance(total, int) or (isinstance(count, int) and total < count)):
            errors.append(f"{where}.total_count deve ser inteiro >= member_count (ou omitido).")
        shown = t.get("fields_shown") or []
        if any(f not in VALID_TEAM_FIELDS for f in shown):
            errors.append(f"{where}.fields_shown: so {sorted(VALID_TEAM_FIELDS)}.")
        if "social_icons" in evidence and "social" not in shown:
            errors.append(f"{where}: a referencia mostra redes por pessoa - inclua 'social' em fields_shown.")
        registration = t.get("registration", "none")
        if registration not in VALID_REGISTRATIONS:
            errors.append(f"{where}.registration invalido: {registration!r} (validos: {sorted(VALID_REGISTRATIONS)}).")
        elif registration != "none" and "registration" not in shown:
            errors.append(f"{where}: registro profissional ({registration}) exigido pelo setor - inclua 'registration' em fields_shown.")
        bio = t.get("bio", "visible" if "bio" in shown else "hidden")
        if bio not in VALID_BIO_MODES:
            errors.append(f"{where}.bio invalido: {bio!r} (validos: {sorted(VALID_BIO_MODES)}).")
        if "hover_bio" in evidence and bio == "hidden":
            errors.append(f"{where}: a referencia revela bio no hover - use bio visible ou collapsed (hover nao funciona no teclado/toque).")
        if not isinstance(t.get("profile_pages"), bool):
            if tid in blocking:
                warnings.append(f"{where}.profile_pages pendente de resposta do usuario.")
            else:
                errors.append(f"{where}.profile_pages: cada pessoa tem pagina propria? true/false (ou uncertainty bloqueante).")
        source = t.get("content_source")
        if source not in VALID_CONTENT_SOURCE:
            errors.append(
                f"{where}.content_source {source!r}: user (equipe real) | demo. Pessoas da referencia costumam ser "
                "foto de banco de imagem com nome inventado."
            )
        elif source == "user":
            if t.get("consent") is not True:
                errors.append(f"{where}.consent: true - autorizacao de uso de imagem/nome de cada pessoa (LGPD).")
        else:
            warnings.append(f"{where}: equipe DEMO - o tema a oculta em producao; peca nomes, fotos e autorizacoes.")


def check_stats(bp, errors, warnings):
    """Numeros em destaque: afirmacao de negocio (comprovavel) - real so
    confirmado; animacao de contagem decidida, nunca presumida."""
    if "stats" not in bp:
        errors.append(
            "Secao 'stats' ausente - registre cada bloco de numeros em destaque da referencia, ou 'stats: []' "
            "depois de conferir que nao ha nenhum (references/team-stats.md)."
        )
        return
    sections = _section_ids(bp)
    editable = {e.get("target") for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    blocking = _pending_blocking_subjects(bp)
    seen = set()
    for i, s in enumerate(bp.get("stats") or []):
        sid = s.get("id") or f"<stats[{i}]>"
        where = f"stats[{sid}]"
        if sid in seen:
            errors.append(f"{where}: id repetido.")
        seen.add(sid)
        if s.get("section") not in sections:
            errors.append(f"{where}.section {s.get('section')!r} nao e id de pages[].sections.")
        elif s.get("section") not in editable:
            errors.append(f"{where}: a secao {s.get('section')!r} nao tem destino em editable_content.")
        if not s.get("storage"):
            errors.append(f"{where}.storage: onde os numeros sao editados (ex.: 'repeater:home_stats').")
        evidence = s.get("evidence") or []
        if not evidence or any(e not in VALID_STATS_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que na referencia indica numeros em destaque ({sorted(VALID_STATS_EVIDENCE)}).")
        if not isinstance(s.get("item_count"), int) or s.get("item_count") < 1:
            errors.append(f"{where}.item_count: quantos numeros a referencia mostra (inteiro >= 1).")
        _decided(s.get("count_up"), sid, blocking, where, "count_up", errors, warnings,
                 "a imagem nao mostra se o numero conta de 0 ate o valor.")
        source = s.get("content_source")
        if source not in VALID_CONTENT_SOURCE:
            errors.append(
                f"{where}.content_source {source!r}: user (valores confirmados e comprovaveis) | demo. "
                "'+500 obras', '100% satisfeitos' sao afirmacoes de negocio (CDC/CONAR)."
            )
        elif source == "demo":
            warnings.append(f"{where}: numeros DEMO - o tema os oculta em producao; confirme os valores reais.")


VALID_BLOG_EVIDENCE = {"post_cards", "dates", "categories", "read_more", "sidebar", "pagination", "section_title", "user"}
VALID_CARD_FIELDS = {"image", "date", "category", "author", "reading_time", "excerpt"}


def check_blog(bp, errors, warnings):
    """Blog/noticias: post nativo, pagina de posts, campos do card,
    comentarios decididos, posts da referencia como demo."""
    blog = bp.get("blog")
    if not isinstance(blog, dict):
        errors.append(
            "Secao 'blog' ausente - declare blog: {enabled: false} depois de conferir que a referencia nao tem "
            "blog/noticias, ou descreva o blog (references/blog.md)."
        )
        return
    if blog.get("enabled") is False:
        return
    if blog.get("enabled") is not True:
        errors.append("blog.enabled: true | false.")
        return
    where = "blog"
    if (blog.get("storage") or "post") != "post":
        errors.append(f"{where}.storage: blog usa o post nativo do WordPress (categorias, tags, feed, SEO) - nao um CPT.")
    evidence = blog.get("evidence") or []
    if not evidence or any(e not in VALID_BLOG_EVIDENCE for e in evidence):
        errors.append(f"{where}.evidence: o que na referencia indica blog ({sorted(VALID_BLOG_EVIDENCE)}).")
    if not blog.get("label"):
        errors.append(f"{where}.label: nome da secao na referencia ('Blog', 'Notícias', 'Artigos').")
    page_slugs = {str(p.get("slug") or "").strip("/") for p in (bp.get("pages") or []) if isinstance(p, dict)}
    posts_page = str(blog.get("posts_page") or "").strip("/")
    if not posts_page:
        errors.append(f"{where}.posts_page: slug da pagina de posts (Configuracoes > Leitura) - ex.: 'blog'.")
    elif posts_page not in page_slugs:
        errors.append(f"{where}.posts_page {posts_page!r} nao esta em pages[] (adicione a pagina do blog).")
    ppp = blog.get("posts_per_page")
    if not isinstance(ppp, int) or ppp < 1:
        errors.append(f"{where}.posts_per_page: quantos posts por pagina (inteiro; o da referencia ou um multiplo das colunas).")
    fields = blog.get("card_fields") or []
    if not fields or any(f not in VALID_CARD_FIELDS for f in fields):
        errors.append(f"{where}.card_fields: o que cada card mostra ({sorted(VALID_CARD_FIELDS)}).")
    if "dates" in evidence and "date" not in fields:
        errors.append(f"{where}: a referencia mostra data nos cards - inclua 'date' em card_fields.")
    if "categories" in evidence and "category" not in fields:
        errors.append(f"{where}: a referencia mostra categoria nos cards - inclua 'category' em card_fields.")
    home = blog.get("home_section")
    if home is not None:
        if not isinstance(home, dict) or home.get("section") not in _section_ids(bp):
            errors.append(f"{where}.home_section.section: id de pages[].sections onde aparecem os ultimos posts.")
        elif not isinstance(home.get("count"), int) or home.get("count") < 1:
            errors.append(f"{where}.home_section.count: quantos posts a referencia mostra na secao (inteiro).")
    if not isinstance(blog.get("sidebar"), bool):
        errors.append(f"{where}.sidebar: true | false (a referencia mostra barra lateral?).")
    if not isinstance(blog.get("comments"), bool):
        errors.append(
            f"{where}.comments: true | false - decisao do usuario (exige moderacao, anti-spam e aviso de "
            "privacidade); nunca ligado por padrao."
        )
    source = blog.get("content_source")
    if source not in VALID_CONTENT_SOURCE:
        errors.append(
            f"{where}.content_source {source!r}: user (posts reais) | demo - posts da referencia sao titulos "
            "inventados; os demo levam a meta _project_demo e somem em producao."
        )
    elif source == "demo":
        warnings.append(f"{where}: posts DEMO (meta _project_demo) - ocultos em producao; o cliente publica os reais.")


VALID_FOOTER_EVIDENCE = {"columns", "footer_menu", "contact_block", "social_icons", "newsletter", "legal_row",
                         "back_to_top", "payment_seals", "map", "credit", "user"}
VALID_FOOTER_KINDS = {"about", "menu", "contact", "social", "newsletter", "hours", "custom"}
VALID_SOCIAL_NETWORKS = {"instagram", "facebook", "linkedin", "youtube", "tiktok", "x", "pinterest", "threads",
                         "whatsapp", "telegram", "spotify"}
VALID_SOCIAL_LOCATIONS = {"header", "footer", "contact"}


def check_footer(bp, errors, warnings):
    """Rodape: colunas da referencia (tipo + titulo literal), politica de
    privacidade (LGPD), CNPJ nunca inventado."""
    footer = bp.get("footer")
    if not isinstance(footer, dict):
        errors.append("Secao 'footer' ausente - descreva as colunas e a faixa inferior do rodape (references/footer-social.md).")
        return
    evidence = footer.get("evidence") or []
    if not evidence or any(e not in VALID_FOOTER_EVIDENCE for e in evidence):
        errors.append(f"footer.evidence: o que o rodape da referencia mostra ({sorted(VALID_FOOTER_EVIDENCE)}).")
    columns = footer.get("columns") or []
    if not columns:
        errors.append("footer.columns: as colunas do rodape na ordem da referencia (id, kind, title).")
    ids = set()
    kinds = []
    for col in columns:
        if not isinstance(col, dict):
            errors.append(f"footer.columns: item {col!r} deve ser objeto (id, kind, title).")
            continue
        cid = str(col.get("id") or "")
        if not re.match(r"^[a-z][a-z0-9_]*$", cid):
            errors.append(f"footer.columns[{cid or '?'}].id: minusculo, sem acento (vira local de menu footer_<id>).")
        if cid in ids:
            errors.append(f"footer.columns[{cid}]: id repetido.")
        ids.add(cid)
        kind = col.get("kind")
        kinds.append(kind)
        if kind not in VALID_FOOTER_KINDS:
            errors.append(f"footer.columns[{cid}].kind invalido: {kind!r} (validos: {sorted(VALID_FOOTER_KINDS)}).")
        if kind == "menu" and not col.get("title"):
            errors.append(f"footer.columns[{cid}]: coluna de menu precisa de title (literal da referencia; nomeia a navegacao).")
    if "social_icons" in evidence and "social" not in kinds and not any(
            isinstance(c, dict) and c.get("social") is True for c in columns):
        errors.append("footer: a referencia mostra icones de redes no rodape - inclua uma coluna kind social ou social: true na coluna onde eles ficam.")
    if "newsletter" in evidence or "newsletter" in kinds:
        if not any(isinstance(f, dict) and f.get("purpose") == "newsletter" for f in (bp.get("forms") or [])):
            errors.append("footer: newsletter no rodape exige um forms[] com purpose newsletter.")
    legal = footer.get("legal") or {}
    if legal.get("privacy_link") is not True:
        errors.append("footer.legal.privacy_link: true - link da politica de privacidade no rodape (LGPD).")
    elif legal.get("privacy_in_reference") is False:
        warnings.append("footer: link de privacidade nao aparece na referencia - registre como desvio intencional aprovado.")
    if legal.get("cnpj") not in {"shown", "hidden"}:
        errors.append("footer.legal.cnpj: shown | hidden (a referencia mostra CNPJ/razao social?).")
    elif legal.get("cnpj") == "shown":
        company = (bp.get("global_settings") or {}).get("company") or {}
        if not company.get("cnpj") and "cnpj" not in _pending_blocking_subjects(bp):
            errors.append(
                "footer.legal.cnpj shown: informe global_settings.company.cnpj (e razao social) ou registre uncertainty "
                "bloqueante com subject 'cnpj' - nunca invente."
            )
    for flag in ("back_to_top", "credit"):
        if not isinstance(footer.get(flag), bool):
            errors.append(f"footer.{flag}: true | false (a referencia mostra?).")


def check_social(bp, errors, warnings):
    """Redes: quais, em que ordem e onde; URLs so do usuario (nunca inventadas)."""
    social = bp.get("social")
    if not isinstance(social, dict):
        errors.append("Secao 'social' ausente - declare as redes da referencia (networks: [] se nao houver).")
        return
    networks = social.get("networks")
    if not isinstance(networks, list) or any(n not in VALID_SOCIAL_NETWORKS for n in networks):
        errors.append(f"social.networks: lista na ordem da referencia ({sorted(VALID_SOCIAL_NETWORKS)}).")
        return
    if not networks:
        return
    locations = social.get("locations") or []
    if not locations or any(loc not in VALID_SOCIAL_LOCATIONS for loc in locations):
        errors.append(f"social.locations: onde os icones aparecem ({sorted(VALID_SOCIAL_LOCATIONS)}).")
    source = social.get("urls_source")
    if source not in {"user", "pending"}:
        errors.append("social.urls_source: user (URLs informadas) | pending (campos vazios no admin) - perfil nunca e inventado.")
    elif source == "user":
        urls = (bp.get("global_settings") or {}).get("social") or {}
        missing = [n for n in networks if n != "whatsapp" and not str(urls.get(n) or "").startswith(("http://", "https://"))]
        if missing:
            errors.append(f"social: urls_source user, mas sem URL em global_settings.social para {missing}.")
    else:
        warnings.append("social: URLs pendentes - os icones so aparecem depois de preenchidas no admin.")


VALID_HEADER_EVIDENCE = {"logo", "nav", "cta_button", "top_bar", "search_icon", "account_icon", "cart_icon",
                         "language", "dropdown_indicator", "transparent_over_hero", "user"}
VALID_HEADER_LAYOUTS = {"logo_left", "logo_center", "logo_center_split"}
VALID_TOPBAR_ITEMS = {"phone", "whatsapp", "email", "hours", "social", "text"}
VALID_HEADER_ACTIONS = {"search", "account", "cart", "language"}
VALID_SUBMENUS = {"none", "dropdown", "mega"}
VALID_MOBILE_MENU = {"dropdown", "offcanvas", "fullscreen"}


def check_header(bp, errors, warnings):
    """Header: layout do logo, botao de destaque, barra superior, acoes,
    transparencia sobre o hero, submenus e menu mobile - tudo decidido."""
    header = bp.get("header")
    if not isinstance(header, dict):
        errors.append("Secao 'header' ausente - descreva logo, menu, botao, barra superior e acoes (references/header-menu.md).")
        return
    evidence = header.get("evidence") or []
    if not evidence or any(e not in VALID_HEADER_EVIDENCE for e in evidence):
        errors.append(f"header.evidence: o que o header da referencia mostra ({sorted(VALID_HEADER_EVIDENCE)}).")
    if header.get("layout") not in VALID_HEADER_LAYOUTS:
        errors.append(f"header.layout: posicao do logo ({sorted(VALID_HEADER_LAYOUTS)}).")
    cta = header.get("cta")
    if "cta_button" in evidence:
        if not isinstance(cta, dict) or not cta.get("label") or not cta.get("target") or str(cta.get("target")).strip() == "#":
            errors.append("header.cta: a referencia mostra botao de destaque - informe label (literal) e target (destino real).")
    elif cta:
        warnings.append("header.cta declarado sem cta_button em evidence - confirme que a referencia mostra o botao.")
    top_bar = header.get("top_bar") or []
    if "top_bar" in evidence and not top_bar:
        errors.append(f"header.top_bar: itens da barra superior na ordem ({sorted(VALID_TOPBAR_ITEMS)}).")
    if any(i not in VALID_TOPBAR_ITEMS for i in top_bar):
        errors.append(f"header.top_bar: itens validos {sorted(VALID_TOPBAR_ITEMS)}.")
    if "social" in top_bar and "header" not in ((bp.get("social") or {}).get("locations") or []):
        errors.append("header.top_bar tem 'social' - inclua header em social.locations.")
    actions = header.get("actions") or []
    if any(a not in VALID_HEADER_ACTIONS for a in actions):
        errors.append(f"header.actions: validos {sorted(VALID_HEADER_ACTIONS)}.")
    for ev, act in (("search_icon", "search"), ("account_icon", "account"), ("cart_icon", "cart"), ("language", "language")):
        if ev in evidence and act not in actions:
            errors.append(f"header: a referencia mostra {ev} - inclua '{act}' em header.actions (ou registre por que nao).")
    if "cart" in actions and (bp.get("project") or {}).get("type") != "ecommerce":
        warnings.append("header.actions: carrinho sem project.type ecommerce - exige WooCommerce (decisao arquitetural).")
    if "language" in actions:
        warnings.append("header.actions: seletor de idioma exige plugin multilingue e conteudo traduzido (decisao arquitetural).")
    transparent = header.get("transparent")
    if not isinstance(transparent, bool):
        errors.append("header.transparent: true | false (o header fica sobre a foto do hero na referencia?).")
    elif transparent:
        if not (bp.get("theme") or {}).get("header_scrolled"):
            errors.append(
                "header.transparent: defina theme.header_scrolled (fundo/cor ao rolar) - a referencia so mostra o estado sobre o hero."
            )
        if not header.get("logo_light"):
            warnings.append("header.transparent: sem logo_light - confirme que o logo atual e legivel sobre o hero.")
    submenus = header.get("submenus")
    if submenus not in VALID_SUBMENUS:
        errors.append(f"header.submenus: {sorted(VALID_SUBMENUS)} (a referencia mostra setinha/indicador de submenu?).")
    has_children = any(item.get("children") for m in (bp.get("menus") or []) if isinstance(m, dict)
                       for item in iter_menu_items(m.get("items")))
    if has_children and submenus == "none":
        errors.append("header.submenus none, mas menus[] tem itens com children - use dropdown (ou mega).")
    if "dropdown_indicator" in evidence and submenus == "none":
        errors.append("header: a referencia mostra indicador de submenu - submenus dropdown ou mega.")
    if submenus == "mega":
        warnings.append("header.submenus mega: o esqueleto implementa dropdown; mega menu exige layout proprio (decisao registrada).")
    if header.get("mobile_menu") not in VALID_MOBILE_MENU:
        errors.append(
            f"header.mobile_menu: {sorted(VALID_MOBILE_MENU)} - da referencia mobile ou decisao registrada "
            "(a imagem desktop nao mostra)."
        )


VALID_HERO_KINDS = {"background", "split", "centered", "form", "page_header", "carousel", "video"}
VALID_HERO_EVIDENCE = {"full_bleed_image", "text_over_image", "split_layout", "headline", "buttons", "form",
                       "breadcrumb", "page_title_band", "user"}
VALID_HERO_HEIGHTS = {"full", "large", "auto"}
VALID_MOBILE_IMAGE = {"same", "focal", "separate"}
VALID_IMAGE_ROLES = {"decorative", "informative"}
VALID_BANNER_KINDS = {"cta_band", "announcement"}


def check_heroes(bp, errors, warnings):
    """Hero/cabecalho de pagina: tipo, um h1 por pagina, botoes reais, e -
    com foto - camada de contraste, enquadramento no celular e alt decididos."""
    if "heroes" not in bp:
        errors.append("Secao 'heroes' ausente - registre o hero da Home e os cabecalhos das paginas internas (references/hero-banners.md).")
        return
    page_of = {s.get("id"): p.get("id") for p in (bp.get("pages") or []) for s in (p.get("sections") or []) if s.get("id")}
    carousel_ids = {c.get("id") for c in (bp.get("carousels") or []) if isinstance(c, dict)}
    video_ids = {v.get("id") for v in (bp.get("videos") or []) if isinstance(v, dict)}
    h1_pages = {}
    for i, h in enumerate(bp.get("heroes") or []):
        hid = h.get("id") or f"<heroes[{i}]>"
        where = f"heroes[{hid}]"
        section = h.get("section")
        if section not in page_of:
            errors.append(f"{where}.section {section!r} nao e id de pages[].sections.")
        kind = h.get("kind")
        if kind not in VALID_HERO_KINDS:
            errors.append(f"{where}.kind invalido: {kind!r} (validos: {sorted(VALID_HERO_KINDS)}).")
        evidence = h.get("evidence") or []
        if not evidence or any(e not in VALID_HERO_EVIDENCE for e in evidence):
            errors.append(f"{where}.evidence: o que a referencia mostra ({sorted(VALID_HERO_EVIDENCE)}).")
        if kind == "carousel" and h.get("carousel") not in carousel_ids:
            errors.append(f"{where}: kind carousel exige 'carousel' com o id em carousels[] (kind hero_banner).")
        if kind == "video" and h.get("video") not in video_ids:
            errors.append(f"{where}: kind video exige 'video' com o id em videos[] (kind background).")
        if h.get("h1", True):
            page = page_of.get(section)
            if page in h1_pages:
                errors.append(f"{where}: a pagina {page!r} ja tem h1 em heroes[{h1_pages[page]}] - um h1 por pagina.")
            h1_pages[page] = hid
        if kind in {"background", "split", "page_header"} and h.get("has_image", kind != "page_header"):
            if not isinstance(h.get("overlay"), (int, float)) or not 0 <= float(h.get("overlay")) <= 1:
                if kind != "split":
                    errors.append(f"{where}.overlay: 0..1 - camada de contraste sobre a foto (0 = sem; o QA mede o contraste real).")
            if h.get("mobile_image") not in VALID_MOBILE_IMAGE:
                errors.append(f"{where}.mobile_image: same | focal (ponto focal editavel) | separate (imagem propria do celular).")
            if h.get("image_role") not in VALID_IMAGE_ROLES:
                errors.append(f"{where}.image_role: decorative (alt vazio) | informative (alt descreve a foto).")
        if kind in {"background", "split", "centered", "form"} and h.get("height") not in VALID_HERO_HEIGHTS:
            errors.append(f"{where}.height: full | large | auto (altura na referencia; vira svh, nunca 100vh).")
        for j, b in enumerate(h.get("buttons") or []):
            if not isinstance(b, dict) or not b.get("label") or not b.get("target") or str(b.get("target")).strip() == "#":
                errors.append(f"{where}.buttons[{j}]: label literal e target real (nunca '#').")
        if "buttons" in evidence and not h.get("buttons"):
            errors.append(f"{where}: a referencia mostra botoes - liste em buttons (label, target, style).")
        if kind == "page_header" and not isinstance(h.get("breadcrumb"), bool):
            errors.append(f"{where}.breadcrumb: true | false (a referencia mostra a trilha 'Início › Página'?).")
        if kind == "form" and not any(isinstance(f, dict) and f.get("section") == section for f in (bp.get("forms") or [])):
            errors.append(f"{where}: hero com formulario exige forms[] com section {section!r}.")


def check_banners(bp, errors, warnings):
    """Faixa de chamada reutilizavel e barra de aviso fechavel."""
    if "banners" not in bp:
        errors.append("Secao 'banners' ausente - registre faixas de chamada e barra de aviso, ou 'banners: []'.")
        return
    sections = _section_ids(bp)
    editable = {e.get("target"): e for e in (bp.get("editable_content") or []) if isinstance(e, dict)}
    for i, b in enumerate(bp.get("banners") or []):
        bid = b.get("id") or f"<banners[{i}]>"
        where = f"banners[{bid}]"
        kind = b.get("kind")
        if kind not in VALID_BANNER_KINDS:
            errors.append(f"{where}.kind invalido: {kind!r} (validos: {sorted(VALID_BANNER_KINDS)}).")
            continue
        if kind == "cta_band":
            if b.get("section") not in sections:
                errors.append(f"{where}.section {b.get('section')!r} nao e id de pages[].sections.")
            if not isinstance(b.get("reusable"), bool):
                errors.append(f"{where}.reusable: true (conteudo na pagina de opcoes, repete em varias paginas) | false.")
            elif b.get("reusable") and (editable.get(b.get("section")) or {}).get("storage") != "options_page":
                errors.append(f"{where}: faixa reutilizavel deve ser editada na pagina de opcoes (editable_content storage options_page).")
            for j, btn in enumerate(b.get("buttons") or []):
                if not isinstance(btn, dict) or not btn.get("label") or not btn.get("target") or str(btn.get("target")).strip() == "#":
                    errors.append(f"{where}.buttons[{j}]: label literal e target real (nunca '#').")
        else:
            if not isinstance(b.get("dismissible"), bool):
                errors.append(f"{where}.dismissible: true | false (a referencia mostra um 'x' para fechar?).")
            if not b.get("text_field"):
                errors.append(f"{where}.text_field: campo do admin com o texto do aviso (ex.: announcement_text).")


VALID_SEO_PLUGINS = {"none", "yoast", "rank_math", "seopress", "aioseo"}
VALID_DESCRIPTION_SOURCES = {"proposed", "client", "reference"}
VALID_SECURITY_EXCEPTIONS = {"xmlrpc", "author_archives", "rest_users", "frame_embedding"}


def check_seo(bp, errors, warnings):
    """Descricao aprovada por pagina, tipo schema.org da empresa e plugin
    de SEO (references/security-seo.md)."""
    seo = bp.get("seo")
    if not isinstance(seo, dict):
        errors.append("Secao 'seo' ausente - declare plugin, organization_type e a descricao de cada pagina (seo.pages).")
        return
    if seo.get("plugin") not in VALID_SEO_PLUGINS:
        errors.append(f"seo.plugin invalido: {seo.get('plugin')!r} (validos: {sorted(VALID_SEO_PLUGINS)}; 'none' = SEO do tema).")
    org_type = seo.get("organization_type")
    if not isinstance(org_type, str) or not re.fullmatch(r"[A-Z][A-Za-z]+", org_type):
        errors.append("seo.organization_type: tipo schema.org - Organization (sem atendimento no local), "
                      "LocalBusiness ou subtipo (GeneralContractor, BeautySalon, Dentist...).")
    elif org_type != "Organization":
        company = (bp.get("global_settings") or {}).get("company") or {}
        if not any(str(company.get(k) or "").strip() for k in ("address", "address_line1")):
            errors.append(f"seo.organization_type {org_type} exige endereco fisico em global_settings.company.address "
                          "- sem endereco, use Organization.")
    pages = {p.get("id"): p for p in bp.get("pages") or [] if isinstance(p, dict) and p.get("id")}
    entries = {}
    for i, s in enumerate(seo.get("pages") or []):
        where = f"seo.pages[{i}]"
        if not isinstance(s, dict) or s.get("page") not in pages:
            errors.append(f"{where}.page deve ser um id de pages[] (recebido {s.get('page') if isinstance(s, dict) else s!r}).")
            continue
        entries[s["page"]] = s
        if s.get("noindex") is True:
            continue
        desc = str(s.get("description") or "").strip()
        if not 50 <= len(desc) <= 160:
            errors.append(f"{where} ({s['page']}): description com {len(desc)} caracteres - escreva 50 a 160 "
                          "(ideal 120-160), com o servico e a cidade quando houver.")
        if s.get("description_source") not in VALID_DESCRIPTION_SOURCES:
            errors.append(f"{where}.description_source: proposed (texto sugerido, entra em pending_decisions) | client | reference.")
        if s.get("title") and len(str(s["title"])) > 60:
            warnings.append(f"{where}.title com {len(str(s['title']))} caracteres - o Google corta perto de 60.")
    for pid, page in pages.items():
        slug = str(page.get("slug") or "")
        if pid not in entries and "<" not in slug and "{" not in slug:
            errors.append(f"seo.pages sem a pagina '{pid}' - toda pagina indexavel precisa de descricao aprovada (ou noindex: true).")
    seen = {}
    for pid, s in entries.items():
        desc = str(s.get("description") or "").strip().lower()
        if desc and not s.get("noindex"):
            if desc in seen:
                errors.append(f"seo.pages: '{pid}' repete a descricao de '{seen[desc]}' - cada pagina precisa da propria.")
            seen.setdefault(desc, pid)


VALID_FONT_DELIVERY = {"self_hosted", "system", "google_cdn"}
VALID_FONT_ROLES = {"heading", "body", "accent", "other"}
VALID_FONT_SOURCES = {"google_fonts", "provided"}
VALID_FONT_LICENSES = {"OFL", "Apache-2.0", "commercial"}
SYSTEM_FONT_NAMES = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-sans-serif", "ui-serif",
    "ui-monospace", "-apple-system", "blinkmacsystemfont", "segoe ui", "roboto", "helvetica", "helvetica neue",
    "arial", "georgia", "times new roman", "times", "verdana", "tahoma", "trebuchet ms", "courier new",
    "apple color emoji", "segoe ui emoji", "noto sans",
}


def _font_names(value):
    return [n.strip().strip("'\"") for n in str(value or "").split(",") if n.strip()]


def check_fonts(bp, errors, warnings):
    """Fontes hospedadas no proprio site, so os pesos usados, no maximo 2
    pre-carregadas, licenca conhecida (references/fonts.md)."""
    fonts = bp.get("fonts")
    if not isinstance(fonts, dict):
        errors.append("Secao 'fonts' ausente - declare delivery e as familias (pesos usados, preload, licenca).")
        return
    delivery = fonts.get("delivery")
    if delivery not in VALID_FONT_DELIVERY:
        errors.append(f"fonts.delivery invalido: {delivery!r} (self_hosted | system | google_cdn).")
        return
    if delivery == "google_cdn" and not str(fonts.get("reason") or "").strip():
        errors.append("fonts.delivery google_cdn exige 'reason': o navegador do visitante conecta no Google "
                      "(IP enviado a terceiro - LGPD). Padrao: self_hosted.")
    if delivery == "self_hosted" and not isinstance(fonts.get("fallback_metrics"), bool):
        errors.append("fonts.fallback_metrics: true (reserva ajustada, sem salto na troca de fonte) | false.")
    families = {}
    preload_count = 0
    for i, f in enumerate(fonts.get("families") or []):
        where = f"fonts.families[{i}]"
        if not isinstance(f, dict) or not str(f.get("family") or "").strip():
            errors.append(f"{where}.family: nome da familia (ex.: Manrope).")
            continue
        name = f["family"].strip()
        families[name.lower()] = f
        where = f"fonts.families[{name}]"
        if f.get("role") not in VALID_FONT_ROLES:
            errors.append(f"{where}.role: heading | body | accent | other.")
        weights = f.get("weights") or []
        if not weights or not all(isinstance(w, int) and 100 <= w <= 900 and w % 100 == 0 for w in weights):
            errors.append(f"{where}.weights: pesos usados no layout, de 100 a 900 (ex.: [400, 700]) - cada peso e um arquivo.")
            weights = []
        elif len(weights) > 4:
            warnings.append(f"{where}: {len(weights)} pesos - cada um e um download; confirme que todos aparecem na referencia.")
        if not set(f.get("styles") or ["normal"]) <= {"normal", "italic"}:
            errors.append(f"{where}.styles: normal | italic.")
        source = f.get("source", "google_fonts")
        if source not in VALID_FONT_SOURCES:
            errors.append(f"{where}.source: google_fonts | provided (arquivo do cliente).")
        lic = f.get("license")
        if lic not in VALID_FONT_LICENSES:
            errors.append(f"{where}.license: OFL | Apache-2.0 (Google Fonts) | commercial.")
        elif lic == "commercial" and not str(f.get("license_note") or "").strip():
            errors.append(f"{where}: fonte comercial exige license_note (quem comprou, para qual dominio) - "
                          "hospedar sem licenca de web e infracao.")
        if lic == "commercial" and source == "google_fonts":
            errors.append(f"{where}: Google Fonts e OFL/Apache - source google_fonts nao combina com license commercial.")
        preload = f.get("preload") or []
        if not set(preload) <= set(weights):
            errors.append(f"{where}.preload {preload} fora de weights {weights}.")
        preload_count += len(preload)
    if preload_count > 2:
        errors.append(f"fonts: {preload_count} arquivos para pre-carregar - no maximo 2 (os do titulo/hero, acima da dobra); "
                      "mais que isso disputa banda com a imagem do hero (LCP).")
    if delivery == "self_hosted" and families and preload_count == 0:
        warnings.append("fonts: nenhum peso em preload - pre-carregue o do titulo do hero (aparece primeiro).")
    tokens = (((bp.get("design") or {}).get("tokens") or {}).get("font_family") or {})
    for token, raw in tokens.items():
        value = raw.get("value") if isinstance(raw, dict) else raw
        names = _font_names(value)
        if not names:
            continue
        first = names[0].lower()
        if names[-1].lower() not in {"serif", "sans-serif", "monospace", "system-ui", "cursive"}:
            errors.append(f"design.tokens.font_family.{token}: termine com a familia generica (sans-serif/serif).")
        if first not in SYSTEM_FONT_NAMES and first not in families:
            errors.append(f"design.tokens.font_family.{token} usa '{names[0]}', que nao esta em fonts.families "
                          "- o navegador mostraria a reserva no lugar da fonte da referencia.")
        if delivery == "system" and first not in SYSTEM_FONT_NAMES:
            errors.append(f"fonts.delivery system, mas design.tokens.font_family.{token} pede '{names[0]}' (fonte web).")
    for name, f in families.items():
        if not any(_font_names(r.get("value") if isinstance(r, dict) else r)[:1] == [f["family"].strip()] for r in tokens.values()):
            warnings.append(f"fonts.families[{f['family']}] nao e a primeira de nenhum design.tokens.font_family - download sem uso?")


VALID_AI_CRAWLERS = {"allow", "block_training", "block_all"}


def check_ai_crawlers(bp, errors, warnings):
    """Politica de robos de IA no robots.txt: decisao de negocio, perguntada
    ao usuario (references/security-seo.md secao 4)."""
    seo = bp.get("seo") if isinstance(bp.get("seo"), dict) else {}
    policy = seo.get("ai_crawlers")
    if policy not in VALID_AI_CRAWLERS:
        errors.append("seo.ai_crawlers: allow (treino e busca de IA liberados) | block_training (bloqueia treino, "
                      "mantem o site nas respostas do ChatGPT/Perplexity/Claude) | block_all - decisao do usuario.")
    elif seo.get("ai_crawlers_source") not in {"user", "default"}:
        errors.append("seo.ai_crawlers_source: user (o usuario escolheu) | default (aplicado o padrao 'allow' e "
                      "registrado em uncertainties para confirmar).")
    elif seo.get("ai_crawlers_source") == "default":
        warnings.append(f"seo.ai_crawlers '{policy}' e o padrao, nao uma escolha do usuario - confirme na aprovacao.")


def check_launch(bp, errors, warnings):
    """Publicacao, icone do site e redirecionamentos do site antigo
    (references/go-live.md, site-icon.md, redirects.md)."""
    launch = bp.get("launch")
    if not isinstance(launch, dict):
        errors.append("Secao 'launch' ausente - declare 'launch: { domain: null }' (ou o dominio final, https://...).")
    else:
        domain = launch.get("domain")
        if domain is not None and not re.fullmatch(r"https?://[a-z0-9.-]+\.[a-z]{2,}", str(domain), re.I):
            errors.append(f"launch.domain invalido: {domain!r} (ex.: https://www.empresa.com.br, sem caminho).")
        elif domain and not str(domain).startswith("https://"):
            warnings.append(f"launch.domain {domain} sem https.")
    branding = ((bp.get("global_settings") or {}).get("branding") or {})
    icon = branding.get("site_icon")
    media_ids = {m.get("id") for m in bp.get("media") or [] if isinstance(m, dict)}
    if not icon:
        errors.append("global_settings.branding.site_icon: media[].id do simbolo do logo (vira o Icone do site) ou 'pending'.")
    elif icon == "pending":
        warnings.append("global_settings.branding.site_icon pendente - peca o simbolo do logo em alta (PNG/SVG).")
    elif icon not in media_ids:
        errors.append(f"global_settings.branding.site_icon '{icon}' nao e um media[].id.")
    red = bp.get("redirects")
    if not isinstance(red, dict):
        errors.append("Secao 'redirects' ausente - declare 'redirects: { old_site: null, map: [] }' "
                      "(ou o endereco do site antigo, se o cliente ja tem site).")
        return
    old = red.get("old_site")
    if old is not None and not re.fullmatch(r"https?://\S+", str(old)):
        errors.append(f"redirects.old_site invalido: {old!r}.")
    pages = {p.get("id"): "/" + str(p.get("slug") or "").strip("/") for p in bp.get("pages") or [] if isinstance(p, dict)}
    seen = set()
    for i, row in enumerate(red.get("map") or []):
        where = f"redirects.map[{i}]"
        src = str((row or {}).get("from") or "") if isinstance(row, dict) else ""
        to = row.get("to") if isinstance(row, dict) else None
        if not src.startswith("/"):
            errors.append(f"{where}.from: caminho do site antigo comecando com '/' (ex.: /quem-somos.html).")
            continue
        norm = "/" + re.sub(r"\.(html?|php|aspx?)$", "", src.lower()).strip("/")
        if norm in seen:
            errors.append(f"{where}: '{src}' repetido.")
        seen.add(norm)
        # So o caminho IDENTICO a uma pagina nova nunca dispara (o mu-plugin so
        # age em 404); /servicos.php ou /servicos.html dao 404 e redirecionam.
        if "/" + src.lower().strip("/") in {v.rstrip("/") or "/" for v in pages.values()}:
            errors.append(f"{where}: '{src}' e o endereco de uma pagina nova - o redirecionamento nunca dispara.")
        if not (to in pages or str(to or "").startswith(("/", "http"))):
            errors.append(f"{where}.to: id de pages[], caminho '/...' ou URL (recebido {to!r}).")
    if old and not red.get("map"):
        warnings.append("redirects.old_site informado, mas redirects.map vazio - rode build_redirects.py --suggest "
                        "e confirme os destinos com o usuario (sem isso os links antigos viram 404).")


def check_security(bp, errors, warnings):
    """Protecao basica sempre ligada; excecao so com motivo
    (references/security-seo.md)."""
    sec = bp.get("security")
    if not isinstance(sec, dict):
        errors.append("Secao 'security' ausente - declare 'security: {hardening: standard, exceptions: []}'.")
        return
    if sec.get("hardening") != "standard":
        errors.append("security.hardening deve ser 'standard' (mu-plugin project-hardening + .htaccess do scaffold).")
    rules = []
    for i, e in enumerate(sec.get("exceptions") or []):
        if not isinstance(e, dict) or e.get("rule") not in VALID_SECURITY_EXCEPTIONS:
            errors.append(f"security.exceptions[{i}].rule invalida (validas: {sorted(VALID_SECURITY_EXCEPTIONS)}).")
            continue
        if not str(e.get("reason") or "").strip():
            errors.append(f"security.exceptions[{i}] ({e['rule']}): motivo obrigatorio (ex.: 'app Jetpack exige XML-RPC').")
        rules.append(e["rule"])
    if len(rules) != len(set(rules)):
        warnings.append("security.exceptions com regra repetida.")


def check_reference_map(bp, errors, warnings):
    """Toda regiao da referencia mapeada a uma secao, e toda secao mapeada."""
    ref_map = bp.get("reference_map")
    if not ref_map:
        errors.append(
            "Secao 'reference_map' ausente - sem o mapa de todas as regioes da "
            "referencia nao ha garantia de que nenhuma secao foi esquecida "
            "(ex.: continuacao da pagina em outra coluna da colagem)."
        )
        return
    pages = {p.get("id"): p for p in (bp.get("pages") or [])}
    mapped = set()
    for i, entry in enumerate(ref_map):
        label = f"reference_map[{i}]"
        page, section = entry.get("page"), entry.get("section")
        box = entry.get("box")
        if not entry.get("file"):
            errors.append(f"{label} sem 'file'.")
        if not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) for v in box)):
            errors.append(f"{label}.box deve ser [x, y, largura, altura] em pixels.")
        if section in {"header", "footer"}:
            continue
        if page not in pages:
            errors.append(f"{label}.page '{page}' nao existe em pages.")
            continue
        sections = {s.get("id") for s in (pages[page].get("sections") or [])}
        if section not in sections:
            errors.append(f"{label}.section '{section}' nao existe em pages[{page}].sections.")
        mapped.add((page, section))
    for pid, page in pages.items():
        for s in page.get("sections") or []:
            if (pid, s.get("id")) not in mapped and s.get("source") != "inference":
                errors.append(
                    f"pages[{pid}].sections[{s.get('id')}] nao tem regiao no reference_map - "
                    "mapeie a regiao da referencia ou marque source: inference."
                )


def check_copy_inventory(bp, errors, warnings):
    """Inventario de textos visiveis da referencia (bp.copy)."""
    copy = bp.get("copy")
    if not copy:
        warnings.append(
            "Secao 'copy' (inventario de textos visiveis da referencia) ausente "
            "ou vazia - sem ela nao ha como garantir que menus, titulos e CTAs "
            "foram reproduzidos literalmente nem separar texto real de demo."
        )
        return

    pages = {p.get("id"): {s.get("id") for s in (p.get("sections") or [])}
             for p in (bp.get("pages") or [])}
    seen = set()
    for entry in copy:
        eid = entry.get("id", "<sem id>")
        if eid in seen:
            errors.append(f"copy[{eid}]: id duplicado.")
        seen.add(eid)
        if not str(entry.get("text") or "").strip():
            errors.append(f"copy[{eid}] sem 'text'.")
        if entry.get("role") not in VALID_COPY_ROLES:
            errors.append(f"copy[{eid}].role invalido: {entry.get('role')!r} (validos: {sorted(VALID_COPY_ROLES)}).")
        if entry.get("source") not in VALID_COPY_SOURCES:
            errors.append(f"copy[{eid}].source invalido: {entry.get('source')!r} (validos: {sorted(VALID_COPY_SOURCES)}).")
        legibility = entry.get("legibility", "clear")
        if legibility not in VALID_LEGIBILITY:
            errors.append(f"copy[{eid}].legibility invalido: {legibility!r}.")
        if legibility == "illegible" and entry.get("source") == "reference_file":
            errors.append(
                f"copy[{eid}]: texto ilegivel na referencia nao pode ter source "
                "'reference_file' - use 'demo' (e liste no VALIDATION.md) ou pergunte."
            )
        page = entry.get("page")
        if page not in (None, "global") and page not in pages:
            warnings.append(f"copy[{eid}].page '{page}' nao existe em pages.")
        elif page in pages and entry.get("section") and entry["section"] not in pages[page]:
            warnings.append(f"copy[{eid}].section '{entry['section']}' nao existe em pages[{page}].sections.")


def check_media(bp, errors, warnings):
    """Classificacao de cada asset visual (bp.media)."""
    media = bp.get("media") or []
    uses_icon_library = False
    for i, item in enumerate(media):
        mid = item.get("id") or item.get("purpose") or f"#{i}"
        mtype = item.get("type")
        treatment = item.get("treatment")
        if mtype not in VALID_MEDIA_TYPES:
            errors.append(f"media[{mid}].type invalido: {mtype!r} (validos: {sorted(VALID_MEDIA_TYPES)}).")
        if treatment not in VALID_MEDIA_TREATMENTS:
            errors.append(f"media[{mid}].treatment invalido ou ausente: {treatment!r} (validos: {sorted(VALID_MEDIA_TREATMENTS)}).")
            continue
        if treatment == "icon_library":
            uses_icon_library = True
        if mtype in {"photo", "illustration", "logo"} and treatment == "css":
            errors.append(
                f"media[{mid}]: {mtype} nao pode ser desenhado em CSS/SVG a mao - "
                "use asset fornecido, recorte da referencia ou placeholder."
            )
        if mtype == "icon" and treatment not in {"icon_library", "provided"}:
            errors.append(f"media[{mid}]: icone deve vir de biblioteca de icones declarada ou de asset fornecido.")
        if treatment in PROVISIONAL_TREATMENTS and item.get("replace_before_launch") is not True:
            errors.append(
                f"media[{mid}]: treatment '{treatment}' e provisorio - marque "
                "replace_before_launch: true (e liste no VALIDATION.md)."
            )
        if mtype in RASTER_MEDIA and not item.get("aspect_ratio"):
            warnings.append(
                f"media[{mid}]: sem 'aspect_ratio' - imagem em container de "
                "proporcao fixa evita que o arquivo dite o layout."
            )
    if uses_icon_library and not (bp.get("design") or {}).get("icon_library"):
        errors.append("media usa treatment 'icon_library' mas design.icon_library nao foi definido.")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    path = sys.argv[1]
    bp = load(path)
    errors, warnings = check(bp)

    print(f"Validando {path}\n")

    if warnings:
        print(f"AVISOS ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"BLOQUEIOS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print("\nResultado: BLOQUEADO  -  resolva os itens acima antes de "
              "seguir para a aprovacao/implementacao.")
        sys.exit(1)

    print("Resultado: OK  -  nenhum bloqueio estrutural encontrado.")
    sys.exit(0)


if __name__ == "__main__":
    main()
