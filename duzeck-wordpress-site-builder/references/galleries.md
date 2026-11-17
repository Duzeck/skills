# Galerias de fotos

Toda galeria da referência entra em `galleries[]` do Blueprint; sem
nenhuma, `galleries: []` registra que a conferência foi feita.

## 1. Como identificar

| Sinal (`evidence`) | O que é |
|---|---|
| `photo_grid` | Várias fotos do mesmo assunto lado a lado, **só foto** (sem título/texto por item) |
| `thumbnails` | Foto grande + faixa de miniaturas (uma destacada) |
| `more_overlay` | "+12", "+12 fotos" sobre a última foto visível |
| `zoom_icon` | Lupa / ícone de ampliar sobre as fotos |
| `view_all_link` | "Ver todas as fotos", "Galeria completa" |
| `user` | O usuário disse |

Não é galeria:

- **grid de cards** — cada item tem título, texto ou botão (projetos,
  serviços): é CPT/repeater com `card_grid`;
- **carrossel de fotos** — bolinhas/setas: `carousels[]` com
  `kind: gallery` (ver `references/carousels.md`);
- **logos de clientes** — `carousels[]` `kind: logos` ou grid de logos;
- **uma foto só** — mídia comum (`media[]`).

## 2. O que registrar e o que perguntar

| Campo | De onde vem |
|---|---|
| `layout` | `grid` (mesma proporção), `masonry` (alturas diferentes, colunas), `featured_thumbs` (1ª grande + miniaturas) |
| `visible_count` | Quantas fotos aparecem na referência |
| `total_count` | Com "+N": `visible_count + N`. Sem "+N" e sem "ver todas": igual ao visível (omita) |
| `aspect_ratio` | Proporção das fotos na referência (não se aplica a masonry) |
| `per_row` | Colunas por breakpoint (sem referência mobile: inferência registrada) |
| `captions` | Legenda visível sob as fotos? |
| `lightbox` | **Pergunte**: a imagem não mostra se clicar amplia. Lupa, "+N" e "ver todas" sugerem que sim. Nunca presuma — `true`/`false` ou `uncertainty` bloqueante (subject = id) |
| `storage` | `acf_gallery:<campo>` (galeria do ACF PRO, padrão) ou `post_type:<cpt>` |

Espelho: as fotos visíveis são as da referência (recortes provisórios
com `crop_from_reference` ou fornecidas); fotos além das visíveis são
pedidas ao usuário ou marcadas como demo.

## 3. Implementação (`template-parts/gallery.php` + `assets/js/gallery.js`)

| Prática | Por quê |
|---|---|
| Lista semântica (`<ul role="list">` de `<figure>`) | Leitor de tela anuncia "lista, 8 itens" |
| Miniatura com `srcset`/`sizes` do WordPress (`medium_large`), `loading="lazy"` | Cada tela baixa o tamanho certo |
| Proporção fixa (`aspect-ratio` + `object-fit: cover`) | Sem salto de layout; fotos de tamanhos diferentes não quebram a grade |
| Fotos além do `visible` ficam em `<li hidden>` | Entram no lightbox, mas não são baixadas antes |
| "+N" `aria-hidden` + texto "(e mais N fotos)" para leitor de tela | O número visual tem equivalente falado |
| Cada miniatura é um **link** para a foto grande (`2048x2048`, não o original) | Funciona sem JS; o original de 6000 px não é servido |
| Lightbox com **`<dialog>` nativo** + `showModal()` | O navegador prende o foco, torna o resto inerte e fecha com Esc — sem biblioteca, sem reimplementar acessibilidade |
| Botão Fechar primeiro (recebe o foco), anterior/próxima com nome acessível, contador "3 de 8" em `aria-live` | Padrão de diálogo modal (W3C APG) |
| Setas ← → do teclado, gesto de arrastar, clique no fundo fecha | Teclado, toque e mouse |
| Foco volta para a miniatura clicada ao fechar | Ninguém perde a posição na página |
| Rolagem da página presa enquanto aberto | O fundo não rola atrás da foto |
| Pré-carrega **só a próxima** foto | Navegação fluida sem baixar a galeria inteira |
| `alt` vem da Biblioteca de Mídia (por foto) | Editável no admin; o QA aponta foto sem texto alternativo |
| `gallery.js` só registrado; o template-part enfileira | Página sem galeria não baixa nada |

Masonry usa colunas CSS: a ordem de leitura desce coluna por coluna —
aceitável para fotos; se a ordem importar, use `grid`.

Visual (espaçamento, "+N", lupa, cores do lightbox, ícones): da
referência; o lightbox não aparece na imagem, então segue a paleta dela.

## 4. Como validar

`scripts/capture_site.py --blueprint` aponta: galeria ausente (P0);
nº de fotos visíveis/total diferente do Blueprint, foto sem texto
alternativo, lightbox pedido e fotos não clicáveis (ou o contrário),
clique que não abre, seta que não avança, Esc que não fecha, foco que não
volta (P1).

Interativo: Tab dentro do lightbox nunca chega a um elemento da página
(o foco circula entre os controles e a barra do navegador), arrastar no
celular troca a foto, a foto grande é nítida em tela retina.
