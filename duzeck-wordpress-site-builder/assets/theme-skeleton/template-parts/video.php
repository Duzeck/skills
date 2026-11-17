<?php
/**
 * Video (references/videos.md) - um por entrada de videos[] do BLUEPRINT.yaml.
 *
 * kind = embed (YouTube/Vimeo): FACHADA - capa + botao play; o player so
 *   carrega no clique (youtube-nocookie / Vimeo dnt). Sem JS o botao e um
 *   link para o video no provedor.
 * kind = file: <video controls preload="none"> da Biblioteca de Midia, com
 *   capa e legenda (<track>) quando houver.
 * kind = background: video decorativo atras do conteudo (mudo, em loop),
 *   SEM atributo autoplay - o video.js so toca se o visitante nao pediu
 *   movimento reduzido, nao esta em economia de dados e a tela e >= 768px;
 *   pausa fora da tela; botao de pausa (WCAG 2.2.2). Senao fica a capa
 *   (<img>, que tambem e o LCP) e o arquivo nem e baixado.
 *
 * Uso:
 *   get_template_part('template-parts/video', null, [
 *       'id'       => 'home_video',                         // videos[].id
 *       'kind'     => 'embed',                              // embed | file | background
 *       'url'      => project_home('home_video_url'),       // embed
 *       'file'     => project_home('home_video_file'),      // file/background: anexo(s); array = varias fontes (webm, mp4)
 *       'captions' => project_home('home_video_captions'),  // file: anexo .vtt
 *       'poster'   => project_home('home_video_poster'),    // capa (anexo); obrigatoria
 *       'fallback' => 'video-capa.jpg',                     // recorte da referencia (provisorio)
 *       'title'    => project_home('home_video_title'),     // nome acessivel
 *       'duration' => project_home('home_video_duration'),  // opcional, ex.: 3:45
 *       'ratio'    => '16 / 9',
 *       'eager'    => false,                                // true se a capa for o LCP (hero)
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'kind' => 'embed',
    'url' => '',
    'file' => '',
    'captions' => '',
    'captions_lang' => 'pt-BR',
    'captions_label' => 'Português',
    'poster' => 0,
    'fallback' => '',
    'title' => '',
    'duration' => '',
    'ratio' => '16 / 9',
    'eager' => false,
    'class' => '',
], $args ?? []);

$title = trim(wp_strip_all_tags((string) $a['title']));
$frame_style = sprintf('--ratio: %s;', $a['ratio']);
$poster_args = [
    'ratio' => $a['ratio'],
    'fallback' => $a['fallback'],
    'alt' => '',
    'label' => __('Capa do vídeo', 'project-theme'),
    'class' => 'video__poster',
    'size' => 'large',
    'loading' => $a['eager'] ? 'eager' : 'lazy',
];
$admin_notice = function ($message) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="video-missing">%s</p>', esc_html($message));
    }
};
$sources = [];
foreach ((array) $a['file'] as $file) {
    $src = project_media_file_url($file);
    if ($src) {
        $sources[] = ['src' => $src, 'type' => wp_check_filetype(strtok($src, '?'))['type'] ?: 'video/mp4'];
    }
}
$root_class = trim('video video--' . $a['kind'] . ' ' . $a['class']);
?>
<?php if ($a['kind'] === 'embed') : ?>
    <?php
    $video = project_video_parse($a['url']);
    if (!$video) {
        $admin_notice(__('Vídeo sem URL válida do YouTube/Vimeo: preencha o campo no admin.', 'project-theme'));
        return;
    }
    /* translators: %s: titulo do video */
    $play_label = $title ? sprintf(__('Reproduzir vídeo: %s', 'project-theme'), $title) : __('Reproduzir vídeo', 'project-theme');
    wp_enqueue_script('project-video');
    ?>
    <div class="<?php echo esc_attr($root_class); ?>" data-video="<?php echo esc_attr($a['id']); ?>" data-video-kind="embed">
        <div class="video__frame" style="<?php echo esc_attr($frame_style); ?>">
            <div class="video__facade" data-video-facade>
                <?php project_media(project_image_id($a['poster']), $poster_args); ?>
                <a class="video__play" href="<?php echo esc_url($video['watch']); ?>" target="_blank" rel="noopener"
                    data-video-load data-video-src="<?php echo esc_url($video['embed']); ?>"
                    data-video-title="<?php echo esc_attr($title ?: $play_label); ?>">
                    <span class="video__play-icon" aria-hidden="true"></span>
                    <span class="screen-reader-text"><?php echo esc_html($play_label); ?></span>
                </a>
                <?php if ($a['duration']) : ?>
                    <span class="video__duration">
                        <span class="screen-reader-text"><?php esc_html_e('Duração:', 'project-theme'); ?></span>
                        <?php echo esc_html($a['duration']); ?>
                    </span>
                <?php endif; ?>
            </div>
        </div>
    </div>

<?php elseif ($a['kind'] === 'file') : ?>
    <?php
    if (!$sources) {
        $admin_notice(__('Vídeo sem arquivo: envie-o na Biblioteca de Mídia e selecione no admin.', 'project-theme'));
        return;
    }
    $poster_url = project_image_url($a['poster'] ?: $a['fallback'], 'large');
    $track = project_media_file_url($a['captions']);
    ?>
    <div class="<?php echo esc_attr($root_class); ?>" data-video="<?php echo esc_attr($a['id']); ?>" data-video-kind="file">
        <div class="video__frame" style="<?php echo esc_attr($frame_style); ?>">
            <video class="video__media" controls preload="none" playsinline
                <?php echo $poster_url ? 'poster="' . esc_url($poster_url) . '"' : ''; ?>
                <?php echo $title ? 'aria-label="' . esc_attr($title) . '"' : ''; ?>>
                <?php foreach ($sources as $s) : ?>
                    <source src="<?php echo esc_url($s['src']); ?>" type="<?php echo esc_attr($s['type']); ?>">
                <?php endforeach; ?>
                <?php if ($track) : ?>
                    <track kind="captions" src="<?php echo esc_url($track); ?>" srclang="<?php echo esc_attr($a['captions_lang']); ?>" label="<?php echo esc_attr($a['captions_label']); ?>" default>
                <?php endif; ?>
            </video>
        </div>
    </div>

<?php elseif ($a['kind'] === 'background') : ?>
    <?php
    if (!$sources) {
        $admin_notice(__('Vídeo de fundo sem arquivo: envie-o na Biblioteca de Mídia e selecione no admin.', 'project-theme'));
        return;
    }
    wp_enqueue_script('project-video');
    ?>
    <div class="<?php echo esc_attr($root_class); ?>" data-video="<?php echo esc_attr($a['id']); ?>" data-video-kind="background"
        data-label-pause="<?php echo esc_attr__('Pausar vídeo de fundo', 'project-theme'); ?>"
        data-label-play="<?php echo esc_attr__('Reproduzir vídeo de fundo', 'project-theme'); ?>">
        <div class="video__frame">
            <?php project_media(project_image_id($a['poster']), $poster_args); ?>
            <?php /* Sem src: nada e baixado ate o video.js decidir que pode tocar. */ ?>
            <video class="video__media" muted loop playsinline preload="none" aria-hidden="true" tabindex="-1" data-bg-video>
                <?php foreach ($sources as $s) : ?>
                    <source data-src="<?php echo esc_url($s['src']); ?>" type="<?php echo esc_attr($s['type']); ?>">
                <?php endforeach; ?>
            </video>
        </div>
        <button type="button" class="video__toggle" data-video-toggle hidden>
            <span class="video__toggle-icon" aria-hidden="true"></span>
            <span class="screen-reader-text" data-video-toggle-label><?php esc_html_e('Pausar vídeo de fundo', 'project-theme'); ?></span>
        </button>
    </div>
<?php endif; ?>
