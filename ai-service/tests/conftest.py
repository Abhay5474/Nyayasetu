import os

# Must be set before app modules read settings: no Postgres, no model downloads, no API keys.
os.environ.update(
    VECTOR_STORE="memory",
    EMBEDDING_PROVIDER="hash",
    RERANKER="lexical",
    LLM_PROVIDER="mock",
    AUTO_INGEST_KB="false",
    INTERNAL_TOKEN="test-token",
)

import pymupdf as fitz  # noqa: E402
import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.container import build_container  # noqa: E402
from app.rag.ingest import ingest_path  # noqa: E402


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture(scope="session")
def container(settings):
    c = build_container(settings)
    ingest_path(settings.kb_dir, c.store, c.embedder)
    return c


def make_pdf(pages: list[str]) -> bytes:
    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        page.insert_textbox(fitz.Rect(50, 50, 550, 780), text, fontsize=11)
    return doc.tobytes()
