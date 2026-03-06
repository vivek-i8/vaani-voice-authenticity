from .base import LLMService
from .mock_llm import MockLLM
from .bedrock_llm import BedrockLLM
from app.core.config import settings


def get_llm_service() -> LLMService:
    """
    Factory function to get appropriate LLM service based on configuration.
    
    Returns:
        LLMService instance (MockLLM or BedrockLLM)
    """
    if settings.use_bedrock:
        try:
            return BedrockLLM()
        except Exception as e:
            return MockLLM()
    else:
        return MockLLM()


__all__ = ["LLMService", "MockLLM", "BedrockLLM", "get_llm_service"]
