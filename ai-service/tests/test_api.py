import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import make_pdf

H = {"X-Internal-Token": "test-token"}
TEXT = (
    "Reply to RTI application dated 05/01/2025 under Section 6(1) of the Right to Information Act, 2005. "
    "The Public Information Officer must provide the information within 30 days. "
    "You may file a first appeal within 30 days before the Appellate Authority."
)


@pytest.fixture
def client(container):
    app.state.container = container
    with TestClient(app) as c:
        yield c


def test_requires_internal_token(client):
    assert client.post("/v1/simplify", json={"text": TEXT}).status_code == 401
    assert client.post("/v1/simplify", json={"text": TEXT}, headers={"X-Internal-Token": "bad"}).status_code == 401


def test_health_is_public(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["llm_provider"] == "mock"
    assert body["knowledge_base"]["chunks"] > 0


def test_extract_then_simplify_roundtrip(client):
    pdf = make_pdf([TEXT])
    r = client.post("/v1/extract", headers=H, files={"file": ("reply.pdf", pdf, "application/pdf")})
    assert r.status_code == 200, r.text
    ex = r.json()
    assert ex["method"] == "digital" and "first appeal" in ex["text"]

    r = client.post("/v1/simplify", headers=H, json={"text": ex["text"], "language": "mr"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model"] == "mock-extractive" and body["language"] == "mr"
    assert body["document"]["summary"] and any(d["period"] for d in body["document"]["deadlines"])
    assert body["sources"]


def test_extract_rejects_non_documents(client):
    r = client.post("/v1/extract", headers=H, files={"file": ("x.pdf", b"MZ not a pdf at all", "application/pdf")})
    assert r.status_code == 422


def test_kb_search_and_ingest(client):
    hits = client.get("/v1/kb/search", headers=H, params={"q": "second appeal 90 days information commission"}).json()
    assert hits and hits[0]["kb_id"].startswith("rti")
    r = client.post("/v1/kb/ingest", headers=H, json={"entries": [
        {"id": "api-test", "title": "T", "citation": "Test Act s.1", "text": "Some test legal text about widgets."}]})
    assert r.json() == {"entries": 1, "chunks": 1}
