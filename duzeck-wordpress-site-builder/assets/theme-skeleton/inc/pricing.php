<?php
/**
 * Precos e tabelas (references/tables-pricing.md).
 *
 * Preco e NUMERO no admin (campo number do ACF, ex.: 149.9) - nunca texto
 * "R$ 149,90": assim formata sempre igual, ordena e calcula (parcelas,
 * desconto do anual). O tema formata no padrao brasileiro.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** Converte valor do admin em float: 149.9 | "149,90" | "1.234,56" | "R$ 99". */
function project_money_value($value) {
    if (is_int($value) || is_float($value)) {
        return (float) $value;
    }
    $s = preg_replace('/[^\d,.\-]/', '', (string) $value);
    if ($s === '' || $s === '-') {
        return null;
    }
    if (strpos($s, ',') !== false) {
        $s = str_replace('.', '', $s);   // 1.234,56 -> 1234,56
        $s = str_replace(',', '.', $s);
    } elseif (preg_match('/^-?\d{1,3}(\.\d{3})+$/', $s)) {
        $s = str_replace('.', '', $s);   // "1.234" escrito no Brasil = mil duzentos e trinta e quatro
    }
    return is_numeric($s) ? (float) $s : null;
}

/**
 * Partes de um valor em reais, para estilizar sem perder a leitura.
 * decimals 'auto': "R$ 99" quando inteiro, "R$ 99,90" quando nao (como a
 * maioria das referencias mostra); 'always': sempre com centavos.
 *
 * @return array{symbol:string, integer:string, cents:string, text:string}|null
 */
function project_money($value, $decimals = 'auto') {
    $amount = project_money_value($value);
    if ($amount === null) {
        return null;
    }
    $show_cents = $decimals === 'always' || abs($amount - round($amount)) > 0.004;
    $formatted = number_format($amount, $show_cents ? 2 : 0, ',', '.');
    $parts = explode(',', $formatted);
    return [
        'symbol' => 'R$',
        'integer' => $parts[0],
        'cents' => $show_cents ? ',' . $parts[1] : '',
        'text' => 'R$ ' . $formatted,   // "R$ 1.234,56" (espaco normal: leitor de tela le "reais")
    ];
}

/**
 * HTML de preco: visual em partes (aria-hidden) + frase completa para
 * leitor de tela. Preco antigo riscado (<del> nao e anunciado como
 * "riscado") vira "antes R$ X" na frase.
 *
 * @param mixed $value
 * @param array $args period ('/mês'), period_text ('por mês'), old (valor antigo),
 *                    prefix ('a partir de'), installments (int), decimals
 */
function project_price($value, array $args = []) {
    $a = array_merge([
        'period' => '',
        'period_text' => '',
        'old' => null,
        'prefix' => '',
        'installments' => 0,
        'decimals' => 'auto',
        'class' => '',
    ], $args);

    $money = project_money($value, $a['decimals']);
    if (!$money) {
        return '';
    }
    $old = $a['old'] !== null && $a['old'] !== '' ? project_money($a['old'], $a['decimals']) : null;
    $installments = (int) $a['installments'];
    $per_installment = $installments > 1 ? project_money(project_money_value($value) / $installments, 'always') : null;

    $sentence = trim(implode(' ', array_filter([
        $a['prefix'],
        $per_installment
            /* translators: 1: parcelas, 2: valor da parcela, 3: total */
            ? sprintf(__('%1$d vezes de %2$s (total %3$s)', 'project-theme'), $installments, $per_installment['text'], $money['text'])
            : $money['text'],
        $a['period_text'],
        /* translators: %s: preco anterior */
        $old ? sprintf(__('(antes %s)', 'project-theme'), $old['text']) : '',
    ])));

    $visual = '';
    if ($old) {
        $visual .= sprintf('<del class="price__old">%s</del> ', esc_html($old['text']));
    }
    if ($a['prefix']) {
        $visual .= sprintf('<span class="price__prefix">%s</span> ', esc_html($a['prefix']));
    }
    $shown = $per_installment ?: $money;
    if ($per_installment) {
        $visual .= sprintf('<span class="price__installments">%dx</span> ', $installments);
    }
    $visual .= sprintf(
        '<span class="price__currency">%s</span><span class="price__amount">%s</span><span class="price__cents">%s</span>',
        esc_html($shown['symbol']),
        esc_html($shown['integer']),
        esc_html($shown['cents'])
    );
    if ($a['period']) {
        $visual .= sprintf('<span class="price__period">%s</span>', esc_html($a['period']));
    }

    return sprintf(
        '<p class="%s"><span class="screen-reader-text">%s</span><span class="price__visual" aria-hidden="true">%s</span></p>',
        esc_attr(trim('price ' . $a['class'])),
        esc_html($sentence),
        $visual
    );
}

/** Celula de comparativo: aceita bool, 1/0, "sim"/"não", "x", "✓". */
function project_check_value($value) {
    if (is_bool($value)) {
        return $value;
    }
    $v = function_exists('mb_strtolower') ? mb_strtolower(trim((string) $value)) : strtolower(trim((string) $value));
    return in_array($v, ['1', 'sim', 's', 'yes', 'y', 'x', '✓', '✔', 'true', 'incluído', 'incluido'], true);
}
