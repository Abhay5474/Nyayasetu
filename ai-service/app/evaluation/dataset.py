"""Labelled evaluation questions.

Each line of `eval/questions.jsonl` is one JSON object:

* `question`, `lang` (en|mr), `category`, `difficulty` (direct|colloquial)
* `relevant` - knowledge-base ids (the `kb_id` of a chunk) that contain the answer. A retrieval counts as a hit if ANY of them
  is returned; they were chosen by reading the source text, not by looking at what the retriever returns.
* `facts` - for answer scoring: a list of groups; every group must be satisfied by one of its alternative strings
  (e.g. ["30 days", "thirty days", "३० दिवस"]).
* `answerable` - false for questions the knowledge base cannot answer (the assistant should say so).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "eval" / "questions.jsonl"


@dataclass(frozen=True)
class Question:
    id: str
    lang: str
    category: str
    difficulty: str
    question: str
    relevant: tuple[str, ...]
    facts: tuple[tuple[str, ...], ...] = ()
    answerable: bool = True


def load_questions(path: Path = DEFAULT_PATH) -> list[Question]:
    questions = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            questions.append(Question(
                id=d["id"], lang=d["lang"], category=d["category"], difficulty=d.get("difficulty", "direct"),
                question=d["question"], relevant=tuple(d.get("relevant", [])),
                facts=tuple(tuple(g) for g in d.get("facts", [])), answerable=d.get("answerable", True),
            ))
        except (KeyError, ValueError) as exc:
            raise ValueError(f"{path}:{n}: bad question line: {exc!r}") from exc
    return questions


def validate(questions: list[Question], kb_status: dict[str, str]) -> list[str]:
    """Return problems: duplicate ids, labels that point at ids missing from / not in force in the knowledge base."""
    problems, seen = [], set()
    for q in questions:
        if q.id in seen:
            problems.append(f"{q.id}: duplicate id")
        seen.add(q.id)
        if q.answerable and not q.relevant:
            problems.append(f"{q.id}: answerable question without relevant ids")
        for kb_id in q.relevant:
            if kb_id not in kb_status:
                problems.append(f"{q.id}: unknown kb id {kb_id}")
            elif kb_status[kb_id] != "in_force":
                problems.append(f"{q.id}: {kb_id} is {kb_status[kb_id]}, not in force")
    return problems
