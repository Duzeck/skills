<?php
/**
 * Registro de Custom Post Types.
 *
 * Gere um register_post_type() por content_type do BLUEPRINT.yaml.
 * NAO registre um CPT que nao esteja no Blueprint aprovado.
 *
 * Exemplo (remover/adaptar conforme o Blueprint real do projeto):
 *
 * function project_register_cpt_service() {
 *     register_post_type('service', [
 *         'labels' => [
 *             'name' => 'Servicos',
 *             'singular_name' => 'Servico',
 *         ],
 *         'public' => true,
 *         'has_archive' => true,
 *         'rewrite' => ['slug' => 'servicos'],
 *         'supports' => ['title', 'thumbnail'],
 *         'menu_icon' => 'dashicons-hammer',
 *         'show_in_rest' => true,
 *     ]);
 * }
 * add_action('init', 'project_register_cpt_service');
 */

if (!defined('ABSPATH')) {
    exit;
}
