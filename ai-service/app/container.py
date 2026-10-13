"""Composition root: wires settings -> embedder/store/retriever/LLM/extractor once per process."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field

from app.config import Settings
from app.extraction.extractor import DocumentExtractor
from app.llm.providers import LlmConfigError, build_chat_model
from app.llm.simplifier import Simplifier
from app.rag.embeddings import Embedder, build_embedder
from app.rag.ingest import ingest_path
from app.rag.reranker import build_reranker
from app.rag.retriever import HybridRetriever, RetrievalConfig
from app.rag.store import InMemoryStore, KnowledgeStore, PgVectorStore

log = logging.getLogger(__name__)


@dataclass
class Container:
    settings: Settings
    embedder: Embedder
    store: KnowledgeStore
    retriever: HybridRetriever
    extractor: DocumentExtractor
    simplifier: Simplifier | None
    llm_error: str | None = None
    kb_status: dict = field(default_factory=lambda: {"state": "idle", "error": None})


def build_container(settings: Settings) -> Container:
    embedder = build_embedder(settings)
    store: KnowledgeStore = (
        InMemoryStore() if settings.vector_store == "memory" else PgVectorStore(settings.database_url, embedder.dim)
    )
    store.setup()
    retriever = HybridRetriever(
        store,
        embedder,
        build_reranker(settings),
        RetrievalConfig(settings.retrieval_candidates, settings.rerank_candidates, settings.retrieval_top_k),
    )
    llm, llm_error = None, None
    if settings.llm_provider != "mock":
        try:
            llm = build_chat_model(settings)
        except LlmConfigError as exc:
            llm_error = str(exc)
            log.error("LLM not configured: %s", exc)
    simplifier = None if llm_error else Simplifier(settings, retriever, llm)
    return Container(settings, embedder, store, retriever, DocumentExtractor(settings), simplifier, llm_error)


def ingest_in_background(container: Container) -> threading.Thread:
    """Seed the knowledge base without delaying service start-up (first run may download models)."""

    def run() -> None:
        container.kb_status.update(state="running", error=None)
        try:
            entries, chunks = ingest_path(container.settings.kb_dir, container.store, container.embedder)
            container.kb_status.update(state="ready", entries=entries, new_chunks=chunks)
            log.info("Knowledge base ready: %d entries, %d new chunks", entries, chunks)
        except Exception as exc:
            log.exception("Knowledge-base ingestion failed")
            container.kb_status.update(state="failed", error=str(exc))

    t = threading.Thread(target=run, name="kb-ingest", daemon=True)
    t.start()
    return t
