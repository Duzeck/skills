<?php
/**
 * Editor de blocos com a cara do site (references/editor.md).
 *
 * theme.json (gerado por scripts/generate_design_tokens.py --theme-json):
 * paleta, fontes, tamanhos e espacos da marca; sem cores/tamanhos livres
 * nem as paletas padrao do WordPress - quem edita um post so escolhe o que
 * existe no site. So "settings": o visual do front-end continua no style.css.
 *
 * Aqui: o conteudo DENTRO do editor usa as mesmas fontes e cores do site
 * (editor-styles carregam fonts.css + tokens.css + editor.css no iframe).
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('after_setup_theme', function () {
    add_theme_support('editor-styles');
    $styles = [];
    foreach (['assets/css/fonts.css', 'assets/css/tokens.css', 'assets/css/editor.css'] as $file) {
        if (is_readable(PROJECT_THEME_DIR . '/' . $file)) {
            $styles[] = $file;
        }
    }
    add_editor_style($styles);
});
