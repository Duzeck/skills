#!/usr/bin/env python3
"""
gerar_pdf.py — converte um arquivo Markdown em um PDF estruturado.

Recursos: bloco de título (ou capa), sumário opcional, marcadores de navegação
(outline do PDF), títulos, parágrafos com negrito/itálico/código/links, listas
aninhadas, citações, blocos de código, tabelas, linhas horizontais e rodapé
com "Página X de Y".

Uso:
    python gerar_pdf.py <entrada.md> [--saida arquivo.pdf] [--titulo "..."]
                        [--subtitulo "..."] [--autor "..."] [--capa] [--sumario]

Caminhos relativos da entrada são procurados no diretório atual e, depois, na
pasta indicada pela variável de ambiente WORKSPACE_DIR.

Códigos de saída:
    0  sucesso (o caminho do PDF é impresso no stdout)
    2  dependências ausentes e instalação automática falhou
    3  erro ao montar o PDF
    5  erro de argumento / arquivo de entrada não encontrado
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


def log(msg: str) -> None:
    print(f"[gerar_pdf] {msg}", file=sys.stderr)


def garantir_dependencias() -> bool:
    try:
        import markdown_it  # noqa: F401
        import reportlab  # noqa: F401
        return True
    except ImportError:
        log("reportlab/markdown-it-py ausentes; tentando instalar")
        for extra in (["--user"], []):
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", *extra, "reportlab", "markdown-it-py"],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                break
        try:
            import markdown_it  # noqa: F401
            import reportlab  # noqa: F401
            return True
        except ImportError:
            return False


# --------------------------------------------------------------------------
# fontes
# --------------------------------------------------------------------------

FONTES_CANDIDATAS = [
    # (regular, negrito, itálico, negrito-itálico)
    ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf",
     "C:/Windows/Fonts/segoeuii.ttf", "C:/Windows/Fonts/segoeuiz.ttf"),
    ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf",
     "C:/Windows/Fonts/ariali.ttf", "C:/Windows/Fonts/arialbi.ttf"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf"),
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf",
     "/Library/Fonts/Arial Italic.ttf", "/Library/Fonts/Arial Bold Italic.ttf"),
]
MONO_CANDIDATAS = [
    "C:/Windows/Fonts/consola.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/Library/Fonts/Courier New.ttf",
]


def registrar_fontes() -> tuple[str, str]:
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    base = "Helvetica"
    for reg, bold, it, bi in FONTES_CANDIDATAS:
        if all(Path(p).exists() for p in (reg, bold, it, bi)):
            try:
                for nome, caminho in (("Doc", reg), ("Doc-B", bold), ("Doc-I", it), ("Doc-BI", bi)):
                    pdfmetrics.registerFont(TTFont(nome, caminho))
                addMapping("Doc", 0, 0, "Doc")
                addMapping("Doc", 1, 0, "Doc-B")
                addMapping("Doc", 0, 1, "Doc-I")
                addMapping("Doc", 1, 1, "Doc-BI")
                base = "Doc"
                break
            except Exception as exc:  # noqa: BLE001
                log(f"fonte {reg} falhou: {exc}")

    mono = "Courier"
    for caminho in MONO_CANDIDATAS:
        if Path(caminho).exists():
            try:
                pdfmetrics.registerFont(TTFont("DocMono", caminho))
                mono = "DocMono"
                break
            except Exception as exc:  # noqa: BLE001
                log(f"fonte mono {caminho} falhou: {exc}")
    return base, mono


def limpar_texto(s: str) -> str:
    """Remove emojis e símbolos fora do plano básico, que as fontes não cobrem."""
    saida = []
    for ch in s:
        cp = ord(ch)
        if cp > 0xFFFF or 0xFE00 <= cp <= 0xFE0F or cp == 0x200D:
            continue
        if 0x2600 <= cp <= 0x27BF and ch not in "✓✔✗✘":
            continue
        saida.append(ch)
    return "".join(saida)


def esc(s: str) -> str:
    return limpar_texto(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# montagem
# --------------------------------------------------------------------------

COR_PRIMARIA = "#1F3A5F"
COR_DESTAQUE = "#2E86AB"
COR_TEXTO = "#222222"
COR_SUAVE = "#6B7280"
COR_FUNDO = "#F3F5F8"


class Montador:
    def __init__(self, fonte: str, mono: str, largura: float):
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.styles import ParagraphStyle

        self.fonte, self.mono, self.largura = fonte, mono, largura
        self.colors = colors
        base = ParagraphStyle("base", fontName=fonte, fontSize=10.5, leading=15,
                              textColor=colors.HexColor(COR_TEXTO), alignment=TA_LEFT, spaceAfter=6)
        self.st = {
            "p": base,
            "li": ParagraphStyle("li", parent=base, spaceAfter=2),
            "h1": ParagraphStyle("h1", parent=base, fontName=fonte, fontSize=18, leading=23,
                                 textColor=colors.HexColor(COR_PRIMARIA), spaceBefore=14, spaceAfter=8),
            "h2": ParagraphStyle("h2", parent=base, fontSize=14.5, leading=19,
                                 textColor=colors.HexColor(COR_PRIMARIA), spaceBefore=12, spaceAfter=6),
            "h3": ParagraphStyle("h3", parent=base, fontSize=12, leading=16,
                                 textColor=colors.HexColor(COR_DESTAQUE), spaceBefore=10, spaceAfter=4),
            "h4": ParagraphStyle("h4", parent=base, fontSize=10.5, leading=15,
                                 textColor=colors.HexColor(COR_TEXTO), spaceBefore=8, spaceAfter=3),
            "quote": ParagraphStyle("quote", parent=base, textColor=colors.HexColor("#374151"), spaceAfter=3),
            "code": ParagraphStyle("code", parent=base, fontName=mono, fontSize=8.8, leading=11.5, spaceAfter=0),
            "th": ParagraphStyle("th", parent=base, fontSize=9.5, leading=12.5,
                                 textColor=colors.white, spaceAfter=0),
            "td": ParagraphStyle("td", parent=base, fontSize=9.5, leading=12.5, spaceAfter=0),
            "titulo": ParagraphStyle("titulo", parent=base, fontSize=24, leading=30,
                                     textColor=colors.HexColor(COR_PRIMARIA), spaceAfter=6),
            "subtitulo": ParagraphStyle("subtitulo", parent=base, fontSize=13, leading=18,
                                        textColor=colors.HexColor(COR_DESTAQUE), spaceAfter=4),
            "meta": ParagraphStyle("meta", parent=base, fontSize=9.5, leading=13,
                                   textColor=colors.HexColor(COR_SUAVE), spaceAfter=0),
        }
        self.n_titulo = 0

    # ---------- inline ----------
    def inline(self, filhos) -> str:
        out: list[str] = []
        pilha_link: list[bool] = []
        for t in filhos or []:
            tipo = t.type
            if tipo == "text":
                out.append(esc(t.content))
            elif tipo == "softbreak":
                out.append(" ")
            elif tipo == "hardbreak":
                out.append("<br/>")
            elif tipo == "strong_open":
                out.append("<b>")
            elif tipo == "strong_close":
                out.append("</b>")
            elif tipo == "em_open":
                out.append("<i>")
            elif tipo == "em_close":
                out.append("</i>")
            elif tipo == "s_open":
                out.append("<strike>")
            elif tipo == "s_close":
                out.append("</strike>")
            elif tipo == "code_inline":
                out.append(f'<font face="{self.mono}" color="#B42318">{esc(t.content)}</font>')
            elif tipo == "link_open":
                href = (t.attrGet("href") or "").replace('"', "%22")
                ok = href.startswith(("http://", "https://", "mailto:"))
                pilha_link.append(ok)
                out.append(f'<a href="{esc(href)}" color="{COR_DESTAQUE}"><u>' if ok else "")
            elif tipo == "link_close":
                out.append("</u></a>" if (pilha_link.pop() if pilha_link else False) else "")
            elif tipo == "image":
                out.append(f"[imagem: {esc(t.content or t.attrGet('alt') or '')}]")
            elif tipo in ("html_inline",):
                out.append(esc(t.content))
            elif t.children:
                out.append(self.inline(t.children))
            elif t.content:
                out.append(esc(t.content))
        return "".join(out)

    # ---------- blocos ----------
    @staticmethod
    def fechamento(tokens, i: int) -> int:
        abre = tokens[i].type
        fecha = abre.replace("_open", "_close")
        nivel = 0
        for j in range(i, len(tokens)):
            if tokens[j].type == abre:
                nivel += 1
            elif tokens[j].type == fecha:
                nivel -= 1
                if nivel == 0:
                    return j
        return len(tokens) - 1

    def blocos(self, tokens, estilo_p: str = "p", largura: float | None = None) -> list:
        from reportlab.platypus import (
            HRFlowable, KeepTogether, ListFlowable, ListItem, Paragraph, Preformatted, Spacer, Table, TableStyle,
        )

        c = self.colors
        largura = largura or self.largura
        out: list = []
        i = 0
        while i < len(tokens):
            t = tokens[i]
            tipo = t.type

            if tipo == "heading_open":
                nivel = min(int(t.tag[1]), 4)
                texto = self.inline(tokens[i + 1].children)
                p = Paragraph(texto, self.st[f"h{nivel}"])
                p._nivel_titulo = nivel  # usado pelo sumário e marcadores
                p._texto_titulo = re.sub(r"<[^>]+>", "", texto)
                if nivel <= 2:
                    out.append(KeepTogether([p, Spacer(1, 1)]))
                    if nivel == 1:
                        out.append(HRFlowable(width="100%", thickness=0.6, color=c.HexColor(COR_DESTAQUE),
                                              spaceBefore=0, spaceAfter=6))
                else:
                    out.append(p)
                i += 3
                continue

            if tipo == "paragraph_open":
                out.append(Paragraph(self.inline(tokens[i + 1].children), self.st[estilo_p]))
                i += 3
                continue

            if tipo in ("bullet_list_open", "ordered_list_open"):
                fim = self.fechamento(tokens, i)
                itens = []
                j = i + 1
                while j < fim:
                    if tokens[j].type == "list_item_open":
                        fim_item = self.fechamento(tokens, j)
                        conteudo = self.blocos(tokens[j + 1:fim_item], "li", largura - 18)
                        itens.append(ListItem(conteudo or [Paragraph("", self.st["li"])], leftIndent=14))
                        j = fim_item + 1
                    else:
                        j += 1
                if tipo == "ordered_list_open":
                    inicio = int(t.attrGet("start") or 1)
                    lista = ListFlowable(itens, bulletType="1", start=inicio, bulletFontName=self.fonte,
                                         bulletFontSize=10, leftIndent=16, bulletColor=c.HexColor(COR_PRIMARIA))
                else:
                    lista = ListFlowable(itens, bulletType="bullet", start="•", bulletFontName=self.fonte,
                                         bulletFontSize=10, leftIndent=14, bulletColor=c.HexColor(COR_DESTAQUE))
                out.append(lista)
                out.append(Spacer(1, 4))
                i = fim + 1
                continue

            if tipo == "blockquote_open":
                fim = self.fechamento(tokens, i)
                conteudo = self.blocos(tokens[i + 1:fim], "quote", largura - 24)
                tabela = Table([[conteudo]], colWidths=[largura])
                tabela.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), c.HexColor(COR_FUNDO)),
                    ("LINEBEFORE", (0, 0), (0, -1), 3, c.HexColor(COR_DESTAQUE)),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                out.extend([tabela, Spacer(1, 6)])
                i = fim + 1
                continue

            if tipo in ("fence", "code_block"):
                max_chars = max(30, int((largura - 16) / (8.8 * 0.55)))
                codigo = limpar_texto(t.content.rstrip("\n"))
                pre = Preformatted(codigo, self.st["code"], maxLineLength=max_chars, newLineChars="")
                tabela = Table([[pre]], colWidths=[largura])
                tabela.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), c.HexColor("#F6F8FA")),
                    ("BOX", (0, 0), (-1, -1), 0.5, c.HexColor("#D0D7DE")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                out.extend([tabela, Spacer(1, 8)])
                i += 1
                continue

            if tipo == "table_open":
                fim = self.fechamento(tokens, i)
                linhas: list[list] = []
                cabecalho = False
                linha: list = []
                for k in range(i + 1, fim):
                    tk = tokens[k]
                    if tk.type == "tr_open":
                        linha = []
                    elif tk.type in ("th_open", "td_open"):
                        estilo = "th" if tk.type == "th_open" else "td"
                        cabecalho = cabecalho or estilo == "th"
                        linha.append(Paragraph(self.inline(tokens[k + 1].children), self.st[estilo]))
                    elif tk.type == "tr_close":
                        linhas.append(linha)
                if linhas:
                    ncol = max(len(r) for r in linhas)
                    for r in linhas:
                        r.extend([Paragraph("", self.st["td"])] * (ncol - len(r)))
                    tabela = Table(linhas, colWidths=[largura / ncol] * ncol, repeatRows=1 if cabecalho else 0)
                    estilo = [
                        ("GRID", (0, 0), (-1, -1), 0.4, c.HexColor("#D0D7DE")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                    if cabecalho:
                        estilo.append(("BACKGROUND", (0, 0), (-1, 0), c.HexColor(COR_PRIMARIA)))
                    inicio_dados = 1 if cabecalho else 0
                    for n in range(inicio_dados, len(linhas)):
                        if (n - inicio_dados) % 2 == 1:
                            estilo.append(("BACKGROUND", (0, n), (-1, n), c.HexColor(COR_FUNDO)))
                    tabela.setStyle(TableStyle(estilo))
                    out.extend([tabela, Spacer(1, 8)])
                i = fim + 1
                continue

            if tipo == "hr":
                out.append(HRFlowable(width="100%", thickness=0.5, color=c.HexColor("#C9CED6"),
                                      spaceBefore=6, spaceAfter=8))
                i += 1
                continue

            if tipo == "html_block":
                texto = re.sub(r"<[^>]+>", "", t.content).strip()
                if texto:
                    out.append(Paragraph(esc(texto), self.st[estilo_p]))
                i += 1
                continue

            i += 1
        return out


def montar_pdf(md: str, saida: Path, titulo: str | None, subtitulo: str | None, autor: str | None,
               capa: bool, sumario: bool) -> None:
    from markdown_it import MarkdownIt
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import (
        BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate, Paragraph, Spacer,
    )
    from reportlab.platypus.tableofcontents import TableOfContents

    fonte, mono = registrar_fontes()
    parser = MarkdownIt("commonmark", {"breaks": False, "html": True}).enable(["table", "strikethrough"])
    tokens = parser.parse(md)

    # Primeiro H1 vira o título do documento, se nenhum foi informado.
    if not titulo and len(tokens) >= 3 and tokens[0].type == "heading_open" and tokens[0].tag == "h1":
        titulo = re.sub(r"[*_`]", "", tokens[1].content).strip()
        tokens = tokens[3:]
    titulo = limpar_texto(titulo or saida.stem.replace("-", " ").replace("_", " ").strip().capitalize())

    niveis = [int(t.tag[1]) for t in tokens if t.type == "heading_open" and int(t.tag[1]) <= 3]
    nivel_base = min(niveis) if niveis else 1

    margem = 2 * cm
    largura_util = A4[0] - 2 * margem
    m = Montador(fonte, mono, largura_util)
    data = dt.date.today().strftime("%d/%m/%Y")

    class Doc(BaseDocTemplate):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            frame = Frame(margem, margem + 0.4 * cm, largura_util, A4[1] - 2 * margem - 0.6 * cm, id="f")
            self.addPageTemplates([
                PageTemplate(id="capa", frames=[frame], onPage=lambda cv, d: None),
                PageTemplate(id="normal", frames=[frame]),
            ])
            self._marcadores = 0
            self._ultimo_nivel = -1

        def beforeDocument(self):
            # multiBuild roda várias passadas; o outline recomeça em cada uma.
            self._marcadores = 0
            self._ultimo_nivel = -1

        def afterFlowable(self, fl):
            nivel = getattr(fl, "_nivel_titulo", None)
            if nivel is None or nivel > 3:
                return
            texto = fl._texto_titulo
            chave = f"h{self._marcadores}"
            self._marcadores += 1
            # O outline do PDF não aceita pular níveis (ex.: começar em H2 sem H1).
            nivel_rel = max(0, min(nivel - nivel_base, self._ultimo_nivel + 1))
            self._ultimo_nivel = nivel_rel
            self.canv.bookmarkPage(chave)
            self.canv.addOutlineEntry(limpar_texto(texto), chave, level=nivel_rel, closed=nivel_rel > 0)
            if nivel_rel <= 1:
                self.notify("TOCEntry", (nivel_rel, texto, self.page, chave))

    class CanvasNumerado(rl_canvas.Canvas):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self._paginas = []

        def showPage(self):
            self._paginas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas)
            for estado in self._paginas:
                self.__dict__.update(estado)
                if not (capa and self._pageNumber == 1):
                    self.rodape(total)
                super().showPage()
            super().save()

        def rodape(self, total):
            self.saveState()
            self.setStrokeColor(colors.HexColor("#D0D7DE"))
            self.setLineWidth(0.5)
            self.line(margem, margem - 0.1 * cm, A4[0] - margem, margem - 0.1 * cm)
            self.setFont(fonte, 8)
            self.setFillColor(colors.HexColor(COR_SUAVE))
            curto = titulo if len(titulo) <= 80 else titulo[:77] + "..."
            self.drawString(margem, margem - 0.55 * cm, curto)
            self.drawRightString(A4[0] - margem, margem - 0.55 * cm, f"Página {self._pageNumber} de {total}")
            self.restoreState()

    historia: list = []
    if capa:
        from reportlab.platypus import NextPageTemplate
        historia += [Spacer(1, 6 * cm),
                     HRFlowable(width="30%", thickness=3, color=colors.HexColor(COR_DESTAQUE), hAlign="LEFT",
                                spaceAfter=14),
                     Paragraph(esc(titulo), ParagraphStyle("capa_t", parent=m.st["titulo"], fontSize=30, leading=37))]
        if subtitulo:
            historia.append(Paragraph(esc(subtitulo), ParagraphStyle("capa_s", parent=m.st["subtitulo"],
                                                                     fontSize=15, leading=21)))
        historia += [Spacer(1, 1.2 * cm)]
        if autor:
            historia.append(Paragraph(esc(autor), m.st["meta"]))
        historia += [Paragraph(data, m.st["meta"]), NextPageTemplate("normal"), PageBreak()]
    else:
        historia.append(Paragraph(esc(titulo), m.st["titulo"]))
        if subtitulo:
            historia.append(Paragraph(esc(subtitulo), m.st["subtitulo"]))
        meta = " · ".join(x for x in (esc(autor) if autor else "", data) if x)
        historia += [Paragraph(meta, m.st["meta"]),
                     HRFlowable(width="100%", thickness=1.2, color=colors.HexColor(COR_PRIMARIA),
                                spaceBefore=8, spaceAfter=12)]

    if sumario:
        toc = TableOfContents()
        toc.dotsMinLevel = 0
        toc.levelStyles = [
            ParagraphStyle("toc1", fontName=fonte, fontSize=11, leading=16, leftIndent=0,
                           textColor=colors.HexColor(COR_PRIMARIA)),
            ParagraphStyle("toc2", fontName=fonte, fontSize=10, leading=14, leftIndent=16,
                           textColor=colors.HexColor(COR_TEXTO)),
        ]
        historia += [Paragraph("Sumário", m.st["h1"]), toc, PageBreak()]

    historia += m.blocos(tokens)

    doc = Doc(str(saida), pagesize=A4, leftMargin=margem, rightMargin=margem, topMargin=margem,
              bottomMargin=margem, title=titulo, author=autor or "", subject=subtitulo or "",
              creator="DuzeckClaw · gerar-pdf")
    if not capa:
        doc.pageTemplates = [doc.pageTemplates[1]]
    if sumario:
        doc.multiBuild(historia, canvasmaker=CanvasNumerado)
    else:
        doc.build(historia, canvasmaker=CanvasNumerado)


# --------------------------------------------------------------------------
# principal
# --------------------------------------------------------------------------

def resolver_entrada(caminho: str) -> Path | None:
    p = Path(caminho)
    if p.is_absolute():
        return p if p.exists() else None
    candidatos = [Path.cwd() / p]
    if os.environ.get("WORKSPACE_DIR"):
        candidatos.append(Path(os.environ["WORKSPACE_DIR"]) / p)
    return next((c for c in candidatos if c.exists()), None)


def slug(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    base = re.sub(r"[^\w\s-]", "", base).strip().lower()
    return re.sub(r"[\s_-]+", "-", base)[:60] or "documento"


def main() -> int:
    ap = argparse.ArgumentParser(description="Converte Markdown em PDF estruturado.")
    ap.add_argument("entrada", help="arquivo .md")
    ap.add_argument("--saida", help="arquivo .pdf de saída (padrão: nome derivado do título)")
    ap.add_argument("--titulo")
    ap.add_argument("--subtitulo")
    ap.add_argument("--autor")
    ap.add_argument("--capa", action="store_true", help="gera página de capa")
    ap.add_argument("--sumario", action="store_true", help="gera sumário a partir dos títulos")
    args = ap.parse_args()

    entrada = resolver_entrada(args.entrada)
    if not entrada:
        log(f"arquivo de entrada não encontrado: {args.entrada}")
        return 5

    if not garantir_dependencias():
        log("não foi possível obter reportlab e markdown-it-py")
        return 2

    md = entrada.read_text(encoding="utf-8", errors="replace")
    if args.saida:
        saida = Path(args.saida)
    else:
        m = re.search(r"^#\s+(.+)$", md, re.MULTILINE)
        saida = Path(f"{slug(args.titulo or (m.group(1) if m else entrada.stem))}.pdf")
    if saida.suffix.lower() != ".pdf":
        saida = saida.with_suffix(".pdf")
    if not saida.is_absolute():
        saida = Path.cwd() / saida

    try:
        montar_pdf(md, saida, args.titulo, args.subtitulo, args.autor, args.capa, args.sumario)
    except Exception as exc:  # noqa: BLE001
        log(f"erro ao montar o PDF: {exc}")
        return 3

    log(f"PDF gerado: {saida.name} ({saida.stat().st_size // 1024} KB)")
    print(saida.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
