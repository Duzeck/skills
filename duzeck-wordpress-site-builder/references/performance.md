# Desempenho e imagens

A captura (`scripts/capture_site.py`) mede o carregamento de cada página
em cada tamanho de tela. É medido **no ambiente local**: os números servem
para achar excessos e comparar antes/depois, não como o tempo real da
produção.

## 1. O que é medido

| Medida | Bom | Precisa melhorar (P2) | Ruim (P1) |
|---|---|---|---|
| Resposta do servidor (TTFB) | < 800 ms | 800–1800 ms | > 1800 ms |
| Primeira pintura (FCP) | < 1800 ms | 1800–3000 ms | > 3000 ms |
| Maior elemento (LCP), com o elemento | < 2500 ms | 2500–4000 ms | > 4000 ms |
| CLS (pulo do layout) | ≤ 0,1 | — | > 0,1 (ver `references/fonts.md`) |
| Peso da página | — | — | > 3 MB |
| Arquivos baixados | — | > 80 | — |
| Elementos no HTML | — | > 1.500 | — |
| JavaScript / CSS | — | > 500 KB / > 200 KB | — |

O relatório mostra a tabela "Desempenho e imagens" com o peso por tipo
(JS/CSS/imagem/fonte).

## 2. Imagens

Depois da rolagem (com as imagens lazy já carregadas):

| Achado | Nível | Por quê |
|---|---|---|
| Imagem acima de 400 KB | **P1** | Foto de câmera (no teste, 9,8 MB) faz o LCP passar de 9 s no 4G |
| Imagem de 200–400 KB | P2 | — |
| Largura natural acima de 2,5× a exibida | P2 | "4000 px exibida a 390 px": falta `srcset`/tamanho menor |
| Sem `width`/`height` nem proporção (`aspect-ratio`, moldura `.media-frame`) | P2 | A página pula quando a imagem chega |
| Fora da tela sem `loading="lazy"` (exceto hero) | P2 | Baixa o que ninguém viu ainda |

**Prevenção** no esqueleto e no fluxo:
- toda imagem de conteúdo entra pela **Mídia**, nunca como URL colada. Assim o WordPress gera os tamanhos e o `srcset`, e reduz automaticamente originais acima de 2560 px;
- `project_media()` / a moldura reservam a proporção;
- o hero usa `eager` + `fetchpriority="high"` (`references/hero-banners.md`) e o resto fica `lazy`;
- `$content_width` (`functions.php`, filtro `project_content_width`, padrão 760) diz ao WordPress a largura da coluna de texto: imagens do editor saem no tamanho certo. Ajuste para a largura medida na referência.

## 3. O que não está aqui de propósito

- `text-wrap: balance`/`pretty` nos títulos: muda onde a linha quebra, e as quebras vêm da referência (espelho).
- `scrollbar-gutter: stable`: reserva a faixa da barra de rolagem até em página curta e soma com elementos de `100vw`, causando rolagem horizontal.
- Pré-renderização com Speculation Rules: o WordPress (6.8+) já faz o prefetch conservador sozinho.
