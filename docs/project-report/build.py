"""Build NyayaSetu-Project-Report.pdf in the format of the WCE project report.
   python3 build.py   (needs: node + playwright-core for render.mjs, PyMuPDF)
Pass 1 renders without page numbers, finds the pages of every heading / figure / table, pass 2 re-renders with them,
then footers and page numbers are stamped with PyMuPDF."""
import json, os, re, subprocess, sys
import pymupdf as fitz
import content as C

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "NyayaSetu-Project-Report.pdf")
RAW = os.path.join(HERE, "_raw.pdf")
FRONT_PLAIN = 5          # cover, acknowledgement, vision, declaration, table of contents
ROMAN = ["i", "ii", "iii", "iv"]


def assemble(pages):
    C.FIGS.clear(); C.TABS.clear()
    body = C.ch1() + C.ch2() + C.ch3() + C.ch4() + C.ch5() + C.refs()
    front = ("".join(f'<section class="{"" if i == 0 else "pb"}">{h}</section>' for i, h in enumerate([
        C.cover(), C.acknowledgement(), C.vision(), C.declaration(), C.toc(pages), C.abbreviations(), C.lof(pages), C.lot(pages), C.abstract()])))
    css = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()
    html = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{C.TITLE}</title><style>{css}</style></head><body>{front}{body}</body></html>'
    open(os.path.join(HERE, "report.html"), "w", encoding="utf-8").write(html)


def render():
    env = dict(os.environ, NODE_PATH=os.environ.get("NODE_PATH", ""))
    subprocess.run(["node", os.path.join(HERE, "render.mjs"), RAW], check=True, env=env)


def find_pages(doc):
    # body starts at the page whose text begins with "1 | Introduction"
    start = next(i for i in range(len(doc)) if doc[i].get_text().strip().startswith("1 | Introduction"))
    pages = {}
    def look(key, label):
        for i in range(start, len(doc)):
            if key in doc[i].get_text():
                pages[label] = i - start + 1; return
    for n, t in [(1, "Introduction"), (2, "Literature Survey"), (3, "Methodology"), (4, "Result and Discussion"), (5, "Conclusion")]:
        look(f"{n} | {t}", f"ch{n}")
    for i in range(start + pages["ch5"], len(doc)):
        if doc[i].get_text().strip().startswith("References"):
            pages["refs"] = i - start + 1; break
    for fid, _ in C.FIGS: look(f"Figure {fid}:", "fig" + fid)
    for tid, _ in C.TABS: look(f"Table {tid} :", "tab" + tid)
    return start, pages


def stamp(start):
    doc = fitz.open(RAW)
    roman_start = FRONT_PLAIN
    font = fitz.Font("tiro")
    for i, page in enumerate(doc):
        if i < roman_start: continue
        if i < start: label = ROMAN[i - roman_start]; txt = label
        else:
            n = i - start + 1
            txt = (f"Walchand College of Engineering, Sangli | {n}" if n % 2 else f"Department of Information Technology, WCE Sangli | {n}")
        w = fitz.get_text_length(txt, fontname="tiro", fontsize=10)
        page.insert_text((page.rect.width / 2 - w / 2, page.rect.height - 40), txt, fontname="tiro", fontsize=10, color=(0, 0, 0))
    doc.set_metadata({"title": C.TITLE, "author": "Haripriya Yele, Pranav Kulkarni", "subject": "B.Tech Project Report, Information Technology, WCE Sangli, AY 2026-27"})
    doc.save(OUT, garbage=3, deflate=True)
    return len(doc)


if __name__ == "__main__":
    pages = {}
    assemble(pages); render()
    start, pages = find_pages(fitz.open(RAW))
    assemble(pages); render()
    start2, pages2 = find_pages(fitz.open(RAW))
    assert pages == pages2 and start == start2, "page numbers moved between passes"
    n = stamp(start2)
    json.dump(pages2, open(os.path.join(HERE, "_pages.json"), "w"), indent=1)
    print("pages:", n, "body starts at physical page", start2 + 1)
