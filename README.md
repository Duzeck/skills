# Duzeck Skills

**A collection of AI agent skills, workflows, and tools that extend what AI coding assistants can do.**

[Português](README.pt-BR.md)

## Overview

Duzeck Skills is an open collection of reusable skills built for **[DuzeckClaw](https://github.com/Duzeck/duzecklaw)** and **Claude Code**, using the [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) format.

Each skill is a folder with a `SKILL.md` (instructions and trigger description) plus optional scripts, references, and assets. The agent loads a skill automatically when a request matches its description.

> The skills are written in Brazilian Portuguese and produce output in Portuguese.

## Available skills

| Skill | What it does | Requirements |
|---|---|---|
| [duzeck-wordpress-site-builder](duzeck-wordpress-site-builder/) | Turns a visual reference (image or screenshots) into a manageable, responsive WordPress site running locally: visual analysis → content model (CPTs, ACF, taxonomies) → approved Blueprint → implementation → visual validation. | WAMP, WP-CLI, PHP, Python 3.9+, ACF PRO, Contact Form 7 |
| [resumo-youtube](resumo-youtube/) | Summarizes YouTube videos from a link, with metadata and timestamps. Uses official captions, auto captions, local Whisper, or Gemini as fallbacks. | Python 3.9+, `yt-dlp`, `ffmpeg` (optional: `faster-whisper`, `GEMINI_API_KEY`) |
| [resumo-audio-video](resumo-audio-video/) | Transcribes audio and video (voice notes, meetings, classes, podcasts, non-YouTube links) with local Whisper and delivers a structured summary as PDF. | Python 3.9+, `ffmpeg`, `faster-whisper`, `yt-dlp` |
| [resumo-pdf](resumo-pdf/) | Extracts text from PDFs, including scanned ones (OCR) and password-protected files, and returns a structured summary. | Python 3.9+, `pypdf`, Tesseract for OCR (auto-installed when possible) |
| [gerar-pdf](gerar-pdf/) | Converts any content (summaries, reports, PRDs, notes) into a formatted PDF with cover, table of contents, tables, and page numbers. | Python 3.9+, `reportlab`, `markdown-it-py` |
| [prd-manager](prd-manager/) | Writes and reviews PRDs and product specs with numbered requirements, priorities, and testable acceptance criteria. | None |

## Using with DuzeckClaw (Telegram)

[DuzeckClaw](https://github.com/Duzeck/duzecklaw) is a personal AI agent that runs locally on your PC and is controlled through Telegram (Node.js + TypeScript). These skills were built for it: `gerar-pdf`, `resumo-audio-video`, `resumo-pdf`, `resumo-youtube`, and `prd-manager` all work out of the box there. You send a YouTube link, a voice note, or a PDF in the chat, and the bot replies with the summary or file.

1. Install DuzeckClaw (Node.js 20+, a Telegram bot token, and an API key for Gemini, DeepSeek, or Groq):

   ```bash
   git clone https://github.com/Duzeck/duzecklaw.git
   cd duzecklaw
   npm install
   cp .env.example .env   # Windows: copy .env.example .env, then fill in the token and API key
   ```

2. Clone this repository into the bot's skills folder:

   ```bash
   git clone https://github.com/Duzeck/skills.git .agents/skills
   ```

3. Install the Python dependencies the skill scripts use (already listed in DuzeckClaw's `requirements.txt`) and start the bot:

   ```bash
   pip install -r requirements.txt
   npm run dev
   ```

To update the skills later, run `git -C .agents/skills pull`. DuzeckClaw rereads the folder on every message, so new or updated skills take effect without restarting the bot.

Some skills depend on that setup: `gerar-pdf` sends the PDF over Telegram, `resumo-audio-video` reads media the bot saves to `workspace/midias/` and uses the `WORKSPACE_DIR` variable, and `prd-manager` returns documents in the bot's file block. In other agents the scripts still run from the command line; see each skill's README.

## Installation in Claude Code

Clone the repository:

```bash
git clone https://github.com/Duzeck/skills.git
```

To install a skill for your user in Claude Code, copy its folder into your personal skills directory:

```bash
mkdir -p ~/.claude/skills
cp -r skills/resumo-youtube ~/.claude/skills/
```

To install it for a single project instead:

```bash
mkdir -p .claude/skills
cp -r skills/resumo-youtube .claude/skills/
```

Restart Claude Code (or start a new session) so it picks up the new skill.

## Repository structure

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

## Compatibility

Built mainly for:

- [DuzeckClaw](https://github.com/Duzeck/duzecklaw)
- Claude Code
- Claude apps (claude.ai) with skills enabled
- Other agents that support the Agent Skills format

How well a skill works on other agents depends on whether they can run scripts and which tools they expose.

## Contributing

Suggestions and improvements are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

Released under the MIT License. See [LICENSE](LICENSE).

---

**Maintained by [Duzeck](https://github.com/Duzeck).**
