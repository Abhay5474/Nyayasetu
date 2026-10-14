"""Check that the configured LLM(s) answer, or list the model names they offer.

    docker compose exec ai-service python -m app.llm.check
    docker compose exec ai-service python -m app.llm.check --list-models
"""
from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from app.config import get_settings
from app.llm.errors import classify
from app.llm.providers import LlmChain, LlmConfigError, build_llm_chain


def _one(label: str, model) -> dict:
    try:
        reply = model.invoke("Reply with the single word: OK")
        return {"model": label, "ok": True, "reply": str(reply.content)[:50]}
    except Exception as exc:
        known = classify(exc)
        return {"model": label, "ok": False, "detail": str(known) if known else f"{type(exc).__name__}: {str(exc)[:300]}"}


def probe(chain: LlmChain, timeout: float = 30.0) -> list[dict]:
    """One tiny call to every model in the chain, all at once (primary first). A model that does not answer in `timeout`
    seconds is reported as failed instead of blocking the check."""
    pool = ThreadPoolExecutor(max_workers=max(1, len(chain.models)))
    futures = [(label, pool.submit(_one, label, model)) for label, model in chain.models]
    results = []
    for label, fut in futures:
        try:
            results.append(fut.result(timeout=timeout))
        except FutureTimeout:
            results.append({"model": label, "ok": False,
                            "detail": f"No answer within {timeout:.0f} s. The provider may be overloaded (try a different model name, e.g. a \"lite\" one), or unreachable: check the base URL."})
    pool.shutdown(wait=False, cancel_futures=True)
    return results


def list_models(base_url: str, api_key: str, timeout: float = 20.0) -> list[str]:
    """Model ids the OpenAI-compatible endpoint offers to this key (GET {base_url}/models)."""
    import httpx

    r = httpx.get(base_url.rstrip("/") + "/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout)
    r.raise_for_status()
    ids = [str(m.get("id", "")).removeprefix("models/") for m in r.json().get("data", [])]
    return sorted(i for i in ids if i)


def _print_models(settings) -> int:
    targets = []
    if settings.llm_provider == "openai" and settings.openai_api_key:
        targets.append(("PRIMARY   (LLM_MODEL = %s)" % settings.llm_model, settings.openai_base_url or "https://api.openai.com/v1", settings.openai_api_key))
    if settings.fallback_llm_provider == "openai" and (settings.fallback_api_key or settings.openai_api_key):
        targets.append(("FALLBACK  (FALLBACK_LLM_MODEL = %s)" % settings.fallback_llm_model,
                        settings.fallback_base_url or "https://api.openai.com/v1", settings.fallback_api_key or settings.openai_api_key))
    if not targets:
        print("No OpenAI-compatible endpoint is configured (listing works for LLM_PROVIDER=openai and FALLBACK_LLM_PROVIDER=openai).")
        return 1
    for title, url, key in targets:
        print(f"\n{title}\n  endpoint: {url}")
        try:
            ids = list_models(url, key)
        except Exception as exc:
            print(f"  could not list models: {type(exc).__name__}: {str(exc)[:200]}")
            continue
        print(f"  {len(ids)} models available to this key - put one of these names in .env:")
        for i in ids:
            print("   ", i)
    return 0


def main() -> int:
    settings = get_settings()
    if "--list-models" in sys.argv[1:]:
        return _print_models(settings)
    if settings.llm_provider == "mock":
        print("LLM_PROVIDER=mock: no real model is configured.")
        return 1
    try:
        chain = build_llm_chain(settings)
    except LlmConfigError as exc:
        print(f"NOT CONFIGURED: {exc}")
        return 1
    results = probe(chain)
    for r in results:
        print(("OK      " if r["ok"] else "FAILED  ") + r["model"] + ("" if r["ok"] else f"\n          {r['detail']}"))
    ok = any(r["ok"] for r in results)
    print("\nThe service can answer." if ok else "\nNo model answered: documents will fail until this is fixed.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
