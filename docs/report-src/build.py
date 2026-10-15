"""Assemble report.html from the section files, drawing the sequence diagrams and the evaluation chart from real data.

   python3 build.py [toc_pages.json]      -> report.html
Then render with:  node render.mjs        -> ../NyayaSetu-System-Architecture-Report.pdf
"""
import glob, json, os, re, sys
from html import escape
import seq

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "eval-results", "retrieval-2026-10-14.json")


def eval_chart(data):
    o = data["overall"]
    names = list(o.keys())
    short = {"vector only": "Vector only", "keyword only (FTS)": "Keyword only", "hybrid (RRF)": "Hybrid (RRF)",
             "hybrid + rerank (lexical)": "Hybrid + lexical rerank"}
    labels = [short.get(n, "Hybrid + cross-encoder rerank") for n in names]
    W, H = 760, 62 + 44 * len(names) + 36
    left, right = 190, 40
    bw = W - left - right
    out = [f'<svg viewBox="0 0 {W} {H}" width="{W}" role="img" aria-label="Retrieval quality by method">']
    out.append('<text x="190" y="20" class="t-s t-b">MRR (bar, whiskers = 95% CI)</text>')
    out.append('<text x="190" y="34" class="t-s t-g">Hit@3 shown as the figure on the right</text>')
    for i in range(0, 11, 2):
        x = left + bw * i / 10
        out.append(f'<line x1="{x:.1f}" y1="44" x2="{x:.1f}" y2="{H-34}" stroke="#e3e7f0"/><text x="{x:.1f}" y="{H-20}" class="t-s t-c t-g">{i/10:.1f}</text>')
    best = max(names, key=lambda n: o[n]["mrr"])
    for k, n in enumerate(names):
        v = o[n]; y = 52 + 44 * k
        w = bw * v["mrr"]
        col = "#e8890c" if n == best else "#1b2547" if k else "#7a859c"
        out.append(f'<text x="{left-10}" y="{y+17}" class="t-m t-c" style="text-anchor:end">{escape(labels[k])}</text>')
        out.append(f'<rect x="{left}" y="{y}" width="{w:.1f}" height="26" rx="3" fill="{col}"/>')
        lo, hi = v["mrr_ci"]
        xl, xh = left + bw * lo, left + bw * hi
        out.append(f'<line x1="{xl:.1f}" y1="{y+13}" x2="{xh:.1f}" y2="{y+13}" stroke="#fff" stroke-width="2"/><line x1="{xl:.1f}" y1="{y+6}" x2="{xl:.1f}" y2="{y+20}" stroke="#fff" stroke-width="2"/><line x1="{xh:.1f}" y1="{y+6}" x2="{xh:.1f}" y2="{y+20}" stroke="#fff" stroke-width="2"/>')
        out.append(f'<text x="{left + 10:.1f}" y="{y+18}" class="t-m t-b" style="fill:#fff">{v["mrr"]:.3f}</text>')
        out.append(f'<text x="{W-6}" y="{y+18}" class="t-m t-b" style="text-anchor:end">Hit@3 {v["hit@3"]*100:.0f}%</text>')
    out.append("</svg>")
    return f'<figure>{"".join(out)}<figcaption>Figure 13.1 — Retrieval quality of the five methods (57 questions, real models). Source: eval-results/retrieval-2026-10-14.json.</figcaption></figure>'


def eval_rows(data):
    rows = []
    for n, v in data["overall"].items():
        lo, hi = v["mrr_ci"]
        label = n.replace("jina-reranker-v2-base-multilingual", "jina-reranker-v2").replace("hybrid + rerank (lexical)", "hybrid + lexical rerank")
        label = "hybrid + cross-encoder rerank (jina)" if "jina" in n else label
        rows.append(f"<tr><td>{escape(label)}</td><td>{v['hit@1']*100:.0f}%</td><td>{v['hit@3']*100:.0f}%</td><td>{v['hit@5']*100:.0f}%</td>"
                    f"<td>{v['mrr']:.3f} ({lo:.2f}–{hi:.2f})</td><td>{v['stale_rate']*100:.0f}%</td></tr>")
    return "".join(rows)


def main():
    toc = {}
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        toc = json.load(open(sys.argv[1]))
    data = json.load(open(RESULTS))
    parts = sorted(glob.glob(os.path.join(HERE, "s[0-9]*.html")))
    body = "\n".join(open(p, encoding="utf-8").read() for p in parts)
    for name, (parts_, msgs) in seq.SEQS.items():
        body = body.replace(f"<!--SEQ:{name}-->", seq.seq(parts_, msgs, title=name))
    body = body.replace("<!--CHART:eval-->", eval_chart(data)).replace("<!--TABLE:eval-->", eval_rows(data))
    # table-of-contents page numbers (second pass)
    def fill(m):
        n = m.group(1)
        return f'<span class="n">{n}</span>{m.group(2)}<span class="d">{toc.get(n, "")}</span>'
    body = re.sub(r'<span class="n">([0-9A-Z]+)</span>([^<]+)<span class="d"></span>', fill, body)
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>NyayaSetu — System Architecture and Interview Guide</title><style>{css}</style></head><body>{body}</body></html>'
    open(os.path.join(HERE, "report.html"), "w", encoding="utf-8").write(html)
    print("report.html", len(html) // 1024, "KB")


main()
