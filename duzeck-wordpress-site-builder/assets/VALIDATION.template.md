# Validação — {{PROJECT_NAME}}

Registro dos testes executados e problemas encontrados, seguindo
`references/validation-playbook.md`.

## Arquitetura

- [ ] Toda página tem template definido
- [ ] Todo conteúdo dinâmico tem modelo (CPT/campos/taxonomia)
- [ ] Nenhum dado global duplicado no código
- [ ] Toda taxonomia tem uso real
- [ ] Todo plugin tem justificativa
- [ ] `scripts/validate_blueprint.py` passou sem bloqueio

## Funcional

- [ ] Tema ativa sem erro fatal
- [ ] CPTs/taxonomias funcionam no admin
- [ ] Campos ACF salvam e exibem
- [ ] Menus corretos
- [ ] Formulário envia/confirma (ver limitação de SMTP local, se aplicável)
- [ ] Imagens carregam sem 404

## Técnico

- [ ] `scripts/check_theme.py` passou sem bloqueio
- [ ] Sem erro de console JS nas páginas principais
- [ ] Sem link interno quebrado

- [ ] `check_theme.py`: nenhum dado global fixo, placeholder esquecido ou
      saída ACF sem escape

## Visual — portão de QA

Procedimento, régua P0–P3 e ordem de prioridade de correção em
`references/validation-playbook.md`.

### Evidência capturada

Rodadas de `scripts/capture_site.py` (cada uma em
`documentation/qa/rodada-N/`, com `report.md` e `compare-*.png`):

| Rodada | Pasta | Candidatos a P0 técnico | Violações axe | Links quebrados | Checkpoint |
|---|---|---|---|---|---|
| 1 | qa/rodada-1 | | | | |

| Página | Referência (arquivo) | Breakpoint | Viewport | Estado | Captura | Visão inteira | Recortes |
|---|---|---|---|---|---|---|---|
| | | desktop | 1440 | | | [ ] | [ ] |
| | | tablet | 834 | | | [ ] | [ ] |
| | | mobile | 390 | | | [ ] | [ ] |

### Ledger de divergências

Uma linha por divergência. `Resolução` = correção aplicada **ou**
desvio intencional com motivo. Nunca remova linhas — atualize o status e
a rodada, para que o histórico de comparações fique visível.

| # | Rodada | Página | Breakpoint | Região | Esperado (referência) | Renderizado | Sev. | Resolução | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | P? | | aberto / corrigido (rodada N) / desvio intencional / aceito pelo usuário |

### Notas de acompanhamento (P3)

- {{P3_1}}

### Resultado final

`Resultado final: {{passed | blocked}}`

- `passed` — nenhum P0/P1/P2 aberto; toda página × breakpoint tem
  captura e comparação registradas.
- `blocked` — motivo: {{MOTIVO}} (P0/P1/P2 aberto, ou captura/comparação
  impossível).

## Conteúdo demo identificado

Liste aqui todo conteúdo que é demonstrativo, não real, para que o
administrador saiba o que substituir antes de publicar: itens marcados
`[DEMO]` pela saída de `seed_demo_content.py --blueprint`, textos `copy`
com `source: demo`, e toda mídia com `replace_before_launch: true`
(recortes da referência e placeholders).

- {{ITEM_DEMO_1}}
- {{ITEM_DEMO_2}}

## Limitações conhecidas

Registre aqui qualquer diferença menor aceita conscientemente, ou
limitação do ambiente local (ex.: envio de e-mail do formulário não
testável sem SMTP configurado no WAMP).
