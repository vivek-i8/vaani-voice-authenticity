from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Explanation(BaseModel):
    primary_language: str = Field(..., description="Primary language code ('hi' or 'en')")
    text: str = Field(..., description="Explanation text in primary language")
    advisory: str = Field(..., description="Safety advisory in primary language")
    alternate_language: Optional[str] = Field(None, description="Alternate language code")
    alternate_text: Optional[str] = Field(None, description="Explanation text in alternate language")
    alternate_advisory: Optional[str] = Field(None, description="Safety advisory in alternate language")


class SingleClipResponse(BaseModel):
    classification: str = Field(..., pattern="^(human|ai_generated|inconclusive)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: Explanation


class BatchClipResponse(BaseModel):
    classification: str = Field(..., pattern="^(human|ai_generated|inconclusive)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: Explanation


class HealthResponse(BaseModel):
    status: str
    device: str