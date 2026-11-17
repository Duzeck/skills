---
name: resumo-pdf
description: Extrai texto de arquivos PDF (inclusive escaneados, via OCR) e devolve um resumo estruturado em português do Brasil. Use quando o usuário pedir para resumir, sintetizar, analisar ou extrair informações de um PDF, documento digitalizado, contrato, relatório, artigo ou material escaneado. Também cobre PDFs protegidos por senha, documentos longos e PDFs sem texto extraível.
---

# Resumo de PDF

## Objetivo

Receber um PDF, extrair seu texto de forma confiável (texto nativo ou OCR) e produzir um resumo estruturado em português do Brasil, sem inventar informação.

## Capacidades necessárias

Esta skill depende de execução de código Python e de OCR. Antes de começar, verifique se o ambiente dispõe de:

- execução de Python 3.9+
- permissão para instalar pacotes (`pip install`)
- binário do Tesseract OCR (o script tenta instalar automaticamente)

Se o ambiente **não** tiver execução de código, não tente adivinhar o conteúdo do PDF. Informe o usuário com clareza:

> "Não consigo executar o script de extração neste ambiente. Posso resumir se você colar o texto do documento ou rodar o script `extrair_pdf.py` e me enviar o `.txt` gerado."

## Fluxo de trabalho

1. **Receber o arquivo.** Confirme o caminho do PDF. Se o usuário não enviou o arquivo, peça.
2. **Verificar proteção por senha.** Se o PDF estiver criptografado, peça a senha ao usuário e aguarde a resposta. Avise: "Evite enviar senhas de documentos sensíveis por chat; se possível, remova a proteção localmente antes."
3. **Executar a extração.** Rode:

   ```
   python extrair_pdf.py "<caminho_do_pdf>" --saida "<caminho_do_txt>" [--senha "<senha>"]
   ```

4. **Interpretar o resultado do script.** O script retorna um dos códigos:
   - `0` — extração concluída (texto nativo ou OCR)
   - `2` — PDF protegido por senha (senha ausente ou incorreta)
   - `3` — nenhum texto extraível mesmo após OCR
   - `4` — dependências indisponíveis e instalação falhou
   - `5` — arquivo inválido, corrompido ou não encontrado

5. **Resumir.** Com o texto extraído, produza o resumo estruturado (formato abaixo).

## Formato do resumo (obrigatório)

Sempre em português do Brasil, nesta estrutura:

```
**Resumo executivo**
(3 a 5 linhas com a essência do documento)

**Identificação**
- Tipo de documento:
- Partes/autores envolvidos:
- Data/período mencionado:
- Extensão: (nº de páginas, e se houve OCR)

**Pontos-chave**
- (5 a 10 tópicos objetivos)

**Números e dados relevantes**
- (valores, prazos, percentuais, quantidades; se não houver, escrever "Não há dados numéricos relevantes.")

**Conclusões e decisões**
- (o que o documento conclui, decide ou recomenda)

**Pendências e riscos**
- (obrigações em aberto, prazos, pontos ambíguos; se não houver, escrever "Nenhuma pendência identificada.")

**Observações sobre a extração**
- (qualidade do OCR, páginas ilegíveis, trechos truncados)
```

## Documentos longos

- Acima de ~30 páginas: gere primeiro um resumo por blocos de seção e depois o consolidado no formato acima.
- Sempre cite a faixa de páginas de onde vem cada bloco de pontos-chave.
- Se o texto extraído for muito extenso para o contexto, priorize: início, sumário/índice, seções de conclusão e anexos com números.

## Regras rígidas

- **Nunca invente conteúdo.** Se algo não está no texto extraído, diga que não está.
- **Não deduza pelo nome do arquivo.** Nome de arquivo não é conteúdo.
- **Se o OCR falhar ou vier ilegível**, reporte explicitamente quais páginas falharam e não preencha lacunas com suposições.
- **Tabelas e gráficos** podem sair desalinhados no OCR: sinalize isso em "Observações sobre a extração" em vez de reconstruir números duvidosos.
- **Idioma de saída é sempre português do Brasil**, mesmo que o documento esteja em outro idioma. Se o documento estiver em outro idioma, informe isso na identificação.

## Casos de borda — sempre perguntar ao usuário

Pergunte antes de prosseguir quando:

- o PDF estiver protegido por senha (peça a senha e aguarde);
- o arquivo parecer corrompido ou incompleto (ofereça tentar mesmo assim);
- o OCR retornar texto com qualidade muito baixa (pergunte se quer tentar outra abordagem ou enviar versão melhor);
- o documento tiver mais de 100 páginas (confirme se quer resumo completo ou foco em seções específicas);
- houver múltiplos PDFs (confirme se quer um resumo por documento ou um consolidado);
- o PDF contiver páginas em branco, imagens sem texto ou anexos escaneados separados.

## Exemplos de acionamento

- "Resume esse PDF pra mim"
- "O que diz esse contrato escaneado?"
- "Extrai os pontos principais desse relatório de 80 páginas"
- "Esse PDF tá pedindo senha, a senha é 1234"
- "Faz um resumo estruturado desse artigo"
