from app.core.config import settings

from .base import LLMService
from .mock_llm import MockLLM
from .openrouter_llm import OpenRouterLLM


def get_llm_service() -> LLMService:
    """
    Factory: real OpenRouter-compatible provider when USE_LLM=true and a key
    is configured; MockLLM otherwise (no-credential / local mode).
    """
    if settings.use_llm:
        try:
            return OpenRouterLLM()
        except Exception as e:
            print(f"⚠️ LLM provider unavailable ({e}); falling back to MockLLM.")
            return MockLLM()
    return MockLLM()


__all__ = ["LLMService", "MockLLM", "OpenRouterLLM", "get_llm_service"]
