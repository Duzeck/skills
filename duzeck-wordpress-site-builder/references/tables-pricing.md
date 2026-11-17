# Tabelas e preços

Toda tabela de dados entra em `tables[]` e todo bloco de planos/preços em
`pricing[]`; sem nenhum, `tables: []` / `pricing: []` registram que a
conferência foi feita.

## 1. Como identificar

**Tabela de dados** (`evidence`):

| Sinal | O que é |
|---|---|
| `grid_lines` | Linhas de grade entre células |
| `header_row` | Primeira linha em negrito/colorida nomeando as colunas |
| `zebra_rows` | Linhas alternando fundo |
| `aligned_numbers` | Coluna de números/valores alinhados à direita |
| `check_marks` | ✓ / ✗ / — em células → **comparativo** (`kind: comparison`) |
| `user` | O usuário disse |

É tabela quando o conteúdo é **dado cruzado** (linha × coluna): horários,
especificações técnicas, medidas, tabela de valores, comparativo de
planos. **Não** é tabela: grid de cards, colunas de layout (texto à
esquerda, imagem à direita), lista de recursos de um plano só, rodapé em
colunas.

**Preços** (`evidence`): `currency_symbol` ("R$"), `period_suffix`
("/mês", "/ano"), `plan_cards` (cards lado a lado com nome, preço,
recursos e botão), `featured_badge` ("Mais popular", card destacado),
`strikethrough` (preço antigo riscado), `billing_toggle` ("Mensal /
Anual"), `installments` ("12x de"), `user`.

## 2. Preço é dado de negócio: nunca inventado

Como telefone e endereço, **preço visto na referência pode ser mockup**
do designer. `price_source` é obrigatório:

- `user` — o usuário confirmou os valores;
- `demo` — fictício, listado em "Conteúdo demo identificado" do
  VALIDATION.md e trocado antes de publicar.

O validador bloqueia qualquer outro valor (inclusive "reference").
Vale também para tabela com coluna `currency`.

## 3. O que registrar e o que perguntar

| Campo | Da imagem | Pergunte |
|---|---|---|
| `columns` (`key`, `label` literal, `type`, `align`) | Cabeçalhos e o tipo de cada coluna (`text`, `number`, `currency`, `check`) | — |
| `row_count`, `plan_count` | Contagem | — |
| `caption` | Título da tabela, se houver | Sem título visível: proponha um e use `caption_visible: false` (o leitor de tela anuncia a tabela por ele) |
| `row_header` | A 1ª coluna nomeia a linha? | — |
| `mobile` (tabela) | Só com referência mobile | `scroll` (rola dentro da região — tabelas largas, comparativos) ou `cards` (cada linha vira card — poucas colunas, leitura linha a linha) |
| `billing`, `default_billing` | Períodos e o selecionado | Valores dos períodos não visíveis (o anual quando a imagem mostra o mensal) |
| `featured_plan` | Card destacado / selo | — |
| Valores | Só se confirmados | `price_source` |

Modelagem: preço é campo **number** do ACF (149.9), nunca texto
"R$ 149,90". Planos em repeater (`repeater:home_pricing_plans`, subcampos
prefixados: nome, descrição, `price_monthly`, `price_yearly`,
`old_price_*`, `installments_*`, `featured`, `badge`, recursos como
repeater interno `text` + `included`, CTA) ou CPT `plan` quando os
planos aparecem em várias páginas. Tabela: repeater com um subcampo por
`columns[].key` — o ACF não tem campo "tabela" nativo e o plugin que faz
isso é de terceiros.

## 4. Implementação (esqueleto)

`inc/pricing.php`, `template-parts/pricing.php`, `assets/js/pricing.js`,
`template-parts/table.php`.

| Prática | Por quê |
|---|---|
| `project_money()` formata `R$ 1.234,56` a partir de número ou texto ("149,90", "1.234", "R$ 99") | Formato único; "1.234" escrito no Brasil é mil duzentos e trinta e quatro |
| Centavos automáticos ("R$ 99" / "R$ 99,90") ou sempre | Como a referência mostra |
| Preço visual em partes (`R$` pequeno, centavos sobrescritos) **`aria-hidden`** + frase completa para leitor de tela | Sem isso o leitor lê "R cifrão 99 vírgula 90 barra mês" aos pedaços |
| Preço antigo vira "(antes R$ X)" na frase | `<del>` não é anunciado como riscado |
| Parcelas calculadas do total ("12 vezes de R$ 332,50 (total R$ 3.990)") | Valor da parcela nunca diverge do total |
| Selo "Mais popular" em **texto**; card com `aria-labelledby` no nome | O destaque não é só cor |
| Recursos com "Incluído:" / "Não incluído:" para leitor de tela; ✓/✗ `aria-hidden` (glifo padrão no CSS, troque pelo ícone da referência) | Ícone sozinho não é lido |
| CTA com o nome do plano para leitor de tela ("Assinar - Profissional") | Três botões "Assinar" iguais não dizem qual plano |
| Seletor Mensal/Anual: grupo de botões `aria-pressed`, troca anunciada em `aria-live` | Padrão de botão de alternância; sem duplicar o HTML dos cards |
| **Sem JS os preços de todos os períodos aparecem**, cada um com rótulo | Nenhum preço some sem JS |
| `<table>` com `<caption>`, `<th scope="col">`, `<th scope="row">` | O leitor de tela diz a que coluna/linha cada célula pertence |
| Tabela dentro de região **nomeada e focável** (`role="region"`, `aria-labelledby`, `tabindex="0"`) | Teclado consegue rolar a tabela larga (WCAG 2.1.1); a página não estoura (WCAG 1.4.10) |
| Número e valor com `white-space: nowrap` e `tabular-nums` | "R$" e "189,50" nunca se separam; colunas alinham |
| `position: relative` em todo contêiner com `overflow` | Sem isso o `.screen-reader-text` (absolute) escapa do recorte e estica a página (encontrado no teste) |
| `mobile: cards` com papéis ARIA explícitos (`role="table/row/cell"`) e "Coluna: valor" | `display: block` apaga a semântica de tabela em alguns navegadores; os papéis a mantêm |
| `pricing.js` só registrado; o template-part enfileira | Página sem seletor não baixa nada |

`check_theme.py` bloqueia preço escrito no template (`R$ 99` fora de
`content-defaults.php`) e avisa `<table>` escrita à mão.

## 5. Como validar

`scripts/capture_site.py --blueprint` aponta: tabela/planos ausentes
(P0); sem `<caption>`, cabeçalhos diferentes da referência, sem `scope`,
contagem de linhas, célula vazia, ✓/✗ sem texto, tabela fora de região
rolável focável, modo cards que não vira card ou perde os papéis ARIA;
contagem de planos, plano sem nome ou preço, preço fora do padrão
"R$ 1.234,56", recurso sem texto para leitor de tela, CTA sem destino,
destaque/selo ausente, seletor de período ausente, período inicial
diferente, troca que não troca os preços ou não é anunciada (P1).

Interativo: leitor de tela lendo um card de plano e uma linha do
comparativo; Tab até a tabela larga e setas rolando; valores conferidos
com o usuário.
