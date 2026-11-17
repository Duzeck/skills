# Modelagem de conteúdo

Pressupõe ACF PRO disponível (decisão deste ambiente). Todos os tipos de
campo do schema (`repeater`, `gallery`, `relationship`, `group` incluídos)
podem ser usados livremente.

## Processo

1. Liste toda estrutura repetitiva encontrada na análise visual.
2. Para cada uma, aplique a régua de `references/decision-framework.md`
   (3+ instâncias, campos estruturados, editável pelo admin?).
3. Para as que viram CPT: defina nome singular/plural, slug, se tem
   arquivo (`has_archive`), e se cada item tem página própria (`single`)
   ou só aparece agregado (ex.: depoimentos geralmente não têm página
   própria; projetos geralmente têm).
4. Defina os campos com tipo, obrigatoriedade e um exemplo de valor demo.
5. Verifique se há relação entre CPTs (ex.: um projeto pode referenciar
   quais serviços foram usados) — só crie `relationship` se isso aparecer
   no layout ou for pedido, não por simetria.
6. Verifique se há agrupamento/filtro visível — só então crie taxonomia.

## Padrões comuns (vocabulário consistente entre projetos)

| Situação visual | Modelagem padrão |
|---|---|
| Grid de 3+ cards de serviço com ícone + título + descrição curta | CPT `service`, campos `service_icon`, `service_short_description`, `service_detailed_description` (rich_text); imagem via `thumbnail` nativo; archive = página de Serviços; single opcional conforme pergunta ao usuário |
| Grid de projetos/portfólio com imagem + filtro por categoria | CPT `project` + taxonomia `project_category`; campos `project_gallery`, `project_location`, `project_completion_date`, `project_client`, `project_featured` (boolean para destaque na home); imagem via `thumbnail` |
| Carrossel/grid de depoimentos (`testimonials[]` — reais só com conteúdo e autorização do cliente, ver `references/social-proof.md`; carrossel: `carousels[]`) | CPT `testimonial`, campos `testimonial_client_name`, `testimonial_quote` (textarea), `testimonial_client_photo`, `testimonial_location`, `testimonial_featured`; normalmente sem single nem archive público (`public: false`, usado só via shortcode/query) |
| Grid de equipe (`team[]` — real só com autorização de imagem; registro profissional quando o setor exige, ver `references/team-stats.md`) | CPT `team_member`, campos `team_member_photo`, `team_member_role`, `team_member_bio`, `team_member_registration`, `team_member_social_links` (group) |
| Lista de perguntas frequentes (acordeão: `accordions[]` com `faq: true`, ver `references/disclosures.md`) | Repeater em ACF Options Page (não precisa de CPT separado) a menos que o FAQ seja reutilizado em várias páginas com conteúdo diferente |
| CTA repetido (texto + botão) em várias seções | Componente reutilizável com campos próprios por instância, não um CPT — é apresentação, não conteúdo editorial |
| Dados de contato no header, footer e página de contato | `global_settings.company` via ACF Options Page — nunca duplicar em múltiplos lugares do código |

## Relacionamento: exemplo correto vs. incorreto

Correto — criar porque o layout mostra explicitamente "Projetos
relacionados a este serviço":

```yaml
fields:
  - id: related_projects
    type: relationship
    target: project
```

Incorreto — criar `related_services` em `testimonial` só porque "poderia
ser interessante algum dia". Isso é inferência não autorizada; se não há
evidência visual nem pedido do usuário, não crie.

## Regras de campos ACF

O objetivo é um modelo que continue compreensível quando o site dobrar de
conteúdo, sem retrabalho de renomear campos depois que o admin já os
preencheu.

**Nomes estáveis com prefixo de domínio.** Todo campo de content type
começa com o id do CPT: `service_short_description`, `project_location`.
Nomes genéricos (`title`, `image`, `link`, `description`, `cta`) perdem o
sentido fora de um template e colidem entre CPTs — o
`validate_blueprint.py` bloqueia. Campos de componente seguem a mesma
lógica com o id do componente (`hero_subtitle`, `cta_label`). Templates
leem sempre pelo **nome**, nunca pela field key (`field_...`).

**Nunca renomeie campo depois da aprovação sem migração.** Renomear
`service_icon` com conteúdo já salvo apaga o vínculo para o admin. Se for
inevitável, é mudança estrutural: nova versão do Blueprint + rotina de
migração da meta antiga (`wp db query` / `wp eval-file`) registrada no
`DECISIONS.md`.

**Repeater vs. CPT.** Repeater só quando os itens:
- pertencem a um único pai e não aparecem em outro lugar;
- não precisam de URL própria, filtro, busca ou ordenação entre pais;
- não têm ciclo de vida próprio (publicar/despublicar individualmente).
Falhou qualquer um → é CPT (com `relationship`, se precisar ligar ao pai).
Todo repeater tem `min`/`max` coerentes com o layout (o grid da referência
mostra 3 itens? `min: 3`, `max` no que o layout comporta) e `sub_fields`
também prefixados.

**Taxonomia vs. campo.** Classificação compartilhada entre itens
(categoria, região, tipo) é taxonomia, nunca texto livre ou `select`
repetido — texto livre gera grafias divergentes e filtro quebrado.

**Instruções para o editor.** Todo campo tem `description` no Blueprint,
que vira `instructions` no ACF: diga onde aparece e o limite prático
("Até 2 linhas; aparece no card da Home").

**Formato de retorno consistente.** Defina uma vez por projeto como
imagem é lida (ID, recomendado — permite `wp_get_attachment_image()` com
`srcset`) e use o mesmo formato em todos os campos de imagem. Idem para
`relationship` (IDs).

**Options Page sem surpresa.** `project_get_global_setting()` sempre
recebe um `$default` e o template trata vazio (não imprime ícone de
WhatsApp sem número). Não misture na mesma Options Page dados de
contato, textos de marketing e credenciais de integração — separe por
responsabilidade em abas ou páginas.

**Campos como código.** Os grupos ficam em `inc/acf-fields.php` via
`acf_add_local_field_group()`, versionados com o tema. Não edite grupos
pela UI do ACF no projeto — o código é a fonte de verdade e a UI sobrescreve
sem deixar rastro.

## Todo conteúdo visível é editável

Modelar só os CPTs não basta: títulos de seção, textos de hero, botões,
números, CTA e rodapé também são conteúdo. Se o administrador não consegue
alterá-los pelo painel, o site não é administrável. Padrão desta skill:

| Parte do site | Onde fica | Leitura no template |
|---|---|---|
| Dados globais (logos, contato, redes), botão do cabeçalho, CTA final, rodapé | Página de opções **Configurações do Site** (abas) | `project_option()` |
| Seções da Home (hero, títulos, textos, números, imagens) | Campos da **página inicial estática** (abas por seção) | `project_home()` |
| Cabeçalho de páginas (título, subtítulo, foto) | Campos da própria página | `project_page_field()` |
| Cabeçalho de arquivos de CPT (`/servicos/`) | **Subpágina** de opções (arquivo não é página) | `project_option()` |
| Itens repetitivos (cards) e sua ordem | CPT + `page-attributes` (campo "Ordem") | `WP_Query` por `menu_order` |
| Filtros / categorias | Taxonomia | `get_terms()` |
| Navegação | Menus (itens com destino real) | `wp_nav_menu()` |
| Galeria de fotos (lightbox, "+N") | Campo galeria do ACF PRO + `template-parts/gallery.php` | `galleries[]` — ver `references/galleries.md` |
| Vídeo (YouTube/Vimeo, arquivo, fundo) | Campo URL/arquivo + capa + `template-parts/video.php` | `videos[]` — ver `references/videos.md` |
| Tabela de dados (horários, especificações, comparativo) | Repeater com um subcampo por coluna + `template-parts/table.php` | `tables[]` — ver `references/tables-pricing.md` |
| Planos e preços | Repeater/CPT com preço em campo **number** + `template-parts/pricing.php` | `pricing[]`; valores só reais com confirmação |
| Logos de clientes/parceiros | Repeater (nome, logo, url) ou CPT `client` + `template-parts/client-logos.php` | `client_logos[]` — só com permissão confirmada, ver `references/social-proof.md` |
| Números em destaque ("+150 projetos") | Repeater: valor (número), prefixo, sufixo, rótulo + `template-parts/stats.php` | `stats[]` — valores só reais com confirmação |
| Blog / notícias | **Post nativo** + categorias/tags nativas (nunca CPT "blog") | `blog` — ver `references/blog.md` |
| Hero, cabeçalho de página, faixa de chamada, barra de aviso | Campos da página (hero, `page_hero_*`) e página de opções (`cta_*`, `announcement_*`) | `heroes` / `banners` — ver `references/hero-banners.md` |
| Header (logo claro/escuro, botão de destaque, barra superior) | Estrutura em `inc/header.php`; conteúdo na página de opções (`company_logo(_light)`, `header_cta_label/target`) | `header` — ver `references/header-menu.md` |
| Rodapé (colunas, contato, faixa legal) e redes sociais | Estrutura em `inc/footer.php`; conteúdo na página de opções (títulos, textos, contato, `social_<rede>`) | `footer` / `social` — ver `references/footer-social.md` |
| SEO e compartilhamento (título na busca, descrição, imagem ao compartilhar, esconder dos buscadores) | Caixa "SEO e compartilhamento" em páginas/posts/CPTs (`seo_title`, `seo_description`, `seo_image`, `seo_noindex`) + imagem padrão na página de opções (`seo_default_image`), registrados por `inc/seo.php` | `seo.pages` — descrições aprovadas gravadas pela migração; ver `references/security-seo.md` |
| Formulário | Contact Form 7 (gerado de `forms[]` por `build_cf7_form.py`) | `project_form()` — ver `references/forms.md` |

Regras:

- **Fonte única com reserva:** `inc/content-defaults.php` guarda o
  conteúdo da referência com as chaves dos campos. Os helpers caem nele se o
  campo estiver vazio, e a migração do projeto **preenche os campos com ele**
  (`update_field()` pela field key) — o admin nunca abre com campos vazios.
- **Imagens na Biblioteca de Mídia:** recortes provisórios são importados
  (`media_handle_sideload`) e atribuídos aos campos/imagem destacada, com a
  descrição "PROVISÓRIA". O arquivo em `assets/img/` fica só como reserva.
- **Quebras de linha vêm do admin:** título em várias linhas = textarea
  renderizado com `project_lines()` (`<br>`), não `&nbsp;` + largura no CSS.
- **Instruções em todo campo:** onde aparece e o formato esperado.
- **Uma seção repetida em duas páginas lê os mesmos campos** (ex.: bloco
  "Sobre" da Home reaproveitado na página Sobre) — nunca duplique.
- **Prove a editabilidade:** altere um campo de cada grupo via
  `update_field()`, confira a página renderizada e reverta (ver
  `references/validation-playbook.md`).

## Leitura de campos nos templates

Use sempre `project_field('nome_do_campo')` (definido em
`inc/helpers.php` do theme-skeleton) em vez de `get_field()` direto nos
templates. `get_field()` só funciona quando o ACF PRO está ativo e o
campo foi preenchido pela própria UI do ACF (que grava uma meta de
referência interna) — conteúdo demo semeado via
`scripts/seed_demo_content.py` grava meta bruta e fica invisível para
`get_field()` mesmo que o valor exista no banco. `project_field()` cai
para `get_post_meta()` bruto nesse caso, então o conteúdo aparece desde o
scaffold, mesmo antes do admin configurar o ACF.

## Conteúdo demo

Quando o conteúdo definitivo não for fornecido:

- Use primeiro os textos do inventário `copy` do Blueprint: se a
  referência mostra "Reforma Residencial" num card, o item semeado se
  chama exatamente assim e não é demo. Só o que não está legível ou não
  aparece na referência vira demo.
- Rode `scripts/seed_demo_content.py --blueprint ... --check-only` antes
  de semear: ele barra meta fora dos fields do Blueprint e lista o que é
  referência vs. DEMO para o `VALIDATION.md`.
- Escreva conteúdo demo plausível e específico do domínio do negócio
  descrito (ex.: para uma construtora, um serviço demo chama-se
  "Reforma Residencial", não "Serviço 1" nem Lorem Ipsum).
- Marque explicitamente no `VALIDATION.md`/`README.md` do projeto quais
  itens são demo.
- Nunca preencha `global_settings.company.phone/email/address` com valor
  inventado — se não foi fornecido, deixe um placeholder óbvio como
  `"(preencher)"` e registre como `uncertainty`.
