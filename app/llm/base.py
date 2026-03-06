from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMService(ABC):
    """Abstract base class for LLM services."""
    
    @abstractmethod
    def generate(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Generate multilingual explanation from structured data.
        
        Args:
            structured_data: Dict containing classification, confidence, and features
            language: Target language ("hi" for Hindi, "en" for English)
            
        Returns:
            Dict with explanation and advisory text in specified language
        """
        pass
