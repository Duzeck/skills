---
name: duzeck-wordpress-site-builder
description: >
  Transforma uma referência visual de site (imagem ou conjunto de imagens;
  PDF é aceito oportunisticamente, Figma/HTML ficam para versões futuras)
  em um projeto WordPress real, administrável, responsivo e executável
  localmente no WAMP. Age como pipeline de engenharia: análise visual →
  inventário → classificação estática/dinâmica → modelagem de conteúdo
  (CPTs, campos ACF, taxonomias) → Blueprint aprovado → implementação →
  testes → validação visual → correção. Use sempre que o usuário pedir
  para transformar uma imagem/referência em um site WordPress, montar um
  tema a partir de um layout, tornar administrável um conjunto de
  cards/seções repetitivas de um design, ou construir um site institucional
  completo a partir de uma referência visual. NÃO ative a pipeline completa
  quando o pedido for explicitamente "só uma página HTML estática" ou
  "ajustar CSS de um WordPress já existente para ficar parecido com X" —
  nesses casos, trate como tarefa direta sem Blueprint nem CPTs.
  Distingue single page (menu de âncoras, header sticky sempre visível)
  de site multipáginas, e identifica carrosséis, banners rotativos,
  formulários, mapas, galerias, vídeos, acordeões, FAQs, abas, tabelas,
  preços, depoimentos, logos de clientes, equipe, números em destaque,
  blog e notícias, hero e banners, header e menu, rodapé e redes sociais.
  Todo site sai com SEO editável por página, proteção básica do WordPress e
  fontes hospedadas no próprio site, sem salto na troca.
---

# duzeck-wordpress-site-builder

Skill pessoal e privada. Prioriza produtividade local, controle, clareza,
rastreabilidade e qualidade — não distribuição pública.

## Objetivo: o site é o espelho da referência

O resultado visível tem de ser **o espelho da imagem de referência**:
mesmas seções na mesma ordem, mesma composição (o que está à esquerda
fica à esquerda, foto de fundo continua foto de fundo), mesmos textos
letra por letra — com acentos —, mesma paleta, mesma tipografia, mesmas
proporções. Administrabilidade (CPTs, ACF) é o que fica **por baixo** do
espelho; nunca é motivo para simplificar o que aparece.

Consequências não negociáveis:

- **Nada some.** Toda seção, card, botão, ícone e imagem da referência
  aparece no site. Imagem sem arquivo real vira recorte da referência ou
  placeholder com a mesma proporção — nunca um espaço vazio, nunca o
  layout colapsando porque o post não tem thumbnail.
- **Nada é reescrito.** Texto da referência é copiado literalmente, em
  UTF-8, com acentos ("Orçamento", não "Orcamento"). Proibido "ASCII por
  segurança".
- **Nada é inventado nem "melhorado".** Sem seção, rótulo, métrica ou
  estilo que a referência não mostra; sem trocar a composição por um
  padrão genérico (hero centralizado, títulos centralizados, cards
  cinza) só porque é mais fácil.
- **Tudo que aparece é editável no admin.** Cada texto, imagem, botão e
  link visível vem de um campo (ACF), da página de opções, de um CPT, de
  uma taxonomia, de um menu ou do formulário — nunca escrito no template.
  O mapa "onde editar" é a seção `editable_content` do Blueprint, e o
  conteúdo da referência entra como **valor inicial dos campos** (os campos
  nunca nascem vazios; as imagens vão para a Biblioteca de Mídia). Ver
  `references/content-modeling.md` → "Todo conteúdo visível é editável".
- **O esqueleto do tema é estrutura, não design.** Nenhuma regra visual
  do `assets/theme-skeleton/` sobrevive se a referência mostrar outra
  coisa: todo layout vem da referência.
- **Fidelidade se prova com evidência**, nunca com "correspondência
  próxima": portão de QA com `compare-*.png` e ledger (passo 9).

Qualquer divergência visível é um defeito, a menos que esteja registrada
como desvio intencional **e aprovada pelo usuário**.

## Princípio central

O Blueprint é o contrato entre análise e implementação. Depois de
aprovado, ele é a fonte de verdade: não reinterprete o layout livremente
durante a implementação. Se durante a implementação surgir uma melhoria
que afete CPT, campo, taxonomia, relacionamento, plugin, template ou fluxo
funcional, proponha a mudança e gere uma nova versão do Blueprint antes de
continuar — nunca altere arquitetura silenciosamente.

Uma resposta que parece completa mas inventou uma decisão arquitetural é
pior do que uma resposta que identifica corretamente a incerteza e
pergunta. Prefira sempre a segunda.

## Estrutura do site: single page × multipáginas

Todo projeto é **uma** das duas estruturas, decidida no passo 1 e gravada
em `project.site_structure` — ela muda menu, header, templates e QA:

- **`single_page`** — uma página com seções; o menu leva a seções da
  própria página. Regras obrigatórias:
  - **o header acompanha a rolagem e fica sempre visível**
    (`theme.header_behavior: sticky`), implementado com as práticas do
    esqueleto: `position: sticky` (não `fixed`), `scroll-padding-top` com a
    altura real do header, scroll-spy e estado rolado via
    `IntersectionObserver` (nenhum listener de `scroll`), rolagem suave só
    sem `prefers-reduced-motion`, offset da barra de admin, menu mobile
    acessível e funcionamento sem JS;
  - cada seção de destino tem `anchor` (slug sem acento, estável) e cada
    item do menu é `type: anchor` (`#servicos`) — no admin, link
    personalizado com URL **relativa**;
  - o item da seção visível recebe `aria-current="location"`.
- **`multi_page`** — várias páginas; o menu leva a páginas/arquivos e o
  header segue a referência (`static` por padrão; `sticky` só se a
  referência ou o usuário pedir).

Na dúvida, `uncertainty` bloqueante — não presuma. Critérios, práticas e
o porquê de cada uma: `references/navigation.md`.

## Quando NÃO acionar a pipeline completa

- Pedido explícito de "apenas uma página HTML" → entregue HTML/CSS direto,
  sem Blueprint, sem CPTs.
- "Tenho um WordPress pronto, só ajuste o CSS/layout para parecer com
  isto" → trate como tarefa de ajuste pontual no tema existente.
- Landing page única, sem nenhuma estrutura visivelmente repetitiva → não
  crie CPTs artificialmente: é `single_page` com seções em campos da
  página (continua administrável e com header sticky).

Nesses casos, ainda assim avise brevemente que a pipeline completa (com
Blueprint e CPTs) existe e pode ser acionada se o usuário quiser conteúdo
administrável depois.

## Pressupostos padrão deste ambiente (já decididos pelo usuário)

Estes são padrões pessoais, não perguntas a repetir a cada projeto:

- **Ambiente local**: WAMP. Projetos ficam em `C:\wamp64\www\<slug>`,
  acessíveis em `http://localhost/<slug>/`. Ver `references/local-environment.md`.
- **Campos complexos**: ACF PRO está licenciado e disponível — pode ser
  usado livremente para `repeater`, `gallery`, `relationship`, `group`
  sempre que a modelagem pedir.
- **Formulário de contato**: padrão é Contact Form 7. Só considere outra
  abordagem (handler PHP nativo) se o usuário pedir explicitamente "sem
  plugins" para esse projeto específico — nesse caso, registre o conflito
  entre "sem plugins" e "formulário administrável" como decisão explícita
  em vez de decidir sozinho.
- **Tema**: clássico por padrão, pelo controle preciso de HTML/CSS/template
  que a spec exige. Só considere tema de blocos (FSE) se o usuário pedir.

## Workflow

1. **Escopo e entradas.** Confirme o que foi pedido (pipeline completa vs.
   exceção da seção acima). Reúna as referências visuais. Se vier mais de
   uma imagem/página, mapeie cada arquivo à página correspondente — se a
   correspondência não for óbvia pelo conteúdo, pergunte antes de seguir.
   Não pergunte o que o usuário já informou (telefone, WhatsApp, páginas,
   etc.) — reaproveite. **Decida a estrutura** (`single_page` ou
   `multi_page`, ver "Estrutura do site" acima e
   `references/navigation.md`); se a referência não deixar claro,
   pergunte.

2. **Mapa da referência, depois inventário.** Antes de qualquer
   classificação, percorra cada imagem de cima para baixo (e, em
   colagens, coluna por coluna) e registre em `reference_map` **toda**
   região visível com sua caixa em pixels (`x, y, largura, altura`) e a
   página/seção a que pertence. Colagem com várias páginas ou uma página
   continuada em outra coluna é comum — mapeie a continuação, não a
   descarte. Uma região sem seção correspondente no Blueprint é seção
   esquecida. Recorte as referências por página com
   `scripts/crop_reference.py` (elas alimentam o `--ref` da captura).
   Depois, para cada referência, identifique
   header, logo, navegação, hero, títulos, botões, cards, grids, listas,
   tabelas, depoimentos, FAQs, CTAs, formulários, footer, elementos únicos
   vs. repetitivos, e pistas de responsividade. Ver
   `references/wordpress-architecture.md`. No mesmo passe, produza dezesseis
   inventários que alimentam o Blueprint:
   - **Textos visíveis** (`copy`): menu, títulos, CTAs, rótulos e footer
     transcritos literalmente, com legibilidade. Não invente rótulos,
     métricas ou seções que a referência não mostra.
   - **Mídia** (`media`): cada foto, logo, ícone e textura com tipo,
     proporção e tratamento (fornecido / recorte da referência /
     placeholder / biblioteca de ícones / CSS simples). Foto, ilustração
     e logo nunca são redesenhados em CSS/SVG.
   - **Carrosséis** (`carousels`): procure em cada seção os sinais de
     rotação — bolinhas, setas, contador "01 / 05", barra de progresso,
     card cortado na borda. A imagem só mostra o slide 1: o número de
     slides vem das bolinhas/contador, e autoplay, intervalo e conteúdo
     dos demais slides **são perguntados**, nunca presumidos. Sem nenhum
     carrossel, registre `carousels: []`. Ver `references/carousels.md`.
   - **Formulários** (`forms`): cada campo com tipo (caixa alta =
     textarea, seta = select...), rótulo e placeholder **literais**,
     obrigatoriedade, largura, texto do botão e aviso de privacidade. O
     e-mail de destino e as opções que a imagem não mostra são
     perguntados. Ver `references/forms.md`.
   - **Mapas** (`maps`): ruas/quarteirões, pin, botões + / −, logo do
     provedor. O endereço vem da página de opções; o mapa carrega só no
     clique. Sem mapa, `maps: []`. Ver `references/maps.md`.
   - **Galerias** (`galleries`): só fotos lado a lado, miniaturas, "+N",
     lupa, "ver todas". Quantas aparecem e o total (pelo "+N") vêm da
     imagem; se clicar amplia (lightbox) é perguntado. Grid de cards com
     título e texto não é galeria. Ver `references/galleries.md`.
   - **Vídeos** (`videos`): ▶ sobre imagem, duração "3:45", logo do
     provedor. A URL/arquivo e se há legenda são perguntados; vídeo de
     fundo só existe com confirmação do usuário (numa imagem estática é
     igual a uma foto). Sem nenhum, `galleries: []` / `videos: []`. Ver
     `references/videos.md`.
   - **Acordeões, FAQ e abas** (`accordions`, `tabs`): linhas com "+",
     "−" ou setinha (uma aberta); fileira de rótulos com um destacado
     sobre um painel. Quantidade, títulos e o que está aberto/ativo vêm
     da imagem; o conteúdo dos itens fechados e das abas inativas, se
     abre um por vez e o comportamento das abas no celular são
     perguntados. Dropdown de menu e filtro de categorias não são
     abas. Sem nenhum, `accordions: []` / `tabs: []`. Ver
     `references/disclosures.md`.
   - **Tabelas e preços** (`tables`, `pricing`): grade com cabeçalho,
     zebra, números alinhados, ✓/✗; "R$", "/mês", cards de planos, "Mais
     popular", preço riscado, "Mensal / Anual". Colunas, contagens e o
     que está destacado vêm da imagem; **o valor de cada preço só é real
     se o usuário confirmar** (`price_source: user`), senão é demo
     marcado. Grid de cards e colunas de layout não são tabela. Sem
     nenhum, `tables: []` / `pricing: []`. Ver
     `references/tables-pricing.md`.
   - **Depoimentos e logos de clientes** (`testimonials`,
     `client_logos`): aspas, fala + nome + foto, estrelas; fileira de
     marcas (cinza, "Clientes", "Parceiros", faixa rolando). Contagem e o
     que cada item mostra vêm da imagem; **o conteúdo da referência é
     mockup** — depoimento real só com texto e autorização do cliente
     (`content_source: user` + `consent`), logo real só com permissão e
     arquivo da empresa (`permission: confirmed`); senão `demo`, que o
     tema não mostra em produção. Sem nenhum, `testimonials: []` /
     `client_logos: []`. Ver `references/social-proof.md`.
   - **Equipe e números em destaque** (`team`, `stats`): grade de
     fotos de rosto com nome e cargo (redes, registro profissional);
     número grande + "+"/"%" + rótulo. Contagens e o que aparece vêm da
     imagem; pessoas reais só com nomes, fotos e autorização de imagem,
     números reais só confirmados (afirmação de negócio), senão `demo`
     (oculto em produção). Registro profissional (CRM, OAB, CREA...)
     nunca inventado; se o número conta de 0 até o valor é perguntado.
     Sem nenhum, `team: []` / `stats: []`. Ver
     `references/team-stats.md`.
   - **Blog e notícias** (`blog`): cards com data, categoria, resumo e
     "Leia mais"; "Blog", "Notícias", "Últimas do blog"; barra lateral e
     paginação. Usa o **post nativo** (nunca CPT), com página de posts,
     campos do card, trecho na Home e comentários decididos com o
     usuário. Posts da referência são `demo` (ocultos em produção em
     todas as saídas). Grid de projetos/serviços não é blog. Sem blog,
     `blog: { enabled: false }`. Ver `references/blog.md`.
   - **Hero e banners** (`heroes`, `banners`): tipo do hero (foto de
     fundo, dividido, centralizado, com formulário, cabeçalho de página
     interna, rotativo, vídeo), botões literais com destino real,
     camada de contraste, enquadramento no celular, trilha de navegação;
     faixa de chamada reutilizável e barra de aviso. Ver
     `references/hero-banners.md`.
   - **Fontes** (`fonts`): família do título e do texto, **só os pesos que
     aparecem** (título, texto, botão), itálico se houver e o peso do título
     do hero (pré-carregado). Hospedadas no próprio site (nunca o link do
     Google Fonts: IP do visitante vai ao Google), licença conhecida. Ver
     `references/fonts.md`.
   - **Ícone, publicação e site antigo** (`branding.site_icon`, `launch`,
     `redirects`): o **símbolo** do logo vira o Ícone do site
     (`make_site_icon.py`, `references/site-icon.md`); o domínio final é
     perguntado antes de publicar; se a empresa já tem site, os endereços
     antigos levam aos novos (`build_redirects.py --suggest`,
     `references/redirects.md`).
   - **SEO e segurança** (`seo`, `security` — não vêm da imagem, são
     sempre decididos): descrição de busca **proposta** para cada página
     (50–160 caracteres, única, serviço + cidade, aprovada com o
     Blueprint), robôs de IA no robots.txt (`allow`, `block_training` ou
     `block_all` — pergunte: bloquear treino sem sumir das buscas com IA?),
     tipo schema.org da empresa (`Organization` ou
     LocalBusiness/subtipo com endereço), plugin de SEO do cliente (se
     houver, o tema se cala) e a proteção básica sempre ligada, com
     exceção só por motivo. Ver `references/security-seo.md`.
   - **Header e menu** (`header`, `menus`): posição do logo, itens do
     menu (literais, na ordem), botão de destaque, barra superior,
     ícones de ação (busca, conta), indicador de submenu e se o header
     fica transparente sobre o hero. O menu mobile e o estado ao rolar
     não aparecem na imagem desktop: referência mobile ou decisão. Ver
     `references/header-menu.md`.
   - **Rodapé e redes sociais** (`footer`, `social`): cada coluna na
     ordem (sobre, menus com título, contato, redes, newsletter), a faixa
     inferior (copyright, CNPJ, links legais, crédito) e quais redes
     aparecem, em que ordem e onde (header/rodapé/contato). URLs de redes,
     CNPJ e contatos nunca são inventados — rede sem URL não aparece;
     ícone ilegível vira pergunta. Ver `references/footer-social.md`.
   - **Medidas** (`design.tokens`): cores em hex, famílias tipográficas,
     escala de tamanhos, escala de espaçamento, raios, sombras, largura do
     container — medidos na referência, com `confidence`.

3. **Classificação.** Classifique cada elemento como Global / Static /
   Dynamic / Configurable. Ver `references/decision-framework.md`.

4. **Modelagem de conteúdo.** Estrutura repetitiva (ex.: vários cards de
   serviço/projeto) não vira automaticamente HTML repetido — avalie se
   representa um Custom Post Type, campos e/ou taxonomia. Ver
   `references/content-modeling.md`. Pergunte quando o impacto for
   arquitetural (ex.: "cada projeto terá página própria?"). Na mesma
   etapa, defina **onde cada seção é editada** (`editable_content`):
   seções da Home como campos da página inicial estática, dados globais
   e blocos repetidos (CTA, rodapé) na página de opções, cabeçalhos de
   páginas como campos da página, cabeçalhos de arquivos de CPT numa
   subpágina de opções.

5. **Blueprint.** Monte o Blueprint seguindo a estrutura completa de
   `references/blueprint-schema.md`. Salve em
   `<projeto>/documentation/BLUEPRINT.yaml`. Rode
   `scripts/validate_blueprint.py` antes de seguir para a aprovação —
   ele falha se houver incerteza bloqueante não resolvida, token de
   design inválido, campo ACF com nome genérico, mídia provisória sem
   marcação ou mídia desenhada em CSS indevidamente.

6. **Aprovação.** Nunca despeje o YAML inteiro no chat. Gere o resumo com
   `scripts/render_blueprint_summary.py` (decisões + incertezas
   pendentes) **e a página visual** com `scripts/render_approval_page.py`
   (`documentation/APROVACAO.html`: cores, fontes reais, botões, cada seção
   ao lado do recorte da referência, menu no celular desenhado). Peça
   aprovação explícita pelos itens numerados. Ver
   `references/approval-protocol.md` para o que conta como aprovação e
   quando bloquear a implementação.

7. **Plano de implementação e geração.** Siga a `generation_order` do
   Blueprint (ambiente → dependências → estrutura do tema → CPTs →
   taxonomias → campos → globais → menus → páginas → templates → assets →
   conteúdo demo → configuração → permalinks → testes). Parta de
   `assets/theme-skeleton/` como ponto de partida do tema, não comece do
   zero. Use `scripts/scaffold_wp_project.py --site-structure <...>
   --schema-type <seo.organization_type> --ai-crawlers <seo.ai_crawlers>
   [--security-exception <regra>]`
   para criar o projeto no WAMP (pasta, banco, `wp-config.php`, instalação
   do core, ativação do tema; grava a estrutura, o comportamento do header
   e o tipo schema.org em `functions.php`). O scaffold já sai protegido:
   senha forte aleatória para o admin (repasse ao usuário, ela não fica
   salva), `DISALLOW_FILE_EDIT`, mu-plugin `project-hardening.php` e o
   bloco "Project hardening" no `.htaccess` (`references/security-seo.md`).

   Logo após o scaffold, hospede as fontes com `scripts/fetch_fonts.py
   BLUEPRINT.yaml --theme <tema>` (woff2 no próprio site + reserva ajustada)
   e gere `assets/css/tokens.css` com
   `scripts/generate_design_tokens.py` — o `style.css` só usa `var(--...)`,
   nunca cor ou medida literal. Recortes provisórios da referência saem de
   `scripts/crop_reference.py`. Gere junto o `theme.json` do editor (`--theme-json <tema>/theme.json`):
   paleta, fontes e tamanhos da marca no editor de blocos, só `settings`
   (`references/editor.md`).

   **Construa por fatias, não tudo de uma vez.** Depois da infraestrutura
   (CPTs, campos, globais), implemente primeiro a **fatia crítica**:
   header + hero da Home sobre os tokens gerados — em single page, já
   com o header sticky e as âncoras funcionando. Renderize, compare
   com a referência e corrija até não haver P0/P1 (ver
   `references/validation-playbook.md`). Mostre ao usuário o
   `aprovacao-visual.html` da captura (referência × site, desktop e celular)
   e **espere a aprovação** — só então propague o sistema
   para as demais seções e páginas. Em páginas longas, repita o laço
   seção a seção. Um erro de grid, container, fonte ou escala de espaçamento
   descoberto na fatia crítica custa uma correção; descoberto no fim, custa
   uma correção por página.

   **Pontos de restauração.** Rode `scripts/checkpoint.py --label <marco>`
   após o scaffold, antes do seed (`pre-seed`), ao fechar a fatia crítica
   e ao fim de cada rodada de QA. Se uma rodada de correção piorar o
   resultado, proponha voltar ao ponto anterior — restaurar é destrutivo
   e exige confirmação do usuário.

8. **Conteúdo demo.** Quando o conteúdo definitivo não for fornecido, use
   `scripts/seed_demo_content.py --blueprint` a partir dos `content_types`
   do Blueprint — títulos visíveis na referência (`copy`) são usados
   literalmente e não contam como demo. Nunca use Lorem Ipsum quando for possível escrever conteúdo
   demo plausível para o domínio do negócio. Marque claramente no
   README do projeto o que é demo vs. real — nunca apresente dado
   fictício como dado real da empresa.

9. **Testes e validação.**
   - Técnico/funcional: `scripts/check_theme.py` (lint PHP, estrutura,
     dado global fixo no código, placeholder esquecido, saída ACF sem
     escape), mais checagem funcional via wp-cli (tema ativa,
     CPTs/campos/taxonomias funcionam, menus, permalinks, formulário envia).
   - Segurança: `scripts/check_security.py --url <home> --path <pasta>`
     testa o site rodando como um ataque testaria (XML-RPC, login vazando
     por `?author=`/REST, erro de login revelador, listagem de pastas,
     versão exposta, cabeçalhos, senha de admin óbvia). P1 bloqueia a
     entrega.
   - Visual — **portão de QA bloqueante**: rode
     `scripts/capture_site.py --blueprint ... --ref ...` para capturar
     cada página em desktop (1440), tablet (834) e mobile (390) — ele já
     aponta rolagem horizontal, erros de JS/console, imagens e links
     quebrados e violações axe; com header sticky, aponta também header
     que some ao rolar, âncora do menu sem seção e destino encoberto pelo
     header; com carrossel, aponta carrossel ausente, número de slides,
     controles e autoplay divergentes do Blueprint; com formulário e mapa,
     campos/rótulos/botão divergentes, mapa que carrega antes do clique e,
     com `--submit-forms --mail-log`, envio que não chega ao destinatário;
     galeria com contagem/alt/lightbox divergentes e vídeo que carrega
     antes do clique ou toca com movimento reduzido; acordeão/abas com
     contagem, item aberto/aba ativa, "um por vez", JSON-LD, teclado ou
     link direto divergentes; tabela sem caption/scope/região rolável e
     preço fora do padrão "R$ 1.234,56", sem destaque ou seletor de
     período quebrado; depoimento sem nome/"N de 5", JSON-LD
     autopromocional, logo com alt "logo" e faixa sem pausa; pessoa sem
     nome/registro, bio só no hover e número sem valor final no HTML ou
     animando com movimento reduzido; card de post com links duplicados
     ou sem `<time>`, paginação sem `aria-label` e post sem JSON-LD;
     rodapé com colunas/títulos divergentes, rede com link `#` ou sem
     nome, `tel:`/`wa.me` inválidos, sem link de privacidade ou ano
     desatualizado; header com menu/botão divergentes, submenu sem
     botão ou que o teclado não opera, logo sem nome e header
     transparente ilegível; hero com contraste medido abaixo do mínimo,
     mais de um `h1`, imagem que não é o LCP e trilha sem JSON-LD.
     Gera `compare-*.png` com referência e implementação lado a
     lado. Compare **no mesmo viewport**, em visão
     inteira **e** em recortes por região, e registre cada divergência no
     ledger do `VALIDATION.md` com severidade P0–P3. Use `claude-in-chrome`
     para estados interativos (hover, menu mobile, formulário, filtros).
   - Servidor respondendo, tema ativo ou `check_theme.py` OK **não são**
     validação visual. Sem captura e comparação feitas, o resultado é
     `blocked`, nunca "validado".
   - Ver `references/validation-playbook.md` para o procedimento, a
     régua P0–P3 e a ordem de prioridade de correção.

10. **Ciclo de correção.** Corrija na ordem de prioridade do playbook
    (composição → proporções → hierarquia → tipografia → espaçamento →
    cor → mídia → ícones) — nunca ajuste detalhe com a estrutura ainda
    errada. Diferença puramente visual → corrija direto no tema,
    recapture no mesmo viewport e atualize o ledger. Diferença que mexe em
    CPT/campo/taxonomia/template/fluxo → volte ao Blueprint, registre a
    mudança, gere nova versão (`blueprint-v0.2.yaml`, etc.) antes de
    reimplementar. Repita até não restar P0/P1/P2; P3 vira nota de
    acompanhamento, não motivo para novo ciclo. A entrega só acontece com
    `Resultado final: passed` no `VALIDATION.md`.

11. **Entrega.** Gere `README.md`, `DECISIONS.md` e `VALIDATION.md` no
    projeto a partir de `assets/*.template.md`, preenchidos com o conteúdo
    real do Blueprint e dos testes executados.

12. **Publicação.** Antes de publicar, `scripts/prelaunch_check.py --path
    <site> --blueprint ... --stage local` junta numa lista única tudo o que
    falta (SMTP, e-mails de teste, usuário `admin`, Política de Privacidade,
    conteúdo de exemplo, imagens provisórias, pendências, Ícone do site,
    redirecionamentos, domínio) — zere P0/P1. Com o domínio confirmado
    (`launch.domain`), `scripts/go_live.py` monta o pacote sem tocar no site
    local: cópia de segurança, banco com o domínio trocado (inclusive dados
    serializados e o JSON dos blocos), arquivos, `.htaccess` da raiz,
    `favicon.ico`, chaves novas e o passo a passo. No endereço final, rode
    de novo com `--stage production`. Ver `references/go-live.md`.

## Regras de bloqueio

- Incerteza com `blocking: true` não resolvida → não implemente essa
  parte; pergunte primeiro.
- Decisão arquitetural (`status: pending_user_approval`) ainda não
  aprovada → não implemente.
- Conflito entre requisitos (ex.: "sem plugins" + campo que exige
  ACF/Contact Form 7) → registre o conflito e apresente opções; nunca
  decida silenciosamente qual lado "vence".
- Nunca invente destinatário de formulário, número de WhatsApp, endereço,
  credencial ou integração externa sem autorização explícita.
- Nunca duplique dado global (telefone, WhatsApp, endereço, redes sociais)
  em mais de um lugar no código — uma única fonte de verdade (ACF Options
  Page ou equivalente).
- Nunca apresente ambiente local como validado sem de fato ter rodado o
  site (WAMP respondendo, tema ativo).
- Nunca omita do template uma imagem, seção ou elemento da referência
  por falta de conteúdo: use recorte da referência ou placeholder com a
  mesma proporção (`project_media()` do esqueleto).
- Nunca grave texto da referência sem acento ou reescrito.
- Nunca ponha `styles` no `theme.json` (reescreve o front-end por cima do
  `style.css`) nem deixe o editor com cor livre/paleta padrão do WordPress.
- Nunca carregue fonte do Google Fonts no navegador do visitante, nem baixe
  peso que a referência não usa: `fetch_fonts.py` hospeda só o necessário,
  com reserva ajustada (`check_theme.py` e a captura apontam).
- Nunca crie admin com senha óbvia (`admin/admin`), nunca desligue a
  proteção básica sem exceção aprovada com motivo, e nunca escreva
  `meta description`/`og:`/canônico à mão no template: o SEO sai de
  `inc/seo.php`, editável por página e calado se houver plugin de SEO
  (`check_security.py`, `check_theme.py` e a captura apontam).
- Nunca escreva conteúdo direto no template: se o administrador não
  consegue alterar pelo painel, está errado (`check_theme.py` bloqueia;
  mensagens de interface vão em `esc_html_e()`).
- Nunca entregue single page com header que não acompanha a rolagem,
  item de menu que não leva a uma seção ou seção que para escondida atrás
  do header (`validate_blueprint.py`, `check_theme.py` e a captura
  bloqueiam).
- Nunca transforme um carrossel da referência em seção estática, nem
  invente rotação onde não há sinal dela; nunca entregue autoplay sem
  botão de pausa ou que ignore `prefers-reduced-motion`. Carrossel usa
  `template-parts/carousel.php` (sem biblioteca de terceiros) com slides
  editáveis no admin.
- Nunca crie formulário à mão nem com destinatário inventado: ele sai de
  `forms[]` via `scripts/build_cf7_form.py` e aparece por `project_form()`
  (nunca shortcode com id fixo); todo formulário tem aviso de
  privacidade. Nunca embuta mapa fixo no template nem carregue o iframe
  sem o clique do visitante (salvo decisão aprovada): use
  `template-parts/map.php` com o endereço da página de opções.
- Nunca embuta player de YouTube/Vimeo nem `<video autoplay>` à mão: vídeo
  usa `template-parts/video.php` (carrega só no clique, sem cookies;
  vídeo de fundo respeita movimento reduzido, tem pausa e não baixa no
  celular). Galeria usa `template-parts/gallery.php` (lightbox com
  `<dialog>` nativo, sem biblioteca) com fotos e textos alternativos
  editáveis na Biblioteca de Mídia.
- Nunca publique depoimento ou logo de cliente da referência como real:
  depoimento só com conteúdo e autorização do cliente, logo só com
  permissão e arquivo da empresa (nunca redesenhado); demo fica oculto em
  produção. Sem JSON-LD Review/AggregateRating autopromocional.
- Nunca publique equipe ou números da referência como reais: pessoas só
  com autorização de imagem, números só confirmados (demo fica oculto em
  produção); registro profissional nunca inventado; bio nunca só no
  hover; contagem animada só decidida, com o valor final no HTML.
- Nunca use foto de hero como `background-image` nem `100vh`: `<img>`
  com `fetchpriority="high"` (é o LCP), imagem/ponto focal do celular,
  altura em `svh`, um `h1` por página, botões com destino real e
  contraste do texto sobre a foto medido na captura (4,5:1; 3:1 grande).
- Nunca faça submenu que abre só no hover: botão com `aria-expanded`
  (padrão disclosure do esqueleto), `:focus-within` sem JS, Esc fecha e
  devolve o foco. Header transparente com links herdando a cor e fundo
  ao rolar; botão de destaque com destino real.
- Nunca invente URL de rede social nem CNPJ, nem deixe ícone de rede com
  link `#`: rede sem URL não aparece. Contato sempre como link (`tel:+55`,
  `wa.me/55`, `mailto:`), copyright com ano dinâmico (`wp_date`), link da
  política de privacidade no rodapé e JSON-LD Organization com `sameAs`.
- Nunca crie CPT para blog: post nativo com `home.php`/`single-post.php`
  do esqueleto; card com um link só, data em `<time>`, JSON-LD
  BlogPosting, compartilhar por links (sem script de terceiro);
  comentários só por decisão do usuário; posts demo ocultos em produção.
- Nunca publique preço da referência como real sem confirmação do usuário,
  nem escreva preço no template: preço é campo número no admin,
  formatado por `project_price()` (`template-parts/pricing.php`); tabela
  de dados usa `template-parts/table.php` (caption, scope, ✓/✗ com texto,
  região rolável no celular).
- Nunca faça acordeão ou abas à mão nem com biblioteca: use
  `template-parts/accordion.php` (`<details>` nativo; FAQ com JSON-LD
  das mesmas perguntas) e `tabs.php` (padrão W3C APG; sem JS todos os
  painéis aparecem), com itens editáveis no admin.
- Nunca deixe item de menu sem destino: link personalizado precisa de URL;
  arquivo de CPT usa item do tipo "arquivo" (URL dinâmica). A captura
  aponta link de menu com `href` vazio ou `#`.
- Nunca declare fidelidade visual sem o portão de QA com
  `Resultado final: passed` — se a captura ou a comparação não puderem
  ser feitas, registre `blocked` e diga o motivo.

## Modos de autonomia

`assisted` / `recommended` (padrão) / `automatic`. A régua operacional do
que é "decisão não crítica" (segue sem perguntar mesmo no modo
recomendado) vs. "decisão arquitetural relevante" (sempre pede aprovação)
está em `references/decision-framework.md` — consulte antes de decidir
sozinho em nome do usuário.

## Quando consultar cada referência

| Referência | Quando ler |
|---|---|
| `references/blueprint-schema.md` | Ao montar, validar ou versionar um Blueprint |
| `references/decision-framework.md` | Ao classificar elementos, ou decidir se algo bloqueia/pergunta |
| `references/content-modeling.md` | Ao decidir CPT vs. estático vs. repeater, nomear campos ACF, taxonomias, relacionamentos |
| `references/wordpress-architecture.md` | Ao estruturar o tema, escolher plugins, nomear arquivos |
| `references/local-environment.md` | Ao fazer scaffold do projeto ou rodar testes no WAMP |
| `references/approval-protocol.md` | Na etapa de aprovação do Blueprint e no versionamento |
| `references/validation-playbook.md` | Nas etapas de teste, validação visual e ciclo de correção |
| `references/navigation.md` | No passo 1 (single page × multipáginas) e ao implementar header, menu e âncoras |
| `references/carousels.md` | No inventário (identificar carrossel/banner rotativo) e ao implementar ou validar um |
| `references/forms.md` | No inventário (ler os campos na imagem) e ao gerar/validar formulários |
| `references/maps.md` | No inventário (identificar mapa) e ao implementar/validar |
| `references/galleries.md` | No inventário (galeria × cards × carrossel) e ao implementar/validar |
| `references/videos.md` | No inventário (identificar vídeo) e ao implementar/validar |
| `references/disclosures.md` | No inventário (acordeão/FAQ/abas × menu/filtro) e ao implementar/validar |
| `references/tables-pricing.md` | No inventário (tabela × layout; preço real × demo) e ao implementar/validar |
| `references/social-proof.md` | No inventário (depoimentos/logos e sua autenticidade) e ao implementar/validar |
| `references/team-stats.md` | No inventário (equipe/números e sua autenticidade) e ao implementar/validar |
| `references/blog.md` | No inventário (blog × grid de CPT) e ao implementar/validar o blog |
| `references/hero-banners.md` | No inventário (tipo de hero, banners) e ao implementar/validar (contraste medido) |
| `references/fonts.md` | No inventário (famílias, pesos, preload), logo após o scaffold (`fetch_fonts.py`) e no QA (fontes, troca, CLS) |
| `references/editor.md` | Ao gerar os tokens (`--theme-json`) e no QA do editor de blocos |
| `references/go-live.md` | Na etapa de publicação (`prelaunch_check.py`, `go_live.py`) |
| `references/performance.md` | No QA (tabela "Desempenho e imagens" da captura) e ao tratar imagens |
| `references/site-icon.md` | No inventário (símbolo do logo) e ao implementar o Ícone do site |
| `references/redirects.md` | Quando o cliente já tem site (análise, Blueprint, antes de publicar) |
| `references/security-seo.md` | Ao montar o Blueprint (`seo`, `security`), no scaffold e no QA (`check_security.py`, seção SEO da captura) |
| `references/header-menu.md` | No inventário (estrutura do header) e ao implementar/validar header, submenus e menu mobile |
| `references/footer-social.md` | No inventário (colunas do rodapé, redes) e ao implementar/validar header/rodapé/contato |
| `references/responsive-guidelines.md` | Quando não há referência mobile explícita |
| `references/accessibility-guidelines.md` | Na validação de acessibilidade |

## Quando executar cada script

| Script | Quando rodar |
|---|---|
| `scripts/validate_blueprint.py` | Depois de montar/editar o Blueprint, antes da etapa de aprovação |
| `scripts/render_approval_page.py` | Junto com o resumo, na aprovação do Blueprint: `documentation/APROVACAO.html` (cores, fontes, botões, seções × recortes da referência, menu no celular) |
| `scripts/render_blueprint_summary.py` | Para gerar o resumo de aprovação (decisions + uncertainties) |
| `scripts/scaffold_wp_project.py` | No início da implementação, para criar o projeto no WAMP |
| `scripts/fetch_fonts.py` | Logo após o scaffold, antes de `generate_design_tokens.py` (e de novo se `fonts` mudar) |
| `scripts/generate_design_tokens.py` | Logo após o scaffold, e de novo a cada ajuste de token no ciclo de correção |
| `scripts/crop_reference.py` | Para gerar assets provisórios `crop_from_reference` (informa o `aspect_ratio`) |
| `scripts/build_cf7_form.py` | Depois do scaffold, para cada `forms[]` (`--print` para revisar, `--project` para gravar) |
| `scripts/seed_demo_content.py` | Depois de CPTs/campos/taxonomias existirem; rode antes com `--blueprint --check-only` |
| `scripts/check_theme.py` | Ao fim da fatia crítica e antes de declarar a implementação pronta para validação visual |
| `scripts/capture_site.py` | A cada rodada do portão de QA (fatia crítica e site completo); saída em `documentation/qa/rodada-N/` |
| `scripts/make_site_icon.py` | Depois do scaffold, com o símbolo do logo (`--box`/`--keep-color` para recortar da referência; `--project` define no WordPress) |
| `scripts/build_redirects.py` | Site antigo: `--suggest` na análise, `--write` na implementação, `--check` antes de publicar |
| `scripts/prelaunch_check.py` | Antes de publicar (`--stage local`) e no endereço final (`--stage production`) |
| `scripts/go_live.py` | Com o domínio confirmado e o prelaunch sem P0/P1: monta o pacote de publicação |
| `scripts/check_security.py` | Depois do scaffold e antes da entrega (`--out documentation/qa/seguranca.json`) |
| `scripts/checkpoint.py` | Nos marcos: scaffold, pre-seed, fatia crítica, fim de cada rodada de QA |

## Formato de saída

Projeto final segue a estrutura de `references/wordpress-architecture.md`.
Sempre entregar, dentro do projeto:

```
documentation/
├── README.md
├── BLUEPRINT.yaml        (+ versões anteriores se houve revisão)
├── DECISIONS.md
└── VALIDATION.md
```

Nunca considere a primeira geração definitiva — comunique ao usuário que o
ciclo normal é gerar, testar, comparar e corrigir.
