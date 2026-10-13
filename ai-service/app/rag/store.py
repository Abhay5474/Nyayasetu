"""Knowledge-base storage: PostgreSQL + pgvector (production) and an in-memory twin (tests)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from app.processing.text import tokenize

log = logging.getLogger(__name__)


@dataclass
class Chunk:
    id: str  # "<kb_id>#<n>"
    kb_id: str
    kind: str
    title: str
    citation: str
    jurisdiction: str
    language: str
    text: str
    content_hash: str = ""
    embedding: np.ndarray | None = None
    status: str = "in_force"
    meta: dict = field(default_factory=dict)


@dataclass
class Hit:
    chunk: Chunk
    score: float  # similarity (vector) or rank score (keyword); only comparable within one list


class KnowledgeStore(Protocol):
    def setup(self) -> None: ...

    def existing_hashes(self) -> dict[str, str]: ...

    def upsert(self, chunks: list[Chunk]) -> None: ...

    def vector_search(self, query_vec: np.ndarray, k: int) -> list[Hit]: ...

    def keyword_search(self, query: str, k: int) -> list[Hit]: ...

    def count(self) -> int: ...

    def prune(self, origin: str, keep_kb_ids: set[str]) -> int: ...


ACTIVE = lambda c: c.status not in ("superseded", "repealed")  # noqa: E731

_tokens = tokenize


class InMemoryStore:
    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}

    def setup(self) -> None:
        pass

    def existing_hashes(self) -> dict[str, str]:
        return {c.id: c.content_hash for c in self._chunks.values()}

    def upsert(self, chunks: list[Chunk]) -> None:
        for c in chunks:
            self._chunks[c.id] = c

    def vector_search(self, query_vec: np.ndarray, k: int) -> list[Hit]:
        scored = [Hit(c, float(np.dot(c.embedding, query_vec))) for c in self._chunks.values() if c.embedding is not None and ACTIVE(c)]
        return sorted(scored, key=lambda h: h.score, reverse=True)[:k]

    def keyword_search(self, query: str, k: int) -> list[Hit]:
        q = set(_tokens(query))
        if not q:
            return []
        df: dict[str, int] = {}
        docs = {cid: _tokens(c.title + " " + c.citation + " " + c.text) for cid, c in self._chunks.items() if ACTIVE(c)}
        for toks in docs.values():
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        n = max(len(docs), 1)
        hits = []
        for cid, toks in docs.items():
            score = sum(
                np.log(1 + n / df[t]) * (toks.count(t) / (toks.count(t) + 1.5)) for t in q if t in df and t in toks
            )
            if score > 0:
                hits.append(Hit(self._chunks[cid], float(score)))
        return sorted(hits, key=lambda h: h.score, reverse=True)[:k]

    def count(self) -> int:
        return len(self._chunks)

    def prune(self, origin: str, keep_kb_ids: set[str]) -> int:
        gone = [cid for cid, c in self._chunks.items() if c.meta.get("origin", "files") == origin and c.kb_id not in keep_kb_ids]
        for cid in gone:
            del self._chunks[cid]
        return len(gone)


class PgVectorStore:
    """Chunks live in `kb.kb_chunks`; cosine HNSW index for dense search, GIN tsvector for keywords.

    A dedicated schema keeps the knowledge base apart from the backend's Flyway-managed `public`
    schema, so start-up order of the two services does not matter.
    """

    TABLE = "kb.kb_chunks"

    def __init__(self, database_url: str, dim: int):
        from psycopg_pool import ConnectionPool

        self.dim = dim
        self.pool = ConnectionPool(database_url, min_size=1, max_size=5, open=False, configure=self._configure)

    @staticmethod
    def _configure(conn) -> None:
        from pgvector.psycopg import register_vector

        register_vector(conn)

    def setup(self) -> None:
        from pgvector.psycopg import register_vector
        import psycopg

        # The extension must exist before the pool connections can register the vector type.
        with psycopg.connect(self.pool.conninfo, autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute("CREATE SCHEMA IF NOT EXISTS kb")
            register_vector(conn)
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE} (
                    id            TEXT PRIMARY KEY,
                    kb_id         TEXT NOT NULL,
                    kind          TEXT NOT NULL,
                    title         TEXT NOT NULL,
                    citation      TEXT NOT NULL,
                    jurisdiction  TEXT NOT NULL DEFAULT 'India',
                    language      TEXT NOT NULL DEFAULT 'en',
                    text          TEXT NOT NULL,
                    content_hash  TEXT NOT NULL,
                    status        TEXT NOT NULL DEFAULT 'in_force',
                    meta          JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding     vector({self.dim}) NOT NULL,
                    tsv           tsvector GENERATED ALWAYS AS
                                  (to_tsvector('simple', title || ' ' || citation || ' ' || text)) STORED,
                    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
                )"""
            )
            # upgrade tables created before provenance existed
            conn.execute(f"ALTER TABLE {self.TABLE} ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'in_force'")
            conn.execute(f"ALTER TABLE {self.TABLE} ADD COLUMN IF NOT EXISTS meta JSONB NOT NULL DEFAULT '{{}}'::jsonb")
            conn.execute(f"CREATE INDEX IF NOT EXISTS kb_chunks_tsv_idx ON {self.TABLE} USING GIN (tsv)")
            conn.execute(
                f"CREATE INDEX IF NOT EXISTS kb_chunks_embedding_idx "
                f"ON {self.TABLE} USING hnsw (embedding vector_cosine_ops)"
            )
        self.pool.open(wait=True)

    @staticmethod
    def _row_to_chunk(row) -> Chunk:
        return Chunk(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], status=row[8], meta=row[9] or {})

    _COLS = "id, kb_id, kind, title, citation, jurisdiction, language, text, status, meta"

    def existing_hashes(self) -> dict[str, str]:
        with self.pool.connection() as conn:
            return dict(conn.execute(f"SELECT id, content_hash FROM {self.TABLE}").fetchall())

    def upsert(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        sql = f"""
            INSERT INTO {self.TABLE} (id, kb_id, kind, title, citation, jurisdiction, language, text, content_hash, embedding, status, meta)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (id) DO UPDATE SET kb_id=EXCLUDED.kb_id, kind=EXCLUDED.kind, title=EXCLUDED.title,
              citation=EXCLUDED.citation, jurisdiction=EXCLUDED.jurisdiction, language=EXCLUDED.language,
              text=EXCLUDED.text, content_hash=EXCLUDED.content_hash, embedding=EXCLUDED.embedding,
              status=EXCLUDED.status, meta=EXCLUDED.meta, updated_at=now()"""
        from psycopg.types.json import Jsonb

        rows = [
            (c.id, c.kb_id, c.kind, c.title, c.citation, c.jurisdiction, c.language, c.text, c.content_hash, c.embedding,
             c.status, Jsonb(c.meta))
            for c in chunks
        ]
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, rows)

    def vector_search(self, query_vec: np.ndarray, k: int) -> list[Hit]:
        sql = f"SELECT {self._COLS}, 1 - (embedding <=> %s) AS sim FROM {self.TABLE} WHERE status NOT IN ('superseded','repealed') ORDER BY embedding <=> %s LIMIT %s"
        with self.pool.connection() as conn:
            rows = conn.execute(sql, (query_vec, query_vec, k)).fetchall()
        return [Hit(self._row_to_chunk(r), float(r[10])) for r in rows]

    def keyword_search(self, query: str, k: int) -> list[Hit]:
        # OR-semantics over query terms: legal queries are long, AND-ing every word matches nothing.
        terms = list(dict.fromkeys(_tokens(query)))[:40]
        if not terms:
            return []
        tsq = " | ".join(terms)
        sql = f"""
            SELECT {self._COLS}, ts_rank_cd(tsv, q) AS rank
            FROM {self.TABLE}, to_tsquery('simple', %s) q
            WHERE tsv @@ q AND status NOT IN ('superseded','repealed') ORDER BY rank DESC LIMIT %s"""
        with self.pool.connection() as conn:
            rows = conn.execute(sql, (tsq, k)).fetchall()
        return [Hit(self._row_to_chunk(r), float(r[10])) for r in rows]

    def prune(self, origin: str, keep_kb_ids: set[str]) -> int:
        with self.pool.connection() as conn:
            cur = conn.execute(
                f"DELETE FROM {self.TABLE} WHERE COALESCE(meta->>'origin', 'files') = %s AND NOT (kb_id = ANY(%s))", (origin, list(keep_kb_ids))
            )
            return cur.rowcount

    def count(self) -> int:
        with self.pool.connection() as conn:
            return conn.execute(f"SELECT count(*) FROM {self.TABLE}").fetchone()[0]

    def ping(self) -> bool:
        try:
            with self.pool.connection() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
