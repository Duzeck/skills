# Protocolo de aprovação do Blueprint

## O que mostrar

Nunca cole o YAML completo do Blueprint no chat como forma de pedir
aprovação — é longo demais para ser revisado de verdade e aumenta a chance
de o usuário aprovar sem ler. Em vez disso, use
`scripts/render_blueprint_summary.py` para gerar um resumo em Markdown
contendo apenas:

1. Objetivo e páginas do projeto (2-3 linhas).
2. Tabela de `decisions` com status `pending_user_approval`: assunto,
   decisão, razão, confiança.
3. Tabela de `uncertainties` com status `pending`: assunto, pergunta,
   opções (se houver), se é bloqueante.
4. Lista de plugins propostos e por quê.
5. Lista de dependências do ambiente que serão necessárias.

Se não houver nenhuma decisão pendente nem incerteza, diga isso
explicitamente — não gere uma tabela vazia sem contexto.

### Página visual (o cliente aprova vendo, não lendo)

Junto com o resumo, gere a página visual com
`scripts/render_approval_page.py BLUEPRINT.yaml --out documentation/APROVACAO.html`.
É um arquivo único (abre com dois cliques e pode ser enviado ao cliente).
Ele mostra:
- **os pontos para confirmar**, numerados;
- as **cores** como amostras (com o contraste sobre o fundo);
- as **fontes** renderizadas com os arquivos reais, em cada peso, e a escala de tamanhos;
- os **botões** com os rótulos do hero;
- **cada seção ao lado do recorte da referência** (`reference_map.box`), com o tipo e onde editar;
- o **menu no celular** desenhado nas três opções, com a proposta marcada;
- o resumo completo no fim.

Tudo sai do Blueprint, sem layout paralelo. Não é um protótipo: não se
constrói nada duas vezes. Diga ao usuário onde está o arquivo e peça a
resposta pelo número do item.

### Aprovação visual na fatia crítica

Ao fechar a fatia crítica (header + hero da Home sem P0/P1), rode a
captura com `--ref`. Ela gera `aprovacao-visual.html` na pasta da rodada,
com a referência à esquerda e o site **já no WordPress** à direita, no
desktop e no celular. Mostre ao usuário e **espere a aprovação antes de
propagar** o sistema para as outras seções e páginas. Um ajuste de
fonte, escala ou espaçamento aqui custa uma correção; depois, custa uma
por página. Isso substitui o protótipo em HTML: o cliente vê o código
definitivo.

## O que conta como aprovação

- Aprovação geral: o usuário responde afirmativamente ao resumo completo
  (ex.: "aprovado", "pode seguir", "sim, para todos").
- Aprovação parcial: o usuário responde a decisões/incertezas específicas
  individualmente. Nesse caso, atualize o status de cada item
  individualmente no Blueprint — não marque como aprovado o que não foi
  respondido.
- Se alguma incerteza bloqueante continuar sem resposta, não inicie a
  implementação da parte afetada por ela, mesmo que o restante tenha sido
  aprovado. Diga explicitamente o que está sendo adiado e por quê.

## Exceção: prototipagem explícita

Se o usuário pedir explicitamente um protótipo antes de aprovar a
arquitetura completa (ex.: "me mostra como ficaria a Home antes de
decidirmos o resto"), é permitido pular a aprovação formal para essa parte
— mas deixe claro que é um protótipo descartável/sujeito a mudança, não a
implementação final, e ainda assim registre o Blueprint parcial usado.

## Versionamento após aprovação

Depois de aprovado, qualquer mudança que seção `implementation` classifica
como estrutural (ver `references/blueprint-schema.md` → regras de
implementação) exige:

1. Propor a mudança explicitamente, com a razão.
2. Gerar uma nova versão do arquivo (`blueprint-v0.N.yaml`) em
   `documentation/blueprint-history/`.
3. Pedir aprovação novamente, apenas para o que mudou (não repita a
   aprovação do que já estava certo).
4. Atualizar `documentation/BLUEPRINT.yaml` para apontar para a versão
   mais recente.

Mudança puramente visual (cor, espaçamento, texto estático) não exige nova
versão do Blueprint nem nova aprovação — corrija e registre em
`DECISIONS.md` como ajuste.
