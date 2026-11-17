<?php
/**
 * Acordeoes, FAQ e abas (references/disclosures.md).
 * Helpers compartilhados por template-parts/accordion.php e tabs.php.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** id estavel de item/aba para link direto (#<grupo>-<titulo>). */
function project_disclosure_anchor($group, $title, $index) {
    $slug = sanitize_title(wp_strip_all_tags((string) $title));
    return sanitize_title($group) . '-' . ($slug !== '' ? $slug : (string) ($index + 1));
}

/** Normaliza linhas do repeater: aceita ['title','content'] ou as chaves prefixadas do Blueprint. */
function project_disclosure_items($rows, $title_key = 'title', $content_key = 'content') {
    $items = [];
    foreach ((array) $rows as $row) {
        $row = (array) $row;
        $title = trim((string) ($row[$title_key] ?? $row['title'] ?? ''));
        $content = (string) ($row[$content_key] ?? $row['content'] ?? '');
        if ($title !== '') {
            $items[] = ['title' => $title, 'content' => $content];
        }
    }
    return $items;
}

/**
 * Dados estruturados FAQPage (schema.org) a partir das MESMAS perguntas do
 * admin - nunca um texto paralelo. Acumula de todos os FAQs da pagina e
 * imprime um unico JSON-LD no rodape.
 * Obs.: desde 2023 o Google so exibe o resultado rico de FAQ para sites
 * governamentais e de saude; o markup continua valido (outros buscadores,
 * assistentes), mas nao prometa o destaque ao cliente.
 */
function project_faq_schema_add(array $items) {
    $GLOBALS['project_faq_schema'] = array_merge($GLOBALS['project_faq_schema'] ?? [], $items);
}

function project_faq_schema_print() {
    $items = $GLOBALS['project_faq_schema'] ?? [];
    if (!$items) {
        return;
    }
    $allowed = ['a' => ['href' => true], 'br' => [], 'p' => [], 'ul' => [], 'ol' => [], 'li' => [], 'strong' => [], 'em' => [], 'b' => [], 'i' => []];
    $data = [
        '@context' => 'https://schema.org',
        '@type' => 'FAQPage',
        'mainEntity' => array_map(function ($item) use ($allowed) {
            return [
                '@type' => 'Question',
                'name' => wp_strip_all_tags($item['title']),
                'acceptedAnswer' => ['@type' => 'Answer', 'text' => trim(wp_kses($item['content'], $allowed))],
            ];
        }, $items),
    ];
    printf(
        "<script type=\"application/ld+json\">%s</script>\n",
        wp_json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG)
    );
}
add_action('wp_footer', 'project_faq_schema_print', 5);
