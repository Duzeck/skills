<?php
/**
 * Rodape (references/footer-social.md). A ESTRUTURA (quais colunas, em
 * que ordem) vem do Blueprint (footer.columns) e fica aqui no codigo; o
 * CONTEUDO (titulos, textos, links, contatos) vem do admin.
 *
 * Tipos de coluna: about (logo + texto), menu (um local de menu proprio
 * por coluna), contact (endereco, telefone, WhatsApp, e-mail, horario),
 * social, newsletter (formulario CF7), hours, custom (texto livre).
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Colunas na ordem da referencia: [id => tipo] ou [id => ['kind' => tipo,
 * 'social' => true]] quando os icones das redes ficam DENTRO da coluna
 * (ex.: abaixo do texto "sobre"), como em muitas referencias.
 * Ajuste por projeto (footer.columns do Blueprint).
 */
function project_footer_columns() {
    $columns = apply_filters('project_footer_columns', [
        'about' => ['kind' => 'about', 'social' => true],
        'links' => 'menu',
        'contact' => 'contact',
    ]);
    $normalized = [];
    foreach ($columns as $id => $col) {
        $col = is_array($col) ? $col : ['kind' => $col];
        $normalized[$id] = array_merge(['kind' => 'custom', 'social' => false], $col);
    }
    return $normalized;
}

/* Um local de menu por coluna de menu ("Links rápidos", "Serviços"...). */
add_action('after_setup_theme', function () {
    $locations = [];
    foreach (project_footer_columns() as $id => $col) {
        if ($col['kind'] === 'menu') {
            /* translators: %s: id da coluna */
            $locations['footer_' . $id] = sprintf(__('Rodapé - coluna %s', 'project-theme'), $id);
        }
    }
    if ($locations) {
        register_nav_menus($locations);
    }
}, 20);

/** Titulo da coluna (admin: footer_<id>_title). */
function project_footer_column_title($id) {
    return trim((string) project_option('footer_' . $id . '_title'));
}

/**
 * Copyright do admin com marcadores: {ano} (ano atual no fuso do site -
 * wp_date, nao date(), que e UTC e viraria o ano as 21h de 31/12) e
 * {empresa} (razao social ou nome do site).
 */
function project_footer_copyright() {
    $text = (string) project_option('footer_copyright');
    if ($text === '') {
        $text = '© {ano} {empresa}';
    }
    $company = project_option('company_legal_name') ?: get_bloginfo('name');
    return strtr($text, ['{ano}' => wp_date('Y'), '{empresa}' => $company]);
}

/** Links legais: Politica de privacidade (pagina do nucleo, LGPD) + termos (admin). */
function project_footer_legal_links() {
    $links = [];
    $privacy = get_privacy_policy_url();   // so retorna se a pagina estiver publicada
    if ($privacy) {
        $links[] = [get_the_title((int) get_option('wp_page_for_privacy_policy')) ?: __('Política de privacidade', 'project-theme'), $privacy];
    }
    $terms = trim((string) project_option('footer_terms_url'));
    if ($terms) {
        $links[] = [project_option('footer_terms_label') ?: __('Termos de uso', 'project-theme'), project_target_url($terms)];
    }
    return $links;
}
