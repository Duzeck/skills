<?php
/**
 * Hero, cabecalho de pagina, faixa de chamada e barra de aviso
 * (references/hero-banners.md).
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Botoes do hero/faixa: [{label, target, style: primary|secondary}].
 * Sem rotulo ou sem destino real o botao NAO aparece (nunca "#").
 */
function project_buttons_html(array $buttons, $class = 'hero__actions') {
    $out = '';
    foreach ($buttons as $b) {
        $b = (array) $b;
        $label = trim((string) ($b['label'] ?? ''));
        $target = $b['target'] ?? '';
        if ($label === '' || $target === '' || $target === '#') {
            continue;
        }
        // Destino RESOLVIDO (whatsapp/telefone/email viram wa.me/tel:/mailto:);
        // sem dado cadastrado, o botao nao aparece (nunca href vazio).
        $url = project_target_url($target);
        if ($url === '' || $url === '#') {
            continue;
        }
        $style = ($b['style'] ?? 'primary') === 'secondary' ? 'secondary' : 'primary';
        $external = preg_match('#^https?://#i', $url) && strpos($url, home_url()) !== 0;
        $out .= sprintf(
            '<a class="button button--%s" href="%s"%s>%s%s</a>',
            $style,
            esc_url($url),
            $external ? ' target="_blank" rel="noopener"' : '',
            esc_html($label),
            $external ? '<span class="screen-reader-text"> ' . esc_html__('(abre em nova aba)', 'project-theme') . '</span>' : ''
        );
    }
    return $out ? sprintf('<div class="%s">%s</div>', esc_attr($class), $out) : '';
}

/**
 * Trilha de navegacao (breadcrumb) da pagina atual: [[rotulo, url|null], ...].
 * Paginas (com ancestrais), posts (blog > categoria > post), CPT (arquivo >
 * item), arquivos e busca. O ultimo item e a pagina atual (sem link).
 */
function project_breadcrumb_trail() {
    $trail = [[__('Início', 'project-theme'), home_url('/')]];
    if (is_front_page()) {
        return [];
    }
    if (is_home()) {
        $trail[] = [get_the_title((int) get_option('page_for_posts')), null];
    } elseif (is_page()) {
        foreach (array_reverse(get_post_ancestors(get_queried_object_id())) as $ancestor) {
            $trail[] = [get_the_title($ancestor), get_permalink($ancestor)];
        }
        $trail[] = [get_the_title(), null];
    } elseif (is_singular('post')) {
        $blog = (int) get_option('page_for_posts');
        if ($blog) {
            $trail[] = [get_the_title($blog), get_permalink($blog)];
        }
        $cats = get_the_category();
        if ($cats) {
            $trail[] = [$cats[0]->name, get_category_link($cats[0])];
        }
        $trail[] = [get_the_title(), null];
    } elseif (is_singular()) {
        $type = get_post_type_object(get_post_type());
        if ($type && $type->has_archive) {
            $trail[] = [$type->labels->name, get_post_type_archive_link($type->name)];
        }
        $trail[] = [get_the_title(), null];
    } elseif (is_search()) {
        /* translators: %s: termo */
        $trail[] = [sprintf(__('Busca: %s', 'project-theme'), get_search_query(false)), null];
    } elseif (is_archive()) {
        $trail[] = [wp_strip_all_tags(get_the_archive_title()), null];
    } elseif (is_404()) {
        $trail[] = [__('Página não encontrada', 'project-theme'), null];
    }
    return $trail;
}

/** <nav> da trilha + JSON-LD BreadcrumbList com os mesmos itens. */
function project_breadcrumb() {
    $trail = project_breadcrumb_trail();
    if (count($trail) < 2) {
        return '';
    }
    $items = '';
    $ld = [];
    foreach ($trail as $i => [$label, $url]) {
        $last = $i === count($trail) - 1;
        $items .= $last
            ? sprintf('<li><span aria-current="page">%s</span></li>', esc_html($label))
            : sprintf('<li><a href="%s">%s</a></li>', esc_url($url), esc_html($label));
        $ld[] = array_filter([
            '@type' => 'ListItem',
            'position' => $i + 1,
            'name' => wp_strip_all_tags($label),
            'item' => $last ? null : $url,   // o item atual pode omitir a URL
        ]);
    }
    $json = wp_json_encode(['@context' => 'https://schema.org', '@type' => 'BreadcrumbList', 'itemListElement' => $ld],
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG);
    return sprintf(
        '<nav class="breadcrumb" aria-label="%s" data-breadcrumb><ol role="list">%s</ol></nav><script type="application/ld+json">%s</script>',
        esc_attr__('Trilha de navegação', 'project-theme'),
        $items,
        $json
    );
}
