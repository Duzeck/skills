# resumo-pdf

Skill para extrair texto de PDFs (nativos ou escaneados, via OCR) e gerar resumo estruturado em português do Brasil.

## Arquivos

- `SKILL.md` — instruções da skill (fluxo, formato do resumo, regras, casos de borda)
- `extrair_pdf.py` — script Python autocontido e autossuficiente de extração
- `testes.md` — casos de teste para validação

## Requisitos

- Python 3.9+
- Permissão de instalação de pacotes (`pip`)
- Para OCR: Tesseract (o script tenta instalar automaticamente)

O script instala sozinho, quando ausentes:

- `pypdf` (extração nativa)
- `pytesseract`, `pdf2image`, `pillow` (OCR)
- binário `tesseract-ocr` + `poppler-utils` (via apt/dnf/apk/brew/winget/choco)

## Uso

```bash
# PDF com texto nativo
python extrair_pdf.py documento.pdf

# PDF escaneado (OCR automático quando o texto nativo for insuficiente)
python extrair_pdf.py digitalizado.pdf -o saida.txt

# PDF protegido por senha
python extrair_pdf.py protegido.pdf --senha "minhasenha"

# Forçar OCR desde o início
python extrair_pdf.py documento.pdf --forcar-ocr

# Só algumas páginas (útil em documentos longos)
python extrair_pdf.py relatorio.pdf --paginas 1-20,45,60-

# Ambiente restrito, sem instalar nada
python extrair_pdf.py documento.pdf --sem-instalar
```

## Códigos de saída

| Código | Significado |
|--------|-------------|
| 0 | Sucesso |
| 2 | PDF protegido por senha (ausente ou incorreta) |
| 3 | Nenhum texto extraível, mesmo após OCR |
| 4 | Dependências indisponíveis e instalação falhou |
| 5 | Arquivo inválido, corrompido ou não encontrado |

## Como o script decide entre texto nativo e OCR

1. Extrai texto nativo com `pypdf`.
2. Calcula a densidade média de caracteres por página.
3. Se ficar abaixo de `--min-chars` (padrão 40), considera PDF escaneado e aplica OCR.
4. Se o Tesseract não estiver disponível, tenta `ocrmypdf` como alternativa.
5. Se nada funcionar, retorna código 3 ou 4 — nunca inventa conteúdo.

## Limitações conhecidas

- Tabelas e gráficos podem sair desalinhados no OCR.
- PDFs com layout em colunas podem ter a ordem de leitura embaralhada.
- Manuscrito tem baixa taxa de acerto no Tesseract.
- O script precisa de execução de código; em ambientes sem Python ele não roda.
