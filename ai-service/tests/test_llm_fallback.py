import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import pytest

from app.config import Settings
from app.llm.errors import classify
from app.llm.providers import build_llm_chain


class _Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    behaviours: dict = {}
    calls: list = []


class _Handler(BaseHTTPRequestHandler):
    """Minimal OpenAI-compatible endpoint: the model name picks the behaviour (ok | 503 | 401 | 404)."""

    def log_message(self, *a):
        pass

    def do_GET(self):
        data = json.dumps({"object": "list", "data": [{"id": "models/big-model"}, {"id": "small-model"}]}).encode()
        self.server.calls.append("GET " + self.path)
        self.send_response(200 if self.headers.get("Authorization") == "Bearer secret" else 401)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        model = body["model"]
        self.server.calls.append(model)
        mode = self.server.behaviours.get(model, "ok")
        if mode == "hang":
            import time

            time.sleep(4)
            mode = "ok"
        if mode == "ok":
            payload = {"id": "x", "object": "chat.completion", "created": 0, "model": model, "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                       "choices": [{"index": 0, "message": {"role": "assistant", "content": f"answer from {model}"}, "finish_reason": "stop"}]}
            code = 200
        else:
            code = int(mode)
            payload = {"error": {"code": code, "message": "scripted failure", "status": "SCRIPTED"}}
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture
def server():
    srv = _Server(("127.0.0.1", 0), _Handler)
    srv.behaviours, srv.calls = {}, []
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


def settings_for(server, **kw):
    base = dict(llm_provider="openai", llm_model="primary", openai_api_key="AQ.test", openai_base_url=f"http://127.0.0.1:{server.server_port}/v1",
                llm_max_retries=0, llm_timeout_s=10)
    return Settings(**{**base, **kw})


def text(reply):
    return reply.content


def test_primary_is_used_when_healthy(server):
    chain = build_llm_chain(settings_for(server, llm_fallback_models="backup"))
    assert text(chain.runnable.invoke("hi")) == "answer from primary"
    assert server.calls == ["primary"] and chain.used.get() == "primary"


def test_overloaded_primary_fails_over_to_a_backup_model(server):
    server.behaviours = {"primary": "503"}
    chain = build_llm_chain(settings_for(server, llm_fallback_models="backup-1,backup-2"))
    assert text(chain.runnable.invoke("hi")) == "answer from backup-1"
    assert server.calls[0] == "primary" and server.calls[-1] == "backup-1"
    assert chain.used.get() == "backup-1"  # the answer is attributed to the model that really gave it


def test_chain_walks_every_fallback_in_order(server):
    server.behaviours = {"primary": "503", "backup-1": "429", "backup-2": "404"}
    s = settings_for(server, llm_fallback_models="backup-1,backup-2", fallback_llm_provider="openai", fallback_llm_model="other-service",
                     fallback_api_key="k2", fallback_base_url=f"http://127.0.0.1:{server.server_port}/v1")
    chain = build_llm_chain(s)
    assert [label for label, _ in chain.models] == ["openai:primary", "openai:backup-1", "openai:backup-2", "openai:other-service"]
    assert text(chain.runnable.invoke("hi")) == "answer from other-service"
    order = [m for i, m in enumerate(server.calls) if i == 0 or m != server.calls[i - 1]]  # each model may be retried once first
    assert order == ["primary", "backup-1", "backup-2", "other-service"]


def test_bad_key_on_primary_still_falls_back_to_second_provider(server):
    server.behaviours = {"primary": "401"}
    s = settings_for(server, fallback_llm_provider="openai", fallback_llm_model="second", fallback_api_key="good",
                     fallback_base_url=f"http://127.0.0.1:{server.server_port}/v1")
    assert text(build_llm_chain(s).runnable.invoke("hi")) == "answer from second"


def test_all_models_failing_raises_a_classifiable_error(server):
    server.behaviours = {"primary": "503", "backup": "503"}
    chain = build_llm_chain(settings_for(server, llm_fallback_models="backup"))
    with pytest.raises(Exception) as err:
        chain.runnable.invoke("hi")
    assert classify(err.value).code == "llm_overloaded"


def test_chain_works_inside_a_prompt_pipeline_and_batch(server):
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    server.behaviours = {"primary": "503"}
    chain = build_llm_chain(settings_for(server, llm_fallback_models="backup"))
    pipeline = ChatPromptTemplate.from_messages([("human", "{x}")]) | chain.runnable | StrOutputParser()  # the map-reduce shape
    assert pipeline.batch([{"x": "a"}, {"x": "b"}], config={"max_concurrency": 2}) == ["answer from backup"] * 2


def test_misconfigured_fallback_is_skipped_but_primary_must_be_valid(server):
    s = settings_for(server, fallback_llm_provider="anthropic", fallback_llm_model="x")  # no Anthropic key anywhere
    assert [label for label, _ in build_llm_chain(s).models] == ["openai:primary"]
    with pytest.raises(Exception, match="OPENAI_API_KEY"):
        build_llm_chain(settings_for(server, openai_api_key=None))


def test_overloaded_error_message_mentions_the_fix():
    class E(Exception):
        status_code = 503

    err = classify(E("high demand"))
    assert err.code == "llm_overloaded" and err.http_status == 503 and "LLM_FALLBACK_MODELS" in str(err)


def test_check_probes_every_model_and_reports_failures(server, capsys, monkeypatch):
    from app.llm import check

    server.behaviours = {"primary": "503"}
    s = settings_for(server, llm_fallback_models="backup")
    results = check.probe(build_llm_chain(s))
    assert [r["ok"] for r in results] == [False, True] and "overloaded" in results[0]["detail"]

    monkeypatch.setattr(check, "get_settings", lambda: s)
    assert check.main() == 0  # one working model is enough for the service to answer
    out = capsys.readouterr().out
    assert "FAILED  openai:primary" in out and "OK      openai:backup" in out and "can answer" in out


def test_probe_does_not_hang_on_a_silent_model(server):
    import time

    from app.llm import check

    server.behaviours = {"primary": "hang"}
    chain = build_llm_chain(settings_for(server, llm_fallback_models="backup"))
    started = time.time()
    results = check.probe(chain, timeout=1.0)
    assert time.time() - started < 3.5  # models are probed together and the slow one is cut off
    assert [r["ok"] for r in results] == [False, True] and "No answer within 1 s" in results[0]["detail"]


def test_list_models_prints_names_for_primary_and_fallback(server, capsys, monkeypatch):
    from app.llm import check

    base = f"http://127.0.0.1:{server.server_port}/v1"
    s = settings_for(server, openai_api_key="secret", fallback_llm_provider="openai", fallback_llm_model="x",
                     fallback_api_key="wrong-key", fallback_base_url=base)
    monkeypatch.setattr(check, "get_settings", lambda: s)
    monkeypatch.setattr(check.sys, "argv", ["check", "--list-models"])
    assert check.main() == 0
    out = capsys.readouterr().out
    assert "PRIMARY" in out and "big-model" in out and "small-model" in out and "models/" not in out
    assert "FALLBACK" in out and "could not list models" in out  # a wrong key is reported, not hidden
