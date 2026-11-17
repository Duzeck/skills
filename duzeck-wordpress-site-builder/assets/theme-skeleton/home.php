<?php
/**
 * Indice do blog: a pagina definida em Configuracoes > Leitura > "Pagina
 * de posts" (com a Home estatica, o WordPress usa ESTE arquivo - sem ele
 * cairia no index.php generico). Titulo = titulo dessa pagina (editavel).
 */
if (!defined('ABSPATH')) { exit; }
get_header();
$posts_page = (int) get_option('page_for_posts');
?>
<main id="conteudo" class="site-main site-main--blog" tabindex="-1">
    <?php
    get_template_part('template-parts/blog-list', null, [
        'title' => $posts_page ? get_the_title($posts_page) : get_bloginfo('name'),
        'description' => $posts_page ? get_post_field('post_excerpt', $posts_page) : '',
    ]);
    ?>
</main>
<?php get_footer(); ?>
