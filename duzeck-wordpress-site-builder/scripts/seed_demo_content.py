#!/usr/bin/env python3
"""
Popula conteudo demo via WP-CLI a partir de um arquivo JSON de itens de
demonstracao (nao a partir do BLUEPRINT.yaml diretamente  -  o Blueprint
descreve a ESTRUTURA dos content_types, nao os valores de cada item demo;
quem monta a Skill/agente escreve o conteudo demo plausivel e salva nesse
JSON antes de rodar este script).

Formato esperado do JSON (--items):
[
  {
    "post_type": "service",
    "title": "Reforma Residencial",
    "status": "publish",
    "meta": {"service_short_description": "Reforma completa...", "service_icon": "hammer"},
    "terms": {"project_category": ["reformas"]}
  }
]

Limitacao conhecida (descoberta rodando o caso Construtora Horizonte):
este script grava meta bruta via `wp post meta update`, NAO via ACF. Isso
significa que get_field() do ACF NAO le esses valores, mesmo com o ACF
PRO ativo - ele exige tambem uma meta de referencia ("_<nome>") que so o
proprio ACF grava. Por isso o theme-skeleton usa project_field() (ver
inc/helpers.php), que cai para get_post_meta() bruto quando get_field()
nao retorna nada - assim o conteudo semeado por este script aparece no
front-end mesmo antes do ACF estar configurado. Use project_field() em
vez de get_field() direto em qualquer template que deva exibir esse
conteudo demo.

Isso NAO resolve campos repeater/gallery/relationship, que nao tem um
equivalente simples em post meta bruta. Para esses, registre no
VALIDATION.md que o preenchimento foi feito manualmente pelo admin apos o
scaffold, ou faca via `wp eval-file` com update_field() do ACF (requer
ACF ja ativo) se o volume justificar o esforco.

Uso:
    python seed_demo_content.py --project-dir "C:\\wamp64\\www\\<slug>" \
        --items demo_content.json --blueprint documentation/BLUEPRINT.yaml

Com --blueprint (recomendado), ANTES de gravar qualquer coisa:
- confere se cada post_type existe em content_types e se cada chave de
  meta existe nos fields daquele content_type (pega nome de campo
  divergente, ex.: 'short_description' vs. 'service_short_description');
- confere se cada termo usa uma taxonomia do Blueprint;
- classifica cada titulo como texto da REFERENCIA (consta em copy com
  source reference_file/user) ou DEMO, e imprime a lista em Markdown para
  colar na secao "Conteudo demo identificado" do VALIDATION.md.
Se houver divergencia, nada e criado (exit 1).

--check-only faz so essa conferencia, sem chamar o wp-cli.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402


# Console do Windows usa cp1252 por padrao e corrompe acentos dos textos do Blueprint.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")



def run(cmd, cwd):
    # Ver nota equivalente em scaffold_wp_project.py: no Windows, "wp" sem
    # extensao so e resolvido para wp.exe automaticamente, nao wp.bat.
    # wp -> WP-CLI com o mesmo PHP do Apache (ver _wpcli.py); demais: resolve .bat/.cmd.
    cmd = _wpcli.resolve(cmd)
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=False,
                             capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Falhou: {result.stderr.strip()}")
        return None
    return result.stdout.strip()


def check_against_blueprint(items, blueprint_path):
    """Retorna (errors, report_lines)."""
    try:
        import yaml
    except ImportError:
        print("Erro: PyYAML nao esta instalado. Rode: pip install pyyaml")
        sys.exit(2)
    with open(blueprint_path, "r", encoding="utf-8") as f:
        bp = yaml.safe_load(f) or {}
    bp = bp.get("blueprint", bp)

    types = {}
    for ct in bp.get("content_types") or []:
        slug = ((ct.get("wordpress") or {}).get("slug")) or ct.get("id")
        types[slug] = {fld.get("id") for fld in (ct.get("fields") or [])}
    taxonomies = {tx.get("slug") or tx.get("id") for tx in (bp.get("taxonomies") or [])}
    real_texts = {
        str(c.get("text", "")).strip().lower()
        for c in (bp.get("copy") or [])
        if c.get("source") in {"reference_file", "user"}
    }

    errors, report = [], []
    for item in items:
        pt, title = item.get("post_type"), item.get("title", "")
        if pt not in types:
            errors.append(f"'{title}': post_type '{pt}' nao existe em content_types ({sorted(types)}).")
            continue
        unknown = sorted(set(item.get("meta") or {}) - types[pt])
        if unknown:
            errors.append(
                f"'{title}' ({pt}): meta fora dos fields do Blueprint: {unknown}. "
                f"Fields validos: {sorted(types[pt])}."
            )
        bad_tax = sorted(set(item.get("terms") or {}) - taxonomies)
        if bad_tax:
            errors.append(f"'{title}' ({pt}): taxonomia(s) inexistente(s) no Blueprint: {bad_tax}.")
        origin = "referencia" if title.strip().lower() in real_texts else "DEMO"
        report.append(f"- [{origin}] {pt}: {title}")
    return errors, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=False)
    ap.add_argument("--items", required=True, help="JSON com itens demo")
    ap.add_argument("--blueprint", help="BLUEPRINT.yaml para conferir post_types/fields/taxonomias")
    ap.add_argument("--check-only", action="store_true",
                    help="so confere contra o Blueprint, sem chamar wp-cli")
    args = ap.parse_args()

    with open(args.items, "r", encoding="utf-8") as f:
        items = json.load(f)

    if args.check_only and not args.blueprint:
        ap.error("--check-only exige --blueprint")
    if not args.check_only and not args.project_dir:
        ap.error("--project-dir e obrigatorio (exceto com --check-only)")

    if args.blueprint:
        errors, report = check_against_blueprint(items, args.blueprint)
        if errors:
            print(f"BLOQUEIOS ({len(errors)}) - nada foi criado:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        print("Conferencia contra o Blueprint: OK.")
        print()
        print("Origem dos titulos (cole os itens DEMO no VALIDATION.md):")
        for line in report:
            print(line)
        if args.check_only:
            sys.exit(0)
        print()

    created = []
    for item in items:
        post_id = run([
            "wp", "post", "create",
            "--post_type=" + item["post_type"],
            "--post_title=" + item["title"],
            "--post_status=" + item.get("status", "publish"),
            "--porcelain",
        ], cwd=args.project_dir)
        if not post_id:
            print(f"  Pulando meta/terms de '{item['title']}' "
                  "(criacao falhou).")
            continue

        for key, value in (item.get("meta") or {}).items():
            run(["wp", "post", "meta", "update", post_id, key, str(value)],
                cwd=args.project_dir)

        for taxonomy, terms in (item.get("terms") or {}).items():
            run(["wp", "post", "term", "add", post_id, taxonomy,
                 *terms], cwd=args.project_dir)

        created.append((item["post_type"], item["title"], post_id))

    print(f"\n{len(created)}/{len(items)} itens demo criados com sucesso.")
    for pt, title, pid in created:
        print(f"  [{pt}] {title} (ID {pid})")

    if len(created) < len(items):
        sys.exit(1)


if __name__ == "__main__":
    main()
