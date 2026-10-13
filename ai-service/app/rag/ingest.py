"""Knowledge-base ingestion: JSON entries, Markdown/text and PDF files -> chunks -> embeddings -> store.

CLI:  python -m app.rag.ingest [path ...]      (defaults to the bundled knowledge_base/ directory)
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
from pathlib import Path

from app.config import Settings, get_settings
from app.processing.chunking import chunk_text
from app.rag.embeddings import Embedder
from app.rag.store import Chunk, KnowledgeStore
from app.schemas import KbEntry

log = logging.getLogger(__name__)

KB_CHUNK_SIZE = 1200
KB_CHUNK_OVERLAP = 150


def entry_to_chunks(entry: KbEntry) -> list[Chunk]:
    parts = chunk_text(entry.text, KB_CHUNK_SIZE, KB_CHUNK_OVERLAP) or [entry.text]
    chunks = []
    for i, part in enumerate(parts):
        digest = hashlib.sha256(
            f"{entry.title}|{entry.citation}|{entry.kind}|{entry.jurisdiction}|{part}".encode()
        ).hexdigest()
        chunks.append(
            Chunk(
                id=f"{entry.id}#{i}",
                kb_id=entry.id,
                kind=entry.kind,
                title=entry.title,
                citation=entry.citation,
                jurisdiction=entry.jurisdiction,
                language=entry.language,
                text=part,
                content_hash=digest,
            )
        )
    return chunks


def ingest_entries(entries: list[KbEntry], store: KnowledgeStore, embedder: Embedder) -> tuple[int, int]:
    """Embed and upsert only chunks that are new or changed. Returns (entries, chunks written)."""
    known = store.existing_hashes()
    pending = [c for e in entries for c in entry_to_chunks(e) if known.get(c.id) != c.content_hash]
    for start in range(0, len(pending), 32):
        batch = pending[start : start + 32]
        vectors = embedder.embed_documents([f"{c.title}. {c.citation}. {c.text}" for c in batch])
        for chunk, vec in zip(batch, vectors):
            chunk.embedding = vec
        store.upsert(batch)
    return len(entries), len(pending)


def load_entries(path: Path) -> list[KbEntry]:
    """Load entries from a .json file (list of KbEntry) or a .md/.txt/.pdf document."""
    suffix = path.suffix.lower()
    if suffix == ".json":
        return [KbEntry(**item) for item in json.loads(path.read_text(encoding="utf-8"))]
    if suffix in (".md", ".txt"):
        text = path.read_text(encoding="utf-8")
    elif suffix == ".pdf":
        from app.extraction.extractor import DocumentExtractor

        text = DocumentExtractor(get_settings()).extract(path.read_bytes()).text
    else:
        return []
    title = path.stem.replace("_", " ").replace("-", " ").title()
    return [KbEntry(id=path.stem.lower(), kind="other", title=title, citation=title, text=text)]


def ingest_path(path: Path, store: KnowledgeStore, embedder: Embedder) -> tuple[int, int]:
    files = sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else [path]
    entries: list[KbEntry] = []
    for f in files:
        try:
            entries.extend(load_entries(f))
        except Exception:
            log.exception("Skipping unreadable knowledge-base file %s", f)
    return ingest_entries(entries, store, embedder)


def main(argv: list[str]) -> int:
    from app.container import build_container

    settings: Settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    container = build_container(settings)
    paths = [Path(a) for a in argv] or [settings.kb_dir]
    for p in paths:
        entries, chunks = ingest_path(p, container.store, container.embedder)
        log.info("Ingested %s: %d entries, %d new/changed chunks", p, entries, chunks)
    log.info("Knowledge base now holds %d chunks", container.store.count())
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
