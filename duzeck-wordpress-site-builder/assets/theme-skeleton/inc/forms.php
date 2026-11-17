<?php
/**
 * Formularios (Contact Form 7) - references/forms.md.
 *
 * - Campos, e-mail de destino e mensagens: editados no admin em
 *   Contato > Formularios (o CF7 grava no banco). O formulario inicial e
 *   gerado do Blueprint por scripts/build_cf7_form.py (rotulos e
 *   placeholders literais da referencia).
 * - QUAL formulario aparece em cada secao: campo da pagina de opcoes
 *   (post_object -> wpcf7_contact_form) ou, na falta dele, o slug que o
 *   build_cf7_form.py grava (= forms[].id). Nunca um id fixo no template:
 *   o id muda entre ambientes (local x producao).
 */

if (!defined('ABSPATH')) {
    exit;
}

/* Sem <p>/<br> automaticos do CF7: o template gerado ja traz a marcacao e
   o layout vem da referencia. */
add_filter('wpcf7_autop_or_not', '__return_false');

/* JS/CSS do CF7 so nas paginas que tem formulario (documentado pelo CF7):
   project_form() enfileira quando renderiza. */
add_filter('wpcf7_load_js', '__return_false');
add_filter('wpcf7_load_css', '__return_false');

/**
 * ID do formulario CF7 a partir de um valor do admin: ID, WP_Post ou slug.
 */
function project_form_id($value) {
    if ($value instanceof WP_Post) {
        return (int) $value->ID;
    }
    if (is_numeric($value)) {
        return (int) $value;
    }
    if (is_string($value) && $value !== '') {
        $found = get_posts([
            'post_type' => 'wpcf7_contact_form',
            'name' => sanitize_title($value),
            'post_status' => 'publish',
            'numberposts' => 1,
            'fields' => 'ids',
        ]);
        return $found ? (int) $found[0] : 0;
    }
    return 0;
}

/**
 * Renderiza o formulario escolhido no admin.
 *
 * @param string $option_field Campo da pagina de opcoes (ex.: 'contact_form_select');
 *                             o conteudo padrao (inc/content-defaults.php) traz o
 *                             slug gerado pelo build_cf7_form.py (ex.: 'contact').
 * @param array  $args         html_class, html_id (atributos do <form>).
 */
function project_form($option_field, array $args = []) {
    $id = project_form_id(project_option($option_field));

    if (!$id || !function_exists('wpcf7_contact_form') || !wpcf7_contact_form($id)) {
        if (current_user_can('edit_theme_options')) {
            printf(
                '<p class="form-missing">%s</p>',
                esc_html__('Formulário não encontrado: escolha-o em Configurações do Site ou rode scripts/build_cf7_form.py.', 'project-theme')
            );
        }
        return;
    }

    if (function_exists('wpcf7_enqueue_scripts')) {
        wpcf7_enqueue_scripts();
    }
    if (function_exists('wpcf7_enqueue_styles')) {
        wpcf7_enqueue_styles();
    }

    $attrs = sprintf(' id="%d"', $id);
    foreach (['html_class', 'html_id'] as $key) {
        if (!empty($args[$key])) {
            $attrs .= sprintf(' %s="%s"', $key, esc_attr($args[$key]));
        }
    }
    echo do_shortcode('[contact-form-7' . $attrs . ']');
}
