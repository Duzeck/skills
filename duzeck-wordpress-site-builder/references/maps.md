# Mapas

Todo mapa da referência entra em `maps[]` do Blueprint; sem nenhum,
`maps: []` registra que a conferência foi feita.

## 1. Como identificar

| Sinal (`evidence`) | O que é |
|---|---|
| `tiles` | Ruas, quarteirões, áreas verdes/água em tons claros de cartografia |
| `pin` | Marcador (gota vermelha, ícone da marca) sobre o mapa |
| `zoom_controls` | Botões + / − no canto |
| `provider_logo` | "Google", "© OpenStreetMap", "Mapbox" no rodapé do mapa |
| `view_larger_link` | "Ver mapa ampliado", "Abrir no Maps", "Como chegar" |
| `user` | O usuário disse |

Não é mapa interativo: ilustração estilizada de mapa (sem ruas reais),
mapa do Brasil com estados destacados ("onde atuamos") — isso é imagem
(`media[]`) ou SVG, não embed. Na dúvida, pergunte.

## 2. O que decidir

| Decisão | Campo | Padrão |
|---|---|---|
| Endereço | `address_field` | Campo da página de opções (o mesmo do rodapé/contato) — **fonte única**; nunca endereço fixo no template. Endereço não informado → `uncertainty` bloqueante (não invente) |
| Provedor | `provider` | `google` (embed por endereço, sem chave de API). `openstreetmap` exige coordenadas (`lat_field`, `lng_field`) |
| Mapa exato do Google | `embed_field` | Opcional: o admin cola o código de "Compartilhar > Incorporar um mapa" (o tema extrai só a URL e só aceita domínio de mapa conhecido) |
| Carregamento | `load` | `click` — fachada + "Carregar mapa". `auto` só com decisão aprovada (ex.: já existe banner de consentimento) |
| Imagem antes do clique | `facade_media` | Entrada em `media[]`: recorte da referência (provisório) ou print estático do endereço real enviado pelo admin |
| Proporção | `aspect_ratio` | A da região do mapa na referência |
| "Como chegar" | `directions_link` | `true` |

## 3. Implementação (`template-parts/map.php` + `inc/maps.php` + `assets/js/map.js`)

| Prática | Por quê |
|---|---|
| **Fachada**: imagem estática + botão; o iframe só entra no clique | O embed baixa ~1 MB de scripts de terceiros e grava cookies do provedor. Sem o clique isso não acontece sem o visitante pedir (LGPD) e a página não paga o custo no carregamento (LCP, INP) |
| Sem JS, "Carregar mapa" é um link que abre o mapa em nova aba | Progressive enhancement |
| Aviso "Ao carregar, o Google Maps pode usar cookies" junto ao botão | Transparência antes da escolha |
| `<iframe title="Mapa: <endereço>">`, `loading="lazy"`, `referrerpolicy` | Nome acessível (WCAG 4.1.2); carrega só perto da tela |
| Foco vai para o mapa após o clique | Quem usa teclado não perde a posição |
| Link "Como chegar" (Maps URLs oficiais, `dir/?api=1&destination=`) | Alternativa acessível ao mapa (iframe de mapa não é navegável por leitor de tela) e abre o app de mapas no celular |
| Endereço também em **texto** na página | O mapa nunca é a única forma de saber onde fica |
| Proporção fixa (`aspect-ratio`) para fachada e iframe | Sem salto de layout ao carregar |
| `map.js` só registrado; o template-part enfileira | Páginas sem mapa não baixam nada |
| Sem chave de API | Nada de credencial/cobrança; chave só se o usuário pedir recursos de API (vários pinos, estilo customizado) |

Visual da fachada e do botão: da referência. A fachada da referência
(recorte) é provisória e vai para "Conteúdo demo identificado" — no
lançamento, o admin envia um print do endereço real.

## 4. Como validar

`scripts/capture_site.py --blueprint` aponta: mapa ausente (P0); iframe
carregado antes do clique, sem botão "Carregar mapa", clique que não
carrega, iframe sem `title`, "Como chegar" ausente ou sem destino (P1).

Interativo: o pin aponta para o endereço do admin; trocar o endereço em
Configurações do Site muda o mapa e o "Como chegar"; ativar pelo teclado
(Tab + Enter) carrega o mapa e põe o foco nele.
