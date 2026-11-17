# Acessibilidade — baseline WCAG AA

Esta é uma checagem de baseline, não uma auditoria WCAG completa. Objetivo:
evitar os erros mais comuns e mais fáceis de prevenir desde a implementação.

## Checklist

- **HTML semântico**: usar `<header>`, `<nav>`, `<main>`, `<section>`,
  `<footer>`, `<article>` em vez de `<div>` genérico para estrutura
  principal da página.
- **Hierarquia de headings**: um único `<h1>` por página, sem pular níveis
  (não ir de `<h2>` direto para `<h4>`).
- **Alt text**: toda imagem de conteúdo tem `alt` descritivo; imagem
  puramente decorativa usa `alt=""`.
- **Labels de formulário**: todo campo de formulário tem `<label>`
  associado (via `for`/`id`), não apenas `placeholder`.
- **Navegação por teclado**: links, botões e campos de formulário devem
  ser alcançáveis e operáveis via Tab/Enter, sem depender de hover/mouse.
- **Foco visível**: não remover o outline de foco (`outline: none`) sem
  fornecer um estilo de foco alternativo visível.
- **Contraste**: texto sobre fundo deve atingir pelo menos 4.5:1 (texto
  normal) ou 3:1 (texto grande/títulos) — checar principalmente em CTAs
  com fundo colorido e texto branco/claro.
- **Propósito do link**: evitar texto de link genérico tipo "clique aqui";
  preferir texto que descreva o destino ("Ver projeto", "Fale conosco").

## Quando registrar como uncertainty em vez de decidir

Se a referência visual tiver um contraste de cor claramente abaixo do
mínimo (ex.: cinza claro sobre branco em texto pequeno), não "corrija
silenciosamente" mudando a cor da marca — registre como decisão proposta
("ajustar X para Y por motivo de contraste/acessibilidade") e pergunte,
porque isso pode entrar em conflito com a identidade visual aprovada.
