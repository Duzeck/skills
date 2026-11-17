<?php
/**
 * Planos e precos (references/tables-pricing.md) - um por pricing[] do Blueprint.
 *
 * Cada plano: nome, descricao, preco por periodo (NUMERO), preco antigo,
 * parcelas, selo ("Mais popular" - texto), recursos com incluido/nao
 * incluido, CTA. Tudo vem do admin (repeater ou CPT); os valores da
 * referencia so entram como reais se o usuario confirmou (price_source).
 *
 * Com mais de um periodo (Mensal/Anual): sem JS os dois precos aparecem
 * em cada plano; o pricing.js mostra o seletor (botoes com aria-pressed),
 * deixa so o periodo escolhido e anuncia a troca (aria-live).
 *
 * Uso:
 *   get_template_part('template-parts/pricing', null, [
 *       'id'      => 'home_pricing',                        // pricing[].id
 *       'plans'   => project_home('home_pricing_plans'),    // repeater (chaves abaixo)
 *       'billing' => ['monthly' => ['label' => 'Mensal', 'period' => '/mês', 'period_text' => 'por mês'],
 *                     'yearly'  => ['label' => 'Anual',  'period' => '/ano', 'period_text' => 'por ano']],
 *       'default' => 'monthly',
 *       'toggle_label' => __('Período de cobrança', 'project-theme'),
 *       'heading_level' => 3,
 *   ]);
 * Chaves de cada plano: name, description, price_<periodo> (ex.: price_monthly),
 * old_price_<periodo>, installments_<periodo>, prefix, featured (bool), badge,
 * features [{text, included}], cta_label, cta_target.
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'plans' => [],
    'billing' => ['monthly' => ['label' => __('Mensal', 'project-theme'), 'period' => __('/mês', 'project-theme'), 'period_text' => __('por mês', 'project-theme')]],
    'default' => 'monthly',
    'toggle_label' => __('Período de cobrança', 'project-theme'),
    'heading_level' => 3,
    'class' => '',
], $args ?? []);

$plans = array_values((array) $a['plans']);
$billing = (array) $a['billing'];
if (!$plans || !$billing) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="pricing-missing">%s</p>', esc_html__('Planos sem conteúdo: preencha no admin.', 'project-theme'));
    }
    return;
}
$default = isset($billing[$a['default']]) ? $a['default'] : array_key_first($billing);
$multi = count($billing) > 1;
$level = min(6, max(2, (int) $a['heading_level']));
if ($multi) {
    wp_enqueue_script('project-pricing');
}
?>
<div class="<?php echo esc_attr(trim('pricing ' . $a['class'])); ?>" data-pricing="<?php echo esc_attr($a['id']); ?>"
    data-billing="<?php echo esc_attr($default); ?>">
    <?php if ($multi) : ?>
        <div class="pricing__toggle" role="group" aria-label="<?php echo esc_attr($a['toggle_label']); ?>" data-pricing-toggle hidden>
            <?php foreach ($billing as $key => $b) : ?>
                <button type="button" class="pricing__toggle-option" data-billing-option="<?php echo esc_attr($key); ?>"
                    aria-pressed="<?php echo $key === $default ? 'true' : 'false'; ?>"><?php echo esc_html($b['label'] ?? $key); ?></button>
            <?php endforeach; ?>
        </div>
        <p class="screen-reader-text" aria-live="polite" data-pricing-status></p>
    <?php endif; ?>
    <ul class="pricing__plans" role="list">
        <?php foreach ($plans as $i => $plan) : ?>
            <?php
            $plan = (array) $plan;
            $heading_id = sanitize_title($a['id'] . '-' . ($plan['name'] ?? $i));
            $featured = !empty($plan['featured']);
            ?>
            <li class="pricing__plan<?php echo $featured ? ' is-featured' : ''; ?>" data-pricing-plan>
                <article class="pricing__card" aria-labelledby="<?php echo esc_attr($heading_id); ?>">
                    <?php if ($featured && !empty($plan['badge'])) : ?>
                        <p class="pricing__badge"><?php echo esc_html($plan['badge']); ?></p>
                    <?php endif; ?>
                    <<?php echo 'h' . $level; ?> class="pricing__name" id="<?php echo esc_attr($heading_id); ?>"><?php echo esc_html($plan['name'] ?? ''); ?></<?php echo 'h' . $level; ?>>
                    <?php if (!empty($plan['description'])) : ?>
                        <p class="pricing__description"><?php echo esc_html($plan['description']); ?></p>
                    <?php endif; ?>
                    <?php foreach ($billing as $key => $b) : ?>
                        <?php
                        $html = project_price($plan['price_' . $key] ?? null, [
                            'period' => $b['period'] ?? '',
                            'period_text' => $b['period_text'] ?? '',
                            'old' => $plan['old_price_' . $key] ?? null,
                            'installments' => $plan['installments_' . $key] ?? 0,
                            'prefix' => $plan['prefix'] ?? '',
                        ]);
                        if ($html === '') {
                            continue;
                        }
                        ?>
                        <div class="pricing__price" data-price-for="<?php echo esc_attr($key); ?>">
                            <?php if ($multi) : ?>
                                <?php /* Rotulo do periodo: so sem JS (com JS o seletor ja diz). */ ?>
                                <p class="pricing__period-label"><?php echo esc_html($b['label'] ?? $key); ?></p>
                            <?php endif; ?>
                            <?php echo $html; // project_price() ja escapa. ?>
                        </div>
                    <?php endforeach; ?>
                    <?php if (!empty($plan['features'])) : ?>
                        <ul class="pricing__features" role="list">
                            <?php foreach ((array) $plan['features'] as $feature) : ?>
                                <?php
                                $feature = (array) $feature;
                                $included = project_check_value($feature['included'] ?? true);
                                ?>
                                <li class="pricing__feature <?php echo $included ? 'is-included' : 'is-excluded'; ?>">
                                    <span class="pricing__feature-icon" aria-hidden="true"></span>
                                    <span class="screen-reader-text"><?php echo $included ? esc_html__('Incluído:', 'project-theme') : esc_html__('Não incluído:', 'project-theme'); ?></span>
                                    <?php echo esc_html($feature['text'] ?? ''); ?>
                                </li>
                            <?php endforeach; ?>
                        </ul>
                    <?php endif; ?>
                    <?php if (!empty($plan['cta_label'])) : ?>
                        <a class="pricing__cta" href="<?php echo esc_url(project_target_url($plan['cta_target'] ?? '')); ?>">
                            <?php echo esc_html($plan['cta_label']); ?>
                            <span class="screen-reader-text">- <?php echo esc_html($plan['name'] ?? ''); ?></span>
                        </a>
                    <?php endif; ?>
                </article>
            </li>
        <?php endforeach; ?>
    </ul>
</div>
