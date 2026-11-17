# Depoimentos e logos de clientes (prova social)

Todo bloco de depoimentos entra em `testimonials[]` e toda faixa/grade
de logos em `client_logos[]`; sem nenhum, `testimonials: []` /
`client_logos: []` registram que a conferência foi feita.

## 1. Regra principal: o da referência é mockup até prova em contrário

Depoimentos e logos da referência quase sempre são **inventados pelo
designer**: nomes genéricos, fotos de banco de imagem, falas vagas,
marcas fictícias. Publicá-los como reais é:

- **depoimento**: propaganda enganosa (CDC art. 37; Código do CONAR) e
  avaliação falsa para o Google;
- **logo**: uso de marca de terceiro sugerindo endosso.

Por isso:

| Campo | Valores | Efeito |
|---|---|---|
| `testimonials[].content_source` | `user` (fornecidos pelo cliente) / `demo` | Obrigatório. `user` exige `consent: true` (autorização para publicar nome/foto/fala — LGPD) |
| `client_logos[].permission` | `confirmed` (clientes reais que autorizaram) / `demo` | Obrigatório. `confirmed` exige `files: provided` ou `pending` |

**Trava técnica**: os template-parts recebem `demo => true` e **não
renderizam conteúdo demo em produção** (`WP_ENVIRONMENT_TYPE=production`);
em local/homologação aparece normalmente para validar o layout. O
administrador logado vê um aviso; o visitante, nada. A cópia literal da
referência (inventário `copy`) serve para o espelho do layout, não torna
o conteúdo real.

## 2. Como identificar

**Depoimentos** (`evidence`): `quote_marks` (aspas grandes “ ”),
`quote_text` (texto em itálico/entre aspas), `author_name` (nome abaixo da
fala), `author_photo` (foto redonda), `rating_stars` (★★★★★),
`source_badge` (logo do Google, Reclame Aqui, "via Facebook"), `user`.
Em carrossel (bolinhas/setas): `layout: carousel` + `carousels[]`
`kind: testimonials`.

**Logos** (`evidence`): `logo_row` (fileira de marcas), `grayscale_logos`
(todas em cinza), `section_title` ("Clientes", "Parceiros", "Quem confia
em nós", "Empresas atendidas"), `marquee` (faixa cortada nas bordas
sugerindo rolagem contínua), `certification_badges` (selos ISO, prêmios —
mesma regra de permissão), `user`.

Não confundir: logos de **redes sociais** (são links, `global_settings`),
**formas de pagamento** no rodapé (ícones da biblioteca), **logo da
própria empresa**.

## 3. O que registrar e perguntar

| Campo | Da imagem | Pergunte |
|---|---|---|
| `item_count` / `logo_count` | Contagem | — |
| `fields_shown` | O que cada depoimento mostra: `photo`, `role`, `company`, `city`, `rating`, `source` | — |
| `layout` | grid / list / single / carousel; logos: grid / row / marquee / carousel | Faixa parada ou rolando, se ambíguo |
| Conteúdo | Só o layout | Os depoimentos reais (texto, nome, autorização) e a lista real de clientes com permissão e arquivos |

Modelagem: depoimentos em CPT `testimonial` (campos prefixados,
`public: false`, ver `content-modeling.md`) ou repeater; nota (`rating`)
como número 0–5 com meia. Logos em repeater (`nome`, `logo` imagem,
`url` opcional) ou CPT `client` se reaparecerem em cases/projetos.

Logos: **nunca** redesenhados nem recortados da referência para ir ao
ar; vêm da própria empresa (PNG/WebP com fundo transparente; SVG só com
plugin de sanitização, porque o WordPress bloqueia upload de SVG por
segurança — decisão registrada).

## 4. Implementação (esqueleto)

`inc/social-proof.php`, `template-parts/testimonials.php`,
`template-parts/client-logos.php`, `assets/js/client-logos.js`.

| Prática | Por quê |
|---|---|
| Lista de `<figure>` com `<blockquote>` (fala) e `<figcaption>` (autor) | Associa a fala a quem disse |
| Nome em `<span>`, **não** em `<cite>` | Pela especificação HTML, `<cite>` é título de obra, não pessoa |
| Foto do autor com `alt=""` | Decorativa: o nome já está escrito ao lado |
| Estrelas: faixa ★★★★★ preenchida até a nota (meia estrela) `aria-hidden` + "Avaliação: 4,5 de 5" | Ícone sozinho não é lido |
| Cor das estrelas por variável (`--star-color`), nunca `currentColor` | O `color: transparent` do recorte zera o `currentColor` e as estrelas somem (encontrado no teste) |
| **Sem** JSON-LD `Review`/`AggregateRating` | Desde 2019 o Google não mostra estrelas para avaliação da empresa sobre si mesma; pode ser tratado como spam (`check_theme.py` bloqueia) |
| Logo: `alt` = **nome da empresa** (sobrepõe o alt da Mídia) | É o que o leitor de tela lê e, com link, o texto do link |
| Caixa de mesma altura + `object-fit: contain` | Logo largo e logo quadrado com peso visual parecido |
| Cinza → cor no hover/foco só em CSS | Visual da referência sem afetar acessibilidade |
| Link do logo abre em nova aba **anunciado** ("abre em nova aba") | Sem surpresa para quem usa leitor de tela |
| Marquee **só com JS**: lista duplicada para o loop com a cópia `aria-hidden` + `inert` | Leitor de tela e Tab encontram cada empresa uma vez |
| Botão de pausa, pausa no hover/foco, parado com movimento reduzido, parado sem JS | WCAG 2.2.2 e 2.3.3 |
| Velocidade constante (~40 px/s) qualquer que seja a quantidade de logos | Não acelera com poucos logos |
| Viewport da faixa com `position: relative` + `overflow: hidden` | Texto de leitor de tela dentro não estica a página |

## 5. Como validar

`scripts/capture_site.py --blueprint` aponta: bloco ausente (P0; demo em
produção fica oculto de propósito); contagem, depoimento sem texto/nome,
estrelas sem "N de 5", foto ausente quando a referência mostra, JSON-LD
autopromocional; logo com `alt` vazio ou "logo", item sem logo nem nome,
faixa sem cópia `aria-hidden/inert`, sem botão de pausa ou se movendo
com movimento reduzido (P1).

Antes de publicar: conferir no VALIDATION.md que nenhum bloco está
`demo`/sem permissão, e acessar o site com `WP_ENVIRONMENT_TYPE=production`
para ver que nada de demo aparece.
