<?php
/**
 * Blog / noticias (references/blog.md). Usa o post NATIVO do WordPress
 * (categorias, tags, feed, arquivos por data, plugins de SEO) - nunca um
 * CPT "blog".
 *
 * Posts da referencia sao titulos inventados com foto de banco de imagem:
 * semeados com a meta _project_demo = 1 e, em PRODUCAO, somem de tudo -
 * listagens, busca, feed, API REST, sitemap - e o link direto da 404.
 */

if (!defined('ABSPATH')) {
    exit;
}

/* Comentarios: decisao do Blueprint (blog.comments). Padrao desligado:
   ligar exige moderacao, anti-spam (Akismet) e aviso de privacidade. */
if (!defined('PROJECT_COMMENTS')) {
    define('PROJECT_COMMENTS', false);
}
if (!PROJECT_COMMENTS) {
    add_filter('comments_open', '__return_false', 20);
    add_filter('pings_open', '__return_false', 20);
    add_filter('comments_array', '__return_empty_array', 20);
}

/* ---------------------------------------------------------------- Demo */

function project_demo_posts_hidden() {
    return project_demo_blocked(true); // producao
}

function project_exclude_demo_meta_query(array $meta_query = []) {
    $clause = ['key' => '_project_demo', 'compare' => 'NOT EXISTS'];
    return $meta_query ? ['relation' => 'AND', $meta_query, $clause] : [$clause];
}

add_action('pre_get_posts', function ($query) {
    if (is_admin() || !project_demo_posts_hidden()) {
        return;
    }
    $types = (array) ($query->get('post_type') ?: 'post');
    if (!in_array('post', $types, true) && !in_array('any', $types, true) && !$query->is_search()) {
        return;
    }
    $query->set('meta_query', project_exclude_demo_meta_query((array) ($query->get('meta_query') ?: [])));
});

add_filter('rest_post_query', function ($args) {
    if (project_demo_posts_hidden()) {
        $args['meta_query'] = project_exclude_demo_meta_query((array) ($args['meta_query'] ?? []));
    }
    return $args;
});

add_filter('wp_sitemaps_posts_query_args', function ($args) {
    if (project_demo_posts_hidden()) {
        $args['meta_query'] = project_exclude_demo_meta_query((array) ($args['meta_query'] ?? []));
    }
    return $args;
});

/* "Anterior / Proximo" (get_adjacent_post) usa SQL proprio, sem WP_Query:
   o pre_get_posts nao alcanca - sem isto o post real mais recente linkaria
   para o demo em producao (encontrado no teste). Alias da tabela: "p". */
foreach (['next', 'previous'] as $project_adjacent) {
    add_filter("get_{$project_adjacent}_post_join", function ($join) {
        if (!project_demo_posts_hidden()) {
            return $join;
        }
        global $wpdb;
        return $join . " LEFT JOIN {$wpdb->postmeta} AS project_demo_pm ON (p.ID = project_demo_pm.post_id AND project_demo_pm.meta_key = '_project_demo')";
    });
    add_filter("get_{$project_adjacent}_post_where", function ($where) {
        return project_demo_posts_hidden() ? $where . ' AND project_demo_pm.post_id IS NULL' : $where;
    });
}

add_action('template_redirect', function () {
    if (project_demo_posts_hidden() && is_singular() && get_post_meta(get_queried_object_id(), '_project_demo', true)) {
        global $wp_query;
        $wp_query->set_404();
        status_header(404);
        nocache_headers();
    }
});

/* ------------------------------------------------------------- Helpers */

/** "4 min de leitura" (200 palavras/min, minimo 1). */
function project_reading_time($post = null) {
    $text = wp_strip_all_tags(strip_shortcodes((string) get_post_field('post_content', $post)));
    $words = count(preg_split('/\s+/u', trim($text), -1, PREG_SPLIT_NO_EMPTY));
    $minutes = max(1, (int) ceil($words / 200));
    /* translators: %d: minutos */
    return sprintf(_n('%d min de leitura', '%d min de leitura', $minutes, 'project-theme'), $minutes);
}

/** <time datetime="ISO 8601">data no formato do site</time>. */
function project_post_time($post = null, $modified = false) {
    $iso = $modified ? get_the_modified_date('c', $post) : get_the_date('c', $post);
    $shown = $modified ? get_the_modified_date('', $post) : get_the_date('', $post);
    return sprintf('<time datetime="%s">%s</time>', esc_attr($iso), esc_html($shown));
}

/** Categoria principal (primeira) como link. */
function project_post_category_link($post = null) {
    $cats = get_the_category($post ? get_post($post)->ID : 0);
    if (!$cats) {
        return '';
    }
    return sprintf('<a class="post-category" href="%s">%s</a>', esc_url(get_category_link($cats[0])), esc_html($cats[0]->name));
}

add_filter('excerpt_length', function () {
    return 24;
});
add_filter('excerpt_more', function () {
    return '…';
});

/**
 * Links de compartilhamento SEM script de terceiros (nada de SDK do
 * Facebook, AddThis, ShareThis: rastreio e peso). URLs de share oficiais.
 */
function project_share_links($post = null) {
    $url = rawurlencode(get_permalink($post));
    $title = rawurlencode(wp_strip_all_tags(get_the_title($post)));
    return [
        'whatsapp' => ['WhatsApp', 'https://wa.me/?text=' . $title . '%20' . $url],
        'linkedin' => ['LinkedIn', 'https://www.linkedin.com/sharing/share-offsite/?url=' . $url],
        'facebook' => ['Facebook', 'https://www.facebook.com/sharer/sharer.php?u=' . $url],
        'x' => ['X', 'https://x.com/intent/post?url=' . $url . '&text=' . $title],
        'email' => [__('E-mail', 'project-theme'), 'mailto:?subject=' . $title . '&body=' . $url],
    ];
}

/* --------------------------------------------- Dados estruturados (post) */

add_action('wp_head', function () {
    // Plugin de SEO ativo gera o proprio BlogPosting/Article.
    if (!is_singular('post') || (function_exists('project_seo_plugin_active') && project_seo_plugin_active())) {
        return;
    }
    $post = get_queried_object();
    $logo = project_image_url(project_option('company_logo') ?: project_option('logo'));
    // Sem autor (importacao, usuario excluido, post criado por script): a
    // empresa assina - nunca "author": {"name": ""}, que e invalido.
    $author_name = trim((string) get_the_author_meta('display_name', (int) $post->post_author));
    $author = $author_name !== ''
        ? ['@type' => 'Person', 'name' => $author_name]
        : ['@type' => 'Organization', 'name' => get_bloginfo('name')];
    $data = [
        '@context' => 'https://schema.org',
        '@type' => 'BlogPosting',
        'headline' => wp_strip_all_tags(get_the_title($post)),
        'datePublished' => get_the_date('c', $post),
        'dateModified' => get_the_modified_date('c', $post),
        'author' => $author,
        'mainEntityOfPage' => get_permalink($post),
        'publisher' => array_filter([
            '@type' => 'Organization',
            'name' => get_bloginfo('name'),
            'logo' => $logo ? ['@type' => 'ImageObject', 'url' => $logo] : null,
        ]),
    ];
    if (has_post_thumbnail($post)) {
        $data['image'] = get_the_post_thumbnail_url($post, 'large');
    }
    $excerpt = wp_strip_all_tags(get_the_excerpt($post));
    if ($excerpt) {
        $data['description'] = $excerpt;
    }
    printf("<script type=\"application/ld+json\">%s</script>\n",
        wp_json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG));
}, 20);

/* Paginacao acessivel: o WordPress ja marca aria-current="page"; aqui o
   nome da navegacao e os rotulos. */
function project_posts_pagination() {
    the_posts_pagination([
        'aria_label' => __('Paginação dos posts', 'project-theme'),
        'mid_size' => 1,
        'prev_text' => __('Anterior', 'project-theme'),
        'next_text' => __('Próxima', 'project-theme'),
        'before_page_number' => '<span class="screen-reader-text">' . esc_html__('Página', 'project-theme') . ' </span>',
    ]);
}
