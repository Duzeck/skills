<?php
/**
 * Grupos de campos ACF. Um acf_add_local_field_group() por content_type
 * com campos no BLUEPRINT.yaml. So registre campos que estao no Blueprint
 * aprovado - nao adicione campos "que podem ser uteis depois".
 *
 * Exemplo (remover/adaptar conforme o Blueprint real do projeto):
 *
 * add_action('acf/init', function () {
 *     if (!function_exists('acf_add_local_field_group')) {
 *         return;
 *     }
 *     acf_add_local_field_group([
 *         'key' => 'group_service',
 *         'title' => 'Detalhes do Servico',
 *         'fields' => [
 *             [
 *                 'key' => 'field_service_short_description',
 *                 'label' => 'Descricao curta',
 *                 'name' => 'service_short_description',   // prefixo de dominio
 *                 'type' => 'textarea',
 *                 'instructions' => 'Ate 2 linhas; aparece no card da Home.',
 *                 'required' => 1,
 *             ],
 *             // Repeater: sempre com min/max e instrucoes coerentes com o layout.
 *             // [ 'key' => 'field_service_steps', 'name' => 'service_steps',
 *             //   'type' => 'repeater', 'min' => 3, 'max' => 6, 'sub_fields' => [...] ],
 *         ],
 *         'location' => [[['param' => 'post_type', 'operator' => '==', 'value' => 'service']]],
 *     ]);
 * });
 */

if (!defined('ABSPATH')) {
    exit;
}
