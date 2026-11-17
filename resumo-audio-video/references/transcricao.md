# Transcrição local com Whisper

O `scripts/processar_midia.py` já cuida de motor, blocos e timestamps. Esta referência serve para escolher opções e diagnosticar problemas.

## Motor

1. **faster-whisper** (padrão): 3 a 4 vezes mais rápido em CPU e usa menos memória.
2. **openai-whisper**: usado só se o faster-whisper não estiver instalado.

Se nenhum estiver instalado, o script sai com código 2. Instale com `pip install faster-whisper`. O primeiro uso de cada modelo baixa os pesos (cerca de 500 MB para o `small`).

## Modelo (`--modelo`)

| Situação | Modelo |
|---|---|
| Áudio limpo, fala clara (padrão) | `small` |
| Ruído, sotaque forte, termos técnicos, nomes próprios | `medium` (cerca de 3 vezes mais lento) |
| Teste rápido / rascunho | `base` ou `tiny` |

O padrão pode ser trocado pela variável de ambiente `MIDIA_WHISPER_MODEL`.

## Idioma (`--idioma`)

- Padrão `pt`: evita que o Whisper detecte errado em trechos curtos e traduza para inglês.
- `--idioma auto` quando o áudio não estiver em português ou misturar idiomas. O idioma detectado aparece no resultado.

## Blocos, tempo e retomada

- O áudio é transcrito em blocos de 10 minutos (`--bloco-min`). Os timestamps de cada bloco são somados ao início do bloco, então batem com o original.
- Cada execução respeita o limite da ferramenta (`SKILL_SCRIPT_TIMEOUT_MS` menos 3 minutos, ou `--tempo-max-min`). Se não der tempo de terminar, o script sai com código 6 e guarda os blocos prontos.
- O cache fica em `midias/trabalho/<id>/` no workspace. Rodar de novo com os mesmos argumentos continua do bloco seguinte; `--refazer` descarta o cache.

## Problemas comuns

- **Frases repetidas em loop** ("obrigado obrigado obrigado"): o script já descarta repetições seguidas e segmentos com `no_speech_prob > 0.6`, e usa `vad_filter`. Se ainda acontecer, rode com `--filtro-silencio --refazer`. Esse filtro corta silêncios do meio do áudio e **desloca os timestamps**; avise isso no resumo.
- **Nomes próprios errados**: corrija no resumo só quando o contexto deixar óbvio; a transcrição fica como está.
- **Áudio muito baixo ou abafado**: o script já aplica `highpass` e normalização dinâmica (`dynaudnorm`). Se a qualidade continuar ruim, tente `--modelo medium`.
- **Vídeo sem som**: código 4 ("a mídia não tem faixa de áudio").
