# app/Services/ThirdParty/providers/gemini/config.py

from pydantic import BaseModel
import os

class GeminiConfig(BaseModel):
    api_key: str
    base_url: str = "https://generativelanguage.googleapis.com/v1"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    default_model: str = "gemini-pro"
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create config from environment variables"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1"),
            timeout=int(os.getenv("GEMINI_TIMEOUT", "30")),
            max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "3")),
            default_model=os.getenv("GEMINI_DEFAULT_MODEL", "gemini-pro")
        )