"""Figure generators for the project report (inline SVG, drawn in the style of the reference report: coloured boxes, black arrows)."""
import json, os, re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = "font-family:'Liberation Sans','DejaVu Sans',Arial,sans-serif"
DEFS = ('<defs><marker id="{id}" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#222"/></marker>'
        '<marker id="{id}d" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="#555"/></marker></defs>')


def svg(w, h, body, uid, label):
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{escape(label)}" style="{FONT}">'
            + DEFS.format(id=uid) + body + "</svg>")


def text(x, y, s, size=11, bold=False, anchor="middle", fill="#111", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{fill}" font-weight="{700 if bold else 400}" {extra}>{escape(s)}</text>'


def box(x, y, w, h, lines, fill="#e8f1fb", stroke="#2b6cb0", size=10.5, title=None, rx=8, tcolor="#111", dark=False):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>']
    n = len(lines) + (1 if title else 0)
    lh = size + 4
    y0 = y + h / 2 - (n - 1) * lh / 2 + size / 3
    k = 0
    col = "#fff" if dark else tcolor
    if title:
        out.append(text(x + w / 2, y0, title, size + 0.5, True, fill=col)); k = 1
    for i, ln in enumerate(lines):
        out.append(text(x + w / 2, y0 + (k + i) * lh, ln, size, False, fill=col))
    return "".join(out)


def arrow(x1, y1, x2, y2, uid, dashed=False, label=None, lx=None, ly=None, lsize=9):
    d = ' stroke-dasharray="5 4"' if dashed else ""
    o = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#222" stroke-width="1.4"{d} marker-end="url(#{uid})"/>'
    if label:
        o += text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 - 4, label, lsize, fill="#333")
    return o


def poly(points, uid, dashed=False):
    d = ' stroke-dasharray="5 4"' if dashed else ""
    return f'<polyline points="{" ".join(f"{a},{b}" for a, b in points)}" fill="none" stroke="#222" stroke-width="1.4"{d} marker-end="url(#{uid})"/>'


# ----------------------------------------------------------------------------- use case diagram
def usecase():
    u = "uc"
    W, H = 780, 640
    b = []
    b.append(f'<rect x="150" y="18" width="480" height="604" rx="6" fill="#fcfcfd" stroke="#333" stroke-width="1.5"/>')
    b.append(text(390, 40, "NyayaSetu – Legal & RTI Document Simplifier", 13, True))
    b.append(text(390, 55, "System boundary", 9, fill="#555"))

    def ell(cx, cy, label, fill, stroke, w=150, h=34):
        lines = label.split("\n")
        o = f'<ellipse cx="{cx}" cy="{cy}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>'
        for i, ln in enumerate(lines):
            o += text(cx, cy + 3.5 + (i - (len(lines) - 1) / 2) * 11.5, ln, 9.5)
        return o

    A = [("Register / Login", 95), ("Upload Document\n(PDF / Image)", 155), ("View Explanation\n(English / Marathi)", 215), ("Ask Follow-up\nQuestions", 275),
         ("Track Deadlines", 335), ("Generate Draft\n(RTI / Appeal / Fee reply)", 395), ("Download PDF / Word", 455), ("Manage Profile\n& Alerts", 515)]
    S = [("Extract Text\n(PDF text / OCR)", 155), ("Retrieve Legal Sources\n(hybrid search + rerank)", 215), ("Generate & Validate\nExplanation", 275),
         ("Capture Deadlines", 335), ("Send Reminders\n(E-mail / SMS)", 395), ("Build Draft Document", 455)]
    for lab, y in A:
        b.append(ell(255, y, lab, "#e6effa", "#2b6cb0", 158, 40 if "\n" in lab else 32))
    for lab, y in S:
        b.append(ell(520, y, lab, "#fdf0d8", "#c27a14", 168, 42 if "\n" in lab else 32))
    # actors
    def actor(x, y, label):
        return (f'<circle cx="{x}" cy="{y}" r="9" fill="#fff" stroke="#222" stroke-width="1.4"/><line x1="{x}" y1="{y+9}" x2="{x}" y2="{y+38}" stroke="#222" stroke-width="1.4"/>'
                f'<line x1="{x-16}" y1="{y+20}" x2="{x+16}" y2="{y+20}" stroke="#222" stroke-width="1.4"/><line x1="{x}" y1="{y+38}" x2="{x-13}" y2="{y+60}" stroke="#222" stroke-width="1.4"/>'
                f'<line x1="{x}" y1="{y+38}" x2="{x+13}" y2="{y+60}" stroke="#222" stroke-width="1.4"/>' + text(x, y + 76, label, 10, True))
    b.append(actor(70, 270, "Citizen (User)"))
    for lab, y in A:
        b.append(f'<line x1="86" y1="{300}" x2="{255-79}" y2="{y}" stroke="#555" stroke-width="1"/>')
    # include relations
    inc = [(155, 155, "Upload Document", "Extract Text"), (215, 215, "View Explanation", "Retrieve Legal Sources"), (275, 275, "Ask", "Generate")]
    b.append(poly([(334, 155), (434, 155)], u + "d", True)); b.append(text(384, 148, "«include»", 8.5, fill="#444"))
    b.append(poly([(334, 215), (434, 215)], u + "d", True)); b.append(text(384, 208, "«include»", 8.5, fill="#444"))
    b.append(poly([(334, 275), (434, 275)], u + "d", True)); b.append(text(384, 268, "«include»", 8.5, fill="#444"))
    b.append(poly([(334, 335), (434, 335)], u + "d", True)); b.append(text(384, 328, "«include»", 8.5, fill="#444"))
    b.append(poly([(334, 395), (434, 455)], u + "d", True)); b.append(text(392, 420, "«include»", 8.5, fill="#444"))
    b.append(poly([(520, 176), (520, 198)], u + "d", True)); b.append(poly([(520, 236), (520, 254)], u + "d", True))
    # external actors
    def ext(x, y, w, h, title, sub):
        return box(x, y, w, h, sub.split("|"), "#efe9f7", "#6b46c1", 8.5, title=title)
    b.append(ext(648, 185, 124, 62, "LLM Provider", "Groq · Gemini|Anthropic · OpenAI"))
    b.append(ext(648, 300, 124, 62, "Knowledge Base", "PostgreSQL + pgvector"))
    b.append(ext(648, 380, 124, 62, "Notification Services", "SMTP · Twilio SMS"))
    b.append(poly([(604, 275), (630, 275), (630, 230), (646, 230)], u + "d", True))
    b.append(poly([(604, 215), (624, 215), (624, 325), (646, 325)], u + "d", True))
    b.append(poly([(604, 395), (646, 405)], u + "d", True))
    return svg(W, H, "".join(b), u, "Use case diagram")


# ----------------------------------------------------------------------------- architecture
def architecture():
    u = "ar"
    W, H = 760, 640
    b = []
    b.append(text(380, 24, "NyayaSetu – Proposed System Architecture", 15, True))
    b.append(f'<rect x="60" y="40" width="640" height="84" rx="8" fill="#2b6cb0"/>')
    b.append(text(380, 60, "① Web Interface — React SPA served by nginx", 11.5, True, fill="#fff"))
    for i, t in enumerate(["Dashboard", "Explanation", "Ask Questions", "Deadlines", "Drafts"]):
        b.append(box(78 + i * 124, 74, 112, 36, [t], "#6b46c1", "#d6c9f2", 10, dark=True, rx=6))
    b.append(arrow(380, 124, 380, 148, u, label="HTTPS  /api/*", lx=450, ly=140))
    b.append(box(250, 148, 260, 40, ["nginx reverse proxy · CSP & security headers"], "#2d3748", "#4a5568", 10, dark=True, rx=6))
    b.append(arrow(380, 188, 380, 214, u, label="JWT (Bearer)", lx=440, ly=206))
    b.append(f'<rect x="60" y="214" width="640" height="108" rx="8" fill="#ebf4ff" stroke="#2b6cb0" stroke-width="1.5"/>')
    b.append(text(380, 234, "② Backend Gateway — Spring Boot 3 (Java 21)", 11.5, True))
    for i, t in enumerate(["Auth & JWT", "Upload &\nStorage", "Job\nOrchestration", "Chat &\nDeadlines", "Alert\nScheduler", "Draft\nProxy"]):
        lines = t.split("\n")
        b.append(box(72 + i * 104, 246, 96, 60, lines, "#2d3748", "#4a5568", 9.5, dark=True, rx=6))
    b.append(arrow(380, 322, 380, 352, u, label="REST + X-Internal-Token", lx=300, ly=342))
    b.append(f'<rect x="40" y="352" width="680" height="132" rx="8" fill="#e8f7ef" stroke="#1f7a5a" stroke-width="1.5"/>')
    b.append(text(380, 372, "③ AI Service — FastAPI (Python 3.12)", 11.5, True))
    eng = [("Extraction Engine", ["PyMuPDF text", "Tesseract OCR", "Cleaning"]), ("RAG Engine", ["Embeddings", "Hybrid search + RRF", "Cross-encoder"]),
           ("LLM Engine", ["Prompts + schema", "Fallback chain", "Grounding"]), ("Draft Engine", ["EN/MR templates", "PDF (PyMuPDF)", "Word (python-docx)"])]
    for i, (t, ls) in enumerate(eng):
        b.append(box(52 + i * 166, 384, 156, 92, ls, "#2d3748", "#4a5568", 9.5, title=t, dark=True, rx=6))
    b.append(arrow(560, 484, 560, 514, u, label="psycopg", lx=598, ly=506))
    b.append(box(300, 514, 400, 70, ["schema public — users, documents, results,", "deadlines, chat_messages, notification_log", "schema kb — kb_chunks (text · tsvector · vector(384))"], "#fff", "#222", 9.5, title="④ PostgreSQL 16 + pgvector"))
    b.append(box(60, 514, 200, 70, ["/data/uploads (original files,", "random names)"], "#fff", "#777", 9.5, title="Uploads volume"))
    b.append(poly([(150, 322), (20, 322), (20, 548), (58, 548)], u, True))
    b.append(text(8, 440, "files", 9, fill="#444", extra='transform="rotate(-90 8 440)"'))
    b.append(poly([(660, 322), (660, 337), (736, 337), (736, 540), (702, 540)], u, True))
    b.append(text(722, 440, "JDBC", 9, fill="#444", extra='transform="rotate(90 722 440)"'))
    b.append(box(60, 596, 290, 38, ["Groq · Gemini · Anthropic · OpenAI · Ollama (HTTPS)"], "#efe9f7", "#6b46c1", 9.5, rx=6))
    b.append(box(410, 596, 290, 38, ["SMTP e-mail · Twilio SMS (optional reminders)"], "#efe9f7", "#6b46c1", 9.5, rx=6))
    return svg(W, H, "".join(b), u, "System architecture")


# ----------------------------------------------------------------------------- flowchart
def flowchart():
    u = "fl"
    W, H = 680, 980
    b = []
    cx = 340

    def term(y, label):
        return f'<rect x="{cx-70}" y="{y}" width="140" height="30" rx="15" fill="#e6f4ea" stroke="#2f855a" stroke-width="1.5"/>' + text(cx, y + 19.5, label, 11, True)

    def proc(y, lines, fill="#e8f1fb", stroke="#2b6cb0", w=250):
        h = 16 + 14 * len(lines)
        o = f'<rect x="{cx-w/2}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        for i, ln in enumerate(lines):
            o += text(cx, y + 18 + i * 14, ln, 10.5, i == 0 and len(lines) > 1)
        return o, h

    def dec(y, label, w=210, h=52):
        pts = f"{cx},{y} {cx+w/2},{y+h/2} {cx},{y+h} {cx-w/2},{y+h/2}"
        return f'<polygon points="{pts}" fill="#fff4d6" stroke="#c27a14" stroke-width="1.5"/>' + text(cx, y + h / 2 + 4, label, 10.5, True)

    y = 10
    b.append(term(y, "Start")); y += 30
    steps = [("A", ["User logs in", "(JWT session)"], None), ("A", ["Upload PDF / image", "and choose output language"], None)]
    def link(y1, y2, lab=None):
        return arrow(cx, y1, cx, y2, u, label=lab, lx=cx + 14, ly=(y1 + y2) / 2 + 3) if lab else arrow(cx, y1, cx, y2, u)
    pos = {}
    items = [("proc", ["User logs in", "(JWT session)"]), ("proc", ["Upload PDF / image;", "choose English or Marathi"]),
             ("dec", "Valid type & size?"), ("proc", ["Store file safely, create job", "(status PROCESSING)"]),
             ("dec", "Digital text on page?"), ("proc", ["Clean & merge text", "(headers, wraps, language hint)"]),
             ("proc", ["Retrieve legal sources", "(vector + keyword → RRF → rerank)"]),
             ("proc", ["Build prompt and call LLM", "(primary → fallback models)"]),
             ("dec", "Valid JSON?"), ("proc", ["Ground citations; drop unknown sources"]),
             ("proc", ["Save result; capture deadlines", "(status COMPLETED)"]),
             ("proc", ["Show explanation, sources, deadlines;", "chat · reminders · drafts"])]
    ys = []
    for kind, content in items:
        gap = 22
        yy = y + gap
        if kind == "proc":
            o, h = proc(yy, content)
        else:
            o, h = dec(yy, content), 52
        b.append(link(y, yy))
        b.append(o)
        ys.append((kind, yy, h))
        y = yy + h
    b.append(link(y, y + 22)); b.append(term(y + 22, "End"))
    # side branches
    def side(idx, label_left, text_lines, right=True, yes_label="No"):
        kind, yy, h = ys[idx]
        mid = yy + h / 2
        x1 = cx + 105; x2 = cx + 160
        bx = x2
        o = arrow(x1, mid, bx, mid, u, label=yes_label, lx=(x1 + bx) / 2, ly=mid - 4)
        return o
    # invalid file -> error
    k, yy, h = ys[2]; mid = yy + h / 2
    b.append(arrow(cx + 105, mid, cx + 150, mid, u, label="No", lx=cx + 127, ly=mid - 4))
    b.append(box(cx + 150, mid - 20, 170, 40, ["Reject with a clear", "message → End"], "#fdeaea", "#c53030", 9.5, rx=6))
    b.append(text(cx + 12, ys[2][1] + 52 + 12, "Yes", 9, anchor="start"))
    # OCR branch
    k, yy, h = ys[4]; mid = yy + h / 2
    b.append(arrow(cx - 105, mid, cx - 150, mid, u, label="No", lx=cx - 127, ly=mid - 4))
    b.append(box(cx - 320, mid - 24, 170, 48, ["OCR the page", "(Tesseract mar+hin+eng)"], "#fdf0d8", "#c27a14", 9.5, rx=6))
    b.append(poly([(cx - 235, mid + 24), (cx - 235, ys[5][1] + 22), (cx - 125, ys[5][1] + 22)], u))
    b.append(text(cx + 12, ys[4][1] + 52 + 12, "Yes (good text)", 9, anchor="start"))
    # repair branch
    k, yy, h = ys[8]; mid = yy + h / 2
    b.append(arrow(cx + 105, mid, cx + 150, mid, u, label="No", lx=cx + 127, ly=mid - 4))
    b.append(box(cx + 150, mid - 24, 170, 48, ["Ask model to repair", "(once) → else error"], "#fdeaea", "#c53030", 9.5, rx=6))
    b.append(poly([(cx + 235, mid - 24), (cx + 235, ys[7][1] + 22), (cx + 125, ys[7][1] + 22)], u, True))
    b.append(text(cx + 12, ys[8][1] + 52 + 12, "Yes", 9, anchor="start"))
    return svg(W, int(y + 70), "".join(b), u, "System flowchart")


# ----------------------------------------------------------------------------- retrieval pipeline
def retrieval():
    u = "rt"
    W, H = 760, 250
    b = []
    b.append(box(6, 92, 104, 60, ["question or", "document slices"], "#fff", "#222", 10, title="Queries"))
    b.append(box(150, 22, 170, 70, ["embed (MiniLM, 384-d)", "pgvector HNSW cosine", "top 20"], "#e8f7ef", "#1f7a5a", 9.5, title="Dense search"))
    b.append(box(150, 152, 170, 70, ["Postgres full-text", "IDF-weighted OR query", "top 20"], "#e8f7ef", "#1f7a5a", 9.5, title="Keyword search"))
    b.append(box(362, 92, 140, 60, ["score = Σ 1/(60 + rank)", "keep best 16"], "#e8f1fb", "#2b6cb0", 9.5, title="RRF fusion"))
    b.append(box(540, 92, 124, 60, ["jina-reranker-v2", "(lexical fallback)"], "#fdf0d8", "#c27a14", 9.5, title="Cross-encoder"))
    b.append(box(694, 92, 60, 60, ["6 (chat 4)"], "#fff", "#222", 9.5, title="top-k"))
    b.append(arrow(110, 112, 148, 66, u)); b.append(arrow(110, 132, 148, 188, u))
    b.append(arrow(320, 60, 360, 108, u)); b.append(arrow(320, 188, 360, 136, u))
    b.append(arrow(502, 122, 538, 122, u)); b.append(arrow(664, 122, 692, 122, u))
    b.append(text(380, 242, "Only chunks with status = in_force are searched (superseded / repealed law is excluded in SQL).", 9.5, fill="#444"))
    return svg(W, H, "".join(b), u, "Retrieval pipeline")


# ----------------------------------------------------------------------------- evaluation charts
def eval_chart(data):
    o = data["overall"]
    names = list(o.keys())
    short = {"vector only": "Vector only", "keyword only (FTS)": "Keyword only (FTS)", "hybrid (RRF)": "Hybrid (RRF)", "hybrid + rerank (lexical)": "Hybrid + lexical rerank"}
    labels = [short.get(n, "Hybrid + cross-encoder") for n in names]
    W = 760; left = 170; right = 70; bw = W - left - right; H = 70 + 40 * len(names) + 30
    out = [text(380, 18, "Retrieval quality of the five methods (57 questions)", 12.5, True), text(left, 38, "MRR (bars, white whiskers = 95% bootstrap CI)  ·  Hit@3 at right", 9.5, anchor="start", fill="#444")]
    for i in range(0, 11, 2):
        x = left + bw * i / 10
        out.append(f'<line x1="{x:.1f}" y1="48" x2="{x:.1f}" y2="{H-28}" stroke="#ddd"/>' + text(x, H - 14, f"{i/10:.1f}", 9, fill="#555"))
    best = max(names, key=lambda n: o[n]["mrr"])
    for k, n in enumerate(names):
        v = o[n]; y = 56 + 40 * k; w = bw * v["mrr"]
        col = "#dd6b20" if n == best else ("#718096" if k == 0 else "#2c5282")
        out.append(text(left - 8, y + 18, labels[k], 10.5, anchor="end"))
        out.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="26" rx="2" fill="{col}"/>')
        lo, hi = v["mrr_ci"]; xl, xh = left + bw * lo, left + bw * hi
        out.append(f'<line x1="{xl:.1f}" y1="{y+13}" x2="{xh:.1f}" y2="{y+13}" stroke="#fff" stroke-width="2"/><line x1="{xl:.1f}" y1="{y+7}" x2="{xl:.1f}" y2="{y+19}" stroke="#fff" stroke-width="2"/><line x1="{xh:.1f}" y1="{y+7}" x2="{xh:.1f}" y2="{y+19}" stroke="#fff" stroke-width="2"/>')
        out.append(text(left + 8, y + 18, f"{v['mrr']:.3f}", 10.5, True, anchor="start", fill="#fff"))
        out.append(text(W - 6, y + 18, f"Hit@3 {v['hit@3']*100:.0f}%", 10.5, True, anchor="end"))
    return svg(W, H, "".join(out), "ec", "Retrieval quality chart")


def eval_groups(data):
    names = list(data["overall"].keys())
    short = ["Vector", "Keyword", "Hybrid", "+Lexical", "+X-enc"]
    W, H = 760, 300; left = 50; top = 40; ph = 190
    out = [text(380, 18, "MRR by language and by question style", 12.5, True)]
    panels = [("by_lang", ["en", "mr"], {"en": "English", "mr": "Marathi"}, "#2c5282", "#dd6b20", 8), ("by_difficulty", ["direct", "colloquial"], {"direct": "Direct questions", "colloquial": "Informal questions"}, "#2f855a", "#b7791f", 392)]
    for key, groups, lab, c1, c2, x0 in panels:
        pw = 350
        ox = x0 + 42
        out.append(f'<line x1="{ox}" y1="{top}" x2="{ox}" y2="{top+ph}" stroke="#555"/><line x1="{ox}" y1="{top+ph}" x2="{ox+pw-50}" y2="{top+ph}" stroke="#555"/>')
        for t in (0, 0.25, 0.5, 0.75, 1.0):
            yy = top + ph - ph * t
            out.append(f'<line x1="{ox}" y1="{yy:.1f}" x2="{ox+pw-50}" y2="{yy:.1f}" stroke="#e5e5e5"/>' + text(ox - 5, yy + 3, f"{t:.2f}", 9.5, anchor="end", fill="#555"))
        gw = (pw - 50) / len(names)
        for i, n in enumerate(names):
            for j, g in enumerate(groups):
                val = data[key][n][g]["mrr"]
                bw_ = gw * 0.32
                bx = ox + gw * i + gw * 0.18 + j * (bw_ + 2)
                out.append(f'<rect x="{bx:.1f}" y="{top+ph-ph*val:.1f}" width="{bw_:.1f}" height="{ph*val:.1f}" fill="{c1 if j == 0 else c2}"/>')
                out.append(text(bx + bw_ / 2, top + ph - ph * val - 3, f"{val:.2f}", 8.5))
            out.append(text(ox + gw * i + gw / 2, top + ph + 12, short[i], 9.5, fill="#222"))
        out.append(f'<rect x="{ox+8}" y="{top+ph+28}" width="10" height="10" fill="{c1}"/>' + text(ox + 22, top + ph + 37, lab[groups[0]], 10.5, anchor="start"))
        out.append(f'<rect x="{ox+130}" y="{top+ph+28}" width="10" height="10" fill="{c2}"/>' + text(ox + 144, top + ph + 37, lab[groups[1]], 10.5, anchor="start"))
    return svg(W, H, "".join(out), "eg", "MRR by language and style")


def er():
    s = open(os.path.join(HERE, "..", "report-src", "s05_backend.html"), encoding="utf-8").read()
    m = re.search(r'<svg viewBox="0 0 760 360".*?</svg>', s, re.S)
    return m.group(0).replace('role="img"', f'style="{FONT}" role="img"')
