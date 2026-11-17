<?php
/**
 * Fontes do site (references/fonts.md). Gerado por scripts/fetch_fonts.py:
 *   assets/css/fonts.css       @font-face (woff2 do proprio site, swap) +
 *                              reserva com metricas ajustadas
 *   assets/fonts/manifest.json arquivos a pre-carregar (no maximo 2: os do
 *                              titulo/hero, acima da dobra)
 *
 * As fontes saem do PROPRIO dominio: o navegador do visitante nao conecta
 * no Google (LGPD: o IP nao sai do site; e uma conexao a menos). Excecao
 * aprovada google_cdn: o manifesto traz a URL do Google e o preconnect.
 */

if (!defined('ABSPATH')) {
    exit;
}

function project_fonts_manifest() {
    static $manifest = null;
    if ($manifest === null) {
        $file = PROJECT_THEME_DIR . '/assets/fonts/manifest.json';
        $manifest = is_readable($file) ? (json_decode((string) file_get_contents($file), true) ?: []) : [];
    }
    return $manifest;
}

/* Prioridade 5: fonts.css entra antes de tokens.css/style.css. */
add_action('wp_enqueue_scripts', function () {
    $m = project_fonts_manifest();
    $delivery = $m['delivery'] ?? '';
    if ($delivery === 'self_hosted' && is_readable(PROJECT_THEME_DIR . '/assets/css/fonts.css')) {
        wp_enqueue_style('project-theme-fonts', PROJECT_THEME_URI . '/assets/css/fonts.css', [], PROJECT_THEME_VERSION);
    } elseif ($delivery === 'google_cdn' && !empty($m['css_url'])) {
        wp_enqueue_style('project-theme-fonts', esc_url_raw($m['css_url']), [], null);
    }
}, 5);

/* Pre-carrega so os arquivos do titulo/hero: a fonte chega junto com o
   HTML, nao depois do CSS. crossorigin e obrigatorio para fonte (sem ele o
   arquivo e baixado duas vezes). */
add_filter('wp_preload_resources', function ($resources) {
    $m = project_fonts_manifest();
    if (($m['delivery'] ?? '') !== 'self_hosted') {
        return $resources;
    }
    foreach (array_slice((array) ($m['preload'] ?? []), 0, 2) as $file) {
        $resources[] = [
            'href' => PROJECT_THEME_URI . '/assets/fonts/' . rawurlencode(basename((string) $file)),
            'as' => 'font',
            'type' => 'font/woff2',
            'crossorigin' => 'anonymous',
        ];
    }
    return $resources;
});

add_filter('wp_resource_hints', function ($urls, $relation) {
    if ($relation === 'preconnect' && (project_fonts_manifest()['delivery'] ?? '') === 'google_cdn') {
        $urls[] = ['href' => 'https://fonts.gstatic.com', 'crossorigin'];
    }
    return $urls;
}, 10, 2);
