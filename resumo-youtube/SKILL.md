---
name: resumo-youtube
description: Resume o conteúdo de vídeos do YouTube a partir de um link, entregando um resumo estruturado em português do Brasil com metadados e timestamps. Use sempre que o usuário enviar uma URL do YouTube (youtube.com, youtu.be, Shorts, transmissões) e pedir resumo, síntese, resenha, "do que se trata", "o que é dito no vídeo", transcrição, pontos principais, ou análise de conteúdo em vídeo. Também use quando o usuário pedir para extrair a transcrição de um vídeo ou entender uma aula, palestra, podcast, entrevista ou tutorial em vídeo, mesmo que ele não use a palavra "resumo".
---

# Resumo de vídeo do YouTube

Transforma um link do YouTube em um resumo estruturado, em português do Brasil, com metadados e timestamps.

## Regra de ouro

Nunca invente conteúdo. Se não for possível obter a transcrição (legenda ou áudio), diga isso com clareza e ofereça caminhos alternativos. Um resumo inventado a partir do título e da descrição é pior do que nenhum resumo — o usuário pode tomar decisões com base nele.

## Fluxo de trabalho

1. **Receba o link** e confirme que é uma URL do YouTube. Aceite os formatos `youtube.com/watch?v=`, `youtu.be/`, `youtube.com/shorts/`, `youtube.com/live/` e links com parâmetros extras.
2. **Pergunte como o usuário quer o resumo** antes de qualquer outra ação. Não rode o script ainda. Pule a pergunta só se o usuário já tiver dito ao menos o estilo na mesma mensagem (ex.: "resumo didático com glossário para estudantes"). Responda apenas com o menu abaixo, sem texto extra:

   ```
   VIDEO INTELLIGENCE
   Como você quer transformar este vídeo em conhecimento?

   1) ESTILO (escolha um)
   1. Resumo executivo: síntese objetiva e conclusões
   2. Resumo rápido (TL;DR): visão geral em poucas linhas
   3. Resumo estruturado: introdução, desenvolvimento e conclusão
   4. Resumo cronológico: na sequência do vídeo
   5. Resumo didático: explicações simples, analogias e exemplos
   6. Material para estudo: conceitos, definições e revisão
   7. Perguntas e respostas: principais questões explicadas
   8. Resumo técnico: procedimentos, códigos e ferramentas
   9. Resumo analítico: argumentos, evidências e premissas
   10. Análise crítica: contradições, lacunas e pontos questionáveis
   11. Extração de insights: ideias valiosas e oportunidades
   12. Resumo orientado à ação: tarefas e etapas práticas
   13. Entrevistas e podcasts: participantes, opiniões e histórias
   14. Resumo jornalístico: fatos, personagens, fontes e contexto
   15. Aulas e palestras: objetivos, conteúdos e exemplos

   2) RECURSOS (opcional, quantos quiser)
   A. Marcações de tempo
   B. Glossário
   C. Frases e declarações importantes
   D. Conceitos-chave
   E. Aplicações práticas
   F. Plano de ação
   G. Flashcards
   H. Questionário
   I. Mapa mental
   J. Referências e fontes mencionadas

   3) DETALHAMENTO
   N1. Enxuto  |  N2. Moderado (padrão)  |  N3. Detalhado

   4) PÚBLICO
   P1. Geral (padrão)  |  P2. Estudantes  |  P3. Profissionais da área  |  P4. Especialistas  |  P5. Outro (escreva qual)

   Responda assim: estilo, letras dos recursos, nível e público.
   Ex.: 5 ABG N3 P2
   ```

3. **Interprete a resposta.** Aceite códigos ou nomes, em qualquer ordem, com ou sem espaços e vírgulas ("5 ABG N3 P2", "5, a, b, g, detalhado, estudantes", "didático com glossário para estudantes"). Para P5, o público é o texto que o usuário escrever depois (ex.: "P5 médicos"). Pegue a URL do vídeo na mensagem anterior do usuário no histórico.
   - Sem estilo reconhecível: use **1. Resumo executivo**.
   - Sem nível: use **N2. Moderado**. Sem público: use **P1. Geral**. Sem recursos: nenhum.
   - Se aplicar algum padrão, diga isso na linha "Configuração" do cabeçalho.
4. **Obtenha a transcrição.** Se houver ferramenta de execução de código, rode `python scripts/resumir_video.py "<URL>"` e use a transcrição gerada. Se não houver, avise em uma linha ("não consigo baixar/transcrever vídeos neste ambiente") e peça a transcrição ou o texto. Não tente adivinhar o conteúdo pelo título.
5. **Monte a resposta** com o cabeçalho, o corpo do estilo, os recursos marcados e o rodapé, nessa ordem, aplicando o nível de detalhamento e o público (ver "Formatos de saída").

## Ordem de preferência para obter a transcrição

1. **Legenda oficial** (manual, enviada pelo canal) — melhor qualidade, já tem tempos.
2. **Legenda automática** do YouTube — boa qualidade, já tem tempos.
3. **Transcrição local com Whisper** (`faster-whisper` ou `openai-whisper`) sobre o áudio baixado com `yt-dlp` — usar quando não houver legenda ou quando a legenda automática estiver claramente ruim (texto sem pontuação, idioma errado, trechos vazios).
4. **Gemini** (`GEMINI_API_KEY` no ambiente) — último recurso, quando o download local falhar (bloqueio, vídeo grande, ambiente sem ffmpeg). O script envia o áudio ou o link conforme a estratégia disponível.

Se todas falharem, pare e pergunte ao usuário. Não prossiga com resumo parcial sem avisar.

## Formatos de saída

Sempre em português do Brasil, independentemente do idioma do vídeo.

### Cabeçalho (sempre)

```
**[Título do vídeo]**
[Canal] · [Publicado em] · [Duração] · [Link]
Configuração: [estilo] | Recursos: [lista ou "nenhum"] | [nível] | Público: [público]
```

Se o idioma original não for português, acrescente "Idioma original: [idioma]".

### Estilos (corpo da resposta)

Use os títulos de seção indicados, em negrito.

1. **Resumo executivo**: **Resumo executivo** (3 a 5 linhas com a ideia central e a conclusão); **Pontos-chave**; **Números e dados citados** (se não houver, "Nenhum dado numérico relevante citado."); **Conclusões e recomendações do vídeo**; **Ressalvas e lacunas** (trechos inaudíveis, assuntos não desenvolvidos, afirmações sem fonte, patrocínio).
2. **Resumo rápido (TL;DR)**: **TL;DR** em uma frase; um parágrafo curto de visão geral; **Principais pontos** com 3 a 5 itens de uma linha.
3. **Resumo estruturado**: **Introdução** (tema e objetivo do vídeo); **Desenvolvimento** (as partes do conteúdo, cada uma com subtítulo); **Argumentos principais**; **Conclusão**.
4. **Resumo cronológico**: blocos **[MM:SS a MM:SS] Título do trecho**, cada um com 1 a 3 linhas, na ordem do vídeo. Sempre com marcações de tempo, mesmo sem o recurso A.
5. **Resumo didático**: **Do que se trata** (contexto e por que importa); **Explicação passo a passo** em linguagem simples, com analogias e os exemplos do vídeo; **O que levar daqui** (3 a 5 aprendizados).
6. **Material para estudo**: **Objetivos de aprendizagem**; **Conteúdo por tema** (tópicos e subtópicos com definições, exemplos, fórmulas ou regras citadas); **Pontos de atenção** (o que mais confunde ou cai em prova); **Revisão em 5 linhas**.
7. **Perguntas e respostas**: 6 a 12 perguntas que o vídeo responde, na ordem em que aparecem, cada uma com uma resposta explicativa baseada no vídeo.
8. **Resumo técnico**: **Escopo**; **Procedimentos** (passos na ordem, com comandos, códigos e parâmetros exatamente como citados); **Ferramentas e tecnologias** (com versões, se citadas); **Terminologia**; **Limitações e pré-requisitos**.
9. **Resumo analítico**: **Tese central**; **Premissas** assumidas pelo autor; **Argumentos e evidências** (indicando se cada um tem dado, fonte ou é opinião); **Lógica da conclusão** (como os argumentos levam à conclusão).
10. **Análise crítica**: **Tese central**; **Pontos fortes**; **Contradições e inconsistências**; **Lacunas e omissões**; **Pontos questionáveis** (afirmações sem fonte, generalizações, vieses, conflitos de interesse como patrocínio ou venda); **Veredito** (quão sólido é o conteúdo e para quem serve). Avalie a argumentação, não o mérito político ou ideológico do tema.
11. **Extração de insights**: **Insights** (5 a 10 itens, cada um com a ideia, por que importa e de que momento do vídeo vem); **Oportunidades** que o conteúdo sugere; **Ideia mais valiosa** em uma frase.
12. **Resumo orientado à ação**: **Objetivo**; **Recomendações** do vídeo; **Etapas práticas** (lista numerada, na ordem de execução, com ferramenta, prazo ou critério de pronto se citados); **Erros a evitar**.
13. **Entrevistas e podcasts**: **Participantes** (nome e papel de cada um); **Perguntas e temas** discutidos; **Opiniões de cada participante**, atribuídas pelo nome; **Histórias e casos** contados; **Declarações de destaque**.
14. **Resumo jornalístico**: **Lide** (o quê, quem, quando, onde, como e por quê em 2 a 3 linhas); **Fatos**; **Personagens**; **Fontes citadas**; **Contexto**; **Consequências e desdobramentos**. Atribua toda afirmação a quem a fez.
15. **Aulas e palestras**: **Palestrante e contexto** (quem fala, evento ou curso, público, se citados); **Objetivos de aprendizagem**; **Conteúdos** na ordem da aula; **Exemplos e casos**; **Conclusões** e leituras sugeridas.

### Recursos complementares

Adicione depois do corpo, na ordem abaixo, cada um com seu título em negrito. Não repita no recurso o que o estilo já entregou: se o estilo for 7 e o recurso H for pedido, faça questões diferentes das perguntas do corpo.

- **A. Marcações de tempo**: coloque `[MM:SS]` no início de cada ponto do corpo, vindo da transcrição. Sem este recurso, não use timestamps no corpo (exceto no estilo 4).
- **B. Glossário**: termos técnicos e siglas, cada um com definição de uma linha baseada no vídeo.
- **C. Frases e declarações importantes**: 3 a 6 citações literais da transcrição, com quem disse e, se houver, o momento.
- **D. Conceitos-chave**: lista dos conceitos fundamentais, cada um com uma linha de explicação.
- **E. Aplicações práticas**: 3 a 6 formas de usar o conteúdo, sem ir além do que o vídeo sustenta.
- **F. Plano de ação**: etapas numeradas para colocar o conteúdo em prática.
- **G. Flashcards**: 8 a 12 cartões "Frente: ... / Verso: ...", um conceito por cartão.
- **H. Questionário**: 5 a 10 questões de múltipla escolha (4 alternativas), com o gabarito no final.
- **I. Mapa mental**: árvore em texto com o tema central no topo e ramos indentados por "-" (até 3 níveis).
- **J. Referências e fontes mencionadas**: livros, artigos, sites, ferramentas, pessoas e materiais citados no vídeo. Se não houver, "Nenhuma referência citada."

### Nível de detalhamento

Vale para o corpo e para os recursos.

- **N1. Enxuto**: só o essencial. Itens de uma linha, use o mínimo de itens indicado em cada seção e corte seções que ficariam vazias.
- **N2. Moderado**: equilíbrio entre síntese e explicação. Itens de 1 a 2 linhas, quantidade intermediária.
- **N3. Detalhado**: profundidade máxima. Use o máximo de itens indicado, explique cada ponto com contexto e exemplos do vídeo.

### Público-alvo

Ajusta linguagem, vocabulário e o que precisa ser explicado.

- **P1. Geral**: linguagem simples, explique todo termo técnico na primeira vez que aparecer.
- **P2. Estudantes**: tom didático, destaque definições e o que é importante memorizar.
- **P3. Profissionais da área**: foco em aplicação e impacto no trabalho; termos da área sem explicação básica.
- **P4. Especialistas**: denso e preciso, com a terminologia técnica exata; omita o básico.
- **P5. Outro**: adapte ao público que o usuário descreveu (ex.: "médicos", "crianças de 10 anos").

### Rodapé (sempre)

```
Origem da transcrição: [legenda oficial | legenda automática | Whisper | Gemini]
```

Se a resposta ficar muito longa (vários recursos em vídeo longo), priorize o corpo do estilo e reduza os recursos ao mínimo de itens indicado, sem cortar nenhum que foi pedido.

## Resumo em PDF

Se o usuário pedir o resumo em PDF (no pedido inicial ou depois de recebê-lo), monte o resumo normalmente e siga a skill **gerar-pdf** para convertê-lo e enviá-lo: grave o Markdown com `criar_arquivo` e rode `executar_script_skill` com skill `gerar-pdf` e script `scripts/gerar_pdf.py`. Nunca diga que não consegue gerar PDF.

## Vídeos longos

Para vídeos acima de ~30 minutos (aulas, podcasts, palestras):

1. Divida a transcrição em blocos de aproximadamente 10 minutos.
2. Resuma cada bloco em 2 a 4 tópicos com o timestamp de início do bloco.
3. Produza um consolidado no estilo escolhido, usando os tópicos dos blocos como base.
4. Não repita o mesmo ponto em blocos diferentes; consolide.

Para vídeos acima de ~2 horas, avise o usuário sobre o tempo de processamento antes de começar e pergunte se ele quer o resumo completo ou apenas de trechos específicos.

## Casos de borda — sempre perguntar antes de prosseguir

Não decida sozinho nestes casos. Explique a situação em uma ou duas linhas e faça uma pergunta objetiva:

- **Vídeo privado, removido, com restrição de idade ou bloqueado na região:** informe e pergunte se o usuário tem outro link ou a transcrição.
- **Sem legenda e sem permissão de download:** informe e ofereça as alternativas (transcrição manual, Gemini com chave, outro vídeo).
- **Transmissão ao vivo em andamento:** pergunte se quer o resumo do trecho já disponível ou esperar o encerramento.
- **Playlist ou canal em vez de vídeo único:** pergunte quais vídeos resumir e se quer um consolidado.
- **Shorts:** resuma normalmente, mas avise que o conteúdo é curto e o resumo será proporcionalmente breve.
- **Vídeo sem fala** (só música, ambientação, demonstração visual): informe que não há conteúdo falado a resumir e pergunte se quer uma descrição do que é mostrado, se houver como.
- **Idioma diferente do português:** resuma normalmente em pt-BR, mas registre o idioma original nos metadados.
- **Conteúdo sensível** (política, saúde, finanças, acusações): resuma o que é dito, atribuindo as afirmações ao autor do vídeo, sem endossar nem refutar.
- **Vídeo muito longo** (acima de 2 horas): ver seção anterior.

## Regras de qualidade

- Timestamps devem vir da transcrição, não ser estimados. Se a fonte não tiver tempos, escreva "timestamps indisponíveis" e explique por quê.
- Distinga o que é fala do apresentador do que é citação, propaganda ou fala de convidado.
- Preserve nomes próprios, números e termos técnicos exatamente como aparecem.
- Se a legenda automática tiver erros evidentes de transcrição, corrija apenas quando o contexto tornar a correção óbvia; caso contrário, mantenha e sinalize.
- O resumo deve ser autossuficiente: quem ler sem assistir ao vídeo precisa entender o conteúdo.
- Não inclua opinião própria sobre o mérito do conteúdo, exceto na seção de ressalvas, e mesmo lá de forma factual.

## Arquivos da skill

- `scripts/resumir_video.py` — script autocontido que baixa legendas ou áudio e transcreve.
- `README.md` — requisitos, uso, códigos de saída e limitações.
- `testes.md` — casos de teste para validação.
