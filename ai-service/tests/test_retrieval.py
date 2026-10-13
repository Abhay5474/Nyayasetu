from app.rag.ingest import ingest_entries
from app.rag.retriever import rrf_fuse
from app.rag.store import Chunk, Hit
from app.schemas import KbEntry


def top_ids(container, query, k=3):
    return [h.chunk.kb_id for h in container.retriever.retrieve(query, top_k=k)]


def test_kb_loaded(container):
    assert container.store.count() >= 28


def test_english_questions_hit_right_provisions(container):
    assert "rti-act-s19" in top_ids(container, "How many days do I have to file a first appeal after the PIO rejected my RTI application?")
    assert "rti-act-s20" in top_ids(container, "penalty of Rs 250 per day on the Public Information Officer for delay")
    assert "ni-act-138-142" in top_ids(container, "cheque dishonoured demand notice within 30 days complaint magistrate")


def test_marathi_queries_hit_marathi_entries(container):
    ids = top_ids(container, "प्रथम अपील किती दिवसांत करावे जन माहिती अधिकारी", k=4)
    assert "rti-marathi-s19-s20" in ids
    assert "ni-act-marathi" in top_ids(container, "धनादेश परत आल्यास नोटीस किती दिवसांत पाठवावी", k=3)


def test_multi_query_retrieval_merges_results(container):
    ids = top_ids(container, ["Section 8(1)(j) personal information exemption", "consumer complaint limitation two years"], k=6)
    assert "rti-act-s8" in ids and "cpa-2019-limitation-jurisdiction" in ids


def test_rrf_prefers_documents_ranked_well_in_both_lists():
    def ch(i):
        return Chunk(i, i, "act", i, i, "India", "en", i)

    a, b, c = ch("a"), ch("b"), ch("c")
    fused = rrf_fuse([[Hit(a, 1), Hit(b, .9), Hit(c, .8)], [Hit(c, 9), Hit(b, 8)]])
    assert {h.chunk.id for h in fused[:2]} == {"b", "c"} and fused[-1].chunk.id == "a"


def test_ingest_is_idempotent_and_updates_changed_entries(container):
    entry = KbEntry(id="tmp-entry", title="Temp", citation="Temp Act - Section 1", text="Original text about zebra crossings.")
    assert ingest_entries([entry], container.store, container.embedder) == (1, 1)
    assert ingest_entries([entry], container.store, container.embedder) == (1, 0)
    entry.text = "Changed text about giraffe feeding."
    assert ingest_entries([entry], container.store, container.embedder) == (1, 1)
