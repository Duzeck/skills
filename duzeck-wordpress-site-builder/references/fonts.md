# Fontes: hospedadas no site, leves e sem salto

A fonte é a primeira coisa que o visitante vê no título do hero. Ela é
carregada para não atrasar a página, para o texto não "pular" quando chega
e sem mandar dados do visitante para terceiros.

## 1. O que identificar na referência

| Na imagem | Registre em `fonts.families` |
|---|---|
| Família dos títulos e do texto (nome no arquivo de design, no PDF ou estimada pela forma) | `family` + `role` (heading, body, accent) |
| Pesos que **aparecem**: título 700, texto 400, botão 600, destaque 800... | `weights`: só esses. Cada peso estático é um arquivo |
| Itálico visível | `styles: [normal, italic]` |
| Peso do título do hero (acima da dobra) | `preload` |

Fonte estimada (`confidence: low`) entra em `uncertainties`: o usuário
confirma, ou a validação visual decide.

## 2. Decisões

| Campo | Padrão | Quando muda |
|---|---|---|
| `delivery` | **`self_hosted`**: arquivos no próprio site | `system` (sem fonte web, pilha do sistema); `google_cdn` só com `reason` |
| `fallback_metrics` | `true` | — |
| `source` | `google_fonts` | `provided`: arquivo do cliente, em `assets/fonts/` |
| `license` | `OFL` / `Apache-2.0` (Google Fonts) | `commercial` exige `license_note`: quem comprou e para qual domínio. Hospedar sem licença de web é infração |
| `preload` | O peso do título do hero + o do texto | No máximo **2 arquivos**. Mais que isso disputa banda com a imagem do hero (LCP) |

**Por que não o link do Google Fonts?** Os projetos anteriores usavam esse
link. Com ele:
- o navegador de **cada visitante** conecta no Google, que recebe o IP (dado pessoal na LGPD; um tribunal alemão condenou um site por isso em 2022);
- a página abre uma conexão extra antes de mostrar o texto.

Hospedado no site, nada disso acontece, e o arquivo vem do mesmo servidor
do HTML.

## 3. Implementação

1. **`scripts/fetch_fonts.py BLUEPRINT.yaml --theme <tema>`**, logo depois do scaffold:
   - baixa só os pesos declarados, em **woff2**, só o subconjunto **latin**, que cobre todo o português (acentos e cedilha);
   - fonte variável (Inter, Manrope...) vira **um arquivo** para vários pesos (`font-weight: 400 600`);
   - grava a licença da família ao lado (`LICENSE-<familia>.txt`);
   - gera `assets/css/fonts.css` com `font-display: swap` e `unicode-range`, mais o `manifest.json` (arquivos a pré-carregar).
2. **A reserva ajustada** (`'<Família> Fallback'`): uma `@font-face` com `local('Arial')` ou `local('Times New Roman')` e `size-adjust`, `ascent-override`, `descent-override` e `line-gap-override`.
   - Os valores são **calculados das métricas reais** da fonte: o script lê as tabelas da fonte e usa a largura média ponderada pela frequência das letras no português.
   - Até a fonte chegar, o texto ocupa o mesmo espaço.
3. **`scripts/generate_design_tokens.py`** insere a reserva na pilha: `'Manrope', 'Manrope Fallback', sans-serif`.
4. **`inc/fonts.php`** (esqueleto):
   - enfileira o `fonts.css` antes dos tokens;
   - pré-carrega os arquivos do manifesto via `wp_preload_resources`, com `crossorigin`: sem ele, o arquivo é baixado duas vezes.
5. O `style.css` do esqueleto aplica `--font-heading` aos títulos (h1–h6). Antes não aplicava: a fonte de título era baixada e não aparecia.

**Nunca**:
- `<link>` ou `@import` para `fonts.googleapis.com`;
- `@font-face` sem `font-display`;
- `.ttf`, `.otf` ou `.woff` (o woff2 tem metade do tamanho);
- peso usado no CSS sem arquivo: o navegador inventa um negrito borrado.

## 4. Como validar

**`scripts/capture_site.py --blueprint`**, seção "Fontes e estabilidade":
- **P1**:
  - fonte de outro domínio;
  - família ou peso usado que não carregou;
  - negrito sintético;
  - `font-display` bloqueante;
  - pilha sem a reserva ajustada;
  - reserva sem `size-adjust`;
  - preload sem `crossorigin` ou que nenhuma `@font-face` usa;
  - arquivo baixado duas vezes;
  - **CLS acima de 0,1** ao carregar, com os elementos que se moveram.
- **P2**:
  - peso sem arquivo próprio (o navegador usa o vizinho);
  - preload sem uso na página;
  - mais de 2 arquivos pré-carregados;
  - mais de ~250 KB de fontes.
- **Troca de fonte**: a Home é aberta duas vezes no desktop e no celular, uma com os arquivos de fonte bloqueados (só a reserva) e outra com eles.
  - O relatório mostra quanto cada texto se move e se o título muda o número de linhas.
  - Valores medidos no teste:

| | Sem reserva ajustada | Com reserva |
|---|---|---|
| Título no celular | 4 → 5 linhas | 5 → 5 linhas |
| Deslocamento do texto | até 46 px | 4–9 px |

**`scripts/check_theme.py`** avisa sobre:
- link do Google Fonts;
- `@font-face` sem `font-display`;
- arquivo que não é woff2;
- token de fonte sem `@font-face` que a carregue.
