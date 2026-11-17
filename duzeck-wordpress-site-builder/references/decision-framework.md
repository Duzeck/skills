# Framework de classificação e autonomia

## Classificação de conteúdo

### A — Global
Aparece em várias páginas, tem uma única fonte de verdade.
Exemplos: logo, telefone, WhatsApp, endereço, redes sociais, menu, footer.

### B — Static
Conteúdo institucional único de uma página específica, sem repetição
estrutural. Exemplos: texto da seção "Sobre", missão/visão, história da
empresa.

### C — Dynamic
Conteúdo repetitivo e administrável, candidato natural a CPT.
Exemplos: serviços, produtos, projetos, depoimentos, equipe, notícias,
portfolio, imóveis, eventos.

### D — Configurable
Valor que muda ocasionalmente mas não é "conteúdo" no sentido editorial.
Exemplos: telefone, WhatsApp, endereço, CTA padrão, links sociais, textos
globais curtos.

Um mesmo dado pode ser Global e Configurable ao mesmo tempo (ex.: telefone
é global porque aparece em vários lugares, e configurable porque é um
valor editável, não um post).

## Regra de ouro para decidir se algo vira CPT

Pergunte, nesta ordem:

1. **Existem 3 ou mais instâncias visualmente repetidas** do mesmo tipo de
   bloco (cards, itens de lista, linhas de tabela)?
2. Essas instâncias têm **campos próprios e estruturados** (imagem,
   título, descrição, data, categoria) em vez de texto livre único?
3. É plausível que o **administrador** (não o desenvolvedor) precise
   adicionar/editar/remover instâncias no futuro?

Se as três respostas forem "sim" → proponha CPT + campos (+ taxonomia se
houver agrupamento/filtro visível). Se a resposta 3 for incerta → não
decida sozinho, registre como `uncertainty` e pergunte (ex.: "Os cards de
X deverão ser editáveis pelo administrador?"). Se a resposta 1 ou 2 for
"não" → trate como conteúdo estático, não force um CPT.

**Não crie CPT para quantidade fixa e pequena de itens que nunca muda**
(ex.: 3 valores institucionais fixos "Qualidade, Compromisso, Inovação")
— isso é conteúdo estático, mesmo que visualmente pareça um grid de cards.

## Taxonomia: quando criar

Só crie taxonomia quando o layout mostrar evidência real de filtragem,
agrupamento ou navegação por categoria (ex.: botões de filtro acima de um
grid, badges de categoria nos cards, menu com submenu por categoria). Não
crie taxonomia "por via das dúvidas".

## Régua de autonomia por modo

| Tipo de decisão | assisted | recommended (padrão) | automatic |
|---|---|---|---|
| Criar/não criar CPT | pergunta sempre | pergunta se impacto incerto (regra acima), senão segue | segue com decisão registrada |
| Criar taxonomia | pergunta sempre | pergunta se evidência visual ambígua | segue com decisão registrada |
| Nome/slug de campos, componentes, templates | pergunta sempre | decide sozinho | decide sozinho |
| Escolha de plugin fora da shortlist padrão | pergunta sempre | pergunta sempre | pergunta sempre |
| Página individual por item de CPT (single template) | pergunta sempre | pergunta se não houver indício visual (link/hover de card) | segue com decisão registrada |
| Comportamento de interação não visível no layout (ex.: filtro AJAX vs. reload) | pergunta sempre | pergunta sempre, e bloqueia se crítico | pergunta sempre, e bloqueia se crítico |
| Cor/espaçamento/tipografia **visíveis na referência** | medir e reproduzir — nunca substituir por "boa prática" | idem | idem |
| Cor/espaçamento/tipografia **não visíveis** (ex.: estado de hover, breakpoint sem referência) | segue derivando do sistema da referência, com nota de baixa confiança | idem | idem |
| Simplificar composição, omitir elemento ou reescrever texto da referência | nunca — só como desvio intencional aprovado pelo usuário | idem | idem |
| Conteúdo demo (texto/imagens placeholder) | pergunta se definitivo não foi dado | segue com conteúdo demo identificado | segue com conteúdo demo identificado |
| Dado global ausente (telefone, endereço, e-mail) | pergunta sempre | pergunta sempre, e bloqueia se usado em formulário/CTA | pergunta sempre, e bloqueia se usado em formulário/CTA |

Em todos os modos: **comportamento de interação não visível e dado de
contato ausente nunca são decididos automaticamente**, porque inventar
esses dois tipos de informação é exatamente o erro que os evals
near-miss (ver `evals/evals.json`) existem para pegar.

## Agrupamento de perguntas

Não pergunte uma coisa de cada vez. Agrupe por etapa do pipeline (ex.:
todas as perguntas de modelagem de conteúdo juntas, depois todas as
perguntas de formulário/integração juntas). Nunca pergunte algo que já foi
respondido pelo usuário em mensagens anteriores da mesma conversa.
