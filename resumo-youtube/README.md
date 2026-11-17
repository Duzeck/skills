# resumo-youtube

Skill para resumir vídeos do YouTube a partir de um link, com metadados e timestamps, em português do Brasil.

Funciona no [DuzeckClaw](https://github.com/Duzeck/duzecklaw) (basta mandar o link no Telegram) e no Claude Code. Para instalar no DuzeckClaw, veja [Usando com o DuzeckClaw](../README.pt-BR.md#usando-com-o-duzeckclaw-telegram).

## Requisitos

- Python 3.9+
- `yt-dlp` (instalado automaticamente pelo script se ausente)
- `ffmpeg` (necessário para extrair áudio; o script tenta instalar via apt/dnf/apk/brew/winget/choco)
- Opcional: `faster-whisper` (transcrição local quando não há legenda)
- Opcional: `GEMINI_API_KEY` no ambiente (fallback de transcrição)

## Uso

```bash
python scripts/resumir_video.py "https://www.youtube.com/watch?v=XXXX"
```

Opções:

| Opção | Padrão | Descrição |
|---|---|---|
| `--idioma` | `pt,en` | Idiomas preferidos para legenda, separados por vírgula |
| `--saida` | `transcricao.txt` | Arquivo de saída com a transcrição |
| `--metadados` | `metadados.json` | Arquivo com título, canal, data, duração e link |
| `--modelo-whisper` | `small` | Modelo do Whisper (`tiny`, `base`, `small`, `medium`, `large`) |
| `--sem-whisper` | desligado | Pula a transcrição local |
| `--sem-gemini` | desligado | Pula o fallback Gemini |

## Ordem de extração

1. Legenda oficial (manual)
2. Legenda automática do YouTube
3. Whisper local sobre o áudio
4. Gemini (se `GEMINI_API_KEY` existir)

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Sucesso |
| 2 | Dependências ausentes e instalação automática falhou |
| 3 | Vídeo inacessível (privado, removido, restrito, ao vivo) |
| 4 | Nenhuma transcrição obtida |
| 5 | URL inválida ou argumento incorreto |

## Limitações conhecidas

- O script não resume: ele apenas extrai a transcrição. O resumo é feito pelo modelo seguindo o `SKILL.md`.
- Vídeos com restrição de idade ou bloqueio regional podem falhar no download.
- O Whisper local em CPU é lento: vídeos de 1 hora podem levar dezenas de minutos com o modelo `small`.
- O fallback Gemini exige chave válida e cota disponível; sem chave, o script retorna código 4.
- Legendas automáticas podem conter erros de transcrição, especialmente com nomes próprios e termos técnicos.
- Timestamps só existem se a fonte tiver tempos (legendas ou Whisper). Se a fonte for Gemini sem áudio, os tempos são aproximados.
