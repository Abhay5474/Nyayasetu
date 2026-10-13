import pathlib

import pytest

from app.rag.legal_parser import split_numbered_provisions, split_paragraph_groups
from app.rag.sources import entries_from_source, load_manifest

KB = pathlib.Path(__file__).resolve().parent.parent / "knowledge_base"


def test_numbered_parser_splits_provisions_in_order_and_ignores_noise():
    text = """Preamble text.
1. Short title.- (1) These rules may be called X.
2. Definitions - (1) In these rules,
(a) "Act" means the Act;
3. Fees.- Fee is rupees thirty.
7. A stray numbered line that is not the next provision.
4. Appeal.- Within 30 days.
ANNEXURE "A" Form of application
(1) Name -"""
    parsed = split_numbered_provisions(text)
    assert [p.number for p in parsed.provisions] == [1, 2, 3, 4]
    assert parsed.provisions[2].text.startswith("Fees.") and "rupees thirty" in parsed.provisions[2].text
    assert "stray numbered line" in parsed.provisions[2].text  # kept inside the provision, not a new one
    assert parsed.annexures.startswith("ANNEXURE")


def test_parser_handles_devanagari_numbers_and_gazette_headers():
    text = "१. संक्षिप्त नाव.- (१) हे नियम.\n12 महाराष्ट्र शासन राजपत्र असाधारण भाग चार-अ, जून १२, २०२६\n२. व्याख्या.- (१) या नियमांत,\n"
    parsed = split_numbered_provisions(text)
    assert [p.number for p in parsed.provisions] == [1, 2]
    assert "राजपत्र" not in parsed.provisions[0].text


def test_paragraph_groups_respect_size():
    groups = split_paragraph_groups("\n\n".join(f"Paragraph {i} " + "x" * 300 for i in range(10)), max_chars=1000)
    assert all(len(g) <= 1000 for g in groups) and len(groups) >= 3


@pytest.fixture(scope="module")
def manifest():
    return {s["id"]: s for s in load_manifest(KB)}


def test_manifest_sources_parse_to_the_expected_provisions(settings, manifest):
    for sid, n in [("mh-rti-rules-2026-en", 27), ("mh-rti-rules-2026-mr", 27), ("mh-rti-rules-2005", 5)]:
        entries = entries_from_source(manifest[sid], KB, settings)
        numbered = [e for e in entries if e.section_ref and e.section_ref.split()[-1].isdigit()]
        assert len(numbered) == n, sid
        assert all(e.source_type == "official_pdf" and e.version_date for e in entries)
    assert entries_from_source(manifest["mh-rti-rules-2005"], KB, settings)[0].status == "superseded"


def test_2026_fee_rules_are_the_current_text(settings, manifest):
    entries = {e.section_ref: e for e in entries_from_source(manifest["mh-rti-rules-2026-en"], KB, settings)}
    assert "rupees thirty" in entries["Rule 3"].text
    assert "rupees five for each page" in entries["Rule 4"].text
    assert "rupees hundred" in entries["Rule 16"].text  # second-appeal fee


def test_fee_question_returns_2026_rules_never_the_superseded_2005_text(container):
    hits = container.retriever.retrieve("What is the application fee for an RTI request in Maharashtra and the fee per page?", top_k=8)
    ids = [h.chunk.kb_id for h in hits]
    assert any(i.startswith("mh-rti-rules-2026") for i in ids)
    assert not any(i.startswith("mh-rti-rules-2005") for i in ids)
    assert all(h.chunk.status == "in_force" for h in hits)


def test_provenance_reaches_the_source_object(container):
    from app.llm.simplifier import hits_to_sources, source_header

    hits = container.retriever.retrieve("fee for providing information rupees per page A-4", top_k=3)
    src = hits_to_sources(hits)[0]
    official = next(s for s in hits_to_sources(hits) if s.source_type == "official_pdf")
    assert official.version_date == "2026-06-12" and official.gazette_ref and official.verified_at is None
    assert "official text, current as of 2026-06-12" in source_header(official)
    assert src.status == "in_force"


def test_seed_summaries_are_labelled_unverified(container):
    from app.llm.simplifier import hits_to_sources, source_header

    hits = container.retriever.retrieve("cheque dishonoured notice complaint magistrate section 138", top_k=3)
    seeds = [s for s in hits_to_sources(hits) if s.source_type == "seed_summary"]
    assert seeds and all("unverified summary" in source_header(s) for s in seeds)
