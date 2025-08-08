# app/Services/ThirdParty/providers/openai/exceptions.py

from ...exceptions import ThirdPartyAPIError

class OpenAIError(ThirdPartyAPIError):
    """Base OpenAI error"""
    pass

class OpenAIContentFilterError(OpenAIError):
    """Content was filtered by OpenAI"""
    pass

class OpenAIModelNotAvailableError(OpenAIError):
    """Requested model is not available"""
    pass