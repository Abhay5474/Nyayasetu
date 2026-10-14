"""Run the retrieval and answer evaluations and render the results."""
from __future__ import annotations

import datetime as dt
import time
from functools import lru_cache
from dataclasses import dataclass
from statistics import mean
from typing import Callable

from app.evaluation import metrics as M
from app.evaluation.dataset import Question
from app.rag.reranker import Reranker
from app.rag.retriever import HybridRetriever, rrf_fuse
from app.rag.store import Hit

DEPTH = 10  # ranks scored per question; Hit@k is reported for k in KS
KS = (1, 3, 5)
CANDIDATES = 20

Ranker = Callable[[str], list[Hit]]


def build_variants(retriever: HybridRetriever, rerankers: dict[str, Reranker]) -> dict[str, Ranker]:
    """The ablation: each variant adds one component to the previous one."""
    store, embedder = retriever.store, retriever.embedder

    @lru_cache(maxsize=None)  # the same question is searched by several variants: do the work once
    def vector(q: str) -> list[Hit]:
        return store.vector_search(embedder.embed_query(q), CANDIDATES)

    @lru_cache(maxsize=None)
    def keyword(q: str) -> list[Hit]:
        return store.keyword_search(q, CANDIDATES)

    @lru_cache(maxsize=None)
    def hybrid(q: str) -> list[Hit]:
        return rrf_fuse([r for r in (vector(q), keyword(q)) if r])

    variants: dict[str, Ranker] = {"vector only": vector, "keyword only (FTS)": keyword, "hybrid (RRF)": hybrid}
    for name, reranker in rerankers.items():
        def rerank(q: str, reranker=reranker) -> list[Hit]:
            return reranker.rerank(q, hybrid(q)[: retriever.cfg.rerank_candidates], DEPTH)

        variants[f"hybrid + rerank ({name})"] = rerank
    return variants


@dataclass
class QuestionResult:
    q: Question
    ranked: list[str]  # kb ids, best first, de-duplicated
    rank: int | None
    stale: bool  # any returned chunk that is superseded/repealed


def evaluate_ranker(ranker: Ranker, questions: list[Question], progress: Callable[[int, int, float], None] | None = None) -> list[QuestionResult]:
    results = []
    scored = [x for x in questions if x.answerable]
    started = time.time()
    for i, q in enumerate(scored, start=1):
        hits = ranker(q.question)
        ids = M.dedupe_ids([h.chunk.kb_id for h in hits])[:DEPTH]
        stale = any(h.chunk.status != "in_force" for h in hits)
        results.append(QuestionResult(q, ids, M.first_rank(ids, set(q.relevant)), stale))
        if progress:
            progress(i, len(scored), time.time() - started)
    return results


def summarise(results: list[QuestionResult]) -> dict:
    out: dict = {"n": len(results)}
    for k in KS:
        vals = [M.hit_at(r.rank, k) for r in results]
        out[f"hit@{k}"] = mean(vals) if vals else 0.0
    rr = [M.reciprocal_rank(r.rank, DEPTH) for r in results]
    out["mrr"] = mean(rr) if rr else 0.0
    out["mrr_ci"] = M.bootstrap_ci(rr)
    out["hit@3_ci"] = M.bootstrap_ci([M.hit_at(r.rank, 3) for r in results])
    out["stale_rate"] = mean(1.0 if r.stale else 0.0 for r in results) if results else 0.0
    return out


def evaluate_all(questions: list[Question], variants: dict[str, Ranker], per_variant: dict[str, list[QuestionResult]],
                 on_start: Callable[[str], None] | None = None,
                 progress: Callable[[str, int, int, float], None] | None = None) -> None:
    """Fill `per_variant` one variant at a time, so the caller still has the finished ones if the run is interrupted."""
    for name, ranker in variants.items():
        if on_start:
            on_start(name)
        per_variant[name] = evaluate_ranker(ranker, questions, (lambda i, n, t, name=name: progress(name, i, n, t)) if progress else None)


def build_report(per_variant: dict[str, list[QuestionResult]]) -> dict:
    report: dict = {"overall": {}, "by_lang": {}, "by_category": {}, "by_difficulty": {}, "misses": {}}
    for name, results in per_variant.items():
        report["overall"][name] = summarise(results)
        for key, attr in (("by_lang", "lang"), ("by_category", "category"), ("by_difficulty", "difficulty")):
            groups: dict[str, list[QuestionResult]] = {}
            for r in results:
                groups.setdefault(getattr(r.q, attr), []).append(r)
            report[key][name] = {g: summarise(rs) for g, rs in sorted(groups.items())}
        report["misses"][name] = [
            {"id": r.q.id, "question": r.q.question, "expected": list(r.q.relevant), "top3": r.ranked[:3], "rank": r.rank}
            for r in results if r.rank is None or r.rank > 3
        ]
    return report


def retrieval_report(questions: list[Question], variants: dict[str, Ranker]) -> dict:
    per_variant: dict[str, list[QuestionResult]] = {}
    evaluate_all(questions, variants, per_variant)
    return build_report(per_variant)


# ----------------------------------------------------------------------------- answers
PLACEHOLDER_DOC = "A user is asking a general legal question. No document has been uploaded for this question."


def answer_report(questions: list[Question], answer_fn: Callable[[Question], object]) -> dict:
    """`answer_fn(q)` returns an `app.schemas.ChatResponse`. Scores facts, citations, number grounding and abstention."""
    rows = []
    for q in questions:
        resp = answer_fn(q)
        cited = [s.kb_id for s in resp.sources]
        evidence = " ".join(s.snippet for s in resp.sources) + " " + q.question
        row = {
            "id": q.id, "lang": q.lang, "answerable": q.answerable, "answer": resp.answer, "answered": resp.answerable,
            "cited": cited, "fact_recall": M.fact_recall(resp.answer, q.facts),
            "cited_relevant": bool(set(cited) & set(q.relevant)) if q.answerable else None,
            "citation_precision": (len(set(cited) & set(q.relevant)) / len(set(cited))) if q.answerable and cited else None,
            "numbers_grounded": M.numbers_grounded(resp.answer, evidence),
        }
        rows.append(row)

    def avg(key: str, subset: list[dict]) -> float | None:
        vals = [float(r[key]) for r in subset if r[key] is not None]
        return mean(vals) if vals else None

    answerable = [r for r in rows if r["answerable"]]
    unanswerable = [r for r in rows if not r["answerable"]]
    summary = {
        "n_answerable": len(answerable),
        "answered_rate": mean(1.0 if r["answered"] else 0.0 for r in answerable) if answerable else None,
        "fact_recall": avg("fact_recall", answerable),
        "citation_hit": avg("cited_relevant", answerable),
        "citation_precision": avg("citation_precision", answerable),
        "numbers_grounded": avg("numbers_grounded", answerable),
        "n_unanswerable": len(unanswerable),
        "correct_abstention": mean(0.0 if r["answered"] else 1.0 for r in unanswerable) if unanswerable else None,
    }
    return {"summary": summary, "rows": rows}


# ----------------------------------------------------------------------------- rendering
def _pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def _row(name: str, s: dict) -> str:
    lo, hi = s["mrr_ci"]
    return (f"| {name} | {s['n']} | {_pct(s['hit@1'])} | {_pct(s['hit@3'])} | {_pct(s['hit@5'])} | "
            f"{s['mrr']:.3f} ({lo:.2f}–{hi:.2f}) | {_pct(s['stale_rate'])} |")


_HEAD = "| Method | n | Hit@1 | Hit@3 | Hit@5 | MRR (95% CI) | Superseded text returned |\n|---|---|---|---|---|---|---|"


def render_retrieval_markdown(report: dict, meta: dict) -> str:
    lines = [
        "# Retrieval evaluation", "",
        *(["> **Partial result: the run was stopped before every method finished.**", ""] if meta.get("partial") else []),
        f"*{meta['date']} · embedder `{meta['embedder']}` · knowledge base {meta['chunks']} chunks · {meta['questions']} labelled questions "
        f"(+{meta['skipped']} out-of-scope, not scored here)*", "",
        "Hit@k = a provision that contains the answer is among the top k results. MRR = mean reciprocal rank (depth 10). "
        "Gold labels were assigned by reading the source text.", "",
        "## Overall", "", _HEAD,
    ]
    lines += [_row(n, s) for n, s in report["overall"].items()]
    for key, title in (("by_lang", "By language"), ("by_category", "By topic"), ("by_difficulty", "By question style")):
        lines += ["", f"## {title}", "", _HEAD.replace("| Method |", "| Method / group |")]
        for name, groups in report[key].items():
            lines += [_row(f"{name} — **{g}**", s) for g, s in groups.items()]
    if not report["overall"]:
        return "# Retrieval evaluation\n\nNo method finished.\n"
    best = max(report["overall"], key=lambda n: report["overall"][n]["mrr"])
    lines += ["", f"## Misses of the best method ({best}): not in top 3", ""]
    misses = report["misses"][best]
    if not misses:
        lines.append("None.")
    for m in misses:
        got = ", ".join(m["top3"]) or "(nothing)"
        lines.append(f"* **{m['id']}** {m['question']}  \n  expected one of `{', '.join(m['expected'])}` · got `{got}` · rank {m['rank'] or '>10'}")
    return "\n".join(lines) + "\n"


def render_answers_markdown(report: dict, meta: dict) -> str:
    s = report["summary"]

    def f(x):
        return "n/a" if x is None else _pct(x)

    return "\n".join([
        "# Answer evaluation", "", f"*{meta['date']} · model `{meta['model']}` · {s['n_answerable']} answerable + {s['n_unanswerable']} out-of-scope questions*", "",
        "| Metric | Result |", "|---|---|",
        f"| Questions answered (not refused) | {f(s['answered_rate'])} |",
        f"| Required facts present (fact recall) | {f(s['fact_recall'])} |",
        f"| Cited a relevant provision | {f(s['citation_hit'])} |",
        f"| Citation precision | {f(s['citation_precision'])} |",
        f"| Every number in the answer appears in the cited text | {f(s['numbers_grounded'])} |",
        f"| Out-of-scope questions correctly declined | {f(s['correct_abstention'])} |", "",
        "Fact recall and number grounding are string checks: they flag likely errors but cannot confirm an answer is right. "
        "Read `answers.json` for the answers behind the numbers.", "",
    ])


def now() -> str:
    return dt.date.today().isoformat()
