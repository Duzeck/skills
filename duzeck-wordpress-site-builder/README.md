# duzeck-wordpress-site-builder

Skill que transforma uma referência visual de site (imagem ou conjunto de imagens; PDF quando der) em um projeto WordPress real, administrável, responsivo e rodando localmente no WAMP.

## Como funciona

A skill age como uma pipeline de engenharia, com aprovação antes de implementar:

1. **Análise visual** da referência e inventário das seções.
2. **Classificação** do que é estático e do que deve ser administrável.
3. **Modelagem de conteúdo**: CPTs, campos ACF, taxonomias e página de opções.
4. **Blueprint** (`BLUEPRINT.yaml`) apresentado para aprovação.
5. **Implementação** a partir do tema base em `assets/theme-skeleton/`.
6. **Testes, validação visual** contra a referência e correções.

Reconhece single page (menu de âncoras, header sticky) e sites multipáginas, além de carrosséis, banners, formulários, mapas, galerias, vídeos, acordeões, FAQs, abas, tabelas de preço, depoimentos, logos de clientes, equipe, números em destaque, blog, header, menu, rodapé e redes sociais. Todo site sai com SEO editável por página, proteção básica do WordPress e fontes hospedadas no próprio site.

Não aciona a pipeline completa para pedidos como "só uma página HTML estática" ou "ajustar o CSS de um WordPress existente".

## Requisitos

- WAMP (projetos em `C:\wamp64\www\<slug>`, acessíveis em `http://localhost/<slug>/`)
- PHP e MySQL do WAMP, WP-CLI no PATH
- Python 3.9+ com `PyYAML`
- Node.js (opcional, para `scripts/capture_site.mjs`)
- ACF PRO (licença própria) e Contact Form 7

O `SKILL.md` registra esses padrões na seção "Pressupostos padrão deste ambiente". Se o seu ambiente for outro (XAMPP, Local, Docker, sem ACF PRO), ajuste essa seção e `references/local-environment.md`.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `SKILL.md` | Workflow, regras de bloqueio, modos de autonomia e quando usar cada referência e script |
| `references/` | Guias por assunto: modelagem de conteúdo, header e menu, carrosséis, formulários, SEO e segurança, acessibilidade, performance, go-live |
| `scripts/` | Scaffold do projeto, validação do Blueprint, tokens de design, fontes locais, checagens de tema e segurança, captura de tela, checklist pré-lançamento |
| `assets/` | Tema base clássico, mu-plugins (hardening, e-mail local, redirects) e templates de Blueprint, decisões e validação |
| `examples/` | Caso completo (`construtora-horizonte`) com referência, Blueprint e relato |
| `evals/` | Casos de avaliação da skill |

## Créditos

Os ícones de redes sociais em `assets/theme-skeleton/assets/icons/social/` têm licença própria, descrita no `LICENSE.txt` da pasta.
