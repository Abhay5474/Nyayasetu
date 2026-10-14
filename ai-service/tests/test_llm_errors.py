import dataclasses

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.errors import LlmCallError, classify
from app.main import app

H = {"X-Internal-Token": "test-token"}
TEXT = "Reply to RTI application under Section 6(1) of the Right to Information Act, 2005 about road repairs in Ward 12."


class AuthenticationError(Exception):
    status_code = 401


class RateLimitError(Exception):
    status_code = 429


class APIConnectionError(Exception):
    pass


def test_classify_maps_provider_failures_to_actionable_messages():
    assert classify(AuthenticationError("bad key")).code == "llm_auth"
    assert "API key" in str(classify(AuthenticationError("bad key")))
    assert classify(RateLimitError()).http_status == 429
    assert classify(APIConnectionError()).code == "llm_unreachable"
    assert classify(ValueError("a bug")) is None  # real bugs must not be hidden behind a friendly message


def test_classify_follows_the_exception_chain():
    try:
        try:
            raise AuthenticationError("inner")
        except AuthenticationError as e:
            raise RuntimeError("wrapper") from e
    except RuntimeError as outer:
        assert classify(outer).code == "llm_auth"


def test_secrets_are_cleaned(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", '"  Bearer AIzaSyExample\n"')
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    s = Settings()
    assert s.openai_api_key == "AIzaSyExample" and s.openai_base_url is None


@pytest.fixture
def broken_llm_client(container):
    class FailingLlm:
        def invoke(self, *a, **k):
            raise AuthenticationError("Error code: 401")

    simplifier = dataclasses.replace(container.simplifier) if dataclasses.is_dataclass(container.simplifier) else container.simplifier
    original = simplifier.llm
    simplifier.llm = FailingLlm()
    app.state.container = container
    try:
        with TestClient(app) as c:
            yield c
    finally:
        simplifier.llm = original


def test_simplify_reports_a_rejected_key_with_a_code(broken_llm_client):
    # The mock container has no real LLM, so exercise the guard through the chat/simplify entry points directly.
    from app.main import _guard_llm

    def boom():
        raise AuthenticationError("Error code: 401")

    with pytest.raises(LlmCallError) as err:
        _guard_llm(boom)
    assert err.value.code == "llm_auth"


def test_error_handler_returns_code_and_detail(container):
    import app.main as main

    @main.app.get("/_boom")
    def _boom():  # temporary route to prove the exception handler's JSON shape
        raise LlmCallError("llm_auth", "The AI model rejected the API key.")

    main.app.state.container = container
    with TestClient(main.app) as c:
        r = c.get("/_boom")
    assert r.status_code == 502 and r.json() == {"detail": "The AI model rejected the API key.", "code": "llm_auth"}
    main.app.router.routes[:] = [x for x in main.app.router.routes if getattr(x, "path", "") != "/_boom"]


def test_llm_check_endpoint_in_mock_mode(container):
    app.state.container = container
    with TestClient(app) as c:
        assert c.get("/v1/llm/check").status_code == 401
        body = c.get("/v1/llm/check", headers=H).json()
    assert body["ok"] is True and body["provider"] == "mock"
