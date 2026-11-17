<?php
/**
 * Icones de redes sociais (references/footer-social.md). O MESMO
 * componente no header, rodape e contato - le as mesmas URLs.
 * $args: location (header | footer | contact), networks (ordem; padrao
 * project_social_order()), label (nome da lista).
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'location' => 'footer',
    'networks' => [],
    'label' => __('Redes sociais', 'project-theme'),
], $args ?? []);

$profiles = project_social_profiles((array) $a['networks']);
if (!$profiles) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="social-missing">%s</p>', esc_html__('Nenhuma rede social preenchida em Configurações do Site.', 'project-theme'));
    }
    return;
}
$owner = project_option('company_name') ?: get_bloginfo('name');
?>
<ul class="social-links social-links--<?php echo esc_attr($a['location']); ?>" role="list"
    aria-label="<?php echo esc_attr($a['label']); ?>" data-social-links="<?php echo esc_attr($a['location']); ?>">
    <?php foreach ($profiles as $key => [$label, $url]) : ?>
        <li>
            <a class="social-links__link social-links__link--<?php echo esc_attr($key); ?>" href="<?php echo esc_url($url); ?>"
                target="_blank" rel="noopener me">
                <?php echo project_social_icon($key); // SVG do tema ou imagem da Midia ?>
                <span class="screen-reader-text">
                    <?php
                    /* translators: 1: rede, 2: empresa. Forma neutra: "da/do" depende do genero do nome. */
                    printf(esc_html__('%1$s: %2$s (abre em nova aba)', 'project-theme'), esc_html($label), esc_html($owner));
                    ?>
                </span>
            </a>
        </li>
    <?php endforeach; ?>
</ul>
