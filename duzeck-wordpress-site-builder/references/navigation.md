# Navegação: single page × multipáginas

> Estrutura do header (logo, botão, barra superior, submenus, header
> transparente): `references/header-menu.md`.

A estrutura do site é decidida **no passo 1** (escopo) e gravada em
`project.site_structure`. Ela muda o menu, o header, os templates e o QA —
não é detalhe de implementação.

## 1. Como decidir

| Sinal na referência / no pedido | Estrutura |
|---|---|
| Uma única imagem longa, menu cujos itens repetem os títulos das seções da própria página ("Sobre", "Serviços", "Contato" e as seções com esses nomes aparecem abaixo) | `single_page` |
| Usuário diz "landing page", "one page", "página única", "site de uma página" | `single_page` |
| Várias imagens, uma por página; ou itens de menu sem seção correspondente na imagem | `multi_page` |
| Cards com "Ver mais"/"Saiba mais" que levam a páginas próprias (single de CPT) | `multi_page` |
| Ambíguo (ex.: uma imagem só, mas menu com itens que não aparecem nela) | `uncertainty` **bloqueante**: pergunte |

Uma single page **pode** ter páginas auxiliares fora do fluxo principal
(política de privacidade, 404, obrigado-pelo-contato). Elas entram em
`pages[]` com `role: auxiliary` e não mudam a estrutura.

Single page **não** significa "sem administração": cada seção continua
com seus campos ACF (`editable_content`), e uma estrutura repetitiva
(depoimentos, serviços) continua podendo ser CPT ou repeater
(`references/content-modeling.md`).

## 2. Single page — regras obrigatórias

1. **O header acompanha a rolagem e fica sempre visível**
   (`theme.header_behavior: sticky`). Não é opcional e não é desvio do
   espelho: a referência estática mostra o header no topo; o
   comportamento de rolagem é requisito da skill.
2. **Cada seção de destino tem âncora** (`pages[].sections[].anchor`):
   slug curto, minúsculo, sem acento, em português e estável
   (`servicos`, `sobre`, `contato`). Âncora é estrutura: fica no template
   (`project_section_anchor()`), não no admin. O que o usuário edita é o
   **rótulo** do item em Aparência > Menus.
3. **Itens do menu são âncoras** (`menus[].items[].type: anchor`,
   `target: "#servicos"`). No WordPress: "Link personalizado" com URL
   **relativa** `#servicos` — nunca `http://localhost/slug/#servicos`, que
   quebra ao mudar de domínio (o WordPress não reescreve link
   personalizado). Fora da Home (página auxiliar, 404) o filtro
   `project_menu_anchor_href()` de `inc/menus.php` prefixa a URL da Home,
   então o item leva de volta à seção. Via wp-cli:
   `wp menu item add-custom menu-principal "Serviços" "#servicos"`.
4. **Item do logo/“Início”** aponta para o topo (`#inicio`, âncora do
   hero) ou para a Home — nunca `#` sozinho.
5. **O item da seção visível fica marcado** (scroll-spy) com
   `aria-current="location"`, estilizado como o "item ativo" da
   referência (se a referência não mostra estado ativo, use só o
   atributo, sem inventar visual).

## 3. Implementação (já no esqueleto do tema)

O `scripts/scaffold_wp_project.py --site-structure single_page` grava
`PROJECT_SITE_STRUCTURE` e `PROJECT_HEADER_BEHAVIOR` em `functions.php`;
`header.php`, `style.css` e `main.js` ligam o resto. Práticas adotadas e
por quê:

| Prática | Por quê |
|---|---|
| `position: sticky; top: 0` em vez de `fixed` | Continua no fluxo: sem `padding-top` compensatório no `body`, sem salto de layout (CLS) e sem conteúdo escondido sob o header no carregamento |
| Header filho **direto** do `<body>`; nunca `overflow: hidden/auto` em `html`, `body` ou wrapper do header | `sticky` para de funcionar dentro de ancestral com overflow. Para cortar rolagem horizontal use `overflow-x: clip` |
| `scroll-padding-top: var(--header-height)` no `html` | Âncora clicada, link externo com `#hash` e foco via Tab param **abaixo** do header (WCAG 2.4.11, foco não encoberto). Sem `scroll-margin` em cada seção, sem offset em JS |
| `--header-height` medido por `ResizeObserver` | Altura real em cada breakpoint e quando o header compacta; o fallback em CSS evita salto antes do JS |
| `scroll-behavior: smooth` **só** em `prefers-reduced-motion: no-preference` | Respeita quem desativou animações (WCAG 2.3.3) |
| `IntersectionObserver` para scroll-spy e `.is-scrolled`; **nenhum** listener de `scroll` | Não roda a cada pixel, não disputa a thread principal, sem throttle manual |
| Offset da barra de admin (`body.admin-bar`: 32px / 46px / 0 ≤600px) | Logado no WordPress, o header não fica embaixo da barra |
| Fundo opaco no header sticky | O conteúdo passa por baixo; header transparente sobre o hero precisa de um estado `.is-scrolled` com fundo (registre em `theme.header_scrolled`) |
| `z-index` via `--z-header` | Um valor só; modais e o skip link ficam acima |
| Skip link "Pular para o conteúdo" → `<main id="conteudo" tabindex="-1">` | Com header sempre presente, teclado e leitor de tela pulam o menu (WCAG 2.4.1) |
| Menu mobile: botão com `aria-expanded`/`aria-controls`, `Esc` fecha e devolve o foco, clique fora fecha, escolher item fecha | Na single page o item leva a uma seção da mesma página — o menu aberto cobriria o destino |
| Menu aberto com `max-height: calc(100dvh - header)` e `overflow-y: auto` | Menu longo rola por dentro e não passa da tela (`dvh` acompanha a barra do navegador mobile) |
| Progressive enhancement | Sem JS: header sticky e âncoras funcionam (CSS puro) e o menu mobile aparece aberto |
| `@media print { position: static }` | Header não se repete/encobre conteúdo na impressão |
| Hash não é reescrito durante a rolagem | `history` não vira uma pilha de `#secao` a cada rolagem; o botão Voltar continua útil |

Estado rolado (sombra, header compacto, troca de logo) só se a referência
ou o usuário definir — registre em `theme.header_scrolled`; não invente.

## 4. Multipáginas

- Itens de menu são páginas (`type: page`) ou arquivos de CPT
  (`type: archive`, URL dinâmica). O WordPress marca o item atual com
  `aria-current="page"` — estilize com o "item ativo" da referência.
- Header segue a referência: `theme.header_behavior: static` por padrão.
  Use `sticky` só se a referência mostrar (ex.: duas capturas do mesmo
  header em alturas diferentes) ou o usuário pedir — aí valem as mesmas
  práticas da seção 3 (`--header-behavior sticky` no scaffold).
- Âncora pontual dentro de uma página (ex.: "Ver planos" → `#planos`) é
  permitida, mas não transforma o site em single page.

## 5. Como validar (portão de QA)

`scripts/capture_site.py --blueprint` lê `site_structure` e
`header_behavior` e, quando o header é sticky, verifica em cada viewport:

- **header visível após rolar** até o meio e até o fim da página
  (P0 se sumir — navegação inutilizável);
- **toda âncora do menu existe** na página (P0 se não existir);
- **destino não fica encoberto**: após ir até cada âncora, o topo da
  seção fica abaixo do header (P1 se encoberto).

Interativo (claude-in-chrome), registrado no ledger: clicar cada item
do menu em desktop e mobile, conferir o item marcado pelo scroll-spy,
abrir/fechar o menu mobile (botão, `Esc`, escolher item), navegar com Tab
do skip link até o rodapé sem foco escondido atrás do header, e logado
no admin conferir que o header não fica sob a barra de administração.
