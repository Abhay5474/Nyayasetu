"""Section-aware splitting of Acts and Rules into one entry per provision.

Chunking legal text by size can cut a section in half or separate "Section 19" from its text. These parsers
split on the numbered provisions instead, so every chunk is a whole section/rule with its number and heading.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# Running page headers of Maharashtra Government Gazette pages (the Marathi text layer is often garbled).
_GAZETTE_HEADER = re.compile(
    r"^\s*\d*\s*महाराष्ट्र\S*\s+शासन\S*(?:\s+राजपत्र\S*)?\s+असाधारण\s+भाग\s+चार-अ.*$|^\s*भाग\s+चार-अ-\S+\s*$", re.M
)
_LINE = re.compile(r"^\s*([0-9०-९]{1,3})\.\s+(.+)$")
# heading ends at ".-", ".–", ".—" or a spaced dash:  "Definitions – (1) In these rules"
_HEADING = re.compile(r"^(?P<h>.+?)(?:\.\s*[-–—]{1,3}|\s+[-–—]{1,3}(?=\s|$))\s*(?P<rest>.*)$")
_ANNEXURE = re.compile(r"^\s*(?:ANNEXURE|Annexure|अनुबंध|परिशिष्ट|जोडपत्र|नमुना)\b")


@dataclass
class Provision:
    number: int
    heading: str
    text: str  # heading line + body


@dataclass
class ParsedInstrument:
    provisions: list[Provision]
    annexures: str  # forms etc. after the last provision


def strip_gazette_headers(text: str) -> str:
    return _GAZETTE_HEADER.sub("", text)


def split_numbered_provisions(text: str) -> ParsedInstrument:
    """Split text containing "1. Heading.- body" provisions (Latin or Devanagari digits), in order.

    A line starts the next provision only if its number is exactly the expected next number and it has a
    heading - this ignores list items and numbers inside the text, and makes OCR noise fail loudly (the
    provision count then comes out short) instead of silently mis-sectioning.
    """
    text = strip_gazette_headers(text)
    provisions: list[tuple[int, str, list[str]]] = []
    annex: list[str] = []
    expected = 1
    in_annex = False
    for line in text.splitlines():
        if in_annex:
            annex.append(line)
            continue
        if provisions and _ANNEXURE.match(line):
            in_annex = True
            annex.append(line)
            continue
        m = _LINE.match(line)
        if m and int(m.group(1).translate(_DEVA_DIGITS)) == expected:
            h = _HEADING.match(m.group(2).strip())
            if h and 3 <= len(h.group("h")) <= 110 and not h.group("h").startswith("("):
                provisions.append((expected, h.group("h").strip(), [h.group("rest")]))
                expected += 1
                continue
        if provisions:
            provisions[-1][2].append(line)
    out = [
        Provision(n, heading, re.sub(r"\n{3,}", "\n\n", f"{heading}. " + "\n".join(body)).strip())
        for n, heading, body in provisions
    ]
    return ParsedInstrument(out, "\n".join(annex).strip())


def split_paragraph_groups(text: str, max_chars: int = 1000) -> list[str]:
    """Fallback for noisy scans where section numbers cannot be trusted: group whole paragraphs."""
    groups, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if cur and len(cur) + len(para) > max_chars:
            groups.append(cur)
            cur = ""
        cur = f"{cur}\n\n{para}".strip()
    if cur:
        groups.append(cur)
    return groups
