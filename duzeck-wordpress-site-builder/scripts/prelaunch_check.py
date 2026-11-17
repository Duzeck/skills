#!/usr/bin/env python3
"""
Lista UNICA do que conferir antes de publicar (references/go-live.md).

Junta os "antes de publicar" espalhados pelos guias (conteudo de exemplo,
redes, envio de e-mail, privacidade, usuarios, imagens provisorias,
pendencias do Blueprint, icone do site, redirecionamentos...) e confere
de verdade no WordPress (WP-CLI) e no Blueprint.

Uso:
    python prelaunch_check.py --path C:/wamp64/www/meu-site --blueprint BLUEPRINT.yaml \
        [--stage local|production] [--out documentation/qa/pre-publicacao.md]

  --stage local       (padrao) o site ainda no WAMP: aponta o que falta
                      para poder publicar.
  --stage production  rodando no servidor (ou na copia de producao):
                      exige ambiente production, HTTPS, nada de localhost,
                      envio real de e-mail.

Saida: 0 sem P0/P1, 1 com P0/P1. P0 = publicar assim quebra algo visivel;
P1 = tem de ser resolvido antes; P2 = recomendacao.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SMTP_PLUGINS = ("wp-mail-smtp", "fluent-smtp", "post-smtp", "easy-wp-smtp", "smtp-mailer", "gosmtp", "suremails")
FAKE_EMAIL = re.compile(r"@(localhost|example\.(com|org)|test\b|[\w.-]+\.test\b|[\w.-]+\.local\b)", re.I)

PHP = r"""
global $wpdb;
$privacy = (int) get_option('wp_page_for_privacy_policy');
$admins = get_users(['role' => 'administrator', 'fields' => ['user_login', 'user_email']]);
$forms = [];
foreach (get_posts(['post_type' => 'wpcf7_contact_form', 'numberposts' => -1, 'post_status' => 'any']) as $f) {
    $mail = get_post_meta($f->ID, '_mail', true);
    $forms[] = ['title' => $f->post_title, 'recipient' => is_array($mail) ? ($mail['recipient'] ?? '') : ''];
}
// Endereco local (http://localhost ou a forma escapada dos blocos) - nao o
// e-mail admin@localhost.test, que tem item proprio.
$like = '%' . $wpdb->esc_like('://localhost') . '%';
$like_esc = '%' . $wpdb->esc_like(':\\/\\/localhost') . '%';
$updates_plugins = get_site_transient('update_plugins');
$updates_core = get_site_transient('update_core');
$opt = function ($n) { return function_exists('project_option') ? project_option($n) : get_option('options_' . $n); };
$social = [];
foreach (['instagram', 'facebook', 'linkedin', 'youtube', 'tiktok', 'x', 'pinterest', 'threads', 'whatsapp', 'telegram', 'spotify'] as $net) {
    $social[$net] = (string) $opt('social_' . $net);
}
echo wp_json_encode([
    'siteurl' => get_option('siteurl'),
    'home' => get_option('home'),
    'blog_public' => (string) get_option('blog_public'),
    'admin_email' => get_option('admin_email'),
    'env' => function_exists('wp_get_environment_type') ? wp_get_environment_type() : 'production',
    'wp_debug' => defined('WP_DEBUG') && WP_DEBUG,
    'debug_display' => defined('WP_DEBUG') && WP_DEBUG && (!defined('WP_DEBUG_DISPLAY') || WP_DEBUG_DISPLAY),
    'privacy' => ['id' => $privacy, 'status' => $privacy ? get_post_status($privacy) : null],
    'site_icon' => (int) get_option('site_icon'),
    'permalink' => get_option('permalink_structure'),
    'admins' => array_map(function ($u) { return ['login' => $u->user_login, 'email' => $u->user_email]; }, $admins),
    'mu_plugins' => array_keys(get_mu_plugins()),
    'active_plugins' => array_values((array) get_option('active_plugins')),
    'demo_posts' => (int) $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->postmeta} m JOIN {$wpdb->posts} p ON p.ID = m.post_id WHERE m.meta_key = '_project_demo' AND p.post_status = 'publish'"),
    'forms' => $forms,
    'localhost_refs' => [
        'posts' => (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_content LIKE %s OR post_content LIKE %s OR guid LIKE %s", $like, $like_esc, $like)),
        'postmeta' => (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE meta_value LIKE %s OR meta_value LIKE %s", $like, $like_esc)),
        'options' => (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM {$wpdb->options} WHERE (option_value LIKE %s OR option_value LIKE %s) AND option_name NOT LIKE '%%transient%%'", $like, $like_esc)),
    ],
    'updates' => [
        'plugins' => is_object($updates_plugins) && !empty($updates_plugins->response) ? array_keys($updates_plugins->response) : [],
        'core' => is_object($updates_core) && !empty($updates_core->updates) && ($updates_core->updates[0]->response ?? '') === 'upgrade',
    ],
    'social' => $social,
    'redirects_file' => is_readable(WP_CONTENT_DIR . '/project-redirects.json'),
]);
"""


def wp_state(path):
    with tempfile.NamedTemporaryFile("w", suffix=".php", delete=False, encoding="utf-8") as tmp:
        tmp.write("<?php\n" + PHP)
    try:
        r = subprocess.run(_wpcli.resolve(["wp", "eval-file", tmp.name]), cwd=path, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
    finally:
        Path(tmp.name).unlink(missing_ok=True)
    if r.returncode != 0:
        sys.exit(f"BLOQUEADO: WP-CLI falhou em {path}: {(r.stderr or r.stdout).strip()[:300]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", required=True, help="pasta do WordPress")
    ap.add_argument("--blueprint", help="BLUEPRINT.yaml (pendencias, conteudo demo, imagens provisorias)")
    ap.add_argument("--stage", choices=["local", "production"], default="local")
    ap.add_argument("--out", help="grava o relatorio em Markdown")
    args = ap.parse_args()

    s = wp_state(args.path)
    raw = yaml.safe_load(Path(args.blueprint).read_text(encoding="utf-8")) if args.blueprint else {}
    bp = (raw or {}).get("blueprint", raw or {})
    prod = args.stage == "production"
    items = []   # (nivel, assunto, detalhe)

    def add(level, subject, detail):
        items.append((level, subject, detail))

    # --- Visibilidade e ambiente
    if s["blog_public"] == "0":
        add("P0", "Site escondido dos buscadores", "Configurações > Leitura > 'Evitar que mecanismos de busca indexem' está marcado.")
    if prod:
        if s["env"] != "production":
            add("P0", "Ambiente", f"WP_ENVIRONMENT_TYPE = {s['env']} - em produção deve ser 'production' (o conteúdo de exemplo só some assim).")
        if not s["home"].startswith("https://"):
            add("P1", "HTTPS", f"Endereço do site {s['home']} sem https.")
        refs = s["localhost_refs"]
        if s["siteurl"].find("localhost") >= 0 or any(refs.values()):
            add("P0", "Endereços locais", f"'localhost' ainda aparece (site: {s['siteurl']}; posts {refs['posts']}, metadados {refs['postmeta']}, opções {refs['options']}) - "
                "importe o banco gerado por go_live.py.")
        if "project-local-mail.php" in s["mu_plugins"]:
            add("P0", "Envio de e-mail", "mu-plugin project-local-mail.php no servidor: os formulários gravam o e-mail num arquivo e NÃO enviam.")
    if s["debug_display"]:
        add("P0" if prod else "P2", "Erros na tela", "WP_DEBUG ligado com exibição: avisos do PHP aparecem para o visitante.")

    # --- E-mail e formularios
    smtp = [p for p in s["active_plugins"] if p.split("/")[0] in SMTP_PLUGINS]
    if not smtp:
        add("P1", "Envio de e-mail (SMTP)", "Nenhum plugin de SMTP ativo. Sem SMTP autenticado, as mensagens dos formulários caem no spam "
            "ou nem saem (references/forms.md). Instale e configure na hospedagem (ex.: WP Mail SMTP).")
    for f in s["forms"]:
        if not f["recipient"] or FAKE_EMAIL.search(f["recipient"]):
            add("P1", "Destino do formulário", f"'{f['title']}' envia para '{f['recipient'] or '(vazio)'}' - use o e-mail real da empresa.")
    if FAKE_EMAIL.search(s["admin_email"] or ""):
        add("P1", "E-mail do administrador", f"{s['admin_email']} - avisos do WordPress e recuperação de senha não chegam a ninguém.")

    # --- Usuarios
    for a in s["admins"]:
        if a["login"].lower() == "admin":
            add("P1", "Usuário 'admin'", "Crie um usuário pessoal para cada pessoa e apague o 'admin' (primeiro alvo de força bruta).")
        if FAKE_EMAIL.search(a["email"] or ""):
            add("P1", "E-mail de usuário", f"Administrador '{a['login']}' com e-mail {a['email']}.")
    try:
        import check_security
        rep = check_security.Report()
        data = check_security.inside_checks(args.path, rep, set())
        for i in rep.items:
            if not i["ok"] and i["check"] in ("senha dos administradores", "editor de arquivos do painel bloqueado", "mu-plugin project-hardening ativo"):
                add("P1", i["check"].capitalize(), i["detail"])
    except Exception as err:  # noqa: BLE001
        add("P2", "Checagens de segurança", f"não rodaram ({err}) - rode check_security.py.")

    # --- Paginas, links e identidade
    priv = s["privacy"]
    if not priv["id"] or priv["status"] != "publish":
        add("P1", "Política de Privacidade", f"Página {'inexistente' if not priv['id'] else 'em ' + str(priv['status'])} - o link do rodapé (LGPD) não funciona. "
            "Revise o texto e publique.")
    if s["permalink"] != "/%postname%/":
        add("P1", "Links permanentes", f"Estrutura '{s['permalink'] or 'padrão (?p=123)'}' - use /%postname%/.")
    if not s["site_icon"]:
        add("P1", "Ícone do site", "Aparência > Personalizar > Identidade do site > Ícone do site vazio (aba do navegador e atalho no celular).")

    # --- Conteudo
    if s["demo_posts"]:
        add("P1", "Posts de exemplo", f"{s['demo_posts']} post(s) de exemplo publicados - em produção ficam ocultos; escreva os reais ou apague.")
    for key, field in (("testimonials", "content_source"), ("team", "content_source"), ("stats", "content_source")):
        for x in bp.get(key) or []:
            if isinstance(x, dict) and x.get(field) == "demo":
                add("P1", "Conteúdo de exemplo", f"{key}[{x.get('id')}] ainda é demonstração - fica oculto em produção; peça o conteúdo real.")
    for x in bp.get("pricing") or []:
        if isinstance(x, dict) and x.get("price_source") not in (None, "user", "client"):
            add("P1", "Preços", f"pricing[{x.get('id')}]: preços da referência ({x.get('price_source')}) - confirme os valores reais.")
    for m in bp.get("media") or []:
        if isinstance(m, dict) and m.get("replace_before_launch"):
            add("P1", "Imagem provisória", f"{m.get('id')}: {m.get('purpose')} - trocar pela versão definitiva (do cliente ou fotografada).")
    social = (bp.get("social") or {})
    for net in social.get("networks") or []:
        if not s["social"].get(net):
            add("P2", "Redes sociais", f"URL de {net} vazia - o ícone não aparece (Configurações do Site > Redes sociais).")
    for u in bp.get("uncertainties") or []:
        if isinstance(u, dict) and u.get("status") == "pending":
            add("P1", "Pendência do Blueprint", f"{u.get('id')}: {u.get('subject') or u.get('question')}")
    for d in bp.get("decisions") or []:
        if isinstance(d, dict) and d.get("status") == "pending_user_approval":
            add("P1", "Decisão não aprovada", f"{d.get('id')}: {d.get('subject')}")
    seo = bp.get("seo") or {}
    if seo.get("ai_crawlers_source") == "default":
        add("P2", "Robôs de IA", "Política de robôs de IA é o padrão, não uma escolha do cliente.")
    redirects = (bp.get("redirects") or {}) if isinstance(bp.get("redirects"), dict) else {}
    if redirects.get("map") and not s["redirects_file"]:
        add("P1", "Redirecionamentos", "Blueprint tem redirecionamentos do site antigo, mas wp-content/project-redirects.json não existe - rode build_redirects.py.")
    launch = bp.get("launch") or {}
    if not launch.get("domain"):
        add("P1", "Domínio", "launch.domain vazio no Blueprint - qual será o endereço do site?")

    # --- Atualizacoes
    if s["updates"]["core"]:
        add("P2", "Atualização", "Há versão nova do WordPress.")
    if s["updates"]["plugins"]:
        add("P2", "Atualização", f"Plugins com atualização: {', '.join(p.split('/')[0] for p in s['updates']['plugins'])}.")

    order = {"P0": 0, "P1": 1, "P2": 2}
    items.sort(key=lambda i: order[i[0]])
    blocking = [i for i in items if i[0] in ("P0", "P1")]
    lines = [f"# Antes de publicar ({args.stage}) - {s['home']}", "",
             f"{len(blocking)} item(ns) bloqueiam a publicação; {len(items) - len(blocking)} recomendação(ões).", "",
             "| Nível | Assunto | O que fazer |", "|---|---|---|"]
    lines += [f"| {lvl} | {subj} | {det} |" for lvl, subj, det in items] or ["| - | Tudo certo | - |"]
    report = "\n".join(lines) + "\n"
    print(report)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(report, encoding="utf-8")
    sys.exit(1 if blocking else 0)


if __name__ == "__main__":
    main()
