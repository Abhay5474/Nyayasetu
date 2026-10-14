"""Integration tests against real Tesseract and PostgreSQL+pgvector. Skipped when unavailable.

    TEST_DATABASE_URL=postgresql://nyayasetu:nyayasetu@localhost:5432/nyayasetu pytest tests/test_integration.py
"""
import os
import shutil
from pathlib import Path

import pymupdf
import pytest

from app.extraction.extractor import DocumentExtractor
from app.rag.embeddings import HashEmbedder
from app.rag.ingest import ingest_path
from app.rag.reranker import LexicalReranker
from app.rag.retriever import HybridRetriever, RetrievalConfig

DEVA_FONT = Path("/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf")
DB_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.mark.skipif(not shutil.which("tesseract") or not DEVA_FONT.exists(), reason="tesseract / Devanagari font missing")
def test_marathi_scan_is_read_by_tesseract(settings):
    page_doc = pymupdf.open()
    page = page_doc.new_page()
    css = f"@font-face {{font-family: deva; src: url('{DEVA_FONT}');}} body {{font-family: deva; font-size: 16pt}}"
    page.insert_htmlbox(pymupdf.Rect(40, 40, 555, 400), "<p>माहितीचा अधिकार अधिनियम अंतर्गत आपला अर्ज प्राप्त झाला.</p><p>Appeal within 30 days.</p>", css=css)
    scan = pymupdf.open()
    scan.new_page().insert_image(scan[0].rect, pixmap=page.get_pixmap(dpi=200))
    result = DocumentExtractor(settings).extract(scan.tobytes())
    assert result.method == "ocr"
    assert "अधिकार" in result.text and "30 days" in result.text


@pytest.mark.skipif(not DB_URL, reason="TEST_DATABASE_URL not set")
def test_pgvector_hybrid_retrieval(settings):
    import psycopg
    from app.rag.store import PgVectorStore

    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS kb.kb_chunks")
    embedder = HashEmbedder(384)
    store = PgVectorStore(DB_URL, 384)
    store.setup()
    entries, chunks = ingest_path(settings.kb_dir, store, embedder)
    assert chunks == store.count() >= 28
    assert ingest_path(settings.kb_dir, store, embedder)[1] == 0  # idempotent

    retriever = HybridRetriever(store, embedder, LexicalReranker(), RetrievalConfig(20, 16, 4))
    ids = [h.chunk.kb_id for h in retriever.retrieve("first appeal within 30 days against PIO decision")]
    assert "rti-act-2005-en-s19" in ids
    mr_ids = [h.chunk.kb_id for h in retriever.retrieve("प्रथम अपील किती दिवसांत करावे")]
    assert "rti-marathi-s19-s20" in mr_ids
    assert store.keyword_search("दंड 250 रुपये", 5)  # Devanagari tokens survive to_tsvector/to_tsquery
    # Keyword ranking is weighted by rarity: filler words ("is", "free", "person") must not outrank "poverty".
    poverty = [h.chunk.kb_id for h in store.keyword_search("is information free for a person below the poverty line", 3)]
    assert poverty[0] == "rti-act-2005-en-s7"
    penalty = [h.chunk.kb_id for h in store.keyword_search("What is the penalty on a Public Information Officer for delaying information?", 3)]
    assert penalty[0] == "rti-act-2005-en-s20"
