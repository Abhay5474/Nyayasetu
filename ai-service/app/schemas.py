"""Pydantic models shared by the API and the LLM output parser."""
from __future__ import annotations

import datetime as dt
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Language = Literal["en", "mr"]
Priority = Literal["high", "medium", "low"]


# --------------------------------------------------------------------------- extraction
class ExtractResponse(BaseModel):
    text: str
    page_count: int
    char_count: int
    method: Literal["digital", "ocr", "mixed"]
    ocr_pages: list[int] = Field(default_factory=list)
    language_hint: Literal["en", "mr", "hi", "unknown"] = "unknown"
    warnings: list[str] = Field(default_factory=list)


# --------------------------------------------------------------------------- LLM output
class Deadline(BaseModel):
    description: str
    # exact calendar date when the document states one (or it is unambiguous)
    date: Optional[dt.date] = None
    # relative period, e.g. "within 30 days of receipt", when no exact date is derivable
    period: Optional[str] = None
    source_text: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def _lenient_date(cls, v):
        if v in (None, "", "null", "None"):
            return None
        if isinstance(v, dt.date):
            return v
        try:
            return dt.date.fromisoformat(str(v).strip()[:10])
        except ValueError:
            return None


class RequiredAction(BaseModel):
    action: str
    priority: Priority = "medium"
    due: Optional[str] = None

    @field_validator("priority", mode="before")
    @classmethod
    def _lenient_priority(cls, v):
        v = str(v or "medium").strip().lower()
        return v if v in ("high", "medium", "low") else "medium"


class LegalReference(BaseModel):
    citation: str
    explanation: str = ""
    # "S1", "S2", ... -> id of a retrieved knowledge-base source; None = cited in the document itself
    source_id: Optional[str] = None


class SimplifiedDocument(BaseModel):
    document_type: str = "other"
    title: str = ""
    summary: str
    key_points: list[str] = Field(default_factory=list)
    deadlines: list[Deadline] = Field(default_factory=list)
    required_actions: list[RequiredAction] = Field(default_factory=list)
    legal_references: list[LegalReference] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)

    @field_validator("key_points", "caveats", mode="before")
    @classmethod
    def _strings(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [str(x) for x in v if str(x).strip()]

    @field_validator("deadlines", "required_actions", "legal_references", mode="before")
    @classmethod
    def _lists(cls, v):
        return v or []


# --------------------------------------------------------------------------- RAG sources
class Source(BaseModel):
    source_id: str  # S1, S2 ... (per response)
    kb_id: str
    kind: str  # act | rule | notification | judgment | other
    title: str
    citation: str
    jurisdiction: str = "India"
    snippet: str
    score: float = 0.0
    cited: bool = False


class SimplifyRequest(BaseModel):
    text: str = Field(min_length=20)
    language: Language = "en"
    document_id: Optional[str] = None


class SimplifyResponse(BaseModel):
    language: Language
    document: SimplifiedDocument
    sources: list[Source] = Field(default_factory=list)
    model: str
    generated_at: dt.datetime
    used_map_reduce: bool = False


# --------------------------------------------------------------------------- knowledge base
class KbEntry(BaseModel):
    id: str
    kind: Literal["act", "rule", "notification", "judgment", "other"] = "other"
    title: str
    citation: str
    jurisdiction: str = "India"
    language: str = "en"
    text: str = Field(min_length=10)


class KbIngestRequest(BaseModel):
    entries: list[KbEntry]


class KbIngestResponse(BaseModel):
    entries: int
    chunks: int


# --------------------------------------------------------------------------- document Q&A
class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=6000)


class ChatRequest(BaseModel):
    text: str = Field(min_length=20)  # the extracted document text
    question: str = Field(min_length=1, max_length=1000)
    language: Language = "en"
    history: list[ChatTurn] = Field(default_factory=list, max_length=30)


class ChatAnswer(BaseModel):
    """What the LLM is asked to return."""

    answer: str
    answerable: bool = True  # False when the document / sources do not contain the answer
    quotes: list[str] = Field(default_factory=list)  # short verbatim snippets from the document
    source_ids: list[str] = Field(default_factory=list)  # S1.. knowledge-base sources used
    follow_ups: list[str] = Field(default_factory=list)

    @field_validator("quotes", "source_ids", "follow_ups", mode="before")
    @classmethod
    def _strs(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return [str(x) for x in v if str(x).strip()]


class ChatResponse(BaseModel):
    language: Language
    answer: str
    answerable: bool
    quotes: list[str] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    model: str
    generated_at: dt.datetime
