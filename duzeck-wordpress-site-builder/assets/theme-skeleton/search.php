<?php
/** Resultado de busca (a trava de demo em producao vale aqui tambem). */
if (!defined('ABSPATH')) { exit; }
get_header();
?>
<main id="conteudo" class="site-main" tabindex="-1">
    <?php
    get_template_part('template-parts/blog-list', null, [
        /* translators: %s: termo buscado */
        'title' => sprintf(__('Resultados para "%s"', 'project-theme'), get_search_query(false)),
        'empty' => __('Nada encontrado para essa busca. Tente outras palavras.', 'project-theme'),
        'fields' => ['date', 'category', 'excerpt'],
    ]);
    ?>
</main>
<?php get_footer(); ?>
