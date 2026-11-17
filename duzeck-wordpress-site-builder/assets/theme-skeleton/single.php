<?php
/**
 * Fallback para single de qualquer post type sem single-<cpt>.php
 * proprio. Crie single-<slug>.php especifico quando o Blueprint definir
 * campos customizados a exibir para aquele CPT.
 */
if (!defined('ABSPATH')) { exit; }
get_header();
?>

<main id="conteudo" class="site-main" tabindex="-1">
    <?php if (have_posts()) : while (have_posts()) : the_post(); ?>
        <article <?php post_class(); ?>>
            <h1><?php the_title(); ?></h1>
            <?php if (has_post_thumbnail()) : the_post_thumbnail('large'); endif; ?>
            <div class="entry-content"><?php the_content(); ?></div>
        </article>
    <?php endwhile; endif; ?>
</main>

<?php get_footer(); ?>
