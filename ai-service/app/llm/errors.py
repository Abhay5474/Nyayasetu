"""Turn raw provider failures (bad API key, quota, unreachable endpoint ...) into messages a person can act on."""
from __future__ import annotations


class LlmCallError(RuntimeError):
    """The LLM provider call failed for a reason the operator can fix (never contains secrets)."""

    def __init__(self, code: str, message: str, http_status: int = 502):
        super().__init__(message)
        self.code, self.http_status = code, http_status


def _chain(exc: BaseException):
    seen = set()
    while exc is not None and id(exc) not in seen:
        seen.add(id(exc))
        yield exc
        exc = exc.__cause__ or exc.__context__


def classify(exc: BaseException) -> LlmCallError | None:
    """Map an exception raised by an LLM SDK call to an LlmCallError, or None if it is not a provider problem."""
    for e in _chain(exc):
        if isinstance(e, LlmCallError):
            return e
        name, status = type(e).__name__, getattr(e, "status_code", None)
        if status in (401, 403) or "Authentication" in name or "PermissionDenied" in name:
            return LlmCallError(
                "llm_auth",
                "The AI model rejected the API key (401/403). Check LLM_PROVIDER, the API key and OPENAI_BASE_URL in .env "
                "(no quotes or spaces around the key), then run `docker compose up -d` to apply the change.")
        if status == 404 or "NotFound" in name:
            return LlmCallError("llm_model", "The AI provider does not know this model name. Check LLM_MODEL in .env.")
        if status == 429 or "RateLimit" in name:
            return LlmCallError("llm_rate_limit", "The AI model's rate limit or quota was reached. Wait a minute and try again, or check your plan.", 429)
        if status == 400 or "BadRequest" in name:
            return LlmCallError("llm_bad_request", "The AI provider rejected the request (400). Check LLM_MODEL and the provider settings in .env.")
        if "Timeout" in name:
            return LlmCallError("llm_timeout", "The AI model took too long to answer. Please try again.")
        if "APIConnection" in name or "ConnectError" in name or "ConnectionError" in name:
            return LlmCallError("llm_unreachable", "The AI model endpoint could not be reached. Check the network and OPENAI_BASE_URL / OLLAMA_BASE_URL in .env.")
    return None
