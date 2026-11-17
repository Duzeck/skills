---
name: resumo-audio-video
description: 'Transcreve e resume áudios e vídeos (mensagens de voz longas ou encaminhadas, arquivos de áudio, vídeos, reuniões, aulas, podcasts, entrevistas, gravações de tela) e entrega um resumo estruturado em PDF. Use sempre que a mensagem trouxer "[Mídia anexada pelo usuário: ...]" ou um link de mídia que não seja do YouTube (Vimeo, X/Twitter, Instagram, link direto de .mp3/.mp4) e o usuário quiser resumo, transcrição, ata, "o que foi dito", pontos principais ou análise do conteúdo, mesmo sem usar a palavra "resumo".'
---

# Resumo de áudio e vídeo

Recebe um áudio ou vídeo, transcreve com Whisper local e entrega um resumo estruturado em PDF.

## Regra de ouro

Resuma só o que foi dito na transcrição. Não invente nomes, números, datas ou falas. Se a transcrição falhar, diga isso e pare; não resuma a partir do nome do arquivo.

## De onde vem a mídia

- **Arquivo enviado no Telegram** (áudio, vídeo, vídeo redondo, mensagem de voz longa, encaminhada ou com legenda, arquivo de mídia como documento): o bot salva no workspace e a mensagem chega assim:

  ```
  <legenda do usuário ou "Resuma o conteúdo deste vídeo.">

  [Mídia anexada pelo usuário: vídeo para transcrever e resumir com a skill resumo-audio-video]
  - arquivo no workspace: midias/20261111-174500-reuniao.mp4
  - nome original: reuniao.mp4
  - duração: 12:34
  ```

  Use o caminho de "arquivo no workspace" exatamente como veio.
- **Link** de mídia: use a URL. Para YouTube, prefira a skill `resumo-youtube`, que usa a legenda e é mais rápida.
- **Arquivo acima de 20 MB:** o Telegram não deixa bots baixarem. O bot já avisa o usuário; não prometa processar.

A legenda do usuário define o pedido: "faça uma ata", "só os números", "quais tarefas ficaram para mim" etc. Sem pedido específico, use o formato padrão abaixo.

## Fluxo

1. **Transcreva** com uma única ferramenta:
   - `executar_script_skill` com skill `resumo-audio-video`, script `scripts/processar_midia.py` e argumentos `["<caminho ou URL>"]`.
   - Opcionais: `--modelo medium` (áudio ruidoso, sotaque forte, termos técnicos), `--idioma auto` (outro idioma ou mais de um), `--filtro-silencio` (só se a transcrição vier com frases repetidas em loop).
   - O script baixa o link se for URL, extrai o áudio, transcreve em blocos de 10 min mantendo os tempos do original e devolve `transcricao.txt` no resultado da ferramenta.
2. **Confira o código de saída:**

   | Código | Significado | O que fazer |
   |---|---|---|
   | 0 | Transcrição completa | Siga para o passo 3. |
   | 6 | Parcial: o tempo da ferramenta acabou | Rode de novo com os MESMOS argumentos; ele continua de onde parou. Repita no máximo 3 vezes; se ainda faltar, resuma o trecho transcrito e diga até que minuto chegou. |
   | 2 | Falta ffmpeg ou Whisper | Informe o erro ao usuário. |
   | 3 | Arquivo ou link inacessível | Informe e peça outro arquivo ou link. |
   | 4 | Sem fala ou sem faixa de áudio | Informe que não há conteúdo falado para resumir. |

3. **Resuma** no formato da seção "Estrutura do resumo", usando os timestamps `[MM:SS]` da transcrição.
4. **Gere o PDF** seguindo a skill `gerar-pdf`:
   - grave o Markdown com `criar_arquivo` em `resumos/<slug>.md` (slug curto, minúsculo, sem acentos);
   - converta com `executar_script_skill` (skill `gerar-pdf`, script `scripts/gerar_pdf.py`, argumentos `["resumos/<slug>.md", "--subtitulo", "Resumo de <áudio|vídeo>"]`, mais `--sumario` se o resumo tiver 4 seções ou mais).
5. **Responda** com 2 a 3 linhas resumindo o conteúdo e, em linha separada, o marcador do PDF com o caminho exato de `arquivos_gerados`:

   ```
   <<<ENVIAR_ARQUIVO:execucoes/gerar-pdf/.../<slug>.pdf>>>
   ```

6. **Transcrição completa** (só se o usuário pedir): grave o conteúdo de `transcricao.txt` com `criar_arquivo` em `resumos/<slug>-transcricao.md` e gere um segundo PDF, ou envie o `.txt` com o marcador de envio.

## Estrutura do resumo

Adapte os títulos ao conteúdo, mas mantenha a ordem:

```
# <Título descritivo do conteúdo>

| | |
|---|---|
| Fonte | <nome original do arquivo ou link> |
| Duração | <mm:ss> |
| Idioma | <idioma> |
| Transcrição | Whisper <modelo> (local) |

## Resumo em 30 segundos
<2 a 4 frases com a ideia central>

## Pontos principais
- <ponto, com [MM:SS] quando ajudar a localizar>

## Tópicos por tempo
- [00:00] <assunto>
- [05:12] <assunto>

## Citações e números relevantes
<falas marcantes, dados, valores, nomes e datas que aparecem na transcrição>

## Decisões e próximos passos
<só se houver decisões, tarefas ou recomendações; diga quem ficou responsável quando isso for dito. Caso contrário, omita a seção>
```

Regras de conteúdo:
- Trechos marcados como inaudíveis ou confusos na transcrição viram `[inaudível]` no resumo.
- Nomes próprios que a transcrição escreveu errado: corrija só quando o contexto deixar óbvio.
- Mais de uma pessoa falando: o Whisper não identifica quem fala. Só atribua falas quando a própria fala deixar claro ("Maria, você cuida disso").
- Áudio curto (menos de 2 min) e sem estrutura: um parágrafo único em vez de todas as seções, e responda direto no chat, sem PDF, a menos que o usuário peça PDF.
- Transcrição parcial: avise no topo do resumo até que minuto o conteúdo foi coberto.

## Arquivos da skill

- `scripts/processar_midia.py`: baixa, extrai o áudio e transcreve em blocos, com cache e retomada.
- `references/transcricao.md`: escolha de modelo, idioma e problemas comuns.
- `README.md`: requisitos e uso manual.
- `testes.md`: casos de teste.
