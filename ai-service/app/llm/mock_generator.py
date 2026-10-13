"""Offline extractive fallback used when LLM_PROVIDER=mock (demos / CI).

It does NOT translate or truly simplify: it surfaces real sentences, dates and statute citations
found in the document so the whole pipeline can be exercised without an API key.
"""
from __future__ import annotations

import datetime as dt
import re

from app.schemas import Deadline, LegalReference, RequiredAction, SimplifiedDocument, Source

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], 1)}
_NUM_DATE = re.compile(r"\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})\b")
_TXT_DATE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(_MONTHS) + r")[,]?\s+(\d{4})\b", re.I)
_PERIOD = re.compile(
    r"(within\s+(?:\d+|[a-z\-]+)\s+(?:working\s+)?(?:days?|months?|hours?)[^.;।\n]{0,60}|"
    r"(?:\d+)\s*(?:दिवसांत|दिवसांच्या आत|महिन्यांत)[^.;।\n]{0,40})",
    re.I,
)
_SECTION = re.compile(
    r"(?:Section|Sec\.|Article|Rule)\s+\d+[A-Za-z]?(?:\(\w+\))*(?:\s+of\s+(?:the\s+)?[A-Z][\w ,.&'-]{3,60}?(?:Act|Code|Rules|Sanhita)[, ]*(?:\d{4})?)?"
    r"|कलम\s+\d+[A-Za-z]?(?:\(\w+\))*",
)
_ACTION_WORDS = re.compile(r"\b(shall|must|should|required to|directed to|is requested|may file|appeal|submit|pay|appear|reply)\b|"
                           r"(करावे|सादर|भरावे|हजर|अपील)", re.I)


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<!\bRs)(?<!\bNo)(?<!\bSh)(?<!\bDr)(?<!\bSec)(?<=[.!?।])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def _dates(text: str) -> list[tuple[dt.date, str]]:
    found: list[tuple[dt.date, str]] = []
    for m in _NUM_DATE.finditer(text):
        d, mo, y = map(int, m.groups())
        try:
            found.append((dt.date(y, mo, d), m.group(0)))  # Indian documents are day-first
        except ValueError:
            pass
    for m in _TXT_DATE.finditer(text):
        try:
            found.append((dt.date(int(m.group(3)), _MONTHS[m.group(2).lower()], int(m.group(1))), m.group(0)))
        except ValueError:
            pass
    return found


def generate(text: str, language: str, sources: list[Source]) -> SimplifiedDocument:
    sentences = _sentences(text)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    deadlines: list[Deadline] = []
    seen: set[str] = set()
    for s in sentences:
        for m in _PERIOD.finditer(s):
            key = m.group(0).lower()
            if key not in seen:
                seen.add(key)
                deadlines.append(Deadline(description=s[:160], period=m.group(0).strip(), source_text=m.group(0)))
    for date, raw in _dates(text):
        if raw not in seen:
            seen.add(raw)
            ctx = next((s for s in sentences if raw in s), raw)
            deadlines.append(Deadline(description=ctx[:160], date=date, source_text=raw))

    actions = [
        RequiredAction(action=s[:200], priority="high" if re.search(r"within|deadline|last date|अंतिम", s, re.I) else "medium")
        for s in sentences
        if _ACTION_WORDS.search(s)
    ][:5]

    refs = [LegalReference(citation=c.strip(), explanation="", source_id=None) for c in dict.fromkeys(m.group(0) for m in _SECTION.finditer(text))][:6]
    refs += [LegalReference(citation=s.citation, explanation=s.snippet[:200], source_id=s.source_id) for s in sources[:3]]

    notice = (
        "यंत्रवत (डेमो) मोड: हा सारांश मूळ मजकुरातून काढला आहे; भाषांतर किंवा सोपे स्पष्टीकरण उपलब्ध नाही."
        if language == "mr"
        else "Demo mode: this summary is extracted directly from the document, not rewritten by an AI model."
    )
    return SimplifiedDocument(
        document_type="other",
        title=(lines[0][:100] if lines else "Document"),
        summary=" ".join(sentences[:3]) or text[:400],
        key_points=sentences[3:8] or sentences[:5],
        deadlines=deadlines[:8],
        required_actions=actions,
        legal_references=refs,
        caveats=[notice],
    )
