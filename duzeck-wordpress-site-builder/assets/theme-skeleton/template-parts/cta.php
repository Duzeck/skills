<?php
/**
 * Faixa de chamada (references/hero-banners.md): "Pronto para comecar?
 * [Fale conosco]". Reutilizavel - o conteudo padrao fica na pagina de
 * opcoes (cta_title, cta_text, cta_primary_label/_target,
 * cta_secondary_label/_target, cta_background); uma pagina pode
 * sobrescrever passando $args. Sem titulo e sem botao valido, nao aparece
 * (nada de "Fale conosco" fixo nem destino "#").
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => 'cta',
    'title' => project_option('cta_title'),
    'text' => project_option('cta_text'),
    'image' => project_option('cta_background'),
    'overlay' => 0.55,
    'buttons' => [
        ['label' => project_option('cta_primary_label'), 'target' => project_option('cta_primary_target')],
        ['label' => project_option('cta_secondary_label'), 'target' => project_option('cta_secondary_target'), 'style' => 'secondary'],
    ],
    'heading_level' => 2,
], $args ?? []);

$buttons = project_buttons_html((array) $a['buttons'], 'cta-band__actions');
if (!trim((string) $a['title']) && !$buttons) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="cta-missing">%s</p>', esc_html__('Faixa de chamada sem conteúdo: preencha em Configurações do Site.', 'project-theme'));
    }
    return;
}
$image_id = project_image_id($a['image']);
$tag = 'h' . min(6, max(2, (int) $a['heading_level']));
?>
<section class="cta-band<?php echo $image_id ? ' cta-band--image' : ''; ?>" data-cta-band="<?php echo esc_attr($a['id']); ?>"
    style="--overlay: <?php echo esc_attr(max(0, min(1, (float) $a['overlay']))); ?>;">
    <?php if ($image_id) : ?>
        <div class="cta-band__media">
            <?php echo wp_get_attachment_image($image_id, 'full', false, ['alt' => '', 'loading' => 'lazy', 'sizes' => '100vw', 'class' => 'cta-band__img']); ?>
            <span class="hero__overlay" aria-hidden="true"></span>
        </div>
    <?php endif; ?>
    <div class="cta-band__content">
        <?php if ($a['title']) : ?>
            <<?php echo $tag; ?> class="cta-band__title" data-contrast><?php echo project_lines($a['title']); ?></<?php echo $tag; ?>>
        <?php endif; ?>
        <?php if ($a['text']) : ?>
            <p class="cta-band__text" data-contrast><?php echo project_lines($a['text']); ?></p>
        <?php endif; ?>
        <?php echo $buttons; ?>
    </div>
</section>
