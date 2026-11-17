<?php
/**
 * Registro de taxonomias. Uma taxonomy_register() por taxonomia do
 * BLUEPRINT.yaml. So existe taxonomia aqui se houver evidencia real de
 * filtro/agrupamento no layout (ver references/decision-framework.md).
 *
 * Exemplo (remover/adaptar conforme o Blueprint real do projeto):
 *
 * function project_register_tax_project_category() {
 *     register_taxonomy('project_category', ['project'], [
 *         'labels' => ['name' => 'Categorias de Projeto'],
 *         'hierarchical' => true,
 *         'public' => true,
 *         'show_in_rest' => true,
 *         'rewrite' => ['slug' => 'categoria-projeto'],
 *     ]);
 * }
 * add_action('init', 'project_register_tax_project_category');
 */

if (!defined('ABSPATH')) {
    exit;
}
