# Carrosséis e banners rotativos

Uma imagem estática mostra **um** estado do carrossel (o primeiro slide).
A rotação não aparece: ela é deduzida por sinais visuais e confirmada com
o usuário. Todo carrossel entra em `carousels[]` do Blueprint; se não houver
nenhum, `carousels: []` registra que a conferência foi feita.

## 1. Como identificar (passe obrigatório do inventário)

Percorra cada seção do `reference_map` procurando:

| Sinal (`evidence`) | O que é | O que indica |
|---|---|---|
| `dots` | Bolinhas/traços em fila, um destacado, abaixo ou sobre o conteúdo | Carrossel; **nº de bolinhas = `slide_count`** (ou de posições de parada, se mostra vários por vez) |
| `arrows` | Setas ‹ › ou botões redondos nas laterais/canto | Navegação manual |
| `counter` | "01 / 05", "1 de 3" | Carrossel; total = `slide_count` |
| `progress_bar` | Barra/traço que parece preencher, junto às bolinhas | Quase sempre autoplay |
| `cut_item` | Último card cortado na borda do container/tela | Carrossel horizontal ou rolagem lateral |
| `user` | O usuário disse ("o banner do topo gira") | Confirmação direta |

Banner rotativo no topo: hero de largura total **com** `dots`, `arrows`,
`counter` ou `progress_bar` → `kind: hero_banner`. Sem nenhum desses sinais
é um hero comum: **não** invente rotação.

Falsos positivos a descartar:

- bolinhas de **paginação** de uma lista (links "1 2 3" para outras
  páginas) — é paginação do WordPress, não carrossel;
- indicadores de **etapas** (passo 1 → 2 → 3) e decoração (pontos de
  textura, divisores);
- grid com todos os itens visíveis e nenhum sinal acima.

Ambíguo (um sinal fraco, como só um card cortado) → `uncertainty`
bloqueante: "A seção X é um carrossel ou um grid fixo?".

## 2. O que a imagem não responde — perguntar

| Pergunta | Campo | Se o usuário não souber |
|---|---|---|
| Gira sozinho? | `autoplay` | Recomende **sem autoplay** em carrossel de cards/depoimentos; em `hero_banner` com `progress_bar`, autoplay de 6 s com pausa |
| A cada quantos segundos? | `interval_ms` | 6000 (mínimo aceito 3000; abaixo de 5000 dá pouco tempo de leitura) |
| Volta ao início depois do último? | `loop` | `true` com autoplay; `false` sem |
| Conteúdo dos slides 2..N | `slides_content` | `demo` marcado + pedido do conteúdo real antes de publicar |
| Quantos aparecem por vez no tablet/celular? | `per_view` | Sem referência mobile: 1 no mobile, metade do desktop no tablet (registre como inferência) |

`autoplay` nunca fica "talvez": `true`, `false` ou `uncertainty`
bloqueante com `subject` igual ao `id` do carrossel (o validador cobra).

Espelho: o **slide 1** é o que a referência mostra — texto literal, mesma
imagem/recorte. Slides seguintes nunca são inventados como reais.

## 3. Modelagem (admin)

- Slides **sempre** editáveis: `storage` diz onde.
  - `repeater:<campo>` (ACF PRO) — banner do topo, destaques; subcampos
    prefixados (`home_banner_slide_title`, `_image`, `_cta_label`,
    `_cta_target`); `min: 2` e `max` coerente.
  - `post_type:<cpt>` — quando o item tem vida própria (depoimentos,
    projetos, logos de clientes reutilizados em outras páginas).
- A seção do carrossel tem entrada em `editable_content`.
- Comportamento (`autoplay`, `interval_ms`) é decisão do Blueprint, fixo
  no template. Só vire campo do admin se o usuário pedir.

## 4. Implementação (componente do esqueleto)

`template-parts/carousel.php` + `assets/js/carousel.js` + bloco
"Carrossel" do `style.css`. **Não** use Slick/Owl/Swiper/Flickity etc.
(`check_theme.py` avisa): peso, CDN externo, jQuery e acessibilidade a
refazer — o componente próprio já cobre tudo abaixo e é dado pelo
Blueprint.

| Prática | Por quê |
|---|---|
| Trilho em CSS `scroll-snap` | Sem JS continua utilizável (arrastar, trackpad, teclado) — progressive enhancement; swipe nativo no celular, sem biblioteca de gestos |
| `<section aria-roledescription="carrossel" aria-label>` e cada slide `role="group" aria-roledescription="slide" aria-label="N de T"` | Padrão W3C APG "Carousel": o leitor de tela anuncia o que é e onde está |
| Botão de pausa **primeiro** na ordem de tabulação quando há autoplay | WCAG 2.2.2 (pausar, parar, ocultar) e APG |
| Pausa ao passar o mouse, ao focar qualquer coisa dentro, com a aba oculta e fora da tela (`IntersectionObserver`) | Ninguém perde o slide que está lendo; não gasta CPU fora de vista |
| `prefers-reduced-motion` → começa **pausado** (o usuário pode dar play) e rolagem sem animação | WCAG 2.3.3; respeita a preferência do sistema |
| `aria-live="off"` com autoplay, `"polite"` parado | Leitor de tela não é interrompido a cada troca automática |
| Slides fora da tela com `inert` | Tab não entra em link invisível |
| Bolinhas = posições de parada (`slides − por_vez + 1`), `aria-current` na ativa | Com 3 por vez e 5 slides são 3 paradas, não 5 bolinhas mortas |
| Setas ← → no trilho focado | Navegação por teclado |
| Setas/bolinhas/pausa com área ≥ 24px | WCAG 2.5.8 |
| Primeiro slide: imagem `loading="eager"` + `fetchpriority="high"` (`project_media(..., ['loading' => 'eager'])`); demais `lazy` | O slide 1 é o LCP; os outros não competem no carregamento |
| Um único `<h1>` (no slide 1, se ele for o título da página); demais `<h2>` | Hierarquia de headings válida |
| `carousel.js` só **registrado**; o template-part enfileira | Páginas sem carrossel não baixam o arquivo |
| Altura estável (proporção fixa via `.media-frame`) | Sem salto de layout (CLS) ao trocar de slide |

Visual (forma e posição das setas, bolinhas, botão de pausa, bolinha
ativa) vem da referência. Se a referência não mostra botão de pausa e há
autoplay, ele entra mesmo assim — discreto, no estilo das bolinhas — e
vira desvio intencional registrado (exigência de acessibilidade).

Responsivo: um grid no desktop **não** vira carrossel no mobile por
inferência. Só se houver referência mobile ou decisão aprovada.

## 5. Como validar

`scripts/capture_site.py --blueprint` (contexto com movimento reduzido —
a captura mostra sempre o slide 1, comparável com a referência) aponta
por página e viewport:

- carrossel do Blueprint **ausente** na página (P0);
- nº de slides diferente de `slide_count`, autoplay diferente do
  Blueprint, setas/bolinhas pedidas e ausentes, seta "próximo" que não
  avança, JS não inicializado, autoplay sem pausa ou girando com
  movimento reduzido (P1).

Interativo (claude-in-chrome), no ledger: autoplay troca no intervalo e
para no hover/foco/botão; Tab chega primeiro no botão de pausa; setas e
bolinhas levam ao slide certo; arrastar no celular para slide a slide;
o slide 1 bate com a referência em todos os viewports.
