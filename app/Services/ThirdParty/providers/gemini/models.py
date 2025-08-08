# app/Services/ThirdParty/providers/gemini/models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ContentPart(BaseModel):
    text: str

class Content(BaseModel):
    parts: List[ContentPart]

class GenerationConfig(BaseModel):
    temperature: Optional[float] = Field(default=0.7, ge=0, le=1)
    max_output_tokens: Optional[int] = Field(default=1000, gt=0)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    top_k: Optional[int] = Field(default=40, gt=0)

class SafetySetting(BaseModel):
    category: str
    threshold: str

class GenerateContentRequest(BaseModel):
    model: str = "gemini-pro"
    contents: List[Content]
    generation_config: Optional[GenerationConfig] = None
    safety_settings: Optional[List[SafetySetting]] = None

class Candidate(BaseModel):
    content: Content
    finish_reason: Optional[str] = None
    index: Optional[int] = None

class UsageMetadata(BaseModel):
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int

class GenerateContentResponse(BaseModel):
    candidates: List[Candidate]
    usage_metadata: Optional[UsageMetadata] = None