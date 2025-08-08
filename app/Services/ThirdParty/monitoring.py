# app/Services/ThirdParty/monitoring.py

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from .factory import AIProviderFactory
from .exceptions import ThirdPartyAPIError

logger = logging.getLogger(__name__)

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class ProviderHealth:
    """Health status for a provider"""
    provider: str
    status: HealthStatus
    response_time_ms: Optional[float] = None
    last_checked: Optional[datetime] = None
    error_message: Optional[str] = None
    success_rate_24h: Optional[float] = None
    
@dataclass
class APIMetrics:
    """Metrics for API usage"""
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0
    rate_limit_hits: int = 0
    last_request: Optional[datetime] = None
    requests_by_hour: Dict[int, int] = field(default_factory=dict)

class ProviderMonitor:
    """Monitor third-party provider health and metrics"""
    
    def __init__(self):
        self.health_status: Dict[str, ProviderHealth] = {}
        self.metrics: Dict[str, APIMetrics] = {}
        self.factory = AIProviderFactory()
        
    async def check_provider_health(self, provider: str) -> ProviderHealth:
        """Check health of a specific provider"""
        
        start_time = time.time()
        health = ProviderHealth(provider=provider, status=HealthStatus.UNKNOWN)
        
        try:
            if not self.factory.is_provider_available(provider):
                health.status = HealthStatus.UNHEALTHY
                health.error_message = f"Provider {provider} not configured"
                return health
            
            # Create client and test with simple request
            client = self.factory.create_client(provider)
            
            async with client:
                # Test request based on provider
                if provider == "openai":
                    await self._test_openai_health(client)
                elif provider == "gemini":
                    await self._test_gemini_health(client)
                
                response_time = (time.time() - start_time) * 1000
                health.response_time_ms = response_time
                health.status = HealthStatus.HEALTHY
                health.last_checked = datetime.utcnow()
                
                # Determine status based on response time
                if response_time > 10000:  # 10 seconds
                    health.status = HealthStatus.DEGRADED
                    
        except Exception as e:
            health.status = HealthStatus.UNHEALTHY
            health.error_message = str(e)
            health.last_checked = datetime.utcnow()
            
            logger.warning(f"Health check failed for {provider}: {str(e)}")
        
        self.health_status[provider] = health
        return health
    
    async def _test_openai_health(self, client):
        """Test OpenAI API health"""
        from .providers.openai.models import ChatCompletionRequest, ChatMessage
        
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",  # Use cheaper model for health checks
            messages=[ChatMessage(role="user", content="Hello")],
            max_tokens=1
        )
        await client.create_chat_completion(request)
    
    async def _test_gemini_health(self, client):
        """Test Gemini API health"""
        from .providers.gemini.models import GenerateContentRequest, Content, ContentPart
        
        request = GenerateContentRequest(
            contents=[Content(parts=[ContentPart(text="Hello")])]
        )
        await client.generate_content(request)
    
    async def check_all_providers_health(self) -> Dict[str, ProviderHealth]:
        """Check health of all available providers"""
        
        available_providers = self.factory.get_available_providers()
        
        # Run health checks concurrently
        tasks = [
            self.check_provider_health(str(provider)) 
            for provider in available_providers
        ]
        
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(health_results):
            provider = str(available_providers[i])
            
            if isinstance(result, Exception):
                self.health_status[provider] = ProviderHealth(
                    provider=provider,
                    status=HealthStatus.UNHEALTHY,
                    error_message=str(result),
                    last_checked=datetime.utcnow()
                )
            else:
                self.health_status[provider] = result
        
        return self.health_status
    
    def record_api_call(
        self, 
        provider: str, 
        success: bool, 
        response_time: float,
        tokens_used: int = 0,
        cost: float = 0.0,
        rate_limited: bool = False
    ):
        """Record metrics for an API call"""
        
        if provider not in self.metrics:
            self.metrics[provider] = APIMetrics(provider=provider)
        
        metrics = self.metrics[provider]
        metrics.total_requests += 1
        metrics.last_request = datetime.utcnow()
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        if rate_limited:
            metrics.rate_limit_hits += 1
        
        metrics.total_tokens += tokens_used
        metrics.total_cost += cost
        
        # Update average response time
        if metrics.total_requests > 0:
            metrics.avg_response_time = (
                (metrics.avg_response_time * (metrics.total_requests - 1) + response_time) / 
                metrics.total_requests
            )
        
        # Track requests by hour
        current_hour = datetime.utcnow().hour
        if current_hour not in metrics.requests_by_hour:
            metrics.requests_by_hour[current_hour] = 0
        metrics.requests_by_hour[current_hour] += 1
    
    def get_provider_metrics(self, provider: str) -> Optional[APIMetrics]:
        """Get metrics for a specific provider"""
        return self.metrics.get(provider)
    
    def get_all_metrics(self) -> Dict[str, APIMetrics]:
        """Get metrics for all providers"""
        return self.metrics.copy()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary"""
        
        total_providers = len(self.health_status)
        healthy_providers = sum(1 for h in self.health_status.values() if h.status == HealthStatus.HEALTHY)
        degraded_providers = sum(1 for h in self.health_status.values() if h.status == HealthStatus.DEGRADED)
        unhealthy_providers = sum(1 for h in self.health_status.values() if h.status == HealthStatus.UNHEALTHY)
        
        overall_status = HealthStatus.HEALTHY
        if unhealthy_providers > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_providers > 0:
            overall_status = HealthStatus.DEGRADED
        
        return {
            "overall_status": overall_status,
            "total_providers": total_providers,
            "healthy_providers": healthy_providers,
            "degraded_providers": degraded_providers,
            "unhealthy_providers": unhealthy_providers,
            "last_check": max([h.last_checked for h in self.health_status.values() if h.last_checked], default=None),
            "provider_details": {
                name: {
                    "status": health.status,
                    "response_time_ms": health.response_time_ms,
                    "error": health.error_message
                }
                for name, health in self.health_status.items()
            }
        }

# Global monitor instance
monitor = ProviderMonitor()

# Health check endpoint for routes
# routes/api/v0/health.py

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.Services.ThirdParty.monitoring import monitor

router = APIRouter(prefix="/health", tags=["Health Checks"])

@router.get("/third-party")
async def check_third_party_health() -> Dict[str, Any]:
    """Check health of all third-party providers"""
    await monitor.check_all_providers_health()
    return monitor.get_health_summary()

@router.get("/third-party/{provider}")
async def check_provider_health(provider: str):
    """Check health of a specific provider"""
    health = await monitor.check_provider_health(provider)
    return {
        "provider": provider,
        "status": health.status,
        "response_time_ms": health.response_time_ms,
        "last_checked": health.last_checked,
        "error": health.error_message
    }

@router.get("/metrics")
async def get_api_metrics() -> Dict[str, Any]:
    """Get API usage metrics"""
    return {
        "providers": monitor.get_all_metrics(),
        "summary": {
            "total_providers": len(monitor.metrics),
            "total_requests": sum(m.total_requests for m in monitor.metrics.values()),
            "total_cost": sum(m.total_cost for m in monitor.metrics.values()),
            "total_tokens": sum(m.total_tokens for m in monitor.metrics.values())
        }
    }

@router.get("/metrics/{provider}")
async def get_provider_metrics(provider: str):
    """Get metrics for a specific provider"""
    metrics = monitor.get_provider_metrics(provider)
    if not metrics:
        return {"error": f"No metrics found for provider {provider}"}
    
    return {
        "provider": provider,
        "total_requests": metrics.total_requests,
        "success_rate": metrics.successful_requests / max(metrics.total_requests, 1),
        "avg_response_time": metrics.avg_response_time,
        "total_cost": metrics.total_cost,
        "total_tokens": metrics.total_tokens,
        "rate_limit_hits": metrics.rate_limit_hits,
        "last_request": metrics.last_request,
        "hourly_requests": metrics.requests_by_hour
    }