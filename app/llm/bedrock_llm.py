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
        
        language_instruction = "Hindi" if language == "hi" else "English"
        
        prompt = f"""
You are Vaani's explanation assistant. Analyze the voice classification data and provide a clear, concise explanation.

INPUT DATA:
- Classification: {classification}
- Confidence: {confidence:.2f}

REQUIREMENTS:
1. Respond in {language_instruction}
2. Maximum 120 words total
3. Include explanation of the classification
4. Include safety advisory guidance
5. No hallucinated claims or legal guarantees
6. No exaggeration

RESPONSE FORMAT (JSON):
{{
    "text": "Brief explanation in {language_instruction}",
    "advisory": "Safety advisory in {language_instruction}"
}}

Analyze the data and provide response in the specified JSON format.
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
                return json.loads(json_str)
            else:
                # Fallback: treat as plain text
                return {
                    "text": content.strip(),
                    "advisory": "Stay alert and verify caller identity."
                }
        except json.JSONDecodeError:
            return {
                "text": content.strip(),
                "advisory": "Stay alert and verify caller identity."
            }
    
    def _fallback_explanation(self, structured_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Fallback explanation when Bedrock fails."""
        classification = structured_data.get("classification", "inconclusive")
        
        if language == "hi":
            fallbacks = {
                "human": {
                    "text": "यह आवाज़ वास्तविक मानव वक्ता की प्रतीत होती है।",
                    "advisory": "सावधानी बरतें और कॉलर की पहचान सत्यापित करें।"
                },
                "ai_generated": {
                    "text": "यह आवाज़ कृत्रिम रूप से उत्पन्न प्रतीत होती है।",
                    "advisory": "सतर्क रहें! OTP या वित्तीय जानकारी साझा न करें।"
                },
                "inconclusive": {
                    "text": "आवाज़ विश्लेषण अनिर्णायक है।",
                    "advisory": "अतिरिक्त सतर्कता के रूप में सतर्क रहें।"
                }
            }
        else:
            fallbacks = {
                "human": {
                    "text": "This voice appears to be from a real human speaker.",
                    "advisory": "Exercise caution and verify caller identity."
                },
                "ai_generated": {
                    "text": "This voice appears to be artificially generated.",
                    "advisory": "Be cautious! Do not share OTP or financial information."
                },
                "inconclusive": {
                    "text": "Voice analysis is inconclusive.",
                    "advisory": "Stay alert as an extra precaution."
                }
            }
        
        return fallbacks.get(classification, fallbacks["inconclusive"])
