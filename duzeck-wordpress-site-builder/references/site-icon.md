# Ícone do site e sinais básicos do `<head>`

Pequenos itens que somem sem ninguém notar e que todo site precisa: o
ícone na aba do navegador e no atalho do celular, a cor da barra do
navegador, o link do feed e a política de IA dita em palavras.

## 1. Ícone do site

Usa o recurso **do WordPress**: Aparência › Personalizar › Identidade do
site › Ícone do site. O core imprime o favicon (32 px), o de 192 px e o
`apple-touch-icon` (180 px), e o administrador troca quando quiser.

**Na referência:** registre o **símbolo** do logo (sem o nome: em 16–32 px,
texto vira borrão) como `media[]` e aponte
`global_settings.branding.site_icon` para ele (`pending` se ainda não
houver).

**`scripts/make_site_icon.py`** prepara a imagem:
- quadrada, 512 px, símbolo centralizado com respiro;
- **fundo sólido**, porque o iPhone pinta de preto o fundo transparente;
- `--box x,y,l,a` recorta da referência (mesmas coordenadas de `reference_map.box`);
- **`--keep-color #FFFFFF`**: símbolo sobre foto (logo branco no header transparente). Mantém só a cor do símbolo e o fundo da foto sai. No teste, o recorte trazia o céu do hero junto, e com a opção o símbolo saiu limpo;
- `--project <wordpress>` importa na Mídia e já define como Ícone do site;
- avisa quando o símbolo é pequeno demais (borra). Nesse caso é provisório: peça o logo em alta (`replace_before_launch`).

O `favicon.ico` **físico** na raiz sai do `go_live.py` (`references/go-live.md`).

## 2. Sinais do `<head>` (`inc/site-icon.php`, `functions.php`)

| Sinal | De onde vem |
|---|---|
| `theme-color` | Cor `background` da paleta do `theme.json` (filtro `project_theme_color`) |
| Manifesto (`/?project_manifest=1`) | Nome, nome curto (palavras inteiras até 12 letras), cores e ícones 192/512 do Ícone do site. Gerado na hora, sem arquivo para manter, e só aparece quando há ícone |
| Link do feed RSS | `add_theme_support('automatic-feed-links')` |
| `Content-Signal` no robots.txt | `seo.ai_crawlers`: `search=yes`, `ai-input` e `ai-train` conforme a política (`references/security-seo.md`) |

## 3. Como validar

A seção SEO da captura, na Home:
- **P1**: sem Ícone do site; manifesto que não abre, não é JSON ou não tem nome/ícones;
- **P2**: sem `apple-touch-icon`, sem manifesto, sem `theme-color`, sem link do feed.

A seção robots.txt aponta `Content-Signal` ausente (P2) ou contrário ao
Blueprint (P1). O `prelaunch_check.py` cobra o Ícone do site (P1).
