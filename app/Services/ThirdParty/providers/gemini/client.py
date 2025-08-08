# app/Services/ThirdParty/providers/gemini/client.py

from typing import Dict, Any, List, Optional
from ...base import BaseAPIClient
from ...exceptions import (
    APIAuthenticationError, APIRateLimitError, APIValidationError,
    APIParsingError
)
from .models import GenerateContentRequest, GenerateContentResponse
from .config import GeminiConfig

class GeminiClient(BaseAPIClient):
    """Professional Gemini API client"""
    
    def __init__(self, config: GeminiConfig):
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
        return "Gemini"
    
    def _get_default_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "User-Agent": "InfluencerPlatform/1.0"
        }
    
    def _handle_api_error(self, status_code: int, response_data: Dict[str, Any]) -> None:
        """Handle Gemini specific errors"""
        error_info = response_data.get("error", {})
        error_message = error_info.get("message", "Unknown error")
        error_code = error_info.get("code")
        
        if status_code == 401 or status_code == 403:
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
    
    async def generate_content(self, request: GenerateContentRequest) -> GenerateContentResponse:
        """Generate content using Gemini"""
        try:
            # Gemini uses API key as query parameter
            endpoint = f"models/{request.model}:generateContent?key={self.api_key}"
            
            response_data = await self.post(
                endpoint,
                request.model_dump(exclude={"model"}, exclude_none=True)
            )
            
            # Validate response
            if "candidates" not in response_data:
                raise APIParsingError(
                    "Invalid response format: missing 'candidates'",
                    self.provider_name,
                    details=response_data
                )
            
            return GenerateContentResponse.model_validate(response_data)
            
        except Exception as e:
            if isinstance(e, (APIAuthenticationError, APIRateLimitError, APIValidationError)):
                raise
            raise APIParsingError(
                f"Failed to process response: {str(e)}",
                self.provider_name,
                details={"original_error": str(e)}
            )