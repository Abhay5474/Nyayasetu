"""Text cleaning for extracted legal documents (English / Marathi / Hindi)."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from app.processing.text import tokenize

# Zero-width space / BOM / soft hyphen are noise; ZWJ/ZWNJ (200C/200D) are meaningful in Devanagari.
_NOISE = dict.fromkeys(map(ord, "​﻿­⁠"), None)
_PAGE_NUM = re.compile(r"^\s*(?:page\s*)?[-–—]?\s*\d{1,4}\s*(?:of\s*\d{1,4})?\s*[-–—]?\s*$", re.I)
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")
# Marathi uses ळ (U+0933) and distinctive function words; Hindi uses है/और/का/की/के/में/नहीं.
_MR_WORDS = {"आहे", "आहेत", "आणि", "झाला", "झाली", "झाले", "केला", "केली", "केले", "रोजी", "नाही", "करावा", "करावी", "मध्ये", "यांनी", "त्या", "हे", "तो", "ती"}
_HI_WORDS = {"है", "हैं", "और", "का", "की", "के", "में", "नहीं", "को", "से", "था", "थी", "किया", "गया", "गई"}


def detect_language(text: str) -> str:
    """Rough script/language hint: en | mr | hi | unknown."""
    sample = text[:6000]
    deva, latin = len(_DEVANAGARI.findall(sample)), len(_LATIN.findall(sample))
    if deva + latin < 20:
        return "unknown"
    if deva <= latin:
        return "en"
    tokens = tokenize(sample)
    mr = sum(1 for t in tokens if t in _MR_WORDS or "ळ" in t or t.endswith("च्या"))
    hi = sum(1 for t in tokens if t in _HI_WORDS)
    return "hi" if hi > mr else "mr"


def _normalise_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def _strip_repeated_lines(pages: list[list[str]]) -> list[list[str]]:
    """Remove running headers/footers: short lines that open or close most pages."""
    if len(pages) < 3:
        return pages
    counts: Counter[str] = Counter()
    for lines in pages:
        edge = {_normalise_line(x) for x in lines[:3] + lines[-3:] if x.strip()}
        # digits vary page to page ("Page 3"), so compare the digit-free shape
        counts.update({re.sub(r"\d+", "#", x) for x in edge if len(x) < 100})
    threshold = max(3, int(len(pages) * 0.6))
    repeated = {shape for shape, n in counts.items() if n >= threshold}
    return [
        [ln for ln in lines if re.sub(r"\d+", "#", _normalise_line(ln)) not in repeated] for lines in pages
    ]


def _merge_wrapped(lines: list[str]) -> str:
    """Join hard-wrapped lines into paragraphs; keep list items / headings on their own line."""
    out: list[str] = []
    buf = ""
    for raw in lines:
        line = _normalise_line(raw)
        if not line:
            if buf:
                out.append(buf)
                buf = ""
            out.append("")
            continue
        starts_item = bool(re.match(r"^(?:\(?[0-9a-zA-Z०-९]{1,3}[.)]|[-•*●▪]|\d+\.\d+)\s", line))
        is_heading = line.isupper() and len(line) < 80
        if buf and not starts_item and not is_heading and not re.search(r"[.:;?!।]$", buf):
            buf = buf[:-1] + line if buf.endswith("-") and line[:1].islower() else f"{buf} {line}"
        else:
            if buf:
                out.append(buf)
            buf = line
    if buf:
        out.append(buf)
    return "\n".join(out)


def clean_pages(pages: list[str]) -> str:
    """Normalise a list of per-page texts into one clean document string."""
    split = [
        [ln for ln in unicodedata.normalize("NFC", p).translate(_NOISE).replace("\r", "\n").split("\n")]
        for p in pages
    ]
    split = _strip_repeated_lines(split)
    kept: list[str] = []
    for lines in split:
        kept.extend(ln for ln in lines if not _PAGE_NUM.match(ln))
        kept.append("")  # page break == paragraph break
    text = _merge_wrapped(kept)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_text(text: str) -> str:
    return clean_pages([text])
