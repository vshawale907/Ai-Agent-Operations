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
