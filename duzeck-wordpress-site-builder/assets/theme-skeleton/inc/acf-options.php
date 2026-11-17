<?php
/**
 * Páginas de opções (ACF PRO) e helpers de leitura do conteúdo editável.
 *
 * REGRA (SKILL.md -> "Tudo que aparece é editável no admin"): nenhum template
 * tem texto/imagem de conteúdo fixo. Cada parte visível lê de um destes:
 *   project_option($name)      -> Configurações do Site (dados globais, CTA, rodapé, cabeçalhos de arquivos)
 *   project_home($name)        -> campos da página inicial (seções da Home)
 *   project_page_field($name)  -> campos da página atual (cabeçalho da página)
 *   CPT / taxonomia / menu / formulário -> para conteúdo repetitivo e navegação
 * Todos caem em inc/content-defaults.php se o campo estiver vazio (o layout
 * nunca quebra), e a migração do projeto preenche os campos a partir dele.
 * O mapa "onde editar" fica em BLUEPRINT.yaml -> editable_content.
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('acf/init', function () {
    if (!function_exists('acf_add_options_page')) {
        return;
    }
    acf_add_options_page([
        'page_title' => 'Configurações do Site',
        'menu_title' => 'Configurações do Site',
        'menu_slug' => 'global-settings',
        'capability' => 'edit_theme_options',
        'icon_url' => 'dashicons-admin-site-alt3',
        'position' => 59,
        'redirect' => false,
    ]);
    // Arquivos de CPT (ex.: /servicos/) não são páginas: o cabeçalho deles vai numa subpágina.
    // acf_add_options_sub_page(['page_title' => 'Cabeçalhos dos arquivos', 'menu_slug' => 'archive-settings', 'parent_slug' => 'global-settings']);
});

function project_is_empty($value) {
    return $value === null || $value === '' || $value === false || $value === [];
}

/** Campo da página de opções, com reserva no conteúdo padrão. */
function project_option($name) {
    $value = function_exists('get_field') ? get_field($name, 'option') : null;
    if (project_is_empty($value)) {
        // Valor gravado sem a referencia do ACF (migracao via wp-cli/script,
        // ACF sem pagina de opcoes): o ACF devolve vazio, mas o dado existe
        // em options_<campo> - mesmo caso do get_post_meta em project_field().
        $value = get_option('options_' . $name, null);
    }
    return project_is_empty($value) ? project_default($name) : $value;
}

/** Campo da página inicial estática, com reserva no conteúdo padrão. */
function project_home($name) {
    $front = (int) get_option('page_on_front');
    $value = ($front && function_exists('get_field')) ? get_field($name, $front) : null;
    return project_is_empty($value) ? project_default($name) : $value;
}

/** Campo da página atual; reserva em page_<slug>_<campo sem "page_">. */
function project_page_field($name, $post = null) {
    $post = get_post($post);
    $value = ($post && function_exists('get_field')) ? get_field($name, $post->ID) : null;
    if (!project_is_empty($value)) {
        return $value;
    }
    if ($name === 'page_hero_title' && $post) {
        return get_the_title($post);
    }
    return $post ? project_default('page_' . $post->post_name . '_' . substr($name, 5)) : '';
}

/** URL de imagem vinda de campo (ID) ou do conteúdo padrão (arquivo em assets/img/). */
function project_image_url($value, $size = 'full') {
    if (is_array($value)) {
        $value = $value['ID'] ?? $value['id'] ?? 0;
    }
    if (is_numeric($value) && (int) $value > 0) {
        $url = wp_get_attachment_image_url((int) $value, $size);
        if ($url) {
            return $url;
        }
    }
    return is_string($value) && $value !== '' && !is_numeric($value)
        ? get_template_directory_uri() . '/assets/img/' . $value
        : '';
}

function project_image_id($value) {
    if (is_array($value)) {
        $value = $value['ID'] ?? $value['id'] ?? 0;
    }
    return is_numeric($value) ? (int) $value : 0;
}

/**
 * Destino de campo page_link/post_object, URL ou slug padrão (respeita subdiretório).
 * Destinos especiais (botões "Falar no WhatsApp", "Ligar", "Enviar e-mail"),
 * montados do dado ÚNICO da página de opções: whatsapp | telefone | email.
 */
function project_target_url($value) {
    if ($value instanceof WP_Post) {
        return get_permalink($value);
    }
    if (is_string($value) && function_exists('project_whatsapp_href')) {
        $special = [
            'whatsapp' => function () { return project_whatsapp_href(project_option('company_whatsapp'), project_option('company_whatsapp_message')); },
            'telefone' => function () { return project_phone_href(project_option('company_phone')); },
            'email' => function () { return project_email_href(project_option('company_email')); },
        ];
        if (isset($special[strtolower(trim($value))])) {
            return $special[strtolower(trim($value))]() ?: '';
        }
    }
    if (is_numeric($value) && (int) $value > 0) {
        return get_permalink((int) $value);
    }
    if (is_string($value) && preg_match('#^(https?:)?//|^\#|^mailto:|^tel:#', $value)) {
        return $value;
    }
    return is_string($value) && $value !== '' ? home_url('/' . trim($value, '/') . '/') : home_url('/');
}

/** Texto multilinha do admin -> HTML com <br> (escapado). Quebras de título vêm do admin. */
function project_lines($text) {
    return nl2br(esc_html(trim((string) $text)), false);
}

/** Compatibilidade: leitura de dado global. */
function project_get_global_setting($field_key, $default = '') {
    $value = project_option($field_key);
    return project_is_empty($value) ? $default : $value;
}
