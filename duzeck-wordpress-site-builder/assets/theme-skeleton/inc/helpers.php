<?php
/**
 * Helpers do tema.
 *
 * project_field($name): leitura de campo com fallback.
 * get_field() do ACF so retorna valor quando o ACF PRO esta ativo E o
 * campo foi preenchido atraves do ACF (que grava uma meta de referencia
 * "_<nome>" apontando para a field key). Conteudo demo semeado via
 * scripts/seed_demo_content.py (que usa `wp post meta update`, gravando
 * so a meta bruta) NAO e lido por get_field() - ele retorna vazio.
 * Este helper cai para get_post_meta() bruto nesse caso.
 * NAO cobre repeater/gallery/relationship.
 *
 * project_media(...): renderiza SEMPRE o espaco de uma imagem da
 * referencia (SKILL.md -> "Nada some"), nesta ordem de preferencia:
 *   1. anexo real (ID do WordPress, ex.: thumbnail ou campo ACF de imagem);
 *   2. recorte provisorio da referencia em assets/img/ (media.treatment =
 *      crop_from_reference, gerado por scripts/crop_reference.py);
 *   3. placeholder com a MESMA proporcao e um rotulo do que falta.
 * Nunca use `if (has_post_thumbnail())` para decidir se o bloco aparece.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Single page (uma pagina com secoes ancoradas) x multipaginas.
 * Ver PROJECT_SITE_STRUCTURE em functions.php e references/navigation.md.
 */
function project_is_single_page() {
    return defined('PROJECT_SITE_STRUCTURE') && PROJECT_SITE_STRUCTURE === 'single_page';
}

/**
 * Header acompanha a rolagem? Em single page, sempre (regra da skill);
 * em multipaginas, so quando o Blueprint diz theme.header_behavior: sticky.
 */
function project_header_is_sticky() {
    return project_is_single_page()
        || (defined('PROJECT_HEADER_BEHAVIOR') && PROJECT_HEADER_BEHAVIOR === 'sticky');
}

/**
 * Atributo id da secao, a partir de pages[].sections[].anchor do Blueprint.
 * Uso no template-part: <section class="hero"<?php project_section_anchor($args['anchor'] ?? ''); ?>>
 * O front-page.php passa a ancora: get_template_part('template-parts/hero', null, ['anchor' => 'inicio']).
 * A ancora e estrutural (o rotulo do menu e que e editavel, em Aparencia > Menus).
 */
function project_section_anchor($anchor) {
    $anchor = sanitize_title((string) $anchor);
    if ($anchor !== '') {
        printf(' id="%s"', esc_attr($anchor));
    }
}

function project_field($name, $post_id = null) {
    $post_id = $post_id ?: get_the_ID();

    if (function_exists('get_field')) {
        $value = get_field($name, $post_id);
        if ($value !== null && $value !== '' && $value !== false) {
            return $value;
        }
    }

    return get_post_meta($post_id, $name, true);
}

/**
 * @param int|null $attachment_id Anexo real (0/null se nao houver).
 * @param array    $args {
 *     @type string $ratio    Proporcao CSS, ex.: '3 / 2' (de media[].aspect_ratio).
 *     @type string $fallback Arquivo em assets/img/ (recorte da referencia).
 *     @type string $alt      Texto alternativo.
 *     @type string $label    Rotulo do placeholder (o que deve entrar ali).
 *     @type string $class    Classes extras da moldura.
 *     @type string $size     Tamanho do WordPress (padrao 'large').
 *     @type string $fit      cover | contain.
 *     @type string $loading  lazy (padrao) | eager - eager + fetchpriority high so para a
 *                            imagem LCP (hero, PRIMEIRO slide de banner rotativo).
 * }
 */
function project_media($attachment_id, array $args = []) {
    $args = array_merge([
        'ratio' => '16 / 9',
        'fallback' => '',
        'alt' => '',
        'label' => 'Imagem',
        'class' => '',
        'size' => 'large',
        'fit' => 'cover',
        'loading' => 'lazy',
    ], $args);
    $eager = $args['loading'] === 'eager';

    $style = sprintf('--ratio: %s; --fit: %s;', esc_attr($args['ratio']), esc_attr($args['fit']));
    $class = trim('media-frame ' . $args['class']);

    if ($attachment_id) {
        $attr = ['alt' => $args['alt'], 'loading' => $eager ? 'eager' : 'lazy'];
        if ($eager) {
            $attr['fetchpriority'] = 'high';
        }
        $img = wp_get_attachment_image((int) $attachment_id, $args['size'], false, $attr);
        if ($img) {
            printf('<figure class="%s" style="%s">%s</figure>', esc_attr($class), $style, $img);
            return;
        }
    }

    if ($args['fallback']) {
        $path = get_template_directory() . '/assets/img/' . $args['fallback'];
        if (file_exists($path)) {
            printf(
                '<figure class="%s" style="%s"><img src="%s" alt="%s" %s data-provisional="crop_from_reference"></figure>',
                esc_attr($class),
                $style,
                esc_url(get_template_directory_uri() . '/assets/img/' . $args['fallback']),
                esc_attr($args['alt']),
                $eager ? 'loading="eager" fetchpriority="high"' : 'loading="lazy"'
            );
            return;
        }
    }

    printf(
        '<figure class="%s media-frame--placeholder" style="%s" role="img" aria-label="%s"><span>%s</span></figure>',
        esc_attr($class),
        $style,
        esc_attr($args['alt'] ?: $args['label']),
        esc_html($args['label'])
    );
}
