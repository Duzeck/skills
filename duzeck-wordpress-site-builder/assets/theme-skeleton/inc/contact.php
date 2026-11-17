<?php
/**
 * Links de contato a partir do dado UNICO da pagina de opcoes
 * (references/footer-social.md). O texto mostrado e o do admin; o link e
 * normalizado: tel:+55..., https://wa.me/55..., mailto:, mapa.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** Digitos com DDI 55 quando o numero brasileiro vem sem ele. null se invalido. */
function project_phone_digits($phone) {
    $digits = preg_replace('/\D+/', '', (string) $phone);
    $digits = ltrim($digits, '0');                       // 0 de discagem / operadora
    if ($digits === '') {
        return null;
    }
    if (strlen($digits) === 10 || strlen($digits) === 11) {  // DDD + numero
        $digits = '55' . $digits;
    }
    return (strlen($digits) >= 12 && strlen($digits) <= 15) ? $digits : null;
}

/** tel:+5562999999999 (toca a ligacao no celular). */
function project_phone_href($phone) {
    $d = project_phone_digits($phone);
    return $d ? 'tel:+' . $d : '';
}

/** https://wa.me/5562999999999?text=... (mensagem inicial opcional, do admin). */
function project_whatsapp_href($phone, $message = '') {
    $d = project_phone_digits($phone);
    if (!$d) {
        return '';
    }
    $message = trim((string) $message);
    return 'https://wa.me/' . $d . ($message !== '' ? '?text=' . rawurlencode($message) : '');
}

function project_email_href($email) {
    $email = sanitize_email((string) $email);
    return is_email($email) ? 'mailto:' . $email : '';
}

/** Endereco -> abre no app de mapas (Maps URLs oficiais, sem chave). */
function project_address_href($address) {
    $address = trim(wp_strip_all_tags((string) $address));
    return $address !== '' ? 'https://www.google.com/maps/search/?api=1&query=' . rawurlencode($address) : '';
}
