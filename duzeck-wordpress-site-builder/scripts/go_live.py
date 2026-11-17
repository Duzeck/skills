#!/usr/bin/env python3
"""
Monta o PACOTE DE PUBLICACAO do site local (references/go-live.md).

NAO altera o banco nem os arquivos do site local: so le e exporta.

Uso:
    python go_live.py --path C:/wamp64/www/meu-site --domain https://www.meusite.com.br \
        --out C:/publicacao/meu-site [--no-uploads]

Gera em --out:
  backup-local-<data>.sql   copia de seguranca do banco local, intacta
  banco-producao.sql        o mesmo banco com http://localhost/<slug> trocado
                            pelo dominio - inclusive dentro de dados
                            serializados (opcoes, campos ACF, widgets) e na
                            forma escapada dos blocos (http:\\/\\/...); feito
                            pelo WP-CLI, que recalcula os tamanhos serializados
                            (troca de texto simples corromperia esses dados)
  wp-content.zip            tema, mu-plugins (sem o de e-mail local), uploads
  .htaccess                 da RAIZ do dominio (protecao + WordPress, RewriteBase /)
  favicon.ico               se o site tiver Icone do site (alguns servidores so
                            servem /favicon.ico como arquivo fisico)
  wp-config-producao.txt    constantes e chaves de seguranca NOVAS
  LEIA-ME-PUBLICACAO.md     passo a passo na hospedagem + o que conferir depois

Antes: rode prelaunch_check.py (--stage local) e resolva os P0/P1.
"""
import argparse
import datetime
import io
import json
import re
import secrets
import string
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402
from scaffold_wp_project import hardening_htaccess_block  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKIP_MU = {"project-local-mail.php"}   # so para o WAMP: em producao, SMTP de verdade


def wp(path, *args, check=True):
    r = subprocess.run(_wpcli.resolve(["wp", *args]), cwd=path, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    if check and r.returncode != 0:
        sys.exit(f"BLOQUEADO: wp {' '.join(args[:3])} falhou: {(r.stderr or r.stdout).strip()[:400]}")
    return r.stdout.strip()


def salts():
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_[]{}<>~+=,.;:/?|"
    names = ["AUTH_KEY", "SECURE_AUTH_KEY", "LOGGED_IN_KEY", "NONCE_KEY",
             "AUTH_SALT", "SECURE_AUTH_SALT", "LOGGED_IN_SALT", "NONCE_SALT"]
    return "\n".join(f"define('{n}', '{''.join(secrets.choice(chars) for _ in range(64))}');" for n in names)


def zip_dir(zf, src, arc_root, skip=()):
    count = 0
    for f in sorted(src.rglob("*")):
        if f.is_file() and f.name not in skip and "__pycache__" not in f.parts:
            zf.write(f, f"{arc_root}/{f.relative_to(src).as_posix()}")
            count += 1
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", required=True, help="pasta do WordPress local")
    ap.add_argument("--domain", required=True, help="endereco final, ex.: https://www.meusite.com.br")
    ap.add_argument("--out", required=True, help="pasta do pacote (fora da pasta publica do WAMP)")
    ap.add_argument("--no-uploads", action="store_true", help="nao incluir wp-content/uploads")
    args = ap.parse_args()

    domain = args.domain.rstrip("/")
    if not re.fullmatch(r"https?://[a-z0-9.-]+\.[a-z]{2,}(:\d+)?", domain, re.I):
        sys.exit(f"--domain invalido: {args.domain} (ex.: https://www.meusite.com.br, sem caminho)")
    if not domain.startswith("https://"):
        print("Aviso: dominio sem https - use https na producao.")
    path = Path(args.path)
    out = Path(args.out)
    if str(out.resolve()).lower().startswith(str(path.resolve()).lower()):
        sys.exit("--out nao pode ficar dentro do site (o pacote ficaria acessivel pelo navegador).")
    out.mkdir(parents=True, exist_ok=True)

    old = wp(path, "option", "get", "siteurl").rstrip("/")
    if old == domain:
        sys.exit("O site ja esta no dominio final - nada a trocar.")
    stamp = datetime.date.today().isoformat()
    print(f"Origem: {old}\nDestino: {domain}\n")

    # 1. Copia de seguranca (banco local intacto)
    backup = out / f"backup-local-{stamp}.sql"
    wp(path, "db", "export", str(backup), "--quiet")
    print(f"1. Copia de seguranca: {backup.name} ({backup.stat().st_size // 1024} KB)")

    # 2. Previa da troca e banco de producao. Uma passada com regex cobre as
    #    duas formas: http://localhost/x e http:\/\/localhost\/x (JSON dos blocos).
    host_path = re.sub(r"^https?://", "", old)
    new_host = re.sub(r"^https?://", "", domain)
    scheme = "https" if domain.startswith("https://") else "http"
    parts = [re.escape(p) for p in host_path.split("/")]
    sep = r"(\\?/)"   # regex PCRE: "/" ou "\/" (barra invertida opcional)
    # Fim do endereco: nao seguido de letra/hifen (evita .../site2, .../site-velho)
    # nem de ".letra" (.../site.old) - mas ponto final de frase vale.
    pattern = r"https?:" + sep + r"\1" + r"\1".join(parts) + r"(?![\w-]|\.\w)"
    # ${1} (e nao $1): dominio comecando com digito viraria $12.
    replacement = scheme + ":${1}${1}" + "${1}".join(new_host.split("/"))
    preview = wp(path, "search-replace", pattern, replacement, "--regex", "--regex-delimiter=#",
                 "--all-tables-with-prefix", "--dry-run", "--report-changed-only", "--format=count")
    prod_sql = out / "banco-producao.sql"
    wp(path, "search-replace", pattern, replacement, "--regex", "--regex-delimiter=#",
       "--all-tables-with-prefix", f"--export={prod_sql}", "--quiet")
    leftover = prod_sql.read_text(encoding="utf-8", errors="replace").count(host_path)
    print(f"2. Banco de producao: {prod_sql.name} ({preview} troca(s); restos de '{host_path}': {leftover})")
    if leftover:
        print("   ATENCAO: ainda ha referencias ao endereco local - confira antes de importar.")

    # 3. Arquivos
    theme = wp(path, "option", "get", "stylesheet")
    content = path / "wp-content"
    zpath = out / "wp-content.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        n_theme = zip_dir(zf, content / "themes" / theme, f"wp-content/themes/{theme}")
        n_mu = zip_dir(zf, content / "mu-plugins", "wp-content/mu-plugins", skip=SKIP_MU) if (content / "mu-plugins").is_dir() else 0
        n_up = 0 if args.no_uploads or not (content / "uploads").is_dir() else zip_dir(zf, content / "uploads", "wp-content/uploads")
        if (content / "project-redirects.json").is_file():
            zf.write(content / "project-redirects.json", "wp-content/project-redirects.json")
    print(f"3. Arquivos: {zpath.name} (tema {n_theme}, mu-plugins {n_mu}, uploads {n_up} arquivo(s); "
          f"{zpath.stat().st_size // 1024} KB)")

    # 4. .htaccess da raiz e favicon.ico
    allow = json.loads(wp(path, "eval", "echo wp_json_encode(array_values(array_filter(['xmlrpc','author_archives','rest_users','frame_embedding'], function($r){$c='PROJECT_ALLOW_'.strtoupper($r); return defined($c) && constant($c);})));"))
    (out / ".htaccess").write_text(
        hardening_htaccess_block("xmlrpc" in allow) +
        "# BEGIN WordPress\n<IfModule mod_rewrite.c>\nRewriteEngine On\n"
        "RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]\nRewriteBase /\n"
        "RewriteRule ^index\\.php$ - [L]\nRewriteCond %{REQUEST_FILENAME} !-f\nRewriteCond %{REQUEST_FILENAME} !-d\n"
        "RewriteRule . /index.php [L]\n</IfModule>\n# END WordPress\n", encoding="utf-8")
    icon_file = wp(path, "eval", "$id=(int)get_option('site_icon'); echo $id ? (string) get_attached_file($id) : '';")
    favicon = False
    if icon_file and Path(icon_file).is_file():
        try:
            from PIL import Image
            with Image.open(icon_file) as im:
                im.convert("RGBA").save(out / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
            favicon = True
        except Exception as err:  # noqa: BLE001
            print(f"   aviso: favicon.ico nao gerado ({err})")
    print(f"4. .htaccess da raiz{' + favicon.ico' if favicon else ' (sem Icone do site: favicon.ico nao gerado)'}")

    # 5. wp-config e plugins
    consts = ["define('WP_ENVIRONMENT_TYPE', 'production');", "define('DISALLOW_FILE_EDIT', true);",
              "define('WP_DEBUG', false);", "define('WP_DEBUG_DISPLAY', false);"]
    consts += [f"define('PROJECT_ALLOW_{r.upper()}', true);" for r in allow]
    (out / "wp-config-producao.txt").write_text(
        "/* Acrescente ao wp-config.php da hospedagem (acima de \"That's all, stop editing\").\n"
        "   As chaves abaixo sao NOVAS: substituem as do arquivo (todos os logins saem). */\n\n"
        + "\n".join(consts) + "\n\n" + salts() + "\n", encoding="utf-8")
    plugins = json.loads(wp(path, "plugin", "list", "--status=active", "--fields=name,title,version", "--format=json"))
    plugin_lines = "\n".join(f"- {p['title']} ({p['name']} {p['version']})" for p in plugins) or "- nenhum"

    readme = f"""# Publicacao - {domain}

Pacote gerado em {stamp} a partir de {old}. O site local nao foi alterado.

## Na hospedagem

1. Crie o banco de dados e o usuario do banco no painel da hospedagem.
2. Instale o WordPress (mesma versao ou mais nova) e, no `wp-config.php`,
   acrescente o conteudo de `wp-config-producao.txt`.
3. Importe `banco-producao.sql` no banco novo (phpMyAdmin ou
   `wp db import banco-producao.sql`). Prefixo das tabelas: o mesmo do local.
4. Envie `wp-content.zip` e descompacte na raiz do site (cria/atualiza
   `wp-content/themes`, `wp-content/mu-plugins` e `wp-content/uploads`).
5. Envie `.htaccess` e `favicon.ico` para a RAIZ (a pasta do `wp-config.php`).
   Em servidor nginx, replique as regras do bloco "Project hardening".
6. Instale e ative os plugins (ACF PRO com a licenca do cliente):
{plugin_lines}
7. Configure o SMTP (ex.: WP Mail SMTP) com a conta de e-mail do dominio.
   O mu-plugin de e-mail local nao foi incluido de proposito.
8. Ative o HTTPS (certificado da hospedagem) antes de divulgar o endereco.
9. Configuracoes > Links permanentes > Salvar (regrava as regras).

## Depois de publicar (conferir no endereco final)

- `python scripts/prelaunch_check.py --path <servidor ou copia> --stage production`
- `python scripts/check_security.py --url {domain}/ --no-login-probe`
- `python scripts/capture_site.py --base {domain} --blueprint BLUEPRINT.yaml --out documentation/qa/producao`
- Envie um formulario de teste e confira a chegada na caixa do cliente.
- Google Search Console: cadastre o dominio e envie `{domain}/wp-sitemap.xml`.
"""
    (out / "LEIA-ME-PUBLICACAO.md").write_text(readme, encoding="utf-8")
    print(f"5. wp-config-producao.txt (chaves novas) e LEIA-ME-PUBLICACAO.md ({len(plugins)} plugin(s) listados)")
    print(f"\nPacote pronto em {out}")


if __name__ == "__main__":
    main()
