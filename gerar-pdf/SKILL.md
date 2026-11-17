---
name: gerar-pdf
description: Gera um PDF estruturado e bem formatado (título ou capa, sumário, seções, listas, tabelas, citações, código, rodapé com numeração de páginas) a partir de qualquer conteúdo, e envia o arquivo ao usuário pelo Telegram. Use sempre que o usuário pedir algo "em PDF", "como PDF", "exporta/salva/gera/manda um PDF", "quero o arquivo", "versão para imprimir", ou pedir para transformar em PDF um resumo de vídeo, resumo de documento, relatório, PRD, ata, roteiro, plano de estudo, lista, resposta anterior da conversa ou qualquer outro texto.
---

# Gerar PDF

Transforma qualquer conteúdo em um PDF estruturado e o envia ao usuário como anexo no Telegram.

## Regra de ouro

Você CONSEGUE gerar PDF: o script `scripts/gerar_pdf.py` faz a conversão. Nunca diga que não consegue gerar PDF nem ofereça Markdown "para converter depois".

## Fluxo de trabalho

1. **Defina o conteúdo.**
   - Se o usuário pedir o PDF de algo que já está na conversa (ex.: "disponibilize o resumo desse vídeo em PDF"), use esse conteúdo do histórico, completo e fiel, sem resumir de novo nem cortar seções.
   - Se o conteúdo ainda não existe, produza-o primeiro (seguindo a skill correspondente, se houver, como resumo-youtube ou resumo-pdf).
   - Se não ficar claro qual conteúdo deve ir para o PDF, pergunte em uma linha.
2. **Escreva o Markdown** com `criar_arquivo` em `documentos/<nome-curto>.md` (nome em minúsculas, sem acentos, com hífens). Siga "Como estruturar o Markdown".
3. **Converta** com `executar_script_skill`:
   - skill: `gerar-pdf`
   - script: `scripts/gerar_pdf.py`
   - argumentos: `["documentos/<nome-curto>.md", ...opções]`
   Pode chamar `criar_arquivo` e `executar_script_skill` na mesma resposta, nessa ordem.
4. **Confira o resultado.** `codigo_saida` 0 significa sucesso. O PDF aparece em `arquivos_gerados`, terminando em `.pdf`.
5. **Envie o arquivo**: na resposta final, escreva uma linha curta (ex.: "Pronto, segue o PDF do resumo.") e, em linha separada, o marcador com o caminho exato que veio em `arquivos_gerados`:

   ```
   <<<ENVIAR_ARQUIVO:execucoes/gerar-pdf/.../nome-do-arquivo.pdf>>>
   ```

   Não cole o conteúdo do PDF no chat.

## Opções do script

| Opção | Quando usar |
|---|---|
| `--titulo "..."` | Título do documento. Se omitido, usa o primeiro `# Título` do Markdown. |
| `--subtitulo "..."` | Linha abaixo do título (ex.: "Resumo executivo · Secretaria de Saúde de Goiás"). |
| `--autor "..."` | Autor ou fonte (ex.: nome do canal do vídeo). |
| `--capa` | Página de capa separada. Use em documentos com 3 páginas ou mais, ou se o usuário pedir. |
| `--sumario` | Sumário com links para as seções. Use quando houver 4 seções `##` ou mais. |
| `--saida "nome.pdf"` | Nome do arquivo. Se omitido, é derivado do título. |

## Como estruturar o Markdown

- Comece com `# Título do documento` (vira o título do PDF; não repita no corpo).
- Use `##` para as seções principais e `###` para subseções. Elas formam o sumário e os marcadores de navegação do PDF.
- Use listas `-` e `1.`, **negrito** para destaques, tabelas Markdown para dados comparáveis (números, indicadores, prós e contras), `>` para citações literais e blocos de código com três crases.
- Links devem ser completos (`https://...`) para ficarem clicáveis.
- Não use emojis: eles são removidos no PDF.
- Não use HTML.

## Conteúdo de resumos de vídeo

Ao gerar o PDF de um resumo da skill resumo-youtube:
- Título: o título do vídeo. Subtítulo: o estilo do resumo. Autor: o canal.
- Coloque os metadados (canal, publicação, duração, link, origem da transcrição) em uma tabela de duas colunas logo no início.
- Mantenha todas as seções, recursos e timestamps do resumo.
- Flashcards e questionários ficam melhores em tabela (Frente | Verso) ou lista numerada com o gabarito em seção própria no final.

## Erros

| Código | Significado | O que fazer |
|---|---|---|
| 2 | Dependências ausentes e instalação falhou | Informe o erro ao usuário (reportlab e markdown-it-py). |
| 3 | Erro ao montar o PDF | Informe o trecho do `stderr`. Se for problema no Markdown, simplifique a parte com problema (ex.: tabela malformada) e tente uma única vez. |
| 5 | Arquivo de entrada não encontrado | Confira o caminho usado em `criar_arquivo` e tente uma única vez. |

## Arquivos da skill

- `scripts/gerar_pdf.py`: conversor Markdown → PDF (reportlab + markdown-it-py).
- `README.md`: requisitos e uso manual.
