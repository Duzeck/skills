<?php
/**
 * Arquivos: de posts (categoria, tag, autor, data) usam a lista do blog;
 * de CPT sem archive-<cpt>.php proprio caem no fallback simples abaixo.
 * Crie archive-<slug>.php especifico quando o Blueprint definir um grid
 * customizado (cards, filtros) para aquele CPT.
 */
if (!defined('ABSPATH')) { exit; }
get_header();
$is_blog = is_category() || is_tag() || is_author() || is_date() || get_post_type() === 'post';
?>

<main id="conteudo" class="site-main" tabindex="-1">
    <?php if ($is_blog) : ?>
        <?php
        get_template_part('template-parts/blog-list', null, [
            'title' => wp_strip_all_tags(get_the_archive_title()),
            'description' => get_the_archive_description(),
            'empty' => __('Nenhum post nesta categoria ainda.', 'project-theme'),
        ]);
        ?>
    <?php else : ?>
        <h1><?php the_archive_title(); ?></h1>
        <div class="archive-grid">
            <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
                <article <?php post_class(); ?>>
                    <h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2>
                </article>
            <?php endwhile; else : ?>
                <p><?php esc_html_e('Nenhum item encontrado.', 'project-theme'); ?></p>
            <?php endif; ?>
        </div>
        <?php project_posts_pagination(); ?>
    <?php endif; ?>
</main>

<?php get_footer(); ?>
