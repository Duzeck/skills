# Rodapé e redes sociais

O rodapé é declarado no objeto `footer` do Blueprint (estrutura) e as
redes no objeto `social`. A **estrutura** (colunas, ordem) fica no código
(`project_footer_columns()`); o **conteúdo** (títulos, textos, contatos,
URLs) fica no admin — uma fonte única para header, rodapé e contato.

## 1. Como ler o rodapé na imagem

| Sinal (`footer.evidence`) | O que é |
|---|---|
| `columns` | Colunas lado a lado — registre **cada uma**, na ordem |
| `footer_menu` | Coluna com título ("Links Rápidos", "Nossos Serviços") e lista de links |
| `contact_block` | Endereço, telefone, WhatsApp, e-mail, horário (com ícones) |
| `social_icons` | Ícones de redes — numa coluna própria ou **dentro** de outra (ex.: abaixo do texto "sobre") |
| `newsletter` | Campo de e-mail + botão (vira `forms[]` com `purpose: newsletter`) |
| `legal_row` | Faixa inferior: copyright, CNPJ/razão social, Política de Privacidade, Termos |
| `back_to_top` | Seta/botão "voltar ao topo" |
| `payment_seals` | Bandeiras de pagamento, selos de segurança (ícones; não são logos de clientes) |
| `map` | Mapa no rodapé (`maps[]`) |
| `credit` | "Desenvolvido por …" |

Cada coluna: `{ id, kind, title, social }` — `kind`: `about` (logo +
texto), `menu` (um local de menu próprio, `footer_<id>`), `contact`,
`social`, `newsletter`, `hours`, `custom`; `social: true` quando os ícones
ficam dentro dela.

## 2. O que nunca se inventa

- **URL de rede social**: `social.urls_source: pending` → campos vazios
  no admin; **rede sem URL não aparece** (nada de link `#`).
  Texto no lugar da URL ("URL não informada") é tratado como ausente.
- **CNPJ e razão social**: só com o dado real (`footer.legal.cnpj: shown`
  exige `global_settings.company.cnpj`); obrigatórios em loja virtual
  (Decreto 7.962/2013).
- **Telefone/WhatsApp/e-mail/endereço**: dado global do usuário.
- **Ícone ilegível** na referência: `uncertainty`, não um palpite de rede.

## 3. Implementação (esqueleto)

`footer.php`, `inc/footer.php`, `inc/contact.php`, `inc/social.php`,
`template-parts/footer-column.php`, `template-parts/social-links.php`,
`assets/icons/social/*.svg` (Phosphor, MIT — `LICENSE.txt` ao lado).

| Prática | Por quê |
|---|---|
| Cada coluna é `<section>` nomeada pelo título (h2); menus em `<nav aria-label="<título>">` | Navegação por regiões e títulos |
| Um local de menu **por coluna** de menu | Cada lista editável em Aparência > Menus |
| Contato em `<address>`: `tel:+55…`, `https://wa.me/55…?text=…` (mensagem do admin), `mailto:`, endereço abrindo o mapa | Toca a ligação/abre o WhatsApp no celular; links gerados do dado único (número sem DDD é recusado, não adivinhado) |
| Telefone e WhatsApp iguais → uma linha só | Como as referências mostram (encontrado no teste: o número aparecia duas vezes) |
| Copyright do admin com `{ano}` (`wp_date('Y')`, fuso do site) e `{empresa}` | `date('Y')` é UTC: às 21h de 31/12 já mostraria o ano seguinte; o "2024" da referência é do mockup |
| Política de privacidade = página do núcleo do WordPress (`get_privacy_policy_url()`) | Link só aparece com a página publicada; o scaffold a renomeia para "Política de Privacidade" (nascia "Privacy Policy" — encontrado no teste) |
| Redes: **o mesmo componente** no header, rodapé e contato, na ordem da referência (`project_social_order()`) | Uma fonte; header e rodapé nunca divergem |
| Ícone SVG inline (`currentColor`, `aria-hidden`) + texto "Instagram: <empresa> (abre em nova aba)" | Ícone sozinho não é lido; forma neutra (sem "da/do", que depende do gênero do nome) |
| Ícone trocável no admin (`social_<rede>_icon`) | Requisito de projeto: ícone editável |
| Área de toque ≥ 44px; `rel="noopener me"` | WCAG 2.5.8; `me` sinaliza perfil próprio |
| Sem Font Awesome inteiro de CDN | Centenas de KB por meia dúzia de ícones (`check_theme.py` avisa) |
| JSON-LD **Organization** na Home: nome, logo, `sameAs` (perfis preenchidos), telefone, e-mail, CNPJ (`taxID`) | Liga o site aos perfis oficiais; uso legítimo |
| "Voltar ao topo" (filtro `project_footer_back_to_top`) → `#topo` (header) | Só se a referência mostrar |

## 4. Como validar

`scripts/capture_site.py --blueprint` aponta em toda página: rodapé
ausente (P0); colunas fora da ordem ou com título diferente da
referência; link sem destino no rodapé; link de rede inválido, sem nome
acessível ou sem ícone; mais ícones no rodapé que redes na referência;
`tel:`/`wa.me`/`mailto:` mal formados; sem link da política de
privacidade; copyright sem o ano atual; na Home, sem JSON-LD
Organization ou `sameAs` diferente dos perfis exibidos (P1). Redes no
header **e** no rodapé não geram alarme (a contagem é só do rodapé).

Antes de publicar: preencher as URLs das redes, publicar a política de
privacidade revisada e conferir o rodapé no celular.
