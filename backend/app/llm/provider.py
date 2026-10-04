"""
LLM provider abstraction.

Supports Google Gemini, OpenAI, and Anthropic via LangChain.
Provider can be changed via LLM_PROVIDER environment variable.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    def get_chat_model(self, temperature: float = 0.0) -> BaseChatModel:
        """Return a LangChain chat model instance."""
        ...

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier string."""
        ...


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider.

    Uses langchain-openai ChatOpenAI pointed at Gemini's OpenAI-compatible
    endpoint (https://generativelanguage.googleapis.com/v1beta/openai/).
    This avoids a separate langchain-google-genai dependency.
    """

    def __init__(self) -> None:
        self._api_key = settings.gemini_api_key
        if not self._api_key:
            raise ValueError(
                "Gemini provider selected but no API key configured. "
                "Set GEMINI_API_KEY in your .env file."
            )

    def get_chat_model(self, temperature: float = 0.0) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

        primary = ChatOpenAI(
            model=settings.gemini_model,
            temperature=temperature,
            api_key=self._api_key,
            base_url=base_url,
            request_timeout=35,
        )
        return primary

    def get_model_name(self) -> str:
        return settings.gemini_model


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError(
                "OpenAI provider selected but no API key configured. "
                "Set OPENAI_API_KEY in your .env file."
            )

    def get_chat_model(self, temperature: float = 0.0) -> BaseChatModel:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=temperature,
            api_key=settings.openai_api_key,
            request_timeout=60,
        )

    def get_model_name(self) -> str:
        return settings.openai_model


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider."""

    def __init__(self) -> None:
        if not settings.anthropic_api_key:
            raise ValueError(
                "Anthropic provider selected but no API key configured. "
                "Set ANTHROPIC_API_KEY in your .env file."
            )

    def get_chat_model(self, temperature: float = 0.0) -> BaseChatModel:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.anthropic_model,
            temperature=temperature,
            api_key=settings.anthropic_api_key,
            timeout=60,
        )

    def get_model_name(self) -> str:
        return settings.anthropic_model


# =============================================================================
# Factory
# =============================================================================

_PROVIDERS = {
    "gemini": GeminiProvider,
    "google": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

_provider_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider (singleton)."""
    global _provider_instance
    if _provider_instance is None:
        provider_name = settings.llm_provider.lower()
        provider_cls = _PROVIDERS.get(provider_name)
        if provider_cls is None:
            raise ValueError(
                f"Unknown LLM provider: '{provider_name}'. "
                f"Supported: {list(_PROVIDERS.keys())}"
            )
        _provider_instance = provider_cls()
        logger.info(f"LLM provider initialized: {provider_name} ({_provider_instance.get_model_name()})")
    return _provider_instance


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """Convenience: get a ready-to-use LangChain chat model."""
    return get_llm_provider().get_chat_model(temperature=temperature)


def get_llm_with_retry(temperature: float = 0.0, max_retries: int = 3) -> BaseChatModel:
    """Get an LLM model instance; retry with exponential backoff on rate-limit errors.

    On a 429 (Too Many Requests) error, waits 1 s, then 2 s, then 4 s before
    giving up. This prevents full agent failures when the LLM API is busy.

    Usage:
        llm = get_llm_with_retry()          # same interface as get_llm()
        response = await llm.ainvoke(msgs)
    """
    import asyncio

    class _RetryWrapper:
        """Thin async wrapper that adds retry-on-429 to any BaseChatModel."""

        def __init__(self, model: BaseChatModel, retries: int) -> None:
            self._model = model
            self._retries = retries

        async def ainvoke(self, messages, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(self._retries):
                try:
                    return await self._model.ainvoke(messages, **kwargs)
                except Exception as exc:
                    err_str = str(exc)
                    is_rate_limit = "429" in err_str or "rate limit" in err_str.lower() or "quota" in err_str.lower()
                    if is_rate_limit and attempt < self._retries - 1:
                        wait_seconds = 2 ** attempt  # 1 s, 2 s, 4 s
                        logger.warning(
                            f"LLM rate-limited (attempt {attempt + 1}/{self._retries}). "
                            f"Retrying in {wait_seconds}s..."
                        )
                        await asyncio.sleep(wait_seconds)
                        last_exc = exc
                    else:
                        raise
            raise last_exc  # type: ignore[misc]

        # Proxy non-async calls and attribute access to the underlying model
        def __getattr__(self, name: str):
            return getattr(self._model, name)

    model = get_llm_provider().get_chat_model(temperature=temperature)
    return _RetryWrapper(model, max_retries)  # type: ignore[return-value]
