"""Tiny sequence-diagram SVG generator for the report."""
from html import escape

COLORS = {"Browser": "#fdf1dd", "nginx": "#fdf1dd", "Backend": "#eef3fb", "AI service": "#eaf6f0", "Postgres": "#ffffff",
          "LLM": "#f3eefb", "Scheduler": "#eef3fb", "Email/SMS": "#f3eefb", "Embedder": "#eaf6f0", "Files": "#ffffff"}
STROKES = {"Browser": "#e8890c", "nginx": "#e8890c", "Backend": "#2c5fa8", "AI service": "#1f7a5a", "Postgres": "#17203a",
           "LLM": "#7b52b8", "Scheduler": "#2c5fa8", "Email/SMS": "#7b52b8", "Embedder": "#1f7a5a", "Files": "#17203a"}


def seq(parts, msgs, width=760, step=33, title=None, num_start=1):
    n = len(parts)
    margin = 62
    xs = [margin + i * (width - 2 * margin) / (n - 1) for i in range(n)]
    X = dict(zip(parts, xs))
    top = 44
    height = top + step * (len(msgs) + 1) + 16
    o = [f'<svg viewBox="0 0 {width} {height}" width="{width}" role="img" aria-label="{escape(title or "sequence")}">',
         '<defs><marker id="sa" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#44506b"/></marker>'
         '<marker id="sr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8a94ab"/></marker></defs>']
    for p in parts:
        x = X[p]
        o.append(f'<line x1="{x:.1f}" y1="{top-4}" x2="{x:.1f}" y2="{height-8}" stroke="#c2c9d8" stroke-dasharray="3 4"/>')
        o.append(f'<rect x="{x-48:.1f}" y="6" width="96" height="30" rx="6" fill="{COLORS.get(p, "#fff")}" stroke="{STROKES.get(p, "#17203a")}" stroke-width="1.4"/>')
        o.append(f'<text x="{x:.1f}" y="25" class="t-m t-b t-c">{escape(p)}</text>')
    y = top + step * 0.6
    k = num_start
    for m in msgs:
        kind = m[3] if len(m) > 3 else "call"
        a, b, label = m[0], m[1], m[2]
        lines = label.split("\n")
        if kind == "note":
            xa, xb = X[a], X[b]
            x0, x1 = min(xa, xb) - 40, max(xa, xb) + 40
            h = 12 * len(lines) + 8
            o.append(f'<rect x="{x0:.1f}" y="{y-12:.1f}" width="{x1-x0:.1f}" height="{h}" rx="4" fill="#fffbea" stroke="#e8c76b"/>')
            for i, ln in enumerate(lines):
                o.append(f'<text x="{(x0+x1)/2:.1f}" y="{y-1+12*i:.1f}" class="t-s t-c">{escape(ln)}</text>')
            y += step + (len(lines) - 1) * 12
            continue
        xa, xb = X[a], X[b]
        ret = kind == "ret"
        col = "#8a94ab" if ret else "#44506b"
        dash = ' stroke-dasharray="5 3"' if ret else ""
        mk = "sr" if ret else "sa"
        badge = "" if ret else f'<circle cx="{min(xa, xb) + 0 if False else xa + (-9 if xb < xa else 9):.1f}" cy="{y:.1f}" r="0"/>'
        if a == b:
            right_side = xa > width * 0.55  # near the right edge the label goes to the left of the lifeline so it is never clipped
            if right_side:
                o.append(f'<path d="M{xa:.1f} {y-9:.1f} h-26 v14 h24" fill="none" stroke="{col}" stroke-width="1.4"{dash} marker-end="url(#{mk})"/>')
                for i, ln in enumerate(lines):
                    o.append(f'<text x="{xa-32:.1f}" y="{y-3+11*i:.1f}" class="t-s" style="text-anchor:end">{escape(ln)}</text>')
                if not ret:
                    o.append(f'<text x="{xa+6:.1f}" y="{y-1:.1f}" class="t-s t-b" style="fill:#e8890c">{k}</text>')
            else:
                o.append(f'<path d="M{xa:.1f} {y-9:.1f} h26 v14 h-24" fill="none" stroke="{col}" stroke-width="1.4"{dash} marker-end="url(#{mk})"/>')
                for i, ln in enumerate(lines):
                    o.append(f'<text x="{xa+32:.1f}" y="{y-3+11*i:.1f}" class="t-s">{escape(ln)}</text>')
                if not ret:
                    o.append(f'<text x="{xa-11:.1f}" y="{y-1:.1f}" class="t-s t-b" style="fill:#e8890c">{k}</text>')
        else:
            o.append(f'<line x1="{xa:.1f}" y1="{y:.1f}" x2="{xb:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="1.5"{dash} marker-end="url(#{mk})"/>')
            mid = (xa + xb) / 2
            for i, ln in enumerate(lines):
                o.append(f'<text x="{mid:.1f}" y="{y-5-11*(len(lines)-1-i):.1f}" class="t-s t-c">{escape(ln)}</text>')
            if not ret:
                o.append(f'<text x="{xa+(8 if xb>xa else -8):.1f}" y="{y+12:.1f}" class="t-s t-b" style="fill:#e8890c;text-anchor:{"start" if xb>xa else "end"}">{k}</text>')
        if not ret:
            k += 1
        y += step + (len(lines) - 1) * 6
    o.append("</svg>")
    return "".join(o)


SEQS = {
 "upload": (["Browser", "nginx", "Backend", "Postgres", "AI service", "LLM"], [
   ("Browser", "nginx", "POST /api/documents (file, language) + JWT"),
   ("nginx", "Backend", "proxy /api/*  (Host header preserved)"),
   ("Backend", "Backend", "verify JWT · size · magic bytes · store · SHA-256"),
   ("Backend", "Postgres", "INSERT document (UPLOADED) + result row PROCESSING"),
   ("Backend", "Browser", "201 + document (status PROCESSING)", "ret"),
   ("Backend", "Backend", "@Async job starts on documentExecutor", "note"),
   ("Backend", "AI service", "POST /v1/extract (file) + X-Internal-Token"),
   ("AI service", "AI service", "sniff type · PDF text or OCR per page · clean"),
   ("AI service", "Backend", "text · pages · method · language hint", "ret"),
   ("Backend", "Postgres", "save extracted_text, page_count, method"),
   ("Backend", "AI service", "POST /v1/simplify (text, language)"),
   ("AI service", "Postgres", "hybrid retrieval on kb.kb_chunks (status = in_force)"),
   ("AI service", "LLM", "prompt: rules + sources + document"),
   ("LLM", "AI service", "JSON explanation", "ret"),
   ("AI service", "AI service", "validate · repair once · ground citations"),
   ("AI service", "Backend", "document + sources + model + map-reduce flag", "ret"),
   ("Backend", "Postgres", "save result JSONB · capture deadlines · COMPLETED"),
   ("Browser", "Backend", "GET /api/documents/{id} every 2.5–3 s  →  COMPLETED", "ret"),
   ("Browser", "Backend", "GET /api/documents/{id}/results/{lang}"),
 ]),
 "chat": (["Browser", "Backend", "Postgres", "AI service", "LLM"], [
   ("Browser", "Backend", "POST /api/documents/{id}/chat {question, language}"),
   ("Backend", "Postgres", "owned(user, doc) · extracted_text · last 10 messages"),
   ("Backend", "AI service", "POST /v1/chat (text, question, history)"),
   ("AI service", "AI service", "query = previous question + this one\nlong doc → in-memory excerpt index"),
   ("AI service", "Postgres", "hybrid retrieval of legal sources (top 4)"),
   ("AI service", "LLM", "system rules + history + excerpts + sources + question"),
   ("LLM", "AI service", "{answer, answerable, quotes, source_ids, follow_ups}", "ret"),
   ("AI service", "AI service", "keep only quotes found in the document\ndrop unknown source ids"),
   ("AI service", "Backend", "answer · quotes · cited sources · follow-ups · model", "ret"),
   ("Backend", "Postgres", "INSERT user message + assistant message (details JSONB)"),
   ("Backend", "Browser", "exchange (both messages)", "ret"),
 ]),
 "draft": (["Browser", "Backend", "AI service"], [
   ("Browser", "Backend", "POST /api/drafts/preview  (form as JSON)"),
   ("Backend", "Backend", "JWT · kind whitelisted · size ≤ 30 000 chars"),
   ("Backend", "AI service", "POST /v1/drafts/preview"),
   ("AI service", "AI service", "pick model by kind → validate → build blocks (en | mr)\ncompute dates and warnings"),
   ("AI service", "Backend", "blocks · warnings · notes · last_date   (422 = field problems)", "ret"),
   ("Backend", "Browser", "preview JSON (or a readable 422 message)", "ret"),
   ("Browser", "Backend", "POST /api/drafts/file?format=pdf|docx"),
   ("Backend", "AI service", "POST /v1/drafts/file?format=…"),
   ("AI service", "AI service", "render PDF (PyMuPDF) or Word (python-docx)"),
   ("AI service", "Browser", "file bytes + Content-Disposition (via Backend)", "ret"),
   ("Browser", "Browser", "blob → download (nothing stored on the server)", "note"),
 ]),
 "kb": (["AI service", "Files", "Embedder", "Postgres"], [
   ("AI service", "AI service", "start: build container (store, embedder, LLM chain)\nserve /health at once; ingest in a background thread"),
   ("AI service", "Files", "read manifest.json + extracted/*.txt + seed JSON"),
   ("AI service", "AI service", "split into provisions · check expected counts · attach provenance"),
   ("AI service", "Postgres", "SELECT id, content_hash FROM kb.kb_chunks"),
   ("AI service", "Embedder", "embed only chunks that are new or changed"),
   ("Embedder", "AI service", "384-dimension vectors", "ret"),
   ("AI service", "Postgres", "UPSERT chunks (text, tsvector, vector, status, meta)"),
   ("AI service", "Postgres", "PRUNE file-origin chunks that no longer exist"),
   ("AI service", "AI service", "/health → knowledge_base.state = ready (467 chunks)", "note"),
 ]),
 "alert": (["Scheduler", "Postgres", "Email/SMS"], [
   ("Scheduler", "Scheduler", "cron 0 0 8 * * * (Asia/Kolkata), only if ALERTS_ENABLED"),
   ("Scheduler", "Postgres", "PENDING deadlines due within today … today + 7"),
   ("Scheduler", "Scheduler", "stage = smallest offset ≥ days left (7, 3, 1, 0)\nskip if last_reminder_stage ≤ stage"),
   ("Scheduler", "Postgres", "load user (language, channels) + document name"),
   ("Scheduler", "Email/SMS", "send bilingual reminder (e-mail and/or SMS)"),
   ("Scheduler", "Postgres", "INSERT notification_log (success/failure) · save stage"),
 ]),
 "auth": (["Browser", "Backend", "Postgres"], [
   ("Browser", "Backend", "POST /api/auth/login {email, password}"),
   ("Backend", "Backend", "LoginThrottle: ≤ 5 failures / 15 min per (email + IP)"),
   ("Backend", "Postgres", "find user by lower(email)"),
   ("Backend", "Backend", "BCrypt verify · sign JWT (sub = user id, 12 h)"),
   ("Backend", "Browser", "{token, expiresAt, user}", "ret"),
   ("Browser", "Browser", "store session; Axios adds  Authorization: Bearer …", "note"),
   ("Browser", "Backend", "any /api/* call → JwtAuthenticationFilter → AuthUser"),
 ]),
}
