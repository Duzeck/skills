# Casos de teste — resumo-audio-video

## T1 — Áudio curto enviado como arquivo
Entrada: MP3 de 3 a 5 minutos, em português, sem legenda.
Esperado: o bot salva em `midias/`, a skill transcreve com código 0, gera o PDF com todas as seções e envia o arquivo com um resumo de 2 a 3 linhas no chat.

## T2 — Vídeo com legenda pedindo ata
Entrada: MP4 de reunião (até 20 MB) com a legenda "faça uma ata com responsáveis".
Esperado: resumo no formato de ata, decisões e tarefas com responsáveis só quando ditos na fala, PDF enviado.

## T3 — Mensagem de voz curta
Entrada: voz de 10 segundos ("que horas são?").
Esperado: NÃO aciona a skill; o bot responde ao comando falado, como antes.

## T4 — Mensagem de voz longa ou encaminhada
Entrada: voz de 4 minutos, ou encaminhada de outra conversa.
Esperado: o bot salva em `midias/` e a skill resume.

## T5 — Arquivo acima de 20 MB
Entrada: vídeo de 80 MB.
Esperado: o bot avisa do limite do Telegram e sugere link ou áudio compactado; a skill não é acionada.

## T6 — Áudio longo (retomada)
Entrada: áudio de 60 a 90 minutos.
Esperado: se a primeira execução sair com código 6, a skill roda de novo com os mesmos argumentos e continua do bloco seguinte; timestamps contínuos e corretos.

## T7 — Link fora do YouTube
Entrada: link do Vimeo ou link direto de .mp3.
Esperado: o script baixa com yt-dlp e segue o fluxo normal. Link do YouTube deve ir para a skill resumo-youtube.

## T8 — Vídeo sem som
Entrada: gravação de tela sem áudio.
Esperado: código 4; a skill informa que não há conteúdo falado e não gera PDF.

## T9 — Áudio em inglês
Entrada: podcast em inglês com legenda "resume".
Esperado: a skill usa `--idioma auto` (ou o resumo nota o idioma), resumo em português, idioma original registrado na tabela de metadados.

## T10 — Pedido de transcrição completa
Entrada: após o resumo, "me manda a transcrição completa".
Esperado: segundo arquivo com a transcrição integral, reaproveitando o cache (sem transcrever de novo).
