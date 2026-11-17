<?php
/**
 * Mapas (references/maps.md). Sem chave de API: embed do Google Maps por
 * endereco (ou o link "Incorporar mapa" colado no admin) ou OpenStreetMap
 * por coordenadas. O endereco vem SEMPRE da pagina de opcoes - a mesma
 * fonte do rodape/contato (dado global unico).
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Normaliza o que o admin colou no campo "mapa incorporado": aceita o
 * <iframe ...> inteiro do "Compartilhar > Incorporar um mapa" do Google ou
 * so a URL. So passa URL de embed de provedor conhecido (nada de iframe
 * arbitrario vindo de campo de texto).
 */
function project_map_embed_from_admin($value) {
    $value = trim((string) $value);
    if ($value === '') {
        return '';
    }
    if (stripos($value, '<iframe') !== false && preg_match('/\ssrc=["\']([^"\']+)["\']/i', $value, $m)) {
        $value = html_entity_decode($m[1]);
    }
    $allowed = '#^https://(www\.google\.com/maps/embed|maps\.google\.com/maps|www\.openstreetmap\.org/export/embed\.html)#i';
    return preg_match($allowed, $value) ? esc_url_raw($value) : '';
}

/**
 * URLs do mapa.
 *
 * @param array $args address, provider (google|openstreetmap), lat, lng, zoom, embed_url
 * @return array{embed:string, view:string, directions:string}
 */
function project_map_urls(array $args) {
    $a = array_merge([
        'address' => '',
        'provider' => 'google',
        'lat' => '',
        'lng' => '',
        'zoom' => 16,
        'embed_url' => '',
    ], $args);

    $address = trim(wp_strip_all_tags((string) $a['address']));
    $zoom = max(3, min(20, (int) $a['zoom']));
    $q = rawurlencode($address);
    $embed = project_map_embed_from_admin($a['embed_url']);

    if ($a['provider'] === 'openstreetmap' && is_numeric($a['lat']) && is_numeric($a['lng'])) {
        $lat = (float) $a['lat'];
        $lng = (float) $a['lng'];
        $d = 0.004;
        $embed = $embed ?: sprintf(
            'https://www.openstreetmap.org/export/embed.html?bbox=%F%%2C%F%%2C%F%%2C%F&layer=mapnik&marker=%F%%2C%F',
            $lng - $d, $lat - $d, $lng + $d, $lat + $d, $lat, $lng
        );
        $view = sprintf('https://www.openstreetmap.org/?mlat=%F&mlon=%F#map=%d/%F/%F', $lat, $lng, $zoom, $lat, $lng);
    } else {
        $embed = $embed ?: sprintf('https://maps.google.com/maps?q=%s&z=%d&output=embed', $q, $zoom);
        $view = 'https://www.google.com/maps/search/?api=1&query=' . $q;
    }

    return [
        'embed' => $embed,
        'view' => $view,
        // "Como chegar": Maps URLs oficiais do Google, sem chave; abre o app no celular.
        'directions' => $address !== '' ? 'https://www.google.com/maps/dir/?api=1&destination=' . $q : $view,
    ];
}
