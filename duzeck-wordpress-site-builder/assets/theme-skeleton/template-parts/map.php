<?php
/**
 * Mapa com "fachada" (references/maps.md) - um por entrada de maps[] do
 * BLUEPRINT.yaml.
 *
 * load = click (padrao): mostra a imagem da fachada (estatica, da Midia) e
 *   o botao "Carregar mapa"; o iframe do provedor so entra no clique.
 *   Por que: o embed carrega ~1 MB de scripts de terceiros e grava cookies
 *   do provedor - sem o clique, nada disso acontece sem o visitante pedir
 *   (LGPD) e a pagina nao paga o custo no carregamento.
 *   Sem JS o botao e um link que abre o mapa numa nova aba.
 * load = auto: iframe direto, com loading="lazy" - so com decisao aprovada
 *   no Blueprint (ex.: banner de consentimento de cookies ja existe).
 *
 * Uso:
 *   get_template_part('template-parts/map', null, [
 *       'id'         => 'contact_map',                          // maps[].id
 *       'address'    => project_option('company_address'),      // fonte unica
 *       'embed_url'  => project_option('company_map_embed'),    // opcional
 *       'facade'     => project_option('company_map_image'),    // imagem estatica
 *       'fallback'   => 'mapa-contato.jpg',                     // recorte da referencia
 *       'ratio'      => '16 / 9',                               // maps[].aspect_ratio
 *       'provider'   => 'google',                               // google | openstreetmap
 *       'directions' => true,                                   // link "Como chegar"
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'address' => '',
    'embed_url' => '',
    'facade' => 0,
    'fallback' => '',
    'ratio' => '16 / 9',
    'provider' => 'google',
    'lat' => '',
    'lng' => '',
    'zoom' => 16,
    'load' => 'click',
    'directions' => true,
    'class' => '',
], $args ?? []);

$address = trim(wp_strip_all_tags((string) $a['address']));
if ($address === '' && !($a['lat'] && $a['lng'])) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="map-missing">%s</p>', esc_html__('Mapa sem endereço: preencha o endereço em Configurações do Site.', 'project-theme'));
    }
    return;
}

$urls = project_map_urls($a);
/* translators: %s: endereco */
$title = sprintf(__('Mapa: %s', 'project-theme'), $address);
$provider_name = $a['provider'] === 'openstreetmap' ? 'OpenStreetMap' : 'Google Maps';
$style = sprintf('--ratio: %s;', $a['ratio']);
?>
<div class="<?php echo esc_attr(trim('map ' . $a['class'])); ?>" data-map="<?php echo esc_attr($a['id']); ?>"
    data-map-load-mode="<?php echo $a['load'] === 'auto' ? 'auto' : 'click'; ?>">
    <div class="map__frame" style="<?php echo esc_attr($style); ?>">
        <?php if ($a['load'] === 'auto') : ?>
            <iframe class="map__iframe" src="<?php echo esc_url($urls['embed']); ?>" title="<?php echo esc_attr($title); ?>"
                loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
        <?php else : ?>
            <div class="map__facade" data-map-facade>
                <?php
                project_media(project_image_id($a['facade']), [
                    'ratio' => $a['ratio'],
                    'fallback' => $a['fallback'],
                    'alt' => '',
                    'label' => __('Mapa', 'project-theme'),
                    'class' => 'map__image',
                ]);
                ?>
                <div class="map__overlay">
                    <a class="map__load" href="<?php echo esc_url($urls['view']); ?>" target="_blank" rel="noopener"
                        data-map-load data-map-src="<?php echo esc_url($urls['embed']); ?>" data-map-title="<?php echo esc_attr($title); ?>">
                        <?php esc_html_e('Carregar mapa', 'project-theme'); ?>
                    </a>
                    <p class="map__notice">
                        <?php
                        /* translators: %s: Google Maps ou OpenStreetMap */
                        printf(esc_html__('Ao carregar, o %s pode usar cookies.', 'project-theme'), esc_html($provider_name));
                        ?>
                    </p>
                </div>
            </div>
        <?php endif; ?>
    </div>
    <?php if ($a['directions']) : ?>
        <a class="map__directions" href="<?php echo esc_url($urls['directions']); ?>" target="_blank" rel="noopener" data-map-directions>
            <?php esc_html_e('Como chegar', 'project-theme'); ?>
            <span class="screen-reader-text"><?php esc_html_e('(abre em nova aba)', 'project-theme'); ?></span>
        </a>
    <?php endif; ?>
</div>
<?php
if ($a['load'] !== 'auto') {
    wp_enqueue_script('project-map');
}
