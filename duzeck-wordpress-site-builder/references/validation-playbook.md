# Playbook de validação

## Arquitetura

- Toda página tem template definido.
- Todo conteúdo dinâmico identificado tem modelo (CPT/campos/taxonomia).
- Todo CPT tem finalidade registrada (não existe "porque sim").
- Todo campo tem finalidade registrada.
- Nenhum dado global está duplicado em mais de um arquivo do tema.
- Toda taxonomia tem uso real (filtro, navegação ou agrupamento visível).
- Todo plugin tem justificativa.
- Toda dependência está resolvida.
- Nenhuma incerteza crítica está em aberto.

Rode `scripts/validate_blueprint.py` para checar isso automaticamente
antes de prosseguir — ele cobre os itens verificáveis mecanicamente
(campos obrigatórios presentes, status válidos, duplicação de globais).
O que exige julgamento (ex.: "o CPT realmente tem finalidade clara?")
continua sendo revisão manual sua.

## Funcional

- Tema ativa sem erro fatal (`wp theme status`).
- CPTs e taxonomias aparecem no admin e aceitam criar/editar conteúdo.
- Campos ACF salvam e exibem corretamente no front-end.
- Menus renderizam e apontam para as URLs corretas.
- Formulário envia e-mail (ou, no mínimo, mostra confirmação sem erro —
  envio real de e-mail pode não funcionar em XAMPP/WAMP local sem SMTP
  configurado; registre isso como limitação conhecida, não como falha
  silenciosa).
- Imagens carregam (sem 404 de mídia).

## Técnico

- `php -l` sem erro de sintaxe em todos os arquivos do tema
  (`scripts/check_theme.py`).
- Console do navegador sem erro JavaScript ao navegar pelas páginas
  principais.
- Nenhum link interno quebrado (404).
- Nenhuma imagem quebrada.
- Estrutura de arquivos segue `references/wordpress-architecture.md`
  (nada de lógica de CPT solta em `functions.php`).
- **Segurança**: `scripts/check_security.py --url <home> --path <pasta>
  --out documentation/qa/seguranca.json` sem P1 (XML-RPC fechado, login
  sem vazar por `?author=`/`/author/`/REST, erro de login genérico, sem
  listagem de pastas, editor de arquivos bloqueado, senha de admin não
  óbvia). P2 (versão exposta, cabeçalhos) entram no ledger. Exceções só as
  aprovadas em `security.exceptions`. Ver `references/security-seo.md`.
- **Desempenho e imagens**: a tabela do `report.md` sem P1 (foto acima de
  400 KB, página acima de 3 MB, LCP/TTFB ruins); P2 entram no ledger. Ver
  `references/performance.md`. **Ícone e sinais**: Home com Ícone do site,
  manifesto válido, `theme-color` e feed (`references/site-icon.md`).
- **Antes de publicar**: `prelaunch_check.py` sem P0/P1
  (`references/go-live.md`); com site antigo, `build_redirects.py --check`
  sem falha (`references/redirects.md`).
- **robots.txt**: a seção do `report.md` sem P0/P1 (buscadores liberados,
  robôs de IA como `seo.ai_crawlers`). **Editor**: `check_theme.py` sem aviso
  de `theme.json` (ver `references/editor.md`).
- **Fontes e estabilidade**: a seção do `report.md` sem P1 (fontes só do
  próprio domínio, pesos usados carregados, `swap`, reserva ajustada, preload
  com `crossorigin`, CLS até 0,1). A linha "Troca de fonte" mostra quanto o
  texto se move na troca; título que muda de linhas é P2. Ver
  `references/fonts.md`.
- **SEO**: a seção "SEO por página" do `report.md` da captura sem P1
  (título, descrição aprovada e única, canônico, `og:*`, imagem de
  compartilhamento que abre, `noindex` só onde o Blueprint pede, JSON-LD
  válido com a empresa na Home).

## Visual — portão de QA bloqueante

A validação visual é um **portão**: a entrega só acontece com
`Resultado final: passed` no `VALIDATION.md`. Servidor respondendo, tema
ativo, `check_theme.py` OK ou "a página abriu" **não são** validação
visual. Se não for possível capturar a referência ou a implementação, ou
compará-las, o resultado é `blocked` — com o motivo nomeado — e você não
declara o site como fiel à referência.

### Procedimento

1. **Normalize a evidência.** Para cada referência, registre página,
   breakpoint que ela representa (ou "desktop inferido"), estado (menu
   aberto/fechado, hover etc.) e regiões ausentes ou ambíguas.
2. **Capture no mesmo viewport.** Rode `scripts/capture_site.py` com
   `--blueprint` e `--ref` (ver `references/local-environment.md`): ele
   captura todas as páginas em desktop **1440**, tablet **834** e mobile
   **390** e gera os `compare-*.png` lado a lado. Os candidatos a P0
   técnico que ele aponta (rolagem horizontal, erro de JS, imagem
   quebrada, HTTP de erro) entram direto no ledger. Use `claude-in-chrome`
   (em single page, siga o roteiro interativo de `references/navigation.md`
   seção 5: cada item do menu, scroll-spy, menu mobile, Tab, barra de admin;
   com carrossel, o de `references/carousels.md` seção 5; formulário e mapa:
   `references/forms.md` seção 7 e `references/maps.md` seção 4; galeria e
   vídeo: `references/galleries.md` e `references/videos.md` seção 4; acordeão,
   FAQ e abas: `references/disclosures.md` seção 4; tabelas e preços:
   `references/tables-pricing.md` seção 5; depoimentos e logos:
   `references/social-proof.md` seção 5; equipe e números:
   `references/team-stats.md` seção 5; blog: `references/blog.md` seção 5;
   rodapé e redes: `references/footer-social.md` seção 4; header e menu:
   `references/header-menu.md` seção 3; hero e banners (contraste medido):
   `references/hero-banners.md` seção 4; SEO: `references/security-seo.md`
   seção 3)
   para estados que a captura estática não pega (hover, menu mobile
   aberto, formulário, filtros). Iguale também estado e conteúdo (mesmo
   número de cards, menu fechado) antes de julgar — diferença de
   enquadramento ou densidade de pixel não é achado. Saída do script com
   código 2 (site fora do ar, Playwright ausente) = portão `blocked`.
3. **Compare em dois níveis.**
   - *Visão inteira*: composição, ordem das seções, proporções, hierarquia.
   - *Recortes por região* (header, hero, cada seção, footer): tipografia,
     espaçamento, alinhamento, ícones, botões, bordas, sombras. Não
     aprove só pela visão inteira quando os detalhes não estão legíveis
     nela.
   Coloque referência e captura lado a lado na mesma análise, não em
   momentos separados de memória.
4. **Registre no ledger** do `VALIDATION.md` cada divergência: página,
   breakpoint, região, esperado (referência), renderizado, severidade,
   e correção aplicada **ou** desvio intencional com motivo. Nunca
   reinterprete o design em silêncio.
5. **Corrija na ordem de prioridade** (abaixo), recapture no mesmo
   viewport e estado, e atualize o ledger citando a rodada.
6. **Feche o portão** com `passed` (nenhum P0/P1/P2 aberto) ou `blocked`
   (com o motivo).

### Ordem de prioridade de correção

Corrija sempre o maior desvio primeiro, nesta ordem — não faz sentido
ajustar sombra com o grid errado:

1. Composição (seções presentes, ordem, grid/colunas)
2. Proporções e container (largura máxima, alturas relativas, gutters)
3. Hierarquia (o que chama atenção primeiro)
4. Tipografia (família, peso, escala, altura de linha)
5. Espaçamento e densidade
6. Cor (paleta, contraste, fundos)
7. Mídia (imagens, recorte, proporção, `object-fit`)
8. Ícones, botões e detalhes de controle
9. Microinteração (hover, transição)

### Régua de severidade (P0–P3)

| Severidade | Critério | Ação |
|---|---|---|
| **P0 — Crítica** | Elemento/seção ausente, seção na ordem errada, conteúdo ilegível, quebra de layout ou rolagem horizontal em algum breakpoint, navegação ou CTA principal inutilizável | Corrigir antes de qualquer outra coisa; bloqueia a entrega |
| **P1 — Maior** | Divergência que o usuário nota de imediato: proporção/espaçamento visivelmente diferente (>~20%), cor claramente errada, família ou peso tipográfico errado, hierarquia invertida | Corrigir no mesmo ciclo; bloqueia a entrega |
| **P2 — Moderada** | Deriva visual moderada: espaçamento ou alinhamento inconsistente, estado de hover/foco ausente, problema responsivo que altera conteúdo acima da dobra, quebra de linha ou densidade | Corrigir antes da entrega; bloqueia a entrega |
| **P3 — Menor** | Refinamento: diferença sutil de sombra/borda/raio, pequena variação de espaçamento (<~20%) sem impacto na hierarquia | **Não** gera novo ciclo; registre como nota de acompanhamento no `VALIDATION.md` |

Equivalência com a nomenclatura antiga: Crítica = P0, Maior = P1/P2,
Menor = P3.

### Diferença visual com causa estrutural

Diferenças puramente visuais (P0–P3) podem ser corrigidas diretamente.
Se a causa raiz for estrutural (ex.: "o grid está errado porque modelei
como 2 colunas e o layout tem 3" é ajuste de CSS; mas "faltam 3 dos 6
projetos porque o Blueprint só previu 3" é estrutural) — trate como
mudança de Blueprint, não como ajuste visual.

## Acessibilidade

Ver checklist completo em `references/accessibility-guidelines.md`. Não é
uma auditoria WCAG exaustiva — é uma checagem de baseline (AA) de HTML
semântico, alt text, navegação por teclado e contraste.

## Ciclo de correção

```
FATIA CRÍTICA (tokens + header + hero) → CAPTURA → COMPARAÇÃO → LEDGER
   → CORREÇÃO por prioridade → RECAPTURA → (sem P0/P1) → PROPAGA para
   demais seções/páginas → mesmo laço → PORTÃO: passed | blocked
```

Valide a fatia crítica antes de propagar o sistema: erro de grid,
container, fonte ou escala descoberto ali custa uma correção; descoberto
no fim, custa uma correção por página.

Repita até não haver P0/P1/P2 abertos. P3 não gera novo ciclo — fica
registrado como nota de acompanhamento no `VALIDATION.md`. Se o usuário
quiser entregar com P2 aberto, isso é decisão dele: pergunte, não decida
sozinho que "está bom o suficiente", e registre o aceite explícito no
ledger.
