<?php
/**
 * "Ultimas do blog" / "Noticias" numa secao da Home (references/blog.md).
 * Consulta propria (sem paginacao, no_found_rows) - a trava de demo em
 * producao vale aqui tambem (pre_get_posts em inc/blog.php).
 *
 * Uso:
 *   get_template_part('template-parts/posts-latest', null, [
 *       'id'       => 'home_blog',                       // blog.home_section.id
 *       'count'    => 3,                                 // blog.home_section.count
 *       'category' => '',                                // slug opcional
 *       'fields'   => ['image', 'date', 'category', 'excerpt'],
 *       'all_label'=> project_home('home_blog_all_label'), // "Ver todos os posts"
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => 'home_blog',
    'count' => 3,
    'category' => '',
    'fields' => ['image', 'date', 'category', 'excerpt'],
    'all_label' => '',
    'heading_level' => 3,
], $args ?? []);

$query = new WP_Query(array_filter([
    'post_type' => 'post',
    'posts_per_page' => max(1, (int) $a['count']),
    'category_name' => $a['category'] ?: null,
    'ignore_sticky_posts' => true,
    'no_found_rows' => true,
]));

if (!$query->have_posts()) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="posts-missing">%s</p>', esc_html__('Nenhum post publicado ainda.', 'project-theme'));
    }
    return;
}
$posts_page = (int) get_option('page_for_posts');
?>
<div class="posts-latest" data-posts-latest="<?php echo esc_attr($a['id']); ?>">
    <ul class="post-grid" role="list">
        <?php while ($query->have_posts()) : $query->the_post(); ?>
            <li><?php get_template_part('template-parts/post-card', null, ['heading_level' => $a['heading_level'], 'fields' => $a['fields']]); ?></li>
        <?php endwhile; ?>
    </ul>
    <?php if ($posts_page && $a['all_label']) : ?>
        <p class="posts-latest__all"><a href="<?php echo esc_url(get_permalink($posts_page)); ?>"><?php echo esc_html($a['all_label']); ?></a></p>
    <?php endif; ?>
</div>
<?php
wp_reset_postdata();
