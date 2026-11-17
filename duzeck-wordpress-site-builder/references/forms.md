# Formulários

Todo formulário da referência vira uma entrada estruturada em `forms[]`
do Blueprint. Dela saem o formulário do Contact Form 7
(`scripts/build_cf7_form.py`), o template (`project_form()`) e as
checagens do QA. Nada é digitado à mão no CF7 na primeira versão.

## 1. Como ler o formulário na imagem

Para cada formulário, de cima para baixo, registre:

| O que olhar | Vai para | Observação |
|---|---|---|
| Para que serve (título/botão: "Fale conosco", "Solicite orçamento", "Assine", "Agende", "Envie seu currículo") | `purpose` | contact / quote / newsletter / booking / job_application / other |
| Cada caixa, na ordem | `fields[]` | Um objeto por campo |
| Texto acima/ao lado da caixa | `label` | **Literal**, com acentos |
| Texto cinza dentro da caixa | `placeholder` | Literal. Sem rótulo visível → `label` = o mesmo texto e `label_visible: false` (o rótulo existe para leitor de tela; placeholder sozinho não é rótulo) |
| Asterisco, "(obrigatório)" | `required` + `required_marker` | Sem marca visível, pergunte quais são obrigatórios (padrão sensato: nome, e-mail e mensagem) |
| Formato da caixa | `type` | Caixa alta → `textarea`; seta ▾ → `select`; quadradinho → `checkbox`; bolinha → `radio`; "Anexar"/clipe → `file`; ícone de calendário → `date` |
| Opções visíveis de select/checkbox/radio | `options` | Ilegíveis ou escondidas (select fechado) → **pergunte** |
| Dois campos na mesma linha | `width: half` | Layout vem da referência |
| Texto do botão, ícone no botão | `submit_label`, `submit_icon` | Literal |
| Caixinha "Li e aceito…" / texto sobre privacidade | `privacy` | Ver seção 3 |

Tipo de dado → `autocomplete` (WCAG 1.3.5): nome `name`, e-mail `email`,
telefone `tel`, empresa `organization`, CEP `postal-code`, cidade
`address-level2`.

Nomes de campo (`name`): minúsculos, sem acento, com prefixo do formulário
(`contato_nome`, `orcamento_cidade`). **Nunca** um termo reservado do
WordPress (`name`, `year`, `day`, `page`, `type`, `s`, `p`, `m`, `order`,
`author`...): sem JS o CF7 envia para a própria página e o WordPress
responde 404 (o validador bloqueia).

## 2. O que nunca se inventa

- **Destino** (`destination`): o e-mail que recebe as mensagens. Não
  informado → `uncertainty` bloqueante com `subject` = id do formulário.
  O gerador se recusa a criar o formulário sem ele.
- **Opções** de select que a imagem não mostra.
- **Integrações** (CRM, planilha, WhatsApp API, e-mail marketing da
  newsletter): só com pedido explícito e credenciais do usuário.

## 3. Privacidade (LGPD)

Formulário coleta dado pessoal: precisa de aviso com link para a
política de privacidade (`privacy`):

- `notice: checkbox` — caixinha obrigatória ("Li e concordo com a
  política de privacidade"); use quando houver uso além de responder
  (newsletter, marketing, currículo);
- `notice: text` — frase junto ao botão ("Ao enviar, você concorda com
  a nossa Política de Privacidade"); suficiente para contato simples;
- `policy_page`: slug da página (em `pages[]` com `role: auxiliary`);
- referência sem aviso → `shown_in_reference: false` e desvio intencional
  aprovado (discreto, no estilo dos textos pequenos da referência).

## 4. Anti-spam

`anti_spam` é decisão do Blueprint: `akismet` (padrão; o CF7 integra
nativamente, precisa da chave do Akismet), `recaptcha_v3` ou `turnstile`
(integração do CF7, precisa das chaves do usuário). `none_local` só
enquanto o site não está publicado — o validador avisa.

## 5. Implementação

1. `scaffold_wp_project.py` instala o CF7 com a tradução e liga
   `WP_ENVIRONMENT_TYPE=local` + o mu-plugin de log de e-mail.
2. `python scripts/build_cf7_form.py --blueprint ... --form <id> --print`
   para revisar; depois com `--project <pasta>` para criar/atualizar.
   O gerador produz:
   - `<label for>` ligado a cada campo, rótulo invisível com
     `screen-reader-text` quando a referência só tem placeholder;
   - checkbox/radio em `<fieldset><legend>`;
   - `autocomplete`, obrigatórios com `*` na tag (o CF7 põe
     `aria-required`), asterisco visual `aria-hidden`;
   - `.form-grid` / `.form-field--half` para o layout de colunas;
   - botão `<button>` (aceita ícone), aviso de privacidade com link;
   - e-mail com `Reply-To` do visitante e corpo "Rótulo: [campo]".
3. No template: `project_form('<campo de opções>')` — o campo
   (post_object do CF7 na página de opções) diz qual formulário aparece;
   o padrão em `content-defaults.php` é o slug (= `forms[].id`). Nunca
   `[contact-form-7 id="..."]` fixo (`check_theme.py` bloqueia).
4. `inc/forms.php` desliga o `<p>/<br>` automático do CF7 e carrega o
   JS/CSS dele só nas páginas com formulário.
5. Visual dos campos, foco, erro e mensagem de retorno: da referência.
   Erro nunca só por cor — o CF7 escreve a mensagem junto ao campo
   (`aria-invalid` + `aria-describedby`); a resposta geral é região
   `aria-live`. O CF7 deixa o foco no botão após um envio inválido: o
   `main.js` do esqueleto move o foco para o primeiro campo inválido
   (evento `wpcf7invalid`, que chega antes de o CF7 marcar os campos — por
   isso ele usa `detail.apiResponse.invalid_fields`).

Editável no admin: campos, textos e destinatário em **Contato >
Formulários**; `editable_content` da seção com `storage: form`.

## 6. Produção

O log local não vai para produção (o mu-plugin só age com
`WP_ENVIRONMENT_TYPE=local`). Antes de publicar: SMTP autenticado
(ex.: WP Mail SMTP com o provedor do cliente), SPF/DKIM do domínio,
`anti_spam` real e um envio de teste para o destinatário — registre no
README do projeto.

## 7. Como validar

`scripts/capture_site.py --blueprint ... --submit-forms --mail-log
<projeto>/wp-content/local-mail`:

- formulário ausente, campo ausente, tipo errado, obrigatório sem
  `aria-required`, sem rótulo acessível, placeholder ou texto do botão
  diferente da referência;
- envio real (desktop): preenche com dados de teste, envia e exige
  status `sent` do CF7;
- o log tem um e-mail novo **para o destinatário do Blueprint**.

Interativo (claude-in-chrome): enviar vazio (mensagens de erro junto a
cada campo, foco vai para o primeiro inválido), e-mail inválido, Tab por
todos os campos, envio só pelo teclado, mensagem de sucesso lida.
