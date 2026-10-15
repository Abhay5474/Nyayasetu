"""NyayaSetu AI service: extraction (PyMuPDF/OCR), RAG retrieval and LangChain simplification."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Body, Depends, FastAPI, File, HTTPException, Query, Request, Response, UploadFile, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.container import Container, build_container, ingest_in_background
from app.extraction.extractor import ExtractionError
from app.drafts import render as draft_render
from app.drafts import templates as draft_templates
from app.drafts.schemas import DraftDocument, FeePaymentReply, FirstAppeal, RtiApplication
from app.llm.check import probe
from app.llm.errors import LlmCallError, classify
from app.llm.simplifier import GenerationError
from app.rag.ingest import ingest_entries
from app.schemas import (
    ChatRequest, ChatResponse, ExtractResponse, KbIngestRequest, KbIngestResponse, SimplifyRequest, SimplifyResponse,
)
from app.security import require_internal_token

log = logging.getLogger("nyayasetu.ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if getattr(app.state, "container", None) is None:  # tests inject their own container
        app.state.container = build_container(settings)
        if settings.auto_ingest_kb:
            ingest_in_background(app.state.container)
    yield


app = FastAPI(title="NyayaSetu AI Service", version="1.0.0", lifespan=lifespan)


def get_container(request: Request) -> Container:
    return request.app.state.container


@app.exception_handler(ExtractionError)
async def _extraction_error(_: Request, exc: ExtractionError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(GenerationError)
async def _generation_error(_: Request, exc: GenerationError):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(LlmCallError)
async def _llm_call_error(_: Request, exc: LlmCallError):
    log.error("LLM call failed (%s): %s", exc.code, exc)
    return JSONResponse(status_code=exc.http_status, content={"detail": str(exc), "code": exc.code})


def _guard_llm(fn, *args):
    """Run an LLM-backed operation; provider failures become LlmCallError (clear message) instead of a bare 500."""
    try:
        return fn(*args)
    except GenerationError:
        raise
    except Exception as exc:
        known = classify(exc)
        if known is None:
            raise
        raise known from exc


class DraftInputError(Exception):
    """The draft form has a problem the person can fix; the message names each field in plain words."""


_PLAIN = {
    "missing": "is required", "string_too_short": "is required", "string_too_long": "is too long", "too_short": "needs at least one entry",
    "too_long": "has too many entries", "literal_error": "has a choice that is not allowed", "date_parsing": "is not a valid date",
    "date_from_datetime_parsing": "is not a valid date", "decimal_parsing": "must be a number", "int_parsing": "must be a whole number",
    "decimal_max_digits": "is too large", "greater_than": "must be more than zero", "greater_than_equal": "is too small", "less_than_equal": "is too large",
}


def _format_draft_errors(errors) -> str:
    """One readable "field: problem" per error, without pydantic's internal paths."""
    out: list[str] = []
    for err in errors:
        where = ".".join(str(p) for p in err.get("loc", ()) if not isinstance(p, int) and p not in ("body",))
        msg = _PLAIN.get(err.get("type", ""), str(err.get("msg", "is not valid")).removeprefix("Value error, "))
        text = msg if (not where or msg.startswith(where + ":")) else f"{where}: {msg}"
        if text not in out:
            out.append(text)
    return "; ".join(out[:6]) or "Invalid request"


@app.exception_handler(DraftInputError)
async def _draft_input_error(_: Request, exc: DraftInputError):
    return JSONResponse(status_code=422, content={"detail": str(exc), "code": "validation"})


@app.exception_handler(RequestValidationError)
async def _validation_error(request: Request, exc: RequestValidationError):
    """Draft forms get a readable message; every other endpoint keeps FastAPI's default 422 body."""
    if not request.url.path.startswith("/v1/drafts"):
        return await request_validation_exception_handler(request, exc)
    return JSONResponse(status_code=422, content={"detail": _format_draft_errors(exc.errors()), "code": "validation"})


@app.get("/health")
def health(c: Container = Depends(get_container)):
    ping = getattr(c.store, "ping", lambda: True)()
    ok = ping and c.llm_error is None
    return {
        "status": "ok" if ok else "degraded",
        "llm_provider": c.settings.llm_provider,
        "llm_model": c.simplifier.model_name if c.simplifier else None,
        "llm_error": c.llm_error,
        "llm_chain": [label for label, _ in c.llm_chain.models] if c.llm_chain else [],
        "database": ping,
        "knowledge_base": {"chunks": c.store.count() if ping else None, **c.kb_status},
        "embedding_model": c.embedder.name,
        "reranker": c.retriever.reranker.name,
        "ocr_engine": c.settings.ocr_engine,
    }


@app.get("/v1/llm/check", dependencies=[Depends(require_internal_token)])
def llm_check(c: Container = Depends(get_container)):
    """One tiny call to EACH configured model (primary and fallbacks): verifies provider, key, base URL and model name."""
    if c.settings.llm_provider == "mock":
        return {"ok": True, "provider": "mock", "detail": "LLM_PROVIDER=mock: no real model is called."}
    if c.llm_error or c.llm_chain is None:
        return JSONResponse(status_code=503, content={"ok": False, "provider": c.settings.llm_provider, "detail": c.llm_error})
    results = probe(c.llm_chain)
    ok = any(r["ok"] for r in results)  # the service works as long as one model in the chain answers
    return JSONResponse(status_code=200 if ok else 502, content={"ok": ok, "primary_ok": results[0]["ok"], "models": results})


@app.post("/v1/extract", response_model=ExtractResponse, dependencies=[Depends(require_internal_token)])
def extract(file: UploadFile = File(...), c: Container = Depends(get_container)):
    data = file.file.read(c.settings.max_upload_mb * 1024 * 1024 + 1)
    if len(data) > c.settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
    r = c.extractor.extract(data)
    return ExtractResponse(
        text=r.text, page_count=r.page_count, char_count=len(r.text), method=r.method,
        ocr_pages=r.ocr_pages, language_hint=r.language_hint, warnings=r.warnings,
    )


@app.post("/v1/simplify", response_model=SimplifyResponse, dependencies=[Depends(require_internal_token)])
def simplify(req: SimplifyRequest, c: Container = Depends(get_container)):
    if c.simplifier is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"LLM is not configured: {c.llm_error}")
    return _guard_llm(c.simplifier.simplify, req.text, req.language)


@app.post("/v1/chat", response_model=ChatResponse, dependencies=[Depends(require_internal_token)])
def chat(req: ChatRequest, c: Container = Depends(get_container)):
    if c.chat is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"LLM is not configured: {c.llm_error}")
    return _guard_llm(c.chat.answer, req.text, req.question, req.language, req.history)


@app.get("/v1/kb/search", dependencies=[Depends(require_internal_token)])
def kb_search(q: str = Query(min_length=2), k: int = Query(5, ge=1, le=20), c: Container = Depends(get_container)):
    hits = c.retriever.retrieve(q, top_k=k)
    return [
        {"kb_id": h.chunk.kb_id, "citation": h.chunk.citation, "kind": h.chunk.kind, "score": round(h.score, 4),
         "text": h.chunk.text}
        for h in hits
    ]


@app.post("/v1/kb/ingest", response_model=KbIngestResponse, dependencies=[Depends(require_internal_token)])
def kb_ingest(req: KbIngestRequest, c: Container = Depends(get_container)):
    entries, chunks = ingest_entries(req.entries, c.store, c.embedder)
    return KbIngestResponse(entries=entries, chunks=chunks)


# ----------------------------------------------------------------------------- drafts (RTI application / appeal / fee reply)
_DRAFT_MODELS = {"rti_application": RtiApplication, "first_appeal": FirstAppeal, "fee_payment_reply": FeePaymentReply}


def _parse_draft(payload: dict):
    """Pick the model by `kind` ourselves (a framework-level union would report errors for every document type at once)."""
    model = _DRAFT_MODELS.get(str(payload.get("kind")))
    if model is None:
        raise DraftInputError("kind: choose rti_application, first_appeal or fee_payment_reply")
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise DraftInputError(_format_draft_errors(exc.errors())) from exc


@app.post("/v1/drafts/preview", response_model=DraftDocument, dependencies=[Depends(require_internal_token)])
def draft_preview(payload: dict = Body(...)):
    return draft_templates.build(_parse_draft(payload))


@app.post("/v1/drafts/file", dependencies=[Depends(require_internal_token)])
def draft_file(payload: dict = Body(...), format: str = Query("pdf", pattern="^(pdf|docx)$")):
    doc = draft_templates.build(_parse_draft(payload))
    if format == "docx":
        data, mime = draft_render.to_docx(doc), draft_render.DOCX_MIME
    else:
        data, mime = draft_render.to_pdf(doc), draft_render.PDF_MIME
    return Response(content=data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{doc.filename}.{format}"'})
