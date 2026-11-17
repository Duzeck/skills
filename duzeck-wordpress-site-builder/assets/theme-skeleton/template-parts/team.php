<?php
/**
 * Equipe (references/team-stats.md) - um por team[] do Blueprint.
 *
 * Pessoas da referencia quase sempre sao foto de banco de imagem com nome
 * inventado: real so com nomes, fotos e AUTORIZACAO de uso de imagem de
 * cada pessoa (team[].content_source user + consent). demo => true fica
 * oculto em producao (inc/social-proof.php).
 *
 * - Nome como titulo do card (h3); foto alt="" (o nome esta escrito ao lado).
 * - Registro profissional (CRM, OAB, CREA...) em texto - nunca inventado;
 *   obrigatorio quando o Blueprint diz que o setor exige.
 * - Bio: 'visible' (no card) ou 'collapsed' (<details> "Sobre <nome>") -
 *   NUNCA so no hover (teclado e toque nao alcancam).
 * - Redes: "LinkedIn de Ana Lima (abre em nova aba)" para leitor de tela.
 *
 * Uso:
 *   get_template_part('template-parts/team', null, [
 *       'id'     => 'about_team',                 // team[].id
 *       'items'  => $pessoas,                     // [name, role, photo, bio, registration, social[{url, network?}], url]
 *       'bio'    => 'collapsed',                  // visible | collapsed | hidden
 *       'ratio'  => '4 / 5',                      // proporcao das fotos na referencia
 *       'heading_level' => 3,
 *       'demo'   => false,
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'items' => [],
    'layout' => 'grid',
    'bio' => 'visible',
    'ratio' => '4 / 5',
    'heading_level' => 3,
    'demo' => false,
    'class' => '',
], $args ?? []);

if (project_demo_blocked($a['demo'])) {
    project_demo_notice(__('Equipe', 'project-theme'));
    return;
}
$items = array_values(array_filter((array) $a['items'], function ($p) {
    return !empty(((array) $p)['name']);
}));
if (!$items) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="team-missing">%s</p>', esc_html__('Equipe sem conteúdo: cadastre no admin.', 'project-theme'));
    }
    return;
}
$level = min(6, max(2, (int) $a['heading_level']));
$networks = [
    'linkedin' => 'LinkedIn', 'instagram' => 'Instagram', 'facebook' => 'Facebook', 'x' => 'X',
    'twitter' => 'X', 'youtube' => 'YouTube', 'tiktok' => 'TikTok', 'github' => 'GitHub',
    'lattes' => 'Currículo Lattes', 'whatsapp' => 'WhatsApp', 'site' => 'Site',
];
$network_of = function ($social) use ($networks) {
    $key = strtolower((string) ($social['network'] ?? ''));
    if (!isset($networks[$key])) {
        $host = (string) wp_parse_url((string) ($social['url'] ?? ''), PHP_URL_HOST);
        $key = 'site';
        foreach (['linkedin', 'instagram', 'facebook', 'youtube', 'tiktok', 'github', 'lattes', 'whatsapp'] as $n) {
            if (stripos($host, $n) !== false || ($n === 'whatsapp' && stripos($host, 'wa.me') !== false)) {
                $key = $n;
                break;
            }
        }
        if (preg_match('/(^|\.)(x|twitter)\.com$/i', $host)) {
            $key = 'x';
        }
    }
    return [$key, $networks[$key]];
};
?>
<ul class="<?php echo esc_attr(trim('team team--' . $a['layout'] . ' ' . $a['class'])); ?>" role="list"
    data-team="<?php echo esc_attr($a['id']); ?>"<?php echo $a['demo'] ? ' data-demo="true"' : ''; ?>>
    <?php foreach ($items as $i => $person) : ?>
        <?php
        $person = (array) $person;
        $name = trim(wp_strip_all_tags((string) $person['name']));
        $heading_id = sanitize_title($a['id'] . '-' . $name);
        $profile = trim((string) ($person['url'] ?? ''));
        ?>
        <li class="team-member">
            <article class="team-member__card" aria-labelledby="<?php echo esc_attr($heading_id); ?>">
                <?php
                project_media(project_image_id($person['photo'] ?? 0), [
                    'ratio' => $a['ratio'],
                    'fallback' => is_string($person['photo'] ?? null) && !is_numeric($person['photo']) ? $person['photo'] : '',
                    'alt' => '',
                    'label' => __('Foto', 'project-theme'),
                    'class' => 'team-member__photo',
                    'size' => 'medium_large',
                ]);
                ?>
                <<?php echo 'h' . $level; ?> class="team-member__name" id="<?php echo esc_attr($heading_id); ?>">
                    <?php if ($profile) : ?>
                        <a href="<?php echo esc_url(project_target_url($profile)); ?>"><?php echo esc_html($name); ?></a>
                    <?php else : ?>
                        <?php echo esc_html($name); ?>
                    <?php endif; ?>
                </<?php echo 'h' . $level; ?>>
                <?php if (!empty($person['role'])) : ?>
                    <p class="team-member__role"><?php echo esc_html($person['role']); ?></p>
                <?php endif; ?>
                <?php if (!empty($person['registration'])) : ?>
                    <p class="team-member__registration"><?php echo esc_html($person['registration']); ?></p>
                <?php endif; ?>
                <?php if (!empty($person['bio']) && $a['bio'] !== 'hidden') : ?>
                    <?php if ($a['bio'] === 'collapsed') : ?>
                        <details class="team-member__bio">
                            <summary>
                                <?php
                                /* translators: %s: nome da pessoa */
                                printf(esc_html__('Sobre %s', 'project-theme'), esc_html($name));
                                ?>
                            </summary>
                            <?php echo wp_kses_post(wpautop($person['bio'])); ?>
                        </details>
                    <?php else : ?>
                        <div class="team-member__bio"><?php echo wp_kses_post(wpautop($person['bio'])); ?></div>
                    <?php endif; ?>
                <?php endif; ?>
                <?php $socials = array_filter((array) ($person['social'] ?? []), function ($s) { return !empty(((array) $s)['url']); }); ?>
                <?php if ($socials) : ?>
                    <ul class="team-member__social" role="list">
                        <?php foreach ($socials as $social) : ?>
                            <?php [$key, $label] = $network_of((array) $social); ?>
                            <li>
                                <a href="<?php echo esc_url($social['url']); ?>" target="_blank" rel="noopener" class="team-member__social-link">
                                    <span class="team-member__social-icon team-member__social-icon--<?php echo esc_attr($key); ?>" aria-hidden="true"></span>
                                    <span class="screen-reader-text">
                                        <?php
                                        /* translators: 1: rede (LinkedIn), 2: nome da pessoa */
                                        printf(esc_html__('%1$s de %2$s (abre em nova aba)', 'project-theme'), esc_html($label), esc_html($name));
                                        ?>
                                    </span>
                                </a>
                            </li>
                        <?php endforeach; ?>
                    </ul>
                <?php endif; ?>
            </article>
        </li>
    <?php endforeach; ?>
</ul>
