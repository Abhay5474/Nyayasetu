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


def entry_to_chunks(entry: KbEntry, origin: str = "files") -> list[Chunk]:
    parts = chunk_text(entry.text, KB_CHUNK_SIZE, KB_CHUNK_OVERLAP) or [entry.text]
    chunks = []
    for i, part in enumerate(parts):
        meta = {
            "origin": origin,
            "source_type": entry.source_type,
            "source_title": entry.source_title,
            "source_url": entry.source_url,
            "gazette_ref": entry.gazette_ref,
            "section_ref": entry.section_ref,
            "version_date": entry.version_date,
            "verified_at": entry.verified_at,
            "verified_by": entry.verified_by,
            "ocr": entry.ocr,
        }
        digest = hashlib.sha256(
            f"{entry.title}|{entry.citation}|{entry.kind}|{entry.jurisdiction}|{entry.status}|{json.dumps(meta, sort_keys=True)}|{part}".encode()
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
                status=entry.status,
                meta=meta,
            )
        )
    return chunks


def ingest_entries(entries: list[KbEntry], store: KnowledgeStore, embedder: Embedder, origin: str = "api") -> tuple[int, int]:
    """Embed and upsert only chunks that are new or changed. Returns (entries, chunks written)."""
    known = store.existing_hashes()
    pending = [c for e in entries for c in entry_to_chunks(e, origin) if known.get(c.id) != c.content_hash]
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


def ingest_path(path: Path, store: KnowledgeStore, embedder: Embedder, prune: bool | None = None) -> tuple[int, int]:
    """Ingest a knowledge-base directory (or a single file).

    A directory is treated as the source of truth: its JSON entries and the PDFs listed in
    `sources/manifest.json` are loaded, and previously ingested file-origin entries that no longer exist are removed.
    """
    settings = get_settings()
    entries: list[KbEntry] = []
    if path.is_dir():
        from app.rag.sources import entries_from_source, load_manifest

        for src in load_manifest(path):
            try:
                entries.extend(entries_from_source(src, path, settings))
            except Exception:
                log.exception("Could not load official source %s", src.get("id"))
        files = sorted(p for p in path.glob("*") if p.is_file())  # top-level JSON/MD/TXT only (sources/ is separate)
    else:
        files = [path]
    for f in files:
        try:
            entries.extend(load_entries(f))
        except Exception:
            log.exception("Skipping unreadable knowledge-base file %s", f)
    result = ingest_entries(entries, store, embedder, origin="files")
    if prune if prune is not None else path.is_dir():
        removed = store.prune("files", {e.id for e in entries})
        if removed:
            log.info("Pruned %d stale knowledge-base chunk(s)", removed)
    return result


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
