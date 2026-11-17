# Publicação na produção

Sem uma etapa de publicação, o fim do projeto fica ao acaso: os avisos de
"antes de publicar" ficam espalhados em vários guias, a troca de
`localhost` pelo domínio é feita à mão e o banco local vira o de produção
com senha fraca e e-mail de teste. Esta etapa fecha isso com dois scripts.

## 1. Lista única: `scripts/prelaunch_check.py`

```bash
python scripts/prelaunch_check.py --path <wordpress> --blueprint BLUEPRINT.yaml [--stage local|production] --out documentation/qa/pre-publicacao.md
```

Confere no WordPress (WP-CLI) e no Blueprint:

| Nível | O que aponta |
|---|---|
| **P0** | site escondido dos buscadores; em produção: ambiente diferente de `production`, `http://localhost` no banco (inclusive a forma escapada dos blocos), mu-plugin de e-mail local no servidor, erros do PHP na tela |
| **P1** | sem SMTP; destino de formulário ou e-mail do admin falso (`@localhost.test`, `example.com`); usuário `admin`; senha óbvia; editor de arquivos liberado; Política de Privacidade não publicada; links permanentes fora de `/%postname%/`; sem Ícone do site; posts de exemplo publicados; conteúdo `demo` (depoimentos, equipe, números) e preços não confirmados; imagens provisórias (`replace_before_launch`); pendências e decisões não aprovadas; redirecionamentos no Blueprint sem o arquivo gravado; `launch.domain` vazio; sem HTTPS (em produção) |
| **P2** | URLs de redes vazias; política de robôs de IA no padrão; atualizações pendentes |

`--stage local` (no WAMP) diz o que falta para publicar. `--stage
production` roda no servidor ou numa cópia de produção.

## 2. Pacote: `scripts/go_live.py`

```bash
python scripts/go_live.py --path <wordpress> --domain https://www.empresa.com.br --out <pasta fora do WAMP>
```

**Não altera o site local**: só lê e exporta. Gera:
- `backup-local-<data>.sql`: o banco local intacto (testado: restaurar volta o site).
- `banco-producao.sql`: o mesmo banco com o endereço local trocado pelo domínio, via `wp search-replace --regex --export`, numa passada só:
  - pega `http://localhost/<slug>` **e** a forma escapada `http:\/\/localhost\/<slug>` que o editor de blocos grava;
  - recalcula o tamanho dos dados serializados (opções, campos ACF, widgets). Uma troca de texto simples os corromperia. Testado: `s:42`/`s:60` recalculados, a opção abre íntegra depois da importação;
  - não pega `…/slug2` nem `…/slug.old`, mas aceita o ponto final de frase (o texto padrão da privacidade termina assim).
- `wp-content.zip`: tema, mu-plugins (**sem** `project-local-mail.php`: em produção é SMTP), uploads e `project-redirects.json`.
- `.htaccess` da **raiz**: bloco de proteção + WordPress com `RewriteBase /`.
- `favicon.ico`: do Ícone do site (16/32/48 px). Alguns servidores nginx respondem `/favicon.ico` sem passar pelo WordPress, então o arquivo físico na raiz é obrigatório.
- `wp-config-producao.txt`: `WP_ENVIRONMENT_TYPE=production`, `DISALLOW_FILE_EDIT`, debug desligado, exceções de segurança aprovadas e **chaves novas** (geradas localmente).
- `LEIA-ME-PUBLICACAO.md`: passo a passo na hospedagem (banco, importação, arquivos, plugins a instalar, SMTP, HTTPS, links permanentes) e o que conferir depois.

Os dumps têm hashes de senha: entregue o pacote por canal privado e apague
as cópias temporárias.

## 3. Ordem

1. Fim do QA (sem P0/P1 na captura) → `prelaunch_check.py --stage local`, até zerar P0/P1.
2. Perguntar o domínio (`launch.domain`) → `go_live.py`.
3. Na hospedagem: seguir o LEIA-ME.
4. No endereço final: `prelaunch_check.py --stage production`, `check_security.py --url <domínio>`, a captura com `--base <domínio>`, um envio real de formulário e o Search Console com o sitemap.

Fora do escopo (combinar com o cliente): limite de tentativas de login,
2FA, backups automáticos, CDN.
