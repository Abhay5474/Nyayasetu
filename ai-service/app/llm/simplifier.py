"""LangChain pipeline: (optional map-reduce) -> RAG retrieval -> bilingual structured explanation."""
from __future__ import annotations

import datetime as dt
import json
import logging
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from app.config import Settings
from app.llm import mock_generator
from app.llm.prompts import (
    HUMAN_PROMPT, LANGUAGE_NAMES, MAP_HUMAN, MAP_SYSTEM, OUTPUT_SCHEMA, REPAIR_HUMAN, SYSTEM_PROMPT,
)
from app.processing.chunking import chunk_text
from app.rag.retriever import HybridRetriever
from app.rag.store import Hit
from app.schemas import SimplifiedDocument, SimplifyResponse, Source

log = logging.getLogger(__name__)

_SECTION_HINT = re.compile(r"(?:Section|Sec\.)\s+\d+[A-Za-z]?(?:\(\w+\))*(?:\s+of\s+(?:the\s+)?[A-Z][\w ,.&'-]{3,60}?(?:Act|Code|Rules)[, ]*(?:\d{4})?)?|कलम\s+\d+", re.I)
_ACT_HINT = re.compile(r"[A-Z][A-Za-z&' -]{3,60}\s(?:Act|Rules|Code|Sanhita)[, ]*\d{4}")


class GenerationError(RuntimeError):
    """The model did not return a usable explanation."""


def extract_json(raw: str) -> dict:
    """Pull the first JSON object out of a model reply (tolerates code fences / chatter)."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
    start = raw.find("{")
    if start == -1:
        raise ValueError("no JSON object found")
    depth, in_str, esc = 0, False, False
    for i in range(start, len(raw)):
        ch = raw[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(raw[start : i + 1])
    raise ValueError("unterminated JSON object")


def build_queries(text: str) -> list[str]:
    """Multiple retrieval formulations: document opening, cited statutes/sections, closing paragraph."""
    queries = [text[:700]]
    hints = list(dict.fromkeys(m.group(0).strip() for m in _SECTION_HINT.finditer(text)))[:6]
    hints += list(dict.fromkeys(m.group(0).strip() for m in _ACT_HINT.finditer(text)))[:4]
    if hints:
        queries.append("; ".join(hints))
    if len(text) > 1800:
        queries.append(text[-600:])
    return queries


class Simplifier:
    def __init__(self, settings: Settings, retriever: HybridRetriever | None, llm: BaseChatModel | None):
        self.settings = settings
        self.retriever = retriever
        self.llm = llm  # None => extractive mock mode

    @property
    def model_name(self) -> str:
        return "mock-extractive" if self.llm is None else self.settings.llm_model

    # ------------------------------------------------------------------ public
    def simplify(self, text: str, language: str) -> SimplifyResponse:
        reduced, used_map_reduce = self._condense(text)
        sources = self._retrieve(text if not used_map_reduce else reduced)
        if self.llm is None:
            doc = mock_generator.generate(text, language, sources)
        else:
            doc = self._generate(reduced, language, sources)
        doc, sources = self._ground(doc, sources)
        return SimplifyResponse(
            language=language,  # type: ignore[arg-type]
            document=doc,
            sources=sources,
            model=self.model_name,
            generated_at=dt.datetime.now(dt.timezone.utc),
            used_map_reduce=used_map_reduce,
        )

    # ------------------------------------------------------------------ steps
    def _condense(self, text: str) -> tuple[str, bool]:
        s = self.settings
        if self.llm is None or len(text) <= s.max_direct_chars:
            return text, False
        chunks = chunk_text(text, s.chunk_size * 3, s.chunk_overlap)[: s.max_map_chunks]
        prompt = ChatPromptTemplate.from_messages([("system", MAP_SYSTEM), ("human", MAP_HUMAN)])
        chain = prompt | self.llm | StrOutputParser()
        notes = chain.batch(
            [{"index": i + 1, "total": len(chunks), "chunk": c} for i, c in enumerate(chunks)],
            config={"max_concurrency": 4},
        )
        log.info("Map-reduce: %d chunks condensed", len(chunks))
        return "\n\n".join(f"[Part {i + 1}]\n{n.strip()}" for i, n in enumerate(notes)), True

    def _retrieve(self, text: str) -> list[Source]:
        if self.retriever is None:
            return []
        try:
            hits: list[Hit] = self.retriever.retrieve(build_queries(text))
        except Exception:
            log.exception("Retrieval failed; continuing without knowledge-base context")
            return []
        return [
            Source(
                source_id=f"S{i}",
                kb_id=h.chunk.kb_id,
                kind=h.chunk.kind,
                title=h.chunk.title,
                citation=h.chunk.citation,
                jurisdiction=h.chunk.jurisdiction,
                snippet=h.chunk.text,
                score=round(h.score, 4),
            )
            for i, h in enumerate(hits, start=1)
        ]

    def _generate(self, document: str, language: str, sources: list[Source]) -> SimplifiedDocument:
        assert self.llm is not None
        source_block = "\n\n".join(
            f"[{s.source_id}] {s.citation} ({s.kind}, {s.jurisdiction})\n{s.snippet}" for s in sources
        ) or "(none available)"
        prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("human", HUMAN_PROMPT)])
        variables = {
            "language_name": LANGUAGE_NAMES[language],
            "today": dt.date.today().isoformat(),
            "schema": OUTPUT_SCHEMA,
            "sources": source_block,
            "document": document,
        }
        messages = prompt.format_messages(**variables)
        raw = self.llm.invoke(messages)
        text = raw.content if isinstance(raw.content, str) else "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in raw.content
        )
        try:
            return SimplifiedDocument.model_validate(extract_json(text))
        except (ValueError, ValidationError) as first_error:
            log.warning("First parse failed (%s); asking the model to repair", first_error)
            retry = self.llm.invoke(
                [*messages, AIMessage(content=text), HumanMessage(content=REPAIR_HUMAN.format(error=str(first_error)[:300]))]
            )
            retry_text = retry.content if isinstance(retry.content, str) else str(retry.content)
            try:
                return SimplifiedDocument.model_validate(extract_json(retry_text))
            except (ValueError, ValidationError) as exc:
                raise GenerationError(f"Model returned invalid output: {exc}") from exc

    @staticmethod
    def _ground(doc: SimplifiedDocument, sources: list[Source]) -> tuple[SimplifiedDocument, list[Source]]:
        """Drop citations to sources that were never retrieved; mark the ones that were really cited."""
        by_id = {s.source_id: s for s in sources}
        for ref in doc.legal_references:
            if ref.source_id:
                sid = ref.source_id.strip().strip("[]").upper()
                if sid in by_id:
                    ref.source_id = sid
                    by_id[sid].cited = True
                else:
                    log.warning("Dropping hallucinated source id %s", ref.source_id)
                    ref.source_id = None
        ordered = sorted(sources, key=lambda s: (not s.cited, s.source_id))
        return doc, ordered
