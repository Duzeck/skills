# gerar-pdf

Skill que converte conteúdo em Markdown em um PDF estruturado e o envia pelo Telegram.

Feita para o [DuzeckClaw](https://github.com/Duzeck/duzecklaw), agente pessoal controlado pelo Telegram: lá o PDF chega como anexo no chat. Para instalar, veja [Usando com o DuzeckClaw](../README.pt-BR.md#usando-com-o-duzeckclaw-telegram). Fora dele, o script roda sozinho pela linha de comando (veja "Uso manual").

## Requisitos

- Python 3.9+
- `reportlab` e `markdown-it-py` (o script tenta instalar sozinho se faltarem)
- Fontes: usa Segoe UI/Arial e Consolas no Windows, DejaVu no Linux; sem elas, cai para Helvetica/Courier

## Uso manual

```bash
python scripts/gerar_pdf.py documento.md
python scripts/gerar_pdf.py documento.md --capa --sumario --subtitulo "Resumo" --autor "Fonte" --saida relatorio.pdf
```

Caminhos relativos da entrada são procurados no diretório atual e depois em `WORKSPACE_DIR`
(o bot define essa variável ao rodar o script). O PDF é gravado no diretório atual e o nome
do arquivo é impresso no stdout.

## O que o PDF inclui

- Bloco de título com data (ou página de capa com `--capa`)
- Sumário com links (`--sumario`) e marcadores de navegação do PDF a partir de `##` e `###`
- Parágrafos com negrito, itálico, tachado, código e links clicáveis
- Listas com marcadores e numeradas, inclusive aninhadas
- Tabelas com cabeçalho destacado e linhas alternadas (o cabeçalho se repete em quebras de página)
- Citações, blocos de código e linhas horizontais
- Rodapé com o título e "Página X de Y"

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | PDF gerado |
| 2 | Dependências ausentes e instalação falhou |
| 3 | Erro ao montar o PDF |
| 5 | Arquivo de entrada não encontrado / argumento inválido |

## Limitações

- Emojis são removidos (as fontes do PDF não os desenham).
- Imagens do Markdown viram o texto "[imagem: ...]".
- HTML dentro do Markdown vira texto simples.
