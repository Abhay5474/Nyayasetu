"""CLI.

    python -m app.evaluation retrieval [--rerankers lexical,cross-encoder]
    python -m app.evaluation answers   [--limit N]            (needs a real LLM: LLM_PROVIDER=anthropic|openai|ollama)

Uses the same settings/environment as the service (EMBEDDING_PROVIDER, RERANKER, DATABASE_URL, VECTOR_STORE ...), so run it with
the configuration you want to measure. Results (Markdown + JSON) are written to `eval/results/`.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from app.config import get_settings
from app.container import build_container
from app.evaluation import runner
from app.evaluation.dataset import DEFAULT_PATH, load_questions, validate
from app.rag.ingest import collect_entries, ingest_path
from app.rag.reranker import CrossEncoderReranker, LexicalReranker, NoopReranker

log = logging.getLogger("evaluation")
RESULTS = DEFAULT_PATH.parent / "results"


def _rerankers(names: str, settings) -> dict:
    out = {}
    for name in (n.strip() for n in names.split(",") if n.strip()):
        if name == "lexical":
            out[name] = LexicalReranker()
        elif name == "none":
            out[name] = NoopReranker()
        elif name == "cross-encoder":
            try:
                out[settings.reranker_model.split("/")[-1]] = CrossEncoderReranker(settings.reranker_model)
            except Exception as exc:  # say so instead of silently reporting lexical numbers under the model's name
                log.error("Cross-encoder %s unavailable (%s) - skipped", settings.reranker_model, exc)
        else:
            raise SystemExit(f"unknown reranker {name!r} (lexical | cross-encoder | none)")
    return out


def _write(stem: str, markdown: str, data: dict) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{stem}.md").write_text(markdown, encoding="utf-8")
    (RESULTS / f"{stem}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2, default=list), encoding="utf-8")
    print(markdown)
    print(f"[written to {RESULTS / (stem + '.md')} and .json]")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.evaluation")
    ap.add_argument("mode", choices=["retrieval", "answers"])
    ap.add_argument("--questions", type=Path, default=DEFAULT_PATH)
    ap.add_argument("--rerankers", default="lexical,cross-encoder",
                    help="comma list for the retrieval ablation. 'lexical' alone is fast; 'cross-encoder' loads a large model and "
                         "takes minutes on a laptop CPU")
    ap.add_argument("--limit", type=int, default=0, help="answers: only the first N questions (cost control)")
    ap.add_argument("--tag", default="", help="suffix for the result file names")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    questions = load_questions(args.questions)
    status = {e.id: e.status for e in collect_entries(settings.kb_dir)}
    problems = validate(questions, status)
    if problems:
        print("Question set does not match the knowledge base:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 2

    container = build_container(settings)
    ingest_path(settings.kb_dir, container.store, container.embedder)  # idempotent; fills the in-memory store
    embedder = type(container.embedder).__name__ + (f" ({settings.embedding_model})" if settings.embedding_provider == "fastembed" else "")
    stem = f"{args.mode}-{runner.now()}{('-' + args.tag) if args.tag else ''}"

    if args.mode == "retrieval":
        variants = runner.build_variants(container.retriever, _rerankers(args.rerankers, settings))
        per_variant: dict = {}
        marks = {"last": 0.0}

        def on_start(name: str) -> None:
            print(f"\n[{len(per_variant) + 1}/{len(variants)}] {name}", flush=True)

        def progress(name: str, i: int, n: int, secs: float) -> None:
            if i == n or time.time() - marks["last"] > 10:  # at most one line every 10 s, plus the last question
                marks["last"] = time.time()
                eta = secs / i * (n - i)
                print(f"    {i}/{n} questions · {secs:.0f}s elapsed · about {eta:.0f}s left", flush=True)

        partial = False
        try:
            runner.evaluate_all(questions, variants, per_variant, on_start, progress)
        except KeyboardInterrupt:
            partial = True
            print("\nStopped: writing the methods that finished.", flush=True)
        report = runner.build_report(per_variant)
        meta = {"date": runner.now(), "embedder": embedder, "chunks": container.store.count(), "partial": partial,
                "questions": sum(q.answerable for q in questions), "skipped": sum(not q.answerable for q in questions)}
        _write(stem + ("-partial" if partial else ""), runner.render_retrieval_markdown(report, meta), {"meta": meta, **report})
        return 0

    if container.chat is None or settings.llm_provider == "mock":
        print("Answer evaluation needs a real LLM: set LLM_PROVIDER (anthropic | openai | ollama) and its key/model.", file=sys.stderr)
        return 2
    subset = questions[: args.limit] if args.limit else questions
    chat = container.chat
    report = runner.answer_report(subset, lambda q: chat.answer(runner.PLACEHOLDER_DOC, q.question, q.lang, []))
    meta = {"date": runner.now(), "model": settings.llm_model, "embedder": embedder}
    _write(stem, runner.render_answers_markdown(report, meta), {"meta": meta, **report})
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
