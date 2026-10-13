"""Second-stage reranking of fused retrieval candidates."""
from __future__ import annotations

import logging
from typing import Protocol

from app.config import Settings
from app.processing.text import tokenize
from app.rag.store import Hit

log = logging.getLogger(__name__)


class Reranker(Protocol):
    name: str

    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]: ...


def _passage(hit: Hit) -> str:
    c = hit.chunk
    return f"{c.title}. {c.citation}. {c.text}"


class NoopReranker:
    name = "none"

    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]:
        return hits[:top_k]


class LexicalReranker:
    """Cheap, model-free reranker: query-term coverage + bigram overlap."""

    name = "lexical"

    @staticmethod
    def _grams(text: str) -> tuple[set[str], set[tuple[str, str]]]:
        toks = tokenize(text)
        return set(toks), set(zip(toks, toks[1:]))

    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]:
        qt, qb = self._grams(query)
        out = []
        for h in hits:
            pt, pb = self._grams(_passage(h))
            uni = len(qt & pt) / (len(qt) or 1)
            bi = len(qb & pb) / (len(qb) or 1)
            out.append(Hit(h.chunk, 0.7 * uni + 0.3 * bi))
        return sorted(out, key=lambda h: h.score, reverse=True)[:top_k]


class CrossEncoderReranker:
    """Multilingual cross-encoder (ONNX via fastembed). Falls back to lexical if scoring fails."""

    def __init__(self, model_name: str):
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.name = model_name
        self._model = TextCrossEncoder(model_name=model_name)
        self._fallback = LexicalReranker()

    def rerank(self, query: str, hits: list[Hit], top_k: int) -> list[Hit]:
        if not hits:
            return []
        try:
            scores = list(self._model.rerank(query, [_passage(h) for h in hits]))
        except Exception as exc:
            log.warning("Cross-encoder failed (%s); using lexical reranker", exc)
            return self._fallback.rerank(query, hits, top_k)
        ranked = sorted(zip(hits, scores), key=lambda p: p[1], reverse=True)
        return [Hit(h.chunk, float(s)) for h, s in ranked[:top_k]]


def build_reranker(settings: Settings) -> Reranker:
    if settings.reranker == "none":
        return NoopReranker()
    if settings.reranker == "cross-encoder":
        try:
            return CrossEncoderReranker(settings.reranker_model)
        except Exception as exc:
            log.warning("Cross-encoder reranker unavailable (%s); falling back to lexical", exc)
    return LexicalReranker()
