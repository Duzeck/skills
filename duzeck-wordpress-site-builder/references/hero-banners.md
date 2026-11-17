# Hero, cabeçalhos de página e banners

O hero da Home e os cabeçalhos das páginas internas entram em `heroes[]`;
faixas de chamada e barra de aviso em `banners[]`.

## 1. Como identificar o tipo

| `kind` | Na imagem |
|---|---|
| `background` | Foto ocupando a seção, texto por cima (`full_bleed_image`, `text_over_image`) |
| `split` | Texto de um lado, imagem do outro (`split_layout`) |
| `centered` | Só texto e botões, sem foto |
| `form` | Texto + formulário ao lado ("Peça seu orçamento") — exige `forms[]` na mesma seção |
| `page_header` | Páginas internas: faixa menor com título da página (`page_title_band`), às vezes trilha "Início › Serviços" (`breadcrumb`) |
| `carousel` | Banner rotativo → `carousels[]` (`kind: hero_banner`) |
| `video` | Vídeo de fundo → `videos[]` (`kind: background`) |

Banners (`banners[]`):

- `cta_band` — faixa de chamada ("Vamos construir o seu projeto? [Botões]"),
  normalmente **reutilizável** (conteúdo na página de opções);
- `announcement` — barra fina no topo ("Agenda 2027 aberta ✕"), `dismissible`
  se tiver o "x".

## 2. O que registrar e decidir

| Campo | Da imagem | Decida |
|---|---|---|
| `height` | `full` / `large` / `auto` | — (vira `svh`, nunca `100vh`) |
| `buttons` | Rótulos **literais**, estilo primário/secundário | Destino real; especiais `whatsapp`, `telefone`, `email` montam `wa.me`/`tel:`/`mailto:` do dado único |
| `overlay` | Escurecimento sobre a foto | 0..1 — o QA mede o contraste resultante |
| `mobile_image` | — | `focal` (ponto focal editável), `separate` (imagem própria do celular) ou `same` |
| `image_role` | — | `decorative` (`alt=""`, o texto já diz tudo) ou `informative` (alt descreve) |
| `breadcrumb` | Trilha visível? | Só se a referência mostra |
| um `h1` por página | — | O título do hero/cabeçalho é o `h1` |

## 3. Implementação (esqueleto)

`template-parts/hero.php`, `page-header.php`, `cta.php` (faixa),
`announcement.php`, `inc/hero.php` (botões, trilha), CSS "Hero".

| Prática | Por quê |
|---|---|
| Foto como **`<img>`** (não `background-image`) com `srcset`, `sizes`, `loading="eager"`, `fetchpriority="high"` | Descoberta cedo, tamanho certo, vira o LCP (medido no teste: LCP = imagem do hero no desktop e no celular) |
| Imagem do celular em `<picture>` ou ponto focal via `object-position` | A foto horizontal não vira uma faixa cortada no celular |
| Foto e texto na **mesma célula do grid** (sem `position: absolute` + altura fixa) | O texto define a altura mínima; nada vaza |
| Camada de contraste `--overlay` (0..1) | Texto legível sobre qualquer foto |
| Botões com **padrão legível** dos tokens (principal: fundo primário; secundário: contorno na cor do contexto) | Sem isso ficavam no azul padrão sobre a foto (1,5:1 medido no teste) |
| Botão sem rótulo ou sem destino real **não aparece** | Nunca `href="#"` nem vazio (WhatsApp sem número não gera botão) |
| Altura em `svh` (reserva `vh` só sob `@supports not`) | `100vh` fica atrás da barra do navegador no celular |
| Trilha `<nav aria-label="Trilha de navegação">` com `aria-current="page"` + JSON-LD **BreadcrumbList** com os mesmos itens; separador "›" com texto alternativo vazio | Navegação e SEO consistentes; o leitor de tela não lê "›" |
| Faixa de chamada do admin, sem conteúdo fixo | O `cta.php` antigo tinha "Fale conosco" e `#contato` fixos — reescrito |
| Barra de aviso: script inline esconde **antes da pintura** se já foi fechada; fecha pelo teclado; foco vai para o logo; chave atrelada ao **texto** (aviso novo volta a aparecer) | Sem piscar nem salto; foco não se perde |

`check_theme.py` avisa `100vh` e imagem como `background-image` inline.

## 4. Como validar — contraste MEDIDO

`scripts/capture_site.py --blueprint` mede o contraste do texto sobre a
foto de verdade: esconde o texto (título, rótulo, texto, **botões**),
fotografa o retângulo atrás dele e compara a cor do texto com o pior
trecho do fundo (percentil 90 para texto claro, 10 para escuro). Mínimo
4,5:1; 3:1 para texto grande. No teste: camada 0 → 1,2:1 (reprova);
camada 0,55 → 5,1–5,7:1 (passa).

Aponta também: mais de um ou nenhum `h1`; imagem do hero com `lazy`,
sem `fetchpriority` ou que não é o LCP; botões diferentes da referência
ou sem destino; trilha ausente, sem `aria-current` ou sem JSON-LD; aviso
fechável sem botão, sem nome ou que volta depois de fechado (P1).
