<?php
if (!defined('ABSPATH')) {
    exit;
}

function project_theme_assets() {
    // tokens.css e gerado por scripts/generate_design_tokens.py a partir do
    // Blueprint e precisa carregar antes de style.css (que so usa var(--...)).
    // Fontes web: inc/fonts.php (fonts.css gerado por scripts/fetch_fonts.py,
    // arquivos no proprio site). Nunca link direto para fonts.googleapis.com.
    wp_enqueue_style(
        'project-theme-tokens',
        PROJECT_THEME_URI . '/assets/css/tokens.css',
        [],
        PROJECT_THEME_VERSION
    );
    wp_enqueue_style(
        'project-theme-style',
        PROJECT_THEME_URI . '/assets/css/style.css',
        ['project-theme-tokens'],
        PROJECT_THEME_VERSION
    );
    // Carrossel (template-parts/carousel.php): so REGISTRADO aqui. O
    // template-part enfileira quando a pagina tem carrossel - paginas sem
    // carrossel nao baixam o arquivo.
    wp_register_script(
        'project-carousel',
        PROJECT_THEME_URI . '/assets/js/carousel.js',
        [],
        PROJECT_THEME_VERSION,
        ['in_footer' => true, 'strategy' => 'defer']
    );
    // Galeria (lightbox), video (fachada/fundo), abas/acordeao, seletor de planos, faixa de logos e contagem de numeros: idem, so registrados.
    foreach (['gallery', 'video', 'disclosure', 'pricing', 'client-logos', 'stats'] as $handle) {
        wp_register_script(
            'project-' . $handle,
            PROJECT_THEME_URI . '/assets/js/' . $handle . '.js',
            [],
            PROJECT_THEME_VERSION,
            ['in_footer' => true, 'strategy' => 'defer']
        );
    }
    // Mapa com fachada (template-parts/map.php): idem, so registrado.
    wp_register_script(
        'project-map',
        PROJECT_THEME_URI . '/assets/js/map.js',
        [],
        PROJECT_THEME_VERSION,
        ['in_footer' => true, 'strategy' => 'defer']
    );
    wp_enqueue_script(
        'project-theme-main',
        PROJECT_THEME_URI . '/assets/js/main.js',
        [],
        PROJECT_THEME_VERSION,
        true
    );
}
add_action('wp_enqueue_scripts', 'project_theme_assets');
