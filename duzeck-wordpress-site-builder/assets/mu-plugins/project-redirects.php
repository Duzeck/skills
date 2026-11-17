<?php
/**
 * Plugin Name: Project Redirects
 * Description: Redirecionamentos 301 dos enderecos do site antigo (references/redirects.md).
 *
 * Fontes, nesta ordem (a segunda completa/sobrepoe a primeira):
 *   1. wp-content/project-redirects.json - gerado por scripts/build_redirects.py
 *      a partir do Blueprint (redirects.map aprovado);
 *   2. Configuracoes do Site > Redirecionamentos - o administrador acrescenta
 *      um por linha: "/endereco-antigo/ /endereco-novo/".
 *
 * So age quando o endereco daria 404: uma pagina nova no mesmo caminho
 * sempre vence. Destino: caminho do site ou ID de pagina; dominio externo
 * so se liberado em allowed_redirect_hosts (wp_safe_redirect).
 * Fica em mu-plugins: vale mesmo se o tema for trocado.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** /Servicos/Index.html, /servicos.php, /servicos/ -> /servicos */
function project_redirect_key($path) {
    $path = strtolower(rawurldecode((string) (parse_url((string) $path, PHP_URL_PATH) ?: '/')));
    $path = preg_replace('#/index\.(html?|php|aspx?)$#', '/', $path);
    $path = preg_replace('#\.(html?|php|aspx?)$#', '', $path);
    return '/' . trim($path, '/');
}

function project_redirects_map() {
    static $map = null;
    if ($map !== null) {
        return $map;
    }
    $map = [];
    $file = WP_CONTENT_DIR . '/project-redirects.json';
    if (is_readable($file)) {
        $data = json_decode((string) file_get_contents($file), true);
        foreach ((array) ($data['map'] ?? []) as $row) {
            if (!empty($row['from']) && isset($row['to']) && $row['to'] !== '') {
                $map[project_redirect_key($row['from'])] = (string) $row['to'];
            }
        }
    }
    foreach (preg_split('/\R/', (string) get_option('options_redirects_extra', '')) as $line) {
        $parts = preg_split('/\s+/', trim($line));
        if (count($parts) >= 2 && strpos($parts[0], '/') === 0) {
            $map[project_redirect_key($parts[0])] = $parts[1];
        }
    }
    return $map;
}

add_action('template_redirect', function () {
    if (!is_404()) {
        return;
    }
    $map = project_redirects_map();
    if (!$map) {
        return;
    }
    $request = (string) parse_url((string) ($_SERVER['REQUEST_URI'] ?? '/'), PHP_URL_PATH);
    $base = rtrim((string) parse_url(home_url('/'), PHP_URL_PATH), '/');   // instalacao em subpasta
    if ($base !== '' && stripos($request, $base . '/') === 0) {
        $request = substr($request, strlen($base));
    }
    $key = project_redirect_key($request);
    if (!isset($map[$key])) {
        return;
    }
    $to = $map[$key];
    if (ctype_digit($to)) {
        $to = (string) get_permalink((int) $to);
    } elseif (strpos($to, '/') === 0) {
        $to = home_url($to);
    }
    // Loop so se o destino for EXATAMENTE o endereco pedido (/servicos.php ->
    // /servicos/ e legitimo, apesar de normalizarem igual).
    $target_path = substr((string) parse_url((string) $to, PHP_URL_PATH), strlen($base));
    if ($to === '' || strtolower(trim($target_path, '/')) === strtolower(trim($request, '/'))) {
        return;
    }
    wp_safe_redirect($to, 301, 'Project Redirects');
    exit;
}, 1);   // antes do redirect_canonical (que "adivinha" e pode errar)

/* Lista editavel no painel (Configuracoes do Site, ACF PRO). */
add_action('acf/init', function () {
    if (!function_exists('acf_add_local_field_group') || !function_exists('acf_add_options_page')) {
        return;
    }
    acf_add_local_field_group([
        'key' => 'group_project_redirects',
        'title' => 'Redirecionamentos (site antigo)',
        'menu_order' => 95,
        'fields' => [[
            'key' => 'field_project_redirects_extra',
            'name' => 'redirects_extra',
            'label' => 'Endereços antigos',
            'type' => 'textarea',
            'rows' => 6,
            'new_lines' => '',
            'instructions' => 'Um por linha: endereço antigo, espaço, endereço novo. Ex.: /quem-somos/ /sobre/. '
                . 'Só funciona se o endereço antigo não existir mais no site.',
        ]],
        'location' => [[['param' => 'options_page', 'operator' => '==', 'value' => 'global-settings']]],
    ]);
});
