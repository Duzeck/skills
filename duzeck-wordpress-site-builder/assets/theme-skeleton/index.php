<?php
/**
 * Template de fallback generico. front-page.php, page.php, single.php e
 * archive.php cobrem os casos especificos — este so entra quando nenhum
 * deles se aplica.
 */
if (!defined('ABSPATH')) { exit; }
get_header();
?>

<main id="conteudo" class="site-main" tabindex="-1">
    <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
        <article <?php post_class(); ?>>
            <h1><?php the_title(); ?></h1>
            <div class="entry-content"><?php the_content(); ?></div>
        </article>
    <?php endwhile; else : ?>
        <p><?php esc_html_e('Nada encontrado.', 'project-theme'); ?></p>
    <?php endif; ?>
</main>

<?php get_footer(); ?>
