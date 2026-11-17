# Blog e notícias

O blog é declarado no objeto `blog` do Blueprint (`blog: { enabled:
false }` quando a referência não tem). Usa sempre o **post nativo do
WordPress** — categorias, tags, feed RSS, arquivos por data, busca e
compatibilidade com plugins de SEO vêm de graça; um CPT "blog" perderia
tudo isso.

## 1. Como identificar

| Sinal (`evidence`) | O que é |
|---|---|
| `post_cards` | Cards com imagem, título e resumo de artigos |
| `dates` | Data em cada card ("12 de maio de 2026", "há 3 dias") |
| `categories` | Etiqueta de categoria no card ("Dicas", "Obras") |
| `read_more` | "Leia mais", "Continuar lendo" |
| `sidebar` | Barra lateral com busca, categorias, posts recentes |
| `pagination` | "1 2 3 Próxima", "Carregar mais" |
| `section_title` | "Blog", "Notícias", "Artigos", "Últimas do blog" |
| `user` | O usuário disse |

Não é blog: grid de **projetos/serviços** (CPT — sem data nem autor),
**cases** com página própria (CPT `project`), **eventos** (data futura,
local — CPT próprio), **FAQ**. "Últimas notícias" na Home é um **trecho**
do blog (`blog.home_section`), não um blog separado.

## 2. O que registrar e decidir

| Campo | Da imagem | Pergunte / decida |
|---|---|---|
| `label` | "Blog", "Notícias" (literal) | — |
| `posts_page` | — | Slug da página de posts (Configurações > Leitura); a página entra em `pages[]` |
| `posts_per_page` | Cards visíveis na listagem | Múltiplo das colunas (3 colunas → 6, 9, 12) |
| `card_fields` | `image`, `date`, `category`, `author`, `reading_time`, `excerpt` | — |
| `home_section` | Seção e quantos posts aparecem na Home | Categoria específica? |
| `sidebar` | Barra lateral visível? | — |
| `comments` | — | **Decisão do usuário**: exige moderação, anti-spam (Akismet) e aviso de privacidade. Padrão: desligado (`PROJECT_COMMENTS` em `inc/blog.php`) |
| `content_source` | — | Posts da referência são títulos inventados: `demo` até o cliente publicar os reais |

## 3. Posts demo nunca aparecem em produção

Posts semeados a partir da referência levam a meta `_project_demo = 1`.
Com `WP_ENVIRONMENT_TYPE=production`, `inc/blog.php` os remove de **todas
as saídas** (testado uma a uma):

| Saída | Como |
|---|---|
| Home, índice do blog, categoria, busca, relacionados, feed | `pre_get_posts` (toda `WP_Query`) |
| API REST | `rest_post_query` |
| Sitemap nativo | `wp_sitemaps_posts_query_args` |
| "Anterior / Próximo" do post | `get_{next,previous}_post_join/where` — **usa SQL próprio, sem `WP_Query`**; sem esse filtro o post real mais recente linkava para o demo (encontrado no teste) |
| Link direto | 404 em `template_redirect` |

Em local/homologação os demo aparecem normalmente para validar o layout.

## 4. Implementação (esqueleto)

`inc/blog.php`, `home.php` (índice do blog — com Home estática o
WordPress usa este arquivo), `archive.php` (categoria/tag/autor/data),
`search.php`, `single-post.php`, `template-parts/post-card.php`,
`posts-latest.php`, `blog-list.php`, `blog-sidebar.php`.

| Prática | Por quê |
|---|---|
| Post nativo + categorias/tags nativas | Feed, arquivos, busca e SEO sem reinventar |
| Card com **um link só** (o título), esticado sobre o card (`::after`); categoria clicável por cima | Imagem + título + "Leia mais" seriam 3 links iguais para leitor de tela e Tab |
| Imagem do card `alt=""`, proporção fixa | O título já nomeia o link; sem salto de layout |
| Data em `<time datetime="ISO">` no formato do site | Legível para pessoas e máquinas |
| Formato de data brasileiro (`j \d\e F \d\e Y`) gravado pelo scaffold | O core instala em inglês: sem isso saía "novembro 1, 2026" (encontrado no teste) |
| Tempo de leitura calculado do texto (200 palavras/min) | Nunca digitado à mão |
| Título da listagem = título da página de posts (editável) | Nada fixo no template |
| Post: imagem de destaque `eager` + `fetchpriority="high"` | É o LCP |
| Publicado em / Atualizado em (só se mudou), autor (se houver), leitura | Transparência; sem separador órfão sem autor |
| JSON-LD **`BlogPosting`** (headline, datas ISO, autor, publisher, imagem) | Válido e útil (ao contrário de avaliação autopromocional). Sem autor, a empresa assina como `Organization` — nunca `"name": ""` (encontrado no teste) |
| Compartilhar por **links** (WhatsApp, LinkedIn, Facebook, X, e-mail) com "Compartilhar no X (abre em nova aba)" | Sem SDK/AddThis/ShareThis: sem rastreio de terceiros nem peso |
| "Leia também": 3 da mesma categoria, sem o atual | Navegação interna |
| Anterior/Próximo com `aria-label` | Navegação entre posts identificada |
| Paginação `<nav aria-label>`, página atual com `aria-current`, "Página 2" para leitor de tela, alvos ≥ 44px | Padrão acessível |
| Estados vazios ("Nenhum post nesta categoria ainda", busca sem resultado + formulário de busca) | Sem página em branco |
| Comentários desligados por padrão | Só com decisão do usuário |
| Scaffold apaga "Olá, mundo!", "Página de exemplo" e o comentário padrão | Senão aparecem no blog e no sitemap (encontrado no teste) |

`check_theme.py` avisa script de compartilhamento de terceiros.

## 5. Como validar

Inclua no Blueprint as páginas do blog com `capture_path`: a página de
posts, um post (`slug: "<post>"`, `capture_path: "<slug-real>"`) e uma
categoria. `scripts/capture_site.py --blueprint` aponta em qualquer página:
card sem título, com mais de um link, sem `<time>` ISO, sem
categoria/imagem pedidas; seção de últimos posts com quantidade
diferente; listagem acima de `posts_per_page`; paginação sem `aria-label`
ou sem página atual; post sem `<h1>`, sem data ISO, imagem sem
`fetchpriority`, compartilhar sem nome acessível, sem JSON-LD ou com
headline/autor/data inválidos; script de compartilhamento de terceiros
(P1).

Antes de publicar: acessar com `WP_ENVIRONMENT_TYPE=production` e
conferir que nenhum post demo aparece (listagens, busca, feed, API REST,
sitemap, anterior/próximo; link direto = 404).
