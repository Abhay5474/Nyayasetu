"""Builds MailMind-Executive-Summary.docx (3 pages), same layout as the NyayaSetu summary.

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
det = {"students": [{"prn": "23610055", "name": "Animesh Ghawale"}], "guide": "Dr. U. B. Chavan"}
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
title("MailMind: Executive Summary", "An ambient AI agent that handles routine email and asks a human before anything is sent")

h("The problem we kept running into")
para("Email is where most professional work arrives, and a large part of it is routine: a meeting request, an acknowledgement, a status question. Each one still has to be opened, understood, checked against a calendar, answered and sent. Studies often quoted in the literature put this at more than a quarter of a knowledge worker's week, and the constant switching between mail and real work makes it worse.")
para("The tools we found do not close the gap. Gmail filters and rules are fast but cannot understand what a message means, and they need constant upkeep. Chat-style AI assistants understand the message but only when you copy it in, ask, copy the draft back and press send. At the other extreme, fully autonomous email agents would read, draft and send on their own, and a wrong reply, a wrong booking or a message to the wrong person cannot be taken back.")
para("None of these problems is about whether a model can write a decent reply; it usually can. They are about the structure around the model: who decides, what is allowed to happen on its own, and what the system learns when a person corrects it. That is the part we decided to build.")

h("What MailMind is")
para("MailMind is an ambient agent. It runs in the background, watches a live Gmail inbox, and reacts to each new message without being asked. It does all the thinking: it decides whether a message needs a reply, checks the calendar, and writes the draft. It stops at the one step that cannot be undone, and asks a person to approve, edit or deny. The simplest way we found to explain it: MailMind is a capable assistant who prepares every reply and puts it on your desk, but never signs anything for you.")
para("It is not a chatbot, because it does not wait for a prompt, and it is not fully autonomous, because nothing leaves your account without a human decision.")

h("What it does, in six jobs")
para("New unread messages are fetched through the Gmail API with read-only access, marked as read, and each is handled in its own task so one slow email never blocks another.", "1. It watches the inbox.")
para("A Gemini model sorts every message into one of three labels: respond, notify the human, or ignore. Routine noise is dropped, and only what matters moves on.", "2. It triages.")
para("For messages that need an answer, a ReAct-style agent uses tools: it checks Google Calendar free and busy time in the Asia/Kolkata timezone, can create an event with a Google Meet link, and drafts a professional reply that mentions real available slots.", "3. It checks the calendar and drafts a reply.")
para("The workflow pauses before any send or calendar booking. Safe results, such as an availability lookup, are shown without approval; dangerous actions wait. The person sends approve, edit (with the revised text) or deny, and only an approved action is executed.", "4. It asks before it acts.")
para("Every outcome is written to a SQLite database: the email history, the original and edited draft pairs, the cases where the person overrode the triage label, and patterns learned from edits. If you always delete the formal greeting, the next draft for that sender omits it. If you reclassify a message, that correction becomes an example in the next triage prompt for that sender.", "5. It learns from corrections.")
para("A small FastAPI service exposes the health check, polling, the pending-approval queue and the decision endpoint, and a web dashboard shows each pending email beside its draft with Approve, Edit and Deny buttons.", "6. It gives you a place to decide.")

h("How it is built")
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_after = Pt(2)
p.add_run().add_picture(os.path.join(HERE, "img", "mailmind_flow.png"), width=Emu(int(6.0 * 914400)))
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(p, "Figure 1: The MailMind workflow, from a new email to a human-approved action", italic=True, size=9.5)
para("The core is a LangGraph state machine with four nodes (triage, react_agent, hitl_checkpoint and execute_action) that share one typed state carrying the email, the triage decision, tool results, the pending action and the human feedback. The graph is compiled to pause before the checkpoint node and keeps its state in a SQLite checkpoint store, so a workflow can wait for hours and resume exactly where it stopped. The application is written in Python 3.11 with FastAPI, LangChain's Gemini wrapper, and the Gmail and Calendar APIs behind OAuth 2.0 with minimal scopes. The triage model runs at temperature 0 for consistency and the drafting model at 0.3 for natural phrasing.")
para("Two engineering problems shaped the design. Resuming a paused workflow by invoking the graph again restarted it from the first node and deadlocked on the checkpoint; we fixed this by executing the approved action directly after reading the saved state. And the model's tool-binding was unreliable in the library version we used, so a keyword and intent router dispatches the three tools instead.")

h("What we measured")
para("We did not want to rely on claims, so we hand-labelled 16 emails across the three categories and measured triage with accuracy, per-category accuracy and a confusion matrix, and we timed every node of the pipeline before and after optimisation.")
table([("What we measured", "Result"),
       ("Triage accuracy, first prompt", "31.25% (everything labelled ignore)"),
       ("Triage accuracy, redesigned prompt", "81.25% (13 of 16), with the same model"),
       ("Time for a respond email, end to end", "about 145 s down to about 13 s"),
       ("Time for an ignore email", "about 4 s"),
       ("Approve, edit and deny paths", "all three behaved as expected; no unapproved sends"),
       ("Dangerous-action detection", "5 of 5 test scenarios routed correctly"),
       ("Memory", "7 SQLite tables; edits and corrections changed later drafts and triage")])
doc.add_paragraph().paragraph_format.space_after = Pt(2)
para("The accuracy gain came from the prompt, not a bigger model: we added a statement of what the agent can do, explicit rules with positive and negative examples for each label, a decision checklist and a fixed JSON output. The speed-up came from switching off the model's extra reasoning budget and compiling the graph once at startup instead of on every request.")
para("A few honest caveats. The evaluation set has only 16 emails, labelled by us, so 81.25% is a development figure rather than a general claim, and the three remaining errors were genuinely ambiguous messages. The drafts themselves were judged by reading them, not by an automated quality score. The system runs for one user on SQLite, and new mail is found by polling, not instantly.")

h("Where it stands, and what is next")
para("MailMind works end to end today against a live Gmail account: it triages, drafts with real calendar data, waits for a human decision, sends only what is approved, and remembers the outcome. Its limits are clear to us: it serves a single mailbox, relies on polling, and its triage numbers come from a small test set.")
para("The next steps we would take are moving from polling to Gmail push notifications through Pub/Sub, re-trying model-driven function calling to replace the keyword router, a real-time dashboard with WebSocket approval cards, a dedicated memory-loading node, a larger independently labelled test set with an automated judge for draft quality, and a PostgreSQL backend so several users can share the system.")
para("No agent can make every judgement for you. What MailMind does is take over the reading, checking and writing, and leave the single decision that matters, whether to send, with the person it belongs to.")
para(f"{det['students'][0]['name']} ({det['students'][0]['prn']}), under the guidance of {det['guide']}, Department of Information Technology, Walchand College of Engineering, Sangli.", italic=True)

# ------------------------------------------------------------------ footer: "NyayaSetu · Executive Summary · <page>"
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run(fp, "NyayaSetu · Executive Summary · ", size=9)
r = fp.add_run(); r.font.size = Pt(9)
for kind, txt in (("begin", None), (None, "PAGE"), ("end", None)):
    if kind:
        e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind); r._r.append(e)
    else:
        e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)

out = os.path.join(HERE, "MailMind-Executive-Summary.docx")
doc.save(out)
print("saved", out)
