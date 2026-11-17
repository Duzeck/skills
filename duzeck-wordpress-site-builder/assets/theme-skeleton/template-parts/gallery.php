<?php
/**
 * Galeria de fotos (references/galleries.md) - uma por galleries[] do Blueprint.
 *
 * Layouts: grid (mesma proporcao), masonry (alturas livres, colunas),
 * featured_thumbs (primeira grande + miniaturas). Galeria em carrossel usa
 * template-parts/carousel.php (carousels[] kind gallery).
 *
 * lightbox = true: cada foto e um link para a versao grande (funciona sem
 * JS); o gallery.js abre num <dialog> modal acessivel (Esc, setas, foco
 * preso e devolvido, contador "3 de 12").
 * visible = N: mostra N fotos; a N-esima recebe o "+X" da referencia e as
 * demais ficam ocultas (entram so no lightbox; nao sao baixadas antes).
 *
 * Uso:
 *   get_template_part('template-parts/gallery', null, [
 *       'id'       => 'project_gallery',                 // galleries[].id
 *       'label'    => get_the_title(),                   // nome acessivel
 *       'images'   => project_field('project_gallery'),  // campo galeria do ACF (IDs/arrays)
 *       'layout'   => 'grid',
 *       'per_row'  => ['desktop' => 3, 'tablet' => 2, 'mobile' => 1],
 *       'ratio'    => '4 / 3',
 *       'visible'  => 6,
 *       'lightbox' => true,
 *       'captions' => false,
 *   ]);
 * Fotos sem arquivo real podem ser nomes de arquivo em assets/img/
 * (recortes da referencia, provisorios).
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'label' => '',
    'images' => [],
    'layout' => 'grid',
    'per_row' => [],
    'ratio' => '4 / 3',
    'visible' => 0,
    'lightbox' => true,
    'captions' => false,
    'size' => 'medium_large',
    'class' => '',
], $args ?? []);

$items = [];
foreach ((array) $a['images'] as $image) {
    $id = project_image_id($image);
    if ($id) {
        $full = wp_get_attachment_image_src($id, '2048x2048') ?: wp_get_attachment_image_src($id, 'full');
        $alt = (string) get_post_meta($id, '_wp_attachment_image_alt', true);
        $items[] = [
            'thumb' => wp_get_attachment_image($id, $a['size'], false, ['loading' => 'lazy', 'alt' => $alt]),
            'full' => $full ? $full[0] : '',
            'alt' => $alt,
            'caption' => (string) wp_get_attachment_caption($id),
        ];
    } elseif (is_string($image) && $image !== '' && file_exists(get_template_directory() . '/assets/img/' . $image)) {
        $url = get_template_directory_uri() . '/assets/img/' . $image;
        $items[] = [
            'thumb' => sprintf('<img src="%s" alt="" loading="lazy" data-provisional="crop_from_reference">', esc_url($url)),
            'full' => $url,
            'alt' => '',
            'caption' => '',
        ];
    }
}

$count = count($items);
if ($count === 0) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="gallery-missing">%s</p>', esc_html__('Galeria sem fotos: adicione as imagens no admin.', 'project-theme'));
    }
    return;
}

$visible = (int) $a['visible'] > 0 ? min((int) $a['visible'], $count) : $count;
$more = $count - $visible;
$per_row = array_merge(['desktop' => 3, 'tablet' => 2, 'mobile' => 1], (array) $a['per_row']);
$style = sprintf(
    '--ratio: %s; --per-row-desktop: %d; --per-row-tablet: %d; --per-row-mobile: %d;',
    $a['ratio'], max(1, (int) $per_row['desktop']), max(1, (int) $per_row['tablet']), max(1, (int) $per_row['mobile'])
);
$layout = in_array($a['layout'], ['grid', 'masonry', 'featured_thumbs'], true) ? $a['layout'] : 'grid';

if ($a['lightbox']) {
    wp_enqueue_script('project-gallery');
}
?>
<div class="<?php echo esc_attr(trim('gallery gallery--' . $layout . ' ' . $a['class'])); ?>"
    data-gallery="<?php echo esc_attr($a['id']); ?>"
    data-lightbox="<?php echo $a['lightbox'] ? 'true' : 'false'; ?>"
    data-label="<?php echo esc_attr($a['label']); ?>"
    data-label-close="<?php echo esc_attr__('Fechar', 'project-theme'); ?>"
    data-label-prev="<?php echo esc_attr__('Foto anterior', 'project-theme'); ?>"
    data-label-next="<?php echo esc_attr__('Próxima foto', 'project-theme'); ?>"
    data-label-counter="<?php echo esc_attr__('%1$d de %2$d', 'project-theme'); ?>"
    style="<?php echo esc_attr($style); ?>">
    <ul class="gallery__list" role="list">
        <?php foreach ($items as $i => $item) : ?>
            <?php
            $is_last_visible = $more > 0 && $i === $visible - 1;
            $hidden = $i >= $visible;
            ?>
            <li class="gallery__item"<?php echo $hidden ? ' hidden' : ''; ?>>
                <figure class="gallery__figure">
                    <?php if ($a['lightbox'] && $item['full']) : ?>
                        <a class="gallery__link" href="<?php echo esc_url($item['full']); ?>" data-gallery-item
                            data-alt="<?php echo esc_attr($item['alt']); ?>" data-caption="<?php echo esc_attr($item['caption']); ?>">
                            <?php echo $item['thumb']; ?>
                            <?php if ($is_last_visible) : ?>
                                <span class="gallery__more" aria-hidden="true">+<?php echo (int) $more; ?></span>
                                <span class="screen-reader-text">
                                    <?php
                                    /* translators: %d: quantidade de fotos ocultas */
                                    printf(esc_html(_n('(e mais %d foto)', '(e mais %d fotos)', $more, 'project-theme')), (int) $more);
                                    ?>
                                </span>
                            <?php endif; ?>
                        </a>
                    <?php else : ?>
                        <?php echo $item['thumb']; ?>
                    <?php endif; ?>
                    <?php if ($a['captions'] && $item['caption']) : ?>
                        <figcaption class="gallery__caption"><?php echo esc_html($item['caption']); ?></figcaption>
                    <?php endif; ?>
                </figure>
            </li>
        <?php endforeach; ?>
    </ul>
</div>
