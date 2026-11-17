# Acordeões, FAQ e abas

Conteúdo que aparece e some ao clicar. A referência estática mostra **um**
estado — um item aberto, uma aba ativa —; o resto é deduzido e perguntado.
Todo acordeão/FAQ entra em `accordions[]` e todo conjunto de abas em
`tabs[]`; sem nenhum, `accordions: []` / `tabs: []` registram que a
conferência foi feita.

## 1. Como identificar

**Acordeão** (`evidence`):

| Sinal | O que é |
|---|---|
| `plus_minus` | "+" à direita de cada linha; "−" na aberta |
| `chevron` | Setinha ˅ / ˄ à direita (girada na aberta) |
| `expanded_item` | Uma linha com texto embaixo, as demais só com o título |
| `question_list` | Títulos em forma de pergunta, empilhados, com divisores → **FAQ** |
| `user` | O usuário disse |

**Abas** (`evidence`):

| Sinal | O que é |
|---|---|
| `tab_row` | Fileira de rótulos curtos lado a lado sobre um único painel |
| `active_indicator` | Um rótulo sublinhado/com fundo/cor diferente — a aba ativa |
| `segmented_control` | Botões colados num bloco (estilo "Mensal / Anual") trocando o conteúdo abaixo |
| `user` | O usuário disse |

Não é acordeão/abas:

- **menu com dropdown** (setinha no menu do header) — é navegação (`menus[]`);
- **filtro de categorias** sobre um grid ("Todos / Residencial / Comercial"
  filtrando cards) — é taxonomia + filtro (`content-modeling.md`); abas
  trocam **conteúdo diferente**, filtro esconde/mostra itens da mesma lista;
- **botões de navegação para outras páginas** com o mesmo visual de abas —
  se cada rótulo leva a uma URL, são links (menu secundário), não abas;
- **lista de perguntas sem nada para abrir** (pergunta + resposta sempre
  visíveis) — é FAQ em lista: texto comum, `accordions` não se aplica.

Ambíguo → `uncertainty` bloqueante.

## 2. O que vem da imagem e o que é perguntado

| Campo | Da imagem | Pergunte |
|---|---|---|
| `item_count` / `tab_count` | Quantas linhas / rótulos | — |
| Títulos/rótulos | Literais (`copy`) | — |
| `open_in_reference` / `active_in_reference` | Qual está aberto / ativo (1 = primeiro) | — |
| Conteúdo dos itens fechados / abas inativas | **Não aparece** | Peça o texto; sem resposta, demo marcado (`items_content: demo`) |
| `exclusive` (acordeão) | Não aparece | Abrir um fecha o outro? Padrão sensato: FAQ curto = `true` |
| `mobile` (abas) | Só com referência mobile | `scroll` (abas rolam na horizontal) ou `stack` (painéis empilhados) — inferência registrada |
| `faq` / `structured_data` | Perguntas e respostas | — (JSON-LD é o padrão em FAQ) |
| `heading_level` | Hierarquia da página | Título da seção é h2 → itens h3 |

Modelagem: repeater na página (`repeater:home_faq_items`, subcampos
prefixados `home_faq_question` / `home_faq_answer` WYSIWYG) ou CPT quando o
mesmo FAQ aparece em várias páginas (`content-modeling.md`).

## 3. Implementação (esqueleto)

`template-parts/accordion.php`, `template-parts/tabs.php`,
`inc/disclosures.php`, `assets/js/disclosure.js`.

| Prática | Por quê |
|---|---|
| Acordeão com **`<details>`/`<summary>` nativos** | Abre/fecha sem JS; teclado (Enter/Espaço) e leitor de tela ("recolhido/expandido") prontos; o Ctrl+F do navegador encontra e abre texto de item fechado |
| "Um por vez" com o atributo **`name`** do `<details>` | Nativo nos navegadores atuais; o `disclosure.js` cobre quem não suporta (testado: sem suporte e sem o JS, 3 itens ficam abertos; com o JS, 1) |
| Título do item como heading (`<summary><h3>`) | A pergunta entra na navegação por títulos do leitor de tela |
| Ícone (+/−, seta) `aria-hidden`, triângulo nativo escondido | Visual da referência; o estado é anunciado pelo `<details>` |
| Abas no padrão **W3C APG** (ativação automática) | `role="tablist/tab/tabpanel"`, `aria-selected`, `aria-controls`/`aria-labelledby`, só a aba ativa no Tab, setas ←/→ circulam, Home/End |
| Painel focável (`tabindex="0"`) | Tab sai da fileira direto para o conteúdo |
| **Sem JS, todos os painéis aparecem**, cada um com título | Lê-se sem JS e buscadores indexam todas as abas; com JS o título repetido sai |
| `mobile: stack` troca abas ↔ painéis empilhados ao cruzar 768px | Abas apertadas no celular viram leitura corrida |
| `mobile: scroll` com `scroll-snap` | Fileira de abas rola sem estourar a tela |
| Cada item/painel com **id estável** (`<grupo>-<titulo>`) | Link direto `#home-faq-qual-a-garantia` abre o item / seleciona a aba e rola até ele (respeita o header sticky) |
| JSON-LD **FAQPage** gerado das MESMAS perguntas do admin, um bloco por página | Nunca diverge do que está na tela |
| `disclosure.js` só registrado; o template-part enfileira | Página sem acordeão/abas não baixa nada |

**SEO, com honestidade**: desde 2023 o Google só mostra o resultado
especial de FAQ para sites governamentais e de saúde. O JSON-LD continua
válido (outros buscadores e assistentes usam), mas não prometa o
destaque ao cliente.

Visual (ícone, divisores, aba ativa `[aria-selected="true"]`, item aberto
`[open]`): da referência.

## 4. Como validar

`scripts/capture_site.py --blueprint` aponta: acordeão/abas ausentes
(P0); quantidade diferente, itens abertos/aba ativa diferentes da
referência, item ou painel vazio, "um por vez" divergente do Blueprint,
FAQ sem JSON-LD ou com pergunta fora dele, abas sem inicializar, teclado
(End, seta circular) quebrado, link direto que não abre/seleciona, modo
`stack` que não empilha no celular (P1).

Interativo: leitor de tela anuncia "recolhido/expandido" e "aba 2 de 4";
Ctrl+F acha a resposta de um item fechado; testar o link direto vindo de
outra página.
