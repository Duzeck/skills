# Equipe e números em destaque

Todo bloco de equipe entra em `team[]` e todo bloco de números em
destaque em `stats[]`; sem nenhum, `team: []` / `stats: []` registram que
a conferência foi feita.

## 1. Mesma regra da prova social: o da referência é mockup

- **Equipe**: pessoas da referência quase sempre são foto de banco de
  imagem (ou rosto gerado por IA) com nome inventado. Real só com nomes,
  fotos e **autorização de uso de imagem** de cada pessoa
  (`content_source: user` + `consent: true` — LGPD).
- **Números**: "+500 obras", "100% de clientes satisfeitos", "nº 1 da
  região" são **afirmações de negócio** — o CDC e o CONAR exigem que
  sejam comprováveis. Real só com valores confirmados pelo usuário
  (`content_source: user`).
- Senão, `demo`: os template-parts recebem `demo => true` e **não
  renderizam em produção** (mesma trava de `inc/social-proof.php`).

## 2. Como identificar

**Equipe** (`evidence`): `headshots` (grade de fotos de rosto, mesma
proporção), `name_role` (nome + cargo embaixo), `social_icons` (LinkedIn,
Instagram por pessoa), `section_title` ("Nossa equipe", "Quem faz
acontecer", "Corpo clínico"), `hover_bio` (foto que revela texto no
hover), `user`.

**Números** (`evidence`): `big_number` (número grande), `prefix_suffix`
("+", "%", " mil", "k", "anos"), `label_below` (rótulo pequeno), `icon`
(ícone por número), `user`. Normalmente 3 ou 4 em fileira, muitas vezes
numa faixa colorida.

Não confundir: números dentro de um **preço** (`pricing`), **passos
numerados** ("1. Contato, 2. Projeto, 3. Obra" — processo), **contador do
carrossel** ("01 / 05"), **tabela de dados** (`tables`).

## 3. O que registrar e perguntar

| Campo | Da imagem | Pergunte |
|---|---|---|
| `member_count`, `total_count` | Pessoas visíveis; "ver equipe completa" | Total da equipe |
| `fields_shown` (equipe) | `photo`, `role`, `bio`, `social`, `registration` | — |
| `registration` | Setor do cliente | Saúde (CRM/CRO/CRP/CRN/CREFITO/COREN), direito (OAB), engenharia/arquitetura (CREA/CAU), contabilidade (CRC), imóveis (CRECI): **o número nunca é inventado** — ex.: o CFM exige CRM (e RQE para especialidade) em publicidade médica |
| `bio` | Bio visível ou revelada no hover | `visible` ou `collapsed` (`<details>` "Sobre <nome>") — **nunca só no hover** |
| `profile_pages` | — | Cada pessoa tem página própria? (CPT público com single) |
| `item_count` (números) | Contagem | — |
| `count_up` | **Não aparece** numa imagem estática | Anima de 0 até o valor? Nunca presumir |
| Valores | Só o layout | Os números reais e comprováveis |

Modelagem: equipe em CPT `team_member` (campos prefixados — ver
`content-modeling.md`; ordem por `menu_order`); números em repeater
(`valor` número, `prefixo`, `sufixo`, `rótulo`, `ícone`).

## 4. Implementação (esqueleto)

`template-parts/team.php`, `template-parts/stats.php`, `assets/js/stats.js`
(e `inc/social-proof.php` para a trava de demo).

| Prática | Por quê |
|---|---|
| Card `<article aria-labelledby>` com o nome como título (h3) | Navegação por títulos lista a equipe |
| Foto com `alt=""` | Decorativa: o nome está escrito ao lado |
| Registro profissional em texto | Exigência de conselhos; legível e indexável |
| Bio `visible` ou `<details>` "Sobre <nome>" | Hover não existe no teclado nem no toque |
| Rede social: ícone `aria-hidden` + "LinkedIn de Ana Lima (abre em nova aba)"; rede detectada pela URL | Cinco links "LinkedIn" iguais não dizem de quem são |
| Área de toque ≥ 44px nos ícones | WCAG 2.5.8 |
| Número: **valor final no HTML** (texto para leitor de tela + cópia visual `aria-hidden`) | Buscador, leitor de tela e quem está sem JS sempre têm o valor certo |
| Formato brasileiro ("12.500", "1,2 mil"), casas decimais do valor informado | "1,2" não vira "1" nem "1,20" |
| Contagem (`count_up`) só na cópia visual, **uma vez**, ao entrar na tela (`IntersectionObserver`), com desaceleração | Não reanima a cada rolagem |
| Termina **exatamente** no texto do servidor (guardado antes de zerar) | Encontrado no teste: guardar depois de zerar deixava "+0" para sempre |
| Largura reservada: `min-width` em `ch` no HTML e, com JS, a largura **medida** do valor final | `ch` não cobre "+", "%", "m²" — sem a medida o layout pulava durante a contagem (encontrado no teste) |
| Nada de contagem com `prefers-reduced-motion` | WCAG 2.3.3 |
| `stats.js` só registrado; enfileirado só com `count_up` | Página sem contagem não baixa nada |

`check_theme.py` avisa contador de terceiros (countUp, counterUp,
odometer).

## 5. Como validar

`scripts/capture_site.py --blueprint` (movimento reduzido) aponta: bloco
ausente (P0; demo em produção fica oculto de propósito); contagem de
pessoas/números, pessoa sem nome, cargo, foto, registro ou bio pedidos,
bio só no hover, rede sem o nome da pessoa; número sem valor final no
HTML, sem rótulo, contagem diferente do Blueprint, animando com
movimento reduzido ou mostrando valor diferente do final (P1).

Interativo (sem movimento reduzido): a contagem começa só ao entrar na
tela, termina no valor exato, não empurra o layout e não reanima;
"Sobre <nome>" abre pelo teclado.
