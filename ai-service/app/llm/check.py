"""Check that the configured LLM(s) answer.   docker compose exec ai-service python -m app.llm.check"""
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
                            "detail": f"No answer within {timeout:.0f} s. Check the network, the base URL, and whether the provider is reachable from Docker."})
    pool.shutdown(wait=False, cancel_futures=True)
    return results


def main() -> int:
    settings = get_settings()
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
