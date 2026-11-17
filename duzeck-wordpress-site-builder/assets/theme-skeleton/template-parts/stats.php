<?php
/**
 * Numeros em destaque (references/team-stats.md) - um por stats[] do Blueprint.
 * "+150 projetos entregues", "100% clientes satisfeitos", "1,2 mil m²".
 *
 * Numero e afirmacao de negocio (CDC/CONAR: tem de ser comprovavel): real
 * so confirmado pelo usuario (stats[].content_source user); demo => true
 * fica oculto em producao.
 *
 * O VALOR FINAL esta sempre no HTML (buscador, leitor de tela, sem JS).
 * count_up => true: o stats.js anima so a copia visual (aria-hidden), uma
 * vez, ao entrar na tela, e nao anima com prefers-reduced-motion. A largura
 * do numero e reservada (min-width em ch + tabular-nums): o layout nao
 * pula durante a contagem.
 *
 * Uso:
 *   get_template_part('template-parts/stats', null, [
 *       'id'       => 'home_stats',                 // stats[].id
 *       'items'    => [['value' => 150, 'prefix' => '+', 'suffix' => '', 'label' => 'projetos entregues'], ...],
 *       'count_up' => true,                         // stats[].count_up
 *       'demo'     => false,
 *   ]);
 * value: numero (150, 1.2) ou texto ("1.250", "1,2"); casas decimais seguem o valor.
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'items' => [],
    'count_up' => false,
    'demo' => false,
    'class' => '',
], $args ?? []);

if (project_demo_blocked($a['demo'])) {
    project_demo_notice(__('Números em destaque', 'project-theme'));
    return;
}
$items = array_values((array) $a['items']);
if (!$items) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="stats-missing">%s</p>', esc_html__('Números sem conteúdo: preencha no admin.', 'project-theme'));
    }
    return;
}
if ($a['count_up']) {
    wp_enqueue_script('project-stats');
}
?>
<ul class="<?php echo esc_attr(trim('stats ' . $a['class'])); ?>" role="list" data-stats="<?php echo esc_attr($a['id']); ?>"
    data-count-up="<?php echo $a['count_up'] ? 'true' : 'false'; ?>"<?php echo $a['demo'] ? ' data-demo="true"' : ''; ?>>
    <?php foreach ($items as $item) : ?>
        <?php
        $item = (array) $item;
        $raw = $item['value'] ?? '';
        $number = project_money_value($raw);
        if ($number === null) {
            continue;
        }
        // Casas decimais: as do valor informado ("1,2" -> 1; 150 -> 0).
        $decimals = 0;
        if (preg_match('/[.,](\d+)$/', is_float($raw) ? rtrim(rtrim(number_format($raw, 6, '.', ''), '0'), '.') : (string) $raw, $m)
            && !preg_match('/^-?\d{1,3}(\.\d{3})+$/', (string) $raw)) {
            $decimals = strlen($m[1]);
        }
        $formatted = number_format($number, $decimals, ',', '.');
        $prefix = (string) ($item['prefix'] ?? '');
        $suffix = (string) ($item['suffix'] ?? '');
        $full = $prefix . $formatted . $suffix;
        ?>
        <li class="stat">
            <?php if (!empty($item['icon'])) : ?>
                <span class="stat__icon stat__icon--<?php echo esc_attr($item['icon']); ?>" aria-hidden="true"></span>
            <?php endif; ?>
            <p class="stat__value">
                <span class="screen-reader-text"><?php echo esc_html($full); ?></span>
                <span class="stat__number" aria-hidden="true"
                    style="min-width: <?php echo (int) (function_exists('mb_strlen') ? mb_strlen($full) : strlen($full)); ?>ch;"
                    data-count-to="<?php echo esc_attr($number); ?>" data-decimals="<?php echo (int) $decimals; ?>"
                    data-prefix="<?php echo esc_attr($prefix); ?>" data-suffix="<?php echo esc_attr($suffix); ?>"><?php echo esc_html($full); ?></span>
            </p>
            <p class="stat__label"><?php echo esc_html($item['label'] ?? ''); ?></p>
        </li>
    <?php endforeach; ?>
</ul>
