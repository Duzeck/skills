<?php
/**
 * Prova social: depoimentos e logos de clientes (references/social-proof.md).
 *
 * Depoimentos e logos da referencia quase sempre sao ficticios do mockup
 * (nomes inventados, fotos de banco de imagem, marcas falsas). Publica-los
 * como reais e propaganda enganosa (CDC/CONAR) e, no caso de logos, uso
 * indevido de marca. Por isso o Blueprint marca a origem (content_source /
 * permission) e o tema tem uma trava: conteudo DEMO nao e renderizado em
 * producao - so em local/desenvolvimento/homologacao.
 */

if (!defined('ABSPATH')) {
    exit;
}

/** Conteudo demo bloqueado neste ambiente? (producao = sim) */
function project_demo_blocked($is_demo) {
    if (!$is_demo) {
        return false;
    }
    $env = function_exists('wp_get_environment_type') ? wp_get_environment_type() : 'production';
    return $env === 'production';
}

/** Aviso so para quem administra (nunca para o visitante). */
function project_demo_notice($what) {
    if (current_user_can('edit_theme_options')) {
        printf(
            '<p class="demo-blocked">%s</p>',
            /* translators: %s: depoimentos / logos de clientes */
            esc_html(sprintf(__('%s de demonstração ocultos em produção: cadastre o conteúdo real e desmarque "demo".', 'project-theme'), $what))
        );
    }
}

/** Nota 0-5 do admin ("4,5", 4.5, "5") -> float limitado, ou null. */
function project_rating_value($value) {
    if ($value === null || $value === '') {
        return null;
    }
    $n = (float) str_replace(',', '.', (string) $value);
    return max(0, min(5, round($n * 2) / 2));   // passos de meia estrela
}
