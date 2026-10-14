# NyayaSetu — न्यायसेतू
**LLM-powered regional-language Legal / RTI document simplifier.** Upload a PDF or photo of a notice, court order or
RTI reply and get a plain-language explanation in **English or Marathi** — summary, key points, deadlines, required
actions, legal references and source citations — grounded in a legal knowledge base via RAG.

```
 Browser ──► nginx + React (3000)
                │  /api
                ▼
        Spring Boot gateway (8080)  ── JWT auth, file storage, orchestration, deadline alerts
           │              │
           │              └──► PostgreSQL 16 + pgvector   (users, documents, results, deadlines | kb.kb_chunks)
           ▼
   FastAPI AI service (8000, internal)
     PyMuPDF / Tesseract OCR → clean + chunk → hybrid RAG (pgvector + FTS → RRF → rerank) → LangChain → LLM
```

| Folder | What it is |
|---|---|
| `frontend/` | React 18, Vite, Tailwind CSS, Axios. Landing page, auth, upload dashboard, results dashboard, deadlines, settings. UI in English & Marathi. |
| `backend/` | Java 21, Spring Boot 3.3, Spring Security (JWT), JPA + Flyway. REST API, local file storage, async orchestration of the AI service, optional e-mail/SMS deadline alerts. |
| `ai-service/` | Python 3.12, FastAPI, PyMuPDF, Tesseract (PaddleOCR optional), LangChain, pgvector, fastembed. |
| `db/init.sql` | Enables the `vector` extension on first DB start. |

## Quick start (Docker)
```bash
cp .env.example .env
# edit .env: set POSTGRES_PASSWORD, JWT_SECRET (openssl rand -base64 48), INTERNAL_TOKEN (openssl rand -hex 32)
# and an LLM key, e.g. ANTHROPIC_API_KEY  (or LLM_PROVIDER=openai|ollama)
docker compose up --build
```
Open http://localhost:3000. The first image build downloads the multilingual embedding model and reranker
(~1.2 GB, baked into the image). To skip the heavy reranker use `RERANKER=lexical`; for a fully offline smoke test use
`LLM_PROVIDER=mock EMBEDDING_PROVIDER=hash RERANKER=lexical` (the `mock` LLM only *extracts* sentences — it does not
translate or truly simplify, and the UI says so).

## How it works
1. **Upload** (`POST /api/documents`): the backend validates the file by magic bytes (PDF/PNG/JPEG/TIFF/BMP/WEBP, ≤ 25 MB),
   stores it under `uploads/{userId}/{uuid}.ext`, records it, and returns `202`. Processing runs on a bounded async pool.
2. **Extract** (`/v1/extract`): PyMuPDF reads digital PDFs; pages with no text layer (and image uploads) go through
   Tesseract (`mar+hin+eng`). Text is cleaned (headers/footers, hyphenation, Devanagari-safe normalisation); script is detected.
3. **Retrieve**: queries built from the document (opening text, cited sections/Acts, closing paragraph) run dense search
   (multilingual embeddings, pgvector HNSW) and keyword search (Postgres FTS); results are fused with Reciprocal Rank Fusion and
   reranked by a multilingual cross-encoder.
4. **Generate** (`/v1/simplify`): a LangChain prompt gives the LLM the document plus numbered sources `[S1]…`; it must answer as
   JSON in the chosen language. Long documents are condensed map-reduce style first. Output is schema-validated (one automatic repair
   retry) and citations to sources that were never retrieved are dropped.
5. **Ask questions** (`/api/documents/{id}/chat`): a continuous, persisted Q&A conversation per document. Each turn replays recent
   history to `/v1/chat`; long documents are narrowed to the most relevant excerpts (hybrid search over the document's own chunks),
   the knowledge base adds legal sources, and quotes the model returns are kept only if they appear verbatim in the document. Questions
   the document cannot answer are flagged "Not found in the document". Up to 100 questions per document; conversations can be cleared.
6. **Results**: stored per `(document, language)`; switching language reuses the extracted text. Deadlines are captured for tracking.
7. **Alerts** (`ALERTS_ENABLED=true`): a daily job (08:00 IST) e-mails / SMSes users at 7, 3, 1 days and on the day of each dated
   deadline. Catches up after downtime; every attempt is logged in `notification_log`. SMTP via `MAIL_*`, SMS via Twilio.

## API (selected)
`POST /api/auth/register|login` · `GET|PATCH|DELETE /api/users/me` · `POST /api/documents` (multipart `file`, `language=en|mr`) ·
`GET /api/documents[/{id}]` · `POST /api/documents/{id}/process?language=mr` · `GET /api/documents/{id}/results/{lang}` ·
`GET /api/documents/{id}/file` · `GET|POST|DELETE /api/documents/{id}/chat` · `GET /api/deadlines` · `PATCH /api/deadlines/{id}`. Health: `/actuator/health`.
AI service (internal, `X-Internal-Token`): `/v1/extract`, `/v1/simplify`, `/v1/chat`, `/v1/kb/search`, `/v1/kb/ingest`, `/health`.

## Knowledge base
Two kinds of content, clearly separated and labelled in the UI on every citation:

* **Official texts** (`ai-service/knowledge_base/sources/*.pdf` + `manifest.json`): Acts, Rules and gazette notifications. Currently loaded:
  * **Maharashtra RTI Rules, 2026 - notification of 7 July 2026** (English + Marathi; *in force*): ₹10 application fee, ₹2 per page,
    ₹20 appeal fee, first appeal in 30 days, second appeal in 90 days. It supersedes
  * the Maharashtra RTI Rules, 2026 notified on 12 June 2026 (₹30 / ₹5 / ₹100 - *superseded*), which had in turn replaced
  * the Maharashtra RTI Rules, 2005 (*superseded*). Superseded texts are kept for history but never retrieved.
  * The authorised **Marathi text of the RTI Act 2005** as in force on 1 Dec 2014 (OCR excerpts).
  * The **Consumer Protection Act, 2019** as enacted (107 sections; its *notes* flag that later Rules changed the pecuniary limits).
  * **Government reprints** (shown as "Government reprint"): the **English RTI Act 2005** (sections 1-31 + Second Schedule) and the
    **Central RTI (Regulation of Fee and Cost) Rules 2005** with the 2005/2006 amendments, taken from Annexures XIII-XIV of the National
    Archives of India *RTI Handbook* (2008). These are text-only sources (`extracted/*_handbook.txt`, no PDF): the handbook text was
    column-scrambled, so sections were put back in order by hand. Staleness is flagged in `notes` (no post-2008 amendments, e.g. the 2019
    Amendment Act; Central rules only - Maharashtra authorities follow the Maharashtra Rules). Replace with the gazette / India Code text.
* **Seed summaries** (`knowledge_base/*.json`): short paraphrases written for this project (a few judgments,
  Consumer Protection, NI Act, BNSS/BNS ...). They are shown as **"Unverified summary"** and are replaced as official PDFs are added.

**Adding an official PDF**
1. Copy the PDF to `knowledge_base/sources/` and add an entry to `sources/manifest.json` (`title`, `kind`, `language`, `jurisdiction`,
   `version_date`, `status` = `in_force`/`superseded`, `gazette_ref`, `source_url`, `parser` = `numbered` (one entry per section/rule,
   optional `expected_provisions` check), `numbered_margin` (gazette Acts with marginal notes), `single` (keep a short instrument whole) or
   `paragraphs` (noisy scans); `source_type` defaults to `official_pdf`, use `official_reprint` for non-gazette reprints; `text_file` points
   at an `extracted/` file when there is no PDF).
2. `python -m app.rag.ingest` - text is extracted (PyMuPDF; Tesseract OCR for scans; a corrupted Devanagari text layer is detected and
   OCR'd instead) and saved to `knowledge_base/extracted/<id>.txt`. **Proofread that file** (OCR can misread digits) - it is what gets
   ingested. Re-running only re-embeds changed text and removes entries that no longer exist.
3. After a person has checked the text against the official source, set `verified_at` and `verified_by` in the manifest; the UI then shows
   "Verified <date> · <name>" instead of "Not yet verified".

Superseded/repealed entries are excluded from retrieval. The prompts tell the model to prefer official text over unverified summaries and
to flag when it relies on a summary. Known gaps: the English RTI Act PDF supplied was corrupted, so the English Act comes from the
2008 handbook reprint above (pre-2019 text); the Central RTI Rules 2012 are still an unverified seed summary.

```bash
python -m app.rag.ingest                     # whole knowledge_base/ (official + seed)
curl -H "X-Internal-Token: …" -X POST :8000/v1/kb/ingest -d '{"entries":[…]}'   # ad-hoc additive entries
```

## Troubleshooting the LLM connection
If a document ends in "We couldn't finish this document", run a one-call check of the provider, key, base URL and model:
```bash
docker compose exec ai-service sh -c 'curl -s -H "X-Internal-Token: $INTERNAL_TOKEN" localhost:8000/v1/llm/check'
```
`{"ok": true ...}` means the model answers. Otherwise `detail` says why (rejected key, unknown model, rate limit, unreachable endpoint).
After editing `.env`, apply it with `docker compose up -d` (a plain `restart` keeps the old values). Keys are trimmed of quotes,
spaces and a `Bearer ` prefix automatically. For Gemini: `LLM_PROVIDER=openai`, `OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`,
`OPENAI_API_KEY=<key from aistudio.google.com/apikey>`, `LLM_MODEL=<a current Gemini model>`.

### Fallback models
Hosted models sometimes answer "503 high demand" or hit a quota. Set a fallback in `.env` and the service switches automatically
(the failure and the model that finally answered are logged; the result records the model that really answered):
```
LLM_FALLBACK_MODELS=gemini-3.1-flash-lite     # same provider and key, tried first
FALLBACK_LLM_PROVIDER=openai                  # then a different service (Groq/OpenRouter/another Gemini key, or ollama/anthropic)
FALLBACK_LLM_MODEL=<model name at that service>
FALLBACK_API_KEY=<its key>
FALLBACK_BASE_URL=<its OpenAI-compatible URL>
```
`/v1/llm/check` tests every model in the chain separately and reports which ones work.

## Evaluation (answer quality)
`ai-service/eval/questions.jsonl` holds 60 labelled questions (40 English, 17 Marathi, 3 out-of-scope). Each lists the knowledge-base
provisions that contain the answer (chosen by reading the source text), and for some, the facts a correct answer must state. A test
checks that every label points at a provision that exists and is in force.

```bash
cd ai-service
# 1. Retrieval ablation: vector only vs keyword only vs hybrid (RRF) vs hybrid + reranker. Run with the REAL models:
EMBEDDING_PROVIDER=fastembed VECTOR_STORE=memory python -m app.evaluation retrieval --rerankers lexical,cross-encoder
# 2. Answer quality (needs a real LLM): fact recall, citation hit/precision, numbers grounded in the cited text, refusal of out-of-scope questions
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=... python -m app.evaluation answers
```
Output goes to `eval/results/<mode>-<date>.md` (tables with 95% bootstrap intervals, split by language, topic and question style, plus the
questions the best method missed) and `.json`. The first run downloads the embedding and reranker models (about 1 GB).
Numbers produced with `EMBEDDING_PROVIDER=hash` only test the harness; do not report them. The string checks (fact recall, number
grounding) flag likely mistakes but cannot prove an answer correct, so read a sample of the answers in the JSON yourself.

## Local development
```bash
# DB with pgvector
docker run -d -p 5432:5432 -e POSTGRES_USER=nyayasetu -e POSTGRES_PASSWORD=nyayasetu -e POSTGRES_DB=nyayasetu pgvector/pgvector:pg16
# AI service  (needs: tesseract-ocr + mar/hin language packs)
cd ai-service && pip install -r requirements-dev.txt && LLM_PROVIDER=mock EMBEDDING_PROVIDER=hash RERANKER=lexical uvicorn app.main:app --port 8000
# Backend
cd backend && JWT_SECRET=$(openssl rand -base64 48) AI_INTERNAL_TOKEN=change-me-internal-token mvn spring-boot:run
# Frontend (proxies /api to :8080)
cd frontend && npm install && npm run dev
```
Tests: `pytest` in `ai-service` (set `TEST_DATABASE_URL` to include pgvector tests) · `mvn test` in `backend`
(set `TEST_DB_URL=jdbc:postgresql://localhost:5432/nyayasetu_test` for the full-stack tests) · `npm test` in `frontend`.

## Security notes
BCrypt(12) passwords, HS256 JWT (≥ 32-char secret enforced), per-user ownership checks on every document/deadline lookup (404, not 403),
login throttling (5 failures / 15 min), content-sniffed uploads with random stored names, service-to-service token between gateway and
AI service (AI service is not published to the host), CSP/security headers in nginx, account erasure endpoint. The JWT is kept in
`localStorage` (mitigated by the CSP); switch to an HttpOnly cookie + CSRF protection if your threat model requires it.

## Known limits / next steps
- Explanations are AI-generated and can be wrong; the UI states this. Not legal advice.
- The login throttle and alert scheduler are single-instance (in-memory / one scheduler); use Redis and a scheduler lock to scale out.
- Chat replies are returned whole (no token streaming yet).
- No refresh tokens (12 h access token); no OCR confidence display; PaddleOCR is wired but optional and untested here.
- The seed knowledge base is tiny; retrieval quality depends on loading real, current legal texts.
