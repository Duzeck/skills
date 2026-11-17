<?php
/**
 * Abas (references/disclosures.md) - uma por tabs[] do Blueprint.
 *
 * Progressive enhancement: o HTML entrega TODOS os paineis, cada um com seu
 * titulo (le-se sem JS, e buscadores indexam tudo). O disclosure.js liga o
 * padrao W3C APG "Tabs": role=tablist/tab/tabpanel, aria-selected, tabindex
 * movel, setas esquerda/direita + Home/End (ativacao automatica), link
 * direto (#<id-do-painel>).
 * mobile = scroll: as abas rolam na horizontal no celular.
 * mobile = stack: no celular os paineis ficam empilhados com titulo (sem abas).
 *
 * Uso:
 *   get_template_part('template-parts/tabs', null, [
 *       'id'            => 'services_tabs',                        // tabs[].id
 *       'label'         => __('Serviços', 'project-theme'),        // nome da lista de abas
 *       'tabs'          => project_disclosure_items(project_home('services_tabs'), 'services_tab_title', 'services_tab_content'),
 *       'active'        => 1,              // tabs[].active_in_reference
 *       'mobile'        => 'scroll',       // tabs[].mobile
 *       'heading_level' => 3,
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'label' => '',
    'tabs' => [],
    'active' => 1,
    'mobile' => 'scroll',
    'heading_level' => 3,
    'class' => '',
], $args ?? []);

$tabs = array_values((array) $a['tabs']);
if (!$tabs) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="tabs-missing">%s</p>', esc_html__('Abas sem conteúdo: preencha no admin.', 'project-theme'));
    }
    return;
}

$level = min(6, max(2, (int) $a['heading_level']));
$active = min(count($tabs), max(1, (int) $a['active']));
$mobile = $a['mobile'] === 'stack' ? 'stack' : 'scroll';
wp_enqueue_script('project-disclosure');
?>
<div class="<?php echo esc_attr(trim('tabs tabs--mobile-' . $mobile . ' ' . $a['class'])); ?>"
    data-tabs="<?php echo esc_attr($a['id']); ?>" data-active="<?php echo (int) $active; ?>" data-mobile="<?php echo esc_attr($mobile); ?>">
    <?php /* Escondida ate o JS: sem JS os paineis aparecem todos, com titulo. */ ?>
    <div class="tabs__list" data-tabs-list aria-label="<?php echo esc_attr($a['label']); ?>" hidden>
        <?php foreach ($tabs as $i => $tab) : ?>
            <?php $panel_id = project_disclosure_anchor($a['id'], $tab['title'], $i); ?>
            <button type="button" class="tabs__tab" id="<?php echo esc_attr($panel_id); ?>-tab"
                aria-controls="<?php echo esc_attr($panel_id); ?>" data-tabs-tab><?php echo esc_html($tab['title']); ?></button>
        <?php endforeach; ?>
    </div>
    <?php foreach ($tabs as $i => $tab) : ?>
        <section class="tabs__panel" id="<?php echo esc_attr(project_disclosure_anchor($a['id'], $tab['title'], $i)); ?>" data-tabs-panel>
            <<?php echo 'h' . $level; ?> class="tabs__panel-title"><?php echo esc_html($tab['title']); ?></<?php echo 'h' . $level; ?>>
            <?php echo wp_kses_post(wpautop($tab['content'])); ?>
        </section>
    <?php endforeach; ?>
</div>
