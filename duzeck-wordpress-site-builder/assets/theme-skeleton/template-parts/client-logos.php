<?php
/**
 * Logos de clientes/parceiros (references/social-proof.md) - um por
 * client_logos[] do Blueprint. Em carrossel com setas/bolinhas: use
 * template-parts/carousel.php (carousels[] kind logos).
 *
 * - alt = NOME da empresa (nunca "logo", nunca o alt da Midia): e o que o
 *   leitor de tela le e, com link, o texto do link.
 * - Caixa de mesma altura com object-fit: contain - logos largos e
 *   quadrados ficam com peso visual parecido.
 * - layout marquee (faixa que rola sem parar): sem JS e com movimento
 *   reduzido fica uma fileira parada; o client-logos.js duplica a lista
 *   para o loop (copia aria-hidden + inert: leitor de tela e Tab veem cada
 *   empresa uma vez so) e mostra o botao de pausa (WCAG 2.2.2).
 *
 * Uso:
 *   get_template_part('template-parts/client-logos', null, [
 *       'id'        => 'home_clients',           // client_logos[].id
 *       'label'     => __('Clientes', 'project-theme'),
 *       'items'     => $itens,                   // [name, logo (anexo ou arquivo em assets/img), url]
 *       'layout'    => 'grid',                   // grid | row | marquee
 *       'grayscale' => true,                     // visual da referencia (cor no hover/foco)
 *       'demo'      => false,                    // client_logos[].permission === 'demo'
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'label' => '',
    'items' => [],
    'layout' => 'grid',
    'grayscale' => false,
    'demo' => false,
    'class' => '',
], $args ?? []);

if (project_demo_blocked($a['demo'])) {
    project_demo_notice(__('Logos de clientes', 'project-theme'));
    return;
}
$items = array_values(array_filter((array) $a['items'], function ($i) {
    return !empty(((array) $i)['name']);
}));
if (!$items) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="client-logos-missing">%s</p>', esc_html__('Logos sem conteúdo: cadastre no admin (nome + arquivo).', 'project-theme'));
    }
    return;
}
$layout = in_array($a['layout'], ['grid', 'row', 'marquee'], true) ? $a['layout'] : 'grid';
$classes = 'client-logos client-logos--' . $layout . ($a['grayscale'] ? ' is-grayscale' : '') . ' ' . $a['class'];
if ($layout === 'marquee') {
    wp_enqueue_script('project-client-logos');
}
?>
<div class="<?php echo esc_attr(trim($classes)); ?>" data-client-logos="<?php echo esc_attr($a['id']); ?>"
    <?php echo $a['label'] ? 'role="region" aria-label="' . esc_attr($a['label']) . '"' : ''; ?>
    <?php echo $a['demo'] ? 'data-demo="true"' : ''; ?>
    data-label-pause="<?php echo esc_attr__('Pausar faixa de logos', 'project-theme'); ?>"
    data-label-play="<?php echo esc_attr__('Reproduzir faixa de logos', 'project-theme'); ?>">
    <?php if ($layout === 'marquee') : ?>
        <button type="button" class="client-logos__toggle" data-logos-toggle hidden>
            <span class="client-logos__toggle-icon" aria-hidden="true"></span>
            <span class="screen-reader-text" data-logos-toggle-label><?php esc_html_e('Pausar faixa de logos', 'project-theme'); ?></span>
        </button>
    <?php endif; ?>
    <div class="client-logos__viewport">
        <div class="client-logos__track" data-logos-track>
            <ul class="client-logos__list" role="list">
                <?php foreach ($items as $item) : ?>
                    <?php
                    $item = (array) $item;
                    $name = trim(wp_strip_all_tags((string) $item['name']));
                    $id = project_image_id($item['logo'] ?? 0);
                    if ($id) {
                        $img = wp_get_attachment_image($id, 'medium', false, ['alt' => $name, 'loading' => 'lazy', 'class' => 'client-logos__img']);
                    } elseif (!empty($item['logo']) && is_string($item['logo'])) {
                        $img = sprintf('<img class="client-logos__img" src="%s" alt="%s" loading="lazy" data-provisional="crop_from_reference">',
                            esc_url(get_template_directory_uri() . '/assets/img/' . $item['logo']), esc_attr($name));
                    } else {
                        $img = sprintf('<span class="client-logos__name">%s</span>', esc_html($name)); // sem arquivo: o nome, nunca um desenho
                    }
                    $url = trim((string) ($item['url'] ?? ''));
                    ?>
                    <li class="client-logos__item">
                        <?php if ($url) : ?>
                            <a class="client-logos__link" href="<?php echo esc_url($url); ?>" target="_blank" rel="noopener">
                                <?php echo $img; ?>
                                <span class="screen-reader-text"><?php esc_html_e('(abre em nova aba)', 'project-theme'); ?></span>
                            </a>
                        <?php else : ?>
                            <?php echo $img; ?>
                        <?php endif; ?>
                    </li>
                <?php endforeach; ?>
            </ul>
        </div>
    </div>
</div>
