<?php if (!defined('ABSPATH')) { exit; } ?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<?php
/*
 * Header (references/header-menu.md + navigation.md). Estrutura de
 * inc/header.php (project_header_config); conteudo do admin.
 * Sticky: single page sempre; multipaginas so se o Blueprint pedir. O
 * header fica filho DIRETO do <body> - position: sticky para de funcionar
 * dentro de um wrapper com overflow.
 */
$project_cfg = project_header_config();
$project_sticky = project_header_is_sticky();
$project_transparent = project_header_is_transparent();
$project_split = $project_cfg['layout'] === 'logo_center_split';
$project_header_class = 'site-header site-header--' . $project_cfg['layout']
    . ($project_sticky ? ' site-header--sticky' : '')
    . ($project_transparent ? ' site-header--transparent' : '');
$project_cta_label = $project_cfg['cta'] ? trim((string) project_option('header_cta_label')) : '';
$project_menu = function ($location, $label) {
    printf('<nav class="site-header__nav" aria-label="%s" data-nav>', esc_attr($label));
    wp_nav_menu(['theme_location' => $location, 'container' => false, 'fallback_cb' => false]);
    echo '</nav>';
};
?>
<a class="skip-link" href="#conteudo"><?php esc_html_e('Pular para o conteúdo', 'project-theme'); ?></a>

<?php get_template_part('template-parts/announcement'); ?>
<?php get_template_part('template-parts/header-topbar', null, ['items' => $project_cfg['top_bar']]); ?>

<header id="topo" class="<?php echo esc_attr($project_header_class); ?>" data-site-header<?php echo $project_sticky ? ' data-sticky' : ''; ?><?php echo $project_transparent ? ' data-transparent' : ''; ?><?php echo project_is_single_page() ? ' data-scrollspy' : ''; ?>
    data-label-submenu="<?php echo esc_attr__('Submenu de %s', 'project-theme'); ?>">
    <div class="site-header__inner">
        <?php if (!$project_split) : ?>
            <?php echo project_site_logo(); // escapado em inc/header.php ?>
        <?php endif; ?>

        <?php /* Escondido ate o JS carregar: sem JS o menu fica sempre visivel (progressive enhancement). */ ?>
        <button class="site-header__toggle" type="button" aria-expanded="false" aria-controls="site-nav-panel" data-nav-toggle hidden>
            <span class="site-header__toggle-icon" aria-hidden="true"></span>
            <span class="screen-reader-text"><?php esc_html_e('Menu', 'project-theme'); ?></span>
        </button>

        <div class="site-header__panel" id="site-nav-panel" data-nav-panel>
            <?php if ($project_split) : ?>
                <?php $project_menu('primary_left', __('Menu principal', 'project-theme')); ?>
                <?php echo project_site_logo(); ?>
                <?php $project_menu('primary_right', __('Menu principal - continuação', 'project-theme')); ?>
            <?php else : ?>
                <?php $project_menu('primary', __('Menu principal', 'project-theme')); ?>
            <?php endif; ?>

            <?php if ($project_cfg['actions'] || $project_cta_label) : ?>
                <div class="site-header__actions">
                    <?php if (in_array('search', $project_cfg['actions'], true)) : ?>
                        <details class="site-header__search" data-header-search>
                            <summary class="site-header__action">
                                <span class="site-header__action-icon site-header__action-icon--search" aria-hidden="true"></span>
                                <span class="screen-reader-text"><?php esc_html_e('Buscar no site', 'project-theme'); ?></span>
                            </summary>
                            <div class="site-header__search-panel"><?php get_search_form(); ?></div>
                        </details>
                    <?php endif; ?>
                    <?php if (in_array('account', $project_cfg['actions'], true) && project_option('header_account_url')) : ?>
                        <a class="site-header__action" href="<?php echo esc_url(project_target_url(project_option('header_account_url'))); ?>">
                            <span class="site-header__action-icon site-header__action-icon--account" aria-hidden="true"></span>
                            <span class="screen-reader-text"><?php echo esc_html(project_option('header_account_label') ?: __('Minha conta', 'project-theme')); ?></span>
                        </a>
                    <?php endif; ?>
                    <?php if ($project_cta_label) : ?>
                        <a class="site-header__cta" href="<?php echo esc_url(project_target_url(project_option('header_cta_target'))); ?>"><?php echo esc_html($project_cta_label); ?></a>
                    <?php endif; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>
</header>
