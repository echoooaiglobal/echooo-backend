# app/Services/ThirdParty/registry.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ProviderType(str, Enum):
    AI_CONTENT = "ai_content"
    PAYMENT = "payment"  
    ANALYTICS = "analytics"
    NOTIFICATION = "notification"
    SOCIAL_MEDIA = "social_media"

@dataclass
class ProviderInfo:
    """Information about a third-party provider"""
    name: str
    type: ProviderType
    client_class: str
    config_class: str
    is_enabled: bool
    description: str
    features: List[str]
    rate_limits: Optional[Dict[str, Any]] = None

class ThirdPartyRegistry:
    """Registry for all third-party service providers"""
    
    def __init__(self):
        self._providers: Dict[str, ProviderInfo] = {}
        self._initialize_default_providers()
    
    def _initialize_default_providers(self):
        """Initialize default providers"""
        
        # AI Content Providers
        self.register(ProviderInfo(
            name="openai",
            type=ProviderType.AI_CONTENT,
            client_class="app.Services.ThirdParty.providers.openai.client.OpenAIClient",
            config_class="app.Services.ThirdParty.providers.openai.config.OpenAIConfig",
            is_enabled=True,
            description="OpenAI GPT models for content generation",
            features=["chat_completion", "text_generation", "code_generation"],
            rate_limits={"requests_per_minute": 3500, "tokens_per_minute": 90000}
        ))
        
        self.register(ProviderInfo(
            name="gemini",
            type=ProviderType.AI_CONTENT,
            client_class="app.Services.ThirdParty.providers.gemini.client.GeminiClient",
            config_class="app.Services.ThirdParty.providers.gemini.config.GeminiConfig",
            is_enabled=True,
            description="Google Gemini models for content generation",
            features=["content_generation", "text_analysis"],
            rate_limits={"requests_per_minute": 60}
        ))
    
    def register(self, provider_info: ProviderInfo):
        """Register a new provider"""
        self._providers[provider_info.name] = provider_info
        logger.info(f"Registered provider: {provider_info.name} ({provider_info.type})")
    
    def get_provider(self, name: str) -> Optional[ProviderInfo]:
        """Get provider information by name"""
        return self._providers.get(name)
    
    def get_providers_by_type(self, provider_type: ProviderType) -> List[ProviderInfo]:
        """Get all providers of a specific type"""
        return [
            provider for provider in self._providers.values()
            if provider.type == provider_type and provider.is_enabled
        ]
    
    def list_all_providers(self) -> Dict[str, ProviderInfo]:
        """List all registered providers"""
        return self._providers.copy()
    
    def enable_provider(self, name: str):
        """Enable a provider"""
        if name in self._providers:
            self._providers[name].is_enabled = True
            logger.info(f"Enabled provider: {name}")
    
    def disable_provider(self, name: str):
        """Disable a provider"""
        if name in self._providers:
            self._providers[name].is_enabled = False
            logger.info(f"Disabled provider: {name}")
    
    def get_enabled_ai_providers(self) -> List[str]:
        """Get list of enabled AI providers"""
        ai_providers = self.get_providers_by_type(ProviderType.AI_CONTENT)
        return [provider.name for provider in ai_providers]

# Global registry instance
registry = ThirdPartyRegistry()