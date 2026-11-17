#!/usr/bin/env python3
"""
Confere a protecao basica de um site WordPress rodando
(references/security-seo.md). Faz, de fora, as mesmas perguntas que uma
ferramenta de ataque faz primeiro - e, com --path, confere por dentro
(WP-CLI) o que nao aparece por HTTP.

Uso:
    python check_security.py --url http://localhost/meu-site/ \
        [--path C:/wamp64/www/meu-site] [--blueprint BLUEPRINT.yaml] \
        [--out documentation/qa/seguranca.json] [--no-login-probe]

Checagens (P1 bloqueia a entrega; P2 e recomendacao):
  P1  XML-RPC respondendo (GET e POST system.listMethods)
  P1  login vazando: ?author=1 -> /author/<login>/, /author/<login>/,
      /wp-json/wp/v2/users e ?rest_route=/wp/v2/users para visitantes
  P1  erro de login diferente para usuario inexistente x senha errada
  P1  listagem de pastas (wp-content/uploads/, wp-includes/)
  P1  (--path) editor de arquivos do painel liberado; senha de admin fraca;
      mu-plugin project-hardening ausente
  P2  versao do WordPress no HTML/feed; readme.html/license.txt acessiveis
  P2  autor no oEmbed; usuarios no sitemap; cabecalho X-Pingback
  P2  cabecalhos nosniff / Referrer-Policy / anti-iframe; HSTS (so https)
  P2  (--path) usuario com login "admin"

Excecoes aprovadas (Blueprint security.exceptions ou PROJECT_ALLOW_* no
wp-config.php) pulam a checagem correspondente e aparecem no relatorio.

O teste de login faz 2 tentativas com senha errada (nao bloqueia conta no
WordPress padrao). --no-login-probe pula, para sites fora do ambiente local.

Saida: 0 sem P1, 1 com P1, 2 se o site nao responde.
"""
import argparse
import json
import re
import secrets
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402

UA = "Mozilla/5.0 (project-security-check)"
WEAK_PASSWORDS = ["admin", "123456", "12345678", "123456789", "password", "senha", "senha123",
                  "admin123", "mudar123", "qwerty", "teste", "test"]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def fetch(url, data=None, headers=None):
    """(status, headers, body) sem seguir redirecionamento."""
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    try:
        with OPENER.open(req, timeout=20) as res:
            return res.status, res.headers, res.read(400_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        body = err.read(400_000).decode("utf-8", "replace") if err.fp else ""
        return err.code, err.headers, body
    except urllib.error.URLError as err:
        return None, {}, str(err.reason)


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, check, ok, detail):
        self.items.append({"level": level, "check": check, "ok": bool(ok), "detail": detail})

    def skip(self, check, why):
        self.items.append({"level": "info", "check": check, "ok": True, "detail": f"pulado: {why}"})

    @property
    def failures(self):
        return [i for i in self.items if not i["ok"]]


def wp_eval(path, php):
    """Roda PHP dentro do WordPress (carrega mu-plugins e o tema)."""
    with tempfile.NamedTemporaryFile("w", suffix=".php", delete=False, encoding="utf-8") as tmp:
        tmp.write("<?php\n" + php)
    try:
        r = subprocess.run(_wpcli.resolve(["wp", "eval-file", tmp.name, "--skip-themes"]), cwd=path,
                           capture_output=True, text=True, timeout=120)
        return r.stdout.strip() if r.returncode == 0 else None
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def inside_checks(path, report, exceptions):
    out = wp_eval(path, r"""
$admins = get_users(['role' => 'administrator', 'fields' => ['ID', 'user_login', 'user_nicename', 'user_pass']]);
$weak = json_decode($argv_weak = '__WEAK__', true);
$rows = [];
foreach ($admins as $u) {
    $cands = array_merge($weak, [$u->user_login, $u->user_login . '123', get_bloginfo('name')]);
    $hit = null;
    foreach ($cands as $p) { if ($p !== '' && wp_check_password($p, $u->user_pass, $u->ID)) { $hit = true; break; } }
    $rows[] = ['login' => $u->user_login, 'nicename' => $u->user_nicename, 'weak' => (bool) $hit];
}
$allow = [];
foreach (['XMLRPC', 'AUTHOR_ARCHIVES', 'REST_USERS', 'FRAME_EMBEDDING'] as $r) {
    if (defined('PROJECT_ALLOW_' . $r) && constant('PROJECT_ALLOW_' . $r)) { $allow[] = strtolower($r); }
}
echo wp_json_encode([
    'file_edit_blocked' => defined('DISALLOW_FILE_EDIT') && DISALLOW_FILE_EDIT,
    'hardening' => function_exists('project_hardening_allows'),
    'admins' => $rows,
    'allow' => $allow,
]);
""".replace("__WEAK__", json.dumps(WEAK_PASSWORDS)))
    if out is None:
        report.skip("checagens internas (--path)", "WP-CLI falhou nesta pasta")
        return None
    try:
        data = json.loads(out.splitlines()[-1])
    except (ValueError, IndexError):
        report.skip("checagens internas (--path)", f"resposta inesperada do WP-CLI: {out[:120]}")
        return None
    exceptions.update(data.get("allow") or [])
    report.add("P1", "mu-plugin project-hardening ativo", data["hardening"],
               "carregado" if data["hardening"] else "wp-content/mu-plugins/project-hardening.php ausente")
    report.add("P1", "editor de arquivos do painel bloqueado", data["file_edit_blocked"],
               "DISALLOW_FILE_EDIT ativo" if data["file_edit_blocked"] else "Aparencia > Editor grava PHP pelo navegador")
    weak = [a["login"] for a in data["admins"] if a["weak"]]
    report.add("P1", "senha dos administradores", not weak,
               f"senha fraca/obvia: {', '.join(weak)}" if weak else f"{len(data['admins'])} admin(s) sem senha obvia")
    physical = Path(path, "robots.txt").exists()
    report.add("P2", "robots.txt virtual (sem arquivo fisico)", not physical,
               "robots.txt fisico na raiz anula a politica de robos de IA do tema (Configuracoes do Site)"
               if physical else "gerado pelo WordPress + tema")
    named_admin = [a["login"] for a in data["admins"] if a["login"].lower() == "admin"]
    report.add("P2", "login 'admin'", not named_admin,
               "login 'admin' e o primeiro alvo de forca bruta - na producao, cada pessoa com o proprio usuario"
               if named_admin else "nenhum administrador com login 'admin'")
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="URL da Home (ex.: http://localhost/meu-site/)")
    ap.add_argument("--path", help="pasta do WordPress (habilita checagens internas via WP-CLI)")
    ap.add_argument("--blueprint", help="BLUEPRINT.yaml (le security.exceptions)")
    ap.add_argument("--user", help="login real para o teste de erro de login (padrao: o 1o admin via --path, ou 'admin')")
    ap.add_argument("--no-login-probe", action="store_true")
    ap.add_argument("--out", help="grava o relatorio em JSON")
    args = ap.parse_args()

    base = args.url.rstrip("/") + "/"
    status, home_headers, home = fetch(base)
    if status is None or status >= 500:
        print(f"BLOQUEADO: {base} nao respondeu ({status or home}).")
        sys.exit(2)

    report = Report()
    exceptions = set()
    if args.blueprint:
        import yaml
        bp = yaml.safe_load(Path(args.blueprint).read_text(encoding="utf-8")) or {}
        exceptions.update(e.get("rule") for e in ((bp.get("security") or {}).get("exceptions") or []) if isinstance(e, dict))
    inside = inside_checks(args.path, report, exceptions) if args.path else None
    login = args.user or ((inside or {}).get("admins") or [{}])[0].get("login") or "admin"
    nicename = ((inside or {}).get("admins") or [{}])[0].get("nicename") or login

    # 1. XML-RPC
    if "xmlrpc" in exceptions:
        report.skip("XML-RPC", "excecao aprovada (xmlrpc)")
    else:
        st, _h, body = fetch(base + "xmlrpc.php")
        report.add("P1", "XML-RPC (GET)", st in (401, 403, 404, 410),
                   f"HTTP {st}" + (" - 'XML-RPC server accepts POST requests only'" if "XML-RPC server" in body else ""))
        xml = b"<?xml version='1.0'?><methodCall><methodName>system.listMethods</methodName><params/></methodCall>"
        st, _h, body = fetch(base + "xmlrpc.php", data=xml, headers={"Content-Type": "text/xml"})
        report.add("P1", "XML-RPC (POST system.listMethods)", "<methodResponse>" not in body,
                   f"HTTP {st}" + (" - lista os metodos (multicall = forca bruta em massa)" if "<methodResponse>" in body else ""))
        report.add("P2", "cabecalho X-Pingback", not home_headers.get("X-Pingback"),
                   home_headers.get("X-Pingback") or "ausente")

    # 2. Enumeracao de usuarios
    if "author_archives" in exceptions:
        report.skip("?author=1 e /author/<login>/", "excecao aprovada (author_archives)")
    else:
        st, h, body = fetch(base + "?author=1")
        loc = (h.get("Location") or "") if h else ""
        leaked = "/author/" in loc or re.search(r'class="[^"]*\bauthor-[a-z0-9_-]+', body)
        report.add("P1", "?author=1 nao revela o login", not leaked,
                   f"redireciona para {loc}" if "/author/" in loc else f"HTTP {st}")
        st, _h, body = fetch(base + f"author/{urllib.parse.quote(nicename)}/")
        report.add("P1", "/author/<login>/ fechado", st != 200, f"HTTP {st} em /author/{nicename}/")
    if "rest_users" in exceptions:
        report.skip("/wp-json/wp/v2/users", "excecao aprovada (rest_users)")
    else:
        for path in ("wp-json/wp/v2/users", "?rest_route=/wp/v2/users"):
            st, _h, body = fetch(base + path)
            # Lista vazia tambem e falha: o core so lista quem tem post
            # publicado - vaza o login no primeiro post.
            open_list = st == 200 and body.lstrip().startswith("[")
            detail = f"HTTP {st}"
            if open_list:
                detail += " - lista os usuarios" if '"slug"' in body else \
                    " - aberto (vazio agora; mostra o login de quem publicar o primeiro post)"
            report.add("P1", f"{path} fechado para visitantes", not open_list, detail)
    # oEmbed de um post/pagina real (a Home de posts nao e incorporavel).
    target = base
    for kind in ("posts", "pages"):
        _st, _h, listing = fetch(base + f"wp-json/wp/v2/{kind}?per_page=1&_fields=link")
        m = re.search(r'"link"\s*:\s*"([^"]+)"', listing)
        if m:
            target = m.group(1).replace("\\/", "/")
            break
    st, _h, body = fetch(base + "wp-json/oembed/1.0/embed?url=" + urllib.parse.quote(target))
    report.add("P2", "oEmbed sem autor", '"author_name"' not in body,
               f"HTTP {st} ({target})" + (" - revela o autor" if '"author_name"' in body else ""))
    st, _h, body = fetch(base + "wp-sitemap-users-1.xml")
    report.add("P2", "sitemap sem usuarios", not (st == 200 and "<loc>" in body), f"HTTP {st}")

    # 3. Erro de login generico
    if args.no_login_probe:
        report.skip("erro de login generico", "--no-login-probe")
    else:
        def login_error(user):
            data = urllib.parse.urlencode({"log": user, "pwd": "x-" + secrets.token_hex(8),
                                           "wp-submit": "Log In", "testcookie": "1"}).encode()
            _st, _h, body = fetch(base + "wp-login.php", data=data, headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "wordpress_test_cookie=WP%20Cookie%20check"})
            m = re.search(r'id="login_error"[^>]*>(.*?)</div>', body, re.S)
            return re.sub(r"<[^>]+>|\s+", " ", m.group(1)).strip() if m else ""
        fake = login_error("naoexiste-" + secrets.token_hex(4))
        real = login_error(login)
        same = bool(fake) and fake.replace(login, "") == real.replace(login, "") and "registrado" not in fake.lower() \
            and "not registered" not in fake.lower()
        report.add("P1", "erro de login nao diz se o usuario existe", same,
                   f"inexistente: \"{fake[:90]}\" | senha errada: \"{real[:90]}\"")

    # 4. Arquivos e pastas
    for path in ("wp-content/uploads/", "wp-includes/"):
        st, _h, body = fetch(base + path)
        listing = st == 200 and "Index of" in body
        report.add("P1", f"sem listagem em /{path}", not listing, f"HTTP {st}" + (" - 'Index of' (lista os arquivos)" if listing else ""))
    for path in ("readme.html", "license.txt"):
        st, _h, _b = fetch(base + path)
        report.add("P2", f"/{path} inacessivel", st != 200, f"HTTP {st} (revela a versao)" if st == 200 else f"HTTP {st}")

    # 5. Versao no HTML e no feed
    gen = re.search(r'<meta name="generator" content="WordPress[^"]*"', home)
    report.add("P2", "versao do WordPress fora do HTML", not gen, gen.group(0) if gen else "sem meta generator")
    st, _h, feed = fetch(base + "feed/")
    fgen = re.search(r"<generator>[^<]*\?v=[\d.]+</generator>", feed)
    report.add("P2", "versao do WordPress fora do feed", not fgen, fgen.group(0) if fgen else f"HTTP {st}")

    # 6. Cabecalhos
    hdr = {k.lower(): v for k, v in (home_headers.items() if home_headers else [])}
    report.add("P2", "X-Content-Type-Options: nosniff", hdr.get("x-content-type-options", "").lower() == "nosniff",
               hdr.get("x-content-type-options") or "ausente")
    report.add("P2", "Referrer-Policy", bool(hdr.get("referrer-policy")), hdr.get("referrer-policy") or "ausente")
    if "frame_embedding" in exceptions:
        report.skip("anti-iframe de terceiros", "excecao aprovada (frame_embedding)")
    else:
        anti = hdr.get("x-frame-options") or ("frame-ancestors" in hdr.get("content-security-policy", "") and "frame-ancestors")
        report.add("P2", "anti-iframe de terceiros (X-Frame-Options/frame-ancestors)", bool(anti), anti or "ausente")
    if base.startswith("https://"):
        report.add("P2", "HSTS (https)", bool(hdr.get("strict-transport-security")),
                   hdr.get("strict-transport-security") or "ausente (so em producao)")

    # Relatorio
    fails = report.failures
    p1 = [i for i in fails if i["level"] == "P1"]
    print(f"Seguranca - {base}\n")
    for i in report.items:
        mark = "ok  " if i["ok"] else ("P1  " if i["level"] == "P1" else "P2  ")
        if i["level"] == "info":
            mark = "--  "
        print(f"{mark}{i['check']}: {i['detail']}")
    if exceptions:
        print(f"\nExcecoes aprovadas: {', '.join(sorted(e for e in exceptions if e))}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"url": base, "exceptions": sorted(e for e in exceptions if e),
                                              "items": report.items}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(p1)} P1, {len(fails) - len(p1)} P2.")
    sys.exit(1 if p1 else 0)


if __name__ == "__main__":
    main()
