# Arquitetura WordPress

## Estrutura do projeto

```
<slug>/
├── wp-config.php
├── wp-content/
│   ├── themes/
│   │   └── <slug>-theme/
│   │       ├── style.css
│   │       ├── functions.php
│   │       ├── front-page.php
│   │       ├── page.php
│   │       ├── single.php
│   │       ├── archive.php
│   │       ├── single-<cpt>.php        (um por CPT com single habilitado)
│   │       ├── archive-<cpt>.php       (um por CPT com archive habilitado)
│   │       ├── header.php
│   │       ├── footer.php
│   │       ├── 404.php
│   │       ├── index.php
│   │       ├── template-parts/
│   │       │   ├── hero.php
│   │       │   ├── card-service.php
│   │       │   ├── card-project.php
│   │       │   ├── testimonial.php
│   │       │   ├── cta.php
│   │       │   └── ...
│   │       ├── inc/
│   │       │   ├── post-types.php
│   │       │   ├── taxonomies.php
│   │       │   ├── acf-fields.php
│   │       │   ├── acf-options.php
│   │       │   ├── menus.php
│   │       │   ├── enqueue.php
│   │       │   └── demo-content.php
│   │       └── assets/
│   │           ├── css/
│   │           │   ├── tokens.css   (GERADO de design.tokens — não editar à mão)
│   │           │   └── style.css    (só var(--...), nunca cor/medida literal)
│   │           ├── img/             (assets fornecidos e recortes provisórios)
│   │           └── js/
│   └── plugins/              (apenas plugins de terceiros, não o tema)
├── documentation/
│   ├── README.md
│   ├── BLUEPRINT.yaml
│   ├── blueprint-history/
│   ├── DECISIONS.md
│   └── VALIDATION.md
└── tests/
```

Nunca coloque toda a lógica de CPTs/campos/taxonomias dentro de
`functions.php` — um único arquivo gigante dificulta manutenção e
revisão. Separe por responsabilidade em `inc/`, e faça `functions.php`
apenas `require` desses arquivos.

## Stack e dependências

Priorizar sempre: WordPress, PHP, HTML, CSS, JavaScript, ACF PRO, Custom
Post Types nativos, taxonomias nativas, Settings API / ACF Options Page,
menus nativos. Evitar frameworks CSS/JS pesados — CSS puro ou Sass simples
é suficiente para a maioria dos layouts institucionais.

## Shortlist de plugins padrão

Só use plugin fora desta lista se o layout exigir algo que ela não cobre,
e sempre justificando no Blueprint (`plugins.required[].reason`):

| Plugin | Finalidade | Quando usar |
|---|---|---|
| Advanced Custom Fields PRO | Campos customizados, repeaters, galeria, relacionamento, Options Page | Sempre que houver campo estruturado além de título/conteúdo padrão |
| Contact Form 7 | Formulário de contato | Padrão deste ambiente para qualquer formulário de contato/orçamento |

**Nota sobre edição programática de formulários do Contact Form 7**: o
template do formulário renderizado no front-end vem da postmeta `_form`,
não de `post_content` (que existe mas não é lido na renderização em CF7
6.x). Para editar labels/campos via `wp eval`/`wp eval-file`, atualize
`_form` com `update_post_meta($id, '_form', $novo_conteudo)`. O
destinatário do e-mail fica em `_mail` (array serializado, chave
`recipient`), não em `post_content`.

Qualquer outro plugin (SEO, cache, segurança, builders visuais) é
`optional` ou `prohibited` por padrão — só promova a `required` se o
usuário pedir explicitamente ou o requisito não puder ser atendido sem
ele, registrando a razão.

## Tema: classic vs. block

Default: **classic theme**, pelo controle preciso de HTML/CSS/templates
que a reprodução fiel de uma referência visual exige. Só proponha tema de
blocos (FSE) se o usuário pedir explicitamente edição via Site Editor.

## Justificativa de dependências

Toda entrada em `plugins.required` ou `dependencies` deve ter uma frase de
`reason` que um humano não-técnico entenda. Não é suficiente dizer
"necessário para campos" — diga "necessário para o administrador poder
editar a galeria de fotos de cada projeto sem mexer em código".
