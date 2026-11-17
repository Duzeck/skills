# Header e menu

O header é declarado no objeto `header` do Blueprint (estrutura); os
itens do menu em `menus[]`. Comportamento de rolagem (sticky, âncoras,
scroll-spy) está em `references/navigation.md`. A estrutura fica no
código (`project_header_config()` em `inc/header.php`); o conteúdo
(logo, rótulo/destino do botão, contatos da barra superior, itens do
menu) fica no admin.

## 1. Como ler o header na imagem

| Sinal (`header.evidence`) | O que registrar |
|---|---|
| `logo` | Posição → `layout`: `logo_left`, `logo_center` (logo em cima, menu embaixo), `logo_center_split` (menu dos dois lados do logo — dois locais de menu) |
| `nav` | Itens **literais** e na ordem em `menus[]`; o item ativo da imagem indica o estilo de `aria-current` |
| `cta_button` | Botão de destaque ("Solicitar Orçamento") → `cta: { label, target }` — destino real, nunca `#` |
| `top_bar` | Faixa acima do header → `top_bar`: `phone`, `whatsapp`, `email`, `hours`, `social`, `text` (do dado único) |
| `search_icon`, `account_icon`, `cart_icon`, `language` | `actions`. Carrinho exige WooCommerce; idioma exige plugin multilíngue — decisões arquiteturais |
| `dropdown_indicator` | Setinha ao lado de um item → `submenus: dropdown` (`mega` para painéis com colunas) |
| `transparent_over_hero` | Header sobre a foto do hero → `transparent: true` + `logo_light` + `theme.header_scrolled` |

O que a imagem desktop **não mostra** e precisa ser decidido:
- `mobile_menu`: `dropdown` (painel desce do header), `offcanvas` (lateral)
  ou `fullscreen` — referência mobile ou decisão registrada;
- `theme.header_scrolled` (fundo/cor ao rolar) quando transparente;
- o conteúdo dos submenus quando eles aparecem fechados.

## 2. Implementação (esqueleto)

`header.php`, `inc/header.php`, `template-parts/header-topbar.php`,
`assets/js/main.js` (blocos 4–6), CSS "Header" em `style.css`.

| Prática | Por quê |
|---|---|
| Logo: imagem da Mídia com `width`/`height`, `alt` = nome da empresa, `rel="home"`, `loading="eager"` **sem** `fetchpriority` | Sem salto de layout; o LCP é o hero, não o logo |
| Logo claro (`company_logo_light`) só enquanto o header transparente está sobre o hero | Legível nos dois estados |
| Botão de destaque do admin (`header_cta_label` / `header_cta_target`) | Editável; nunca fixo |
| Barra superior com `tel:+55`/`mailto:`/redes do dado único | Mesmos helpers do rodapé |
| Busca em `<details>` nativo: abre sem JS; com JS foca o campo, Esc e clique fora fecham | Nada de ícone que não faz nada |
| Ícones de ação com nome para leitor de tela; área ≥ 44px | Ícone sozinho não é lido |
| **Submenu: padrão W3C "disclosure"** — botão ao lado do item com `aria-expanded`/`aria-controls` e "Submenu de <item>" | Hover-only não funciona no teclado nem no toque |
| Enter/clique abre, **seta para baixo** leva ao primeiro item, **Esc** fecha e devolve o foco, sair com Tab fecha, clique fora fecha; hover só como conveniência em desktop com mouse | Comportamento previsível; mouse continua prático |
| **Sem JS**: o submenu abre com `:hover` **e** `:focus-within` | Focar o item pai abre; Tab entra no submenu e sai fechando (testado) |
| Celular: o menu abre um **painel** (menu + ações + botão); submenu vira acordeão dentro dele; **Esc em camadas** (submenu, depois painel) | Um Esc não derruba tudo |
| Header transparente: margem negativa = altura real (medida pelo JS) — o hero fica por baixo **sem** tirar o header do fluxo (sticky continua funcionando) | Sem `position: absolute` frágil |
| No estado transparente os links **herdam** a cor do header | Senão ficam no azul padrão sobre a foto, quase ilegíveis (encontrado no teste) |
| Ao rolar (sticky): fundo opaco, cor normal, logo padrão; menu mobile aberto também ganha fundo | Legível sobre o conteúdo |
| Linhas do header quebram (`flex-wrap`) em largura intermediária | Nunca estoura a tela antes de virar hambúrguer |
| `position: relative` no painel rolável do menu | Texto de leitor de tela não estica a página |

`check_theme.py` avisa CSS de submenu que abre só no `:hover` sem
`:focus-within`.

## 3. Como validar

`scripts/capture_site.py --blueprint` aponta em toda página: header
ausente (P0); logo sem link para a Home, sem nome ou sem `width/height`;
itens do menu diferentes da referência (rótulo, ordem, quantidade);
botão de destaque ausente, com outro texto ou sem destino; barra superior
ausente ou com `tel:`/`mailto:` inválidos; busca/ícones sem nome
acessível; item com submenu sem botão (hover-only), botão sem
`aria-expanded`/`aria-controls`; Enter que não abre, Esc que não fecha
ou não devolve o foco, seta para baixo que não entra no submenu; no
celular, botão do menu ausente, painel que não abre ou Esc que não fecha;
na Home com header transparente, fundo no topo, links com cor diferente
da do header (contraste) e, com sticky, sem fundo ao rolar (P1).

Interativo: contraste real do texto sobre a foto do hero (a captura
checa a herança de cor, não a foto), tablet entre 768 e 1024px, e o
menu mobile com leitor de tela.
