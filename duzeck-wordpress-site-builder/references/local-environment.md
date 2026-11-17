# Ambiente local (WAMP)

## Convenções

- Raiz de projetos: `C:\wamp64\www\<slug>`.
- URL local: `http://localhost/<slug>/`.
- Banco de dados: MySQL do WAMP, um banco por projeto, nome = `<slug>`
  (trocar `-` por `_` se o MySQL reclamar de hífen).
- `<slug>` deve ser kebab-case curto derivado do nome do projeto (ex.:
  "Construtora Horizonte" → `construtora-horizonte`).

## Pré-requisitos (validar antes de tudo)

Antes de iniciar a etapa `environment_validation` do Blueprint, confirme:

1. WAMP está rodando (Apache e MySQL ativos).
2. `wp` (WP-CLI) está disponível no PATH. Se não estiver, pare e informe o
   usuário em vez de tentar instalar WordPress manualmente arquivo por
   arquivo — isso é lento e propenso a erro.
3. `php -v` responde com uma versão compatível (8.1+ recomendado).
4. Para o portão de QA: Node.js + Playwright e axe-core **globais**
   (`npm i -g playwright axe-core && playwright install chromium` — já
   instalados neste ambiente em 2026-11-11). Sem eles, `capture_site.py`
   sai com código 2 e o portão fica `blocked`.
5. `git` no PATH, para os pontos de restauração (`checkpoint.py`).

Observações deste ambiente Windows:
- O `wp` é `C:\Users\duzec\bin\wp.bat`. O `which` do Git Bash não acha
  `.bat`, mas os scripts Python o resolvem via `shutil.which`. No terminal,
  prefira PowerShell para chamar `wp` diretamente.
- No Git Bash, argumentos começando com `/` são convertidos em caminho
  do Windows (`/` → `C:/Program Files/Git/`). Passe slugs sem barra
  inicial aos scripts ou prefixe com `MSYS_NO_PATHCONV=1`.
- **WP-CLI com o PHP do Apache.** O `wp.bat` chama o `php` do PATH
  (8.2.18 aqui), mas o Apache do WAMP roda 8.3.6. Quando um plugin exige
  PHP mais novo (Contact Form 7 6.2+ exige 8.3), o WP-CLI derruba com
  "Há um erro crítico no seu site" **embora o site funcione no navegador**.
  Não é defeito do site. Os scripts da skill resolvem sozinhos
  (`scripts/_wpcli.py` lê o `LoadModule php_module` do `httpd.conf`); para
  comandos manuais no PowerShell:
  `& 'C:\wamp64\bin\php\php8.3.6\php.exe' 'C:\Users\duzec\bin\wp-cli.phar' <comando>`
  — e coloque entre aspas argumentos com vírgula (`'--fields=ID,post_title'`),
  senão o PowerShell os divide. `wp eval` com código inline quebra nas aspas
  do `.bat`: prefira `wp eval-file arquivo.php`.

Se qualquer pré-requisito falhar, registre como `dependency` não resolvida
no Blueprint e bloqueie a geração — não deixe o projeto pela metade.

### Gotchas conhecidos do PHP CLI do WAMP

Descobertos na primeira execução real desta Skill (caso Construtora
Horizonte) — verifique antes de assumir que o ambiente está pronto:

- **`curl.cainfo`/`openssl.cafile` vazios no `php.ini`** fazem qualquer
  chamada HTTPS do PHP (inclusive `wp core download` e instalação de
  plugins) falhar com "SSL certificate problem: unable to get local
  issuer certificate", mesmo com a rede funcionando normalmente. Baixe um
  bundle de CAs (ex.: `https://curl.se/ca/cacert.pem`) e aponte as duas
  diretivas no `php.ini` usado pelo CLI (`php --ini` mostra qual arquivo).
- **`memory_limit` padrão (128M) é baixo demais** para extrair o pacote do
  WordPress core via `PharData` no Windows — aumente para `512M` no mesmo
  `php.ini`.
- Em geral, no Windows, `subprocess`/`CreateProcess` sem `shell=True` só
  resolve automaticamente a extensão `.exe` para um comando sem extensão
  — nunca `.bat`/`.cmd`. Qualquer script desta Skill que chama `wp`
  resolve o caminho primeiro via `shutil.which()` por causa disso.

## Scaffolding (via `scripts/scaffold_wp_project.py`)

O script automatiza, nesta ordem:

1. Criar a pasta `C:\wamp64\www\<slug>` (falhar se já existir e não
   estiver vazia, para não sobrescrever trabalho existente). **Exceção:**
   pasta que só contém material de referência (subpastas com imagens/PDF/
   MD/YAML, ex.: `template/` com os PNGs do layout, ou `documentation/`)
   é aceita e mantida — é comum o usuário criar a pasta e colocar as
   referências antes. Copie as referências para `documentation/referencias/`.
   Depois do `core install`, o script instala o idioma (`--locale`, padrão
   `pt_BR`), o fuso `America/Sao_Paulo` e o formato de data brasileiro
   (`j \d\e F \d\e Y`, hora `H:i` — o core instala em inglês e manteria
   "novembro 1, 2026"), e apaga o conteúdo de exemplo ("Olá, mundo!",
   "Página de exemplo", comentário padrão) e renomeia a página de
   privacidade do núcleo para "Política de Privacidade"
   (`/politica-de-privacidade/`, rascunho até o cliente revisar); rode também
   `wp language plugin install contact-form-7 pt_BR` **antes** de criar o
   formulário, senão as mensagens dele ficam gravadas em inglês.
2. Baixar e extrair o WordPress core via Python (`urllib` + `zipfile`),
   não via `wp core download`. O extrator do WP-CLI (PharData/tar) cria um
   diretório temporário com nome muito longo antes de mover os arquivos
   para o destino, e isso estoura o limite de caminho do Windows (MAX_PATH)
   por causa de arquivos profundamente aninhados no core do WordPress.
   Extrair direto para o destino final evita o problema.
3. Criar o banco de dados no MySQL do WAMP.
4. `wp config create` com as credenciais padrão do WAMP (`root`, senha
   vazia, host `localhost`).
5. `wp core install` com `--url=http://localhost/<slug>` e dados do
   projeto (nome do site, admin local). A senha do admin é **gerada
   aleatoriamente** e mostrada uma única vez no fim do scaffold (passe
   `--admin-password` só se o usuário pedir uma). Nunca `admin/admin`: o
   banco local costuma virar o da produção.
6. Copiar `assets/theme-skeleton/` para
   `wp-content/themes/<slug>-theme/`, renomeando o que for necessário.
7. `wp theme activate <slug>-theme`
8. `wp plugin install advanced-custom-fields-pro --activate` (se você
   tiver o `.zip` da licença local, use `wp plugin install <caminho-zip>
   --activate` em vez do repositório público, já que ACF PRO não está no
   WordPress.org).
9. `wp plugin install contact-form-7 --activate` + tradução do CF7
   (quando o Blueprint incluir formulário), `WP_ENVIRONMENT_TYPE=local`
   no `wp-config.php` e o mu-plugin `assets/mu-plugins/project-local-mail.php`
   em `wp-content/mu-plugins/`. O PHP do WAMP não envia e-mail: com o
   mu-plugin, cada `wp_mail()` vira um JSON em `wp-content/local-mail/`
   (bloqueado ao navegador) e o QA confere o envio
   (`capture_site.py --submit-forms --mail-log`). Projeto antigo sem isso:
   `wp config set WP_ENVIRONMENT_TYPE local --type=constant` + copiar o
   mu-plugin.
10. `wp rewrite structure '/%postname%/'` e `wp rewrite flush`. **Isso
    normalmente NAO gera o `.htaccess`** porque `wp rewrite flush` (mesmo
    com `--hard`) roda em contexto CLI, sem `SERVER_SOFTWARE` definido, e
    o WordPress pula a escrita do arquivo. Depois do flush, verifique se
    `.htaccess` existe na raiz do projeto (ex.: `curl` em uma URL que nao
    seja a home - se der 404, e isso); se nao existir, crie manualmente
    com o bloco padrao do WordPress (`RewriteEngine On` + `RewriteRule`
    para `index.php`, com `RewriteBase /<slug>/`).
11. Proteção básica (`references/security-seo.md`): `DISALLOW_FILE_EDIT`
    no `wp-config.php`, `readme.html`/`license.txt`/`wp-config-sample.php`
    apagados, mu-plugin `project-hardening.php` e, no `.htaccess`, o bloco
    "Project hardening" **antes** do bloco do WordPress (`Options -Indexes`
    e arquivos sensíveis negados). Exceções aprovadas viram constantes
    `PROJECT_ALLOW_*` (`--security-exception`). Confira com
    `scripts/check_security.py --url <home> --path <pasta>`.

## Testes funcionais via WP-CLI

Depois do scaffolding e da implementação, valide com comandos como:

- `wp post-type list` — confirma que os CPTs do Blueprint existem.
- `wp taxonomy list` — confirma taxonomias.
- `wp post create` de teste para cada CPT — confirma que salva sem erro
  PHP.
- `wp menu list` / `wp menu item list` — confirma menus.
- `wp theme status` — confirma tema ativo sem erros fatais.

## Validação visual

**Captura em lote — `scripts/capture_site.py` (padrão).** Uma chamada
captura todas as páginas do Blueprint em 1440/834/390, de forma
determinística (animações congeladas, lazy-load disparado, escala 1:1), e
já entrega erros de console/JS, HTTP ≥ 400, imagens quebradas, rolagem
horizontal com os elementos culpados, axe WCAG 2 A/AA e links internos
quebrados. Com `--ref`, monta `compare-*.png` com referência e
implementação lado a lado — abra-os com Read para a comparação.

```
python scripts/capture_site.py --base http://localhost/<slug>/ \
    --blueprint C:\wamp64\www\<slug>\documentation\BLUEPRINT.yaml \
    --out C:\wamp64\www\<slug>\documentation\qa\rodada-1 \
    --ref home=<referencia-home-desktop.png>
```

**Inspeção interativa — `claude-in-chrome`.** Para o que a captura
estática não cobre: estados de hover/foco, menu mobile aberto, envio de
formulário, filtros, modais. Ao registrar a evidência, iguale viewport e
estado com a referência.

**Pontos de restauração — `scripts/checkpoint.py`.** Commit git de tema +
`documentation/` + dump do banco (`db/database.sql`) a cada marco. Para
desfazer uma rodada ruim, o script imprime os comandos de restauração —
que são destrutivos e só rodam com confirmação do usuário.

## O que nunca fazer neste ambiente

- Nunca instalar WordPress "manualmente" copiando arquivos um a um quando
  `wp core download`/`wp core install` está disponível — é mais lento e
  mais sujeito a erro de configuração.
- Nunca reportar "ambiente validado" sem ter de fato acessado a URL local
  e confirmado resposta HTTP 200 (ou visualmente via browser).
- Nunca sobrescrever uma pasta de projeto existente sem confirmar com o
  usuário — pode ser trabalho em andamento.
