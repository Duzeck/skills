# Casos de teste — resumo-pdf

Cada caso descreve entrada, comportamento esperado do script e do resumo.

## T1 — PDF curto com texto nativo

**Entrada:** PDF de 3 páginas gerado digitalmente (texto selecionável), ex.: um comunicado interno.

**Comando:**
```bash
python extrair_pdf.py comunicado.pdf -o comunicado.txt
```

**Esperado:**
- Código de saída 0
- Cabeçalho com `Metodo: texto nativo`
- Texto das 3 páginas com marcadores `===== PAGINA n =====`
- Resumo estruturado completo, sem seção de OCR

**Falha se:** o script acionar OCR desnecessariamente ou perder páginas.

---

## T2 — PDF escaneado (imagem), sem camada de texto

**Entrada:** PDF de 2 páginas digitalizado por scanner, sem texto embutido.

**Comando:**
```bash
python extrair_pdf.py escaneado.pdf -o escaneado.txt
```

**Esperado:**
- Código 0
- Cabeçalho com `Metodo: OCR`
- Marcadores `===== PAGINA n (OCR) =====`
- Texto legível, com eventuais erros de OCR sinalizados em "Observações sobre a extração"

**Falha se:** retornar texto vazio com código 0, ou inventar conteúdo.

---

## T3 — PDF protegido por senha

**Entrada:** PDF criptografado com senha `teste123`.

**Comando sem senha:**
```bash
python extrair_pdf.py protegido.pdf
```
**Esperado:** código 2, mensagem "PDF protegido por senha: informe --senha". A skill deve pedir a senha ao usuário e aguardar.

**Comando com senha correta:**
```bash
python extrair_pdf.py protegido.pdf --senha teste123
```
**Esperado:** código 0 e texto extraído.

**Comando com senha errada:**
```bash
python extrair_pdf.py protegido.pdf --senha errada
```
**Esperado:** código 2, mensagem "senha incorreta".

---

## T4 — PDF longo (80+ páginas)

**Entrada:** relatório de 80 páginas com texto nativo.

**Comando:**
```bash
python extrair_pdf.py relatorio.pdf -o relatorio.txt
```

**Esperado:**
- Código 0
- Skill confirma com o usuário se quer resumo completo ou por seções
- Resumo por blocos com faixas de páginas + consolidado no formato padrão

**Falha se:** o resumo ignorar seções finais (conclusões/anexos).

---

## T5 — PDF corrompido ou arquivo inexistente

**Comando:**
```bash
python extrair_pdf.py nao_existe.pdf
```
**Esperado:** código 5, mensagem clara. A skill informa o problema e pergunta se o usuário quer reenviar o arquivo.

---

## T6 — PDF só de imagens sem texto reconhecível

**Entrada:** PDF com fotos, gráficos ou páginas em branco.

**Esperado:**
- Código 3, mensagem "nenhum texto extraivel, mesmo apos OCR"
- Skill avisa que não consegue resumir e pede versão melhor ou texto colado
- **Nunca** gera resumo especulativo

---

## T7 — Documento em outro idioma

**Entrada:** PDF em inglês.

**Esperado:**
- Texto extraído normalmente
- Resumo em português do Brasil
- Seção "Identificação" informa que o documento original está em inglês

---

## T8 — Extração parcial por faixa de páginas

**Comando:**
```bash
python extrair_pdf.py grande.pdf --paginas 1-10
```

**Esperado:**
- Código 0
- Cabeçalho indica `Paginas processadas: 10`
- Resumo limitado ao conteúdo dessas páginas, com aviso de que é parcial

---

## T9 — Ambiente sem execução de código

**Entrada:** usuário pede resumo de PDF em ambiente sem Python.

**Esperado:**
- Skill não tenta adivinhar o conteúdo
- Mensagem explicando a limitação e oferecendo alternativas (colar texto, rodar o script, usar OCR externo)

---

## T10 — PDF com tabelas e números

**Entrada:** PDF com tabela de valores.

**Esperado:**
- Números extraídos quando legíveis
- Se o OCR desalinhar a tabela, a skill sinaliza em "Observações sobre a extração" e não reconstrói valores duvidosos
