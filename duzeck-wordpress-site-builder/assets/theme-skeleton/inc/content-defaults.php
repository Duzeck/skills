<?php
/**
 * Conteúdo padrão = textos e imagens da REFERÊNCIA (BLUEPRINT.yaml -> copy e media).
 *
 * Fonte única usada para:
 *  1. preencher os campos do admin na instalação (migração do projeto chama
 *     update_field() com estes valores e importa as imagens para a Mídia);
 *  2. reserva no front-end se um campo for apagado (o layout nunca quebra).
 * O conteúdo publicado é SEMPRE o do admin. Chaves = nomes dos campos ACF
 * (com prefixo de domínio). Imagens: nome do arquivo em assets/img/.
 * Quebras de linha de títulos: "\n" (o template usa project_lines()).
 */

if (!defined('ABSPATH')) {
    exit;
}

function project_content_defaults() {
    return [
        // Exemplos - substitua pelas chaves reais do Blueprint (editable_content.fields):
        // 'company_phone' => '(00) 0000-0000',
        // 'home_hero_title' => "Linha 1\nLinha 2",
        // 'home_hero_image' => 'hero-home.jpg',
        // 'contact_form_select' => 'contact',   // slug do CF7 = forms[].id (project_form())
        // 'company_address' => 'Rua ..., 123 - Bairro - Cidade - UF', // mapa + rodapé
    ];
}

function project_default($name) {
    $d = project_content_defaults();
    return $d[$name] ?? '';
}
