"""Official source documents (PDFs) -> reviewable text -> knowledge-base entries with provenance.

`knowledge_base/sources/manifest.json` describes each PDF (title, version date, status, parser ...).
The extracted text is written to `knowledge_base/extracted/<id>.txt` so a person can proofread / correct OCR
mistakes; if that file exists it is used instead of re-reading the PDF.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from app.config import Settings
from app.rag.legal_parser import split_numbered_provisions, split_paragraph_groups, strip_gazette_headers
from app.schemas import KbEntry

log = logging.getLogger(__name__)


def extracted_text(src: dict, kb_dir: Path, settings: Settings) -> tuple[str, bool]:
    """Return (text, used_ocr) for a manifest source, reading or creating its extracted-text file."""
    text_path = kb_dir / "extracted" / f"{src.get('text_file', src['id'])}.txt"
    if text_path.exists():
        return text_path.read_text(encoding="utf-8"), bool(src.get("ocr", False))
    from app.extraction.extractor import DocumentExtractor  # heavy import, only when needed

    pdf = kb_dir / "sources" / src["file"]
    result = DocumentExtractor(settings.model_copy(update={"ocr_dpi": 300, "max_pages": 200})).extract(pdf.read_bytes())
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text(result.text, encoding="utf-8")
    log.info("Extracted %s: %d pages, method=%s", src["file"], result.page_count, result.method)
    return result.text, bool(result.ocr_pages)


def _slice(text: str, src: dict) -> str:
    start, end = src.get("slice_from"), src.get("slice_to")
    if start:
        i = text.find(start)
        if i == -1:
            raise ValueError(f"{src['id']}: slice_from marker not found: {start!r}")
        text = text[i:]
    if end:
        j = text.find(end)
        if j == -1:
            raise ValueError(f"{src['id']}: slice_to marker not found: {end!r}")
        text = text[:j]
    return text


def _provenance(src: dict, ocr: bool) -> dict:
    return {
        "status": src.get("status", "in_force"),
        "source_type": "official_pdf",
        "source_title": src["title"],
        "source_url": src.get("source_url"),
        "gazette_ref": src.get("gazette_ref"),
        "version_date": src.get("version_date"),
        "verified_at": src.get("verified_at"),
        "verified_by": src.get("verified_by"),
        "ocr": ocr,
    }


def entries_from_source(src: dict, kb_dir: Path, settings: Settings) -> list[KbEntry]:
    text, ocr = extracted_text(src, kb_dir, settings)
    text = _slice(strip_gazette_headers(text), src)
    prov = _provenance(src, ocr)
    base = dict(kind=src["kind"], title=src["title"], jurisdiction=src.get("jurisdiction", "India"),
                language=src.get("language", "en"), **prov)
    label = src.get("provision_label", "Section")
    short = src.get("short_title", src["title"])
    parser = src.get("parser", "numbered")

    if parser == "numbered":
        parsed = split_numbered_provisions(text)
        expected = src.get("expected_provisions")
        if expected and len(parsed.provisions) != expected:
            raise ValueError(f"{src['id']}: parsed {len(parsed.provisions)} provisions, expected {expected}")
        entries = [
            KbEntry(id=f"{src['id']}-{label[0].lower()}{p.number}", citation=f"{short} - {label} {p.number} ({p.heading})",
                    section_ref=f"{label} {p.number}", text=p.text, **base)
            for p in parsed.provisions
        ]
        if parsed.annexures:
            entries.append(KbEntry(id=f"{src['id']}-annexures", citation=f"{short} - Annexures (prescribed forms)",
                                   section_ref="Annexures", text=parsed.annexures, **base))
        return entries

    # "paragraphs": noisy scans - whole paragraphs, no section labels (numbers cannot be trusted)
    return [
        KbEntry(id=f"{src['id']}-p{i}", citation=f"{short} (excerpt {i})", section_ref=None, text=group, **base)
        for i, group in enumerate(split_paragraph_groups(text), start=1)
        if len(re.sub(r"\W", "", group)) >= 40
    ]


def load_manifest(kb_dir: Path) -> list[dict]:
    path = kb_dir / "sources" / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
