"""Render a DraftDocument as PDF (PyMuPDF, which shapes Devanagari itself) or Word (python-docx)."""
from __future__ import annotations

import html
import io

import pymupdf
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from app.drafts.schemas import DraftDocument

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"


# ----------------------------------------------------------------------------- PDF
_CSS = """
body { font-family: sans-serif; font-size: 11pt; line-height: 1.35; }
h1 { font-size: 14pt; text-align: center; margin: 6pt 0 10pt 0; }
.sub { text-align: center; font-size: 9.5pt; margin: 0 0 4pt 0; }
p { margin: 0 0 7pt 0; }
p.h { page-break-after: avoid; }
.right { text-align: right; }
.sig { text-align: right; margin-top: 14pt; }
table { width: 100%; border-collapse: collapse; margin: 4pt 0 9pt 0; }
td { border: 1px solid #555555; padding: 4pt 6pt; vertical-align: top; }
"""
# PyMuPDF's HTML engine ignores percentage widths on tables and treats 1px as 1pt, so sizes are given in points:
# A4 (595pt) minus 56pt margins on both sides = 483pt of text width.
_MARGIN = 56
_TEXT_W = 595 - 2 * _MARGIN
_PAD = 26  # left + right cell padding (6pt each) plus the 1px borders are added on top of a cell's width
_LABEL_W = 188
_VALUE_W = _TEXT_W - _LABEL_W - 2 * _PAD
_BOX_W = 230


def _h(text: str) -> str:
    return html.escape(text).replace("\n", "<br/>")


def _pdf_html(doc: DraftDocument) -> str:
    parts: list[str] = []
    for b in doc.blocks:
        if b.type == "title":
            parts.append(f"<h1>{_h(b.text)}</h1>")
        elif b.type == "subtitle":
            parts.append(f'<p class="sub">{_h(b.text)}</p>')
        elif b.type == "box":
            parts.append(f'<table style="width:{_BOX_W}px;margin-left:{_TEXT_W - _BOX_W - _PAD}px"><tr><td>{_h(b.text)}</td></tr></table>')
        elif b.type == "para":
            parts.append(f'<p class="h"><b>{_h(b.text)}</b></p>' if b.bold else f"<p>{_h(b.text)}</p>")
        elif b.type == "right":
            parts.append(f'<p class="right">{_h(b.text)}</p>')
        elif b.type == "numbered":
            parts += [f"<p>{_h(i)}</p>" for i in b.items]
        elif b.type == "signature":
            parts.append(f'<p class="sig">{_h(b.text)}</p>')
        elif b.type == "spacer":
            parts.append("<p>&nbsp;</p>")
        elif b.type == "rows":
            body = "".join(
                f'<tr><td style="width:{_LABEL_W}px">{_h(k)}</td><td style="width:{_VALUE_W}px">{_h(v)}</td></tr>' if v
                else f'<tr><td colspan="2" style="width:{_TEXT_W - _PAD}px"><b>{_h(k)}</b></td></tr>'
                for k, v in b.rows
            )
            parts.append(f"<table>{body}</table>")
    return "".join(parts)


def to_pdf(doc: DraftDocument) -> bytes:
    story = pymupdf.Story(html=_pdf_html(doc), user_css=_CSS)
    buf = io.BytesIO()
    writer = pymupdf.DocumentWriter(buf)
    page = pymupdf.paper_rect("a4")
    area = page + (_MARGIN, _MARGIN, -_MARGIN, -_MARGIN)
    more = 1
    while more:
        device = writer.begin_page(page)
        more, _ = story.place(area)
        story.draw(device)
        writer.end_page()
    writer.close()
    return buf.getvalue()


# ----------------------------------------------------------------------------- Word
def _set_font(run, name: str, size: float, bold: bool = False) -> None:
    run.font.size = Pt(size)
    run.bold = bold
    props = run._element.get_or_add_rPr()
    fonts = props.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        props.insert(0, fonts)
    for slot in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(slot), name)
    if bold:  # complex-script bold is a separate switch in Word
        props.append(OxmlElement("w:bCs"))


def _borders(table) -> None:
    table.style = "Table Grid"


def to_docx(doc: DraftDocument) -> bytes:
    mr = doc.language == "mr"
    font = "Mangal" if mr else "Times New Roman"  # Mangal ships with Windows and covers Devanagari + Latin
    size = 12

    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.2)
    sec.top_margin = sec.bottom_margin = Cm(2.0)
    d.core_properties.title = doc.title
    d.core_properties.author = "NyayaSetu"

    def para(text: str, *, bold=False, align=None, sz=size, after=6):
        p = d.add_paragraph()
        p.paragraph_format.space_after = Pt(after)
        if align is not None:
            p.alignment = align
        for i, line in enumerate(text.split("\n")):
            run = p.add_run(line)
            _set_font(run, font, sz, bold)
            if i < len(text.split("\n")) - 1:
                run.add_break()
        return p

    for b in doc.blocks:
        if b.type == "title":
            para(b.text, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, sz=14, after=10)
        elif b.type == "subtitle":
            para(b.text, align=WD_ALIGN_PARAGRAPH.CENTER, sz=10, after=4)
        elif b.type == "box":
            t = d.add_table(rows=1, cols=1)
            _borders(t)
            t.alignment = WD_TABLE_ALIGNMENT.RIGHT
            cell = t.rows[0].cells[0]
            cell.width = Cm(6)
            _set_font(cell.paragraphs[0].add_run(b.text), font, 9.5)
            d.add_paragraph().paragraph_format.space_after = Pt(2)
        elif b.type == "para":
            para(b.text, bold=b.bold)
        elif b.type == "right":
            para(b.text, align=WD_ALIGN_PARAGRAPH.RIGHT)
        elif b.type == "numbered":
            for item in b.items:
                para(item, after=4)
        elif b.type == "signature":
            para(b.text, align=WD_ALIGN_PARAGRAPH.RIGHT, after=0)
        elif b.type == "spacer":
            para("", after=6)
        elif b.type == "rows":
            t = d.add_table(rows=0, cols=2)
            _borders(t)
            for k, v in b.rows:
                cells = t.add_row().cells
                cells[0].width, cells[1].width = Cm(7.2), Cm(9.4)
                if v:
                    _set_font(cells[0].paragraphs[0].add_run(k), font, 11)
                    for i, line in enumerate(v.split("\n")):
                        run = cells[1].paragraphs[0].add_run(line)
                        _set_font(run, font, 11)
                        if i < len(v.split("\n")) - 1:
                            run.add_break()
                else:  # section heading row spanning both columns
                    merged = cells[0].merge(cells[1])
                    _set_font(merged.paragraphs[0].add_run(k), font, 11, bold=True)
            d.add_paragraph().paragraph_format.space_after = Pt(2)

    out = io.BytesIO()
    d.save(out)
    return out.getvalue()
