# Schema do Blueprint

Este é o schema canônico. Ele consolida e substitui qualquer versão anterior
discutida durante a criação desta Skill — trate-o como a única fonte de
verdade estrutural.

"Determinístico", neste contexto, não significa que duas análises visuais
produzirão sempre o mesmo Blueprint byte a byte (isso é impossível para uma
análise feita por um modelo de linguagem). Significa que o **schema** é
fixo e sem ambiguidade de interpretação: um agente de implementação lendo
qualquer Blueprint válido deve saber exatamente o que construir, sem
precisar reinterpretar a referência visual original.

## Estrutura de alto nível

```yaml
blueprint:
  metadata: {}
  project: {}
  requirements: {}
  design: {}
  reference_map: []
  copy: []
  editable_content: []
  pages: []
  components: []
  content_types: []
  taxonomies: []
  global_settings: {}
  menus: []
  carousels: []
  forms: []
  maps: []
  galleries: []
  videos: []
  accordions: []
  tabs: []
  tables: []
  pricing: []
  testimonials: []
  client_logos: []
  team: []
  stats: []
  blog: {}
  header: {}
  heroes: []
  banners: []
  footer: {}
  social: {}
  media: []
  fonts: {}
  seo: {}
  security: {}
  launch: {}
  redirects: {}
  plugins: {}
  theme: {}
  responsive: {}
  accessibility: {}
  integrations: []
  decisions: []
  uncertainties: []
  dependencies: []
  implementation: {}
  validation: {}
  generation: {}
```

## metadata

```yaml
metadata:
  schema_version: "1.18"   # 1.1: design.tokens, copy, media.treatment; 1.2: editable_content;
                          # 1.3: site_structure, sections[].anchor, menu anchor, header_behavior;
                          # 1.4: carousels; 1.5: forms estruturado, maps;
                          # 1.6: galleries, videos; 1.7: accordions, tabs;
                          # 1.8: tables, pricing; 1.9: testimonials, client_logos;
                          # 1.10: team, stats; 1.11: blog; 1.12: footer, social;
                          # 1.13: header; 1.14: heroes, banners; 1.15: seo, security;
                          # 1.16: fonts; 1.17: seo.ai_crawlers;
                          # 1.18: launch, branding.site_icon, redirects
  blueprint_version: "0.1"
  generated_at: <iso8601>
  updated_at: <iso8601>
  generator:
    skill: "duzeck-wordpress-site-builder"
  mode: assisted | recommended | automatic
  status: draft | analysis | awaiting_review | approved | generating |
          generated | testing | completed | blocked | revision_required
```

## project

```yaml
project:
  name:
  slug:
  type: institutional | landing_page | portfolio | blog | news | catalog |
        ecommerce | directory | membership | booking | service_business |
        corporate | custom
  site_structure: single_page | multi_page   # obrigatório (1.3) - decidido no passo 1
  description:
  language:
    primary:
    secondary: []
  objective:
    primary:
    secondary: []
  audience:
    description:
  reference_files: []
```

`site_structure` (ver `references/navigation.md`):

- `single_page` — uma página com seções ancoradas; o menu leva a seções
  da mesma página. Exige `theme.header_behavior: sticky`, `anchor` nas
  seções de destino e itens de menu `type: anchor`. Páginas auxiliares
  (política de privacidade, 404) entram em `pages[]` com `role: auxiliary`.
- `multi_page` — várias páginas; o menu leva a páginas/arquivos.

`project.type: landing_page` não é o mesmo que `single_page`: o tipo diz
o negócio, a estrutura diz a navegação. Na dúvida entre as duas
estruturas, registre `uncertainty` bloqueante.

## requirements

```yaml
requirements:
  functional: []
  technical: []
  business: []
  content: []
```

Cada item: `id`, `description`, `priority`, `source`, `status`.

Fontes válidas em todo o Blueprint (campo `source`):
`user`, `layout`, `reference_file`, `requirement`, `inference`,
`best_practice`, `system`.

## design

Duas camadas:

1. **Atributos descritivos** — cores, tipografia, espaçamento, estilo,
   bordas, sombras, imagens, layout em linguagem natural, cada um com
   `confidence` (`high`/`medium`/`low`) e `evidence` (`visual`,
   `provided_asset`, `user_statement`, `reference`, `inference`,
   `best_practice`). Servem para explicar e aprovar.
2. **`tokens`** — os mesmos valores em **CSS válido**, medidos na
   referência. É a fonte única de verdade visual: o
   `scripts/generate_design_tokens.py` gera `assets/css/tokens.css`
   (variáveis em `:root`) a partir daqui, e o `style.css` do tema só usa
   `var(--...)`.

```yaml
design:
  colors: { primary: { value: "Dourado dos CTAs", confidence: high, evidence: visual } }
  icon_library: "Phosphor (regular)"   # obrigatório se algum media usar icon_library
  tokens:
    color:       { primary: "#C9872E", secondary: "#14171C", background: "#FFFFFF", text: "#1F2328" }
    font_family: { heading: "'Montserrat', sans-serif", body: "'Inter', sans-serif" }
    font_size:   { h1: "clamp(2.25rem, 4vw, 3.5rem)", h2: "2rem", body: "1rem" }
    font_weight: { heading: 700, body: 400 }
    line_height: { heading: 1.15, body: 1.6 }
    space:       { xs: "8px", sm: "16px", md: "24px", lg: "48px", xl: "96px" }
    radius:      { sm: "4px", md: "8px" }
    shadow:      { card: "0 8px 24px rgba(0,0,0,.08)" }
    layout:      { container_max: "1200px", gutter: "24px" }
```

- Cada token aceita valor simples ou `{ value, confidence, evidence }`.
  Tokens com `confidence: low` saem comentados no CSS para conferência na
  validação visual.
- Obrigatórios: `color.primary`, `color.background`, `color.text`,
  `font_family.heading`, `font_family.body`, `layout.container_max` e ao
  menos 3 passos de `space`.
- Prosa no lugar de valor (ex.: `"#C9872E (dourado)"`) é bloqueio — a
  descrição vai na camada descritiva.
- Breakpoints não ficam em `tokens`: vêm de `responsive.breakpoints`.
- `global_settings.branding` (cores editáveis pelo admin, se existirem)
  deve coincidir com `tokens.color` — o validador avisa se divergirem.
- Ajuste de token durante o ciclo de correção é mudança visual: não exige
  nova versão do Blueprint, só regerar o CSS e registrar em
  `DECISIONS.md`.

## reference_map

Mapa de **toda** região visível de cada imagem de referência, de cima
para baixo (em colagens, coluna por coluna), com a caixa em pixels da
própria imagem e a página/seção correspondente. É o que garante que
nenhuma seção da referência foi esquecida — inclusive a continuação de
uma página em outra coluna da colagem.

```yaml
reference_map:
  - file: reference.png
    page: home
    section: home_projects          # id de pages[].sections, ou header/footer
    box: [605, 2, 512, 445]         # x, y, largura, altura
    note: "Coluna central = continuação da Home"
```

Regras (checadas pelo `validate_blueprint.py`):

- Toda entrada aponta para página e seção existentes (`header` e
  `footer` são aceitos como seções globais).
- Toda seção de toda página aparece em pelo menos uma entrada — seção
  sem região na referência é inferência e precisa de `source: inference`.
- As caixas alimentam `scripts/crop_reference.py` para gerar a
  referência de cada página (usada no `--ref` da captura) e os recortes
  provisórios de imagem.

## editable_content

Onde o administrador edita **cada parte visível** do site. Toda seção de
toda página, mais `header` e `footer`, precisa de uma entrada — o
`validate_blueprint.py` bloqueia (schema 1.2) se faltar alguma.

```yaml
editable_content:
  - target: home_hero                       # id de pages[].sections, header ou footer
    where: "Páginas > Início > Hero"        # caminho no admin, como o usuário vê
    storage: page_fields                    # options_page | page_fields | post_type | taxonomy | menu | form | editor
    fields: [home_hero_title, home_hero_text, home_hero_image]   # obrigatório para options_page/page_fields
```

Os `fields` são as chaves de `inc/content-defaults.php` e dos campos ACF;
o README do projeto deriva daqui a tabela "Onde editar cada coisa".
Padrões de `storage` por tipo de parte em `references/content-modeling.md`
→ "Todo conteúdo visível é editável".

## copy

Inventário dos **textos visíveis na referência** — menu, títulos,
subtítulos, CTAs, rótulos, footer. Serve a dois propósitos: reproduzir os
textos literalmente e separar texto real de conteúdo demo.

```yaml
copy:
  - id: home_hero_title
    page: home            # id de pages, ou "global" (header/footer)
    section: home_hero    # id de pages[].sections
    role: nav | heading | subheading | body | cta | label | footer | form | other
    text: "Construímos a casa que você sonha"
    source: reference_file | user | demo
    legibility: clear | partial | illegible   # padrão: clear
```

Regras:

- Texto com `legibility: clear` na referência é reproduzido **literalmente**
  — não reescreva, não "melhore", não traduza.
- `partial`: transcreva o que é legível e complete com demo, marcando
  `source: demo`.
- `illegible` nunca pode ter `source: reference_file`.
- Não invente o que não está na referência: rótulos acima do título
  ("eyebrow"), métricas ("+500 obras"), selos, categorias ou seções
  extras. Se o layout parece pedir, registre como `uncertainty`.
- Corpo de texto longo (parágrafos) pode ser resumido no inventário — o
  que importa literalmente são navegação, títulos, CTAs e rótulos.
- `scripts/seed_demo_content.py --blueprint` usa este inventário para
  classificar cada item semeado como texto da referência ou DEMO.

## pages

```yaml
pages:
  - id:
    slug:            # slug variavel permitido em singles: "servicos/<servico>"
    capture_path:    # opcional: exemplo concreto para a captura do QA ("servicos/cabelos")
    role: main | auxiliary   # padrão main; single_page tem exatamente UMA main
    name:
    template:
    status:
    sections:
      - id:
        component:
        type: global | static | dynamic | reusable | functional
        source:
        order:
        visibility:
        anchor:      # single_page: id da seção (slug sem acento: "servicos"); destino do menu
```

`anchor` é obrigatório em toda seção que um item de menu `type: anchor`
aponta, e único na página. Não use `conteudo` (reservado ao skip link).

## components

```yaml
components:
  - id:
    name:
    reusable: true | false
    fields: []
    source:
```

Componentes comuns: `header`, `navigation`, `hero`, `button`, `card`,
`card_grid`, `service_card`, `service_grid`, `project_card`,
`project_grid`, `testimonial_card`, `testimonial_grid`, `team_card`,
`gallery`, `faq`, `cta`, `contact_form`, `footer`.

Reutilize um componente quando estrutura, finalidade e comportamento forem
equivalentes. Não force reutilização só por semelhança visual superficial.

## content_types

```yaml
content_types:
  - id:
    name:
    plural_name:
    wordpress:
      type: custom_post_type
      slug:
      public:
      has_archive:
      rewrite:
    supports: []
    fields: []
```

Tipos de campo (via ACF PRO, disponível neste ambiente):
`text`, `textarea`, `rich_text`, `number`, `email`, `phone`, `url`,
`boolean`, `select`, `multiselect`, `image`, `gallery`, `video`, `file`,
`color`, `date`, `datetime`, `time`, `relationship`, `repeater`, `group`.

Cada campo: `id`, `label`, `type`, `required`, `default`, `validation`,
`description`, `source`. Repeater acrescenta `sub_fields`, `min` e `max`.

- `id` é o **nome estável** do campo no ACF, com prefixo de domínio do
  content type (`service_short_description`, não `short_description`).
  Nomes genéricos (`title`, `image`, `link`, `description`...) são
  bloqueio; nunca use a field key (`field_...`) como id.
- `description` vira a instrução do campo no admin — escreva para o
  editor ("Até 2 linhas; aparece no card da Home").
- Regras completas de modelagem ACF em `references/content-modeling.md`.

Relacionamentos devem ser explícitos e só criados quando há necessidade
real:

```yaml
- id: related_services
  type: relationship
  target: service
```

## taxonomies

```yaml
taxonomies:
  - id:
    name:
    slug:
    hierarchical:
    post_types: []
    terms: []
```

Criar apenas quando houver necessidade real de classificação, filtragem ou
organização — não crie taxonomia "porque poderia ser útil depois".

## global_settings

```yaml
global_settings:
  company:
    logo:
    name:
    phone:
    whatsapp:
    email:
    address:
    business_hours:
  social:
    instagram:
    facebook:
    youtube:
    linkedin:
  branding:
    primary_color:
    secondary_color:
  cta:
    default_label:
    default_url:
```

Implementar sempre como fonte única de verdade (ACF Options Page, neste
ambiente). Nenhum template deve hardcodar esses valores.

## menus

```yaml
menus:
  - id:
    name:
    location:
    items:
      - label:
        target:      # page: slug | archive: post type | anchor: "#servicos" | custom: URL
        type: page | archive | anchor | custom
        children: []
```

- `single_page`: os itens do menu principal são `type: anchor`, cada
  `target` igual a `#<anchor>` de uma seção da página `main`. No admin
  viram "Link personalizado" com URL **relativa** (`#servicos`).
- `type: custom` exige URL completa; `#` sozinho é proibido (item sem
  destino).

## carousels

Um por carrossel/banner rotativo identificado na referência; `[]` quando
o passe de identificação não achou nenhum (a seção é obrigatória no 1.4).
Como identificar e o que perguntar: `references/carousels.md`.

```yaml
carousels:
  - id: home_banner                 # vai em data-carousel no HTML (o QA procura por ele)
    section: home_hero              # id de pages[].sections (precisa estar em editable_content)
    kind: hero_banner | cards | testimonials | logos | gallery | other
    evidence: [dots, arrows]        # dots | arrows | counter | progress_bar | cut_item | user
    slide_count: 3                  # >= 2; com bolinhas, o número de bolinhas
    autoplay: true                  # true | false - nunca nulo (ou uncertainty bloqueante com subject = id)
    interval_ms: 6000               # obrigatório com autoplay; >= 3000, recomendado >= 5000
    loop: true
    controls: { arrows: true, dots: true, pause: true }   # pause: true obrigatório com autoplay
    per_view: { desktop: 1, tablet: 1, mobile: 1 }        # hero_banner: sempre 1
    storage: "repeater:home_banner_slides"                # ou "post_type:testimonial"
    slides_content: reference | user | demo               # demo: slides 2..N fictícios, marcados
```

## forms

Um por formulário da referência (como ler cada campo na imagem:
`references/forms.md`). Mecânica padrão: Contact Form 7, gerado por
`scripts/build_cf7_form.py`.

```yaml
forms:
  - id: contact                     # slug do formulário no CF7
    page: contact
    section: contact_form           # id de pages[].sections (editable_content com storage: form)
    purpose: contact | quote | newsletter | booking | job_application | other
    destination: "contato@empresa.com.br"   # nunca inventado: ou uncertainty bloqueante com subject = id
    reply_to_field: contato_email
    subject_field: contato_assunto  # opcional
    required_marker: "*"            # se a referência marca obrigatórios
    fields:
      - name: contato_nome          # minúsculo, prefixado, nunca termo reservado do WordPress
        type: text | email | tel | url | number | date | textarea | select | checkbox | radio | file
        label: "Nome"               # literal; obrigatório mesmo se invisível
        label_visible: true         # false: referência só mostra placeholder
        placeholder: ""             # literal
        required: true
        autocomplete: name          # WCAG 1.3.5
        width: full | half
        options: []                 # select/checkbox/radio (literais)
        accept: [pdf, docx]         # file
        max_size: 5mb               # file
    submit_label: "Enviar Mensagem"
    submit_icon: false
    privacy:
      notice: checkbox | text       # LGPD: aviso com link para a política
      text: "Ao enviar, você concorda com a nossa"
      link_text: "Política de Privacidade"
      policy_page: politica-de-privacidade
      shown_in_reference: true      # false = desvio intencional aprovado
    anti_spam: akismet | recaptcha_v3 | turnstile | none_local
```

## maps

Um por mapa da referência; `[]` quando conferiu e não há (obrigatória no
1.5). Ver `references/maps.md`.

```yaml
maps:
  - id: contact_map                 # vai em data-map no HTML
    section: contact_info
    evidence: [tiles, pin]          # tiles | pin | zoom_controls | provider_logo | view_larger_link | user
    provider: google | openstreetmap
    address_field: company_address  # campo da página de opções (fonte única)
    lat_field:                      # openstreetmap
    lng_field:
    embed_field: company_map_embed  # opcional
    load: click | auto              # click = fachada, carrega só no clique (padrão)
    aspect_ratio: "16:9"
    facade_media: contact_map_image # id em media[] (obrigatório com load click)
    directions_link: true
```

## media

Uma entrada por asset visual identificado no inventário (cada foto de
hero, imagem de card, logo, ícone, textura).

```yaml
media:
  - id: home_hero_photo
    purpose: "Foto de fachada no hero da Home"
    page: home
    section: home_hero
    type: photo | illustration | logo | icon | texture | background | video
    treatment: provided | crop_from_reference | placeholder | icon_library | css
    source: provided | generated | placeholder | external | unknown
    aspect_ratio: "16:9"          # obrigatório para photo/illustration/background/texture
    object_fit: cover | contain
    required:
    replace_before_launch: true   # obrigatório true para crop_from_reference/placeholder
```

Como escolher `treatment`:

| Treatment | Quando |
|---|---|
| `provided` | O usuário forneceu o arquivo real |
| `crop_from_reference` | Não há arquivo real, mas a região é aproveitável da referência — recorte com `scripts/crop_reference.py`. Sempre provisório |
| `placeholder` | Não há arquivo e o recorte não serve (baixa resolução, texto embutido, marca d'água) |
| `icon_library` | Ícones — de **uma** biblioteca declarada em `design.icon_library`, a mais parecida com a referência |
| `css` | Só formas simples: fundos chapados, gradientes, divisores, bordas |

- Foto, ilustração e logo **nunca** são desenhados em CSS ou SVG à mão.
- Texto que faz parte da imagem (ex.: lettering artístico) fica na
  imagem; texto de interface fica em HTML.
- Toda mídia raster entra em container de proporção fixa (`.media-frame`
  com `--ratio` vindo de `aspect_ratio` e `object-fit`) — o tamanho do
  arquivo nunca dita o layout.
- Todo `crop_from_reference` e `placeholder` vai para a seção "Conteúdo
  demo identificado" do `VALIDATION.md`. Nunca apresentar asset fictício
  ou provisório como asset real.

## galleries

Uma por galeria de fotos; `[]` quando conferiu e não há (obrigatória no
1.6). Ver `references/galleries.md`.

```yaml
galleries:
  - id: project_gallery             # vai em data-gallery no HTML
    section: project_gallery        # precisa estar em editable_content
    layout: grid | masonry | featured_thumbs   # carrossel de fotos -> carousels[] kind gallery
    evidence: [photo_grid, more_overlay]       # photo_grid | thumbnails | more_overlay | zoom_icon | view_all_link | user
    visible_count: 6                # fotos visíveis na referência
    total_count: 18                 # obrigatório com "+N"
    lightbox: true                  # true | false - nunca nulo (ou uncertainty bloqueante com subject = id)
    captions: false
    aspect_ratio: "4:3"             # exceto masonry
    per_row: { desktop: 3, tablet: 2, mobile: 1 }
    storage: "acf_gallery:project_gallery"     # ou "post_type:<cpt>"
```

## videos

Um por vídeo; `[]` quando conferiu e não há (obrigatória no 1.6). Ver
`references/videos.md`.

```yaml
videos:
  - id: home_video                  # vai em data-video no HTML
    section: home_about
    kind: embed | file | background # background só com evidence: [user]
    source: youtube | vimeo | file  # file para kind file/background
    evidence: [play_button, duration_badge]   # play_button | duration_badge | progress_bar | provider_logo | watch_cta | user
    url_field: home_video_url       # youtube/vimeo (URL editável no admin)
    file_field:                     # file/background (Biblioteca de Mídia)
    poster_media: home_video_poster # id em media[]
    title_field: home_video_title   # nome acessível (exceto background)
    captions: true                  # true | false - nunca nulo (WCAG 1.2.2); exceto background
    captions_field:                 # file com legenda: anexo .vtt
    aspect_ratio: "16:9"            # exceto background
    load: click                     # embed: fachada (padrão)
```

## accordions

Um por acordeão/FAQ; `[]` quando conferiu e não há (obrigatória no 1.7).
Ver `references/disclosures.md`.

```yaml
accordions:
  - id: home_faq                    # vai em data-accordion no HTML
    section: home_faq               # precisa estar em editable_content
    evidence: [plus_minus, expanded_item, question_list]   # plus_minus | chevron | expanded_item | question_list | user
    item_count: 6
    open_in_reference: [1]          # itens abertos na imagem (1 = primeiro); [] se todos fechados
    exclusive: true                 # um aberto por vez - nunca nulo (ou uncertainty bloqueante com subject = id)
    faq: true                       # pergunta/resposta
    structured_data: true           # JSON-LD FAQPage (só com faq)
    heading_level: 3                # 2..6
    storage: "repeater:home_faq_items"   # ou "post_type:faq"
    items_content: reference | user | demo
```

## tabs

Um por conjunto de abas; `[]` quando conferiu e não há (obrigatória no 1.7).

```yaml
tabs:
  - id: services_tabs               # vai em data-tabs no HTML
    section: home_services
    evidence: [tab_row, active_indicator]   # tab_row | active_indicator | segmented_control | user
    tab_count: 4                    # >= 2
    active_in_reference: 1
    mobile: scroll | stack          # da referência mobile ou decisão aprovada
    heading_level: 3
    storage: "repeater:services_tabs"
    items_content: reference | user | demo
```

## tables

Uma por tabela de dados; `[]` quando conferiu e não há (obrigatória no
1.8). Ver `references/tables-pricing.md`.

```yaml
tables:
  - id: opening_hours               # vai em data-table no HTML
    section: contact_info           # precisa estar em editable_content
    kind: data | comparison         # comparison = recursos x planos com ✓/✗
    evidence: [header_row, zebra_rows]   # grid_lines | header_row | zebra_rows | aligned_numbers | check_marks | user
    caption: "Horário de atendimento"     # obrigatório (literal ou proposto)
    caption_visible: true
    columns:
      - { key: day, label: "Dia" }
      - { key: hours, label: "Horário", type: text, align: end }   # type: text | number | currency | check
    row_count: 3
    row_header: true                # 1a coluna vira <th scope=row>
    mobile: scroll | cards
    heading_level: 3
    storage: "repeater:opening_hours_rows"   # subcampos = columns[].key
    items_content: reference | user | demo
    price_source: user | demo       # obrigatório com coluna currency
```

## pricing

Um por bloco de planos/preços; `[]` quando conferiu e não há (obrigatória
no 1.8). **Preço nunca vai ao ar como real sem confirmação.**

```yaml
pricing:
  - id: home_pricing                # vai em data-pricing no HTML
    section: home_pricing
    evidence: [plan_cards, currency_symbol, period_suffix, featured_badge, billing_toggle]
    plan_count: 3
    currency: BRL
    billing: [monthly, yearly]      # monthly | quarterly | semiannual | yearly | once
    default_billing: monthly        # obrigatório com mais de um período
    featured_plan: 2                # 1 = primeiro; obrigatório com featured_badge
    price_source: user | demo       # obrigatório
    comparison_table: plans_compare # opcional: id em tables[]
    storage: "repeater:home_pricing_plans"   # preços como campo number
```

## testimonials

Um por bloco de depoimentos; `[]` quando conferiu e não há (obrigatória
no 1.9). **Os da referência são mockup até prova em contrário** — ver
`references/social-proof.md`.

```yaml
testimonials:
  - id: home_testimonials           # vai em data-testimonials no HTML
    section: home_testimonials
    layout: grid | list | single | carousel   # carousel: + carousel: <id em carousels[]>
    evidence: [quote_marks, quote_text, author_name, author_photo]   # + rating_stars | source_badge | user
    item_count: 3
    fields_shown: [photo, city]     # photo | role | company | city | rating | source
    content_source: user | demo     # obrigatório; demo é oculto em produção
    consent: true                   # obrigatório com user (LGPD)
    storage: "post_type:testimonial"
    # structured_data: proibido (Review/AggregateRating autopromocional)
```

## client_logos

Uma por faixa/grade de logos; `[]` quando conferiu e não há (obrigatória
no 1.9).

```yaml
client_logos:
  - id: home_clients                # vai em data-client-logos no HTML
    section: home_clients
    layout: grid | row | marquee | carousel   # carousel: + carousel: <id em carousels[]>
    evidence: [logo_row, grayscale_logos, section_title]   # + marquee | certification_badges | user
    logo_count: 6
    permission: confirmed | demo    # obrigatório; demo é oculto em produção
    files: provided | pending       # com confirmed (nunca redesenhar/recortar)
    storage: "repeater:home_clients"
```

## team

Um por bloco de equipe; `[]` quando conferiu e não há (obrigatória no
1.10). Pessoas da referência são mockup até prova em contrário — ver
`references/team-stats.md`.

```yaml
team:
  - id: about_team                  # vai em data-team no HTML
    section: about_team
    layout: grid | list | carousel  # carousel: + carousel: <id em carousels[]>
    evidence: [headshots, name_role, social_icons]   # + section_title | hover_bio | user
    member_count: 4
    total_count: 8                  # opcional ("ver equipe completa")
    fields_shown: [photo, role, social]   # photo | role | bio | social | registration
    registration: none              # none | crm | cro | crp | crn | crefito | coren | oab | crea | cau | crc | creci | other
    bio: visible | collapsed | hidden     # nunca só no hover
    profile_pages: false            # obrigatório (true/false ou uncertainty)
    content_source: user | demo     # obrigatório; demo é oculto em produção
    consent: true                   # obrigatório com user (uso de imagem)
    storage: "post_type:team_member"
```

## stats

Um por bloco de números em destaque; `[]` quando conferiu e não há
(obrigatória no 1.10).

```yaml
stats:
  - id: home_stats                  # vai em data-stats no HTML
    section: home_about
    evidence: [big_number, prefix_suffix, label_below]   # + icon | user
    item_count: 3
    count_up: false                 # contagem 0 -> valor: nunca nulo (ou uncertainty com subject = id)
    content_source: user | demo     # obrigatório (afirmação de negócio)
    storage: "repeater:home_stats"  # valor número + prefixo + sufixo + rótulo
```

O número de versão é comparado como `(major, minor)` numérico: `1.10` é
mais novo que `1.9`.

## blog

Objeto único (obrigatório no 1.11); `blog: { enabled: false }` quando
conferiu e a referência não tem blog/notícias. Ver `references/blog.md`.

```yaml
blog:
  enabled: true
  label: "Blog"                     # literal da referência ("Notícias", "Artigos")
  evidence: [post_cards, dates, categories, read_more]   # + sidebar | pagination | section_title | user
  storage: post                     # sempre o post nativo (nunca CPT)
  posts_page: blog                  # slug da página de posts (precisa estar em pages[])
  posts_per_page: 9
  card_fields: [image, date, category, excerpt]   # + author | reading_time
  home_section: { id: home_blog, section: home_blog, count: 3 }   # opcional
  sidebar: false
  comments: false                   # decisão do usuário (moderação, anti-spam, privacidade)
  content_source: user | demo       # demo = meta _project_demo, oculto em produção
```

Para a captura, inclua em `pages[]` um post e uma categoria com
`capture_path` (ex.: `slug: "<post>"`, `capture_path: "meu-primeiro-post"`).

## header

Objeto (obrigatório no 1.13). Estrutura do header da referência — ver
`references/header-menu.md` (rolagem/âncoras: `references/navigation.md`).

```yaml
header:
  evidence: [logo, nav, cta_button]   # + top_bar | search_icon | account_icon | cart_icon | language | dropdown_indicator | transparent_over_hero | user
  layout: logo_left                 # logo_left | logo_center | logo_center_split
  cta: { label: "Solicitar Orçamento", target: contato }   # obrigatório com cta_button; destino real
  top_bar: []                       # phone | whatsapp | email | hours | social | text
  actions: []                       # search | account | cart (WooCommerce) | language (plugin)
  transparent: false                # true exige theme.header_scrolled (e logo_light recomendado)
  logo_light:                       # campo do logo claro
  submenus: none                    # none | dropdown | mega (menus[] com children exige dropdown/mega)
  mobile_menu: dropdown             # dropdown | offcanvas | fullscreen - referência mobile ou decisão
```

## heroes

Um por hero/cabeçalho de página (obrigatória no 1.14). Ver
`references/hero-banners.md`.

```yaml
heroes:
  - id: home_hero
    section: home_hero
    kind: background                # background | split | centered | form | page_header | carousel (+carousel) | video (+video)
    evidence: [full_bleed_image, text_over_image, headline, buttons]   # + split_layout | form | breadcrumb | page_title_band | user
    height: full                    # full | large | auto (svh, nunca 100vh)
    overlay: 0.45                   # 0..1 (o QA mede o contraste)
    mobile_image: focal             # same | focal | separate
    image_role: decorative          # decorative | informative
    h1: true                        # um h1 por página
    buttons:
      - { label: "Solicitar Orçamento", target: contato, style: primary }   # target real; whatsapp | telefone | email especiais
  - { id: about_hero, section: about_hero, kind: page_header, evidence: [page_title_band], breadcrumb: false, has_image: true, overlay: 0.5, mobile_image: focal, image_role: decorative }
```

## banners

`[]` quando não há (obrigatória no 1.14).

```yaml
banners:
  - { id: home_cta, kind: cta_band, section: home_cta, reusable: true, buttons: [{ label: "Falar no WhatsApp", target: whatsapp }] }
  - { id: aviso, kind: announcement, dismissible: true, text_field: announcement_text }
```

## footer

Objeto (obrigatório no 1.12). Estrutura do rodapé da referência — ver
`references/footer-social.md`.

```yaml
footer:
  evidence: [columns, footer_menu, contact_block, social_icons, legal_row]   # + newsletter | back_to_top | payment_seals | map | credit | user
  columns:                          # na ordem da referência
    - { id: about, kind: about, social: true }        # about | menu | contact | social | newsletter | hours | custom
    - { id: links, kind: menu, title: "Links Rápidos" }   # menu exige title (literal); vira local footer_links
    - { id: contact, kind: contact, title: "Contato" }
  copyright: "© {ano} {empresa}. Todos os direitos reservados."   # {ano} dinâmico
  legal: { privacy_link: true, terms_link: true, cnpj: hidden }    # privacy_link sempre true (LGPD); cnpj shown exige company.cnpj real
  back_to_top: false
  credit: false
```

## social

Objeto (obrigatório no 1.12); `networks: []` quando a referência não tem
redes.

```yaml
social:
  networks: [instagram, facebook, linkedin]   # ordem da referência: instagram | facebook | linkedin | youtube | tiktok | x | pinterest | threads | whatsapp | telegram | spotify
  locations: [footer]               # header | footer | contact
  urls_source: pending              # user (URLs reais em global_settings.social) | pending (vazias no admin)
```

## fonts

Objeto (obrigatório no 1.16). Ver `references/fonts.md`. Toda família de
`design.tokens.font_family` (exceto fontes do sistema) está aqui, e toda
família daqui abre algum token.

```yaml
fonts:
  delivery: self_hosted             # self_hosted (padrão: scripts/fetch_fonts.py) | system | google_cdn (exige reason - IP do visitante vai ao Google)
  fallback_metrics: true            # reserva '<Família> Fallback' com métricas ajustadas (sem salto na troca)
  families:
    - family: Manrope
      role: heading                 # heading | body | accent | other
      weights: [600, 700, 800]      # só os pesos que aparecem na referência
      styles: [normal]              # normal | italic
      source: google_fonts          # google_fonts | provided (arquivo do cliente)
      license: OFL                  # OFL | Apache-2.0 | commercial (exige license_note)
      preload: [700]                # peso do título do hero; no máximo 2 no total
```

## seo

Objeto (obrigatório no 1.15). Ver `references/security-seo.md`. Não
inventar informação empresarial (CNPJ, redes sociais, endereço) que não foi
fornecida.

```yaml
seo:
  plugin: none                      # none (SEO do tema, inc/seo.php) | yoast | rank_math | seopress | aioseo (tema se cala)
  organization_type: LocalBusiness  # Organization | LocalBusiness | subtipo schema.org (GeneralContractor, BeautySalon...) - exige global_settings.company.address
  share_image: home_hero_image      # media[].id da imagem padrão ao compartilhar (1200x630), opcional
  ai_crawlers: block_training       # obrigatório no 1.17 - PERGUNTE: allow | block_training (bloqueia treino, mantém nas buscas com IA) | block_all
  ai_crawlers_source: user          # user (escolha do usuário) | default (padrão allow aplicado - confirmar)
  pages:                            # TODA página de pages[] (menos slug variável)
    - page: home                    # id de pages[]
      description: "..."            # 50-160 caracteres, única, serviço + cidade
      description_source: proposed  # proposed (sugerida pela skill, aprovada com o Blueprint) | client | reference
      title: "..."                  # opcional, até 60 (vazio = título da página + nome do site)
    - { page: obrigado, noindex: true }   # esconde do Google e do sitemap (dispensa descrição)
```

A migração grava cada descrição no campo `seo_description` da página
(caixa "SEO e compartilhamento") e em `inc/content-defaults.php`
(`home_seo_description`, `page_<slug>_seo_description`).

## security

Objeto (obrigatório no 1.15). A proteção básica é sempre ligada; exceção só
com motivo.

```yaml
security:
  hardening: standard               # mu-plugin project-hardening + .htaccess do scaffold
  exceptions:                       # [] quando nenhuma
    - rule: xmlrpc                  # xmlrpc | author_archives | rest_users | frame_embedding
      reason: "app Jetpack do cliente exige XML-RPC"
```

Cada exceção vira `--security-exception <rule>` no scaffold (constante
`PROJECT_ALLOW_<RULE>` no `wp-config.php`).

## launch

Objeto (obrigatório no 1.18). Ver `references/go-live.md`.

```yaml
launch:
  domain: https://www.empresa.com.br   # null até o cliente confirmar; https, sem caminho
```

## branding.site_icon

`global_settings.branding.site_icon` (obrigatório no 1.18): `media[].id` do
**símbolo** do logo (sem o nome), que vira o Ícone do site, ou `pending`.
Ver `references/site-icon.md`.

## redirects

Objeto (obrigatório no 1.18). Ver `references/redirects.md`.

```yaml
redirects:
  old_site: null                    # URL do site atual do cliente, se houver
  map:                              # confirmado com o usuário (build_redirects.py --suggest propõe)
    - { from: /quem-somos.html, to: about }   # from: caminho antigo com "/"; to: id de pages[], "/caminho/" ou URL
```

Regras: `from` único e diferente do caminho exato de uma página nova (o
redirecionamento só age em 404); `old_site` com `map` vazio é aviso.

## plugins

```yaml
plugins:
  required: []
  optional: []
  prohibited: []
```

Cada plugin: `name`, `purpose`, `reason`, `source`. Ver a shortlist padrão
em `references/wordpress-architecture.md` — não adicione plugin fora dela
sem justificar.

## theme

```yaml
theme:
  name:
  slug:
  type: classic | block | hybrid
  header_behavior: sticky | static   # single_page: sempre sticky; multi_page: o que a referência mostrar
  header_scrolled:                   # opcional: estado ao rolar (sombra, fundo, compacto) - só se a referência/usuário definir
  supports: []
  structure:
    templates: []
    template_parts: []
    includes: []
    assets: []
```

## responsive

Registrar disponibilidade de referência mobile, breakpoints, comportamento
de navegação, grids, hero, tipografia, imagens e espaçamento. Sem
referência mobile, registrar a inferência explicitamente (ver
`references/responsive-guidelines.md`).

## accessibility

Registrar semantic HTML, alt text, navegação por teclado, foco, labels,
contraste, hierarquia de headings, propósito de links (ver
`references/accessibility-guidelines.md`).

## integrations

Registrar serviço, finalidade, habilitação, autorização e configuração
necessária. Nenhuma integração externa sem requisito/autorização
explícita do usuário.

## decisions

```yaml
decisions:
  - id: D001
    subject:
    decision:
    reason:
    source:
    confidence: high | medium | low
    status: pending_user_approval | approved | superseded
    affects: []
```

## uncertainties

```yaml
uncertainties:
  - id: U001
    subject:
    question:
    options: []
    impact: low | medium | high
    blocking: true | false
    status: pending | resolved
```

Incertezas críticas (`blocking: true`) bloqueiam a implementação da parte
afetada até serem resolvidas ou explicitamente autorizadas pelo usuário.

## dependencies

```yaml
dependencies:
  - id:
    from:
    depends_on:
    reason:
    type:
```

## implementation

```yaml
implementation:
  strategy:
  wordpress:
    version_constraint:
    php_version_constraint:
  theme:
    type:
    slug:
  content_model:
    strategy:
  custom_fields:
    provider: acf_pro
  dependencies:
  generation_order: []
  filesystem:
    target:
    writable:
  configuration:
    required: []
```

### Ordem de geração padrão

1. environment_validation
2. dependency_validation
3. theme_structure
4. theme_bootstrap
5. design_tokens (gera `assets/css/tokens.css` do Blueprint)
6. post_types
7. taxonomies
8. custom_fields
9. global_settings
10. menus
11. critical_slice (header + hero da Home, renderizados e comparados — ver `references/validation-playbook.md`)
12. pages
13. templates
14. template_parts
15. assets (recortes da referência, placeholders, ícones)
16. demo_content
17. configuration
18. permalinks
19. functional_tests
20. visual_validation

### Regras de implementação

- Não reinterpretar o layout após aprovação.
- Não alterar arquitetura silenciosamente.
- Mudanças estruturais geram nova versão do Blueprint.
- Melhorias que alterem arquitetura devem ser propostas antes da
  implementação, não durante.

## validation

```yaml
validation:
  architecture: { status:, checks: [] }
  functionality: { status:, checks: [] }
  content: { status:, checks: [] }
  navigation: { status:, checks: [] }
  forms: { status:, checks: [] }
  responsive: { status:, checks: [] }
  accessibility: { status:, checks: [] }
  performance: { status:, checks: [] }
  security: { status:, checks: [] }
  visual: { status:, checks: [] }
```

Ver `references/validation-playbook.md` para os checklists completos de
cada dimensão.

## generation

```yaml
generation:
  status:
  target:
    environment: local
  wordpress:
    required: true
  output:
    theme: { required: true }
    plugins: { required: true }
    database: { required: true }
    documentation: { required: true }
    demo_content: { required: true }
    tests: { required: true }
```

## Bloqueios

Bloquear a implementação (ou a parte afetada) quando:

- incerteza crítica não resolvida;
- decisão arquitetural pendente de aprovação;
- ambiente local não validado;
- dependência obrigatória ausente (ex.: wp-cli não encontrado);
- conflito entre requisitos não resolvido;
- Blueprint inconsistente (falha em `scripts/validate_blueprint.py`);
- autorização necessária ausente (ex.: integração externa sem permissão).

## Critérios de aprovação

Só considerar o Blueprint aprovado quando: objetivo definido; páginas
definidas; componentes definidos; conteúdo dinâmico definido; CPTs
definidos; campos definidos; taxonomias definidas; globais definidos;
plugins definidos; tema definido; integrações definidas; incertezas
críticas resolvidas; dependências resolvidas; estratégia de implementação
definida; e o usuário aprovou explicitamente (ver
`references/approval-protocol.md`).

## Versionamento

Mudança estrutural gera nova versão do arquivo:
`blueprint-v0.1.yaml`, `blueprint-v0.2.yaml`, etc., guardados em
`documentation/blueprint-history/`. `documentation/BLUEPRINT.yaml` é
sempre uma cópia da versão mais recente.

## Rastreamento

O Blueprint deve permitir seguir a cadeia:

```
ELEMENTO VISUAL → COMPONENTE → CONTEÚDO → DECISÃO → IMPLEMENTAÇÃO → TESTE
```

Isso é o que torna possível auditar, meses depois, por que uma
determinada estrutura existe no projeto.
