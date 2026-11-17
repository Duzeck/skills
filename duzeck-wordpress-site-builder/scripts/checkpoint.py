#!/usr/bin/env python3
"""
Ponto de restauracao do projeto: commit git do tema + documentacao + dump
do banco. Permite desfazer um ciclo de correcao ruim sem reconstruir nada.

Quando criar (ver SKILL.md):
    - logo apos o scaffold                     --label scaffold
    - apos a aprovacao do Blueprint aplicada   --label blueprint-v0.N
    - antes de semear conteudo demo            --label pre-seed
    - ao fechar a fatia critica                --label fatia-critica
    - ao fim de cada rodada de correcao        --label qa-rodada-N

Uso:
    python checkpoint.py --project-dir "C:\\wamp64\\www\\<slug>" --label fatia-critica
    python checkpoint.py --project-dir ... --label x --no-db   (so codigo)
    python checkpoint.py --project-dir ... --list               (historico)

Na primeira execucao cria o repositorio git no projeto com um .gitignore
que versiona APENAS: documentation/, db/ e wp-content/themes/ (exceto os
temas padrao twenty*). Core do WordPress, plugins e uploads ficam fora -
uploads podem ser grandes e plugins sao reinstalaveis.

O banco vai para db/database.sql (sempre o mesmo arquivo, sobrescrito):
o git guarda cada versao. Requer MySQL/MariaDB do WAMP ligado e wp-cli.

Restaurar NAO e automatico: e destrutivo (sobrescreve tema e banco). Este
script so imprime os comandos; peca confirmacao ao usuario antes de rodar.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402


# Console do Windows usa cp1252 por padrao e corrompe acentos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GITIGNORE = """# Gerado por duzeck-wordpress-site-builder/scripts/checkpoint.py
# Versiona so o que o projeto produz: tema, documentacao e dump do banco.
/*
!/.gitignore
!/documentation/
!/db/
!/wp-content/
/wp-content/*
!/wp-content/themes/
/wp-content/themes/twenty*/
"""


def run(cmd, cwd, check=False):
    # wp -> WP-CLI com o mesmo PHP do Apache (ver _wpcli.py); demais: resolve .bat/.cmd.
    cmd = _wpcli.resolve(cmd)
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if check and result.returncode != 0:
        print(f"Falhou: {' '.join(cmd)}\n{result.stderr.strip() or result.stdout.strip()}")
        sys.exit(1)
    return result


def ensure_repo(project):
    if (project / ".git").exists():
        return False
    run(["git", "init", "-q"], project, check=True)
    (project / ".gitignore").write_text(GITIGNORE, encoding="utf-8", newline="\n")
    print("Repositorio git criado no projeto (.gitignore versiona tema, documentation/ e db/).")
    return True


def export_db(project):
    if not (project / "wp-config.php").exists():
        return "wp-config.php ausente - projeto sem WordPress instalado ainda"
    (project / "db").mkdir(exist_ok=True)
    result = run(["wp", "db", "export", "db/database.sql", "--add-drop-table", "--quiet"], project)
    if result.returncode != 0:
        lines = (result.stderr.strip() or result.stdout.strip()).splitlines()
        return lines[-1] if lines else "erro desconhecido"
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--label", help="nome curto do ponto (ex.: fatia-critica, qa-rodada-2)")
    ap.add_argument("--no-db", action="store_true", help="nao exportar o banco")
    ap.add_argument("--list", action="store_true", help="listar pontos existentes")
    args = ap.parse_args()

    project = Path(args.project_dir)
    if not project.is_dir():
        print(f"Diretorio nao encontrado: {project}")
        sys.exit(1)
    if not shutil.which("git"):
        print("git nao encontrado no PATH.")
        sys.exit(2)

    if args.list:
        if not (project / ".git").exists():
            print("Nenhum ponto de restauracao ainda (projeto sem repositorio git).")
            sys.exit(0)
        print(run(["git", "log", "--date=format:%Y-%m-%d %H:%M", "--pretty=%h  %ad  %s"], project).stdout)
        sys.exit(0)

    if not args.label or not re.fullmatch(r"[\w.-]+", args.label):
        ap.error("--label obrigatorio, so letras, numeros, ponto, hifen e underscore")

    ensure_repo(project)

    db_note = "banco nao exportado (--no-db)"
    db_ok = False
    if not args.no_db:
        failure = export_db(project)
        if failure:
            db_note = f"BANCO NAO EXPORTADO: {failure} - o ponto cobre so o codigo"
            hint = "" if "wp-config" in failure else " O MySQL do WAMP esta ligado?"
            print(f"Aviso: {db_note}.{hint}")
        else:
            db_ok = True
            db_note = "banco exportado em db/database.sql"

    run(["git", "add", "-A"], project, check=True)
    if not run(["git", "status", "--porcelain"], project).stdout.strip():
        print(f"Nada mudou desde o ultimo ponto - nenhum commit criado ({db_note}).")
        sys.exit(0)
    message = f"checkpoint: {args.label}\n\n{db_note}"
    run(["git", "commit", "-q", "-m", message], project, check=True)
    commit = run(["git", "rev-parse", "--short", "HEAD"], project).stdout.strip()

    print(f"Ponto de restauracao '{args.label}' criado: {commit} ({db_note}).")
    print("\nPara restaurar (DESTRUTIVO - confirme com o usuario antes):")
    paths = "wp-content/themes documentation" + (" db" if db_ok else "")
    print(f'  git -C "{project}" checkout {commit} -- {paths}')
    if db_ok:
        print(f'  cd "{project}" && wp db import db/database.sql')


if __name__ == "__main__":
    main()
