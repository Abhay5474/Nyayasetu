import json

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.llm.simplifier import GenerationError, Simplifier, build_queries, extract_json

RTI_REPLY = """Office of the Public Information Officer, Pune Municipal Corporation.
Subject: Reply to your RTI application dated 05/01/2025 under Section 6(1) of the Right to Information Act, 2005.
The information sought regarding road repair expenditure is rejected under Section 8(1)(j) as it is personal information.
If you are not satisfied you may file a first appeal within 30 days before the Appellate Authority, Pune Municipal Corporation."""

GOOD = {
    "document_type": "RTI reply",
    "title": "Reply rejecting RTI request",
    "summary": "The office refused to share the information.",
    "key_points": ["Request rejected under Section 8(1)(j)"],
    "deadlines": [{"description": "File first appeal", "date": "not a date", "period": "within 30 days of this reply"}],
    "required_actions": [{"action": "File a first appeal if you disagree", "priority": "URGENT"}],
    "legal_references": [
        {"citation": "RTI Act, 2005 - Section 19(1)", "explanation": "First appeal in 30 days", "source_id": "[S1]"},
        {"citation": "Made-up Act", "explanation": "x", "source_id": "S99"},
    ],
}


def make(settings, container, responses):
    return Simplifier(settings, container.retriever, FakeListChatModel(responses=responses))


def test_extract_json_handles_fences_and_chatter():
    assert extract_json('Sure!\n```json\n{"a": {"b": "}"}}\n```') == {"a": {"b": "}"}}
    with pytest.raises(ValueError):
        extract_json("no json")


def test_build_queries_picks_up_statutes():
    qs = build_queries(RTI_REPLY)
    assert any("Section 8(1)(j)" in q for q in qs)


def test_structured_output_is_validated_and_grounded(settings, container):
    res = make(settings, container, [json.dumps(GOOD)]).simplify(RTI_REPLY, "en")
    doc = res.document
    assert doc.deadlines[0].date is None and doc.deadlines[0].period.startswith("within 30 days")
    assert doc.required_actions[0].priority == "medium"  # invalid priority coerced
    ids = {r.citation: r.source_id for r in doc.legal_references}
    assert ids["RTI Act, 2005 - Section 19(1)"] == "S1"
    assert ids["Made-up Act"] is None  # hallucinated id dropped
    assert res.sources and res.sources[0].cited and res.sources[0].source_id == "S1"
    assert res.model == settings.llm_model


def test_repairs_invalid_json_once(settings, container):
    res = make(settings, container, ["I cannot do that", json.dumps(GOOD)]).simplify(RTI_REPLY, "mr")
    assert res.language == "mr" and res.document.summary


def test_gives_up_after_failed_repair(settings, container):
    with pytest.raises(GenerationError):
        make(settings, container, ["nope", "still nope"]).simplify(RTI_REPLY, "en")


class RoutingFake(FakeListChatModel):
    """Returns condensed notes for map prompts and the final JSON for the explanation prompt."""

    def _call(self, messages, stop=None, run_manager=None, **kwargs):
        return json.dumps(GOOD) if "REFERENCE SOURCES" in messages[-1].content else "- note about the reply"


def test_long_documents_use_map_reduce(settings, container):
    long_text = (RTI_REPLY + "\n") * 120  # > max_direct_chars
    assert len(long_text) > settings.max_direct_chars
    res = Simplifier(settings, container.retriever, RoutingFake(responses=["unused"])).simplify(long_text, "en")
    assert res.used_map_reduce and res.document.title
