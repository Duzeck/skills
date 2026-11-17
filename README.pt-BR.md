# Duzeck Skills

**Uma coleção de skills, fluxos de trabalho e ferramentas que ampliam o que assistentes de IA conseguem fazer.**

[English](README.md)

## Visão geral

Duzeck Skills é uma coleção aberta de skills reutilizáveis, feitas principalmente para o **Claude Code**, no formato [Agent Skills](https://docs.claude.com/pt/docs/claude-code/skills).

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

### Observações sobre o ambiente

`gerar-pdf`, `resumo-audio-video` e `prd-manager` foram escritas para um agente que roda por trás de um bot do Telegram. Elas citam esse ambiente (envio de arquivo pelo Telegram, a variável `WORKSPACE_DIR`, um bloco de arquivo definido no system prompt). Os scripts também rodam sozinhos pela linha de comando; veja o README de cada skill.

## Instalação

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
