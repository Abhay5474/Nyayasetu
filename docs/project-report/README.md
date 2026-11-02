# Project report generator

Builds `NyayaSetu-Project-Report.pdf` (WCE project-report format).

One-time setup (Windows / Linux / macOS):
```
pip install pymupdf
npm install                      # installs playwright-core only; uses your installed Chrome or Edge
copy student_details.example.json student_details.json   # (cp on Linux/macOS) then edit names, PRNs, guide, year
```
Build:
```
python build.py
```
`student_details.json`, the PDF and `report.html` are git-ignored. Edit the text in `content.py`, the look in `style.css`.
