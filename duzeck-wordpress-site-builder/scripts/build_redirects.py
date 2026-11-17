#!/usr/bin/env python3
"""
Redirecionamentos do site antigo (references/redirects.md).

Tres modos:

  --suggest   le o sitemap do site ANTIGO e propoe para onde vai cada
              endereco (semelhanca com as paginas do Blueprint). Saida em
              YAML para colar em redirects.map - o usuario confirma.
                python build_redirects.py --blueprint BLUEPRINT.yaml --suggest \
                    --old-sitemap https://site-antigo.com.br/sitemap.xml

  --write     grava <wordpress>/wp-content/project-redirects.json a partir
              de redirects.map do Blueprint (lido pelo mu-plugin
              project-redirects.php).
                python build_redirects.py --blueprint BLUEPRINT.yaml --write --path C:/wamp64/www/site

  --check     confere no site novo: cada endereco antigo responde 301 para
              o destino e o destino abre (200). Com --old-sitemap, aponta
              tambem enderecos antigos SEM destino (viram 404).
                python build_redirects.py --blueprint BLUEPRINT.yaml --check --url http://localhost/site/

Saida do --check: 0 sem falha, 1 com falha.
"""
import argparse
import difflib
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = "Mozilla/5.0 (project-redirects-check)"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch(url, follow=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with (urllib.request.urlopen if follow else OPENER.open)(req, timeout=20) as res:
            return res.status, res.headers, res.read(2_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        return err.code, err.headers, ""
    except urllib.error.URLError as err:
        return None, {}, str(err.reason)


def load_bp(path):
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return raw.get("blueprint", raw)


def old_paths(sitemap):
    """Caminhos do sitemap antigo (URL ou arquivo; segue sitemap index)."""
    seen, out, queue = set(), [], [sitemap]
    while queue:
        src = queue.pop(0)
        if src in seen:
            continue
        seen.add(src)
        if re.match(r"https?://", src):
            _st, _h, body = fetch(src, follow=True)
        else:
            body = Path(src).read_text(encoding="utf-8", errors="replace")
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body)
        if "<sitemapindex" in body:
            queue += locs
        else:
            out += [urllib.parse.urlparse(u).path or "/" for u in locs]
    return list(dict.fromkeys(out))


def key(path):
    path = urllib.parse.unquote(urllib.parse.urlparse(path).path or "/").lower()
    path = re.sub(r"/index\.(html?|php|aspx?)$", "/", path)
    path = re.sub(r"\.(html?|php|aspx?)$", "", path)
    return "/" + path.strip("/")


# Nomes comuns de paginas institucionais em portugues -> um conceito so.
# A semelhanca de letras sozinha nao sabe que "quem somos" = "sobre".
SYNONYMS = [
    ("sobre", r"quem[- ]?somos|sobre|empresa|institucional|a[- ]empresa|historia|nossa[- ]historia|about"),
    ("contato", r"fale[- ]?conosco|contato|contatos|atendimento|contact|orcamento|localizacao|onde[- ]estamos"),
    ("servicos", r"servicos|solucoes|o[- ]que[- ]fazemos|services|especialidades"),
    ("projetos", r"projetos|portfolio|portifolio|obras|trabalhos|cases|galeria"),
    ("blog", r"blog|noticias|novidades|artigos|imprensa|news"),
    ("carreiras", r"trabalhe[- ]?conosco|carreiras|vagas|jobs"),
    ("privacidade", r"privacidade|politica[- ]de[- ]privacidade|lgpd|termos"),
]


def concept(text):
    t = re.sub(r"[-_/]+", " ", text.lower())
    t = t.translate(str.maketrans("áàâãéêíóôõúç", "aaaaeeiooouc"))
    for name, pattern in SYNONYMS:
        if re.search(rf"(^|\s)({pattern.replace('[- ]', '[ ]')})(\s|$)", t):
            return name
    return None


def new_pages(bp):
    pages = {}
    for p in bp.get("pages") or []:
        slug = str(p.get("slug") or "").strip("/")
        if "<" in slug or "{" in slug:
            continue
        pages[p.get("id")] = {"path": f"/{slug}/" if slug else "/", "words": f"{slug} {p.get('name') or ''}".lower()}
    return pages


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--blueprint", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--suggest", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--old-sitemap", help="URL ou arquivo do sitemap do site antigo")
    ap.add_argument("--path", help="pasta do WordPress (--write)")
    ap.add_argument("--url", help="URL do site novo (--check)")
    args = ap.parse_args()

    bp = load_bp(args.blueprint)
    red = bp.get("redirects") if isinstance(bp.get("redirects"), dict) else {}
    pages = new_pages(bp)
    page_paths = {key(p["path"]) for p in pages.values()}

    if args.suggest:
        sitemap = args.old_sitemap or (f"{red['old_site'].rstrip('/')}/sitemap.xml" if red.get("old_site") else None)
        if not sitemap:
            ap.error("--suggest precisa de --old-sitemap ou redirects.old_site no Blueprint")
        paths = old_paths(sitemap)
        print(f"# {len(paths)} endereco(s) no sitemap antigo. Confirme cada destino com o usuario.")
        print("redirects:\n  old_site: " + (red.get("old_site") or "null") + "\n  map:")
        exact_pages = {"/" + p["path"].strip("/") for p in pages.values()}
        for path in paths:
            k = key(path)
            if "/" + urllib.parse.unquote(path).lower().strip("/") in exact_pages:
                print(f"    # {path} -> continua existindo no site novo (sem redirecionamento)")
                continue
            words = re.sub(r"[-_/]+", " ", k).strip()
            c = concept(words)
            by_concept = [pid for pid, p in pages.items() if c and concept(p["words"]) == c]
            if by_concept:
                print(f"    - {{ from: \"{path}\", to: {by_concept[0]}, confidence: high }}   # mesmo assunto: {c}")
                continue
            best = max(pages.items(), key=lambda kv: difflib.SequenceMatcher(None, words, kv[1]["words"]).ratio(), default=None)
            score = difflib.SequenceMatcher(None, words, best[1]["words"]).ratio() if best else 0
            if c or not best or score < 0.6:
                # Assunto sem pagina equivalente (ex.: "trabalhe conosco"): nao
                # inventar destino - a Home e so um palpite a confirmar.
                note = f"sem pagina de '{c}' no site novo" if c else f"sem equivalente claro (semelhanca {score:.2f})"
                print(f"    - {{ from: \"{path}\", to: home, confidence: low }}   # CONFIRMAR: {note}")
            else:
                print(f"    - {{ from: \"{path}\", to: {best[0]}, confidence: {'high' if score >= 0.75 else 'low'} }}   # semelhanca {score:.2f}")
        return

    entries = []
    for i, row in enumerate(red.get("map") or []):
        if not isinstance(row, dict) or not str(row.get("from", "")).startswith("/"):
            sys.exit(f"redirects.map[{i}]: 'from' deve ser um caminho comecando com '/'.")
        to = row.get("to")
        target = pages[to]["path"] if to in pages else str(to or "")
        if not target.startswith(("/", "http")):
            sys.exit(f"redirects.map[{i}] ({row['from']}): 'to' deve ser id de pages[], caminho '/...' ou URL.")
        entries.append({"from": row["from"], "to": target})

    if args.write:
        if not args.path:
            ap.error("--write precisa de --path")
        dest = Path(args.path) / "wp-content" / "project-redirects.json"
        dest.write_text(json.dumps({"generated_by": "build_redirects.py", "map": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Gravado: {dest} ({len(entries)} redirecionamento(s))")
        return

    if not args.url:
        ap.error("--check precisa de --url")
    base = args.url.rstrip("/")
    base_path = urllib.parse.urlparse(base).path.rstrip("/")

    def site_key(url):
        """Caminho dentro do site (sem a subpasta do WAMP), normalizado."""
        p = urllib.parse.urlparse(url).path
        if base_path and p.startswith(base_path):
            p = p[len(base_path):]
        return key(p)

    fails = 0
    for e in entries:
        st, h, _ = fetch(base + e["from"])
        loc = (h.get("Location") or "") if h else ""
        want = e["to"] if e["to"].startswith("http") else base + e["to"]
        ok = st == 301 and site_key(loc) == site_key(want)
        dst = fetch(loc or want, follow=True)[0] if ok else None
        if ok and dst == 200:
            print(f"ok  {e['from']} -> 301 {loc}")
        else:
            fails += 1
            print(f"P1  {e['from']}: HTTP {st}{' -> ' + loc if loc else ''} (esperado 301 para {want}{', destino abre ' + str(dst) if dst else ''})")
    if args.old_sitemap:
        mapped = {key(e["from"]) for e in entries}
        for path in old_paths(args.old_sitemap):
            if key(path) not in mapped:   # quem decide e a resposta real (404 = sem destino)
                st = fetch(base + path)[0]
                if st == 404:
                    fails += 1
                    print(f"P1  {path}: endereco antigo sem destino (404) - acrescente em redirects.map")
    print(f"\n{len(entries)} redirecionamento(s) conferido(s), {fails} falha(s).")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
