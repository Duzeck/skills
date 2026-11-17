<?php
/**
 * Cabecalho de pagina interna (references/hero-banners.md): faixa menor
 * com trilha de navegacao, titulo (h1) e texto - todos do admin
 * (page_hero_title / page_hero_text / page_hero_image da pagina).
 * $args: title, text, image, breadcrumb (bool), overlay.
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'title' => project_page_field('page_hero_title'),
    'text' => project_page_field('page_hero_text'),
    'image' => project_page_field('page_hero_image'),
    'breadcrumb' => true,
    'overlay' => 0.5,
], $args ?? []);

$image_id = project_image_id($a['image']);
?>
<header class="page-header<?php echo $image_id ? ' page-header--image' : ''; ?>" data-page-header
    style="--overlay: <?php echo esc_attr(max(0, min(1, (float) $a['overlay']))); ?>;">
    <?php if ($image_id) : ?>
        <div class="page-header__media">
            <?php echo wp_get_attachment_image($image_id, 'full', false, ['alt' => '', 'loading' => 'eager', 'fetchpriority' => 'high', 'sizes' => '100vw', 'class' => 'page-header__img']); ?>
            <span class="hero__overlay" aria-hidden="true"></span>
        </div>
    <?php endif; ?>
    <div class="page-header__content">
        <?php if ($a['breadcrumb']) : ?>
            <?php echo project_breadcrumb(); // escapado em inc/hero.php ?>
        <?php endif; ?>
        <h1 class="page-header__title" data-contrast><?php echo esc_html($a['title'] ?: get_the_title()); ?></h1>
        <?php if ($a['text']) : ?>
            <p class="page-header__text" data-contrast><?php echo project_lines($a['text']); ?></p>
        <?php endif; ?>
    </div>
</header>
