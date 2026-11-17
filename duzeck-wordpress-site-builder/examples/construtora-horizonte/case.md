# Caso de referência — Construtora Horizonte

Empresa fictícia usada como caso de teste de ponta a ponta para esta
Skill. Pequena construtora residencial de Goiânia, foco em casas de médio
padrão.

## Páginas
Home, Sobre, Serviços, Projetos, Contato.

## Elementos visuais (ver `reference.png`)
Header, logo, menu, CTA "Solicitar Orçamento", hero, cards de serviços,
seção sobre, cards de projetos, depoimentos, CTA final, formulário,
footer, filtros de projetos.

## Classificação esperada
- **Global:** logo, telefone, WhatsApp, endereço, redes sociais, menu, footer
- **Static:** conteúdo institucional da página Sobre
- **Dynamic:** serviços, projetos, depoimentos
- **Configurable:** telefone, WhatsApp, endereço, CTA, redes sociais

## Modelagem esperada
Imagem dos cards = thumbnail nativo (`supports: thumbnail`), não campo ACF.
Campos com prefixo de domínio (schema 1.1):

- CPT `service` — service_icon, service_short_description,
  service_detailed_description
- CPT `project` — project_neighborhood, project_city, project_state,
  project_gallery, project_description, project_completion_date,
  project_client, project_featured
- CPT `testimonial` — testimonial_client_name, testimonial_quote,
  testimonial_client_photo, testimonial_location, testimonial_featured
- Taxonomia `project_category` — termos: casas, reformas, projetos

## Incerteza conhecida (propositalmente não resolvida pela referência)
O layout mostra filtros de projetos por categoria, mas não indica se o
filtro deve recarregar a página ou usar AJAX. Este é o teste principal do
comportamento esperado: a Skill deve registrar isso como `uncertainty`
(bloqueante, dado o impacto no JS/template) e perguntar — nunca assumir
AJAX nem assumir reload silenciosamente.

## Critério de sucesso do caso

Ver `evals/evals.json` (eval `construtora_horizonte_e2e`) para a execução
completa deste caso do zero até um WordPress validado no WAMP.
