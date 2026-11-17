<?php
/**
 * Depoimentos (references/social-proof.md) - um por testimonials[] do Blueprint.
 * Em carrossel: use template-parts/carousel.php com este markup por slide
 * (carousels[] kind testimonials) - a regra de autenticidade vale igual.
 *
 * Marcacao: <figure> com <blockquote> (a fala) e <figcaption> (quem disse).
 * O nome NAO vai em <cite> (pela especificacao, <cite> e titulo de obra,
 * nao pessoa). Estrelas: visual aria-hidden + "Avaliação: 4,5 de 5".
 * Foto ao lado do nome e decorativa (alt vazio: o nome ja esta escrito).
 * SEM dados estruturados Review/AggregateRating: o Google nao mostra
 * estrelas para avaliacoes que a empresa publica sobre si mesma (2019).
 *
 * Uso:
 *   get_template_part('template-parts/testimonials', null, [
 *       'id'     => 'home_testimonials',        // testimonials[].id
 *       'items'  => $itens,                     // [quote, name, role, company, city, photo, rating, source]
 *       'layout' => 'grid',                     // grid | list | single
 *       'demo'   => false,                      // testimonials[].content_source === 'demo'
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'items' => [],
    'layout' => 'grid',
    'demo' => false,
    'class' => '',
], $args ?? []);

if (project_demo_blocked($a['demo'])) {
    project_demo_notice(__('Depoimentos', 'project-theme'));
    return;
}
$items = array_values((array) $a['items']);
if (!$items) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="testimonials-missing">%s</p>', esc_html__('Depoimentos sem conteúdo: cadastre no admin.', 'project-theme'));
    }
    return;
}
$layout = in_array($a['layout'], ['grid', 'list', 'single'], true) ? $a['layout'] : 'grid';
?>
<ul class="<?php echo esc_attr(trim('testimonials testimonials--' . $layout . ' ' . $a['class'])); ?>" role="list"
    data-testimonials="<?php echo esc_attr($a['id']); ?>"<?php echo $a['demo'] ? ' data-demo="true"' : ''; ?>>
    <?php foreach ($items as $item) : ?>
        <?php
        $item = (array) $item;
        $rating = project_rating_value($item['rating'] ?? null);
        $meta = array_filter([
            trim(implode(', ', array_filter([$item['role'] ?? '', $item['company'] ?? '']))),
            $item['city'] ?? '',
        ]);
        ?>
        <li class="testimonial">
            <figure class="testimonial__figure">
                <?php if ($rating !== null) : ?>
                    <p class="testimonial__rating">
                        <span class="testimonial__stars" aria-hidden="true" style="--rating: <?php echo esc_attr($rating); ?>;"></span>
                        <span class="screen-reader-text">
                            <?php
                            /* translators: %s: nota, ex.: 4,5 */
                            printf(esc_html__('Avaliação: %s de 5', 'project-theme'), esc_html(str_replace('.', ',', (string) $rating)));
                            ?>
                        </span>
                    </p>
                <?php endif; ?>
                <blockquote class="testimonial__quote">
                    <?php echo wp_kses_post(wpautop(esc_html($item['quote'] ?? ''))); ?>
                </blockquote>
                <figcaption class="testimonial__author">
                    <?php if (!empty($item['photo'])) : ?>
                        <?php
                        project_media(project_image_id($item['photo']), [
                            'ratio' => '1 / 1',
                            'fallback' => is_string($item['photo']) && !is_numeric($item['photo']) ? $item['photo'] : '',
                            'alt' => '',
                            'label' => __('Foto', 'project-theme'),
                            'class' => 'testimonial__photo',
                            'size' => 'thumbnail',
                        ]);
                        ?>
                    <?php endif; ?>
                    <span class="testimonial__name"><?php echo esc_html($item['name'] ?? ''); ?></span>
                    <?php if ($meta) : ?>
                        <span class="testimonial__meta"><?php echo esc_html(implode(' · ', $meta)); ?></span>
                    <?php endif; ?>
                    <?php if (!empty($item['source'])) : ?>
                        <span class="testimonial__source"><?php echo esc_html($item['source']); ?></span>
                    <?php endif; ?>
                </figcaption>
            </figure>
        </li>
    <?php endforeach; ?>
</ul>
