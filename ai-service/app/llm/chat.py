"""Multi-turn Q&A over one uploaded document, grounded in the document and the legal knowledge base."""
from __future__ import annotations

import datetime as dt
import hashlib
import logging
import re
import threading
from collections import OrderedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import ValidationError

from app.config import Settings
from app.llm import mock_generator
from app.llm.prompts import CHAT_HUMAN, CHAT_SCHEMA, CHAT_SYSTEM, LANGUAGE_NAMES, REPAIR_HUMAN
from app.llm.simplifier import GenerationError, extract_json, hits_to_sources, source_header
from app.processing.chunking import chunk_text
from app.rag.embeddings import Embedder
from app.rag.reranker import LexicalReranker
from app.rag.retriever import HybridRetriever, RetrievalConfig
from app.rag.store import Chunk, InMemoryStore
from app.schemas import ChatAnswer, ChatResponse, ChatTurn, Source

log = logging.getLogger(__name__)

MAX_HISTORY_TURNS = 8  # recent messages replayed to the model
MAX_TURN_CHARS = 1500
EXCERPT_CHUNK = 900
EXCERPT_TOP_K = 6


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


class DocumentIndex:
    """Small in-memory hybrid index over one document's chunks (for documents too long for the prompt)."""

    def __init__(self, text: str, embedder: Embedder):
        pieces = chunk_text(text, EXCERPT_CHUNK, 120)
        vectors = embedder.embed_documents(pieces)
        store = InMemoryStore()
        store.upsert([
            Chunk(id=f"d#{i}", kb_id="doc", kind="other", title="doc", citation="doc", jurisdiction="",
                  language="", text=piece, embedding=vec)
            for i, (piece, vec) in enumerate(zip(pieces, vectors))
        ])
        self.order = {f"d#{i}": i for i in range(len(pieces))}
        self.retriever = HybridRetriever(store, embedder, LexicalReranker(), RetrievalConfig(20, 12, EXCERPT_TOP_K))

    def excerpts(self, query: str) -> str:
        hits = self.retriever.retrieve(query, top_k=EXCERPT_TOP_K)
        ordered = sorted(hits, key=lambda h: self.order[h.chunk.id])  # keep reading order
        return "\n[...]\n".join(h.chunk.text for h in ordered)


class _IndexCache:
    """LRU of per-document indexes so follow-up questions do not re-embed a long document."""

    def __init__(self, size: int = 8):
        self.size, self._d, self._lock = size, OrderedDict(), threading.Lock()

    def get(self, text: str, embedder: Embedder) -> DocumentIndex:
        key = hashlib.sha256(text.encode()).hexdigest()
        with self._lock:
            if key in self._d:
                self._d.move_to_end(key)
                return self._d[key]
        index = DocumentIndex(text, embedder)  # built outside the lock (can be slow)
        with self._lock:
            self._d[key] = index
            while len(self._d) > self.size:
                self._d.popitem(last=False)
        return index


class DocumentChat:
    def __init__(self, settings: Settings, retriever: HybridRetriever | None, embedder: Embedder, llm: BaseChatModel | None):
        self.settings, self.retriever, self.embedder, self.llm = settings, retriever, embedder, llm
        self._indexes = _IndexCache()

    @property
    def model_name(self) -> str:
        return "mock-extractive" if self.llm is None else self.settings.llm_model

    # ------------------------------------------------------------------ public
    def answer(self, text: str, question: str, language: str, history: list[ChatTurn]) -> ChatResponse:
        recent = history[-MAX_HISTORY_TURNS:]
        # Follow-ups like "and what about the second one?" retrieve badly alone: add the previous user question.
        previous_q = next((t.content for t in reversed(recent) if t.role == "user"), "")
        retrieval_query = f"{previous_q} {question}".strip()

        excerpts = self._excerpts(text, retrieval_query)
        sources = self._sources(question, retrieval_query)

        if self.llm is None:
            parsed = mock_generator.answer(excerpts, question, language)
        else:
            parsed = self._ask_llm(excerpts, sources, question, language, recent)

        quotes = self._verified_quotes(parsed.quotes, text)
        used = {sid.strip().strip("[]").upper() for sid in parsed.source_ids}
        cited = [s.model_copy(update={"cited": True}) for s in sources if s.source_id in used]
        return ChatResponse(
            language=language,  # type: ignore[arg-type]
            answer=parsed.answer.strip(),
            answerable=parsed.answerable,
            quotes=quotes,
            sources=cited,
            follow_ups=parsed.follow_ups[:3],
            model=self.model_name,
            generated_at=dt.datetime.now(dt.timezone.utc),
        )

    # ------------------------------------------------------------------ steps
    def _excerpts(self, text: str, query: str) -> str:
        if len(text) <= self.settings.max_direct_chars:
            return text
        return self._indexes.get(text, self.embedder).excerpts(query)

    def _sources(self, question: str, context_query: str) -> list[Source]:
        if self.retriever is None:
            return []
        try:
            return hits_to_sources(self.retriever.retrieve([question, context_query], top_k=4))
        except Exception:
            log.exception("Knowledge-base retrieval failed; answering from the document only")
            return []

    def _messages(self, excerpts: str, sources: list[Source], question: str, language: str,
                  history: list[ChatTurn]) -> list[BaseMessage]:
        source_block = "\n\n".join(f"{source_header(s)}\n{s.snippet}" for s in sources) or "(none available)"
        system = CHAT_SYSTEM.format(language_name=LANGUAGE_NAMES[language], today=dt.date.today().isoformat(),
                                    schema=CHAT_SCHEMA)
        messages: list[BaseMessage] = [SystemMessage(content=system)]
        for turn in history:
            content = turn.content[:MAX_TURN_CHARS]
            messages.append(HumanMessage(content=content) if turn.role == "user" else AIMessage(content=content))
        # Context goes into the latest message only, so it never accumulates across turns.
        messages.append(HumanMessage(content=CHAT_HUMAN.format(sources=source_block, excerpts=excerpts, question=question)))
        return messages

    def _ask_llm(self, excerpts, sources, question, language, history) -> ChatAnswer:
        assert self.llm is not None
        messages = self._messages(excerpts, sources, question, language, history)
        raw = self.llm.invoke(messages)
        text = raw.content if isinstance(raw.content, str) else "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in raw.content)
        try:
            return ChatAnswer.model_validate(extract_json(text))
        except (ValueError, ValidationError) as first:
            log.warning("Chat reply not parseable (%s); retrying once", first)
            retry = self.llm.invoke([*messages, AIMessage(content=text),
                                     HumanMessage(content=REPAIR_HUMAN.format(error=str(first)[:300]))])
            retry_text = retry.content if isinstance(retry.content, str) else str(retry.content)
            try:
                return ChatAnswer.model_validate(extract_json(retry_text))
            except (ValueError, ValidationError) as exc:
                raise GenerationError(f"Model returned invalid output: {exc}") from exc

    @staticmethod
    def _verified_quotes(quotes: list[str], document: str) -> list[str]:
        """Keep only quotes that really occur in the document (whitespace/case-insensitive)."""
        haystack = _norm(document)
        out = []
        for q in quotes:
            nq = _norm(q.strip(" \"'“”‘’…."))
            if len(nq) >= 8 and nq in haystack and q.strip() not in out:
                out.append(q.strip())
        return out[:2]
