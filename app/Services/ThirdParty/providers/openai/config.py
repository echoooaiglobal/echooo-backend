# app/Services/ThirdParty/providers/openai/config.py

from pydantic import BaseModel
import os

class OpenAIConfig(BaseModel):
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    default_model: str = "gpt-4"
    
    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create config from environment variables"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        return cls(
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
            max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
            default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4")
        )