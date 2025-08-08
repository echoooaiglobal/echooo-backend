# app/Services/ThirdParty/factory.py

from typing import Dict, Type, Optional, Union, List
from enum import Enum
import logging

from .base import BaseAPIClient
from .providers.openai.client import OpenAIClient
from .providers.openai.config import OpenAIConfig
from .providers.gemini.client import GeminiClient
from .providers.gemini.config import GeminiConfig
from .exceptions import ThirdPartyAPIError

logger = logging.getLogger(__name__)

class ProviderType(str, Enum):
    AI_CONTENT = "ai_content"
    PAYMENT = "payment"  
    ANALYTICS = "analytics"
    NOTIFICATION = "notification"
    SOCIAL_MEDIA = "social_media"

class AIProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"

class AIProviderFactory:
    """Factory for creating AI provider clients"""
    
    _providers: Dict[AIProviderName, Type[BaseAPIClient]] = {
        AIProviderName.OPENAI: OpenAIClient,
        AIProviderName.GEMINI: GeminiClient,
    }
    
    _configs = {
        AIProviderName.OPENAI: OpenAIConfig,
        AIProviderName.GEMINI: GeminiConfig,
    }
    
    @classmethod
    def register_provider(
        cls, 
        name: AIProviderName, 
        client_class: Type[BaseAPIClient],
        config_class: Type
    ):
        """Register a new AI provider"""
        cls._providers[name] = client_class
        cls._configs[name] = config_class
        logger.info(f"Registered AI provider: {name}")
    
    @classmethod
    def create_client(cls, provider: Union[AIProviderName, str]) -> BaseAPIClient:
        """Create an AI provider client"""
        
        if isinstance(provider, str):
            try:
                provider = AIProviderName(provider)
            except ValueError:
                raise ValueError(f"Unknown AI provider: {provider}")
        
        if provider not in cls._providers:
            raise ValueError(f"AI provider {provider} is not registered")
        
        try:
            # Get config and client classes
            config_class = cls._configs[provider]
            client_class = cls._providers[provider]
            
            # Create config from environment
            config = config_class.from_env()
            
            # Create and return client
            client = client_class(config)
            logger.info(f"Created {provider} client")
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create {provider} client: {str(e)}")
            raise ThirdPartyAPIError(
                f"Failed to initialize {provider} client: {str(e)}",
                str(provider)
            )
    
    @classmethod
    def get_available_providers(cls) -> List[AIProviderName]:
        """Get list of available AI providers"""
        return list(cls._providers.keys())
    
    @classmethod
    def is_provider_available(cls, provider: Union[AIProviderName, str]) -> bool:
        """Check if a provider is available and configured"""
        
        if isinstance(provider, str):
            try:
                provider = AIProviderName(provider)
            except ValueError:
                return False
        
        if provider not in cls._providers:
            return False
        
        try:
            # Try to create config to see if it's properly configured
            config_class = cls._configs[provider]
            config_class.from_env()
            return True
        except Exception:
            return False