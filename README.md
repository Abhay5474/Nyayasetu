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
`ai-service/knowledge_base/*.json` ships a **small seed corpus** (RTI Act 2005 sections, RTI fee rules, key judgments, Consumer
Protection Act 2019, Limitation Act, NI Act §138, BNSS/BNS highlights, Marathi summaries). These are paraphrased summaries for
demonstration — **verify against official gazette text before relying on them** and extend them for production:
```bash
python -m app.rag.ingest path/to/acts_dir     # .json entries, .md/.txt, or .pdf; idempotent
curl -H "X-Internal-Token: …" -X POST :8000/v1/kb/ingest -d '{"entries":[…]}'
```

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
