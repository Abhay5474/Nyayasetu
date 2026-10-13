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


def _numbered(entries):
    return [e for e in entries if e.section_ref and e.section_ref.split()[-1].isdigit()]


def test_manifest_sources_parse_to_the_expected_provisions(settings, manifest):
    expected = {"mh-rti-rules-2026-07-en": 5, "mh-rti-rules-2026-07-mr": 5, "mh-rti-rules-2026-06-en": 27,
                "mh-rti-rules-2026-06-mr": 27, "mh-rti-rules-2005": 5, "consumer-protection-act-2019": 107,
                "rti-act-2005-en": 31, "rti-fee-rules-2005": 5}
    for sid, n in expected.items():
        entries = entries_from_source(manifest[sid], KB, settings)
        assert len(_numbered(entries)) == n, sid
        assert all(e.source_type == manifest[sid].get("source_type", "official_pdf") and e.version_date for e in entries)


def test_supersession_chain_is_recorded(manifest):
    status = {sid: s["status"] for sid, s in manifest.items()}
    assert status["mh-rti-rules-2026-07-en"] == status["mh-rti-rules-2026-07-mr"] == "in_force"
    assert status["mh-rti-rules-2026-06-en"] == status["mh-rti-rules-2026-06-mr"] == status["mh-rti-rules-2005"] == "superseded"


def test_july_2026_rules_are_the_current_text(settings, manifest):
    en = {e.section_ref: e for e in entries_from_source(manifest["mh-rti-rules-2026-07-en"], KB, settings)}
    assert "rupees ten" in en["Rule 3"].text
    assert "rupees two for each page" in en["Rule 4"].text
    assert "thirty days" in en["Rule 5"].text and "ninety days" in en["Rule 5"].text and "rupees twenty" in en["Rule 5"].text
    mr = {e.section_ref: e for e in entries_from_source(manifest["mh-rti-rules-2026-07-mr"], KB, settings)}
    assert "रुपये दहा" in mr["नियम 3"].text and "तीस दिवसांच्या" in mr["नियम 5"].text
    june = {e.section_ref: e for e in entries_from_source(manifest["mh-rti-rules-2026-06-en"], KB, settings)}
    assert "rupees thirty" in june["Rule 3"].text  # the superseded text differs: kept for history only


def test_consumer_protection_act_sections(settings, manifest):
    secs = {e.section_ref: e for e in entries_from_source(manifest["consumer-protection-act-2019"], KB, settings)}
    assert "two years from the date on which the cause of action" in secs["Section 69"].text
    assert secs["Section 34"].text.lstrip().startswith("34.") and "District Commission" in secs["Section 34"].text
    assert secs["Section 107"].text.rstrip().find("repealed") != -1
    assert manifest["consumer-protection-act-2019"]["notes"]


def test_fee_question_returns_current_rules_never_superseded_ones(container):
    hits = container.retriever.retrieve("What is the application fee for an RTI request in Maharashtra and the fee per page?", top_k=8)
    ids = [h.chunk.kb_id for h in hits]
    assert any(i.startswith("mh-rti-rules-2026-07") for i in ids)
    assert not any(i.startswith(("mh-rti-rules-2026-06", "mh-rti-rules-2005")) for i in ids)
    assert all(h.chunk.status == "in_force" for h in hits)


def test_limitation_question_finds_consumer_act_section_69(container):
    ids = [h.chunk.kb_id for h in container.retriever.retrieve("within how many years must a consumer complaint be filed limitation period", top_k=5)]
    assert "consumer-protection-act-2019-s69" in ids


def test_provenance_reaches_the_source_object(container):
    from app.llm.simplifier import hits_to_sources, source_header

    hits = container.retriever.retrieve("fee for providing information rupees two for each page copied", top_k=3)
    src = hits_to_sources(hits)[0]
    official = next(s for s in hits_to_sources(hits) if s.source_type == "official_pdf")
    assert official.version_date == "2026-07-07" and official.gazette_ref and official.verified_at is None
    assert "official text, current as of 2026-07-07" in source_header(official)
    assert src.status == "in_force"


def test_seed_summaries_are_labelled_unverified(container):
    from app.llm.simplifier import hits_to_sources, source_header

    hits = container.retriever.retrieve("cheque dishonoured notice complaint magistrate section 138", top_k=3)
    seeds = [s for s in hits_to_sources(hits) if s.source_type == "seed_summary"]
    assert seeds and all("unverified summary" in source_header(s) for s in seeds)


def test_notes_reach_the_prompt_header(container):
    from app.llm.simplifier import hits_to_sources, source_header

    hits = container.retriever.retrieve("consumer complaint District Commission jurisdiction value of goods one crore rupees", top_k=6)
    cp = next(s for s in hits_to_sources(hits) if s.kb_id.startswith("consumer-protection-act-2019"))
    assert "NOTE:" in source_header(cp) and "Rules, 2021" in source_header(cp)


def test_english_rti_act_reprint_is_labelled_and_in_order(settings, manifest):
    from app.llm.simplifier import source_header
    from app.schemas import Source

    entries = entries_from_source(manifest["rti-act-2005-en"], KB, settings)
    secs = {e.section_ref: e for e in entries}
    assert [e.section_ref for e in entries] == [f"Section {i}" for i in range(1, 32)]
    assert all(e.source_type == "official_reprint" and e.verified_at is None for e in entries)
    assert "thirty days" in secs["Section 19"].text and "two hundred and fifty rupees" in secs["Section 20"].text
    assert "thirty days" in secs["Section 7"].text and "forty-eight hours" in secs["Section 7"].text
    assert "Amendment) Act, 2019" in secs["Section 13"].notes  # known staleness is carried with the text
    e = secs["Section 6"]
    s = Source(source_id="S1", kb_id=e.id, kind=e.kind, title=e.title, citation=e.citation, jurisdiction=e.jurisdiction,
               snippet=e.text, score=1, status=e.status, source_type=e.source_type, version_date=e.version_date, notes=e.notes)
    assert "government reprint of the official text" in source_header(s) and "NOTE:" in source_header(s)


def test_second_schedule_is_kept_whole(settings, manifest):
    (sched,) = entries_from_source(manifest["rti-act-2005-en-sched2"], KB, settings)
    assert "Intelligence Bureau" in sched.text and sched.section_ref == "Second Schedule"


def test_central_fee_rules_carry_the_amended_inspection_fee(settings, manifest):
    rules = {e.section_ref: e for e in entries_from_source(manifest["rti-fee-rules-2005"], KB, settings)}
    assert "rupees ten" in rules["Rule 3"].text and "rupees two for each page" in rules["Rule 4"].text
    assert "Maharashtra" in rules["Rule 4"].notes and "G.S.R. 649(E)" in rules["Rule 4"].notes
    (amend,) = entries_from_source(manifest["rti-fee-rules-2005-amend"], KB, settings)
    assert "for each subsequent hour" in amend.text and "Indian Postal Order" in amend.text


def test_act_question_retrieves_the_english_reprint_not_a_seed_summary(container):
    ids = [h.chunk.kb_id for h in container.retriever.retrieve("which organisations are exempt from the RTI Act second schedule intelligence bureau", top_k=4)]
    assert "rti-act-2005-en-sched2" in ids
    assert not any(i.startswith("rti-act-s") and not i.startswith("rti-act-2005") for i in ids)
