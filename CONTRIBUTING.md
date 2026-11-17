# Contributing / Contribuindo

[English](#english) · [Português](#português)

## English

Thanks for your interest in improving these skills.

### Reporting problems

Open an issue describing:

- which skill you used and what you asked the agent;
- what you expected and what happened;
- your environment (agent, OS, Python version) and any error output.

### Proposing changes

1. Fork the repository and create a branch from `main`.
2. Make your change. Keep each pull request focused on one skill or one topic.
3. Test it: run the skill end to end in Claude Code (or another compatible agent), and run any scripts you changed. Skills with a `testes.md` or `evals/` folder list the cases to check.
4. Open a pull request explaining what changed and why.

### Skill guidelines

- Every skill lives in its own folder with a `SKILL.md` whose frontmatter has `name` (matching the folder name) and `description`.
- The `description` decides when the agent loads the skill: say what it does and when to use it, with the words users actually type.
- Keep `SKILL.md` focused on instructions. Move long reference material to `references/` and code to `scripts/`.
- Add a `README.md` for humans: requirements, manual usage, exit codes, and known limitations.
- Scripts should fail with a clear message and a documented exit code, never invent output.
- Do not commit secrets, API keys, personal data, or generated files (`__pycache__`, outputs, caches).
- Existing skills are written in Brazilian Portuguese; keep that language when editing them.

By contributing, you agree that your contributions are licensed under the MIT License.

## Português

Obrigado pelo interesse em melhorar estas skills.

### Relatando problemas

Abra uma issue informando:

- qual skill você usou e o que pediu ao agente;
- o que esperava e o que aconteceu;
- seu ambiente (agente, sistema operacional, versão do Python) e as mensagens de erro.

### Propondo mudanças

1. Faça um fork do repositório e crie uma branch a partir de `main`.
2. Faça a alteração. Cada pull request deve tratar de uma skill ou de um assunto.
3. Teste: rode a skill do início ao fim no Claude Code (ou em outro agente compatível) e execute os scripts que você alterou. As skills com `testes.md` ou pasta `evals/` listam os casos a verificar.
4. Abra o pull request explicando o que mudou e por quê.

### Diretrizes para skills

- Cada skill fica na própria pasta, com um `SKILL.md` cujo frontmatter tem `name` (igual ao nome da pasta) e `description`.
- A `description` decide quando o agente carrega a skill: diga o que ela faz e quando usar, com as palavras que o usuário realmente escreve.
- Mantenha o `SKILL.md` focado nas instruções. Material de referência longo vai para `references/` e código para `scripts/`.
- Inclua um `README.md` para pessoas: requisitos, uso manual, códigos de saída e limitações conhecidas.
- Scripts devem falhar com mensagem clara e código de saída documentado, nunca inventar resultado.
- Não envie segredos, chaves de API, dados pessoais nem arquivos gerados (`__pycache__`, saídas, caches).
- As skills existentes são escritas em português do Brasil; mantenha o idioma ao editá-las.

Ao contribuir, você concorda que sua contribuição será licenciada sob a Licença MIT.
