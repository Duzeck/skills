<?php
/**
 * Pagina interna: cabecalho (trilha + titulo + texto do admin) e conteudo.
 * Paginas com layout proprio da referencia ganham page-<slug>.php.
 */
if (!defined('ABSPATH')) { exit; }
get_header();
?>

<main id="conteudo" class="site-main" tabindex="-1">
    <?php while (have_posts()) : the_post(); ?>
        <?php get_template_part('template-parts/page-header'); ?>
        <article <?php post_class(); ?>>
            <div class="entry-content"><?php the_content(); ?></div>
        </article>
    <?php endwhile; ?>
</main>

<?php get_footer(); ?>
