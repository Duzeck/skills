<?php
/**
 * Hero (references/hero-banners.md) - um por heroes[] do Blueprint.
 *
 * kind:
 *   background - foto ocupando a secao, texto por cima (camada de contraste)
 *   split      - texto de um lado, imagem do outro
 *   centered   - so texto e botoes
 *   form       - texto + formulario (CF7, project_form)
 * Banner rotativo: carousel.php (kind hero_banner). Video de fundo: video.php.
 *
 * - Imagem e <img> (nao background-image do CSS): o navegador a descobre
 *   cedo, ela tem srcset e entra como LCP com fetchpriority="high".
 * - Celular: imagem propria (<picture>) ou ponto focal (object-position).
 * - Camada de contraste configuravel (overlay 0..1) - o QA mede o contraste
 *   real do texto sobre a foto.
 * - Altura em svh/dvh (100vh fica atras da barra do navegador no celular).
 * - Titulo h1 (um por pagina); botoes so com rotulo e destino reais.
 *
 * Uso (front-page.php):
 *   get_template_part('template-parts/hero', null, [
 *       'kind'    => 'background',
 *       'anchor'  => 'inicio',
 *       'eyebrow' => project_home('home_hero_eyebrow'),
 *       'title'   => project_home('home_hero_title'),
 *       'text'    => project_home('home_hero_text'),
 *       'image'   => project_home('home_hero_image'),
 *       'image_mobile' => project_home('home_hero_image_mobile'),
 *       'focal'   => project_home('home_hero_focal') ?: '50% 50%',
 *       'image_alt' => '',                       // decorativa; descreva se a foto informa algo
 *       'overlay' => 0.45,                       // 0 = sem camada
 *       'height'  => 'full',                     // full | large | auto
 *       'buttons' => [['label' => project_home('home_hero_primary_label'), 'target' => project_home('home_hero_primary_page')],
 *                     ['label' => project_home('home_hero_secondary_label'), 'target' => ..., 'style' => 'secondary']],
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => 'hero',
    'kind' => 'background',
    'anchor' => '',
    'eyebrow' => '',
    'title' => '',
    'text' => '',
    'image' => 0,
    'image_mobile' => 0,
    'fallback' => '',
    'focal' => '50% 50%',
    'image_alt' => '',
    'overlay' => 0.45,
    'height' => 'large',
    'buttons' => [],
    'form' => '',
    'heading_level' => 1,
    'class' => '',
], $args ?? []);

$title = trim((string) $a['title']) !== '' ? $a['title'] : get_the_title();
$kind = in_array($a['kind'], ['background', 'split', 'centered', 'form'], true) ? $a['kind'] : 'background';
$tag = 'h' . min(6, max(1, (int) $a['heading_level']));
$image_id = project_image_id($a['image']);
$mobile_id = project_image_id($a['image_mobile']);
$focal = preg_match('/^\d{1,3}% \d{1,3}%$/', (string) $a['focal']) ? $a['focal'] : '50% 50%';

$media = '';
if ($kind === 'background' || $kind === 'split') {
    $img_attrs = [
        'alt' => (string) $a['image_alt'],
        'loading' => 'eager',
        'fetchpriority' => 'high',   // o hero e o LCP da pagina
        'sizes' => $kind === 'background' ? '100vw' : '(max-width: 767px) 100vw, 50vw',
        'class' => 'hero__img',
        'style' => 'object-position: ' . $focal . ';',
    ];
    if ($image_id) {
        $img = wp_get_attachment_image($image_id, 'full', false, $img_attrs);
        if ($mobile_id) {
            $img = sprintf(
                '<picture><source media="(max-width: 767px)" srcset="%s" sizes="100vw">%s</picture>',
                esc_attr((string) wp_get_attachment_image_srcset($mobile_id, 'large')),
                $img
            );
        }
        $media = $img;
    } elseif ($a['fallback'] && file_exists(get_template_directory() . '/assets/img/' . $a['fallback'])) {
        $media = sprintf('<img class="hero__img" src="%s" alt="%s" loading="eager" fetchpriority="high" style="object-position: %s;" data-provisional="crop_from_reference">',
            esc_url(get_template_directory_uri() . '/assets/img/' . $a['fallback']), esc_attr($a['image_alt']), esc_attr($focal));
    } else {
        ob_start();
        project_media(0, ['ratio' => '16 / 9', 'label' => __('Imagem do hero', 'project-theme'), 'class' => 'hero__placeholder']);
        $media = ob_get_clean();
    }
}
$classes = trim(sprintf('hero hero--%s hero--h-%s %s', $kind, $a['height'], $a['class']));
?>
<section class="<?php echo esc_attr($classes); ?>"<?php project_section_anchor($a['anchor']); ?> data-hero="<?php echo esc_attr($a['id']); ?>"
    style="--overlay: <?php echo esc_attr(max(0, min(1, (float) $a['overlay']))); ?>;">
    <?php if ($media) : ?>
        <div class="hero__media">
            <?php echo $media; // gerado pelo WordPress/escapado acima ?>
            <?php if ($kind === 'background' && (float) $a['overlay'] > 0) : ?>
                <span class="hero__overlay" aria-hidden="true"></span>
            <?php endif; ?>
        </div>
    <?php endif; ?>
    <div class="hero__content">
        <?php if ($a['eyebrow']) : ?>
            <p class="hero__eyebrow" data-contrast><?php echo project_lines($a['eyebrow']); ?></p>
        <?php endif; ?>
        <<?php echo $tag; ?> class="hero__title" data-contrast><?php echo project_lines($title); ?></<?php echo $tag; ?>>
        <?php if ($a['text']) : ?>
            <p class="hero__text" data-contrast><?php echo project_lines($a['text']); ?></p>
        <?php endif; ?>
        <?php echo project_buttons_html((array) $a['buttons']); ?>
        <?php if ($kind === 'form' && $a['form']) : ?>
            <div class="hero__form"><?php project_form($a['form']); ?></div>
        <?php endif; ?>
    </div>
</section>
