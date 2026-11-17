<?php
/**
 * Icone do site e sinais basicos do <head> (references/site-icon.md).
 *
 * O icone em si e o do WordPress (Aparencia > Personalizar > Identidade do
 * site > Icone do site): o core ja imprime favicon 32px, 192px e o
 * apple-touch-icon 180px, e o administrador troca quando quiser.
 * scripts/make_site_icon.py prepara a imagem a partir do simbolo do logo.
 *
 * Aqui:
 *  - theme-color: cor da barra do navegador no celular = cor de fundo da
 *    paleta do theme.json (filtro project_theme_color para outra);
 *  - manifesto (site.webmanifest) com nome e icones, gerado do proprio site
 *    (sem arquivo para manter) - so quando ha Icone do site.
 * O favicon.ico fisico na raiz sai do go_live.py (alguns servidores nginx
 * nunca passam /favicon.ico para o WordPress).
 */

if (!defined('ABSPATH')) {
    exit;
}

function project_theme_color() {
    $color = '';
    if (function_exists('wp_get_global_settings')) {
        foreach ((array) wp_get_global_settings(['color', 'palette', 'theme']) as $entry) {
            if (($entry['slug'] ?? '') === 'background') {
                $color = (string) $entry['color'];
            }
        }
    }
    $color = (string) apply_filters('project_theme_color', $color);
    return preg_match('/^#[0-9a-f]{3,8}$/i', $color) ? $color : '';
}

add_action('wp_head', function () {
    $color = project_theme_color();
    if ($color) {
        printf("<meta name=\"theme-color\" content=\"%s\">\n", esc_attr($color));
    }
    if (has_site_icon()) {
        printf("<link rel=\"manifest\" href=\"%s\">\n", esc_url(add_query_arg('project_manifest', '1', home_url('/'))));
    }
}, 3);

/* /?project_manifest=1 -> manifesto JSON (sem regra de reescrita para regravar). */
add_action('template_redirect', function () {
    if (empty($_GET['project_manifest'])) {
        return;
    }
    $icons = [];
    foreach ([192, 512] as $size) {
        $url = get_site_icon_url($size);
        if ($url) {
            $icons[] = ['src' => $url, 'sizes' => "{$size}x{$size}", 'type' => 'image/png', 'purpose' => 'any'];
        }
    }
    $name = wp_strip_all_tags(get_bloginfo('name'));
    // Nome curto (icone na tela do celular): palavras inteiras ate 12 letras.
    $short = '';
    foreach (preg_split('/\s+/', $name) as $word) {
        if (mb_strlen(trim($short . ' ' . $word)) > 12) {
            break;
        }
        $short = trim($short . ' ' . $word);
    }
    $short = $short !== '' ? $short : mb_substr($name, 0, 12);
    $color = project_theme_color() ?: '#ffffff';
    nocache_headers();
    header('Content-Type: application/manifest+json; charset=utf-8');
    echo wp_json_encode([
        'name' => $name,
        'short_name' => $short,
        'start_url' => home_url('/'),
        'display' => 'browser',
        'lang' => get_bloginfo('language'),
        'background_color' => $color,
        'theme_color' => $color,
        'icons' => $icons,
    ], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}, 0);
