from types import SimpleNamespace

from app.evaluation import metrics as M
from app.evaluation import runner
from app.evaluation.dataset import load_questions, validate
from app.rag.ingest import collect_entries
from app.rag.reranker import LexicalReranker


def test_question_set_is_consistent_with_the_knowledge_base(settings):
    questions = load_questions()
    status = {e.id: e.status for e in collect_entries(settings.kb_dir)}
    assert validate(questions, status) == []
    assert {q.lang for q in questions} == {"en", "mr"}
    assert sum(q.lang == "mr" for q in questions if q.answerable) >= 15
    assert any(not q.answerable for q in questions)  # out-of-scope questions exist for the abstention check


def test_validate_reports_bad_labels():
    from app.evaluation.dataset import Question

    qs = [Question("a", "en", "x", "direct", "q", ("missing",)), Question("a", "en", "x", "direct", "q", ("old",)),
          Question("b", "en", "x", "direct", "q", ())]
    problems = validate(qs, {"old": "superseded"})
    assert any("unknown kb id missing" in p for p in problems)
    assert any("not in force" in p for p in problems)
    assert any("duplicate id" in p for p in problems)
    assert any("without relevant ids" in p for p in problems)


def test_rank_metrics():
    ids = M.dedupe_ids(["a", "a", "b", "c", "b"])
    assert ids == ["a", "b", "c"]
    rank = M.first_rank(ids, {"c", "z"})
    assert rank == 3 and M.hit_at(rank, 3) == 1 and M.hit_at(rank, 2) == 0
    assert abs(M.reciprocal_rank(rank, 10) - 1 / 3) < 1e-9 and M.reciprocal_rank(None, 10) == 0
    lo, hi = M.bootstrap_ci([1, 0, 1, 1, 0, 1, 1, 1])
    assert 0 <= lo <= 0.75 <= hi <= 1


def test_fact_and_number_checks_handle_devanagari_digits():
    facts = (("30 days", "thirty days"), ("appeal",))
    assert M.fact_recall("You may file an appeal within ३० days.", facts) == 1.0  # Devanagari digits normalised
    assert M.fact_recall("It takes 30 days", facts) == 0.5  # one of two fact groups present
    assert M.fact_recall("File an appeal within thirty days", facts) == 1.0
    assert M.fact_recall("No idea", facts) == 0.0 and M.fact_recall("x", ()) is None
    assert M.numbers_grounded("पहिले अपील ३० दिवसांत", "within 30 days of receipt")
    assert not M.numbers_grounded("Pay Rs 500", "the fee is Rs 10")
    assert M.numbers_grounded("1. First step\n2. Second step within 30 days", "30 days")  # list numbering is not a claim


def test_retrieval_report_runs_all_variants(container):
    questions = [q for q in load_questions() if q.id in {"q04", "q06", "q07", "m01", "u01"}]
    variants = runner.build_variants(container.retriever, {"lexical": LexicalReranker()})
    report = runner.retrieval_report(questions, variants)
    assert set(report["overall"]) == {"vector only", "keyword only (FTS)", "hybrid (RRF)", "hybrid + rerank (lexical)"}
    for s in report["overall"].values():
        assert s["n"] == 4  # the out-of-scope question is not scored for retrieval
        assert 0 <= s["hit@1"] <= s["hit@3"] <= s["hit@5"] <= 1 and s["stale_rate"] == 0
    md = runner.render_retrieval_markdown(report, {"date": "d", "embedder": "e", "chunks": 1, "questions": 4, "skipped": 1})
    assert "| hybrid (RRF) |" in md and "By language" in md


def test_answer_report_scores_facts_citations_and_abstention():
    qs = [q for q in load_questions() if q.id in {"q04", "u01"}]

    def fake(q):
        if q.id == "q04":
            src = SimpleNamespace(kb_id="rti-act-2005-en-s19", snippet="appeal within thirty days (30 days)")
            return SimpleNamespace(answer="File the first appeal within 30 days.", answerable=True, sources=[src])
        return SimpleNamespace(answer="Sorry, I cannot help with that.", answerable=False, sources=[])

    report = runner.answer_report(qs, fake)
    s = report["summary"]
    assert s["fact_recall"] == 1.0 and s["citation_hit"] == 1.0 and s["citation_precision"] == 1.0
    assert s["numbers_grounded"] == 1.0 and s["correct_abstention"] == 1.0
    assert "Answer evaluation" in runner.render_answers_markdown(report, {"date": "d", "model": "m"})
