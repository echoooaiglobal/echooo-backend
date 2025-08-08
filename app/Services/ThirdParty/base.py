# app/Services/ThirdParty/base.py

import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta

from .exceptions import (
    APIConnectionError, APIAuthenticationError, APIRateLimitError,
    APITimeoutError, APIValidationError, ThirdPartyAPIError
)

logger = logging.getLogger(__name__)

class BaseAPIClient(ABC):
    """Base class for all third-party API clients"""
    
    def __init__(
        self, 
        base_url: str,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 1
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self.last_request_time: Optional[datetime] = None
        self.min_request_interval = 0.1  # Minimum seconds between requests
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the API provider"""
        pass
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_session()
    
    async def _create_session(self):
        """Create aiohttp session"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._get_default_headers()
            )
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @abstractmethod
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests"""
        pass
    
    @abstractmethod
    def _handle_api_error(self, status_code: int, response_data: Dict[str, Any]) -> None:
        """Handle API-specific errors"""
        pass
    
    async def _rate_limit(self):
        """Simple rate limiting"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = datetime.now()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        
        if not self.session:
            await self._create_session()
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Rate limiting
                await self._rate_limit()
                
                # Log request
                logger.info(f"{self.provider_name}: {method} {url} (attempt {attempt + 1})")
                
                async with self.session.request(
                    method=method,
                    url=url,
                    json=data if method in ['POST', 'PUT', 'PATCH'] else None,
                    params=params,
                    headers=request_headers
                ) as response:
                    
                    # Get response data
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_data = {"text": await response.text()}
                    
                    # Handle success
                    if response.status == 200:
                        logger.info(f"{self.provider_name}: Request successful")
                        return response_data
                    
                    # Handle API errors
                    self._handle_api_error(response.status, response_data)
                    
                    # If we get here, it's an unhandled error
                    raise ThirdPartyAPIError(
                        f"API request failed with status {response.status}",
                        self.provider_name,
                        response.status,
                        details=response_data
                    )
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = APIConnectionError(
                    f"Connection error: {str(e)}", 
                    self.provider_name
                )
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"{self.provider_name}: Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                    
            except ThirdPartyAPIError:
                # Don't retry on authentication, validation, or quota errors
                raise
                
        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise ThirdPartyAPIError(f"Max retries exceeded", self.provider_name)

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request"""
        return await self._make_request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request"""
        return await self._make_request("POST", endpoint, data=data)
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request"""
        return await self._make_request("PUT", endpoint, data=data)
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request"""
        return await self._make_request("DELETE", endpoint)