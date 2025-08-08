# app/Services/ThirdParty/providers/openai/client.py

from typing import Dict, Any, List, Optional
from ...base import BaseAPIClient
from ...exceptions import (
    APIAuthenticationError, APIRateLimitError, APIValidationError, 
    APIQuotaExceededError, APIParsingError
)
from .models import ChatCompletionRequest, ChatCompletionResponse
from .config import OpenAIConfig

class OpenAIClient(BaseAPIClient):
    """Professional OpenAI API client"""
    
    def __init__(self, config: OpenAIConfig):
        super().__init__(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay
        )
        self.config = config
    
    @property
    def provider_name(self) -> str:
        return "OpenAI"
    
    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"InfluencerPlatform/1.0"
        }
    
    def _handle_api_error(self, status_code: int, response_data: Dict[str, Any]) -> None:
        """Handle OpenAI specific errors"""
        error_info = response_data.get("error", {})
        error_message = error_info.get("message", "Unknown error")
        error_code = error_info.get("code")
        
        if status_code == 401:
            raise APIAuthenticationError(
                f"Authentication failed: {error_message}",
                self.provider_name,
                status_code,
                error_code
            )
        elif status_code == 429:
            raise APIRateLimitError(
                f"Rate limit exceeded: {error_message}",
                self.provider_name,
                status_code,
                error_code
            )
        elif status_code == 400:
            raise APIValidationError(
                f"Invalid request: {error_message}",
                self.provider_name,
                status_code,
                error_code
            )
        elif status_code == 402:
            raise APIQuotaExceededError(
                f"Quota exceeded: {error_message}",
                self.provider_name,
                status_code,
                error_code
            )
    
    async def create_chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        """Create chat completion"""
        try:
            response_data = await self.post(
                "chat/completions",
                request.model_dump(exclude_none=True)
            )
            
            # Validate and parse response
            if "choices" not in response_data:
                raise APIParsingError(
                    "Invalid response format: missing 'choices'",
                    self.provider_name,
                    details=response_data
                )
            
            return ChatCompletionResponse.model_validate(response_data)
            
        except Exception as e:
            if isinstance(e, (APIAuthenticationError, APIRateLimitError, APIValidationError, APIQuotaExceededError)):
                raise
            raise APIParsingError(
                f"Failed to process response: {str(e)}",
                self.provider_name,
                details={"original_error": str(e)}
            )