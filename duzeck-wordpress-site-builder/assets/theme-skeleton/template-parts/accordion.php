<?php
/**
 * Acordeao / FAQ (references/disclosures.md) - um por accordions[] do Blueprint.
 *
 * <details>/<summary> nativos: abre e fecha sem JS, teclado e leitor de
 * tela funcionam por padrao, e o Ctrl+F do navegador acha (e abre) texto
 * de item fechado. exclusive = true usa o atributo name (um aberto por
 * vez, nativo); o disclosure.js cobre navegador sem suporte e o link
 * direto (#<id-do-item>).
 *
 * Uso:
 *   get_template_part('template-parts/accordion', null, [
 *       'id'            => 'home_faq',                              // accordions[].id
 *       'items'         => project_disclosure_items(project_home('home_faq_items'), 'home_faq_question', 'home_faq_answer'),
 *       'exclusive'     => true,          // accordions[].exclusive
 *       'open'          => [1],           // accordions[].open_in_reference (1 = primeiro)
 *       'heading_level' => 3,             // nivel do titulo de cada item na hierarquia da pagina
 *       'faq'           => true,          // pergunta/resposta
 *       'schema'        => true,          // JSON-LD FAQPage (so com faq)
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'items' => [],
    'exclusive' => false,
    'open' => [],
    'heading_level' => 3,
    'faq' => false,
    'schema' => true,
    'class' => '',
], $args ?? []);

$items = array_values((array) $a['items']);
if (!$items) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="accordion-missing">%s</p>', esc_html__('Lista sem itens: preencha no admin.', 'project-theme'));
    }
    return;
}

$level = min(6, max(2, (int) $a['heading_level']));
$open = array_map('intval', (array) $a['open']);
if ($a['exclusive']) {
    $open = array_slice($open, 0, 1);
}
if ($a['faq'] && $a['schema']) {
    project_faq_schema_add($items);
}
wp_enqueue_script('project-disclosure');
?>
<div class="<?php echo esc_attr(trim('accordion' . ($a['faq'] ? ' accordion--faq' : '') . ' ' . $a['class'])); ?>"
    data-accordion="<?php echo esc_attr($a['id']); ?>"<?php echo $a['exclusive'] ? ' data-exclusive' : ''; ?>>
    <?php foreach ($items as $i => $item) : ?>
        <details class="accordion__item" id="<?php echo esc_attr(project_disclosure_anchor($a['id'], $item['title'], $i)); ?>"
            <?php echo $a['exclusive'] ? 'name="' . esc_attr($a['id']) . '"' : ''; ?>
            <?php echo in_array($i + 1, $open, true) ? 'open' : ''; ?>>
            <summary class="accordion__summary">
                <<?php echo 'h' . $level; ?> class="accordion__title"><?php echo esc_html($item['title']); ?></<?php echo 'h' . $level; ?>>
                <span class="accordion__icon" aria-hidden="true"></span>
            </summary>
            <div class="accordion__panel">
                <?php echo wp_kses_post(wpautop($item['content'])); ?>
            </div>
        </details>
    <?php endforeach; ?>
</div>
