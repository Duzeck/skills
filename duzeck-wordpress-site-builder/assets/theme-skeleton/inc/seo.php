<?php
/**
 * SEO basico de cada pagina (references/security-seo.md).
 *
 * Editavel no admin (caixa "SEO e compartilhamento" em paginas, posts e
 * CPTs publicos): titulo na busca, descricao, imagem ao compartilhar e
 * "esconder dos buscadores". Imagem padrao de compartilhamento em
 * Configuracoes do Site. A migracao do projeto preenche as descricoes
 * aprovadas no Blueprint (seo.pages) - reserva em inc/content-defaults.php:
 *   home_seo_description, page_<slug>_seo_description.
 *
 * Saida no <head>: meta description, Open Graph, Twitter card, canonico das
 * listagens (o core ja imprime o das paginas/posts) e robots (noindex da
 * pagina marcada + homologacao inteira). O JSON-LD da empresa fica em
 * inc/social.php (Organization/LocalBusiness + WebSite).
 *
 * Plugin de SEO ativo (Yoast, Rank Math, SEOPress, AIOSEO, The SEO
 * Framework): o tema se cala inteiro - descricao/og:title em dobro
 * confundem buscadores e redes sociais.
 */

if (!defined('ABSPATH')) {
    exit;
}

function project_seo_plugin_active() {
    return defined('WPSEO_VERSION') || defined('RANK_MATH_VERSION') || defined('SEOPRESS_VERSION')
        || defined('AIOSEO_VERSION') || defined('THE_SEO_FRAMEWORK_VERSION');
}

/* Recorte das redes sociais (1200x630, proporcao 1,91:1). */
add_action('after_setup_theme', function () {
    add_image_size('project-share', 1200, 630, true);
});

/* ------------------------------------------------------- Campos do admin */

add_action('init', function () {
    // init 20: os CPTs (inc/post-types.php, init 10) ja existem.
    if (!function_exists('acf_add_local_field_group')) {
        return;
    }
    $types = array_values(array_diff(get_post_types(['public' => true]), ['attachment']));
    // Com plugin de SEO, os campos da pagina sao os do plugin; a politica de
    // robos de IA (robots.txt) continua no tema.
    if (!project_seo_plugin_active()) acf_add_local_field_group([
        'key' => 'group_project_seo',
        'title' => 'SEO e compartilhamento',
        'menu_order' => 90,
        'fields' => [
            [
                'key' => 'field_project_seo_title',
                'name' => 'seo_title',
                'label' => 'Título na busca',
                'type' => 'text',
                'maxlength' => 70,
                'instructions' => 'Opcional. Vazio = título da página + nome do site. Até 60 caracteres.',
            ],
            [
                'key' => 'field_project_seo_description',
                'name' => 'seo_description',
                'label' => 'Descrição na busca',
                'type' => 'textarea',
                'rows' => 3,
                'maxlength' => 160,
                'new_lines' => '',
                'instructions' => 'Texto que aparece abaixo do título no Google e ao compartilhar o link. Entre 120 e 160 caracteres, diferente em cada página.',
            ],
            [
                'key' => 'field_project_seo_image',
                'name' => 'seo_image',
                'label' => 'Imagem ao compartilhar',
                'type' => 'image',
                'return_format' => 'id',
                'preview_size' => 'medium',
                'mime_types' => 'jpg,jpeg,png,webp',
                'instructions' => '1200 × 630 px. Vazio = imagem destacada ou do topo da página; senão, a imagem padrão (Configurações do Site).',
            ],
            [
                'key' => 'field_project_seo_noindex',
                'name' => 'seo_noindex',
                'label' => 'Esconder dos buscadores',
                'type' => 'true_false',
                'ui' => 1,
                'instructions' => 'Só para páginas que não devem aparecer no Google (ex.: "obrigado pelo contato"). A página sai também do sitemap.',
            ],
        ],
        'location' => array_map(function ($type) {
            return [['param' => 'post_type', 'operator' => '==', 'value' => $type]];
        }, $types),
    ]);
    if (function_exists('acf_add_options_page')) {
        acf_add_local_field_group([
            'key' => 'group_project_seo_options',
            'title' => 'SEO e compartilhamento',
            'menu_order' => 90,
            'fields' => array_slice([[
                'key' => 'field_project_seo_ai_crawlers',
                'name' => 'seo_ai_crawlers',
                'label' => 'Robôs de inteligência artificial',
                'type' => 'select',
                'choices' => [
                    'allow' => 'Liberar todos (o conteúdo pode treinar IAs e aparecer nas respostas delas)',
                    'block_training' => 'Bloquear treinamento de IA, manter nas buscas com IA (ChatGPT, Perplexity, Claude)',
                    'block_all' => 'Bloquear todos os robôs de IA (o site não aparece nas respostas das IAs)',
                ],
                'default_value' => defined('PROJECT_AI_CRAWLERS') ? PROJECT_AI_CRAWLERS : 'allow',
                'instructions' => 'Vale para o robots.txt do site. Não afeta o Google nem o Bing comuns.',
            ], [
                'key' => 'field_project_seo_default_image',
                'name' => 'seo_default_image',
                'label' => 'Imagem padrão ao compartilhar',
                'type' => 'image',
                'return_format' => 'id',
                'preview_size' => 'medium',
                'mime_types' => 'jpg,jpeg,png,webp',
                'instructions' => '1200 × 630 px. Usada quando a página não tem imagem própria (WhatsApp, Facebook, LinkedIn).',
            ]], 0, project_seo_plugin_active() ? 1 : 2),
            'location' => [[['param' => 'options_page', 'operator' => '==', 'value' => 'global-settings']]],
        ]);
    }
}, 20);

/* ------------------------------------------------------------ robots.txt */

/*
 * Robos de IA (Blueprint seo.ai_crawlers; Configuracoes do Site > SEO e
 * compartilhamento). Lista revisada em 2026-11 - references/security-seo.md
 * secao 4 (mantenha igual a AI_TRAINING_BOTS/AI_SEARCH_BOTS de
 * scripts/capture_site.py).
 *   treino: coletam conteudo para treinar modelos;
 *   busca:  buscam/abrem a pagina para responder um usuario (citam o site).
 * Google-Extended so controla o uso pelo Gemini - nao tira o site da busca
 * do Google nem do AI Overviews (esses usam o Googlebot).
 */
function project_ai_bots() {
    return [
        'training' => ['GPTBot', 'ClaudeBot', 'anthropic-ai', 'Google-Extended', 'Applebot-Extended', 'CCBot',
                       'Bytespider', 'meta-externalagent', 'cohere-training-data-crawler', 'Diffbot'],
        'search' => ['OAI-SearchBot', 'ChatGPT-User', 'Claude-SearchBot', 'Claude-User', 'PerplexityBot',
                     'Perplexity-User', 'DuckAssistBot', 'meta-externalfetcher'],
    ];
}

function project_ai_crawlers_policy() {
    $policy = (string) project_option('seo_ai_crawlers');
    if (!in_array($policy, ['allow', 'block_training', 'block_all'], true)) {
        $policy = defined('PROJECT_AI_CRAWLERS') ? PROJECT_AI_CRAWLERS : 'allow';
    }
    return $policy;
}

/* O WordPress gera /robots.txt virtual (sem arquivo fisico na raiz - um
   robots.txt fisico anula este filtro). "Evitar mecanismos de busca"
   (Leitura) nao mexe no robots.txt desde o WP 5.3 - vira noindex nas
   paginas (a captura aponta); a politica de IA vale do mesmo jeito. */
add_filter('robots_txt', function ($output) {
    $policy = project_ai_crawlers_policy();
    $bots = project_ai_bots();
    $blocked = $policy === 'block_all' ? array_merge($bots['training'], $bots['search'])
        : ($policy === 'block_training' ? $bots['training'] : []);
    $lines = ["", "# Robos de IA: {$policy} (Configuracoes do Site > SEO e compartilhamento)"];
    if ($blocked) {
        foreach ($blocked as $bot) {
            $lines[] = 'User-agent: ' . $bot;
        }
        $lines[] = 'Disallow: /';
    }
    // Content-Signal (contentsignals.org): a mesma politica dita em palavras,
    // para quem le a intencao e nao so o nome do robo. Vai no grupo
    // "User-agent: *" do core (antes da primeira linha em branco).
    $signal = 'Content-Signal: search=yes, ai-input=' . ($policy === 'block_all' ? 'no' : 'yes')
        . ', ai-train=' . ($policy === 'allow' ? 'yes' : 'no');
    $output = rtrim($output);
    $cut = strpos($output, "\n\n");
    $output = $cut === false ? $output . "\n" . $signal
        : substr($output, 0, $cut) . "\n" . $signal . substr($output, $cut);
    return $output . "\n" . implode("\n", $lines) . "\n";
}, 20);

/* ------------------------------------------------------- Dados da pagina */

/** Texto de uma linha, sem HTML, cortado em palavra inteira. */
function project_seo_clean($text, $max = 160) {
    $text = trim(preg_replace('/\s+/u', ' ', wp_strip_all_tags((string) $text)));
    if (mb_strlen($text) <= $max) {
        return $text;
    }
    $cut = mb_substr($text, 0, $max - 1);
    $space = mb_strrpos($cut, ' ');
    return rtrim($space > $max * 0.6 ? mb_substr($cut, 0, $space) : $cut, " ,.;:-") . '…';
}

/** Titulo, descricao, URL canonica, imagem e robots da pagina atual. */
function project_seo_context() {
    static $ctx = null;
    if ($ctx !== null) {
        return $ctx;
    }
    $ctx = ['title' => wp_get_document_title(), 'description' => '', 'url' => '', 'image' => 0,
            'image_fallback' => '', 'type' => 'website', 'noindex' => false, 'post' => null];
    $paged = max(1, (int) get_query_var('paged'));

    $id = 0;
    if (is_singular()) {
        $id = get_queried_object_id();
    } elseif (is_home() && get_option('page_for_posts')) {
        $id = (int) get_option('page_for_posts');
    }

    if ($id) {
        $post = get_post($id);
        $ctx['post'] = $post;
        $is_front = (int) get_option('page_on_front') === $id;
        $default_key = $is_front ? 'home_seo_description' : 'page_' . $post->post_name . '_seo_description';
        $ctx['description'] = project_field('seo_description', $id)
            ?: project_default($default_key)
            ?: (has_excerpt($id) ? get_the_excerpt($id) : '')
            ?: ($is_front ? project_home('home_hero_text') : project_page_field('page_hero_text', $id));
        if (!$is_front && !is_home()) {
            $ctx['title'] = project_field('seo_title', $id) ?: get_the_title($id);
        }
        $ctx['url'] = is_home() ? get_pagenum_link($paged) : get_permalink($id);
        $ctx['image'] = project_image_id(project_field('seo_image', $id)) ?: (int) get_post_thumbnail_id($id);
        if (!$ctx['image']) {
            $hero = $is_front ? project_home('home_hero_image') : project_page_field('page_hero_image', $id);
            $ctx['image'] = project_image_id($hero);
            $ctx['image_fallback'] = $ctx['image'] ? '' : project_image_url($hero);
        }
        $ctx['type'] = is_singular('post') ? 'article' : 'website';
        $ctx['noindex'] = (bool) project_field('seo_noindex', $id);
    } elseif (is_category() || is_tag() || is_tax()) {
        $term = get_queried_object();
        $ctx['description'] = term_description($term);
        $ctx['url'] = $paged > 1 ? get_pagenum_link($paged) : get_term_link($term);
    } elseif (is_post_type_archive()) {
        $type = get_post_type_object(get_query_var('post_type'));
        $ctx['description'] = $type ? $type->description : '';
        $ctx['url'] = $paged > 1 ? get_pagenum_link($paged) : get_post_type_archive_link($type ? $type->name : '');
    }

    $ctx['description'] = project_seo_clean($ctx['description'] ?: get_bloginfo('description'));
    $ctx['title'] = project_seo_clean($ctx['title'], 90);
    if (!$ctx['image']) {
        $ctx['image'] = project_image_id(project_option('seo_default_image'));
        if (!$ctx['image'] && !$ctx['image_fallback']) {
            $ctx['image_fallback'] = project_image_url(project_option('seo_default_image'));
        }
    }
    $ctx = apply_filters('project_seo_context', $ctx);
    return $ctx;
}

/* ------------------------------------------------------------ <head> */

add_filter('pre_get_document_title', function ($title) {
    if (project_seo_plugin_active() || !is_singular()) {
        return $title;
    }
    $custom = trim((string) project_field('seo_title', get_queried_object_id()));
    return $custom !== '' ? $custom : $title;
});

add_filter('wp_robots', function ($robots) {
    if (project_seo_plugin_active()) {
        return $robots;
    }
    // Homologacao inteira fora do Google (copia publica do site).
    $staging = function_exists('wp_get_environment_type') && wp_get_environment_type() === 'staging';
    if ($staging || ((is_singular() || is_home()) && project_seo_context()['noindex'])) {
        $robots['noindex'] = true;
        $robots['follow'] = true;
        unset($robots['max-image-preview']);
    }
    return $robots;
});

/* Pagina marcada "esconder dos buscadores" sai tambem do sitemap. */
add_filter('wp_sitemaps_posts_query_args', function ($args) {
    if (project_seo_plugin_active()) {
        return $args;
    }
    $clause = ['relation' => 'OR',
               ['key' => 'seo_noindex', 'compare' => 'NOT EXISTS'],
               ['key' => 'seo_noindex', 'value' => '1', 'compare' => '!=']];
    $mq = (array) ($args['meta_query'] ?? []);
    $args['meta_query'] = $mq ? ['relation' => 'AND', $mq, $clause] : [$clause];
    return $args;
}, 20);

add_action('wp_head', function () {
    if (project_seo_plugin_active() || is_404() || is_search()) {
        return;
    }
    $ctx = project_seo_context();
    $tags = [];
    $meta = function ($attr, $key, $value) use (&$tags) {
        $value = trim((string) $value);
        if ($value !== '') {
            $tags[] = sprintf('<meta %s="%s" content="%s">', $attr, esc_attr($key), esc_attr($value));
        }
    };
    $meta('name', 'description', $ctx['description']);
    // Canonico: o core (rel_canonical) ja imprime em paginas/posts.
    if ($ctx['url'] && !is_singular()) {
        $tags[] = sprintf('<link rel="canonical" href="%s">', esc_url($ctx['url']));
    }
    $url = $ctx['url'] ?: (is_singular() ? wp_get_canonical_url() : '');
    $meta('property', 'og:locale', str_replace('-', '_', get_bloginfo('language')));
    $meta('property', 'og:type', $ctx['type']);
    $meta('property', 'og:site_name', get_bloginfo('name'));
    $meta('property', 'og:title', $ctx['title']);
    $meta('property', 'og:description', $ctx['description']);
    $meta('property', 'og:url', $url);

    $image = '';
    if ($ctx['image']) {
        $src = wp_get_attachment_image_src($ctx['image'], 'project-share');
        if ($src) {
            $image = $src[0];
            $meta('property', 'og:image', $src[0]);
            $meta('property', 'og:image:width', $src[1]);
            $meta('property', 'og:image:height', $src[2]);
            $meta('property', 'og:image:alt', get_post_meta($ctx['image'], '_wp_attachment_image_alt', true));
        }
    } elseif ($ctx['image_fallback']) {
        $image = $ctx['image_fallback'];
        $meta('property', 'og:image', $image);
    }
    $meta('name', 'twitter:card', $image ? 'summary_large_image' : 'summary');
    if ($ctx['type'] === 'article' && $ctx['post']) {
        $meta('property', 'article:published_time', get_the_date('c', $ctx['post']));
        $meta('property', 'article:modified_time', get_the_modified_date('c', $ctx['post']));
    }
    echo implode("\n", $tags) . "\n";
}, 2);
