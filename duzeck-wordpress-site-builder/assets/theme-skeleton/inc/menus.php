<?php
/**
 * Registro de menus. Um register_nav_menu() por menu do BLUEPRINT.yaml.
 */

if (!defined('ABSPATH')) {
    exit;
}

function project_register_menus() {
    register_nav_menus([
        'primary' => 'Menu Principal',
        // Menus do rodape: um local por coluna, registrados em inc/footer.php.
    ]);
}
add_action('after_setup_theme', 'project_register_menus');

/**
 * Itens de ancora (single page). No admin, cada item e um "Link
 * personalizado" com URL RELATIVA "#servicos" - nunca
 * "http://localhost/slug/#servicos", que quebra quando o site muda de
 * dominio (o WordPress nao reescreve URLs de links personalizados).
 *
 * Na Home o "#servicos" rola ate a secao. Fora dela (politica de
 * privacidade, 404, busca) o mesmo item precisa levar de volta a Home:
 * este filtro prefixa a URL da pagina inicial so nesses casos.
 */
function project_menu_anchor_href($atts) {
    $href = isset($atts['href']) ? (string) $atts['href'] : '';
    if (strlen($href) > 1 && $href[0] === '#' && !is_front_page()) {
        $atts['href'] = home_url('/') . $href;
    }
    return $atts;
}
add_filter('nav_menu_link_attributes', 'project_menu_anchor_href');
