# Responsividade

## Breakpoints padrão (usar quando não há referência mobile)

| Faixa | Largura | Uso |
|---|---|---|
| Desktop | ≥1200px | Layout de referência original |
| Tablet | 768px–1199px | Grids reduzem colunas (ex.: 3→2), navegação pode colapsar |
| Mobile | <768px | Coluna única, menu hambúrguer, hero com texto/imagem empilhados |

## Quando há referência mobile

Siga a referência fornecida com a mesma disciplina de qualquer outra parte
do Blueprint — não infira onde há evidência visual direta.

## Quando NÃO há referência mobile

Pode inferir usando boas práticas, mas:

1. Registre explicitamente em `blueprint.responsive` que o comportamento
   mobile é inferido, não confirmado (`evidence: inference`,
   `confidence: medium` ou `low`).
2. Regras de inferência padrão:
   - Grids de N colunas (N≥3) → 2 colunas em tablet, 1 em mobile.
   - Menu horizontal → menu hambúrguer em mobile.
     Em single page o header continua sticky em mobile e o menu fecha ao
     escolher um item (`references/navigation.md`).
   - Hero com texto + imagem lado a lado → empilhado (texto acima da
     imagem) em mobile.
   - Tabelas largas → rolagem horizontal ou cards empilhados em mobile
     (`tables[].mobile`, ver `references/tables-pricing.md`),
     o que for mais legível para o conteúdo específico.
   - Tipografia: reduzir tamanho de títulos grandes (hero/h1) em ~30-40%
     em mobile; manter corpo de texto legível (mínimo ~16px).
3. Depois de implementar, valide visualmente nos três breakpoints via
   `claude-in-chrome` e ajuste o que ficar visualmente quebrado — a
   inferência é um ponto de partida, não a palavra final.
