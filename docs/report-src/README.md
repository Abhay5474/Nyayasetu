# Report sources

`NyayaSetu-System-Architecture-Report.pdf` (one level up) is built from the `s*.html` section files, `style.css`, `seq.py`
(sequence diagrams) and the real evaluation results in `../../eval-results/`.

    python3 build.py toc.json     # assemble report.html (diagrams and chart are generated)
    node render.mjs               # print to PDF with Chromium (needs playwright-core; set CHROME=/path/to/chrome)

`toc.json` holds the page numbers of the chapters (re-compute after large edits: render once, read the heading pages, render again).
