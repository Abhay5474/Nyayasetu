"""Sentence-aware chunking for long documents and knowledge-base entries."""
from __future__ import annotations

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Paragraph -> line -> sentence (Latin and Devanagari danda) -> clause -> word.
SEPARATORS = ["\n\n", "\n", "। ", "॥ ", ". ", "? ", "! ", "; ", ", ", " ", ""]


def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=min(overlap, chunk_size // 2),
        separators=SEPARATORS,
        keep_separator="end",
    )
    return [c.strip() for c in splitter.split_text(text) if c.strip()]
