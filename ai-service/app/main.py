"""NyayaSetu AI service: extraction (PyMuPDF/OCR), RAG retrieval and LangChain simplification."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.container import Container, build_container, ingest_in_background
from app.extraction.extractor import ExtractionError
from app.llm.simplifier import GenerationError
from app.rag.ingest import ingest_entries
from app.schemas import (
    ExtractResponse, KbIngestRequest, KbIngestResponse, SimplifyRequest, SimplifyResponse,
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


@app.get("/health")
def health(c: Container = Depends(get_container)):
    ping = getattr(c.store, "ping", lambda: True)()
    ok = ping and c.llm_error is None
    return {
        "status": "ok" if ok else "degraded",
        "llm_provider": c.settings.llm_provider,
        "llm_model": c.simplifier.model_name if c.simplifier else None,
        "llm_error": c.llm_error,
        "database": ping,
        "knowledge_base": {"chunks": c.store.count() if ping else None, **c.kb_status},
        "embedding_model": c.embedder.name,
        "reranker": c.retriever.reranker.name,
        "ocr_engine": c.settings.ocr_engine,
    }


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
    return c.simplifier.simplify(req.text, req.language)


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
