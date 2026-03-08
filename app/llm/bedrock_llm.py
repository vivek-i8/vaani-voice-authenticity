import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any
from .base import LLMService

from app.core.config import settings


class BedrockLLM(LLMService):
    """Amazon Bedrock LLM service using Claude 3.5 Sonnet."""
    
    def __init__(self):
        """Initialize Bedrock client."""
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=settings.aws_region
            )
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Configure AWS credentials for Bedrock access.")
    
    def generate(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Generate explanation using Claude 3.5 Sonnet via Bedrock.
        
        Args:
            structured_data: Dict with classification, confidence, and features
            language: Target language ("hi" or "en")
            
        Returns:
            Dict with explanation and advisory text
        """
        try:
            prompt = self._construct_prompt(structured_data, language)
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = self.client.invoke_model(
                modelId=settings.bedrock_model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read().decode('utf-8'))
            content = response_body['content'][0]['text']
            
            # Parse structured response
            return self._parse_response(content)
            
        except ClientError as e:
            # Fallback to deterministic explanation
            return self._fallback_explanation(structured_data, language)
        except Exception as e:
            return self._fallback_explanation(structured_data, language)
    
    def _construct_prompt(self, structured_data: Dict[str, Any], language: str) -> str:
        """Construct structured prompt for Claude."""
        classification = structured_data.get("classification", "unknown")
        confidence = structured_data.get("confidence", 0.0)
        pitch_variance = structured_data.get("pitch_variance", 0.0)
        spectral_drift = structured_data.get("spectral_drift", 0.0)
        zcr_variance = structured_data.get("zcr_variance", 0.0)
        entropy = structured_data.get("entropy", 0.0)
        
        language_instruction = "Hindi" if language == "hi" else "English"
        
        prompt = f"""
You are Vaani's explanation assistant. Analyze the voice classification data and provide a structured explanation.

VAANI SIGNAL METRICS:
- Predicted Label: {classification}
- Confidence: {confidence:.2f}
- Pitch Variance: {pitch_variance:.2f}
- Spectral Drift: {spectral_drift:.2f}
- Zero Crossing Rate Variance: {zcr_variance:.6f}
- Entropy: {entropy:.3f}

REQUIREMENTS:
1. Respond in {language_instruction}
2. Maximum 150 words total across all fields
3. Explain the decision based on the specific VAANI signal metrics provided
4. Reference the actual values in your technical analysis
5. Include specific safety recommendations based on the classification
6. No hallucinated claims or legal guarantees

RESPONSE FORMAT (JSON):
{{
    "summary": "Brief explanation of the classification result",
    "technical_analysis": "Explain how the VAANI signal metrics influenced the decision",
    "recommendation": "Recommended action for the user",
    "model": "Claude Bedrock"
}}

Analyze the VAANI signal metrics and provide response in the specified JSON format.
"""
        return prompt
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response and extract structured data."""
        try:
            # Try to parse JSON response
            if "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                parsed = json.loads(json_str)
                
                # Check if it's the new structured format with model field
                if "summary" in parsed and "technical_analysis" in parsed and "recommendation" in parsed and "model" in parsed:
                    return parsed
                # Check if it's the old format
                elif "summary" in parsed and "analysis" in parsed and "recommendation" in parsed:
                    # Convert old format to new format
                    return {
                        "summary": parsed.get("summary", ""),
                        "technical_analysis": parsed.get("analysis", ""),
                        "recommendation": parsed.get("recommendation", ""),
                        "model": "Claude Bedrock"
                    }
                else:
                    # Fallback: treat as plain text
                    return {
                        "summary": content.strip(),
                        "technical_analysis": content.strip(),
                        "recommendation": "Stay alert and verify caller identity.",
                        "model": "Claude Bedrock"
                    }
            else:
                # Fallback: treat as plain text
                return {
                    "summary": content.strip(),
                    "technical_analysis": content.strip(),
                    "recommendation": "Stay alert and verify caller identity.",
                    "model": "Claude Bedrock"
                }
        except json.JSONDecodeError:
            return {
                "summary": content.strip(),
                "technical_analysis": content.strip(),
                "recommendation": "Stay alert and verify caller identity.",
                "model": "Claude Bedrock"
            }
    
    def _fallback_explanation(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Fallback explanation when Bedrock fails."""
        classification = structured_data.get("classification", "inconclusive")
        
        if language == "hi":
            fallbacks = {
                "human": {
                    "summary": "यह आवाज़ वास्तविक मानव वक्ता की प्रतीत होती है।",
                    "technical_analysis": "प्राकृतिक पिच विविधता और स्पेक्ट्रल पैटर्न मानव भाषण के लिए विशिष्ट हैं।",
                    "recommendation": "सावधानी बरतें और कॉलर की पहचान सत्यापित करें।",
                    "model": "Claude Bedrock"
                },
                "ai_generated": {
                    "summary": "यह आवाज़ AI द्वारा उत्पन्न लगती है।",
                    "technical_analysis": "स्थिर पिच पैटर्न और कम स्पेक्ट्रल परिवर्तनशीलता सिंथेटिक भाषण का संकेत है।",
                    "recommendation": "इस कॉल पर सतर्क रहें और बोलने वाले को दूसरे चैनल से सत्यापित करें।",
                    "model": "Claude Bedrock"
                },
                "inconclusive": {
                    "summary": "ऑडियो गुणवत्ता निर्णायक विश्लेषण के लिए अपर्याप्त है।",
                    "technical_analysis": "शोर या खराब ऑडियो गुणवत्ता के कारण सटीक विश्लेषण संभव नहीं है।",
                    "recommendation": "कृपया बेहतर ऑडियो नमूना प्रदान करें।",
                    "model": "Claude Bedrock"
                }
            }
        else:
            fallbacks = {
                "human": {
                    "summary": "This voice sample appears to be authentic human speech.",
                    "technical_analysis": "Natural pitch variations and spectral patterns are consistent with authentic human speech.",
                    "recommendation": "No further action required. This appears to be a genuine human voice.",
                    "model": "Claude Bedrock"
                },
                "ai_generated": {
                    "summary": "This voice sample shows characteristics of AI-generated speech.",
                    "technical_analysis": "The model detected extremely stable pitch patterns and low spectral variability which are common in neural TTS systems.",
                    "recommendation": "Treat this voice call with caution and verify the speaker through another channel.",
                    "model": "Claude Bedrock"
                },
                "inconclusive": {
                    "summary": "Audio quality is insufficient for definitive analysis.",
                    "technical_analysis": "Background noise or poor audio quality prevents accurate acoustic analysis.",
                    "recommendation": "Please provide a clearer audio sample with minimal background noise.",
                    "model": "Claude Bedrock"
                }
            }
        
        return fallbacks.get(classification, fallbacks["inconclusive"])
