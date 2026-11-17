# Vídeos

Todo vídeo da referência entra em `videos[]` do Blueprint; sem nenhum,
`videos: []` registra que a conferência foi feita.

## 1. Como identificar

| Sinal (`evidence`) | O que é |
|---|---|
| `play_button` | Triângulo ▶ (em círculo ou não) sobre uma imagem |
| `duration_badge` | "3:45" num canto da imagem |
| `progress_bar` | Barra de progresso / controles de player na base |
| `provider_logo` | Logo do YouTube/Vimeo, título do vídeo no topo da imagem |
| `watch_cta` | "Assista ao vídeo", "Veja como trabalhamos" com ▶ |
| `user` | O usuário disse |

**Vídeo de fundo** (hero com vídeo rodando atrás do texto) é
indistinguível de uma foto numa imagem estática: só existe com
confirmação do usuário (`evidence: [user]`) — nunca presuma.

Não é vídeo: ícone ▶ em botão de link para outra página ("Ver projeto ▶"),
ícone do YouTube nas redes sociais (é link de rede social).

## 2. O que decidir

| Decisão | Campo | Observação |
|---|---|---|
| Tipo | `kind` | `embed` (YouTube/Vimeo), `file` (arquivo na Biblioteca, com controles), `background` (decorativo, mudo, em loop) |
| Fonte | `source` + `url_field`/`file_field` | URL colada no admin (qualquer formato: watch, youtu.be, shorts, vimeo) ou arquivo. **Pergunte** a URL/arquivo — nunca invente um vídeo |
| Capa | `poster_media` | O frame que aparece na referência (recorte provisório) ou capa enviada pelo admin |
| Nome acessível | `title_field` / `title` | "Reproduzir vídeo: <título>" |
| Legendas | `captions` | **Pergunte**: o vídeo tem fala ou informação só em áudio? Então precisa de legenda (WCAG 1.2.2). YouTube/Vimeo: legenda no provedor; arquivo: `captions_field` com `.vtt` |
| Carregamento | `load` | `click` (fachada). `auto` só com decisão aprovada |
| Proporção | `aspect_ratio` | A da região na referência |

Vídeo de fundo: arquivo **curto** (5–15 s), **sem áudio**, WebM (VP9) +
MP4 (H.264) como segunda fonte, idealmente < 3 MB; a capa é obrigatória
(é o que aparece no celular e com movimento reduzido).

## 3. Implementação (`template-parts/video.php` + `inc/video.php` + `assets/js/video.js`)

| Prática | Por quê |
|---|---|
| **Fachada** (embed): capa + botão play; o player entra só no clique | O player do YouTube baixa ~1 MB e define cookies/armazenamento; sem o clique nada disso acontece (LGPD, LCP, INP) |
| `youtube-nocookie.com` / Vimeo `dnt=1`, `autoplay=1` só depois do clique | Modo de privacidade reforçada; o clique já foi o "play" |
| Sem JS, o play é um link para o vídeo no provedor | Progressive enhancement |
| Só URLs de YouTube/Vimeo (domínio conferido) viram iframe | Nada de iframe arbitrário vindo de campo de texto |
| `iframe title`, foco vai para o player após o clique | Nome acessível; teclado não perde a posição |
| Arquivo próprio: `<video controls preload="none" playsinline poster>` + `<track kind="captions">` | Nada baixa até o play; capa e legenda nativas |
| Fundo **sem** atributo `autoplay`: o JS só toca se não houver `prefers-reduced-motion`, nem economia de dados (`saveData`), e a tela tiver ≥ 768px | Respeita a preferência do sistema; no celular fica a capa e o arquivo nem é baixado |
| Com movimento reduzido: começa pausado e o botão permite dar play | A escolha é do visitante |
| Botão de pausa visível (WCAG 2.2.2), pausa fora da tela e com a aba oculta | Movimento que dura > 5 s precisa ser pausável; não gasta CPU/bateria à toa |
| Capa como `<img>` (LCP, `srcset`) sob o vídeo; o vídeo aparece só quando toca | Primeira pintura rápida e nítida; sem tela preta enquanto carrega |
| Vídeo de fundo `aria-hidden` | É decoração; o conteúdo está no texto sobre ele |
| JS só registrado; o template-part enfileira | Página sem vídeo não baixa nada |

`check_theme.py` bloqueia iframe de YouTube/Vimeo fixo e `<video autoplay>`
escrito à mão.

## 4. Como validar

`scripts/capture_site.py --blueprint` (com movimento reduzido) aponta:
vídeo ausente (P0); player carregado antes do clique, embed sem modo de
privacidade, play sem nome acessível, clique que não carrega, player sem
`title`; arquivo sem controles/capa/legenda pedida; vídeo de fundo
tocando com movimento reduzido, sem `aria-hidden`, sem botão de pausa ou
baixado no celular (P1).

Interativo: sem movimento reduzido, o fundo toca no desktop, pausa no
botão e fora da tela; com movimento reduzido, dar play pelo botão
funciona; a legenda aparece no player; nenhuma requisição ao
YouTube/Vimeo antes do clique (aba Rede).
