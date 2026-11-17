# prd-manager

Skill que cria e revisa PRDs e specs de produto ou feature, no papel de um Product Manager técnico sênior.

## O que entrega

Um documento Markdown com estrutura fixa de 14 seções: resumo, contexto, goals com métricas, non-goals, personas, requisitos funcionais e não funcionais, design, modelo de dados, integrações, edge cases, segurança, plano de rollout e open questions.

- Requisitos com IDs (`RF-01`, `RNF-01`), prioridade (Must/Should/Could) e critério de aceite verificável.
- Quando falta contexto, a skill faz suposições razoáveis e as lista em "Open Questions".
- O arquivo é nomeado `prd-<nome-curto>.md`.

## Requisitos

Nenhum. A skill não usa scripts.

## Uso com o DuzeckClaw

A skill foi feita para o [DuzeckClaw](https://github.com/Duzeck/duzecklaw), agente pessoal controlado pelo Telegram. A seção "Entrega" do `SKILL.md` pede que o documento saia no "bloco de arquivo descrito no system prompt": é o marcador `<<<ARQUIVO:nome.md>>> ... <<<FIM_ARQUIVO>>>` do DuzeckClaw, que o bot converte em anexo `.md` no chat. Para instalar, veja [Usando com o DuzeckClaw](../README.pt-BR.md#usando-com-o-duzeckclaw-telegram).

Em outro agente (como o Claude Code), ajuste essa seção para gravar o arquivo diretamente ou devolver o Markdown na resposta.
