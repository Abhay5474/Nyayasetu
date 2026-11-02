"""Text of the NyayaSetu project report. Each function returns an HTML string; build.py assembles them."""
import json, os
import figs, seq

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = json.load(open(os.path.join(HERE, "..", "..", "eval-results", "retrieval-2026-10-14.json"), encoding="utf-8"))

TITLE = "NyayaSetu: An LLM-Powered Regional-Language Legal and RTI Document Simplifier using Hybrid Retrieval-Augmented Generation"
# Student names / PRNs live in student_details.json (git-ignored; see student_details.example.json)
_d = json.load(open(os.path.join(HERE, "student_details.json" if os.path.exists(os.path.join(HERE, "student_details.json")) else "student_details.example.json"), encoding="utf-8"))
STUDENTS = [(s["prn"], s["name"]) for s in _d["students"]]
GUIDE = _d["guide"]
AY = _d["academic_year"]

# ------------------------------------------------------------------ figure / table registry (order = list order)
FIGS = []   # (id, title)
TABS = []


def fig(fid, title, inner, cls=""):
    FIGS.append((fid, title))
    return f'<figure class="{cls}">{inner}<div class="cap">Figure {fid}:&nbsp; {title}</div></figure>'


def img(name, kind="shot"):
    return f'<img class="{kind}" src="img/{name}.png">'


def tab(tid, title, inner):
    TABS.append((tid, title))
    return f'<div class="keep">{inner}<div class="cap">Table {tid} :&nbsp; {title}</div></div>'


def grid(head, rows, widths=None, numcols=()):
    cg = "".join(f'<col style="width:{w}">' for w in widths) if widths else ""
    h = "".join(f'<th class="{"n" if i in numcols else ""}">{c}</th>' for i, c in enumerate(head))
    r = "".join("<tr>" + "".join(f'<td class="{"n" if i in numcols else ""}">{c}</td>' for i, c in enumerate(row)) + "</tr>" for row in rows)
    return f'<table class="grid"><colgroup>{cg}</colgroup><tr>{h}</tr>{r}</table>'


def chapter(num, title, body):
    return f'<h1 class="ch" id="ch{num}">{num} | {title}</h1><div class="rule"></div>{body}'


# ------------------------------------------------------------------ front matter
def cover():
    rows = "".join(f"<tr><td>{p}</td><td>{n}</td></tr>" for p, n in STUDENTS)
    return f'''<div class="cover">
<p style="margin-top:8pt"><b>A Project Report</b></p><p>On</p>
<p class="t">{TITLE}</p>
<p>For the Degree of</p><p><b>Bachelor of Technology</b></p><p>In</p><p><b>Information Technology</b></p>
<p style="margin-top:16pt">Submitted by</p>
<table><tr><th>PRN</th><th>Name</th></tr>{rows}</table>
<p>Under the Guidance of</p><p><b>{GUIDE}</b></p>
<img src="img/logo.png">
<p><b>Department of Information Technology</b></p>
<p class="col">Walchand College of Engineering, Sangli</p>
<p class="sm">(Government Aided Autonomous Institute)</p>
<p style="margin-top:14pt"><b>{AY}</b></p></div>'''


def acknowledgement():
    return f'''<h1 class="plain" style="margin-top:6pt">Acknowledgement</h1>
<p>With a deep sense of gratitude, we would like to thank all the people who have lit our path with their kind guidance. We are very grateful to these intellectuals who did their best to help during our project work.</p>
<p>The special gratitude goes to our guide, {GUIDE}, for his valuable guidance, constant encouragement and suggestions to enhance the project implementation. We are grateful and remain in debt to him for his consistent instructions and guidance for the completion of the project.</p>
<p>We are thankful to the Head of the Department and to all the faculty members and technical staff of the Information Technology Department for their extensive, excellent and precious guidance in the completion of this work. We thank all our class colleagues for their appreciable help with our working project.</p>
<p>Finally, we thank our families for their patience and support, and the people who tested the system and gave us honest feedback on the explanations, the Marathi wording and the draft documents.</p>'''


def vision():
    pos = [("PO1: Engineering Knowledge", "Apply the knowledge of mathematics, engineering fundamentals and computational science to the solution of engineering problems."),
           ("PO2: Problem Analysis", "Identify, formulate, interpret and analyze complex engineering problems leading to substantiated conclusions."),
           ("PO3: Design/Development of Solutions", "Design systems, components or processes to meet desired needs within realistic constraints such as economic, environmental, societal and ethical considerations."),
           ("PO4: Conduct Investigations of Complex Problems", "Use research-based knowledge and methods including design of experiments, analysis, interpretation and synthesis of information to provide valid conclusions."),
           ("PO5: Modern Tool Usage", "Select and apply appropriate techniques, engineering skills and modern IT tools to prototype the model of complex engineering activities."),
           ("PO6: The Engineer and Society", "Apply contextual knowledge pertaining to social, secure, legal and cultural issues with consequent responsibilities relevant to Information Technology."),
           ("PO7: Environment And Sustainability", "Understand the impact of professional engineering solutions in social, environmental and the global contexts, demonstrating the knowledge of, and the need for sustainable development."),
           ("PO8: Ethics", "Apply ethical principles and commit to professional ethics with responsibilities and norms of the engineering practices."),
           ("PO9: Individual and Teamwork", "Work effectively as an individual as well as a member or a leader in diverse teams for multidisciplinary settings."),
           ("PO10: Communication", "Communicate effectively with the engineering community and with society at large, such as, being able to comprehend and write reports and design documentation to make effective presentations."),
           ("PO11: Project Management and Finance", "Demonstrate knowledge and understanding of the engineering and management principles and apply those to original work or contemporary issues, as a member or/and a leader in a team or an entrepreneur, to manage projects in multidisciplinary environments")]
    li = "".join(f"<li><b>{a}:</b> {b}</li>" for a, b in pos)
    return f'''<div style="font-size:11pt;line-height:1.38">
<h2 style="font-size:13pt;margin-top:0">Vision, Mission &amp; Course Outcomes</h2>
<p><b>VISION:</b><br>To be an Information Technology programme as the first choice by the aspiring students and prospective employers by implementing world class education practices</p>
<p><b>MISSION:</b><br>To meet above Vision, all stakeholders of this programme are committed towards Outcome Based Education Philosophy.</p>
<p><b>Under-Graduate POs</b></p><ul style="padding-left:22pt">{li}</ul></div>'''


def declaration():
    ss = "".join(f"<tr><td>{p}</td><td>{n}</td></tr>" for p, n in STUDENTS)
    return f'''<h1 class="plain" style="margin-top:6pt">Declaration</h1>
<p style="margin-top:24pt">We hereby declare that the work presented in this project report titled &ldquo;{TITLE.upper()}&rdquo; submitted by us in the partial fulfilment of the requirement of the award of the degree of Bachelor of Technology (B.Tech) submitted in the Department of Information Technology, Walchand College of Engineering, Sangli, is an authentic record of our project work carried out under the guidance of {GUIDE}.</p>
<div style="height:230pt"></div>
<p>Place: Sangli.<br>Date: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;/05/2027</p>
<table class="plain" style="width:60%;margin-top:12pt"><tr><th>PRN</th><th>Name</th></tr>{ss}</table>'''


def toc(pages):
    g = lambda k: pages.get(k, "")
    rows = [("i", "Abbreviations", "i"), ("ii", "List of Figures", "ii"), ("iii", "List of Tables", "iii"), ("iv", "Abstract", "iv"),
            ("1", "Introduction", g("ch1")), ("2", "Literature Survey", g("ch2")), ("3", "Methodology", g("ch3")),
            ("4", "Result and Discussion", g("ch4")), ("5", "Conclusion", g("ch5")), ("6", "References", g("refs"))]
    r = "".join(f'<tr><td style="width:46pt">{a}</td><td>{b}</td><td class="r" style="width:70pt">{c}</td></tr>' for a, b, c in rows)
    return f'<h1 class="plain" style="margin-top:6pt">Table of Contents</h1><table class="plain toc" style="margin-top:26pt"><tr><th style="width:46pt">Sr. no.</th><th>Name of the Content</th><th class="r" style="white-space:nowrap">Page No.</th></tr>{r}</table>'


def abbreviations():
    ab = [("RTI", "Right to Information"), ("PIO", "Public Information Officer"), ("FAA", "First Appellate Authority"), ("LLM", "Large Language Model"),
          ("RAG", "Retrieval-Augmented Generation"), ("OCR", "Optical Character Recognition"), ("RRF", "Reciprocal Rank Fusion"), ("MRR", "Mean Reciprocal Rank"),
          ("FTS", "Full-Text Search"), ("HNSW", "Hierarchical Navigable Small World (index)"), ("API", "Application Programming Interface"),
          ("REST", "Representational State Transfer"), ("JWT", "JSON Web Token"), ("UI", "User Interface"), ("SPA", "Single Page Application"),
          ("JSON", "JavaScript Object Notation"), ("SQL", "Structured Query Language"), ("ER", "Entity Relationship"), ("PDF", "Portable Document Format"),
          ("SMTP", "Simple Mail Transfer Protocol"), ("SMS", "Short Message Service"), ("CI", "Confidence Interval"), ("PRN", "Permanent Registration Number")]
    rows = "".join(f"<tr><td style='width:120pt'>{a}</td><td>{b}</td></tr>" for a, b in ab)
    return f'<h1 class="plain" style="margin-top:4pt;margin-bottom:12pt">Abbreviations</h1><table class="plain" style="margin-top:2pt;line-height:1.15"><tr><th>Abbreviation</th><th>Full Form</th></tr>{rows}</table>'


def lof(pages):
    rows = "".join(f'<tr><td style="width:78pt">Fig. {i}</td><td>{t}</td><td class="r" style="width:50pt">{pages.get("fig" + i, "")}</td></tr>' for i, t in FIGS)
    return f'<h1 class="plain" style="margin-top:4pt;margin-bottom:10pt">List of Figures</h1><table class="plain" style="line-height:1.12;font-size:11.5pt"><tr><th>Sr No.</th><th>Content</th><th class="r" style="white-space:nowrap">Page No.</th></tr>{rows}</table>'


def lot(pages):
    rows = "".join(f'<tr><td style="width:84pt">Table {i}</td><td>{t}</td><td class="r" style="width:50pt">{pages.get("tab" + i, "")}</td></tr>' for i, t in TABS)
    return f'<h1 class="plain" style="margin-top:4pt;margin-bottom:10pt">List of Tables</h1><table class="plain"><tr><th>Table No.</th><th>Title</th><th class="r" style="white-space:nowrap">Page No.</th></tr>{rows}</table>'


def abstract():
    return '''<h1 class="plain" style="margin-top:4pt;margin-bottom:14pt">Abstract</h1>
<p>Legal and government documents such as RTI replies, notices, orders and fee demands carry deadlines and rights that ordinary citizens often cannot read, because the language is formal, the legal references are unfamiliar and most of the material is in English even when the reader is more comfortable in Marathi. A missed 30-day appeal window can cost a citizen the right to challenge a decision. This project presents <b>NyayaSetu</b>, a web platform that reads such a document, explains it in plain English or Marathi, and points to the exact legal source it relied on.</p>
<p>The system is built as four cooperating services: a React web interface, a Spring Boot gateway that handles authentication, file storage and job orchestration, a FastAPI AI service that performs text extraction (PyMuPDF with Tesseract OCR for scans), retrieval and language-model calls, and a PostgreSQL database with the pgvector extension that stores users, documents, results and a knowledge base of 318 legal entries (467 searchable chunks) built from official sources, mainly the RTI Act, 2005 and the Maharashtra RTI Rules. Retrieval is hybrid: vector search and full-text search are fused with Reciprocal Rank Fusion and re-ordered by a multilingual cross-encoder, so the language model only sees verified passages and its citations are checked against them.</p>
<p>Beyond the explanation, the platform extracts deadlines and sends e-mail or SMS reminders, lets the user ask follow-up questions about the document, and generates ready-to-file drafts (RTI application, first appeal and fee-payment reply) in English or Marathi as PDF or Word files. On an evaluation set of 57 questions, the full retrieval pipeline reached a Mean Reciprocal Rank of 0.702 and a Hit@3 of 82%, against 0.559 and 67% for vector search alone. The project shows that a grounded, bilingual, deadline-aware assistant can be built from open components and be run by a student team with a single <code>docker compose up</code>.</p>'''


# ------------------------------------------------------------------ chapter 1
def ch1():
    b = '''<h2>1.1&nbsp; Introduction</h2>
<p class="ind">Every year millions of citizens in India receive documents they must act on: a reply to a Right to Information (RTI) application, a notice from a municipal office, a consumer-court order, a fee demand. These documents are usually written in formal English, they refer to sections of Acts by number, and they hide the one sentence that matters, for example that the applicant has thirty days to file a first appeal. A person who cannot read the document correctly either pays for a lawyer or clerk to read it, or does nothing and loses the right to respond.</p>
<p class="ind">This project proposes <b>NyayaSetu</b> (Marathi: <i>nyayasetu</i>, &ldquo;bridge to justice&rdquo;), a web application that bridges that gap. The user uploads a PDF or a photograph of a document; the system extracts the text, finds the relevant provisions in a legal knowledge base, and asks a large language model to produce a structured explanation: a short summary, the key points, what the user needs to do, the deadlines, and the legal references with their sources. The explanation can be shown in English or in Marathi, and the user can ask follow-up questions that are answered only from the document and the knowledge base.</p>
<p class="ind">NyayaSetu does not give legal advice and says so on every page. Its aim is narrower and more achievable: to make sure that a citizen understands what a document says, what the next step is and by when, and to take away the effort of writing the first reply.</p>
<h2>1.2&nbsp; Problem Statement</h2>
<p class="ind">The main purpose of this project was to design and develop a platform that simplifies legal and RTI documents for citizens in their own language, grounded in verifiable legal sources, and that turns the understanding into action by tracking deadlines and preparing the next document to be filed. Instead of leaving the reader alone with a page of legal English, the platform brings explanation, source checking, reminders and drafting into one place.</p>
<p class="ind">A plain chatbot is not enough for this task. A general language model can produce a confident but wrong statement of the law, it does not know the Maharashtra RTI Rules, and it has no way to show where a claim comes from. The platform therefore has to retrieve the actual text of the law first and constrain the model to it.</p>
<h2>1.3&nbsp; Motivation</h2>
<p class="ind">The motivation came from how ordinary the problem is. An RTI reply that refuses information under Section 8(1)(j), or that demands a copying fee for 74 pages, is routine for an officer but bewildering for the applicant. The remedy (a first appeal within 30 days, or paying the fee within a set period) exists in the Act, yet it is rarely visible to the person who needs it. Language is a second barrier: most state-level users are more at ease in Marathi than in English, but most tools and most legal text are in English.</p>
<p class="ind">Recent progress in retrieval-augmented generation and in multilingual embedding models makes it practical to build an assistant that answers from a curated corpus rather than from memory. This project applies those techniques to a concrete, socially useful domain and measures them honestly, including where they fail.</p>
<h2>1.4&nbsp; Contributions of work</h2>
<p class="ind">The most important contribution of this work is NyayaSetu, an end-to-end system that handles reading, explaining, grounding, reminding and drafting under one roof. The platform is meant to assist the citizen, not to replace a lawyer.</p>
<h3 class="ind">1.4.1 Bilingual document explanation</h3>
<p class="ind">Uploaded PDFs and photographs are converted to text (using OCR where the page is a scan) and explained in English or Marathi in a fixed structure: summary, key points, required actions, deadlines and legal references.</p>
<h3 class="ind">1.4.2 Grounded legal knowledge base</h3>
<p class="ind">A knowledge base of 318 entries (467 chunks) is built from official texts. Every entry records its provenance (official text, government reprint or unverified summary) and its legal status, and superseded provisions are excluded from search so that the system never cites repealed law.</p>
<h3 class="ind">1.4.3 Hybrid retrieval with re-ranking</h3>
<p class="ind">Dense vector search and keyword search are combined with Reciprocal Rank Fusion and re-ordered by a cross-encoder. The pipeline is evaluated on 57 questions and each stage is shown to add measurable value.</p>
<h3 class="ind">1.4.4 Citation checking</h3>
<p class="ind">Every source cited by the model must be one of the passages it was given. Unknown citations are dropped, and a quotation in a chat answer is shown only if it can be found verbatim in the document.</p>
<h3 class="ind">1.4.5 Deadlines and reminders</h3>
<p class="ind">Dates and periods found in the document become deadline cards. A scheduler sends e-mail or SMS reminders 7, 3 and 1 days before and on the day itself.</p>
<h3 class="ind">1.4.6 Draft generator</h3>
<p class="ind">The user answers a few questions and receives a ready-to-file RTI application, first appeal or fee-payment reply in English or Marathi, laid out on the official forms (Annexures A and B of the Maharashtra RTI Rules) and downloadable as PDF or Word.</p>
<h2>1.5&nbsp; Objectives</h2>
<p><b>1.5.1 Plain-language explanation:</b> To explain a legal or RTI document in simple English or Marathi so that a citizen can understand what it says, what to do next and by when.</p>
<p><b>1.5.2 Source-grounded answers:</b> To retrieve the relevant provisions from a curated knowledge base and make the language model answer only from them, with every citation traceable to a source.</p>
<p><b>1.5.3 Hybrid retrieval and evaluation:</b> To build a hybrid retrieval pipeline (vector, keyword, rank fusion, cross-encoder) and to measure its quality with a reproducible evaluation harness.</p>
<p><b>1.5.4 Secure and modular architecture:</b> To design four loosely coupled services with authenticated access, validated uploads and a database schema managed by migrations, so that each part can be tested and replaced independently.</p>
<p><b>1.5.5 Deadline tracking:</b> To extract deadlines automatically and remind the user through e-mail or SMS before they expire.</p>
<p><b>1.5.6 Draft generation:</b> To prepare the next document the citizen has to file (RTI application, first appeal, fee-payment reply) in English or Marathi as PDF or Word.</p>
<p><b>1.5.7 Reliability with free or low-cost models:</b> To keep the system usable when one language-model provider is slow, rate-limited or unavailable, by using an ordered fallback chain across providers.</p>'''
    return chapter(1, "Introduction", b)


# ------------------------------------------------------------------ chapter 2
REFS = [
    'P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal et al., &ldquo;Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,&rdquo; <i>Advances in Neural Information Processing Systems (NeurIPS)</i>, vol. 33, 2020, arXiv: 2005.11401.',
    'N. Reimers and I. Gurevych, &ldquo;Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,&rdquo; <i>Proc. EMNLP-IJCNLP</i>, 2019, arXiv: 1908.10084.',
    'N. Reimers and I. Gurevych, &ldquo;Making Monolingual Sentence Embeddings Multilingual using Knowledge Distillation,&rdquo; <i>Proc. EMNLP</i>, 2020, arXiv: 2004.09813.',
    'Y. A. Malkov and D. A. Yashunin, &ldquo;Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs,&rdquo; <i>IEEE Transactions on Pattern Analysis and Machine Intelligence</i>, vol. 42, no. 4, pp. 824&ndash;836, 2020.',
    'G. V. Cormack, C. L. A. Clarke and S. Buettcher, &ldquo;Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods,&rdquo; <i>Proc. ACM SIGIR</i>, pp. 758&ndash;759, 2009.',
    'R. Nogueira and K. Cho, &ldquo;Passage Re-ranking with BERT,&rdquo; arXiv preprint, arXiv: 1901.04085, 2019.',
    'I. Chalkidis, M. Fergadiotis, P. Malakasiotis, N. Aletras and I. Androutsopoulos, &ldquo;LEGAL-BERT: The Muppets Straight Out of Law School,&rdquo; <i>Findings of EMNLP</i>, 2020.',
    'Z. Ji, N. Lee, R. Frieske, T. Yu, D. Su, Y. Xu et al., &ldquo;Survey of Hallucination in Natural Language Generation,&rdquo; <i>ACM Computing Surveys</i>, vol. 55, no. 12, 2023.',
    'K. Sp&auml;rck Jones, &ldquo;A Statistical Interpretation of Term Specificity and its Application in Retrieval,&rdquo; <i>Journal of Documentation</i>, vol. 28, no. 1, pp. 11&ndash;21, 1972.',
    'Government of India, &ldquo;The Right to Information Act, 2005 (Act No. 22 of 2005),&rdquo; Ministry of Law and Justice. [Online]. Available: https://rti.gov.in/',
    'Government of Maharashtra, General Administration Department, &ldquo;Maharashtra Right to Information Rules,&rdquo; and the notification of 7 July 2026 prescribing the application and appeal annexures. [Online]. Available: https://rti.maharashtra.gov.in/',
    'pgvector contributors, &ldquo;pgvector: Open-source vector similarity search for Postgres.&rdquo; [Online]. Available: https://github.com/pgvector/pgvector',
    'Spring Boot Reference Documentation, VMware / Broadcom. [Online]. Available: https://spring.io/projects/spring-boot',
    'S. Ram&iacute;rez, &ldquo;FastAPI Documentation.&rdquo; [Online]. Available: https://fastapi.tiangolo.com/',
    'R. Smith, &ldquo;An Overview of the Tesseract OCR Engine,&rdquo; <i>Proc. International Conference on Document Analysis and Recognition (ICDAR)</i>, 2007.',
    'Artifex Software, &ldquo;PyMuPDF Documentation.&rdquo; [Online]. Available: https://pymupdf.readthedocs.io/',
    'Meta Open Source, &ldquo;React Documentation.&rdquo; [Online]. Available: https://react.dev/',
    'Docker Inc., &ldquo;Docker and Docker Compose Documentation.&rdquo; [Online]. Available: https://docs.docker.com/',
]


def ch2():
    b = '''<p class="ind">Earlier work that this project builds on falls into four groups: retrieval-augmented generation for grounded answers, dense and sparse retrieval with rank fusion and re-ranking, language models and embeddings for legal and multilingual text, and the practical tools used to read documents and to build the service.</p>
<p class="ind">Lewis et al. introduced retrieval-augmented generation, in which a generator is conditioned on passages fetched from an external corpus, and showed that this improves factual accuracy in knowledge-intensive tasks while keeping the source of an answer inspectable [1]. The same line of work responds to the well-documented tendency of language models to hallucinate fluent but unsupported statements [8]. In a legal setting the cost of such an error is high, which is why NyayaSetu places a verified corpus between the document and the model and checks every citation afterwards.</p>
<p class="ind">Retrieval quality decides how useful the generator can be. Dense retrieval with sentence embeddings [2] finds passages by meaning, and multilingual distillation extends this to languages other than English [3], which is what allows a Marathi question to match an English statute. Approximate nearest-neighbour search is made fast by HNSW graphs [4] and is available inside PostgreSQL through pgvector [12]. Keyword search with inverse-document-frequency weighting [9] remains stronger for exact terms such as section numbers. Reciprocal Rank Fusion combines the two ranked lists without needing comparable scores [5], and a cross-encoder re-ranker reads the question and each candidate together to produce a sharper final order [6]. Our evaluation chapter reproduces this ordering on a legal corpus.</p>
<p class="ind">Domain-specific language models such as LEGAL-BERT show that legal text has its own vocabulary and benefits from specialised treatment [7]. Because few resources of this kind exist for Marathi or for Indian state rules, this project relies on a multilingual general embedding model and compensates with a carefully curated knowledge base drawn from the primary texts of the RTI Act [10] and the Maharashtra Rules [11].</p>
<p class="ind">On the engineering side, the system uses Tesseract for OCR [15] and PyMuPDF for text and PDF handling [16], FastAPI for the AI service [14], Spring Boot for the gateway [13], React for the interface [17] and Docker for packaging [18].</p>
<p class="ind">Nevertheless, available tools remain fragmented. General chatbots do not cite the Maharashtra Rules and do not track deadlines, government portals publish the law but do not explain a specific document, and neither prepares the reply that the citizen must file. Combining explanation, grounding, reminders and drafting in a bilingual tool for ordinary users is the gap this project addresses.</p>'''
    return chapter(2, "Literature Survey", b)


# ------------------------------------------------------------------ chapter 3
def sw():
    return '''<table class="grid" style="font-size:11.5pt"><tr><th>Strengths</th><th>Weaknesses</th><th>Opportunities</th><th>Threats</th></tr>
<tr><td>Answers grounded in a curated legal knowledge base with checked citations.</td><td>Depends on an external language-model provider for generation.</td><td>More Indian languages and more Acts (consumer, tenancy, labour) can be added to the knowledge base.</td><td>Laws, rules and fee schedules change; stale entries would mislead.</td></tr>
<tr><td>Bilingual output (English and Marathi) and Marathi interface.</td><td>OCR quality on poor photographs limits what can be read.</td><td>Integration with court and RTI portals for status tracking.</td><td>Users may treat the explanation as legal advice.</td></tr>
<tr><td>Deadline extraction with e-mail and SMS reminders.</td><td>Marathi retrieval is weaker than English (MRR 0.605 against 0.744).</td><td>Voice input and read-aloud for users who cannot read well.</td><td>Provider rate limits, price changes or outages.</td></tr>
<tr><td>Ready-to-file drafts as PDF and Word on the official forms.</td><td>The knowledge base is small (318 entries) and mainly covers RTI.</td><td>Lawyer and legal-aid review workflow.</td><td>Privacy risk if uploaded documents are mishandled.</td></tr></table>'''


def reqs_table():
    return tab("3.2.1", "System Requirements", grid(["Category", "Requirement"], [
        ["Hardware (recommended)", "Dual-core or better CPU (4 cores preferred), 8 GB RAM, 15 GB free disk for images and model files"],
        ["Operating system", "Windows 10/11, Linux or macOS with Docker Engine / Docker Desktop and Docker Compose v2"],
        ["Languages and runtimes", "Java 21 (backend), Python 3.12 (AI service), Node.js 20 (frontend build)"],
        ["Frameworks", "Spring Boot 3.3, Spring Security (JWT), FastAPI, LangChain, React 18, Vite, Tailwind CSS"],
        ["Database", "PostgreSQL 16 with the pgvector extension; Flyway migrations"],
        ["Document tools", "PyMuPDF, Tesseract OCR (Marathi, Hindi, English language packs), python-docx"],
        ["AI models", "Multilingual MiniLM embedding (384-d), multilingual cross-encoder re-ranker, one or more hosted LLMs through an OpenAI-compatible API"],
        ["Network", "Internet access for the LLM provider; optional SMTP server and Twilio account for reminders"],
        ["Client", "Any modern web browser"]], ["30%", "70%"]))


def algorithm():
    steps = [
        ("Receive the document", "The user signs in, uploads a PDF or an image (up to 25 MB) and chooses the output language, English or Marathi."),
        ("Validate and store", "The gateway checks the token, the size and the file signature (magic bytes), stores the file under a random name, records a SHA-256 hash and creates a job in the PROCESSING state."),
        ("Extract the text", "The AI service reads the text layer with PyMuPDF. If a page has little or no text it is rendered and passed to Tesseract (Marathi, Hindi and English)."),
        ("Clean and prepare", "Headers, footers and broken line wraps are removed, pages are merged and the document language is detected."),
        ("Retrieve legal sources", "The document is split into slices. Each slice is searched by dense vector search (top 20) and keyword search (top 20); the lists are fused with Reciprocal Rank Fusion (k = 60), the best 16 are re-ordered by the cross-encoder and the top 6 are kept."),
        ("Build the prompt and call the model", "The document text and the retrieved passages are placed in a prompt that asks for a fixed JSON structure. The call goes to the primary model and, on a timeout, rate-limit or server error, to the next model in the fallback chain."),
        ("Validate the output", "The reply must be valid JSON that matches the schema. If it is not, the model is asked once to repair it; a second failure ends the job with a clear error."),
        ("Ground the citations", "Every source cited is checked against the passages that were supplied; unknown ones are dropped. Dates and periods are turned into deadlines."),
        ("Save and notify", "The result, sources and deadlines are saved and the job becomes COMPLETED. The scheduler later sends reminders 7, 3 and 1 days before each deadline and on the day."),
        ("Interact and draft", "The user reads the explanation, asks follow-up questions answered from the same document and sources, or opens the draft generator to prepare an RTI application, first appeal or fee reply as PDF or Word.")]
    h = '<div class="algo"><div class="st">Start</div>'
    for i, (t, d) in enumerate(steps, 1):
        k = ' class="keep"' if i == len(steps) else ''
        h += f'<div{k}><div class="st">{i}.&nbsp; {t}:</div><div class="bd">{d}</div>' + ('<div class="st">End</div>' if i == len(steps) else '') + '</div>'
    return h + '</div>'


def ch3():
    b = '''<h2>3.1&nbsp; Steps for Implementation</h2>
<h3 class="ind">3.1.1 Document Input &amp; Validation:</h3>
<p class="ind">The system begins with a document intake component. It accepts PDFs and images, checks their type by file signature and size, and stores them safely before any processing starts.</p>
<h3 class="ind">3.1.2 Text Extraction:</h3>
<p class="ind">Digital PDFs are read directly. Scanned pages and photographs are passed to Tesseract OCR with Marathi, Hindi and English language data, so that the same pipeline can handle a typed reply and a photographed notice.</p>
<h3 class="ind">3.1.3 Knowledge Base Preparation:</h3>
<p class="ind">Official texts are cleaned, split into chunks of about 1,200 characters with a 150-character overlap, tagged with their act, section, provenance and legal status, embedded into 384-dimensional vectors and loaded into PostgreSQL together with a full-text index.</p>
<h3 class="ind">3.1.4 Hybrid Retrieval and Re-ranking:</h3>
<p class="ind">For every document the engine retrieves candidate passages by meaning and by keywords, fuses the two rankings and re-orders the best candidates with a cross-encoder.</p>
<h3 class="ind">3.1.5 Explanation, Chat and Drafts:</h3>
<p class="ind">A language model produces the structured explanation from the document and the retrieved passages. Follow-up questions use the same retrieval, and the draft engine fills official templates with the answers given by the user.</p>
<h3 class="ind">3.1.6 Presentation and Reminders:</h3>
<p class="ind">The results are shown in a responsive interface in English and Marathi, while a scheduler sends deadline reminders by e-mail or SMS.</p>

<h2>3.2&nbsp; Methodology</h2>
<h3 class="ind">3.2.1 Define Core Functionalities and Requirements:</h3>
<p class="ind">The key functions are user registration and login, document upload, text extraction, retrieval of legal sources, explanation in two languages, follow-up questions, deadline tracking with reminders, draft generation, and an evaluation harness to measure retrieval quality.</p>
<h3 class="ind">3.2.2 Select Backend and Frontend Technologies:</h3>
<p class="ind"><b>Frontend:</b> React 18 with Vite, Tailwind CSS and Axios; served by nginx, which also proxies the API.<br>
<b>Gateway:</b> Java 21 with Spring Boot 3.3, Spring Security (JWT), JPA and Flyway.<br>
<b>AI service:</b> Python 3.12 with FastAPI, PyMuPDF, Tesseract, LangChain, fastembed and python-docx.<br>
<b>Database:</b> PostgreSQL 16 with pgvector (HNSW index) and full-text search.<br>
<b>Deployment:</b> Docker and Docker Compose; optional frontend hosting on Vercel.</p>
<h3 class="ind">3.2.3 Development of APIs and Engines:</h3>
<p class="ind">The gateway exposes REST endpoints for authentication, documents, results, chat, deadlines, drafts and profile. It calls the AI service, which is not reachable from outside, through a shared internal token. The AI service exposes endpoints for extraction, explanation, chat and drafts.</p>
<h3 class="ind">3.2.4 Knowledge Base and Retrieval Engine:</h3>
<p class="ind">The knowledge base is built from official PDFs and handbook text. Each entry stores its provenance (official text, government reprint or unverified summary) and status (in force or superseded); only in-force entries are searched.</p>
<h3 class="ind">3.2.5 User Interface and Visualization:</h3>
<p class="ind">A responsive interface with a dashboard, an explanation page with tabs for the explanation and for questions, a deadlines page, a draft generator and a settings page, all available in English and Marathi.</p>
<h3 class="ind">3.2.6 Testing and Performance Evaluation:</h3>
<p class="ind">Unit and integration tests cover each service (101 tests in the AI service, 27 in the gateway and 11 in the frontend), and a separate harness measures retrieval quality with Hit@k and Mean Reciprocal Rank on 57 questions.</p>
<h3 class="ind">3.2.7 System Deployment:</h3>
<p class="ind">The whole platform is packaged as four containers and started with <code>docker compose up</code>. Secrets are supplied through an environment file that is never committed.</p>
''' + reqs_table() + '''

<h2>3.3&nbsp; System Analysis and Design</h2>
<h3 class="ind">3.3.1 Requirement Specification:</h3>
<p class="ind"><b>Functional:</b> register and log in; upload a document; view an explanation in English or Marathi; ask follow-up questions; see deadlines and mark them done; receive reminders; generate and download drafts. <b>Non-functional:</b> answers must be traceable to sources; uploads must be validated; a failed language-model call must not lose the user&rsquo;s work; the interface must be usable on a phone; the system must run from a single command.</p>
<h3 class="ind">3.3.2 Feasibility Study:</h3>
<p class="ind">The project is technically feasible because every component is open source and well supported: Spring Boot, FastAPI, PostgreSQL with pgvector, Tesseract, PyMuPDF and React. The language model is the only external dependency and several providers with free tiers exist; the fallback chain lets the system continue when one of them is unavailable. The cost of running the platform is therefore limited to a small server and optional SMS charges.</p>
<h3 class="ind">3.3.3 Data Collection Methods:</h3>
<p class="ind">The knowledge base is collected from official sources only: the English text of the RTI Act, 2005, the Maharashtra RTI Rules with their annexures, and the central fee rules, taken from government PDFs and handbook text. Entries are classified as official text, government reprint or unverified summary so that users can see how reliable a citation is. Evaluation questions were written separately from the knowledge base, in English and Marathi, in direct and in informal styles.</p>
<h3 class="ind">3.3.4 Use Case Diagram:</h3>
<p class="ind">The citizen is the only human actor. The system uses an external language-model provider, the knowledge base and notification services (SMTP and Twilio).</p>
''' + fig("3.3.4", "Use Case Diagram", figs.usecase()) + '''
<h3 class="ind">3.3.5 SWOT Analysis:</h3>
<p class="ind">NyayaSetu combines explanation, source-grounding, reminders and drafting in one interface. It is strong where the knowledge base is strong, and weaker where it is thin, which is why the knowledge base and the evaluation harness are treated as first-class parts of the project.</p>
''' + tab("3.3.5", "SWOT Analysis", sw()) + '''
<h3 class="ind">3.3.6 Database Design:</h3>
<p class="ind">The relational schema stores users, documents, results, deadlines, chat messages and a notification log in the <code>public</code> schema, and the knowledge base in a separate <code>kb</code> schema. Flyway migrations V1 and V2 create and evolve the tables, so the schema is reproducible on any machine.</p>
''' + fig("3.3.6", "Entity-Relationship Diagram", figs.er()) + '''

<h2>3.4&nbsp; Architecture Diagram</h2>
''' + fig("3.4.1", "Proposed System Architecture", figs.architecture()) + '''
<p class="ind">The architecture follows the flow of a request. The browser loads the React application from nginx, and every <code>/api</code> call is proxied to the Spring Boot gateway, which authenticates the user with a JWT. For explanation, chat and drafts the gateway calls the FastAPI service over the internal network with a shared token. The AI service performs extraction, retrieval, model calls and document generation, and reads the knowledge base from PostgreSQL. The gateway stores users, documents, results and deadlines in the same database, keeps the original files in a volume and sends reminders through SMTP or Twilio. The AI service is never exposed to the internet.</p>
<p class="ind">Figure 3.4.2 shows the retrieval stage in detail, and Figure 3.4.3 shows how one upload travels through the services.</p>
''' + fig("3.4.2", "Hybrid Retrieval Pipeline", figs.retrieval()) + fig("3.4.3", "Sequence Diagram: Document Upload and Explanation", seq.seq(*seq.SEQS["upload"], title="upload")) + '''

<h2>3.5&nbsp; Flowchart</h2>
''' + fig("3.5.1", "Proposed System Flowchart", figs.flowchart()) + '''

<h2>3.6&nbsp; Algorithm</h2>
''' + algorithm() + '''

<h2>3.7&nbsp; Performance Study</h2>
<h3 class="ind">3.7.1 Registration and Login:</h3>
''' + fig("3.7.1", "Registration Interface", img("reg"), "md") + '''
<p class="ind">The registration page creates an account with a name, e-mail address and password. Passwords are stored as BCrypt hashes, login returns a 12-hour JWT, and repeated failed logins are throttled (5 attempts per 15 minutes). The language of the interface can be switched between English and Marathi from the header.</p>
<h3 class="ind">3.7.2 Document Upload:</h3>
''' + fig("3.7.2", "Document Upload Dashboard", img("upload"), "md") + '''
<p class="ind">The dashboard is the starting point after login. The user drags in a PDF or photograph, chooses whether the explanation should be in English or Marathi, and the system starts a background job. Files up to 25 MB are accepted after a signature check.</p>
<h3 class="ind">3.7.3 Document History:</h3>
''' + fig("3.7.3", "Document History and Status", img("history"), "md") + '''
<p class="ind">The history lists earlier documents with their type, date and status (Processing, Ready or Failed). The status is refreshed automatically while a job is running, and a failed job shows the reason in plain words.</p>
<h3 class="ind">3.7.4 Marathi Interface:</h3>
''' + fig("3.7.4", "Dashboard in Marathi", img("dash_mr"), "md") + '''
<p class="ind">The whole interface, not only the explanation, can be shown in Marathi, so that a user who does not read English can use the application from the first screen.</p>
<h3 class="ind">3.7.5 Explanation Page:</h3>
''' + fig("3.7.5", "Explanation of an Uploaded Document", img("expl_top"), "md") + '''
<p class="ind">The explanation page opens with a short plain-language summary, followed by the key points, the actions the user needs to take, the deadlines, the legal references and the sources. A side panel shows the document type, pages, how the text was read (digital text or OCR) and the model that generated the answer.</p>
<h3 class="ind">3.7.6 Follow-up Questions:</h3>
''' + fig("3.7.6", "Ask Questions About the Document", img("chat"), "md") + '''
<p class="ind">The second tab lets the user ask questions about the document in English or Marathi. Answers come only from the document and the knowledge base, carry the legal sources they relied on, and may show a verbatim quotation from the document. Suggested follow-up questions are offered after each answer.</p>
<h3 class="ind">3.7.7 Deadlines:</h3>
''' + fig("3.7.7", "Deadlines Page", img("deadlines"), "md") + '''
<p class="ind">All deadlines extracted from all documents are collected on one page, ordered by date, with the document they came from and the original sentence. A deadline can be marked as done, and reminders can be switched on in the settings.</p>
<h3 class="ind">3.7.8 Draft Generator:</h3>
''' + fig("3.7.8", "Choosing the Document to Draft", img("drafts_choose"), "md") + '''
<p class="ind">The draft generator offers three documents: an RTI application, a first appeal and a reply to a fee demand. The user selects one, answers a short form and receives a draft in English or Marathi.</p>
<h3 class="ind">3.7.9 Draft Form with Live Preview:</h3>
''' + fig("3.7.9", "Draft Form and Preview", img("draft_form"), "tall") + '''
<p class="ind">The form asks only for what the document needs, with hints below each field. The preview is laid out on the official annexure and updates after the user presses Preview, and the draft can then be downloaded as PDF or Word. Dates are checked (for example, a draft cannot be dated in the future) and a short &ldquo;how to file it&rdquo; note is shown below the preview.</p>'''
    return chapter(3, "Methodology", b)


# ------------------------------------------------------------------ chapter 4
def ch4():
    o = DATA["overall"]
    keys = list(o.keys())
    nm = ["Vector search only", "Keyword search only (FTS)", "Hybrid (RRF)", "Hybrid + lexical re-rank", "Hybrid + cross-encoder re-rank"]
    rows = [[nm[i], f'{o[k]["hit@1"]*100:.0f}%', f'{o[k]["hit@3"]*100:.0f}%', f'{o[k]["hit@5"]*100:.0f}%', f'{o[k]["mrr"]:.3f}', f'{o[k]["mrr_ci"][0]:.2f}&ndash;{o[k]["mrr_ci"][1]:.2f}'] for i, k in enumerate(keys)]
    t1 = tab("4.2.1", "Retrieval Quality of the Five Methods (57 questions)", grid(["Method", "Hit@1", "Hit@3", "Hit@5", "MRR", "MRR 95% CI"], rows, ["34%", "11%", "11%", "11%", "11%", "22%"], numcols=(1, 2, 3, 4, 5)))
    t2 = tab("4.3.1", "Automated Test Suites", grid(["Component", "Framework", "Tests", "What is covered"], [
        ["AI service", "pytest", "101", "Extraction, chunking, retrieval, JSON validation and repair, citation grounding, fallback chain, drafts"],
        ["Gateway", "JUnit 5, Mockito", "27", "Authentication, throttling, upload validation, job orchestration, deadlines, reminders"],
        ["Frontend", "Vitest, Testing Library", "11", "Rendering, language switching, forms and API client"]], ["16%", "22%", "10%", "52%"], numcols=(2,)))
    b = '''<h2>4.1&nbsp; Results</h2>
<p class="ind">The final solution is a working, modular platform that explains legal and RTI documents for citizens in English and Marathi. Through a clean web interface the user uploads a document and within a short time sees what it means, what to do, by when, and which provisions the answer rests on. The backend extracts the text, retrieves the relevant passages from the knowledge base, validates the model&rsquo;s output and stores the result, the sources and the deadlines. Figures 4.1.1 to 4.1.3 show the output for a sample RTI reply from a municipal corporation, which refused part of the information under Section 8(1)(j) and asked for a copying fee of Rs. 148.</p>
<p class="ind">In the sample, the system identified the document as an RTI reply, summarised that part of the information was refused as personal information and that a fee must be paid within 10 days, and listed two actions with deadlines of 10 and 30 days. It also pointed out that a first appeal is available within 30 days of receiving the reply.</p>
<p class="ind">Each legal reference is tied to a numbered source below it. A badge shows how reliable the source is (official text or government reprint) and whether it was cited in the answer or only retrieved as related. This lets the user and any reviewer check the claim against the text of the Act.</p>
''' + fig("4.1.1", "Final Output: Summary, Key Points and Actions", img("expl_a"), "tall") + fig("4.1.2", "Deadlines and Legal References", img("expl_b"), "sm") + fig("4.1.3", "Sources and Citations with Provenance Badges", img("expl_c"), "sm") + '''
<p class="ind">The draft generator then turns the next step into a document. Figure 4.1.4 shows an RTI application generated in English on the prescribed annexure, and Figure 4.1.5 shows a first appeal generated in Marathi with the grounds the user selected.</p>
''' + fig("4.1.4", "Generated RTI Application (English, PDF)", img("pdf_rti_en", "pdfpage"), "md") + fig("4.1.5", "Generated First Appeal (Marathi, PDF)", img("pdf_appeal", "pdfpage"), "md") + '''

<h2>4.2&nbsp; Retrieval Evaluation</h2>
<p class="ind">To measure retrieval honestly we wrote 57 questions (English and Marathi; direct and informal; mostly on the RTI Act, some on consumer law) and recorded the knowledge-base entry that should be found for each. Five configurations were compared using Hit@k (the right entry is in the top k) and Mean Reciprocal Rank (MRR), with 95% bootstrap confidence intervals. Real embedding and re-ranking models were used.</p>
''' + fig("4.2.1", "Retrieval Quality of the Five Methods", figs.eval_chart(DATA)) + t1 + '''
<p class="ind">Vector search alone reached an MRR of 0.559 and keyword search alone only 0.373, because a literal match fails when a question is phrased informally. Fusing the two (0.589) helped modestly, a lexical re-ranker raised it to 0.648, and the multilingual cross-encoder gave the best result: an MRR of 0.702 and a Hit@3 of 82%, an absolute gain of 14 percentage points in MRR over vector search. The confidence intervals overlap, so we report the ordering as consistent rather than as a proven separation.</p>
''' + fig("4.2.2", "MRR by Language and by Question Style", figs.eval_groups(DATA)) + '''
<p class="ind">The breakdown shows where the system is weaker. With the full pipeline, English questions scored 0.744 and Marathi questions 0.605. Direct questions scored 0.766, while informal questions that avoid the legal vocabulary scored only 0.465. The evaluation also found a real defect: the keyword search originally treated every word as equally important and was dominated by common words. Weighting words by inverse document frequency fixed this, and the effect is included in the numbers above.</p>

<h2>4.3&nbsp; Testing</h2>
<p class="ind">Each service has its own automated tests, which were run repeatedly during development. The tests also protect behaviour that was found to be fragile, such as the validation of draft requests and the handling of a model that returns malformed JSON.</p>
''' + t2 + '''
<h2>4.4&nbsp; Discussion</h2>
<p class="ind">The results show three things. First, grounding works: because the model is shown retrieved passages and its citations are verified, the explanation of the sample reply names the correct Section 19 remedy and does not invent sources. Second, each stage of the retrieval pipeline earns its place, and the evaluation harness makes it possible to say so with numbers. Third, the weak spots are known: Marathi and informal questions retrieve less well, the knowledge base mainly covers RTI, and the text of a Marathi draft needs review by a Marathi speaker before it is filed.</p>
<p class="ind">The architecture leaves room to grow. New Acts can be added to the knowledge base without changing the code, other languages can be added through the prompt and templates, and a different model provider can be placed in the fallback chain by configuration. The platform explains and prepares documents; it does not replace a lawyer, and the interface says so.</p>'''
    return chapter(4, "Result and Discussion", b)


def ch5():
    b = '''<p class="ind">NyayaSetu is a bilingual, source-grounded assistant that helps citizens understand legal and RTI documents and act on them. It combines text extraction with OCR, a knowledge base of official legal texts, hybrid retrieval with re-ranking, a language model with a validated output format, deadline tracking with reminders, and a generator for the documents a citizen has to file next. The system is delivered as four services that run together with one command.</p>
<p class="ind">The evaluation shows that the retrieval design is sound: a full pipeline of vector search, keyword search, rank fusion and cross-encoder re-ranking reached an MRR of 0.702 and a Hit@3 of 82% on 57 questions, against 0.559 and 67% for vector search alone. It also shows the limits honestly: Marathi and informal questions are retrieved less well than English and direct ones, and the knowledge base is still small.</p>
<p class="ind"><b>Future scope.</b> The most valuable next steps are to widen the knowledge base to other Acts and to more state rules; to improve Marathi and informal-question retrieval, for example with a larger evaluation set and a fine-tuned embedding model; to add voice input and read-aloud for users who cannot read well; to add Hindi and other regional languages; to let users share a draft with a legal-aid volunteer for review; and to integrate with RTI portals so that the status of an application and its appeals can be tracked automatically.</p>
<p class="ind">Nevertheless, no automated tool can remove the uncertainty of the law or replace a qualified lawyer for an important decision. NyayaSetu is meant to give the citizen the first and most important step: to know what the document says and what to do before the deadline passes.</p>'''
    return chapter(5, "Conclusion", b)


def refs():
    items = "".join(f'<p style="margin-bottom:3.5pt;text-align:left;padding-left:26pt;text-indent:-26pt;font-size:11pt;line-height:1.3">[{i}]&nbsp; {r}</p>' for i, r in enumerate(REFS, 1))
    return f'<h1 class="ch" id="refs">References</h1><div class="rule"></div>{items}'
