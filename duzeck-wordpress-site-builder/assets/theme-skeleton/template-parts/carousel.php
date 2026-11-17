<?php
/**
 * Carrossel acessivel (references/carousels.md) - um por entrada de
 * carousels[] do BLUEPRINT.yaml. Base em CSS scroll-snap (funciona sem JS:
 * arrastar/rolar); assets/js/carousel.js adiciona setas, bolinhas, autoplay
 * com pausa e teclado, no padrao W3C APG "Carousel".
 *
 * Uso (front-page.php):
 *   get_template_part('template-parts/carousel', null, [
 *       'id'             => 'home_banner',               // carousels[].id
 *       'label'          => __('Destaques', 'project-theme'),
 *       'items'          => project_home('home_banner_slides'),   // repeater ACF
 *       'slide_template' => 'template-parts/carousel-slide-banner',
 *       'autoplay'       => true,        // carousels[].autoplay
 *       'interval'       => 6000,        // carousels[].interval_ms
 *       'loop'           => true,
 *       'arrows'         => true,
 *       'dots'           => true,
 *       'per_view'       => ['desktop' => 1, 'tablet' => 1, 'mobile' => 1],
 *       'anchor'         => 'inicio',    // single page
 *       'class'          => 'carousel--banner', // hero_banner: slides sem espaco
 *   ]);
 *
 * Os slides vem do admin (repeater/CPT): o template nunca escreve conteudo.
 * O visual (posicao das setas, formato das bolinhas) vem da referencia.
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'label' => '',
    'items' => [],
    'slide_template' => '',
    'autoplay' => false,
    'interval' => 6000,
    'loop' => false,
    'arrows' => true,
    'dots' => true,
    'per_view' => [],
    'anchor' => '',
    'class' => '',
], $args ?? []);

$items = array_values(is_array($a['items']) ? $a['items'] : []);
$count = count($items);
if ($count === 0 || $a['slide_template'] === '') {
    return;
}

$per_view = array_merge(['desktop' => 1, 'tablet' => 1, 'mobile' => 1], (array) $a['per_view']);
$uid = 'carousel-' . sanitize_title($a['id'] ?: uniqid());
$style = sprintf(
    '--per-view-desktop: %d; --per-view-tablet: %d; --per-view-mobile: %d;',
    max(1, (int) $per_view['desktop']),
    max(1, (int) $per_view['tablet']),
    max(1, (int) $per_view['mobile'])
);
$autoplay = (bool) $a['autoplay'] && $count > 1;

wp_enqueue_script('project-carousel');
?>
<section class="<?php echo esc_attr(trim('carousel ' . $a['class'])); ?>"<?php project_section_anchor($a['anchor']); ?>
    data-carousel="<?php echo esc_attr($a['id']); ?>"
    data-autoplay="<?php echo $autoplay ? 'true' : 'false'; ?>"
    data-interval="<?php echo esc_attr(max(3000, (int) $a['interval'])); ?>"
    data-loop="<?php echo $a['loop'] ? 'true' : 'false'; ?>"
    data-label-slide="<?php echo esc_attr__('%1$d de %2$d', 'project-theme'); ?>"
    data-label-dot="<?php echo esc_attr__('Ir para o slide %d', 'project-theme'); ?>"
    data-label-pause="<?php echo esc_attr__('Pausar carrossel', 'project-theme'); ?>"
    data-label-play="<?php echo esc_attr__('Reproduzir carrossel', 'project-theme'); ?>"
    aria-roledescription="<?php echo esc_attr__('carrossel', 'project-theme'); ?>"
    aria-label="<?php echo esc_attr($a['label']); ?>"
    style="<?php echo esc_attr($style); ?>">

    <?php /* Controles ANTES dos slides na ordem de tabulacao (APG); a posicao visual e do CSS. Escondidos ate o JS. */ ?>
    <div class="carousel__controls" data-carousel-controls hidden>
        <?php if ($autoplay) : ?>
            <button type="button" class="carousel__toggle" data-carousel-toggle aria-controls="<?php echo esc_attr($uid); ?>-track">
                <span class="carousel__toggle-icon" aria-hidden="true"></span>
                <span class="screen-reader-text" data-carousel-toggle-label><?php esc_html_e('Pausar carrossel', 'project-theme'); ?></span>
            </button>
        <?php endif; ?>
        <?php if ($a['arrows'] && $count > 1) : ?>
            <button type="button" class="carousel__arrow carousel__arrow--prev" data-carousel-prev aria-controls="<?php echo esc_attr($uid); ?>-track">
                <span class="carousel__arrow-icon" aria-hidden="true"></span>
                <span class="screen-reader-text"><?php esc_html_e('Slide anterior', 'project-theme'); ?></span>
            </button>
            <button type="button" class="carousel__arrow carousel__arrow--next" data-carousel-next aria-controls="<?php echo esc_attr($uid); ?>-track">
                <span class="carousel__arrow-icon" aria-hidden="true"></span>
                <span class="screen-reader-text"><?php esc_html_e('Próximo slide', 'project-theme'); ?></span>
            </button>
        <?php endif; ?>
    </div>

    <div class="carousel__track" id="<?php echo esc_attr($uid); ?>-track" data-carousel-track tabindex="0" aria-live="<?php echo $autoplay ? 'off' : 'polite'; ?>">
        <?php foreach ($items as $i => $item) : ?>
            <div class="carousel__slide" data-carousel-slide role="group" aria-roledescription="slide"
                aria-label="<?php echo esc_attr(sprintf(__('%1$d de %2$d', 'project-theme'), $i + 1, $count)); ?>">
                <?php get_template_part($a['slide_template'], null, ['item' => $item, 'index' => $i, 'count' => $count]); ?>
            </div>
        <?php endforeach; ?>
    </div>

    <?php if ($a['dots'] && $count > 1) : ?>
        <div class="carousel__dots" data-carousel-dots hidden></div>
    <?php endif; ?>
</section>
