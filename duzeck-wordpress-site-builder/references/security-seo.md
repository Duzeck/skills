# Segurança básica e SEO de cada página

Todo site entregue sai com **proteção básica ligada** e **SEO editável por
página**. Nada disso aparece na referência visual: é decisão de engenharia,
registrada no Blueprint (`security`, `seo`) e conferida no QA.

## 1. Segurança básica (`security`)

### O que é feito, e onde

| Proteção | Onde | Por quê |
|---|---|---|
| Senha forte aleatória para o admin (nunca `admin/admin`) | scaffold | É a primeira tentativa de qualquer robô, e o banco local costuma ir para a produção |
| `DISALLOW_FILE_EDIT` | wp-config (scaffold) + mu-plugin | Quem rouba uma conta de admin não consegue gravar PHP pelo painel |
| XML-RPC desligado (403 antes de autenticar) | mu-plugin + `.htaccess` | `system.multicall` testa centenas de senhas por requisição; pingback é usado em ataques |
| Login não vaza: `?author=1` vira 404, `/author/<login>/` fechado, `/wp-json/wp/v2/users` só logado, sem autor no oEmbed nem usuários no sitemap | mu-plugin | Saber o login é metade da força bruta |
| Erro de login genérico ("usuário ou senha incorretos") | mu-plugin | "Usuário não registrado" × "senha incorreta" confirma quais logins existem |
| Versão do WordPress fora do HTML e do feed; `readme.html`/`license.txt` apagados e negados | mu-plugin + scaffold + `.htaccess` | Ferramentas de ataque começam pela versão para escolher a falha |
| Listagem de pastas desligada (`Options -Indexes`) | `.htaccess` | `wp-content/uploads/` e `wp-includes/` não têm `index.php`: o Apache listaria tudo |
| Cabeçalhos: `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `X-Frame-Options` + `frame-ancestors 'self'` | mu-plugin | Bloqueiam clickjacking, troca de tipo de arquivo e vazamento de URL |
| HSTS | mu-plugin, **só** em produção com HTTPS | Em localhost "prenderia" o navegador em https por um ano |

**Por que um mu-plugin** (`assets/mu-plugins/project-hardening.php`): a
proteção é do site, não do visual. Ela continua valendo se alguém trocar o
tema, e não pode ser desativada pelo painel.

O que **não** está aqui de propósito:
- **CSP completo**: quebraria os scripts inline (aviso, trilha, JSON-LD), os mapas, o YouTube e o CF7;
- **limite de tentativas de login e 2FA**: são de plugin ou servidor, então ficam na lista da produção;
- **remover `?ver=`**: quebraria a atualização do cache dos arquivos.

### Exceções (`security.exceptions`)

São raras e exigem **motivo**. O scaffold grava cada uma como constante
(`--security-exception <regra>`), e o mu-plugin e o `.htaccess` respeitam.

| `rule` | Quando |
|---|---|
| `xmlrpc` | App ou serviço que exige XML-RPC (Jetpack, app antigo de publicação) |
| `author_archives` | Blog com página por autor visível na referência |
| `rest_users` | Integração que lê usuários sem login |
| `frame_embedding` | O site é exibido dentro de outro domínio |

O tema nunca linka a página do autor (o `check_theme.py` avisa). O nome do
autor aparece sem link.

## 2. SEO de cada página (`seo`)

### O que o administrador edita

A caixa **"SEO e compartilhamento"** aparece em páginas, posts e CPTs
públicos (`inc/seo.php`):

| Campo | Vazio = |
|---|---|
| Título na busca (até 60) | título da página + nome do site |
| Descrição na busca (120–160) | descrição aprovada no Blueprint (`content-defaults`), resumo, texto do topo, slogan |
| Imagem ao compartilhar (1200×630) | imagem destacada → imagem do topo → imagem padrão (Configurações do Site) |
| Esconder dos buscadores | — (a página sai também do sitemap) |

Recorte `project-share` de 1200×630, que é a prévia do WhatsApp, do
Facebook e do LinkedIn.

### O que sai no `<head>`

- `meta description`;
- Open Graph: `og:title`, `og:description`, `og:url`, `og:image` com largura, altura e alt, `og:type` (`article` em posts) e `og:locale`;
- `twitter:card`;
- canônico das listagens (o core já imprime o de páginas e posts);
- `noindex` da página marcada e de toda a **homologação** (`WP_ENVIRONMENT_TYPE=staging`);
- JSON-LD da Home (`inc/social.php`), no formato `@graph`:
  - **empresa**, com o tipo vindo de `PROJECT_SCHEMA_TYPE`;
  - `sameAs` (redes preenchidas), telefone, e-mail e CNPJ;
  - **endereço**, quando o tipo é LocalBusiness ou um subtipo dele;
  - **WebSite**, que dá o nome do site no Google.

**Plugin de SEO ativo** (Yoast, Rank Math, SEOPress, AIOSEO, The SEO
Framework): o tema se cala inteiro, incluindo a caixa do admin e os JSON-LD
da empresa e do post. Duas descrições ou dois `og:title` confundem o Google
e as redes.

### O que decidir no Blueprint

| Campo | Decida |
|---|---|
| `plugin` | `none` (padrão: o tema resolve) ou o plugin que o cliente já usa |
| `organization_type` | `Organization` (sem atendimento no local) ou **LocalBusiness/subtipo**. Exemplos de subtipo: `GeneralContractor` (construtora), `BeautySalon`, `Dentist`, `Restaurant`, `LegalService`, `AccountingService`. Esse tipo exige o endereço em `global_settings.company.address` |
| `pages[].description` | **Proposta** pela skill para cada página: 50 a 160 caracteres, única, com o serviço e a cidade, sem promessa que o cliente não confirmou. `description_source: proposed` entra na aprovação |
| `pages[].noindex` | Páginas de "obrigado", testes, conteúdo duplicado |
| `share_image` | `media[].id` da imagem padrão de compartilhamento |

O FAQ continua gerando FAQPage (`references/disclosures.md`), mas sem
prometer resultado rico: o Google só mostra esse resultado para sites de
governo e saúde.

## 2b. Robôs de inteligência artificial (`seo.ai_crawlers`)

Decisão de **negócio**: pergunte ao usuário na aprovação.

| Política | Treino de IA (GPTBot, ClaudeBot, Google-Extended, CCBot...) | Busca/resposta com IA (OAI-SearchBot, ChatGPT-User, Claude-SearchBot, PerplexityBot...) | Para quem |
|---|---|---|---|
| `allow` | liberado | liberado | Quer máxima exposição |
| **`block_training`** | bloqueado | liberado: o site continua **citado** nas respostas | Não quer o conteúdo treinando modelos, mas quer clientes vindos do ChatGPT/Perplexity |
| `block_all` | bloqueado | bloqueado: o site some das respostas de IA | Conteúdo exclusivo, pago |

- Nenhuma política afeta o Google ou o Bing comuns. `Google-Extended` só controla o uso pelo Gemini; o AI Overviews usa o Googlebot.
- O robots.txt é virtual: o WordPress gera e o tema acrescenta as regras (`inc/seo.php`). O valor inicial vem do scaffold (`--ai-crawlers`), e o administrador muda em **Configurações do Site › SEO e compartilhamento**.
- Um `robots.txt` **físico** na raiz anula tudo isso (o `check_security.py` avisa).
- **Instalação em subpasta** (`localhost/<slug>/`): o WordPress não responde `/robots.txt`, porque ele só vale na raiz do domínio. A captura lê o mesmo conteúdo por `?robots=1` e anota isso como P2.
- "Evitar mecanismos de busca" (Leitura) não mexe no robots.txt desde o WP 5.3: vira `noindex` nas páginas, e a seção SEO da captura aponta.
- As listas de robôs estão em `project_ai_bots()` (tema) e `AI_TRAINING_BOTS`/`AI_SEARCH_BOTS` (`capture_site.py`). Mantenha as duas iguais e revise quando surgir robô novo.
- `llms.txt` não é feito: não é padrão adotado pelos buscadores.

## 3. Como validar

- **`scripts/check_security.py --url <home> --path <pasta>`**: testa de fora, como um ataque faria, e por dentro, via WP-CLI.
  - **P1**: XML-RPC respondendo; login vazando (`?author=1`, `/author/<login>/`, REST users); erro de login diferente para usuário inexistente; listagem de pastas; editor de arquivos liberado; **senha de admin óbvia**; mu-plugin ausente.
  - **P2**: versão no HTML ou no feed; `readme.html` acessível; cabeçalhos ausentes; login `admin`.
- **`scripts/capture_site.py --blueprint`**: a seção **robots.txt** confere o site liberado para buscadores, a linha Sitemap e os robôs de IA conforme `seo.ai_crawlers` (P1 se divergir); a seção **SEO** do relatório.
  - **P1**: título ausente; descrição ausente, duplicada ou diferente da aprovada; canônico ausente ou errado; `og:*` ausente ou duplicado; `og:image` que não abre; `noindex` indevido; JSON-LD inválido ou com campo vazio; empresa ausente na Home, de outro tipo ou sem endereço.
  - **P2**: tamanho do título e da descrição; imagem menor que 1200×630.
- **`scripts/check_theme.py`**: avisa sobre `meta description`, `og:` ou canônico escritos à mão no template, e sobre links para a página do autor.

Antes da produção, fora do escopo do tema:
- HTTPS com redirecionamento;
- limite de tentativas de login (plugin ou servidor);
- 2FA para os administradores;
- backups;
- cada pessoa com o próprio usuário, sem login `admin`;
- apagar a conta criada pelo scaffold.
