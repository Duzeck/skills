<?php
if (!defined('ABSPATH')) { exit; }
get_header();
?>

<main id="conteudo" class="site-main" tabindex="-1">
    <h1><?php esc_html_e('Página não encontrada', 'project-theme'); ?></h1>
    <p><a href="<?php echo esc_url(home_url('/')); ?>"><?php esc_html_e('Voltar para a página inicial', 'project-theme'); ?></a></p>
</main>

<?php get_footer(); ?>
