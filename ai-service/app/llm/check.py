"""Check that the configured LLM(s) answer.   docker compose exec ai-service python -m app.llm.check"""
from __future__ import annotations

import sys

from app.config import get_settings
from app.llm.errors import classify
from app.llm.providers import LlmChain, LlmConfigError, build_llm_chain


def probe(chain: LlmChain) -> list[dict]:
    """One tiny call to every model in the chain (primary first)."""
    results = []
    for label, model in chain.models:
        try:
            reply = model.invoke("Reply with the single word: OK")
            results.append({"model": label, "ok": True, "reply": str(reply.content)[:50]})
        except Exception as exc:
            known = classify(exc)
            results.append({"model": label, "ok": False,
                            "detail": str(known) if known else f"{type(exc).__name__}: {str(exc)[:300]}"})
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
