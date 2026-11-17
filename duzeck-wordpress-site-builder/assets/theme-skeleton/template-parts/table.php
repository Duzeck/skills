<?php
/**
 * Tabela de dados (references/tables-pricing.md) - uma por tables[] do Blueprint.
 * Horarios, especificacoes, medidas, comparativo de planos (✓/✗).
 *
 * <table> semantica: <caption> (nome da tabela - visivel ou so para
 * leitor de tela), <th scope="col">, primeira coluna como <th scope="row">
 * quando ela nomeia a linha. Celulas ✓/✗ tem texto ("Incluído"/"Não
 * incluído"); moeda e numero formatados no padrao brasileiro e alinhados.
 *
 * mobile = scroll: a tabela rola na horizontal DENTRO de uma regiao
 *   nomeada e focavel (teclado consegue rolar); a pagina nao estoura.
 * mobile = cards: abaixo de 768px cada linha vira um card com
 *   "Coluna: valor"; os papeis ARIA explicitos (role=table/row/cell...)
 *   mantem a semantica que o display:block tiraria.
 *
 * Uso:
 *   get_template_part('template-parts/table', null, [
 *       'id'      => 'opening_hours',                       // tables[].id
 *       'caption' => project_home('opening_hours_caption'), // obrigatorio (acessibilidade)
 *       'caption_visible' => true,
 *       'columns' => [
 *           ['key' => 'day',   'label' => 'Dia'],
 *           ['key' => 'open',  'label' => 'Abertura', 'align' => 'end'],
 *           ['key' => 'price', 'label' => 'Valor', 'type' => 'currency'],   // text | number | currency | check
 *       ],
 *       'rows'       => project_home('opening_hours_rows'),  // repeater: chaves = columns[].key
 *       'row_header' => true,
 *       'mobile'     => 'scroll',                            // scroll | cards
 *   ]);
 */
if (!defined('ABSPATH')) { exit; }

$a = array_merge([
    'id' => '',
    'caption' => '',
    'caption_visible' => true,
    'columns' => [],
    'rows' => [],
    'row_header' => true,
    'mobile' => 'scroll',
    'class' => '',
], $args ?? []);

$columns = array_values((array) $a['columns']);
$rows = array_values((array) $a['rows']);
if (!$columns || !$rows) {
    if (current_user_can('edit_theme_options')) {
        printf('<p class="table-missing">%s</p>', esc_html__('Tabela sem dados: preencha no admin.', 'project-theme'));
    }
    return;
}
$cards = $a['mobile'] === 'cards';
$caption_id = sanitize_title($a['id'] . '-caption');
// Em modo cards os papeis ARIA explicitos preservam a semantica de tabela.
$role = function ($r) use ($cards) {
    return $cards ? ' role="' . $r . '"' : '';
};
$align_class = function ($col) {
    $type = $col['type'] ?? 'text';
    $align = $col['align'] ?? (in_array($type, ['number', 'currency'], true) ? 'end' : ($type === 'check' ? 'center' : 'start'));
    return 'is-' . $align;
};
$cell = function ($col, $value) {
    $type = $col['type'] ?? 'text';
    if ($type === 'check') {
        $yes = project_check_value($value);
        return sprintf(
            '<span class="data-table__check %s" aria-hidden="true"></span><span class="screen-reader-text">%s</span>',
            $yes ? 'is-yes' : 'is-no',
            $yes ? esc_html__('Incluído', 'project-theme') : esc_html__('Não incluído', 'project-theme')
        );
    }
    if ($type === 'currency') {
        $money = project_money($value);
        return $money ? esc_html($money['text']) : esc_html((string) $value);
    }
    if ($type === 'number') {
        $n = project_money_value($value);
        return $n !== null ? esc_html(number_format($n, abs($n - round($n)) > 0.004 ? 2 : 0, ',', '.')) : esc_html((string) $value);
    }
    return esc_html((string) $value);
};
?>
<div class="<?php echo esc_attr(trim('data-table data-table--mobile-' . ($cards ? 'cards' : 'scroll') . ' ' . $a['class'])); ?>"
    data-table="<?php echo esc_attr($a['id']); ?>">
    <div class="data-table__scroll" role="region" aria-labelledby="<?php echo esc_attr($caption_id); ?>" tabindex="0">
        <table class="data-table__table"<?php echo $role('table'); ?>>
            <caption id="<?php echo esc_attr($caption_id); ?>"<?php echo $a['caption_visible'] ? '' : ' class="screen-reader-text"'; ?>><?php echo esc_html($a['caption']); ?></caption>
            <thead<?php echo $role('rowgroup'); ?>>
                <tr<?php echo $role('row'); ?>>
                    <?php foreach ($columns as $col) : ?>
                        <th scope="col" class="<?php echo esc_attr($align_class($col)); ?>"<?php echo $role('columnheader'); ?>><?php echo esc_html($col['label'] ?? ''); ?></th>
                    <?php endforeach; ?>
                </tr>
            </thead>
            <tbody<?php echo $role('rowgroup'); ?>>
                <?php foreach ($rows as $row) : ?>
                    <?php $row = (array) $row; ?>
                    <tr<?php echo $role('row'); ?>>
                        <?php foreach ($columns as $c => $col) : ?>
                            <?php
                            $value = $row[$col['key']] ?? '';
                            $is_header = $a['row_header'] && $c === 0;
                            $tag = $is_header ? 'th' : 'td';
                            $attrs = $is_header ? ' scope="row"' . $role('rowheader') : $role('cell');
                            ?>
                            <<?php echo $tag . $attrs; ?> class="<?php echo esc_attr($align_class($col)); ?>" data-label="<?php echo esc_attr($col['label'] ?? ''); ?>"><?php echo $cell($col, $value); ?></<?php echo $tag; ?>>
                        <?php endforeach; ?>
                    </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</div>
