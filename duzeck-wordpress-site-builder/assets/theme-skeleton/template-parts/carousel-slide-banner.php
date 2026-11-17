<?php
/**
 * Exemplo de slide (banner rotativo do topo). Renomeie os subcampos para os
 * do Blueprint (repeater home_banner_slides em editable_content).
 *
 * $args: item (linha do repeater), index (0 = primeiro), count.
 * O PRIMEIRO slide e o LCP da pagina: imagem eager + fetchpriority high e,
 * se for o titulo principal da pagina, <h1>; os demais ficam lazy e <h2>.
 */
if (!defined('ABSPATH')) { exit; }

$item = (array) ($args['item'] ?? []);
$index = (int) ($args['index'] ?? 0);
$first = $index === 0;
$heading = $first ? 'h1' : 'h2';
$title = $item['home_banner_slide_title'] ?? '';
$text = $item['home_banner_slide_text'] ?? '';
$cta_label = $item['home_banner_slide_cta_label'] ?? '';
$cta_target = $item['home_banner_slide_cta_target'] ?? '';
?>
<div class="banner-slide">
    <?php
    project_media(project_image_id($item['home_banner_slide_image'] ?? 0), [
        'ratio' => '16 / 6',
        'fallback' => is_string($item['home_banner_slide_image'] ?? null) ? $item['home_banner_slide_image'] : '',
        'alt' => '',
        'label' => sprintf('Banner %d', $index + 1),
        'class' => 'banner-slide__media',
        'size' => 'full',
        'loading' => $first ? 'eager' : 'lazy',
    ]);
    ?>
    <div class="banner-slide__content">
        <?php if ($title) : ?>
            <<?php echo $heading; ?> class="banner-slide__title"><?php echo project_lines($title); ?></<?php echo $heading; ?>>
        <?php endif; ?>
        <?php if ($text) : ?>
            <p class="banner-slide__text"><?php echo project_lines($text); ?></p>
        <?php endif; ?>
        <?php if ($cta_label) : ?>
            <a class="banner-slide__cta" href="<?php echo esc_url(project_target_url($cta_target)); ?>"><?php echo esc_html($cta_label); ?></a>
        <?php endif; ?>
    </div>
</div>
