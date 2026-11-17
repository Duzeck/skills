<?php
/**
 * Bootstrap do tema. Nao coloque logica de CPT/taxonomia/campos aqui —
 * cada responsabilidade tem seu proprio arquivo em inc/.
 */

if (!defined('ABSPATH')) {
    exit;
}

define('PROJECT_THEME_VERSION', '0.1.0');
define('PROJECT_THEME_DIR', get_template_directory());
define('PROJECT_THEME_URI', get_template_directory_uri());

/*
 * Estrutura do site e comportamento do header - espelham o Blueprint
 * (project.site_structure e theme.header_behavior) e sao gravados pelo
 * scripts/scaffold_wp_project.py (--site-structure / --header-behavior).
 * Sao decisoes de arquitetura, nao conteudo: nao vao para o admin.
 *
 *   single_page -> uma pagina com secoes ancoradas; header SEMPRE sticky,
 *                  menu de ancoras com scroll-spy (references/navigation.md).
 *   multi_page  -> varias paginas; header segue a referencia (static, ou
 *                  sticky se a referencia/usuario pedir).
 */
define('PROJECT_SITE_STRUCTURE', 'multi_page');
define('PROJECT_HEADER_BEHAVIOR', 'static');

/*
 * Tipo schema.org da empresa (Blueprint seo.organization_type), gravado pelo
 * scaffold (--schema-type). Organization = sem atendimento no local;
 * LocalBusiness ou subtipo (GeneralContractor, BeautySalon, Dentist...) =
 * endereco fisico, que entra nos dados estruturados (inc/social.php).
 */
define('PROJECT_SCHEMA_TYPE', 'Organization');

/*
 * Robos de IA no robots.txt (Blueprint seo.ai_crawlers), gravado pelo
 * scaffold (--ai-crawlers): allow | block_training | block_all. E o valor
 * inicial - o administrador muda em Configuracoes do Site (inc/seo.php).
 */
define('PROJECT_AI_CRAWLERS', 'allow');

require_once PROJECT_THEME_DIR . '/inc/content-defaults.php';
require_once PROJECT_THEME_DIR . '/inc/helpers.php';
require_once PROJECT_THEME_DIR . '/inc/fonts.php';
require_once PROJECT_THEME_DIR . '/inc/enqueue.php';
require_once PROJECT_THEME_DIR . '/inc/editor.php';
require_once PROJECT_THEME_DIR . '/inc/post-types.php';
require_once PROJECT_THEME_DIR . '/inc/taxonomies.php';
require_once PROJECT_THEME_DIR . '/inc/acf-options.php';
require_once PROJECT_THEME_DIR . '/inc/acf-fields.php';
require_once PROJECT_THEME_DIR . '/inc/menus.php';
require_once PROJECT_THEME_DIR . '/inc/forms.php';
require_once PROJECT_THEME_DIR . '/inc/maps.php';
require_once PROJECT_THEME_DIR . '/inc/video.php';
require_once PROJECT_THEME_DIR . '/inc/disclosures.php';
require_once PROJECT_THEME_DIR . '/inc/pricing.php';
require_once PROJECT_THEME_DIR . '/inc/social-proof.php';
require_once PROJECT_THEME_DIR . '/inc/blog.php';
require_once PROJECT_THEME_DIR . '/inc/contact.php';
require_once PROJECT_THEME_DIR . '/inc/social.php';
require_once PROJECT_THEME_DIR . '/inc/footer.php';
require_once PROJECT_THEME_DIR . '/inc/header.php';
require_once PROJECT_THEME_DIR . '/inc/hero.php';
require_once PROJECT_THEME_DIR . '/inc/seo.php';
require_once PROJECT_THEME_DIR . '/inc/site-icon.php';

function project_theme_setup() {
    add_theme_support('title-tag');
    add_theme_support('post-thumbnails');
    add_theme_support('html5', ['search-form', 'gallery', 'caption']);
    add_theme_support('responsive-embeds');
    // <link rel="alternate" type="application/rss+xml"> do blog: leitores de
    // feed e agentes acham /feed/ sem adivinhar (references/site-icon.md).
    add_theme_support('automatic-feed-links');
}
add_action('after_setup_theme', 'project_theme_setup');

/*
 * Largura da coluna de texto dos posts/paginas (px). O WordPress usa para
 * escolher o tamanho certo das imagens inseridas no editor (srcset/sizes) e
 * dos videos incorporados - sem isso, serve a imagem grande demais.
 * Ajuste para a largura medida na referencia (references/performance.md).
 */
add_action('after_setup_theme', function () {
    $GLOBALS['content_width'] = (int) apply_filters('project_content_width', 760);
}, 0);
