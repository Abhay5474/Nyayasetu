"""Metrics and small statistics helpers (no external dependencies)."""
from __future__ import annotations

import random
import re
from statistics import mean

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def to_ascii_digits(text: str) -> str:
    return text.translate(_DEVANAGARI_DIGITS)


def first_rank(ranked_ids: list[str], relevant: set[str]) -> int | None:
    """1-based rank of the first relevant id, or None."""
    for rank, kb_id in enumerate(ranked_ids, start=1):
        if kb_id in relevant:
            return rank
    return None


def hit_at(rank: int | None, k: int) -> float:
    return 1.0 if rank is not None and rank <= k else 0.0


def reciprocal_rank(rank: int | None, depth: int) -> float:
    return 1.0 / rank if rank is not None and rank <= depth else 0.0


def dedupe_ids(kb_ids: list[str]) -> list[str]:
    """Several chunks can belong to one provision; rank provisions, not chunks."""
    seen, out = set(), []
    for kb_id in kb_ids:
        if kb_id not in seen:
            seen.add(kb_id)
            out.append(kb_id)
    return out


def bootstrap_ci(values: list[float], samples: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% percentile bootstrap interval of the mean (resampling questions)."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    means = sorted(mean(rng.choices(values, k=n)) for _ in range(samples))
    return means[int(0.025 * samples)], means[int(0.975 * samples) - 1]


# ----------------------------------------------------------------------------- answer scoring
def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", to_ascii_digits(text)).lower()


def fact_recall(answer: str, facts: tuple[tuple[str, ...], ...]) -> float | None:
    """Share of fact groups present in the answer (None when the question has no facts)."""
    if not facts:
        return None
    a = _norm(answer)
    return sum(any(_norm(alt) in a for alt in group) for group in facts) / len(facts)


_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


_LIST_MARKER = re.compile(r"(?m)^\s*\d+[.)]\s")


def numbers_in(text: str) -> set[str]:
    text = _LIST_MARKER.sub("", to_ascii_digits(text))  # "1. First step" is numbering, not a claim
    return {m.rstrip(",").replace(",", "") for m in _NUMBER.findall(text)}


def numbers_grounded(answer: str, evidence: str) -> bool:
    """True when every number the answer states also appears in the evidence it cites (or the question)."""
    return numbers_in(answer) <= numbers_in(evidence)
