<?php
/**
 * Home. Monte as secoes aqui chamando get_template_part() para cada
 * componente do BLUEPRINT.yaml (pages[slug=home].sections), na ordem
 * definida la — nao invente ordem diferente da aprovada.
 *
 * Exemplo:
 *   get_template_part('template-parts/hero');
 *   get_template_part('template-parts/card-grid', 'service');
 *   get_template_part('template-parts/testimonial');
 *   get_template_part('template-parts/cta');
 *
 * SINGLE PAGE (project.site_structure: single_page): cada secao recebe a
 * ancora de pages[].sections[].anchor - e o destino dos itens do menu
 * (links personalizados "#servicos"). Ver references/navigation.md.
 *   get_template_part('template-parts/hero', null, ['anchor' => 'inicio']);
 *   get_template_part('template-parts/card-grid', 'service', ['anchor' => 'servicos']); *
 * CARROSSEL / BANNER ROTATIVO (carousels[] do Blueprint): use o componente
 * template-parts/carousel.php - nunca uma biblioteca de terceiros nem
 * slides fixos no template. Ver o cabecalho do arquivo e references/carousels.md.
 */
if (!defined('ABSPATH')) { exit; }
get_header();
?>

<main id="conteudo" class="site-main site-main--home" tabindex="-1">
    <?php get_template_part('template-parts/hero', null, ['anchor' => 'inicio']); ?>
    <?php get_template_part('template-parts/cta'); ?>
</main>

<?php get_footer(); ?>
