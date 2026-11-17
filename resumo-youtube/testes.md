# Casos de teste — resumo-youtube

## T1 — Vídeo curto com legenda oficial
Link: vídeo de 5 a 10 minutos, em português, com legenda manual.
Esperado: primeiro o menu (estilo, recursos, detalhamento, público); após a escolha, resumo no estilo pedido, cabeçalho com metadados, timestamps coerentes, origem "legenda oficial".

## T2 — Vídeo com apenas legenda automática
Link: vídeo em inglês sem legenda manual.
Esperado: resumo em pt-BR, idioma original registrado como inglês, origem "legenda automática", timestamps presentes.

## T3 — Vídeo sem legenda alguma
Link: vídeo recente sem legendas.
Esperado: script cai para Whisper; resumo com timestamps; origem "Whisper". Se Whisper não estiver disponível, aviso claro ao usuário.

## T4 — Vídeo longo (aula de 1h30)
Esperado: resumo por blocos de ~10 min e consolidado; sem repetição de pontos; tempo de processamento informado antes de começar.

## T5 — Vídeo privado ou removido
Esperado: script retorna código 3; a skill informa o problema e pergunta se há outro link ou transcrição. Nenhum resumo inventado.

## T6 — Transmissão ao vivo em andamento
Esperado: aviso de que a transcrição cobre apenas o trecho disponível; pergunta ao usuário se quer prosseguir.

## T7 — Shorts
Esperado: resumo proporcionalmente curto, com aviso de que o conteúdo é breve.

## T8 — Playlist em vez de vídeo
Esperado: a skill pergunta quais vídeos resumir e se quer consolidado.

## T9 — Vídeo sem fala (música ou demonstração visual)
Esperado: a skill informa que não há conteúdo falado e pergunta como prosseguir.

## T10 — URL inválida ou de outra plataforma
Esperado: script retorna código 5; a skill informa que o link não é do YouTube.

## T11 — Ambiente sem execução de código
Esperado: a skill avisa em uma linha que não consegue baixar/transcrever e pede a transcrição ou o texto.

## T12 — Fallback Gemini sem chave
Esperado: script retorna código 4 com mensagem sobre `GEMINI_API_KEY`; a skill informa a limitação e oferece alternativas.

## T13 — Conteúdo sensível (saúde, finanças, política)
Esperado: resumo atribui as afirmações ao autor do vídeo, sem endossar nem refutar; ressalvas registram ausência de fontes.

## T14 — Legenda automática com erros evidentes
Esperado: correções apenas quando óbvias pelo contexto; erros mantidos e sinalizados nas ressalvas.
