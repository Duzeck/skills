"""
Monta o comando do WP-CLI usando o MESMO PHP que o Apache do WAMP usa.

Por que: o `wp.bat` chama o `php` do PATH, que pode ser outra versão. Se um
plugin exigir PHP mais novo (ex.: Contact Form 7 6.2+ exige 8.3) e o PATH
apontar para 8.2, o WP-CLI derruba com "erro crítico" mesmo com o site
funcionando no navegador (Apache em 8.3). Descoberto em 2026-11-12.

Ordem de resolução:
  1. variável de ambiente WP_CLI_PHP (caminho do php.exe) - força uma versão;
  2. PHP do Apache do WAMP (LoadModule php_module ... em httpd.conf);
  3. `wp` do PATH, sem alteração.
O wp-cli.phar é procurado ao lado do `wp`/`wp.bat` do PATH.
"""
import os
import re
import shutil
from pathlib import Path

WAMP_DIR = Path(os.environ.get("WAMP_DIR", r"C:\wamp64"))


def apache_php():
    """php.exe correspondente ao php_module carregado pelo Apache do WAMP."""
    for conf in sorted(WAMP_DIR.glob("bin/apache/*/conf/httpd.conf"), reverse=True):
        try:
            text = conf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        m = re.search(r'^\s*LoadModule\s+php\w*_module\s+"?[^"\n]*?/bin/php/(php[\d.]+)/', text, re.M)
        if m:
            exe = WAMP_DIR / "bin" / "php" / m.group(1) / "php.exe"
            if exe.exists():
                return str(exe)
    return None


def wp_phar():
    wp = shutil.which("wp")
    if wp:
        phar = Path(wp).with_name("wp-cli.phar")
        if phar.exists():
            return str(phar)
    return None


def wp_command():
    """Lista inicial do comando, ex.: ['C:/wamp64/.../php.exe', '.../wp-cli.phar'] ou ['wp']."""
    php = os.environ.get("WP_CLI_PHP") or apache_php()
    phar = wp_phar()
    if php and phar:
        return [php, phar]
    resolved = shutil.which("wp")
    return [resolved] if resolved else ["wp"]


def resolve(cmd):
    """Troca um comando que começa com 'wp' pelo comando completo; resolve .bat/.cmd do resto."""
    if cmd and cmd[0] == "wp":
        return wp_command() + list(cmd[1:])
    resolved = shutil.which(cmd[0]) if cmd else None
    return ([resolved] + list(cmd[1:])) if resolved else list(cmd)
