"""LangChain chat-model factory (Anthropic, OpenAI-compatible, Ollama) with an optional fallback chain."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable

from app.config import Settings
from app.llm.errors import classify

log = logging.getLogger(__name__)


class LlmConfigError(RuntimeError):
    """The configured LLM provider cannot be used (e.g. missing API key)."""


class UsedModel:
    """Which model produced the latest answer on this thread (so the UI shows the model that really answered)."""

    def __init__(self, default: str):
        self.default, self._local = default, threading.local()

    def set(self, name: str) -> None:
        self._local.name = name

    def get(self) -> str:
        return getattr(self._local, "name", self.default)


class _Watch(BaseCallbackHandler):
    """Logs every failed attempt (so failovers are visible) and records the model that answered."""

    def __init__(self, label: str, used: UsedModel, model: str):
        self.label, self.used, self.model = label, used, model

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        self.used.set(self.model)

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        known = classify(error)
        log.warning("LLM %s failed (%s): %s", self.label, known.code if known else type(error).__name__,
                    known or str(error)[:200])


def _make_model(provider: str, model: str, *, api_key: str | None, base_url: str | None, settings: Settings,
                max_retries: int, callbacks: list | None = None) -> BaseChatModel:
    common = dict(temperature=settings.llm_temperature, callbacks=callbacks or [])
    if provider == "anthropic":
        if not api_key:
            raise LlmConfigError("ANTHROPIC_API_KEY is not set")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, api_key=api_key, max_tokens=settings.llm_max_tokens,
                             timeout=settings.llm_timeout_s, max_retries=max_retries, **common)
    if provider == "openai":
        if not api_key:
            raise LlmConfigError("OPENAI_API_KEY is not set")
        from langchain_openai import ChatOpenAI

        if "generativelanguage.googleapis.com" in (base_url or "") and not api_key.startswith(("AIza", "AQ.")):
            log.warning("This does not look like a Gemini API key; if requests fail with 401, create one at "
                        "https://aistudio.google.com/apikey")
        return ChatOpenAI(model=model, api_key=api_key, base_url=base_url, max_tokens=settings.llm_max_tokens,
                          timeout=settings.llm_timeout_s, max_retries=max_retries, **common)
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=model, base_url=base_url or settings.ollama_base_url,
                          num_predict=settings.llm_max_tokens, **common)
    raise LlmConfigError(f"Provider '{provider}' has no chat model")


def build_chat_model(settings: Settings) -> BaseChatModel:
    """The primary model alone (no fallbacks)."""
    return _make_model(settings.llm_provider, settings.llm_model,
                       api_key=settings.anthropic_api_key if settings.llm_provider == "anthropic" else settings.openai_api_key,
                       base_url=settings.openai_base_url, settings=settings, max_retries=settings.llm_max_retries)


@dataclass
class LlmChain:
    runnable: Runnable  # primary with fallbacks; use like any chat model (invoke / batch / `prompt | chain`)
    models: list[tuple[str, BaseChatModel]] = field(default_factory=list)  # (label, model) in order, for diagnostics
    used: UsedModel | None = None


def build_llm_chain(settings: Settings) -> LlmChain:
    """Primary model, then LLM_FALLBACK_MODELS (same provider and key), then the FALLBACK_LLM_* provider.

    The primary must be configured (raises LlmConfigError); a misconfigured fallback is skipped with a warning.
    """
    used = UsedModel(settings.llm_model)
    same = [m.strip() for m in settings.llm_fallback_models.split(",") if m.strip() and m.strip() != settings.llm_model]
    other = settings.fallback_llm_provider != "none" and bool(settings.fallback_llm_model)
    retries = 1 if (same or other) else settings.llm_max_retries

    primary_key = settings.anthropic_api_key if settings.llm_provider == "anthropic" else settings.openai_api_key
    models: list[tuple[str, BaseChatModel]] = []

    def add(label: str, provider: str, model: str, api_key, base_url, required: bool) -> None:
        try:
            models.append((label, _make_model(provider, model, api_key=api_key, base_url=base_url, settings=settings,
                                              max_retries=retries, callbacks=[_Watch(label, used, model)])))
        except Exception as exc:
            if required:
                raise
            log.warning("Fallback %s skipped: %s", label, exc)

    add(f"{settings.llm_provider}:{settings.llm_model}", settings.llm_provider, settings.llm_model, primary_key,
        settings.openai_base_url, required=True)
    for m in same:
        add(f"{settings.llm_provider}:{m}", settings.llm_provider, m, primary_key, settings.openai_base_url, required=False)
    if other:
        fp = settings.fallback_llm_provider
        key = settings.fallback_api_key or (settings.anthropic_api_key if fp == "anthropic" else settings.openai_api_key)
        add(f"{fp}:{settings.fallback_llm_model}", fp, settings.fallback_llm_model, key,
            settings.fallback_base_url if fp != "anthropic" else None, required=False)

    primary = models[0][1]
    runnable = primary.with_fallbacks([m for _, m in models[1:]]) if len(models) > 1 else primary
    if len(models) > 1:
        log.info("LLM fallback chain: %s", " -> ".join(label for label, _ in models))
    return LlmChain(runnable, models, used)
