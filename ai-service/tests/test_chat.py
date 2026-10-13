import json

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from app.llm.chat import DocumentChat
from app.llm.simplifier import GenerationError
from app.schemas import ChatTurn

DOC = (
    "Reply to your RTI application dated 05/01/2025 under Section 6(1) of the Right to Information Act, 2005. "
    "Information about contractors' salaries is rejected under Section 8(1)(j) as personal information. "
    "You are required to pay Rs. 148 within 10 days from receipt of this letter. "
    "If you are not satisfied you may file a first appeal within 30 days before the Appellate Authority."
)


class Recorder(FakeListChatModel):
    """Fake model that records the messages it was called with."""

    seen: list = []

    def _call(self, messages, stop=None, run_manager=None, **kwargs):
        type(self).seen = messages
        return super()._call(messages, stop, run_manager, **kwargs)


def reply(**kw):
    base = {"answer": "You must pay Rs. 148 within 10 days.", "answerable": True,
            "quotes": ["pay Rs. 148 within 10 days"], "source_ids": ["S1", "S99"], "follow_ups": ["What if I do not pay?"]}
    return json.dumps({**base, **kw})


def make(settings, container, responses):
    return DocumentChat(settings, container.retriever, container.embedder, Recorder(responses=responses))


def test_answer_is_grounded_and_quotes_verified(settings, container):
    chat = make(settings, container, [reply(quotes=["pay Rs. 148 within 10 days", "invented sentence not in the document"])])
    res = chat.answer(DOC, "How much do I have to pay?", "en", [])
    assert res.answerable and "148" in res.answer
    assert res.quotes == ["pay Rs. 148 within 10 days"]  # fabricated quote dropped
    assert all(s.cited for s in res.sources) and all(s.source_id != "S99" for s in res.sources)
    assert res.follow_ups == ["What if I do not pay?"]


def test_history_and_context_are_sent_to_model(settings, container):
    chat = make(settings, container, [reply()])
    history = [ChatTurn(role="user", content="What is this letter about?"), ChatTurn(role="assistant", content="It rejects part of your RTI request.")]
    chat.answer(DOC, "And what is the deadline for that?", "mr", history)
    roles = [type(m).__name__ for m in Recorder.seen]
    assert roles == ["SystemMessage", "HumanMessage", "AIMessage", "HumanMessage"]
    assert "Marathi" in Recorder.seen[0].content
    last = Recorder.seen[-1].content
    assert "DOCUMENT EXCERPTS" in last and "QUESTION: And what is the deadline for that?" in last and "REFERENCE SOURCES" in last
    assert "DOCUMENT EXCERPTS" not in Recorder.seen[1].content  # context is not replayed in old turns


def test_unanswerable_passes_through_and_repair_works(settings, container):
    chat = make(settings, container, ["not json at all", reply(answer="The document does not say.", answerable=False, quotes=[], source_ids=[])])
    res = chat.answer(DOC, "Who is the judge?", "en", [])
    assert res.answerable is False and res.quotes == [] and res.sources == []


def test_invalid_output_after_repair_raises(settings, container):
    with pytest.raises(GenerationError):
        make(settings, container, ["nope", "still nope"]).answer(DOC, "q?", "en", [])


def test_long_documents_use_relevant_excerpts(settings, container):
    filler = "This paragraph is about unrelated municipal maintenance schedules and office timings. " * 40
    long_doc = filler * 12 + "\nThe appellant must deposit a security amount of Rs. 5000 before the hearing on 20/04/2025.\n" + filler * 12
    assert len(long_doc) > settings.max_direct_chars
    chat = make(settings, container, [reply()])
    chat.answer(long_doc, "How much security amount must the appellant deposit?", "en", [])
    prompt = Recorder.seen[-1].content
    assert "security amount of Rs. 5000" in prompt
    assert len(prompt) < len(long_doc) / 3


def test_mock_mode_is_extractive_and_honest(settings, container):
    chat = DocumentChat(settings, container.retriever, container.embedder, None)
    res = chat.answer(DOC, "Within how many days can I file a first appeal?", "en", [])
    assert "30 days" in res.answer and res.model == "mock-extractive" and "Demo mode" in res.answer
    none = chat.answer(DOC, "zebra giraffe", "en", [])
    assert none.answerable is False
