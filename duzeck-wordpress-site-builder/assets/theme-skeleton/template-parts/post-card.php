<?php
/**
 * Card de post (references/blog.md) - dentro do loop (the_post()).
 * UM link por card (o titulo), esticado sobre o card inteiro por CSS:
 * leitor de tela e Tab encontram o post uma vez so (imagem + titulo +
 * "Leia mais" separados seriam 3 links iguais). A categoria continua
 * clicavel por cima.
 *
 * $args: heading_level (padrao 2 em listagem; 3 na secao da Home),
 *        fields (image, date, category, author, reading_time, excerpt).
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'heading_level' => 2,
    'fields' => ['image', 'date', 'category', 'excerpt'],
    'ratio' => '16 / 9',
], $args ?? []);
$f = (array) $a['fields'];
$level = 'h' . min(6, max(2, (int) $a['heading_level']));
?>
<article <?php post_class('post-card'); ?> data-post-card>
    <?php if (in_array('image', $f, true)) : ?>
        <?php
        project_media(get_post_thumbnail_id(), [
            'ratio' => $a['ratio'],
            'alt' => '',                 // o titulo do post ja e o nome do link
            'label' => __('Imagem do post', 'project-theme'),
            'class' => 'post-card__image',
            'size' => 'medium_large',
        ]);
        ?>
    <?php endif; ?>
    <div class="post-card__body">
        <?php if (in_array('category', $f, true)) : ?>
            <?php echo project_post_category_link(); // ja escapado ?>
        <?php endif; ?>
        <<?php echo $level; ?> class="post-card__title">
            <a class="post-card__link" href="<?php the_permalink(); ?>"><?php the_title(); ?></a>
        </<?php echo $level; ?>>
        <?php
        $meta = [];
        if (in_array('date', $f, true)) {
            $meta[] = project_post_time();
        }
        if (in_array('author', $f, true)) {
            $meta[] = esc_html(get_the_author());
        }
        if (in_array('reading_time', $f, true)) {
            $meta[] = esc_html(project_reading_time());
        }
        ?>
        <?php if ($meta) : ?>
            <p class="post-card__meta"><?php echo implode(' <span aria-hidden="true">·</span> ', $meta); ?></p>
        <?php endif; ?>
        <?php if (in_array('excerpt', $f, true)) : ?>
            <p class="post-card__excerpt"><?php echo esc_html(wp_strip_all_tags(get_the_excerpt())); ?></p>
        <?php endif; ?>
    </div>
</article>
