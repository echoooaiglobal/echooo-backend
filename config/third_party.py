# app/Config/third_party.py

import os
from typing import Dict, Optional
from pydantic import BaseModel, Field
from enum import Enum

class ThirdPartyProvider(str, Enum):
    """Supported third-party providers"""
    OPENAI = "openai"
    GEMINI = "gemini" 
    ANTHROPIC = "anthropic"
    STRIPE = "stripe"
    SENDGRID = "sendgrid"
    TWILIO = "twilio"

class AIProviderConfig(BaseModel):
    """Base configuration for AI providers"""
    enabled: bool = False
    api_key: Optional[str] = None
    timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    rate_limit_rpm: int = Field(default=60, ge=1)  # Requests per minute

class OpenAIProviderConfig(AIProviderConfig):
    """OpenAI specific configuration"""
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4"
    organization_id: Optional[str] = None
    max_tokens: int = Field(default=2000, ge=1, le=8000)

class GeminiProviderConfig(AIProviderConfig):
    """Gemini specific configuration"""
    base_url: str = "https://generativelanguage.googleapis.com/v1"
    default_model: str = "gemini-pro"

class AnthropicProviderConfig(AIProviderConfig):
    """Anthropic Claude specific configuration"""
    base_url: str = "https://api.anthropic.com"
    default_model: str = "claude-3-sonnet-20240229"

class ThirdPartyConfig(BaseModel):
    """Main third-party services configuration"""
    
    # AI Providers
    openai: OpenAIProviderConfig = OpenAIProviderConfig()
    gemini: GeminiProviderConfig = GeminiProviderConfig() 
    anthropic: AnthropicProviderConfig = AnthropicProviderConfig()
    
    # Default AI provider for content generation
    default_ai_provider: str = "openai"
    
    # Global settings
    enable_ai_content_generation: bool = True
    ai_content_cache_ttl: int = 3600  # Cache AI responses for 1 hour
    max_followup_count: int = Field(default=5, ge=1, le=10)
    
    @classmethod
    def from_env(cls) -> "ThirdPartyConfig":
        """Load configuration from environment variables"""
        
        config = cls()
        
        # OpenAI Configuration
        if os.getenv("OPENAI_API_KEY"):
            config.openai = OpenAIProviderConfig(
                enabled=True,
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
                max_retries=int(os.getenv("OPENAI_MAX_RETRIES", "3")),
                rate_limit_rpm=int(os.getenv("OPENAI_RATE_LIMIT_RPM", "3500")),
                default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4"),
                organization_id=os.getenv("OPENAI_ORGANIZATION_ID"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
            )
        
        # Gemini Configuration  
        if os.getenv("GEMINI_API_KEY"):
            config.gemini = GeminiProviderConfig(
                enabled=True,
                api_key=os.getenv("GEMINI_API_KEY"),
                base_url=os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1"),
                timeout=int(os.getenv("GEMINI_TIMEOUT", "30")),
                max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "3")),
                rate_limit_rpm=int(os.getenv("GEMINI_RATE_LIMIT_RPM", "60")),
                default_model=os.getenv("GEMINI_DEFAULT_MODEL", "gemini-pro")
            )
        
        # Anthropic Configuration
        if os.getenv("ANTHROPIC_API_KEY"):
            config.anthropic = AnthropicProviderConfig(
                enabled=True,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
                timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "30")),
                max_retries=int(os.getenv("ANTHROPIC_MAX_RETRIES", "3")),
                rate_limit_rpm=int(os.getenv("ANTHROPIC_RATE_LIMIT_RPM", "50")),
                default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-sonnet-20240229")
            )
        
        # Global settings
        config.default_ai_provider = os.getenv("DEFAULT_AI_PROVIDER", "openai")
        config.enable_ai_content_generation = os.getenv("ENABLE_AI_CONTENT_GENERATION", "true").lower() == "true"
        config.ai_content_cache_ttl = int(os.getenv("AI_CONTENT_CACHE_TTL", "3600"))
        config.max_followup_count = int(os.getenv("MAX_FOLLOWUP_COUNT", "5"))
        
        return config
    
    def get_enabled_ai_providers(self) -> Dict[str, AIProviderConfig]:
        """Get all enabled AI providers"""
        providers = {}
        
        if self.openai.enabled:
            providers["openai"] = self.openai
        if self.gemini.enabled:
            providers["gemini"] = self.gemini
        if self.anthropic.enabled:
            providers["anthropic"] = self.anthropic
            
        return providers
    
    def is_provider_enabled(self, provider: str) -> bool:
        """Check if a specific provider is enabled"""
        if provider == "openai":
            return self.openai.enabled
        elif provider == "gemini":
            return self.gemini.enabled
        elif provider == "anthropic":
            return self.anthropic.enabled
        return False

# Global configuration instance
third_party_config = ThirdPartyConfig.from_env()