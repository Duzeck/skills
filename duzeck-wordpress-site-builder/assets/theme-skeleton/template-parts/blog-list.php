<?php
/**
 * Lista de posts do loop principal (home.php, archive.php de posts,
 * search.php): grade de cards + paginacao acessivel + estado vazio.
 * $args: title (h1), description, empty (mensagem), fields.
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'title' => '',
    'description' => '',
    'empty' => __('Nenhum post encontrado.', 'project-theme'),
    'fields' => ['image', 'date', 'category', 'excerpt'],
], $args ?? []);
$sidebar = defined('PROJECT_BLOG_SIDEBAR') && PROJECT_BLOG_SIDEBAR;
?>
<div class="blog-layout<?php echo $sidebar ? ' blog-layout--sidebar' : ''; ?>">
    <div class="blog-layout__main" data-posts-index>
        <?php if ($a['title']) : ?>
            <h1 class="blog-title"><?php echo esc_html($a['title']); ?></h1>
        <?php endif; ?>
        <?php if ($a['description']) : ?>
            <div class="blog-description"><?php echo wp_kses_post($a['description']); ?></div>
        <?php endif; ?>
        <?php if (have_posts()) : ?>
            <ul class="post-grid" role="list">
                <?php while (have_posts()) : the_post(); ?>
                    <li><?php get_template_part('template-parts/post-card', null, ['heading_level' => 2, 'fields' => $a['fields']]); ?></li>
                <?php endwhile; ?>
            </ul>
            <?php project_posts_pagination(); ?>
        <?php else : ?>
            <p class="blog-empty"><?php echo esc_html($a['empty']); ?></p>
            <?php get_search_form(); ?>
        <?php endif; ?>
    </div>
    <?php if ($sidebar) : ?>
        <?php get_template_part('template-parts/blog-sidebar'); ?>
    <?php endif; ?>
</div>
