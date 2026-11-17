# resumo-audio-video

Skill que transcreve áudios e vídeos com Whisper local e entrega um resumo estruturado em PDF (via skill `gerar-pdf`).

## Requisitos

- Python 3.9+
- `ffmpeg` e `ffprobe` no PATH
- `faster-whisper` (ou `openai-whisper`)
- `yt-dlp`, só para links

## Como a mídia chega

O bot salva em `workspace/midias/` os áudios, vídeos, vídeos redondos e arquivos de mídia enviados como documento, e as mensagens de voz longas (acima de `VOICE_AS_MEDIA_SECONDS`, padrão 120 s), encaminhadas ou com legenda. A mensagem enviada ao agente traz o caminho do arquivo. Mensagens de voz curtas continuam sendo tratadas como comandos falados.

O Telegram só deixa bots baixarem arquivos de até 20 MB. Acima disso o bot pede um link ou um arquivo menor.

## Uso manual

```bash
# arquivo (relativo ao diretório atual ou a WORKSPACE_DIR)
python scripts/processar_midia.py midias/reuniao.mp4

# link, modelo maior, idioma automático
python scripts/processar_midia.py "https://vimeo.com/123" --modelo medium --idioma auto
```

Grava `transcricao.txt` e `info.json` no diretório atual e imprime um resumo JSON. O cache fica em `<WORKSPACE_DIR>/midias/trabalho/<id>/`.

| Opção | Padrão | Descrição |
|---|---|---|
| `--modelo` | `small` (ou `MIDIA_WHISPER_MODEL`) | `tiny`, `base`, `small`, `medium`, `large-v3` |
| `--idioma` | `pt` | código do idioma ou `auto` |
| `--bloco-min` | `10` | tamanho dos blocos de transcrição |
| `--tempo-max-min` | limite da ferramenta − 3 min | tempo máximo desta execução |
| `--filtro-silencio` | desligado | remove silêncios longos (desloca os timestamps) |
| `--refazer` | — | ignora o cache |

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | Transcrição completa |
| 2 | Dependência ausente (ffmpeg, ffprobe, Whisper, yt-dlp) |
| 3 | Entrada não encontrada, download falhou ou mídia ilegível |
| 4 | Nenhuma fala detectada ou mídia sem faixa de áudio |
| 5 | Argumento inválido |
| 6 | Parcial: rode de novo com os mesmos argumentos para continuar |

## Limitações

- Não identifica quem está falando (sem diarização).
- Em CPU, o modelo `small` leva da ordem de alguns minutos por hora de áudio a dezenas de minutos, conforme a máquina; áudios longos podem precisar de mais de uma execução (código 6).
- Os arquivos em `workspace/midias/` não são apagados automaticamente.
