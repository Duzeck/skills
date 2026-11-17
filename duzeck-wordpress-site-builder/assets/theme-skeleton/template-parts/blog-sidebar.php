<?php
/**
 * Barra lateral do blog (so se o Blueprint pedir: blog.sidebar e
 * PROJECT_BLOG_SIDEBAR em inc/blog.php). Busca, categorias e recentes -
 * remova o que a referencia nao mostra.
 */
if (!defined('ABSPATH')) { exit; }
$recent = new WP_Query(['post_type' => 'post', 'posts_per_page' => 4, 'no_found_rows' => true, 'ignore_sticky_posts' => true]);
?>
<aside class="blog-sidebar" aria-label="<?php esc_attr_e('Barra lateral do blog', 'project-theme'); ?>">
    <section class="blog-sidebar__block">
        <h2 class="blog-sidebar__title"><?php esc_html_e('Buscar', 'project-theme'); ?></h2>
        <?php get_search_form(); ?>
    </section>
    <section class="blog-sidebar__block">
        <h2 class="blog-sidebar__title"><?php esc_html_e('Categorias', 'project-theme'); ?></h2>
        <ul><?php wp_list_categories(['title_li' => '', 'show_count' => false, 'hide_empty' => true]); ?></ul>
    </section>
    <?php if ($recent->have_posts()) : ?>
        <section class="blog-sidebar__block">
            <h2 class="blog-sidebar__title"><?php esc_html_e('Posts recentes', 'project-theme'); ?></h2>
            <ul>
                <?php while ($recent->have_posts()) : $recent->the_post(); ?>
                    <li><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a> <?php echo project_post_time(); ?></li>
                <?php endwhile; wp_reset_postdata(); ?>
            </ul>
        </section>
    <?php endif; ?>
</aside>
