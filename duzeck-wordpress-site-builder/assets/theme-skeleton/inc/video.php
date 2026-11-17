<?php
/**
 * Videos (references/videos.md). URL colada no admin (YouTube/Vimeo) ->
 * embed de privacidade reforcada; arquivo proprio -> <video>.
 */

if (!defined('ABSPATH')) {
    exit;
}

/**
 * Interpreta a URL de video que o admin colou (qualquer formato comum).
 *
 * YouTube: watch?v=, youtu.be/, /shorts/, /embed/, /live/ -> youtube-nocookie.com
 * Vimeo:   vimeo.com/123, vimeo.com/123/hash, player.vimeo.com/video/123 -> dnt=1
 * Outro dominio -> null (nada de iframe arbitrario vindo de campo de texto).
 *
 * @return array{provider:string, id:string, embed:string, watch:string}|null
 */
function project_video_parse($url) {
    $url = trim((string) $url);
    if ($url === '') {
        return null;
    }
    if (preg_match('~^https?://(?:(?:www\.|m\.)?youtube(?:-nocookie)?\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})~', $url, $m)) {
        $id = $m[1];
        return [
            'provider' => 'youtube',
            'id' => $id,
            // autoplay=1: o clique na fachada ja foi o "play"; rel=0: sugestoes so do mesmo canal.
            'embed' => 'https://www.youtube-nocookie.com/embed/' . $id . '?autoplay=1&rel=0&playsinline=1',
            'watch' => 'https://www.youtube.com/watch?v=' . $id,
        ];
    }
    if (preg_match('~^https?://(?:www\.|player\.)?vimeo\.com/(?:video/)?(\d+)(?:/([0-9a-f]+))?~', $url, $m)) {
        $id = $m[1];
        $hash = !empty($m[2]) ? '&h=' . $m[2] : '';
        return [
            'provider' => 'vimeo',
            'id' => $id,
            'embed' => 'https://player.vimeo.com/video/' . $id . '?autoplay=1&dnt=1' . $hash,
            'watch' => 'https://vimeo.com/' . $id,
        ];
    }
    return null;
}

/** URL de arquivo de midia (ID do anexo, array do ACF ou nome em assets/). */
function project_media_file_url($value) {
    if (is_array($value)) {
        $value = $value['ID'] ?? $value['id'] ?? ($value['url'] ?? '');
    }
    if (is_numeric($value) && (int) $value > 0) {
        return (string) wp_get_attachment_url((int) $value);
    }
    if (is_string($value) && $value !== '') {
        return preg_match('~^https?://~', $value) ? $value : get_template_directory_uri() . '/assets/video/' . ltrim($value, '/');
    }
    return '';
}
