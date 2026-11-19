"""Builds NyayaSetu-Project-Report-Template.docx (and .pdf via LibreOffice) in the B.Tech Final Year Project-I report template format.

   pip install python-docx beautifulsoup4 pillow pymupdf ;  npm install  (playwright-core, for the diagram PNGs)
   python build_docx.py
Format (from the template): Letter, 1" margins, Times New Roman; chapter title 24 bold, heading 14 bold, subheading 12 bold,
text 12 with 1.5 line spacing; figure label below the figure and table label above the table, both 10 bold;
front matter in roman numerals, body footer "Department of Information Technology, WCE Sangli | n".
"""
import json, os, re, subprocess, sys, shutil
from bs4 import BeautifulSoup, NavigableString, Tag
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Inches, RGBColor, Emu
from PIL import Image
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DOCX = os.path.join(HERE, "NyayaSetu-Project-Report-Template.docx")
OUT_PDF = os.path.join(HERE, "NyayaSetu-Project-Report-Template.pdf")
TMP = os.path.join(HERE, "_svg"); os.makedirs(TMP, exist_ok=True)
FONT = "Times New Roman"
COURSE = "PROJECT (7IT492)"
AY_SHORT, AY_LONG = "2026-27", "AY 2026 - 27"
GUIDE = C.GUIDE            # guide and Head of Department are the same person
HEAD = C.GUIDE
TITLE = C.TITLE
STUDENTS = C.STUDENTS
MAXW = 6.5                 # text width in inches


# ------------------------------------------------------------------ low-level helpers
def set_font(run, size=12, bold=None, italic=None, color=None):
    run.font.name = FONT
    run._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    run.font.size = Pt(size)
    if bold is not None: run.bold = bold
    if italic is not None: run.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)


def spacing(p, line=1.5, before=0, after=6):
    pf = p.paragraph_format
    pf.line_spacing, pf.space_before, pf.space_after = line, Pt(before), Pt(after)


def para(doc, text="", size=12, bold=False, italic=False, align=None, line=1.5, before=0, after=6, color=None):
    p = doc.add_paragraph()
    if text:
        set_font(p.add_run(text), size, bold, italic, color)
    if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "j": p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "r": p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    spacing(p, line, before, after)
    return p


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def bottom_border(p, style="dashed", color="000000", sz=6, space=1):
    pPr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); e = OxmlElement("w:bottom")
    for k, v in (("val", style), ("sz", str(sz)), ("space", str(space)), ("color", color)): e.set(qn("w:" + k), v)
    b.append(e); pPr.append(b)


def top_border(p):
    pPr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); e = OxmlElement("w:top")
    for k, v in (("val", "single"), ("sz", "4"), ("space", "4"), ("color", "BFBFBF")): e.set(qn("w:" + k), v)
    b.append(e); pPr.append(b)


def cell_borders(cell, on=True, color="000000"):
    tcPr = cell._tc.get_or_add_tcPr(); b = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + side)
        e.set(qn("w:val"), "single" if on else "nil"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), color); b.append(e)
    tcPr.append(b)


def cell_margins(cell, top=40, left=80, bottom=40, right=80):
    tcPr = cell._tc.get_or_add_tcPr(); m = OxmlElement("w:tcMar")
    for side, w in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement("w:" + side); e.set(qn("w:w"), str(w)); e.set(qn("w:type"), "dxa"); m.append(e)
    tcPr.append(m)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), fill); tcPr.append(s)


def keep_row(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def simple_table(doc, rows, widths, size=14, header=True, borders=True, align_cols=None, bold_first_col=False, line=1.0):
    t = doc.add_table(rows=len(rows), cols=len(widths))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, row in enumerate(rows):
        keep_row(t.rows[i])
        for j, txt in enumerate(row):
            c = t.cell(i, j); c.width = Inches(widths[j]); cell_borders(c, borders); cell_margins(c)
            if borders and header and i == 0: shade(c, "E8EDF3")
            p = c.paragraphs[0]; spacing(p, line, 0, 0)
            a = (align_cols or {}).get(j)
            if a == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif a == "r": p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            set_font(p.add_run(txt), size, bold=(header and i == 0) or (bold_first_col and j == 0 and i > 0))
    return t


def field(run, instr):
    for kind in ("begin", None, "end"):
        if kind:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind); run._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = instr; run._r.append(e)


def set_pgnum(section, fmt, start=1):
    sp = section._sectPr
    for old in sp.findall(qn("w:pgNumType")): sp.remove(old)
    e = OxmlElement("w:pgNumType"); e.set(qn("w:fmt"), fmt); e.set(qn("w:start"), str(start)); sp.append(e)


def footer_roman(section):
    section.footer.is_linked_to_previous = False
    f = section.footer; p = f.paragraphs[0]
    for r in list(p.runs): r._r.getparent().remove(r._r)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER; top_border(p)
    field(p.add_run(), "PAGE"); [set_font(r, 12) for r in p.runs]
    for r in p.runs: set_font(r, 12)


def footer_body(section):
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]
    for r in list(p.runs): r._r.getparent().remove(r._r)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER; top_border(p)
    set_font(p.add_run("Department of Information Technology, WCE Sangli  | "), 12)
    r = p.add_run(); field(r, "PAGE"); set_font(r, 12)


def footer_none(section):
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]
    for r in list(p.runs): r._r.getparent().remove(r._r)


def new_section(doc):
    s = doc.add_section(WD_SECTION.NEW_PAGE)
    s.page_width, s.page_height = Inches(8.5), Inches(11)
    for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(s, a, Inches(1))
    s.footer_distance = Inches(0.5)
    return s


# ------------------------------------------------------------------ images
def svg_pngs(svgs):
    """Render every inline svg of the report body to a PNG (once); returns the png paths."""
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    css = "\n".join(l for l in css.splitlines() if l.strip().startswith("svg "))
    body = "".join(s.replace("<svg ", '<svg class="fig" ', 1) for s in svgs)
    html = os.path.join(TMP, "svgs.html")
    open(html, "w", encoding="utf-8").write(f'<html><head><style>body{{margin:0;background:#fff}} svg.fig{{display:block;margin:8px}} {css}</style></head><body>{body}</body></html>')
    subprocess.run(["node", os.path.join(HERE, "render_svgs.mjs"), html, TMP], check=True)
    return [os.path.join(TMP, f"svg_{i}.png") for i in range(len(svgs))]


def add_picture(doc, path, max_w, max_h):
    w, h = Image.open(path).size
    inch_w = max_w; inch_h = inch_w * h / w
    if inch_h > max_h: inch_h = max_h; inch_w = inch_h * w / h
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(p, 1.0, 6, 3)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Inches(inch_w))
    return p


# ------------------------------------------------------------------ HTML body -> docx
def inline(p, node, size=12, bold=False, italic=False, mono=False):
    for ch in node.children:
        if isinstance(ch, NavigableString):
            t = str(ch).replace("\n", " ")
            if t:
                r = p.add_run(t); set_font(r, size, bold, italic)
                if mono: r.font.name = "Courier New"; r._r.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Courier New"); r.font.size = Pt(size - 1)
        elif isinstance(ch, Tag):
            if ch.name == "br": p.add_run().add_break()
            elif ch.name in ("b", "strong"): inline(p, ch, size, True, italic, mono)
            elif ch.name in ("i", "em"): inline(p, ch, size, bold, True, mono)
            elif ch.name == "code": inline(p, ch, size, bold, italic, True)
            else: inline(p, ch, size, bold, italic, mono)


def html_table(doc, tbl):
    rows = []
    for tr in tbl.find_all("tr"):
        rows.append([td.get_text(" ", strip=True).replace("\xa0", " ") for td in tr.find_all(["th", "td"])])
    ncol = len(rows[0])
    cg = [re.sub(r"[^0-9.]", "", c.get("style", "").split("width:")[-1]) for c in tbl.find_all("col")]
    ws = [float(x) / 100 * MAXW if x else MAXW / ncol for x in cg] if cg and all(cg) else [MAXW / ncol] * ncol
    ncl = {i for i, th in enumerate(tbl.find("tr").find_all(["th", "td"])) if "n" in (th.get("class") or [])}
    t = simple_table(doc, rows, ws, size=11, align_cols={i: "r" for i in ncl}, line=1.0)
    sp = doc.add_paragraph(); spacing(sp, 1.0, 0, 6)
    return t


def walk(doc, root, pics):
    state = {"svg": 0}
    for el in root.children:
        if isinstance(el, NavigableString): continue
        cls = el.get("class") or []
        if el.name == "h1":
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(p, 1.0, 0, 0)
            p.paragraph_format.page_break_before = True
            set_font(p.add_run(el.get_text()), 24, True)
            d = doc.add_paragraph(); spacing(d, 1.0, 0, 14); bottom_border(d)
        elif el.name == "div" and "rule" in cls:
            continue
        elif el.name == "h2":
            p = doc.add_paragraph(); spacing(p, 1.5, 6, 3); p.paragraph_format.keep_with_next = True
            set_font(p.add_run(el.get_text().replace("\xa0", " ")), 14, True)
        elif el.name == "h3":
            p = doc.add_paragraph(); spacing(p, 1.5, 3, 0); p.paragraph_format.keep_with_next = True
            set_font(p.add_run(el.get_text().replace("\xa0", " ")), 12, True)
        elif el.name == "p":
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT if el.find("br") else WD_ALIGN_PARAGRAPH.JUSTIFY; spacing(p, 1.5, 0, 6)
            inline(p, el)
        elif el.name == "figure":
            cap = el.find(class_="cap").get_text(" ", strip=True).replace("\xa0", " ")
            fcls = el.get("class") or []
            img = el.find("img"); sv = el.find("svg")
            if img:
                path = os.path.join(HERE, img["src"])
                if "tall" in fcls: add_picture(doc, path, MAXW, 7.0)
                elif "sm" in fcls or "md" in fcls: add_picture(doc, path, 5.0, 8.0)
                else: add_picture(doc, path, 5.6, 8.0)
            else:
                path = pics[state["svg"]]; state["svg"] += 1
                add_picture(doc, path, 6.2, 8.2)
            c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(c, 1.0, 2, 10)
            set_font(c.add_run(cap), 10, True)
        elif el.name == "div" and "keep" in cls:
            cap = el.find(class_="cap").get_text(" ", strip=True).replace("\xa0", " ")
            c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(c, 1.0, 6, 3); c.paragraph_format.keep_with_next = True
            set_font(c.add_run(cap), 10, True)
            html_table(doc, el.find("table"))
        elif el.name == "div" and "algo" in cls:
            for ch in el.children:
                if not isinstance(ch, Tag): continue
                for node in ([ch] if "st" in (ch.get("class") or []) or "bd" in (ch.get("class") or []) else ch.find_all("div", recursive=False)):
                    nc = node.get("class") or []
                    p = doc.add_paragraph(); spacing(p, 1.5, 0, 0 if "st" in nc else 4)
                    if "st" in nc: p.paragraph_format.keep_with_next = True
                    else: p.paragraph_format.left_indent = Inches(0.4); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    set_font(p.add_run(node.get_text().replace("\xa0", " ")), 12, "st" in nc)
        elif el.name == "div" and not cls:
            pass


# ------------------------------------------------------------------ front matter
def logo(doc, width):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(p, 1.0, 0, 6)
    p.add_run().add_picture(os.path.join(HERE, "img", "logo.png"), width=Inches(width))


def students_table(doc, size=14):
    rows = [["PRN", "Name"]] + [[p, n] for p, n in STUDENTS]
    t = simple_table(doc, rows, [1.5, 3.2], size=size, header=False, borders=False, align_cols={0: "c", 1: "c"})
    for c in t.rows[0].cells:
        for r in c.paragraphs[0].runs: r.bold = True
    return t


def cover(doc):
    para(doc, "A Project Report", 16, True, align="c", line=1.0, after=8)
    para(doc, "On", 14, align="c", line=1.0, after=8)
    para(doc, TITLE, 16, True, align="c", line=1.15, after=10)
    para(doc, "For the Degree of", 14, align="c", line=1.0, after=8)
    para(doc, "Bachelor of Technology", 14, True, align="c", line=1.0, after=8)
    para(doc, "In", 14, align="c", line=1.0, after=8)
    para(doc, "Information Technology", 14, True, align="c", line=1.0, after=16)
    para(doc, "Submitted by", 12, align="c", line=1.0, after=4)
    students_table(doc)
    para(doc, "", line=1.0, after=4)
    para(doc, "Under the Guidance of", 14, align="c", line=1.0, after=6)
    para(doc, GUIDE, 14, True, align="c", line=1.0, after=8)
    logo(doc, 1.0)
    para(doc, "Department of Information Technology", 14, True, align="c", line=1.0, after=4)
    para(doc, "Walchand College of Engineering, Sangli", 24, True, align="c", line=1.0, after=0)
    para(doc, "(Government Aided Autonomous Institute)", 12, align="c", line=1.0, after=12)
    para(doc, AY_LONG, 14, True, align="c", line=1.0, after=0)


def certificate(doc):
    page_break(doc)
    logo(doc, 1.0)
    para(doc, "Walchand College of Engineering, Sangli", 24, True, align="c", line=1.0, after=0)
    p = para(doc, "", align="c", line=1.0, after=6)
    set_font(p.add_run("(Government Aided "), 12); set_font(p.add_run("Autonomous Institute"), 12, italic=True); set_font(p.add_run(")"), 12)
    para(doc, "Department of Information Technology", 15, True, align="c", line=1.0, after=8, color="0000CC")
    para(doc, "Certificate", 24, True, align="c", line=1.0, after=8)
    p = para(doc, "", align="j", line=1.5, after=4)
    set_font(p.add_run("This is to certify that the Project Report entitled, "), 12)
    set_font(p.add_run(f"“{TITLE.upper()}”"), 12, True); set_font(p.add_run(" submitted by,"), 12)
    students_table(doc)
    p = para(doc, "", align="j", line=1.5, before=8, after=4)
    set_font(p.add_run("to "), 12); set_font(p.add_run("Walchand College of Engineering, Sangli"), 12, True)
    set_font(p.add_run(", India, is a record of bonafide Project work of course "), 12)
    set_font(p.add_run(f"“{COURSE}”"), 12, True)
    set_font(p.add_run(" carried out by them under my supervision and guidance and is worthy of consideration for the award of the degree of Bachelor of Technology in Information Technology during the academic year "), 12)
    set_font(p.add_run(AY_SHORT), 12, True); set_font(p.add_run("."), 12)
    para(doc, "", line=1.0, after=18)
    t = doc.add_table(rows=1, cols=2); t.autofit = False
    for j, (a, b) in enumerate(((GUIDE, "Guide"), ("", "External Examiner"))):
        c = t.cell(0, j); c.width = Inches(3.25); c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        spacing(c.paragraphs[0], 1.0, 0, 0)
        if a: set_font(c.paragraphs[0].add_run(a), 12, True)
        q = c.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(q, 1.0, 0, 0); set_font(q.add_run(b), 12)
    para(doc, "", line=1.0, after=14)
    para(doc, HEAD, 12, True, align="c", line=1.0, after=0)
    para(doc, "Head", 12, align="c", line=1.0, after=0)
    para(doc, "Department of Information Technology", 12, align="c", line=1.0, after=0)


def acknowledgement(doc):
    page_break(doc)
    para(doc, "Acknowledgement", 24, True, align="c", line=1.0, before=24, after=24)
    for t in [
        "With a deep sense of gratitude, we would like to thank all the people who have lit our path with their kind guidance and helped us complete this project successfully.",
        f"We express our sincere gratitude to our project guide and Head of the Department, {GUIDE}, for his valuable guidance, continuous support and constant encouragement throughout the development of NyayaSetu. His suggestions and the questions he asked us shaped both the design of the system and the way we evaluated it.",
        "We are thankful to the Director of Walchand College of Engineering, Sangli, and to the Project Coordinator for providing the facilities and the opportunity to carry out this work. We thank all the faculty members and the technical and non-technical staff of the Department of Information Technology for their cooperation and feedback during the project.",
        "We also thank our classmates and friends who tested the application and gave honest feedback on the explanations, the Marathi wording and the generated drafts, and our families for their patience and support."]:
        para(doc, t, 12, align="j", line=1.5, after=8)


def vision_and_declaration(doc):
    page_break(doc)
    para(doc, "Vision, Mission & Course Outcomes", 16, True, align="c", line=1.0, before=6, after=10)
    para(doc, "VISION:", 10, True, line=1.0, after=2)
    para(doc, "To be an Information Technology programme as the first choice by the aspiring students and prospective employers by implementing world class education practices", 12, align="j", line=1.0, after=8)
    para(doc, "MISSION:", 10, True, line=1.0, after=2)
    para(doc, "To meet above Vision, all stakeholders of this programme are committed towards Outcome Based Education Philosophy.", 12, align="j", line=1.0, after=8)
    para(doc, "Under-Graduate POs", 10, True, line=1.0, after=4)
    html = C.vision()
    for li in BeautifulSoup(html, "html.parser").find_all("li"):
        p = doc.add_paragraph(style=None); spacing(p, 1.0, 0, 3); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.first_line_indent = Inches(-0.2)
        set_font(p.add_run("●  "), 10); inline(p, li, 12)
    dh = para(doc, "Declaration", 24, True, align="c", line=1.0, before=14, after=8); dh.paragraph_format.keep_with_next = True
    p = para(doc, "", align="j", line=1.5, after=8)
    set_font(p.add_run("We hereby declare that the work presented in this project report titled "), 12)
    set_font(p.add_run(f"“{TITLE.upper()}”"), 12, True)
    set_font(p.add_run(f" submitted by us in the partial fulfilment of the requirement of the award of the degree of Bachelor of Technology (B.Tech) submitted in the Department of Information Technology, Walchand College of Engineering, Sangli, is an authentic record of our project work carried out under the guidance of {GUIDE}, Head, Department of Information Technology, Walchand College of Engineering, Sangli."), 12)
    para(doc, "", line=1.0, after=10)
    for prn, name in STUDENTS:
        para(doc, f"{prn} {name}", 12, True, align="r", line=1.15, after=2)
    p = para(doc, "", line=1.5, before=8, after=0); set_font(p.add_run("Date:"), 10, True)
    p = para(doc, "", line=1.5, after=0); set_font(p.add_run("Place: "), 10, True); set_font(p.add_run("Sangli."), 10)


def content_table(doc, pages):
    page_break(doc)
    para(doc, "Content", 24, True, align="c", line=1.0, before=30, after=28)
    g = lambda k: str(pages.get(k, ""))
    rows = [("S. N.", "Name of the Content", "Page No."), ("i.", "Abbreviations", "i"), ("ii.", "List of Figures", "ii"), ("iii.", "List of Tables", "iii"), ("iv.", "Abstract", "iv"),
            ("1.", "Introduction", g("ch1")), ("2.", "Literature Survey", g("ch2")), ("3.", "Methodology", g("ch3")), ("4.", "Result and Discussion", g("ch4")),
            ("5.", "Conclusion", g("ch5")), ("6.", "References", g("refs")), ("7.", "Annexure", g("annex"))]
    simple_table(doc, [list(r) for r in rows], [0.9, 4.0, 1.2], size=14, header=False, borders=False, align_cols={0: "c", 2: "c"}, line=1.4, bold_first_col=True)
    t = doc.tables[-1]
    for c in t.rows[0].cells:
        for r in c.paragraphs[0].runs: r.bold = True


def heading_page(doc, text):
    p = para(doc, text, 24, True, align="c", line=1.0, before=18, after=22)


def abbreviations(doc):
    heading_page(doc, "Abbreviations")
    rows = [["Abbreviation", "Full Form"]] + [list(x) for x in [
        ("RTI", "Right to Information"), ("PIO", "Public Information Officer"), ("FAA", "First Appellate Authority"), ("LLM", "Large Language Model"),
        ("RAG", "Retrieval-Augmented Generation"), ("OCR", "Optical Character Recognition"), ("RRF", "Reciprocal Rank Fusion"), ("MRR", "Mean Reciprocal Rank"),
        ("FTS", "Full-Text Search"), ("HNSW", "Hierarchical Navigable Small World (index)"), ("API", "Application Programming Interface"),
        ("REST", "Representational State Transfer"), ("JWT", "JSON Web Token"), ("UI", "User Interface"), ("SPA", "Single Page Application"),
        ("JSON", "JavaScript Object Notation"), ("SQL", "Structured Query Language"), ("ER", "Entity Relationship"), ("PDF", "Portable Document Format"),
        ("SMTP", "Simple Mail Transfer Protocol"), ("SMS", "Short Message Service"), ("CI", "Confidence Interval"), ("PRN", "Permanent Registration Number")]]
    simple_table(doc, rows, [1.6, 4.6], size=12, header=True, borders=False, line=1.15)


def list_page(doc, title, head, items, pages, prefix):
    page_break(doc)
    heading_page(doc, title)
    rows = [list(head)] + [[i, t, str(pages.get(prefix + i, ""))] for i, t in items]
    simple_table(doc, rows, [0.8, 4.9, 0.8], size=12 if len(items) > 12 else 14, header=False, borders=False, align_cols={0: "c", 2: "c"}, line=1.0, bold_first_col=True)
    t = doc.tables[-1]
    for c in t.rows[0].cells:
        for r in c.paragraphs[0].runs: r.bold = True


def abstract(doc):
    page_break(doc)
    heading_page(doc, "Abstract")
    for p in BeautifulSoup(C.abstract(), "html.parser").find_all("p"):
        q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; spacing(q, 1.5, 0, 6); inline(q, p)


def references(doc):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(p, 1.0, 0, 0); p.paragraph_format.page_break_before = True
    set_font(p.add_run("References"), 24, True)
    d = doc.add_paragraph(); spacing(d, 1.0, 0, 14); bottom_border(d)
    for i, r in enumerate(C.REFS, 1):
        soup = BeautifulSoup(f"<p>[{i}] {r}</p>", "html.parser").p
        q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; spacing(q, 1.15, 0, 6)
        q.paragraph_format.left_indent = Inches(0.4); q.paragraph_format.first_line_indent = Inches(-0.4)
        inline(q, soup)


def annexure(doc):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(p, 1.0, 0, 0); p.paragraph_format.page_break_before = True
    set_font(p.add_run("Annexure"), 24, True)
    d = doc.add_paragraph(); spacing(d, 1.0, 0, 14); bottom_border(d)
    h = doc.add_paragraph(); spacing(h, 1.5, 6, 3); h.paragraph_format.keep_with_next = True
    set_font(h.add_run("Annexure A: Database Tables"), 14, True)
    para(doc, "The tables created by the Flyway migrations (V1 and V2) in the PostgreSQL database.", 12, align="j")
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(c, 1.0, 6, 3); c.paragraph_format.keep_with_next = True
    set_font(c.add_run("Table A.1:  Database Tables"), 10, True)
    simple_table(doc, [["Table (schema)", "Purpose"],
                       ["users (public)", "Registered users, hashed passwords, preferred language, alert settings"],
                       ["documents (public)", "Uploaded files: original name, stored path, size, SHA-256, status, extracted text"],
                       ["processing_results (public)", "Explanation JSON, sources, model used, status of each document"],
                       ["deadlines (public)", "Deadlines extracted from documents, due dates, completion and reminder stage"],
                       ["chat_messages (public)", "Questions and answers of the follow-up chat, with the legal sources used"],
                       ["notification_log (public)", "E-mail and SMS reminders sent, with success or error details"],
                       ["kb_chunks (kb)", "Knowledge base chunks with text, tsvector for keyword search and vector(384) embedding"]],
                 [2.2, 4.3], size=11, line=1.0)
    para(doc, "", line=1.0, after=8)
    h = doc.add_paragraph(); spacing(h, 1.5, 6, 3); h.paragraph_format.keep_with_next = True; h.paragraph_format.page_break_before = True
    set_font(h.add_run("Annexure B: Configuration Settings"), 14, True)
    para(doc, "NyayaSetu is configured through an environment file (.env); secrets are never committed. The main groups of settings are listed below.", 12, align="j")
    c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(c, 1.0, 6, 3); c.paragraph_format.keep_with_next = True
    set_font(c.add_run("Table A.2:  Main Configuration Settings"), 10, True)
    simple_table(doc, [["Group", "Settings"],
                       ["Database", "POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD"],
                       ["Security", "JWT_SECRET, JWT_EXPIRATION_MINUTES, INTERNAL_TOKEN, CORS_ALLOWED_ORIGINS, MAX_UPLOAD_MB"],
                       ["Language model", "LLM_PROVIDER, LLM_MODEL, LLM_FALLBACK_MODELS, FALLBACK_LLM_PROVIDER, FALLBACK_LLM_MODEL"],
                       ["Retrieval", "EMBEDDING_MODEL, EMBEDDING_DIM, RERANKER, RERANKER_MODEL"],
                       ["Reminders", "ALERTS_ENABLED, ALERTS_CRON, ALERTS_REMINDER_DAYS, MAIL_HOST, SMS_PROVIDER"],
                       ["Deployment", "FRONTEND_PORT; VITE_API_URL when the frontend is hosted separately"]],
                 [1.6, 4.9], size=11, line=1.0)
    para(doc, "", line=1.0, after=8)
    para(doc, "Start-up: copy .env.example to .env, fill in the secrets and an LLM key, then run “docker compose up --build”. The application is then available on the frontend port.", 12, align="j")


# ------------------------------------------------------------------ assemble
def build(pages, pics_cache={}):
    C.FIGS.clear(); C.TABS.clear()
    body_html = C.ch1() + C.ch2() + C.ch3() + C.ch4() + C.ch5()
    soup = BeautifulSoup(f"<div id='root'>{body_html}</div>", "html.parser")
    root = soup.find(id="root")
    svgs = [str(s) for s in root.find_all("svg")]
    if "pics" not in pics_cache or len(pics_cache["pics"]) != len(svgs):
        pics_cache["pics"] = svg_pngs(svgs)
    pics = pics_cache["pics"]

    doc = Document()
    st = doc.styles["Normal"]; st.font.name = FONT; st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT); st.font.size = Pt(12)
    s0 = doc.sections[0]
    s0.page_width, s0.page_height = Inches(8.5), Inches(11)
    for a in ("left_margin", "right_margin", "top_margin", "bottom_margin"): setattr(s0, a, Inches(1))
    s0.footer_distance = Inches(0.5)
    footer_none(s0)
    # --- unnumbered front pages
    cover(doc); certificate(doc); acknowledgement(doc); vision_and_declaration(doc); content_table(doc, pages)
    # --- roman-numbered front matter
    s1 = new_section(doc); set_pgnum(s1, "lowerRoman", 1); footer_roman(s1)
    abbreviations(doc)
    list_page(doc, "List of Figures", ("S. N.", "Content", "Page No."), C.FIGS, pages, "fig")
    list_page(doc, "List of Tables", ("S. N.", "Content", "Page No."), C.TABS + [("A.1", "Database Tables"), ("A.2", "Main Configuration Settings")], pages, "tab")
    abstract(doc)
    # --- body
    s2 = new_section(doc); set_pgnum(s2, "decimal", 1); footer_body(s2)
    # remove the empty first paragraph python-docx leaves at the start of the section
    walk(doc, root, pics)
    references(doc); annexure(doc)
    return doc


def pdf_of(docx_path):
    outdir = os.path.dirname(docx_path)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, docx_path], check=True, capture_output=True)
    return docx_path[:-5] + ".pdf"


def find_pages(pdf):
    import pymupdf as fitz
    d = fitz.open(pdf)
    texts = [p.get_text() for p in d]
    start = next(i for i, t in enumerate(texts) if t.strip().startswith("1 | Introduction"))
    pages = {}
    def look(key, label, frm=start):
        for i in range(frm, len(texts)):
            if key in texts[i]: pages[label] = i - start + 1; return
    for n, t in [(1, "Introduction"), (2, "Literature Survey"), (3, "Methodology"), (4, "Result and Discussion"), (5, "Conclusion")]:
        look(f"{n} | {t}", f"ch{n}")
    for fid, _ in C.FIGS: look(f"Figure {fid}:", "fig" + fid)
    for tid, _ in C.TABS: look(f"Table {tid}:", "tab" + tid)
    for lab, key in (("A.1", "Table A.1:"), ("A.2", "Table A.2:")): look(key, "tab" + lab)
    for i in range(start, len(texts)):
        s = texts[i].strip()
        if s.startswith("References") and "refs" not in pages: pages["refs"] = i - start + 1
        if s.startswith("Annexure") and "annex" not in pages: pages["annex"] = i - start + 1
    return pages, len(d)


if __name__ == "__main__":
    pages = {}
    doc = build(pages); doc.save(OUT_DOCX)
    pdf = pdf_of(OUT_DOCX); pages, n = find_pages(pdf)
    doc = build(pages); doc.save(OUT_DOCX)
    pdf = pdf_of(OUT_DOCX); pages2, n = find_pages(pdf)
    if pages2 != pages:   # numbers shifted because the lists changed width: one more pass
        doc = build(pages2); doc.save(OUT_DOCX); pdf = pdf_of(OUT_DOCX); pages2, n = find_pages(pdf)
    print("pages:", n, "->", OUT_DOCX, OUT_PDF)
