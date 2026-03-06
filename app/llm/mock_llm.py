from typing import Dict, Any
from .base import LLMService


class MockLLM(LLMService):
    """Mock LLM service for local development and testing."""
    
    def generate(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Generate mock explanation based on structured data.
        
        Args:
            structured_data: Dict with classification, confidence, and features
            language: Target language ("hi" or "en")
            
        Returns:
            Dict with explanation and advisory text
        """
        classification = structured_data.get("classification", "unknown")
        confidence = structured_data.get("confidence", 0.0)
        
        # Mock explanations based on classification
        if language == "hi":
            explanations = {
                "human": {
                    "text": f"यह आवाज़ वास्तविक मानव वक्ता की प्रतीत होती है। विश्वास स्तर: {confidence:.2f}",
                    "advisory": "यह कॉल प्रतीत होता है कि वैध है। सावधानी बरतें।"
                },
                "ai_generated": {
                    "text": f"यह आवाज़ कृत्रिम रूप से उत्पन्न प्रतीत होती है। विश्वास स्तर: {confidence:.2f}",
                    "advisory": "सतर्क रहें! OTP या बैंक विवरण साझा न करें।"
                },
                "inconclusive": {
                    "text": f"आवाज़ विश्लेषण अनिर्णायक है। विश्वास स्तर: {confidence:.2f}",
                    "advisory": "अतिरिक्त सतर्कता के रूप में सतर्क रहें।"
                }
            }
        else:  # English
            explanations = {
                "human": {
                    "text": f"This voice appears to be from a real human speaker. Confidence level: {confidence:.2f}",
                    "advisory": "This call appears to be legitimate. Exercise caution."
                },
                "ai_generated": {
                    "text": f"This voice appears to be artificially generated. Confidence level: {confidence:.2f}",
                    "advisory": "Be cautious! Do not share OTP or bank details."
                },
                "inconclusive": {
                    "text": f"Voice analysis is inconclusive. Confidence level: {confidence:.2f}",
                    "advisory": "Stay alert as an extra precaution."
                }
            }
        
        return explanations.get(classification, explanations["inconclusive"])
