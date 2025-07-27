# app/Utils/social_media_errors.py
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

class SocialMediaError(Exception):
    """Base exception for social media integration errors"""
    def __init__(self, message: str, platform: str, error_code: Optional[str] = None):
        self.message = message
        self.platform = platform
        self.error_code = error_code
        super().__init__(self.message)

class TokenExpiredError(SocialMediaError):
    """OAuth token has expired"""
    pass

class RateLimitExceededError(SocialMediaError):
    """API rate limit exceeded"""
    def __init__(self, message: str, platform: str, retry_after: Optional[int] = None):
        super().__init__(message, platform)
        self.retry_after = retry_after

class PlatformAPIError(SocialMediaError):
    """General platform API error"""
    def __init__(self, message: str, platform: str, status_code: int, response_data: Optional[Dict] = None):
        super().__init__(message, platform)
        self.status_code = status_code
        self.response_data = response_data

class InsufficientPermissionsError(SocialMediaError):
    """User hasn't granted required permissions"""
    def __init__(self, message: str, platform: str, required_permissions: list):
        super().__init__(message, platform)
        self.required_permissions = required_permissions

def handle_social_media_error(error: Exception, platform: str) -> HTTPException:
    """Convert social media errors to HTTP exceptions"""
    
    if isinstance(error, TokenExpiredError):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "token_expired",
                "message": error.message,
                "platform": error.platform,
                "action_required": "refresh_token"
            }
        )
    
    elif isinstance(error, RateLimitExceededError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": error.message,
                "platform": error.platform,
                "retry_after": error.retry_after
            }
        )
    
    elif isinstance(error, InsufficientPermissionsError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": error.message,
                "platform": error.platform,
                "required_permissions": error.required_permissions
            }
        )
    
    elif isinstance(error, PlatformAPIError):
        return HTTPException(
            status_code=error.status_code,
            detail={
                "error": "platform_api_error",
                "message": error.message,
                "platform": error.platform,
                "platform_error_code": error.error_code,
                "platform_response": error.response_data
            }
        )
    
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "unknown_error",
                "message": str(error),
                "platform": platform
            }
        )