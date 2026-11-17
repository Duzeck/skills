#!/usr/bin/env python3
"""
Gera o formulario do Contact Form 7 a partir de forms[] do BLUEPRINT.yaml
(references/forms.md) e o grava no WordPress pela API do proprio CF7.

Uso:
    python build_cf7_form.py --blueprint documentation/BLUEPRINT.yaml --form contact --print
    python build_cf7_form.py --blueprint documentation/BLUEPRINT.yaml --form contact \
        --project C:/wamp64/www/<slug>

    --print     so mostra o template do formulario e o e-mail (nao grava nada)
    --project   pasta do WordPress: cria/atualiza o formulario (slug = forms[].id)

O que sai do Blueprint, sem reinterpretar:
- rotulo e placeholder LITERAIS da referencia (rotulo invisivel na
  referencia -> <label class="screen-reader-text">, nunca so placeholder);
- obrigatoriedade (tag com *), autocomplete, opcoes de select/checkbox/radio,
  limite e tipos de arquivo, largura (form-field--half);
- aviso de privacidade (LGPD) com link para a politica;
- texto do botao (<button>, com gancho de icone se submit_icon) e asterisco
  de obrigatorio (required_marker) quando a referencia mostra;
- e-mail: destinatario = forms[].destination, Reply-To = campo de e-mail
  do visitante, corpo com "Rotulo: [campo]" na ordem do formulario.

Rodar de novo ATUALIZA o mesmo formulario (procura pelo slug). Ajustes
feitos depois no admin (Contato > Formularios) sao sobrescritos - rode
so na criacao ou quando o Blueprint mudar.

Exit code: 0 ok | 1 Blueprint invalido para gerar | 2 erro ao gravar.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _wpcli  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import yaml
except ImportError:
    print("Erro: PyYAML nao esta instalado. Rode: pip install pyyaml")
    sys.exit(2)

POLICY_TOKEN = "%%POLICY_URL%%"
CF7_TYPES = {
    "text": "text", "email": "email", "tel": "tel", "url": "url", "number": "number",
    "date": "date", "textarea": "textarea", "select": "select", "checkbox": "checkbox",
    "radio": "radio", "file": "file",
}
GROUP_TYPES = {"checkbox", "radio"}
PURPOSE_LABELS = {
    "contact": "Contato", "quote": "Orçamento", "newsletter": "Newsletter",
    "booking": "Agendamento", "job_application": "Trabalhe conosco", "other": "Formulário",
}


def quote(text):
    """Valor entre aspas numa tag do CF7 (aspas internas viram tipograficas)."""
    return '"' + str(text).replace('"', "\u201d").strip() + '"'


def html(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def field_tag(form_id, f):
    ftype = f["type"]
    name = f["name"]
    tag = CF7_TYPES[ftype] + ("*" if f.get("required") and ftype != "radio" else "")
    parts = [tag, name]
    if ftype not in GROUP_TYPES:
        parts.append(f"id:{form_id}-{name}")
    if f.get("autocomplete"):
        parts.append(f"autocomplete:{f['autocomplete']}")
    if ftype == "file":
        if f.get("max_size"):
            parts.append(f"limit:{f['max_size']}")
        if f.get("accept"):
            parts.append("filetypes:" + "|".join(str(x).lstrip(".") for x in f["accept"]))
    if ftype in GROUP_TYPES:
        parts.append("use_label_element")
        if ftype == "radio":
            parts.append("default:1")
    options = [quote(o) for o in f.get("options") or []]
    if ftype == "select" and f.get("placeholder"):
        parts.append("first_as_label")
        options.insert(0, quote(f["placeholder"]))
    elif f.get("placeholder") and ftype not in {"select", "file"} | GROUP_TYPES:
        parts += ["placeholder", quote(f["placeholder"])]
    return "[" + " ".join(parts + options) + "]"


def build_template(form):
    fid = form["id"]
    marker = form.get("required_marker")
    lines = ['<div class="form-grid">']
    for f in form["fields"]:
        width = " form-field--half" if f.get("width") == "half" else ""
        css = f"form-field form-field--{f['name']}{width}"
        label = html(f["label"])
        if marker and f.get("required"):
            # O CF7 ja marca aria-required; o asterisco visual nao e lido.
            label += f' <span class="form-required" aria-hidden="true">{html(marker)}</span>'
        hidden = "" if f.get("label_visible", True) else ' class="screen-reader-text"'
        tag = field_tag(fid, f)
        if f["type"] in GROUP_TYPES:
            legend_cls = "" if f.get("label_visible", True) else ' class="screen-reader-text"'
            lines.append(f'<div class="{css}"><fieldset><legend{legend_cls}>{label}</legend>{tag}</fieldset></div>')
        else:
            lines.append(f'<p class="{css}"><label for="{fid}-{f["name"]}"{hidden}>{label}</label>{tag}</p>')
    privacy = form.get("privacy") or {}
    if privacy.get("notice") == "checkbox":
        text = html(privacy.get("text", ""))
        link = html(privacy.get("link_text", "política de privacidade"))
        lines.append(
            f'<p class="form-field form-field--privacy">[acceptance {fid}_privacidade] {text} '
            f'<a href="{POLICY_TOKEN}" target="_blank" rel="noopener">{link}</a>. [/acceptance]</p>'
        )
    elif privacy.get("notice") == "text":
        text = html(privacy.get("text", ""))
        link = html(privacy.get("link_text", "política de privacidade"))
        lines.append(f'<p class="form-field form-field--privacy">{text} <a href="{POLICY_TOKEN}" target="_blank" rel="noopener">{link}</a>.</p>')
    # <button> (e nao [submit], que gera <input>): aceita icone como na referencia.
    icon = '<span class="form-submit__icon" aria-hidden="true"></span>' if form.get("submit_icon") else ""
    lines.append(
        '<p class="form-field form-field--submit"><button type="submit" class="wpcf7-form-control wpcf7-submit">'
        f'{html(form["submit_label"])}{icon}</button></p>'
    )
    lines.append("</div>")
    return "\n".join(lines)


def build_mail(form):
    fields = form["fields"]
    body = [f"{f['label']}: [{f['name']}]" for f in fields if f["type"] != "file"]
    body += ["", "--", f"Enviado pelo formulário \"{PURPOSE_LABELS.get(form.get('purpose'), 'Formulário')}\" de [_site_title] ([_url])"]
    subject_field = next((f["name"] for f in fields if f["name"] == form.get("subject_field")), None)
    subject = f"[_site_title] - {PURPOSE_LABELS.get(form.get('purpose'), 'Formulário')}"
    if subject_field:
        subject += f": [{subject_field}]"
    reply = form.get("reply_to_field")
    return {
        "recipient": str(form["destination"]).strip(),
        "subject": subject,
        "body": "\n".join(body),
        "additional_headers": f"Reply-To: [{reply}]" if reply else "",
        "attachments": "\n".join(f"[{f['name']}]" for f in fields if f["type"] == "file"),
    }


def problems(form):
    out = []
    if not form.get("destination") or "@" not in str(form.get("destination")):
        out.append("destination ausente/invalido - o e-mail de destino nunca e inventado (pergunte ao usuario).")
    if not form.get("submit_label"):
        out.append("submit_label ausente (texto literal do botao na referencia).")
    fields = form.get("fields") or []
    if not fields or not all(isinstance(f, dict) for f in fields):
        out.append("fields deve ser uma lista de objetos (schema 1.5).")
        return out
    for f in fields:
        if f.get("type") not in CF7_TYPES:
            out.append(f"campo {f.get('name')!r}: type {f.get('type')!r} sem equivalente no CF7.")
        if not f.get("name") or not f.get("label"):
            out.append(f"campo {f.get('name')!r}: name e label sao obrigatorios.")
    if (form.get("privacy") or {}).get("notice") in {"checkbox", "text"} and not (form.get("privacy") or {}).get("policy_page"):
        out.append("privacy.policy_page ausente (slug da politica de privacidade).")
    return out


PHP_APPLY = r"""<?php
$data = json_decode(file_get_contents(getenv('PROJECT_CF7_JSON')), true);
if (!class_exists('WPCF7_ContactForm')) { fwrite(STDERR, "Contact Form 7 nao esta ativo.\n"); exit(1); }
$found = get_posts(['post_type' => 'wpcf7_contact_form', 'name' => $data['slug'], 'post_status' => 'any', 'numberposts' => 1]);
$cf = $found ? wpcf7_contact_form($found[0]->ID) : WPCF7_ContactForm::get_template(['title' => $data['title'], 'locale' => get_locale()]);
$cf->set_title($data['title']);
$props = $cf->get_properties();
$policy = $data['policy_page'] ? home_url('/' . trim($data['policy_page'], '/') . '/') : home_url('/');
$props['form'] = str_replace($data['token'], esc_url($policy), $data['form']);
$props['mail'] = array_merge($props['mail'], $data['mail']);
$cf->set_properties($props);
$id = $cf->save();
wp_update_post(['ID' => $id, 'post_name' => $data['slug']]);
echo ($found ? 'atualizado' : 'criado') . " formulario #$id (slug {$data['slug']})\n";
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--blueprint", required=True)
    ap.add_argument("--form", required=True, help="forms[].id")
    ap.add_argument("--project", help="pasta do WordPress (grava o formulario)")
    ap.add_argument("--print", action="store_true", dest="show")
    args = ap.parse_args()

    bp = yaml.safe_load(Path(args.blueprint).read_text(encoding="utf-8")) or {}
    bp = bp.get("blueprint", bp)
    form = next((f for f in bp.get("forms") or [] if isinstance(f, dict) and f.get("id") == args.form), None)
    if not form:
        print(f"forms[{args.form}] nao existe no Blueprint.")
        sys.exit(1)
    errs = problems(form)
    if errs:
        print(f"forms[{args.form}] nao pode ser gerado:")
        print("\n".join(f"  - {e}" for e in errs))
        sys.exit(1)

    template = build_template(form)
    mail = build_mail(form)
    if args.show or not args.project:
        print("=== Formulario (Contato > Formularios > aba Formulario) ===")
        print(template)
        print("\n=== E-mail (aba E-mail) ===")
        print(json.dumps(mail, ensure_ascii=False, indent=2))
        if not args.project:
            return

    payload = {
        "slug": re.sub(r"[^a-z0-9-]+", "-", args.form.lower()).strip("-"),
        "title": form.get("title") or PURPOSE_LABELS.get(form.get("purpose"), args.form),
        "form": template,
        "mail": mail,
        "policy_page": (form.get("privacy") or {}).get("policy_page") or "",
        "token": POLICY_TOKEN,
    }
    with tempfile.TemporaryDirectory() as tmp:
        data_file = Path(tmp) / "form.json"
        php_file = Path(tmp) / "apply.php"
        data_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        php_file.write_text(PHP_APPLY, encoding="utf-8")
        import os
        env = {**os.environ, "PROJECT_CF7_JSON": str(data_file)}
        result = subprocess.run(_wpcli.resolve(["wp", "eval-file", str(php_file)]),
                                cwd=args.project, env=env, capture_output=True, text=True, encoding="utf-8")
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip())
        sys.exit(2)
    print("Confira no admin (Contato > Formularios) e no front-end; o slug e o valor padrao de project_form().")


if __name__ == "__main__":
    main()
