# app/Services/ThirdParty/exceptions.py

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ThirdPartyAPIError(Exception):
    """Base exception for all third-party API errors"""
    
    def __init__(
        self, 
        message: str, 
        provider: str, 
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.provider = provider
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        
        super().__init__(self.message)
        
        # Log the error
        logger.error(f"{provider} API Error: {message}", extra={
            'provider': provider,
            'status_code': status_code,
            'error_code': error_code,
            'details': details
        })

class APIConnectionError(ThirdPartyAPIError):
    """Network/connection related errors"""
    pass

class APIAuthenticationError(ThirdPartyAPIError):
    """Authentication/authorization errors"""
    pass

class APIRateLimitError(ThirdPartyAPIError):
    """Rate limit exceeded errors"""
    pass

class APIValidationError(ThirdPartyAPIError):
    """Request validation errors"""
    pass

class APIQuotaExceededError(ThirdPartyAPIError):
    """Quota/usage limit exceeded"""
    pass

class APITimeoutError(ThirdPartyAPIError):
    """Request timeout errors"""
    pass

class APIParsingError(ThirdPartyAPIError):
    """Response parsing errors"""
    pass