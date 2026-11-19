"""Builds NyayaSetu-Executive-Summary.docx (2-3 pages) in the layout of the Continuum executive summary.

   pip install python-docx
   python exec_summary.py
Names / PRNs come from student_details.json (git-ignored), like the project report.
"""
import json, os
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Twips, Emu

HERE = os.path.dirname(os.path.abspath(__file__))
det = json.load(open(os.path.join(HERE, "student_details.json" if os.path.exists(os.path.join(HERE, "student_details.json")) else "student_details.example.json"), encoding="utf-8"))
BLUE = RGBColor(0x1F, 0x3A, 0x5F)
FONT = "Times New Roman"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Twips(11906), Twips(16838)
sec.top_margin, sec.bottom_margin, sec.left_margin, sec.right_margin = Twips(1150), Twips(1100), Twips(1300), Twips(1300)
sec.header_distance = sec.footer_distance = Twips(708)

st = doc.styles["Normal"]
st.font.name = FONT
st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
st.font.size = Pt(11.5)
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.08


def run(p, text, bold=False, italic=False, size=None, color=None):
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size: r.font.size = Pt(size)
    if color is not None: r.font.color.rgb = color
    return r


def border_bottom(p):
    pPr = p._p.get_or_add_pPr()
    b = OxmlElement("w:pBdr")
    e = OxmlElement("w:bottom")
    for k, v in (("val", "dashed"), ("color", "6B7480"), ("sz", "6"), ("space", "6")): e.set(qn("w:" + k), v)
    b.append(e); pPr.append(b)


def title(text, sub):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(3)
    run(p, text, bold=True, size=18)
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(10)
    run(p, sub, italic=True, size=11); border_bottom(p)


def h(text):
    p = doc.add_paragraph(); p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(9), Pt(4)
    run(p, text, bold=True, size=12.5, color=BLUE)


def para(text, lead=None, italic=False):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if lead: run(p, lead + " ", bold=True)
    run(p, text, italic=italic)
    return p


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), fill); tcPr.append(s)


def borders(cell, color="8A939E"):
    tcPr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + side)
        for k, v in (("val", "single"), ("sz", "4"), ("color", color)): e.set(qn("w:" + k), v)
        b.append(e)
    tcPr.append(b)
    m = OxmlElement("w:tcMar")
    for side, w in (("top", 50), ("left", 100), ("bottom", 50), ("right", 100)):
        e = OxmlElement("w:" + side); e.set(qn("w:w"), str(w)); e.set(qn("w:type"), "dxa"); m.append(e)
    tcPr.append(m)


def table(rows, widths=(5600, 3426)):
    t = doc.add_table(rows=len(rows), cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    for i, (a, b) in enumerate(rows):
        tr = t.rows[i]
        trPr = tr._tr.get_or_add_trPr(); trPr.append(OxmlElement("w:cantSplit"))
        for j, txt in enumerate((a, b)):
            c = tr.cells[j]; c.width = Twips(widths[j]); borders(c)
            if i == 0: shade(c, "E8EDF3")
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0
            run(p, txt, bold=(i == 0), size=10)
    return t


# ------------------------------------------------------------------ content
title("NyayaSetu: Executive Summary",
      "A bilingual, source-grounded assistant for understanding legal and RTI documents")

h("The problem we kept running into")
para("Almost everyone eventually receives a document they must act on: a reply to a Right to Information (RTI) application, a notice from a municipal office, a fee demand, a court order. These documents are written in formal English, they refer to sections of an Act by number, and the one sentence that matters, for example that you have thirty days to file a first appeal, is buried in the middle. Most people either pay someone to read it for them or put it aside and hope for the best.")
para("A general AI chatbot looks like the obvious answer. It explains things fluently, but it answers from memory, so it can quote a section number that does not say what it claims, it has no reliable knowledge of the Maharashtra RTI Rules, it cannot show where a statement came from, and it never reminds anybody of a deadline. A wrong answer about a legal time limit is worse than no answer, because the person trusts it.")
para("None of these problems is about the model being clever enough. They are about what surrounds the model: the sources it is allowed to use, the checks on what it says, the language the reader is comfortable in, and what happens after the explanation. That is the part we decided to build.")

h("What NyayaSetu is")
para("NyayaSetu (Marathi: “bridge to justice”) is a web application. A person uploads a PDF or a photograph of a document and, within a short time, gets a plain-language explanation in English or Marathi: a short summary, the key points, what they need to do, the deadlines, and the legal provisions the explanation relies on, each linked to its source. The simplest way we found to explain it: a general chatbot is a well-read friend who answers from memory, and NyayaSetu is a clerk who first opens the law book to the right page, reads your letter, and shows you the page that was used.")
para("It does not give legal advice, and says so on every screen. Its job is narrower and more achievable: to make sure that a citizen understands what a document says, what the next step is and by when, and to take the effort out of writing the first reply.")

h("What it does, in six jobs")
para("A digital PDF is read directly. A scan or a phone photograph goes through OCR in Marathi, Hindi and English, so a typed reply and a crumpled notice take the same path.", "1. It reads whatever you have.")
para("The whole result, and the whole interface, can be switched between English and Marathi. The explanation always has the same shape (summary, key points, actions, deadlines, references), so a reader learns where to look.", "2. It explains in your language.")
para("Before the language model writes anything, the system looks up the relevant provisions in a knowledge base of 318 entries taken from official texts, mainly the RTI Act, 2005 and the Maharashtra RTI Rules. Every source the model cites must be one of the passages it was given; anything else is dropped. Each source carries a badge showing whether it is official text, a government reprint or an unverified summary, and repealed or superseded provisions are never searched.", "3. It shows its sources.")
para("Dates and periods in the document (“within 30 days of receipt of this reply”) become deadline cards. A daily scheduler sends e-mail or SMS reminders 7, 3 and 1 days before, and on the day itself.", "4. It remembers dates for you.")
para("A second tab lets the user ask questions about the document in either language. Answers come only from the document and the knowledge base, carry their legal sources, and show a quotation from the document only if it can be found there word for word.", "5. It answers follow-up questions.")
para("The user answers a few questions and receives a ready-to-file RTI application, first appeal or fee-payment reply, in English or Marathi, laid out on the official annexures of the Maharashtra RTI Rules and downloadable as PDF or Word. Dates are checked, for instance a draft cannot be dated in the future.", "6. It writes the first reply.")
para("If one language-model provider is slow, out of free quota or down, the request quietly moves to the next one in a configured chain, so a demo or a real user does not meet the error.")

h("How it is built")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
p.add_run().add_picture(os.path.join(HERE, "img", "arch.png"), width=Emu(int(4.1 * 914400)))
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Figure 1: How the four services of NyayaSetu fit together", italic=True, size=9.5)
para("There are four services. The web interface is a React single-page app served by nginx, which also forwards every API call. A Spring Boot 3 (Java 21) gateway handles sign-in with 12-hour tokens, validates and stores uploads, runs each document as a background job, schedules reminders and passes work to the AI service over a private network with a shared token. A FastAPI (Python 3.12) AI service does the reading, the retrieval, the language-model calls and the drafting. PostgreSQL 16 with the pgvector extension holds users, documents, results and deadlines, and the knowledge base in a separate schema, managed by versioned migrations. The whole platform starts with a single Docker Compose command, and the interface can also be hosted separately, for example on Vercel, for a demo.")
para("Retrieval is where we spent the most care. For each document the system searches the knowledge base in two ways at once: by meaning, with a multilingual embedding model and an HNSW vector index, which lets a Marathi question find an English section, and by keywords, weighted so that rare words count more than filler, which is better at exact terms like a section number. The two ranked lists are merged with Reciprocal Rank Fusion, and a multilingual cross-encoder re-reads the best sixteen candidates together with the question to pick the top six for the model.")

h("What we measured")
para("We did not want to rely on claims, so we wrote 57 test questions (in English and Marathi, some phrased the way a worried citizen would ask and some in legal vocabulary), recorded which provision answers each one, and compared five retrieval set-ups with real models. MRR is the average of 1 divided by the rank of the right answer, so higher is better; Hit@3 is how often it is in the top three.")
table([("What we measured", "Result"),
       ("Knowledge base", "318 entries, 467 searchable chunks, from official texts"),
       ("Vector search alone", "MRR 0.559, Hit@3 67%"),
       ("Keyword search alone", "MRR 0.373, Hit@3 44%"),
       ("Full pipeline (hybrid + re-ranker)", "MRR 0.702, Hit@3 82%"),
       ("English vs Marathi questions (full pipeline)", "MRR 0.744 vs 0.605"),
       ("Direct vs informally phrased questions", "MRR 0.766 vs 0.465"),
       ("Automated tests", "101 AI service, 27 gateway, 11 frontend")])
doc.add_paragraph().paragraph_format.space_after = Pt(2)
para("A few honest caveats. The 57 questions were written by us and are few, and the confidence intervals of the last two methods overlap, so we report the ordering as consistent rather than proven. Marathi and informally phrased questions retrieve clearly worse than English and direct ones. Testing found a real defect, in which the keyword search let common words decide the ranking; weighting words by how rare they are fixed it, and the numbers above include the fix. We have not run a formal user study, so how helpful the explanations are to real citizens is still untested. The knowledge base mainly covers RTI, and a Marathi draft should be read by a Marathi speaker before it is filed.")

h("Where it stands, and what is next")
para("NyayaSetu works end to end today: upload, explanation, sources, follow-up questions, deadlines with reminders, and drafts in both languages. The limits are clear to us. The knowledge base is small, answers are only as good as the model behind them, and the system explains and prepares documents but cannot decide whether someone should appeal.")
para("The next steps we would take are widening the knowledge base to more Acts and state rules, improving Marathi and informal-question retrieval with a larger test set, adding voice input and read-aloud for people who cannot read well, adding Hindi and other regional languages, letting a user share a draft with a legal-aid volunteer for review, and running a small trial with real users.")
para("No tool can remove the uncertainty of the law or replace a lawyer for an important decision. What NyayaSetu does is give a citizen the first and most important step: to know what the document says, and what to do, before the deadline passes.")
names = " and ".join(f"{s['name'].split('. ', 1)[-1]} ({s['prn']})" for s in det["students"])
para(f"{names}, under the guidance of {det['guide']}, Department of Information Technology, Walchand College of Engineering, Sangli.", italic=True)

# ------------------------------------------------------------------ footer: "NyayaSetu · Executive Summary · <page>"
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(fp, "NyayaSetu · Executive Summary · ", size=9)
r = fp.add_run(); r.font.size = Pt(9)
for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if kind:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind); r._r.append(e)
    else:
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)

out = os.path.join(HERE, "NyayaSetu-Executive-Summary.docx")
doc.save(out)
print("saved", out)
