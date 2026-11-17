<?php
/**
 * Redes sociais (references/footer-social.md).
 *
 * - URLs na pagina de opcoes (social_<rede>), UMA fonte para header,
 *   rodape e contato. Nascem VAZIAS: o perfil nunca e inventado, e rede
 *   sem URL nao aparece (nada de link "#").
 * - Icones: SVG da Phosphor (MIT) em assets/icons/social/, inline e
 *   coloridos por currentColor; o admin pode trocar por um icone proprio
 *   (social_<rede>_icon, imagem da Midia).
 * - Dados estruturados Organization com sameAs (os perfis preenchidos).
 */

if (!defined('ABSPATH')) {
    exit;
}

function project_social_networks() {
    return [
        'instagram' => 'Instagram',
        'facebook' => 'Facebook',
        'linkedin' => 'LinkedIn',
        'youtube' => 'YouTube',
        'tiktok' => 'TikTok',
        'x' => 'X',
        'pinterest' => 'Pinterest',
        'threads' => 'Threads',
        'whatsapp' => 'WhatsApp',
        'telegram' => 'Telegram',
        'spotify' => 'Spotify',
    ];
}

/**
 * Ordem das redes = a da referencia (social.networks do Blueprint).
 * Ajuste aqui por projeto.
 */
function project_social_order() {
    return apply_filters('project_social_order', ['instagram', 'facebook', 'linkedin', 'youtube', 'whatsapp']);
}

/** Perfis preenchidos, na ordem da referencia: [rede => [label, url]]. */
function project_social_profiles(array $order = []) {
    $networks = project_social_networks();
    $out = [];
    foreach ($order ?: project_social_order() as $key) {
        if (!isset($networks[$key])) {
            continue;
        }
        $url = trim((string) project_option('social_' . $key));
        if ($key === 'whatsapp' && $url === '') {
            $url = project_whatsapp_href(project_option('company_whatsapp'), project_option('company_whatsapp_message'));
        }
        if ($url === '' || $url === '#' || !preg_match('#^https?://#i', $url)) {
            continue;   // sem URL valida: a rede nao aparece
        }
        $out[$key] = [$networks[$key], esc_url_raw($url)];
    }
    return $out;
}

/** SVG inline (aria-hidden) ou o icone proprio enviado no admin. */
function project_social_icon($key) {
    $custom = project_image_id(project_option('social_' . $key . '_icon'));
    if ($custom) {
        return wp_get_attachment_image($custom, 'thumbnail', false, ['alt' => '', 'class' => 'social-links__icon', 'aria-hidden' => 'true']);
    }
    static $cache = [];
    if (!isset($cache[$key])) {
        $file = get_template_directory() . '/assets/icons/social/' . sanitize_file_name($key) . '.svg';
        $svg = is_readable($file) ? (string) file_get_contents($file) : '';
        $cache[$key] = $svg ? preg_replace('/<svg\b/', '<svg class="social-links__icon" aria-hidden="true" focusable="false" width="1em" height="1em"', $svg, 1) : '';
    }
    return $cache[$key];
}

/*
 * Empresa (+ sameAs) e WebSite na Home: liga o site aos perfis oficiais e
 * da o nome do site ao Google. Tipo = PROJECT_SCHEMA_TYPE (functions.php):
 * LocalBusiness/subtipo leva o endereco do dado unico de contato. Plugin de
 * SEO ativo gera o proprio grafo - o tema nao duplica.
 */
add_action('wp_head', function () {
    if (!is_front_page() || (function_exists('project_seo_plugin_active') && project_seo_plugin_active())) {
        return;
    }
    $profiles = array_values(array_map(function ($p) { return $p[1]; }, project_social_profiles()));
    $profiles = array_values(array_filter($profiles, function ($u) { return stripos($u, 'wa.me') === false; }));
    $logo = project_image_url(project_option('company_logo') ?: project_option('logo'));
    $phone = project_phone_digits(project_option('company_phone'));
    $type = defined('PROJECT_SCHEMA_TYPE') && preg_match('/^[A-Za-z]+$/', PROJECT_SCHEMA_TYPE) ? PROJECT_SCHEMA_TYPE : 'Organization';
    $org = [
        '@type' => $type,
        '@id' => home_url('/#organization'),
        'name' => project_option('company_legal_name') ?: get_bloginfo('name'),
        'url' => home_url('/'),
        'logo' => $logo ?: null,
        'sameAs' => $profiles ?: null,
        'telephone' => $phone ? '+' . $phone : null,
        'email' => is_email((string) project_option('company_email')) ? project_option('company_email') : null,
        'taxID' => project_option('company_cnpj') ?: null,
    ];
    if ($type !== 'Organization') {
        // Endereco: texto unico do admin (company_address) ou as duas linhas.
        $address = trim((string) project_option('company_address'));
        if ($address === '') {
            $address = trim(implode(', ', array_filter([
                trim((string) project_option('company_address_line1')),
                trim((string) project_option('company_address_line2')),
            ])));
        }
        $org['address'] = $address !== ''
            ? ['@type' => 'PostalAddress', 'streetAddress' => wp_strip_all_tags($address), 'addressCountry' => 'BR']
            : null;
        $org['image'] = $logo ?: null;
    }
    $data = [
        '@context' => 'https://schema.org',
        '@graph' => [
            array_filter($org),
            [
                '@type' => 'WebSite',
                '@id' => home_url('/#website'),
                'url' => home_url('/'),
                'name' => get_bloginfo('name'),
                'inLanguage' => get_bloginfo('language'),
                'publisher' => ['@id' => home_url('/#organization')],
            ],
        ],
    ];
    printf("<script type=\"application/ld+json\">%s</script>\n",
        wp_json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_HEX_TAG));
}, 21);
