"""Multilingual embedding providers."""
from __future__ import annotations

import hashlib
import logging
from typing import Protocol

import numpy as np

from app.config import Settings
from app.processing.text import tokenize

log = logging.getLogger(__name__)


class Embedder(Protocol):
    name: str
    dim: int

    def embed_documents(self, texts: list[str]) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


def _normalise(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=-1, keepdims=True)
    return mat / np.clip(norms, 1e-9, None)


class FastEmbedEmbedder:
    """ONNX multilingual sentence embeddings (no PyTorch needed). Handles E5 prefixes."""

    def __init__(self, model_name: str, dim: int):
        from fastembed import TextEmbedding

        self.name = model_name
        self.dim = dim
        self._model = TextEmbedding(model_name=model_name)
        self._is_e5 = "e5" in model_name.lower()

    def _run(self, texts: list[str], prefix: str) -> np.ndarray:
        vectors = np.array(list(self._model.embed([prefix + t for t in texts])), dtype=np.float32)
        return _normalise(vectors)

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._run(texts, "passage: " if self._is_e5 else "")

    def embed_query(self, text: str) -> np.ndarray:
        return self._run([text], "query: " if self._is_e5 else "")[0]


class HashEmbedder:
    """Deterministic character-n-gram hashing embedder.

    Works fully offline and across scripts (Latin + Devanagari) so tests and quick demos run
    without downloading a model. Quality is lexical-ish; use FastEmbed in production.
    """

    def __init__(self, dim: int = 384):
        self.name = f"hash-{dim}"
        self.dim = dim

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        tokens = tokenize(text)
        for tok in tokens:
            padded = f"^{tok}$"
            grams = [padded[i : i + n] for n in (3, 4) for i in range(max(1, len(padded) - n + 1))]
            for g in grams + [tok]:
                h = int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "little")
                v[h % self.dim] += 1.0 if (h >> 33) & 1 else -1.0
        return v

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return _normalise(np.stack([self._vec(t) for t in texts])) if texts else np.zeros((0, self.dim), np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return _normalise(self._vec(text)[None, :])[0]


def build_embedder(settings: Settings) -> Embedder:
    if settings.embedding_provider == "hash":
        return HashEmbedder(settings.embedding_dim)
    return FastEmbedEmbedder(settings.embedding_model, settings.embedding_dim)
