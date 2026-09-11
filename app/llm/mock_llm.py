from typing import Any, Dict

from .base import LLMService


class MockLLM(LLMService):
    """No-credential LLM service for local development and testing.

    Returns deterministic explanations in the same structured format as the
    real provider so the V1 API contract holds without any API key.
    """

    def generate(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        classification = str(
            structured_data.get("classification", structured_data.get("label", "inconclusive"))
        ).lower()
        confidence = structured_data.get("confidence", 0.0)

        if language == "hi":
            if classification == "human":
                return {
                    "summary": f"यह आवाज़ वास्तविक मानव वक्ता की प्रतीत होती है। विश्वास स्तर: {confidence:.2f}",
                    "technical_analysis": "प्राकृतिक पिच विविधता और स्पेक्ट्रल पैटर्न मानव भाषण के लिए विशिष्ट हैं।",
                    "recommendation": "यह कॉल वैध प्रतीत होता है। सावधानी बरतें।",
                    "model": "mock",
                }
            if classification in ("ai", "ai_generated"):
                return {
                    "summary": f"यह आवाज़ कृत्रिम रूप से उत्पन्न प्रतीत होती है। विश्वास स्तर: {confidence:.2f}",
                    "technical_analysis": "स्थिर पिच पैटर्न और कम स्पेक्ट्रल परिवर्तनशीलता सिंथेटिक भाषण का संकेत है।",
                    "recommendation": "सतर्क रहें! OTP या बैंक विवरण साझा न करें।",
                    "model": "mock",
                }
            return {
                "summary": f"आवाज़ विश्लेषण अनिर्णायक है। विश्वास स्तर: {confidence:.2f}",
                "technical_analysis": "शोर या खराब ऑडियो गुणवत्ता के कारण सटीक विश्लेषण संभव नहीं है।",
                "recommendation": "अतिरिक्त सतर्कता के रूप में सतर्क रहें।",
                "model": "mock",
            }

        if classification == "human":
            return {
                "summary": f"This voice appears to be from a real human speaker. Confidence level: {confidence:.2f}",
                "technical_analysis": "Natural pitch variations and spectral patterns are consistent with authentic human speech.",
                "recommendation": "This call appears to be legitimate. Exercise caution.",
                "model": "mock",
            }
        if classification in ("ai", "ai_generated"):
            return {
                "summary": f"This voice appears to be artificially generated. Confidence level: {confidence:.2f}",
                "technical_analysis": "The model detected stable pitch patterns and low spectral variability common in AI-generated speech.",
                "recommendation": "Be cautious! Do not share OTP or bank details.",
                "model": "mock",
            }
        return {
            "summary": f"Voice analysis is inconclusive. Confidence level: {confidence:.2f}",
            "technical_analysis": "Background noise or poor audio quality prevents accurate acoustic analysis.",
            "recommendation": "Stay alert as an extra precaution.",
            "model": "mock",
        }
