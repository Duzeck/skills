# Duzeck Skills

**Uma coleção de skills, fluxos de trabalho e ferramentas que ampliam o que assistentes de IA conseguem fazer.**

[English](README.md)

## Visão geral

Duzeck Skills é uma coleção aberta de skills reutilizáveis, feitas para o **[DuzeckClaw](https://github.com/Duzeck/duzecklaw)** e o **Claude Code**, no formato [Agent Skills](https://docs.claude.com/pt/docs/claude-code/skills).

Cada skill é uma pasta com um `SKILL.md` (instruções e descrição de quando acionar) e, quando necessário, scripts, referências e arquivos de apoio. O agente carrega a skill sozinho quando o pedido combina com a descrição dela.

> As skills são escritas em português do Brasil e respondem em português.

## Skills disponíveis

| Skill | O que faz | Requisitos |
|---|---|---|
| [duzeck-wordpress-site-builder](duzeck-wordpress-site-builder/) | Transforma uma referência visual (imagem ou capturas de tela) em um site WordPress administrável e responsivo rodando localmente: análise visual → modelagem de conteúdo (CPTs, ACF, taxonomias) → Blueprint aprovado → implementação → validação visual. | WAMP, WP-CLI, PHP, Python 3.9+, ACF PRO, Contact Form 7 |
| [resumo-youtube](resumo-youtube/) | Resume vídeos do YouTube a partir do link, com metadados e timestamps. Usa legenda oficial, legenda automática, Whisper local ou Gemini, nessa ordem. | Python 3.9+, `yt-dlp`, `ffmpeg` (opcional: `faster-whisper`, `GEMINI_API_KEY`) |
| [resumo-audio-video](resumo-audio-video/) | Transcreve áudios e vídeos (mensagens de voz, reuniões, aulas, podcasts, links fora do YouTube) com Whisper local e entrega um resumo estruturado em PDF. | Python 3.9+, `ffmpeg`, `faster-whisper`, `yt-dlp` |
| [resumo-pdf](resumo-pdf/) | Extrai o texto de PDFs, inclusive escaneados (OCR) e protegidos por senha, e devolve um resumo estruturado. | Python 3.9+, `pypdf`, Tesseract para OCR (instalado automaticamente quando possível) |
| [gerar-pdf](gerar-pdf/) | Converte qualquer conteúdo (resumos, relatórios, PRDs, anotações) em um PDF formatado, com capa, sumário, tabelas e numeração de páginas. | Python 3.9+, `reportlab`, `markdown-it-py` |
| [prd-manager](prd-manager/) | Escreve e revisa PRDs e specs de produto com requisitos numerados, prioridades e critérios de aceite testáveis. | Nenhum |

## Usando com o DuzeckClaw (Telegram)

O [DuzeckClaw](https://github.com/Duzeck/duzecklaw) é um agente pessoal de IA que roda localmente no seu PC e é controlado pelo Telegram (Node.js + TypeScript). Estas skills foram feitas para ele: `gerar-pdf`, `resumo-audio-video`, `resumo-pdf`, `resumo-youtube` e `prd-manager` funcionam direto lá. Você manda um link do YouTube, uma mensagem de voz ou um PDF no chat, e o bot responde com o resumo ou o arquivo.

1. Instale o DuzeckClaw (Node.js 20+, um token de bot do Telegram e uma API key do Gemini, DeepSeek ou Groq):

   ```bash
   git clone https://github.com/Duzeck/duzecklaw.git
   cd duzecklaw
   npm install
   cp .env.example .env   # no Windows: copy .env.example .env; depois preencha o token e a API key
   ```

2. Clone este repositório na pasta de skills do bot:

   ```bash
   git clone https://github.com/Duzeck/skills.git .agents/skills
   ```

3. Instale as dependências Python usadas pelos scripts das skills (já listadas no `requirements.txt` do DuzeckClaw) e inicie o bot:

   ```bash
   pip install -r requirements.txt
   npm run dev
   ```

Para atualizar as skills depois, rode `git -C .agents/skills pull`. O DuzeckClaw relê a pasta a cada mensagem, então skills novas ou atualizadas valem na hora, sem reiniciar o bot.

Algumas skills dependem desse ambiente: `gerar-pdf` envia o PDF pelo Telegram, `resumo-audio-video` lê as mídias que o bot salva em `workspace/midias/` e usa a variável `WORKSPACE_DIR`, e `prd-manager` devolve os documentos no bloco de arquivo do bot. Em outros agentes os scripts continuam rodando pela linha de comando; veja o README de cada skill.

## Instalação no Claude Code

Clone o repositório:

```bash
git clone https://github.com/Duzeck/skills.git
```

Para instalar uma skill para o seu usuário no Claude Code, copie a pasta dela para o diretório pessoal de skills:

```bash
mkdir -p ~/.claude/skills
cp -r skills/resumo-youtube ~/.claude/skills/
```

Para instalar só em um projeto:

```bash
mkdir -p .claude/skills
cp -r skills/resumo-youtube .claude/skills/
```

Reinicie o Claude Code (ou abra uma nova sessão) para ele reconhecer a skill.

## Estrutura do repositório

```text
skills/
├── duzeck-wordpress-site-builder/
│   ├── SKILL.md
│   ├── README.md
│   ├── references/
│   ├── scripts/
│   ├── assets/
│   ├── examples/
│   └── evals/
├── gerar-pdf/
│   ├── SKILL.md
│   ├── README.md
│   └── scripts/
├── prd-manager/
│   ├── SKILL.md
│   └── README.md
├── resumo-audio-video/
│   ├── SKILL.md
│   ├── README.md
│   ├── references/
│   ├── scripts/
│   └── testes.md
├── resumo-pdf/
│   ├── SKILL.md
│   ├── README.md
│   ├── extrair_pdf.py
│   └── testes.md
├── resumo-youtube/
│   ├── SKILL.md
│   ├── README.md
│   ├── scripts/
│   └── testes.md
├── README.md
├── README.pt-BR.md
├── CONTRIBUTING.md
└── LICENSE
```

## Compatibilidade

Feitas principalmente para:

- [DuzeckClaw](https://github.com/Duzeck/duzecklaw)
- Claude Code
- Apps do Claude (claude.ai) com skills habilitadas
- Outros agentes compatíveis com o formato Agent Skills

O funcionamento em outros agentes depende de eles conseguirem executar scripts e das ferramentas que oferecem.

## Contribuindo

Sugestões e melhorias são bem-vindas. Leia o [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir um pull request.

## Licença

Distribuído sob a Licença MIT. Veja [LICENSE](LICENSE).

---

**Mantido por [Duzeck](https://github.com/Duzeck).**
