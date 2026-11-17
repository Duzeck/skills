# Editor de blocos com a cara do site (`theme.json`)

Quem escreve um post ou edita uma página deve ver as **cores, as fontes e
os tamanhos do site**, e escolher só entre eles. Sem isso, o editor oferece
a paleta padrão do WordPress (rosa, verde-limão, roxo...), qualquer cor e
qualquer tamanho, e o conteúdo sai da marca.

## 1. O que é gerado

`scripts/generate_design_tokens.py BLUEPRINT.yaml --out <tema>/assets/css/tokens.css --theme-json <tema>/theme.json`
gera os dois arquivos **da mesma fonte**, `design.tokens`:

| No editor | Vem de |
|---|---|
| Paleta (nomes em português: Principal, Fundo, Texto...) | `tokens.color`, exceto camadas como `overlay` |
| Fontes "Títulos" e "Texto", com a reserva ajustada | `tokens.font_family` |
| Tamanhos ("Título do topo", "Título 2", "Texto"...) | `tokens.font_size` |
| Espaços | `tokens.space` |
| Largura do conteúdo | `tokens.layout.container_max` |

Fica desligado:
- cor livre;
- gradientes;
- duotone;
- paletas e tamanhos padrão do WordPress;
- tamanho livre;
- capitular.

`inc/editor.php` carrega `fonts.css`, `tokens.css` e `editor.css` dentro
da área de edição. Os títulos aparecem em Manrope e o texto em Inter, com
os arquivos do próprio site.

## 2. Por que só `settings` (nunca `styles`)

O `styles` do `theme.json` vira CSS no front-end (cor de link, fundo,
peso dos títulos, espaço entre blocos) e passa por cima do `style.css`,
o que quebra o espelho da referência. No teste:
- **com só `settings`**: a página com títulos, lista, citação, botão e colunas ficou **idêntica pixel a pixel** (0 pixel diferente no desktop e no celular);
- **com um `styles` típico**: cerca de 5.400 pixels mudaram (links e títulos).

O WordPress mantém as classes da paleta antiga no CSS, então conteúdo
antigo que usava essas cores não quebra.

O `editor.css` só repete regras que existem no site; nunca inventa
(ex.: cor de link). Estilos de conteúdo do projeto (`.entry-content`)
são copiados para lá.

## 3. Como validar

`scripts/check_theme.py` avisa quando:
- o `theme.json` está ausente (havendo `tokens.css`);
- tem `styles`;
- permite cor livre ou a paleta padrão;
- a paleta difere do `tokens.css` (desatualizado: regere os dois juntos).

Conferência no editor (opcional, no QA): abrir uma página no painel e
ver:
- a paleta da marca e só ela;
- os títulos na fonte de título;
- nenhum seletor de cor livre.
