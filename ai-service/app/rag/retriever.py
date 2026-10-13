"""Hybrid retrieval: dense (pgvector) + sparse (full-text) -> RRF fusion -> rerank."""
from __future__ import annotations

from dataclasses import dataclass

from app.rag.embeddings import Embedder
from app.rag.reranker import Reranker
from app.rag.store import Hit, KnowledgeStore

RRF_K = 60


def rrf_fuse(rankings: list[list[Hit]], weights: list[float] | None = None) -> list[Hit]:
    """Reciprocal Rank Fusion: score(d) = sum_i w_i / (RRF_K + rank_i(d)). Scale-free across retrievers."""
    weights = weights or [1.0] * len(rankings)
    fused: dict[str, float] = {}
    chunks = {}
    for ranking, w in zip(rankings, weights):
        for rank, hit in enumerate(ranking, start=1):
            fused[hit.chunk.id] = fused.get(hit.chunk.id, 0.0) + w / (RRF_K + rank)
            chunks[hit.chunk.id] = hit.chunk
    return [Hit(chunks[cid], s) for cid, s in sorted(fused.items(), key=lambda kv: kv[1], reverse=True)]


@dataclass
class RetrievalConfig:
    candidates: int = 20
    rerank_candidates: int = 16
    top_k: int = 6


class HybridRetriever:
    def __init__(self, store: KnowledgeStore, embedder: Embedder, reranker: Reranker, cfg: RetrievalConfig):
        self.store, self.embedder, self.reranker, self.cfg = store, embedder, reranker, cfg

    def retrieve(self, queries: list[str] | str, top_k: int | None = None) -> list[Hit]:
        """Retrieve for one or several query formulations and return reranked, de-duplicated hits."""
        queries = [queries] if isinstance(queries, str) else [q for q in queries if q.strip()]
        if not queries:
            return []
        rankings: list[list[Hit]] = []
        for q in queries:
            rankings.append(self.store.vector_search(self.embedder.embed_query(q), self.cfg.candidates))
            rankings.append(self.store.keyword_search(q, self.cfg.candidates))
        fused = rrf_fuse([r for r in rankings if r])[: self.cfg.rerank_candidates]
        return self.reranker.rerank(" ".join(queries)[:2000], fused, top_k or self.cfg.top_k)
