#!/usr/bin/env python3
"""
Gera um resumo em Markdown de um BLUEPRINT.yaml, pronto para apresentar ao
usuario na etapa de aprovacao (ver references/approval-protocol.md).

Uso:
    python render_blueprint_summary.py <caminho/para/BLUEPRINT.yaml>

Imprime o resumo no stdout. Nunca cole o YAML inteiro no chat em vez
deste resumo  -  o objetivo e que o usuario consiga revisar de verdade.
"""
import sys

try:
    import yaml
except ImportError:
    print("Erro: PyYAML nao esta instalado. Rode: pip install pyyaml")
    sys.exit(2)

# Console do Windows usa cp1252 por padrao e corrompe acentos dos textos do Blueprint.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



def load(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if "blueprint" in data:
        data = data["blueprint"]
    return data


def table(rows, headers):
    if not rows:
        return "_(nenhum)_\n"
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) if c else "" for c in r) + " |")
    return "\n".join(out) + "\n"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    bp = load(sys.argv[1])
    project = bp.get("project", {}) or {}
    pages = bp.get("pages") or []
    decisions = [d for d in (bp.get("decisions") or [])
                 if d.get("status") == "pending_user_approval"]
    uncertainties = [u for u in (bp.get("uncertainties") or [])
                      if u.get("status") == "pending"]
    plugins = (bp.get("plugins") or {}).get("required") or []
    dependencies = bp.get("dependencies") or []

    print(f"# Resumo para aprovacao  -  {project.get('name', '(sem nome)')}\n")
    print(f"Tipo: {project.get('type', '?')} | "
          f"Objetivo: {(project.get('objective') or {}).get('primary', '?')}\n")
    structure = project.get("site_structure", "?")
    behavior = (bp.get("theme") or {}).get("header_behavior", "?")
    nav_note = (" (menu de ancoras; header acompanha a rolagem e fica sempre visivel)"
                if structure == "single_page" else "")
    print(f"Estrutura: {structure} | Header: {behavior}{nav_note}\n")
    carousels = bp.get("carousels") or []
    if carousels:
        print(f"## Carrosseis ({len(carousels)})\n")
        print(table(
            [[c.get("id"), c.get("section"), c.get("kind"), c.get("slide_count"),
              {True: f"sim ({c.get('interval_ms')} ms, com pausa)", False: "nao"}.get(c.get("autoplay"), "A PERGUNTAR"),
              c.get("slides_content")] for c in carousels],
            ["Id", "Secao", "Tipo", "Slides", "Autoplay", "Conteudo dos slides"],
        ))
        print()
    forms = [f for f in (bp.get("forms") or []) if isinstance(f, dict)]
    if forms:
        print(f"## Formularios ({len(forms)})\n")
        print(table(
            [[f.get("id"), f.get("purpose"), len(f.get("fields") or []),
              f.get("destination") or "A PERGUNTAR", (f.get("privacy") or {}).get("notice", "?"),
              f.get("anti_spam")] for f in forms],
            ["Id", "Finalidade", "Campos", "Destino", "Aviso LGPD", "Anti-spam"],
        ))
        print()
    maps = bp.get("maps") or []
    if maps:
        print(f"## Mapas ({len(maps)})\n")
        print(table(
            [[m.get("id"), m.get("section"), m.get("provider"), m.get("address_field"),
              "so no clique" if m.get("load", "click") == "click" else "automatico"] for m in maps],
            ["Id", "Secao", "Provedor", "Endereco (opcoes)", "Carregamento"],
        ))
        print()
    galleries = bp.get("galleries") or []
    if galleries:
        print(f"## Galerias ({len(galleries)})\n")
        print(table(
            [[g.get("id"), g.get("section"), g.get("layout"),
              f"{g.get('visible_count')} de {g.get('total_count') or g.get('visible_count')}",
              {True: "sim", False: "nao"}.get(g.get("lightbox"), "A PERGUNTAR")] for g in galleries],
            ["Id", "Secao", "Layout", "Fotos (visiveis de total)", "Lightbox"],
        ))
        print()
    videos = bp.get("videos") or []
    if videos:
        print(f"## Videos ({len(videos)})\n")
        print(table(
            [[v.get("id"), v.get("section"), v.get("kind"), v.get("source"),
              "-" if v.get("kind") == "background" else {True: "sim", False: "nao"}.get(v.get("captions"), "A PERGUNTAR")]
             for v in videos],
            ["Id", "Secao", "Tipo", "Fonte", "Legendas"],
        ))
        print()
    accordions = bp.get("accordions") or []
    if accordions:
        print(f"## Acordeoes / FAQ ({len(accordions)})\n")
        print(table(
            [[a.get("id"), a.get("section"), "FAQ" if a.get("faq") else "acordeao", a.get("item_count"),
              {True: "sim", False: "nao"}.get(a.get("exclusive"), "A PERGUNTAR"), a.get("items_content")]
             for a in accordions],
            ["Id", "Secao", "Tipo", "Itens", "Um por vez", "Conteudo"],
        ))
        print()
    tabsets = bp.get("tabs") or []
    if tabsets:
        print(f"## Abas ({len(tabsets)})\n")
        print(table(
            [[t.get("id"), t.get("section"), t.get("tab_count"), t.get("active_in_reference"),
              t.get("mobile") or "A DECIDIR", t.get("items_content")] for t in tabsets],
            ["Id", "Secao", "Abas", "Ativa", "Celular", "Conteudo"],
        ))
        print()
    tables = bp.get("tables") or []
    if tables:
        print(f"## Tabelas ({len(tables)})\n")
        print(table(
            [[t.get("id"), t.get("section"), t.get("kind"), len(t.get("columns") or []), t.get("row_count"),
              t.get("mobile") or "A DECIDIR"] for t in tables],
            ["Id", "Secao", "Tipo", "Colunas", "Linhas", "Celular"],
        ))
        print()
    pricing = bp.get("pricing") or []
    if pricing:
        print(f"## Precos ({len(pricing)})\n")
        print(table(
            [[p.get("id"), p.get("section"), p.get("plan_count"), " / ".join(p.get("billing") or []),
              {"user": "confirmados", "demo": "DEMO (nao publicar)"}.get(p.get("price_source"), "A CONFIRMAR")]
             for p in pricing],
            ["Id", "Secao", "Planos", "Periodos", "Valores"],
        ))
        print()
    testimonials = bp.get("testimonials") or []
    logos = bp.get("client_logos") or []
    if testimonials or logos:
        print(f"## Prova social ({len(testimonials) + len(logos)})\n")
        rows = [[t.get("id"), "depoimentos", t.get("item_count"),
                 {"user": "reais, autorizados" if t.get("consent") else "reais SEM autorizacao",
                  "demo": "DEMO (oculto em producao)"}.get(t.get("content_source"), "A CONFIRMAR")]
                for t in testimonials]
        rows += [[c.get("id"), f"logos ({c.get('layout')})", c.get("logo_count"),
                  {"confirmed": "permissao confirmada", "demo": "DEMO (oculto em producao)"}.get(c.get("permission"), "A CONFIRMAR")]
                 for c in logos]
        print(table(rows, ["Id", "Tipo", "Itens", "Origem"]))
        print()
    team = bp.get("team") or []
    stats = bp.get("stats") or []
    if team or stats:
        print(f"## Equipe e numeros ({len(team) + len(stats)})\n")
        rows = [[t.get("id"), "equipe", t.get("member_count"),
                 t.get("registration") if t.get("registration") not in (None, "none") else "-",
                 {"user": "real, autorizada" if t.get("consent") else "real SEM autorizacao",
                  "demo": "DEMO (oculto em producao)"}.get(t.get("content_source"), "A CONFIRMAR")]
                for t in team]
        rows += [[s.get("id"), "numeros" + (" (contagem)" if s.get("count_up") else ""), s.get("item_count"), "-",
                  {"user": "confirmados", "demo": "DEMO (oculto em producao)"}.get(s.get("content_source"), "A CONFIRMAR")]
                 for s in stats]
        print(table(rows, ["Id", "Tipo", "Itens", "Registro", "Origem"]))
        print()
    blog = bp.get("blog") or {}
    if blog.get("enabled"):
        home = blog.get("home_section") or {}
        print("## Blog\n")
        print(table(
            [[blog.get("label"), f"/{blog.get('posts_page')}/", blog.get("posts_per_page"),
              f"{home.get('count')} na secao {home.get('section')}" if home else "-",
              {True: "sim", False: "nao"}.get(blog.get("comments"), "A DECIDIR"),
              {"user": "reais", "demo": "DEMO (oculto em producao)"}.get(blog.get("content_source"), "A CONFIRMAR")]],
            ["Nome", "Pagina", "Por pagina", "Na Home", "Comentarios", "Posts"],
        ))
        print()
    heroes = bp.get("heroes") or []
    banners = bp.get("banners") or []
    if heroes or banners:
        print(f"## Hero e banners ({len(heroes) + len(banners)})\n")
        rows = [[h.get("id"), h.get("kind"), " / ".join(b.get("label", "?") for b in h.get("buttons") or [] if isinstance(b, dict)) or "-",
                 h.get("overlay", "-"), h.get("mobile_image") or "-",
                 {True: "sim", False: "nao"}.get(h.get("breadcrumb"), "-")] for h in heroes]
        rows += [[b.get("id"), b.get("kind"), " / ".join(x.get("label", "?") for x in b.get("buttons") or [] if isinstance(x, dict)) or "-",
                  "-", "-", "reutilizavel" if b.get("reusable") else ("fechavel" if b.get("dismissible") else "-")] for b in banners]
        print(table(rows, ["Id", "Tipo", "Botoes", "Camada", "Celular", "Trilha/obs"]))
        print()
    fonts = bp.get("fonts") or {}
    if fonts.get("families"):
        print(f"## Fontes ({fonts.get('delivery')}{', reserva ajustada' if fonts.get('fallback_metrics') else ''})\n")
        print(table(
            [[f.get("family"), f.get("role"), ", ".join(str(w) for w in f.get("weights") or []),
              ", ".join(f.get("styles") or ["normal"]), ", ".join(str(w) for w in f.get("preload") or []) or "-",
              f.get("license") or "?"] for f in fonts["families"] if isinstance(f, dict)],
            ["Familia", "Uso", "Pesos", "Estilos", "Pre-carregar", "Licenca"],
        ))
        print()
    seo = bp.get("seo") or {}
    if seo.get("pages"):
        print(f"## SEO - descricao de cada pagina (tipo {seo.get('organization_type') or '?'}, "
              f"plugin {seo.get('plugin') or '?'})\n")
        print(table(
            [[s.get("page"), "nao indexar" if s.get("noindex") else s.get("description") or "-",
              len(s.get("description") or "") or "-", s.get("description_source") or "-"]
             for s in seo["pages"] if isinstance(s, dict)],
            ["Pagina", "Descricao (aparece no Google e ao compartilhar)", "Caracteres", "Origem"],
        ))
        print()
    if seo.get("ai_crawlers"):
        labels = {"allow": "liberados (treino e busca)", "block_training": "treino bloqueado, buscas com IA liberadas",
                  "block_all": "todos bloqueados"}
        print(f"Robos de IA no robots.txt: {labels.get(seo['ai_crawlers'], seo['ai_crawlers'])}"
              f"{' (PADRAO - confirmar)' if seo.get('ai_crawlers_source') == 'default' else ''}.")
        print()
    launch = bp.get("launch") or {}
    branding = ((bp.get("global_settings") or {}).get("branding") or {})
    redirects = bp.get("redirects") if isinstance(bp.get("redirects"), dict) else {}
    if launch or branding.get("site_icon") or redirects:
        print("## Publicacao\n")
        n_red = len(redirects.get("map") or [])
        old_site = redirects.get("old_site")
        old_txt = f"{old_site} ({n_red} redirecionamento(s))" if old_site else "nao ha"
        print(f"Dominio: {launch.get('domain') or 'A CONFIRMAR'} | Icone do site: {branding.get('site_icon') or '-'} | "
              f"Site antigo: {old_txt}.\n")
    security = bp.get("security") or {}
    if security:
        exc = [f"{e.get('rule')} ({e.get('reason')})" for e in security.get("exceptions") or [] if isinstance(e, dict)]
        print(f"## Seguranca\n\nProtecao basica: {security.get('hardening') or '?'}. "
              f"Excecoes: {', '.join(exc) or 'nenhuma'}.\n")
    header = bp.get("header") or {}
    if header.get("layout"):
        cta = header.get("cta") if isinstance(header.get("cta"), dict) else {}
        print("## Header\n")
        print(table(
            [[header.get("layout"), f"{cta.get('label')} -> {cta.get('target')}" if cta else "-",
              ", ".join(header.get("top_bar") or []) or "-", ", ".join(header.get("actions") or []) or "-",
              "sim" if header.get("transparent") else "nao", header.get("submenus"), header.get("mobile_menu") or "A DECIDIR"]],
            ["Logo", "Botao", "Barra superior", "Acoes", "Transparente", "Submenus", "Menu mobile"],
        ))
        print()
    footer = bp.get("footer") or {}
    social = bp.get("social") or {}
    if footer.get("columns") or social.get("networks"):
        print("## Rodape e redes\n")
        cols = " | ".join(
            (c.get("title") or c.get("kind", "?")) + (" + redes" if c.get("social") else "")
            for c in footer.get("columns") or [] if isinstance(c, dict))
        legal = footer.get("legal") or {}
        print(table(
            [[cols or "-",
              ", ".join(social.get("networks") or []) or "-",
              {"user": "informadas", "pending": "PENDENTES (icones ocultos)"}.get(social.get("urls_source"), "-"),
              "sim" if legal.get("privacy_link") else "NAO", "mostra" if legal.get("cnpj") == "shown" else "nao"]],
            ["Colunas", "Redes (ordem)", "URLs", "Privacidade", "CNPJ"],
        ))
        print()

    print(f"## Paginas ({len(pages)})\n")
    print(table(
        [[p.get("name"), p.get("slug"), p.get("template")] for p in pages],
        ["Nome", "Slug", "Template"],
    ))

    print(f"\n## Decisoes aguardando aprovacao ({len(decisions)})\n")
    print(table(
        [[d.get("id"), d.get("subject"), d.get("decision"),
          d.get("reason"), d.get("confidence")] for d in decisions],
        ["ID", "Assunto", "Decisao", "Razao", "Confianca"],
    ))

    print(f"\n## Incertezas pendentes ({len(uncertainties)})\n")
    print(table(
        [[u.get("id"), u.get("subject"), u.get("question"),
          "SIM" if u.get("blocking") else "nao", u.get("impact")]
         for u in uncertainties],
        ["ID", "Assunto", "Pergunta", "Bloqueante?", "Impacto"],
    ))

    print(f"\n## Plugins propostos ({len(plugins)})\n")
    print(table(
        [[p.get("name"), p.get("purpose"), p.get("reason")] for p in plugins],
        ["Plugin", "Finalidade", "Razao"],
    ))

    if dependencies:
        print(f"\n## Dependencias do ambiente ({len(dependencies)})\n")
        print(table(
            [[d.get("from"), d.get("depends_on"), d.get("reason")]
             for d in dependencies],
            ["De", "Depende de", "Razao"],
        ))

    blocking_count = sum(1 for u in uncertainties if u.get("blocking"))
    print("\n---")
    if blocking_count:
        print(f"**{blocking_count} incerteza(s) bloqueante(s) pendente(s)  -  "
              "a implementacao da parte afetada nao comeca ate isso ser "
              "resolvido.**")
    else:
        print("Nenhuma incerteza bloqueante pendente.")


if __name__ == "__main__":
    main()
