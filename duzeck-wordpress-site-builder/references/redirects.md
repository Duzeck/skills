# Redirecionamentos do site antigo

Quando o cliente **já tem um site**, os endereços antigos estão no Google,
em links compartilhados e em material impresso. Sem redirecionamento, todos
viram "página não encontrada" no dia da troca, e o site perde a posição na
busca.

## 1. Blueprint

```yaml
redirects:
  old_site: https://www.site-antigo.com.br   # null quando não há site antigo
  map:
    - { from: /quem-somos.html, to: about }    # id de pages[], caminho "/..." ou URL
```

Pergunte na análise: "a empresa já tem site? qual o endereço?".

## 2. Montar o mapa: `scripts/build_redirects.py`

```bash
python scripts/build_redirects.py --blueprint BLUEPRINT.yaml --suggest --old-sitemap https://site-antigo.com.br/sitemap.xml
```

Lê o sitemap antigo (segue o índice de sitemaps) e propõe o destino de cada
endereço:
- **mesmo assunto**, por um dicionário de nomes institucionais em português: "quem somos/empresa/institucional" → sobre; "fale conosco/atendimento" → contato; "obras/portfólio" → projetos; "notícias" → blog...;
- semelhança de letras para o resto;
- **assunto sem página equivalente** (ex.: "trabalhe conosco") sai como `CONFIRMAR`, nunca com um destino inventado;
- endereços que continuam iguais no site novo não entram.

Teste: 5 de 5 destinos certos; "trabalhe conosco" ficou para confirmar.
Confirme com o usuário e cole no Blueprint.

## 3. Implementar

- `build_redirects.py --write --path <wordpress>` grava `wp-content/project-redirects.json`.
- O mu-plugin **`project-redirects.php`** (copiado pelo scaffold):
  - redireciona com **301**, e só quando o endereço daria 404. Uma página nova no mesmo caminho sempre vence;
  - normaliza `/Servicos.php`, `/servicos.html`, `/servicos/index.html` → `/servicos`;
  - entende a instalação em subpasta;
  - não aceita destino externo fora de `allowed_redirect_hosts`;
  - não entra em loop: só é loop quando o destino é **idêntico** ao pedido. `/servicos.php` → `/servicos/` é legítimo; no teste, essa comparação estava errada e foi corrigida.
- **Editável no painel**: Configurações do Site › Redirecionamentos, um por linha (`/antigo/ /novo/`), para o cliente acrescentar depois.

## 4. Conferir

```bash
python scripts/build_redirects.py --blueprint BLUEPRINT.yaml --check --url <site novo> --old-sitemap <sitemap antigo>
```

Cada endereço do mapa deve responder 301 para o destino certo, e o destino
deve abrir (200). Com o sitemap antigo, aponta também endereços **sem
destino** que dão 404 (P1). O `prelaunch_check.py` cobra o arquivo gravado
quando o Blueprint tem mapa.

Limite: endereços antigos por parâmetro (`?page_id=5`) não são 404 no
WordPress e não passam por aqui. Se o site antigo usava esse formato, liste
os casos e trate um a um.
