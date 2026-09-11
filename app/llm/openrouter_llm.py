import json
import re
from typing import Any, Dict

import httpx

from app.core.config import settings

from .base import LLMService


class OpenRouterLLM(LLMService):
    """LLM explanation service backed by an OpenRouter-compatible chat API.

    Transport/auth/provider logic only; prompt semantics follow the original
    V1 Bedrock prompt. Falls back to deterministic explanations on any
    provider failure.
    """

    def __init__(self, timeout: float = 30.0):
        if not settings.openrouter_api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not configured. "
                "Set USE_LLM=false to run without an LLM provider."
            )
        self.base_url = settings.openrouter_base_url.rstrip("/")
        self.model = settings.openrouter_model
        self.timeout = timeout

    def _send(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """POST to the provider and return the parsed JSON response."""
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def generate(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        prompt = self._construct_prompt(structured_data, language)
        try:
            payload = self._send(
                f"{self.base_url}/chat/completions",
                {
                    "model": self.model,
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            content = payload["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty completion content")
            return self._parse_response(content)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as e:
            print(f"⚠️ OpenRouter request failed: {e}")
            return self._fallback_explanation(structured_data, language)
        except Exception as e:
            print(f"⚠️ Failed to generate explanation: {e}")
            return self._fallback_explanation(structured_data, language)

    def _construct_prompt(self, structured_data: Dict[str, Any], language: str) -> str:
        """Construct structured prompt (preserved from V1's Bedrock prompt)."""
        predicted_label = structured_data.get("label", "unknown")
        confidence = structured_data.get("confidence", 0.0)
        pitch_variance = structured_data.get("pitch_variance", 0.0)
        spectral_drift = structured_data.get("spectral_drift", 0.0)
        zcr_variance = structured_data.get("zcr_variance", 0.0)
        entropy = structured_data.get("entropy", 0.0)

        language_instruction = "Hindi" if language == "hi" else "English"

        prompt = f"""
You are an AI forensic speech analysis expert.
A machine learning system has already analyzed an audio sample and produced the following acoustic signal metrics and classification result.

Your job is to explain WHY the model reached this decision using acoustic signal metrics.

Important rules:
* Do not question audio quality.
* Do not refuse analysis.
* Do not say audio is insufficient.
* Assume the ML system already processed the audio correctly.
* Explain how acoustic signals support the classification result.

Predicted Label: {predicted_label}
Confidence: {confidence:.2f}

Acoustic Metrics:
Pitch Variance: {pitch_variance:.2f}
Spectral Drift: {spectral_drift:.2f}
ZCR Variance: {zcr_variance:.6f}
Entropy: {entropy:.3f}

Explain how these acoustic signal metrics support the classification result. Reference specific values in your technical analysis.

Return structured JSON with this exact format:
{{
    "summary": "Short explanation of the classification result",
    "technical_analysis": "Detailed reasoning referencing acoustic signal metrics and explaining why they indicate human or AI speech",
    "recommendation": "Suggested action for the user (verify source, request clearer sample, etc.)",
    "model": "OpenRouter"
}}

Example style to follow:

Summary
The system classified this voice sample as AI-generated with very high confidence.

Technical Analysis
The acoustic analysis detected extremely stable pitch patterns combined with unusually high spectral drift. These characteristics are commonly associated with neural speech synthesis systems because synthesized voices often maintain consistent pitch while producing unnatural spectral transitions across frequency bands.

Recommendation
Treat this voice sample with caution and verify the speaker identity through another trusted communication channel.

Respond in {language_instruction}.
"""
        return prompt

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response: structured JSON, old format, or plain text."""
        try:
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                parsed = json.loads(json_str)

                if not isinstance(parsed, dict):
                    parsed = {}

                if "summary" in parsed and "technical_analysis" in parsed and "recommendation" in parsed:
                    return {
                        "summary": str(parsed.get("summary", "")),
                        "technical_analysis": str(parsed.get("technical_analysis", "")),
                        "recommendation": str(parsed.get("recommendation", "")),
                        "model": str(parsed.get("model", self.model)),
                    }
                # Old format: analysis instead of technical_analysis
                if "summary" in parsed and "analysis" in parsed and "recommendation" in parsed:
                    return {
                        "summary": str(parsed.get("summary", "")),
                        "technical_analysis": str(parsed.get("analysis", "")),
                        "recommendation": str(parsed.get("recommendation", "")),
                        "model": str(parsed.get("model", self.model)),
                    }
            # Plain text / malformed
            text = content.strip()
            return {
                "summary": text,
                "technical_analysis": text,
                "recommendation": "Stay alert and verify caller identity.",
                "model": self.model,
            }
        except Exception:
            text = content.strip()
            return {
                "summary": text,
                "technical_analysis": text,
                "recommendation": "Stay alert and verify caller identity.",
                "model": self.model,
            }

    def _fallback_explanation(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Deterministic explanation when the provider fails (V1 fallback preserved)."""
        classification = str(structured_data.get("classification", structured_data.get("label", ""))).lower()
        human_labels = ("human",)
        ai_labels = ("ai", "ai_generated")

        if language == "hi":
            if classification in human_labels:
                return {
                    "summary": "यह आवाज़ वास्तविक मानव वक्ता की प्रतीत होती है।",
                    "technical_analysis": "प्राकृतिक पिच विविधता और स्पेक्ट्रल पैटर्न मानव भाषण के लिए विशिष्ट हैं।",
                    "recommendation": "सावधानी बरतें और कॉलर की पहचान सत्यापित करें।",
                    "model": "fallback",
                }
            if classification in ai_labels:
                return {
                    "summary": "यह आवाज़ AI द्वारा उत्पन्न लगती है।",
                    "technical_analysis": "स्थिर पिच पैटर्न और कम स्पेक्ट्रल परिवर्तनशीलता सिंथेटिक भाषण का संकेत है।",
                    "recommendation": "इस कॉल पर सतर्क रहें और बोलने वाले को दूसरे चैनल से सत्यापित करें।",
                    "model": "fallback",
                }
            return {
                "summary": "ऑडियो गुणवत्ता निर्णायक विश्लेषण के लिए अपर्याप्त है।",
                "technical_analysis": "शोर या खराब ऑडियो गुणवत्ता के कारण सटीक विश्लेषण संभव नहीं है।",
                "recommendation": "कृपया बेहतर ऑडियो नमूना प्रदान करें।",
                "model": "fallback",
            }

        if classification in human_labels:
            return {
                "summary": "This voice sample appears to be authentic human speech.",
                "technical_analysis": "Natural pitch variations and spectral patterns are consistent with authentic human speech.",
                "recommendation": "No further action required. This appears to be a genuine human voice.",
                "model": "fallback",
            }
        if classification in ai_labels:
            return {
                "summary": "This voice sample shows characteristics of AI-generated speech.",
                "technical_analysis": "The model detected extremely stable pitch patterns and low spectral variability which are common in neural TTS systems.",
                "recommendation": "Treat this voice call with caution and verify the speaker through another channel.",
                "model": "fallback",
            }
        return {
            "summary": "Audio quality is insufficient for definitive analysis.",
            "technical_analysis": "Background noise or poor audio quality prevents accurate acoustic analysis.",
            "recommendation": "Please provide a clearer audio sample with minimal background noise.",
            "model": "fallback",
        }
