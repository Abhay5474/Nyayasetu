"""LangChain chat-model factory (Anthropic, OpenAI-compatible, Ollama)."""
from __future__ import annotations

import logging

from langchain_core.language_models import BaseChatModel

from app.config import Settings


log = logging.getLogger(__name__)


class LlmConfigError(RuntimeError):
    """The configured LLM provider cannot be used (e.g. missing API key)."""


def build_chat_model(settings: Settings) -> BaseChatModel:
    p = settings.llm_provider
    if p == "anthropic":
        if not settings.anthropic_api_key:
            raise LlmConfigError("ANTHROPIC_API_KEY is not set")
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model,
            api_key=settings.anthropic_api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout_s,
            max_retries=2,
        )
    if p == "openai":
        if not settings.openai_api_key:
            raise LlmConfigError("OPENAI_API_KEY is not set")
        from langchain_openai import ChatOpenAI

        if "generativelanguage.googleapis.com" in (settings.openai_base_url or "") and not settings.openai_api_key.startswith("AIza"):
            log.warning("Gemini API keys from Google AI Studio normally start with 'AIza'; if requests fail with 401, "
                        "create a key at https://aistudio.google.com/apikey")

        return ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout_s,
            max_retries=2,
        )
    if p == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            num_predict=settings.llm_max_tokens,
        )
    raise LlmConfigError(f"Provider '{p}' has no chat model")
