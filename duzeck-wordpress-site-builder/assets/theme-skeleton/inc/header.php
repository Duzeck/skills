<?php
/**
 * Header (references/header-menu.md). A ESTRUTURA vem do Blueprint
 * (header.*) e fica aqui no codigo; o CONTEUDO (rotulo/destino do botao,
 * logo, contatos da barra superior, itens do menu) vem do admin.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * layout:      logo_left | logo_center (logo em cima, menu embaixo) |
 *              logo_center_split (menu dividido dos dois lados do logo)
 * cta:         botao de destaque (header_cta_label / header_cta_target no admin)
 * top_bar:     itens da barra superior: phone | whatsapp | email | hours | social | text
 * actions:     search | account (cart exige WooCommerce; language, plugin de idiomas)
 * transparent: header sobre o hero da Home; ganha fundo ao rolar (precisa de sticky
 *              para o estado rolado) e usa o logo claro (company_logo_light)
 * submenus:    none | dropdown (submenu acessivel, assets/js/main.js)
 */
function project_header_config() {
    return array_merge([
        'layout' => 'logo_left',
        'cta' => false,
        'top_bar' => [],
        'actions' => [],
        'transparent' => false,
        'submenus' => 'dropdown',
    ], (array) apply_filters('project_header_config', []));
}

/* Menu dividido: um local de cada lado do logo (no celular, os dois juntos). */
add_action('after_setup_theme', function () {
    if (project_header_config()['layout'] === 'logo_center_split') {
        register_nav_menus([
            'primary_left' => __('Menu principal - esquerda do logo', 'project-theme'),
            'primary_right' => __('Menu principal - direita do logo', 'project-theme'),
        ]);
    }
}, 20);

/** Header transparente so onde ha hero por baixo (Home). */
function project_header_is_transparent() {
    return project_header_config()['transparent'] && is_front_page();
}

/**
 * Logo: imagem da Midia com width/height (sem salto de layout), alt = nome
 * da empresa, link para a Home. Header transparente: versao clara
 * (company_logo_light) enquanto esta sobre o hero.
 */
function project_site_logo() {
    $name = project_option('company_name') ?: get_bloginfo('name');
    $logo = project_image_id(project_option('company_logo') ?: project_option('logo'));
    $light = project_header_is_transparent() ? project_image_id(project_option('company_logo_light')) : 0;
    $out = sprintf('<a class="site-logo" href="%s" rel="home">', esc_url(home_url('/')));
    if ($logo) {
        $out .= wp_get_attachment_image($logo, 'medium', false, [
            // eager (esta no topo), SEM fetchpriority high: o LCP e o hero, nao o logo.
            'alt' => $name, 'class' => 'site-logo__img site-logo__img--default', 'loading' => 'eager',
        ]);
        if ($light) {
            $out .= wp_get_attachment_image($light, 'medium', false, [
                'alt' => $name, 'class' => 'site-logo__img site-logo__img--light', 'loading' => 'eager',
            ]);
        }
    } else {
        $out .= sprintf('<span class="site-logo__text">%s</span>', esc_html($name));   // sem arquivo: o nome
    }
    return $out . '</a>';
}
