# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

Gerado pela Skill `duzeck-wordpress-site-builder` a partir de
`documentation/BLUEPRINT.yaml`.

## Requisitos

- WAMP (Apache, MySQL, PHP {{PHP_VERSION}}+)
- WP-CLI
- Plugin ACF PRO (licenciado separadamente)
- Plugin Contact Form 7 (se o projeto tiver formulário)

## Instalação local

```
cd C:\wamp64\www\{{SLUG}}
# já criado pelo scripts/scaffold_wp_project.py — ver abaixo se precisar recriar
```

URL local: `http://localhost/{{SLUG}}/`
Admin: `http://localhost/{{SLUG}}/wp-admin/`

## Estrutura do tema

Ver `wp-content/themes/{{SLUG}}-theme/` — organização descrita em
`references/wordpress-architecture.md` da Skill.

## Custom Post Types

{{TABELA_CPTS}}

## Campos (ACF)

{{TABELA_CAMPOS}}

## Taxonomias

{{TABELA_TAXONOMIAS}}

## Configurações globais

Editáveis em **Configurações Globais** no admin (ACF Options Page):
logo, telefone, WhatsApp, e-mail, endereço, horário, redes sociais, cores
de marca, CTA padrão.

## Menus

{{TABELA_MENUS}}

## Conteúdo demo

Ver `documentation/VALIDATION.md` → seção "Conteúdo demo identificado"
para a lista do que é demonstrativo e precisa ser substituído por conteúdo
real antes de publicar.

## Manutenção

- Decisões arquiteturais: `documentation/DECISIONS.md`
- Histórico de versões do Blueprint: `documentation/blueprint-history/`
- Resultados de validação: `documentation/VALIDATION.md`

Mudanças que afetem CPT, campo, taxonomia, relacionamento, plugin,
template ou fluxo funcional devem gerar uma nova versão do Blueprint antes
de serem implementadas — não edite a arquitetura diretamente no código sem
atualizar o Blueprint correspondente.
