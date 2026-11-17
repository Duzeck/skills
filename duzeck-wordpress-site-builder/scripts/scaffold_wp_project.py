#!/usr/bin/env python3
"""
Cria um novo projeto WordPress no WAMP a partir do theme-skeleton desta
Skill. Ver references/local-environment.md para o raciocinio por tras de
cada passo.

Uso:
    python scaffold_wp_project.py --slug construtora-horizonte \
        --title "Construtora Horizonte" \
        --site-structure multi_page|single_page [--header-behavior sticky|static] \
        [--wamp-root "C:\\wamp64\\www"] \
        [--acf-zip <zip>] [--skip-cf7] [--locale pt_BR] \
        [--schema-type GeneralContractor] [--security-exception xmlrpc] \
        [--ai-crawlers allow|block_training|block_all]

Sai protegido (references/security-seo.md): senha forte aleatoria para o
admin (mostrada uma vez no fim), DISALLOW_FILE_EDIT, mu-plugin
project-hardening.php, readme.html/license.txt apagados e o bloco
"Project hardening" no .htaccess.

A pasta do projeto pode ja existir se contiver apenas material de
referencia (pastas com imagens/PDF/MD/YAML, ex.: template/ e
documentation/) - comum quando o usuario cria a pasta e coloca as
referencias antes de chamar a skill. Qualquer outra coisa aborta.

Pre-requisitos: WAMP rodando, wp-cli ('wp') e php no PATH. O script para
e explica o problema em vez de tentar contornar um pre-requisito ausente.

ACF PRO nao esta no WordPress.org (e plugin pago)  -  este script NAO tenta
baixa-lo automaticamente. Se voce tiver o .zip da licenca, instale com:
    wp plugin install <caminho-para-o-zip> --activate
depois de rodar este script, ou passe --acf-zip <caminho>.
"""
import argparse
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402


SKILL_DIR = Path(__file__).resolve().parent.parent
THEME_SKELETON = SKILL_DIR / "assets" / "theme-skeleton"
MU_PLUGINS = SKILL_DIR / "assets" / "mu-plugins"
SITE_STRUCTURES = {"single_page", "multi_page"}
HEADER_BEHAVIORS = {"sticky", "static"}


def set_navigation_constants(functions_php, structure, behavior):
    """Grava project.site_structure e theme.header_behavior no tema
    (PROJECT_SITE_STRUCTURE / PROJECT_HEADER_BEHAVIOR em functions.php)."""
    code = functions_php.read_text(encoding="utf-8")
    for const, value in (("PROJECT_SITE_STRUCTURE", structure),
                         ("PROJECT_HEADER_BEHAVIOR", behavior)):
        code, count = re.subn(rf"define\('{const}', '[a-z_]+'\);",
                              f"define('{const}', '{value}');", code)
        if count != 1:
            print(f"Aviso: {const} nao encontrado em {functions_php} - defina a mao.")
    functions_php.write_text(code, encoding="utf-8")
    print(f"Navegacao: site_structure={structure}, header_behavior={behavior}")


def set_schema_type(functions_php, schema_type):
    """Grava seo.organization_type do Blueprint (PROJECT_SCHEMA_TYPE)."""
    code = functions_php.read_text(encoding="utf-8")
    code, count = re.subn(r"define\('PROJECT_SCHEMA_TYPE', '[A-Za-z]+'\);",
                          f"define('PROJECT_SCHEMA_TYPE', '{schema_type}');", code)
    if count != 1:
        print(f"Aviso: PROJECT_SCHEMA_TYPE nao encontrado em {functions_php} - defina a mao.")
    functions_php.write_text(code, encoding="utf-8")
    print(f"Dados estruturados: @type {schema_type}")


AI_CRAWLER_POLICIES = {"allow", "block_training", "block_all"}


def set_ai_crawlers(functions_php, policy):
    """Grava seo.ai_crawlers do Blueprint (PROJECT_AI_CRAWLERS): valor inicial
    do robots.txt; o admin muda em Configuracoes do Site."""
    code = functions_php.read_text(encoding="utf-8")
    code, count = re.subn(r"define\('PROJECT_AI_CRAWLERS', '[a-z_]+'\);",
                          f"define('PROJECT_AI_CRAWLERS', '{policy}');", code)
    if count != 1:
        print(f"Aviso: PROJECT_AI_CRAWLERS nao encontrado em {functions_php} - defina a mao.")
    functions_php.write_text(code, encoding="utf-8")
    print(f"Robos de IA (robots.txt): {policy}")


# Excecoes da protecao basica (Blueprint security.exceptions) -> constantes
# lidas pelo mu-plugin project-hardening.php.
SECURITY_EXCEPTIONS = {"xmlrpc", "author_archives", "rest_users", "frame_embedding"}

# Arquivos do core que so revelam a versao do WordPress (o wpscan le o
# readme.html primeiro). Voltam em atualizacoes do core: o .htaccess nega.
VERSION_LEAK_FILES = ("readme.html", "license.txt", "wp-config-sample.php")


def hardening_htaccess_block(allow_xmlrpc):
    """Bloco do Apache: sem listagem de pastas (uploads/ nao tem index.php)
    e arquivos sensiveis negados. Precisa de AllowOverride All (padrao do
    WAMP e da maioria das hospedagens)."""
    denied = ["readme\\.html", "license\\.txt", "wp-config\\.php", "wp-config-sample\\.php"]
    if not allow_xmlrpc:
        denied.append("xmlrpc\\.php")
    return (
        "# BEGIN Project hardening\n"
        "Options -Indexes\n"
        f"<FilesMatch \"^({'|'.join(denied)})$\">\n"
        "    Require all denied\n"
        "</FilesMatch>\n"
        "# END Project hardening\n\n"
    )
WORDPRESS_ZIP_URL = "https://wordpress.org/latest.zip"


def download_and_extract_wordpress(project_dir):
    """
    Baixa e extrai o WordPress core diretamente via Python em vez de usar
    'wp core download'. O extrator do WP-CLI (PharData/tar) cria um
    diretorio temporario com nome muito longo antes de mover os arquivos
    para o destino, e isso estoura o limite de caminho do Windows (MAX_PATH)
    por causa de arquivos profundamente aninhados no core do WordPress
    (ex.: wp-includes/php-ai-client/.../*Interface.php). Extrair direto
    para o destino final (caminho curto) evita o problema por completo.
    """
    tmp_zip = Path(tempfile.gettempdir()) / "wp-core-download.zip"
    print(f"Baixando WordPress de {WORDPRESS_ZIP_URL}...")
    urllib.request.urlretrieve(WORDPRESS_ZIP_URL, tmp_zip)

    print(f"Extraindo para {project_dir}...")
    with zipfile.ZipFile(tmp_zip) as z:
        z.extractall(project_dir)

    # O zip contém tudo dentro de uma pasta "wordpress/" - sobe um nivel.
    inner = project_dir / "wordpress"
    for item in inner.iterdir():
        shutil.move(str(item), str(project_dir / item.name))
    inner.rmdir()
    tmp_zip.unlink(missing_ok=True)


def run(cmd, cwd=None, check=True):
    # No Windows, subprocess com shell=False nao resolve .bat/.cmd via PATH
    # (isso so acontece com shell=True/cmd.exe). shutil.which ja faz essa
    # resolucao corretamente (inclusive PATHEXT), entao resolvemos aqui.
    # wp -> WP-CLI com o mesmo PHP do Apache (ver _wpcli.py); demais: resolve .bat/.cmd.
    cmd = _wpcli.resolve(cmd)
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=False)
    if check and result.returncode != 0:
        print(f"Falhou (exit {result.returncode}): {' '.join(cmd)}")
        sys.exit(result.returncode)
    return result


REFERENCE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".md",
                  ".yaml", ".yml", ".txt", ".svg"}


def only_reference_material(project_dir):
    """True se a pasta so contem diretorios com material de referencia."""
    for entry in project_dir.iterdir():
        if not entry.is_dir():
            return False
        for f in entry.rglob("*"):
            if f.is_file() and f.suffix.lower() not in REFERENCE_EXTS:
                return False
    return True


def check_prerequisites():
    for tool in ("wp", "php"):
        if shutil.which(tool) is None:
            print(f"Pre-requisito ausente: '{tool}' nao encontrado no PATH.")
            print("Instale/configure antes de continuar  -  nao tente "
                  "contornar isso copiando arquivos manualmente.")
            sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--wamp-root", default=r"C:\wamp64\www")
    ap.add_argument("--admin-user", default="admin")
    ap.add_argument("--admin-password", default=None,
                    help="padrao: senha forte aleatoria, mostrada no fim (guarde num gerenciador de senhas)")
    ap.add_argument("--admin-email", default="admin@localhost.test")
    ap.add_argument("--acf-zip", default=None,
                     help="Caminho local para o zip do ACF PRO")
    ap.add_argument("--skip-cf7", action="store_true")
    ap.add_argument("--locale", default="pt_BR",
                    help="Idioma do WordPress (padrao pt_BR; 'en_US' mantem o ingles)")
    ap.add_argument("--site-structure", required=True, choices=sorted(SITE_STRUCTURES),
                    help="project.site_structure do Blueprint aprovado")
    ap.add_argument("--header-behavior", choices=sorted(HEADER_BEHAVIORS), default=None,
                    help="theme.header_behavior (padrao: sticky em single_page, static em multi_page)")
    ap.add_argument("--schema-type", default="Organization",
                    help="seo.organization_type do Blueprint (Organization, LocalBusiness ou subtipo, ex.: GeneralContractor)")
    ap.add_argument("--security-exception", action="append", default=[], choices=sorted(SECURITY_EXCEPTIONS),
                    help="security.exceptions[].rule do Blueprint (repetivel; so com motivo aprovado)")
    ap.add_argument("--ai-crawlers", choices=sorted(AI_CRAWLER_POLICIES), default="allow",
                    help="seo.ai_crawlers do Blueprint (robots.txt): allow | block_training | block_all")
    args = ap.parse_args()
    if not re.fullmatch(r"[A-Z][A-Za-z]+", args.schema_type):
        ap.error("--schema-type deve ser um tipo schema.org (ex.: Organization, LocalBusiness, GeneralContractor).")
    generated_password = args.admin_password is None
    if generated_password:
        # admin/admin e a primeira tentativa de qualquer robo de forca bruta -
        # e o banco local costuma ir para a producao.
        args.admin_password = secrets.token_urlsafe(18)
    args.header_behavior = args.header_behavior or (
        "sticky" if args.site_structure == "single_page" else "static")
    if args.site_structure == "single_page" and args.header_behavior != "sticky":
        ap.error("single_page exige header sticky (references/navigation.md).")

    check_prerequisites()

    project_dir = Path(args.wamp_root) / args.slug
    if project_dir.exists() and any(project_dir.iterdir()):
        if not only_reference_material(project_dir):
            print(f"Pasta '{project_dir}' ja existe e nao esta vazia. "
                  "Abortando para nao sobrescrever trabalho existente.")
            sys.exit(1)
        kept = ", ".join(sorted(e.name for e in project_dir.iterdir()))
        print(f"Pasta existente com material de referencia ({kept}) - mantido.")
    project_dir.mkdir(parents=True, exist_ok=True)

    url = f"http://localhost/{args.slug}"
    theme_slug = f"{args.slug}-theme"

    download_and_extract_wordpress(project_dir)
    run(["wp", "config", "create",
         "--dbname=" + args.slug.replace("-", "_"),
         "--dbuser=root", "--dbpass=", "--dbhost=localhost"],
        cwd=str(project_dir))
    run(["wp", "db", "create"], cwd=str(project_dir), check=False)
    run(["wp", "core", "install",
         "--url=" + url,
         "--title=" + args.title,
         "--admin_user=" + args.admin_user,
         "--admin_password=" + args.admin_password,
         "--admin_email=" + args.admin_email],
        cwd=str(project_dir))

    if args.locale and args.locale != "en_US":
        run(["wp", "language", "core", "install", args.locale, "--activate"],
            cwd=str(project_dir), check=False)
        run(["wp", "option", "update", "timezone_string", "America/Sao_Paulo"],
            cwd=str(project_dir), check=False)
        if args.locale == "pt_BR":
            # O core instala em ingles e so depois troca o idioma: o formato de
            # data continuaria "F j, Y" ("novembro 1, 2026"). Padrao brasileiro:
            run(["wp", "option", "update", "date_format", r"j \d\e F \d\e Y"], cwd=str(project_dir), check=False)
            run(["wp", "option", "update", "time_format", "H:i"], cwd=str(project_dir), check=False)
            # A pagina de privacidade nasce em ingles ("Privacy Policy"): o link
            # do rodape (LGPD) sairia em ingles. Rascunho - o cliente revisa o texto.
            privacy_id = subprocess.run(_wpcli.resolve(["wp", "option", "get", "wp_page_for_privacy_policy"]),
                                        cwd=str(project_dir), capture_output=True, text=True).stdout.strip()
            if privacy_id.isdigit() and privacy_id != "0":
                run(["wp", "post", "update", privacy_id, "--post_title=Política de Privacidade",
                     "--post_name=politica-de-privacidade"], cwd=str(project_dir), check=False)

    # Conteudo de exemplo do WordPress ("Olá, mundo!", "Página de exemplo",
    # comentario padrao) apareceria no blog e no sitemap: remove.
    # Comentario antes dos posts: apagar o post ja leva o comentario junto.
    run(["wp", "comment", "delete", "1", "--force"], cwd=str(project_dir), check=False)
    for post_type, slugs in (("post", "hello-world,ola-mundo"), ("page", "sample-page,pagina-exemplo")):
        found = subprocess.run(_wpcli.resolve(["wp", "post", "list", f"--post_type={post_type}", f"--post_name__in={slugs}",
                                               "--field=ID", "--format=ids"]),
                               cwd=str(project_dir), capture_output=True, text=True).stdout.split()
        if found:
            run(["wp", "post", "delete", *found, "--force"], cwd=str(project_dir), check=False)

    theme_dest = project_dir / "wp-content" / "themes" / theme_slug
    if THEME_SKELETON.exists():
        shutil.copytree(THEME_SKELETON, theme_dest,
                        ignore=shutil.ignore_patterns("__pycache__"))
        print(f"Theme skeleton copiado para {theme_dest}")
        set_navigation_constants(theme_dest / "functions.php",
                                 args.site_structure, args.header_behavior)
        set_schema_type(theme_dest / "functions.php", args.schema_type)
        set_ai_crawlers(theme_dest / "functions.php", args.ai_crawlers)
    else:
        print(f"Aviso: {THEME_SKELETON} nao encontrado  -  crie o tema "
              "manualmente em {theme_dest}.")

    run(["wp", "theme", "activate", theme_slug], cwd=str(project_dir))

    if args.acf_zip:
        run(["wp", "plugin", "install", args.acf_zip, "--activate"],
            cwd=str(project_dir))
    else:
        print("Nenhum --acf-zip informado. Instale o ACF PRO manualmente:")
        print(f'  cd "{project_dir}" && wp plugin install '
              '<caminho-do-zip-acf-pro> --activate')

    if not args.skip_cf7:
        run(["wp", "plugin", "install", "contact-form-7", "--activate"],
            cwd=str(project_dir), check=False)
        # Antes de criar formularios (build_cf7_form.py), senao as mensagens
        # do CF7 ficam gravadas em ingles.
        if args.locale and args.locale != "en_US":
            run(["wp", "language", "plugin", "install", "contact-form-7", args.locale],
                cwd=str(project_dir), check=False)

    # Ambiente local: liga o log de e-mail (mu-plugin) - o WAMP nao envia
    # e-mail; o QA confere o envio dos formularios pelo log.
    run(["wp", "config", "set", "WP_ENVIRONMENT_TYPE", "local", "--type=constant"],
        cwd=str(project_dir), check=False)
    # Protecao basica (references/security-seo.md): editor de arquivos do
    # painel bloqueado (o mu-plugin tambem define, caso o wp-config mude) e
    # excecoes aprovadas no Blueprint.
    run(["wp", "config", "set", "DISALLOW_FILE_EDIT", "true", "--raw", "--type=constant"],
        cwd=str(project_dir), check=False)
    for rule in sorted(set(args.security_exception)):
        run(["wp", "config", "set", f"PROJECT_ALLOW_{rule.upper()}", "true", "--raw", "--type=constant"],
            cwd=str(project_dir), check=False)
    for leak in VERSION_LEAK_FILES:
        (project_dir / leak).unlink(missing_ok=True)
    mu_dir = project_dir / "wp-content" / "mu-plugins"
    mu_dir.mkdir(parents=True, exist_ok=True)
    for mu in MU_PLUGINS.glob("*.php"):
        shutil.copy2(mu, mu_dir / mu.name)
        print(f"mu-plugin copiado: {mu.name}")

    run(["wp", "rewrite", "structure", "/%postname%/"], cwd=str(project_dir))
    run(["wp", "rewrite", "flush"], cwd=str(project_dir))

    htaccess = project_dir / ".htaccess"
    if not htaccess.exists():
        # 'wp rewrite flush' normalmente nao escreve o .htaccess em
        # contexto CLI (sem SERVER_SOFTWARE). Sem ele, qualquer URL que
        # nao seja a home retorna 404. Escrevemos o bloco padrao do
        # WordPress manualmente.
        htaccess.write_text(
            "# BEGIN WordPress\n"
            "<IfModule mod_rewrite.c>\n"
            "RewriteEngine On\n"
            "RewriteRule .* - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]\n"
            f"RewriteBase /{args.slug}/\n"
            "RewriteRule ^index\\.php$ - [L]\n"
            "RewriteCond %{REQUEST_FILENAME} !-f\n"
            "RewriteCond %{REQUEST_FILENAME} !-d\n"
            f"RewriteRule . /{args.slug}/index.php [L]\n"
            "</IfModule>\n"
            "# END WordPress\n",
            encoding="utf-8",
        )
        print(f"'.htaccess' nao foi gerado por 'wp rewrite flush' - criado manualmente em {htaccess}")

    # Bloco de protecao ANTES do bloco do WordPress (o core so reescreve o
    # trecho entre BEGIN/END WordPress).
    code = htaccess.read_text(encoding="utf-8")
    if "# BEGIN Project hardening" not in code:
        htaccess.write_text(hardening_htaccess_block("xmlrpc" in args.security_exception) + code, encoding="utf-8")
        print("'.htaccess': bloco Project hardening gravado (sem listagem de pastas, arquivos sensiveis negados).")

    print(f"\nProjeto criado em {project_dir}")
    print(f"URL local: {url}/")
    print(f"Admin: {url}/wp-admin/ (usuario: {args.admin_user})")
    if generated_password:
        print(f"Senha do admin (gerada agora, NAO fica salva em lugar nenhum): {args.admin_password}")
        print("  Guarde num gerenciador de senhas. Na producao, cada pessoa usa o proprio usuario.")
    print(f"Conferir a protecao: python scripts/check_security.py --url {url}/ --path \"{project_dir}\"")


if __name__ == "__main__":
    main()
