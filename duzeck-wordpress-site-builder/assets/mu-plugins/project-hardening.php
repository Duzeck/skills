<?php
/**
 * Plugin Name: Project Hardening
 * Description: Protecao basica do WordPress (references/security-seo.md). Fica em mu-plugins: vale mesmo se o tema for trocado e nao pode ser desativado pelo painel.
 *
 * O que faz (cada item fecha uma porta que ferramentas de ataque testam
 * primeiro - wpscan, enumeracao de usuarios, forca bruta):
 *   1. XML-RPC desligado (forca bruta em massa via system.multicall, pingback).
 *   2. Logins nao vazam: ?author=N, /author/<login>/, /wp-json/wp/v2/users
 *      para visitantes, autor no oEmbed, usuarios no sitemap.
 *   3. Erro de login generico (nao diz se o usuario existe).
 *   4. Versao do WordPress fora do HTML e dos feeds.
 *   5. Editor de arquivos do painel bloqueado (DISALLOW_FILE_EDIT).
 *   6. Cabecalhos de seguranca (nosniff, referrer, anti-iframe de terceiros).
 *
 * Excecoes (decididas no Blueprint, security.exceptions, com motivo):
 * constantes no wp-config.php, gravadas pelo scaffold (--security-exception):
 *   PROJECT_ALLOW_XMLRPC          app/Jetpack que exige XML-RPC
 *   PROJECT_ALLOW_AUTHOR_ARCHIVES  blog com pagina por autor
 *   PROJECT_ALLOW_REST_USERS       integracao que le usuarios sem login
 *   PROJECT_ALLOW_FRAME_EMBEDDING  site exibido dentro de outro dominio
 *
 * Servidor (Apache): o scaffold grava no .htaccess o bloco "Project
 * hardening" (listagem de pastas desligada; readme.html, license.txt,
 * xmlrpc.php e wp-config.php negados). Em nginx, replicar na configuracao.
 */

if (!defined('ABSPATH')) {
    exit;
}

function project_hardening_allows($rule) {
    $const = 'PROJECT_ALLOW_' . strtoupper($rule);
    return defined($const) && constant($const);
}

/* 5. Editor de temas/plugins do painel: quem invade uma conta de admin nao
   consegue gravar PHP pelo navegador. Atualizacoes continuam funcionando. */
if (!defined('DISALLOW_FILE_EDIT')) {
    define('DISALLOW_FILE_EDIT', true);
}

/* 1. XML-RPC ------------------------------------------------------------ */
if (!project_hardening_allows('xmlrpc')) {
    // xmlrpc.php define XMLRPC_REQUEST antes de carregar o WordPress: corta
    // aqui, antes de qualquer autenticacao (nem chega a testar senha).
    if (defined('XMLRPC_REQUEST') && XMLRPC_REQUEST) {
        status_header(403);
        header('Content-Type: text/plain; charset=utf-8');
        exit('XML-RPC desativado neste site.');
    }
    add_filter('xmlrpc_enabled', '__return_false');
    add_filter('xmlrpc_methods', '__return_empty_array');
    add_filter('pings_open', '__return_false', 99);
    add_filter('wp_headers', function ($headers) {
        unset($headers['X-Pingback']);
        return $headers;
    });
    remove_action('wp_head', 'rsd_link');
}

/* 2. Enumeracao de usuarios --------------------------------------------- */
if (!project_hardening_allows('author_archives')) {
    // ?author=1 redireciona para /author/<login>/ e entrega o login. Antes
    // do redirect_canonical (prioridade 10): vira 404.
    add_action('template_redirect', function () {
        if (current_user_can('list_users')) {
            return;
        }
        if (is_author() || isset($_GET['author']) || get_query_var('author_name')) {
            global $wp_query;
            remove_action('template_redirect', 'redirect_canonical');
            $wp_query->set_404();
            status_header(404);
            nocache_headers();
        }
    }, 1);
    add_filter('author_link', function ($link) {
        return current_user_can('list_users') ? $link : home_url('/');
    });
}

if (!project_hardening_allows('rest_users')) {
    // O editor de blocos (logado) continua listando autores normalmente.
    add_filter('rest_endpoints', function ($endpoints) {
        if (is_user_logged_in()) {
            return $endpoints;
        }
        foreach (array_keys($endpoints) as $route) {
            if (strpos($route, '/wp/v2/users') === 0) {
                unset($endpoints[$route]);
            }
        }
        return $endpoints;
    });
}

add_filter('oembed_response_data', function ($data) {
    unset($data['author_name'], $data['author_url']);
    return $data;
});

add_filter('wp_sitemaps_add_provider', function ($provider, $name) {
    return $name === 'users' ? false : $provider;
}, 10, 2);

/* 3. Erro de login generico: "usuario nao registrado" x "senha incorreta"
   diz ao atacante quais logins existem. */
add_filter('authenticate', function ($user) {
    if (is_wp_error($user)) {
        $leaky = ['invalid_username', 'invalid_email', 'incorrect_password'];
        if (array_intersect($leaky, $user->get_error_codes())) {
            return new WP_Error('project_login_failed', sprintf(
                '<strong>%s</strong> %s',
                esc_html__('Erro:', 'project-theme'),
                esc_html__('usuário ou senha incorretos.', 'project-theme')
            ));
        }
    }
    return $user;
}, 99);

/* 4. Versao do WordPress fora do HTML/feeds (wpscan comeca por ela). */
remove_action('wp_head', 'wp_generator');
add_filter('the_generator', '__return_empty_string');

/* 6. Cabecalhos de seguranca ------------------------------------------- */
function project_security_headers() {
    if (headers_sent()) {
        return;
    }
    header('X-Content-Type-Options: nosniff');
    header('Referrer-Policy: strict-origin-when-cross-origin');
    header('Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()');
    if (!project_hardening_allows('frame_embedding')) {
        // Clickjacking: so o proprio site pode exibir as paginas num iframe
        // (o preview do Personalizar continua funcionando).
        header('X-Frame-Options: SAMEORIGIN');
        header("Content-Security-Policy: frame-ancestors 'self'");
    }
    // HSTS so em producao com HTTPS - em localhost/homologacao "prenderia"
    // o navegador em https por um ano.
    if (is_ssl() && function_exists('wp_get_environment_type') && wp_get_environment_type() === 'production') {
        header('Strict-Transport-Security: max-age=31536000');
    }
}
add_action('send_headers', 'project_security_headers');
add_action('login_init', 'project_security_headers');
add_action('admin_init', 'project_security_headers');
