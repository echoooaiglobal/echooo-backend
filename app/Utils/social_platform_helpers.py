# app/Utils/social_platform_helpers.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

class SocialPlatform(Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    TIKTOK = "tiktok"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"

class PlatformCapabilities:
    """Define capabilities for each social platform"""
    
    CAPABILITIES = {
        SocialPlatform.INSTAGRAM: {
            "messaging": True,
            "posting": True,
            "stories": True,
            "insights": True,
            "webhook_support": True,
            "automation_features": [
                "auto_reply", "scheduled_posts", "bulk_messaging",
                "follower_automation", "story_interactions", "comment_management"
            ],
            "rate_limits": {
                "messages_per_day": 100,
                "posts_per_day": 25,
                "api_calls_per_hour": 200
            },
            "supported_media": ["image", "video", "carousel"],
            "required_permissions": [
                "instagram_basic", "instagram_content_publish", 
                "instagram_manage_messages", "instagram_manage_insights"
            ]
        },
        SocialPlatform.FACEBOOK: {
            "messaging": True,
            "posting": True,
            "stories": False,
            "insights": True,
            "webhook_support": True,
            "automation_features": [
                "auto_reply", "scheduled_posts", "bulk_messaging",
                "page_management", "ad_management"
            ],
            "rate_limits": {
                "messages_per_day": 1000,
                "posts_per_day": 50,
                "api_calls_per_hour": 600
            },
            "supported_media": ["image", "video", "link", "text"],
            "required_permissions": [
                "pages_manage_posts", "pages_manage_engagement",
                "pages_messaging", "pages_read_engagement"
            ]
        },
        SocialPlatform.WHATSAPP: {
            "messaging": True,
            "posting": False,
            "stories": False,
            "insights": True,
            "webhook_support": True,
            "automation_features": [
                "auto_reply", "bulk_messaging", "template_messages",
                "broadcast_lists", "group_messaging"
            ],
            "rate_limits": {
                "messages_per_day": 1000,
                "template_messages_per_day": 250,
                "api_calls_per_hour": 80
            },
            "supported_media": ["text", "image", "video", "audio", "document"],
            "required_permissions": [
                "whatsapp_business_messaging", "whatsapp_business_management"
            ]
        },
        SocialPlatform.TIKTOK: {
            "messaging": False,
            "posting": True,
            "stories": False,
            "insights": True,
            "webhook_support": False,
            "automation_features": [
                "scheduled_posts", "bulk_upload", "hashtag_suggestions"
            ],
            "rate_limits": {
                "posts_per_day": 10,
                "api_calls_per_hour": 100
            },
            "supported_media": ["video"],
            "required_permissions": [
                "video.upload", "video.list", "user.info.basic"
            ]
        }
    }
    
    @classmethod
    def get_capabilities(cls, platform: SocialPlatform) -> Dict[str, Any]:
        """Get capabilities for a specific platform"""
        return cls.CAPABILITIES.get(platform, {})
    
    @classmethod
    def supports_feature(cls, platform: SocialPlatform, feature: str) -> bool:
        """Check if platform supports a specific feature"""
        capabilities = cls.get_capabilities(platform)
        return capabilities.get(feature, False)
    
    @classmethod
    def get_rate_limits(cls, platform: SocialPlatform) -> Dict[str, int]:
        """Get rate limits for a platform"""
        capabilities = cls.get_capabilities(platform)
        return capabilities.get("rate_limits", {})

class SocialMediaValidator:
    """Validation utilities for social media data"""
    
    @staticmethod
    def validate_username(username: str, platform: SocialPlatform) -> bool:
        """Validate username format for specific platform"""
        if not username:
            return False
        
        # Basic validation - extend based on platform requirements
        if platform == SocialPlatform.INSTAGRAM:
            return len(username) <= 30 and username.replace('_', '').replace('.', '').isalnum()
        elif platform == SocialPlatform.FACEBOOK:
            return len(username) >= 5 and len(username) <= 50
        elif platform == SocialPlatform.TIKTOK:
            return len(username) <= 24 and username.replace('_', '').replace('.', '').isalnum()
        
        return True
    
    @staticmethod
    def validate_message_content(content: str, platform: SocialPlatform) -> Dict[str, Any]:
        """Validate message content for platform requirements"""
        result = {"is_valid": True, "errors": [], "warnings": []}
        
        if not content:
            result["is_valid"] = False
            result["errors"].append("Message content cannot be empty")
            return result
        
        # Platform-specific validation
        if platform == SocialPlatform.INSTAGRAM:
            if len(content) > 2200:
                result["is_valid"] = False
                result["errors"].append("Instagram messages cannot exceed 2200 characters")
        elif platform == SocialPlatform.WHATSAPP:
            if len(content) > 4096:
                result["is_valid"] = False
                result["errors"].append("WhatsApp messages cannot exceed 4096 characters")
        elif platform == SocialPlatform.FACEBOOK:
            if len(content) > 63206:
                result["warnings"].append("Facebook posts over 63,206 characters may be truncated")
        
        return result

class RateLimitManager:
    """Manage rate limits for social media APIs"""
    
    def __init__(self):
        self.usage_cache = {}  # In production, use Redis or database
    
    def check_rate_limit(
        self, 
        connection_id: str, 
        platform: SocialPlatform, 
        action: str
    ) -> Dict[str, Any]:
        """Check if action is within rate limits"""
        
        limits = PlatformCapabilities.get_rate_limits(platform)
        if not limits:
            return {"allowed": True, "remaining": float('inf')}
        
        # Get current usage (simplified - in production, use proper storage)
        today = datetime.now().date()
        cache_key = f"{connection_id}:{platform.value}:{action}:{today}"
        
        current_usage = self.usage_cache.get(cache_key, 0)
        limit_key = f"{action}_per_day"
        
        if limit_key in limits:
            daily_limit = limits[limit_key]
            remaining = daily_limit - current_usage
            
            return {
                "allowed": remaining > 0,
                "remaining": max(0, remaining),
                "limit": daily_limit,
                "current_usage": current_usage,
                "reset_time": (datetime.combine(today, datetime.min.time()) + timedelta(days=1)).isoformat()
            }
        
        return {"allowed": True, "remaining": float('inf')}
    
    def record_usage(
        self, 
        connection_id: str, 
        platform: SocialPlatform, 
        action: str, 
        count: int = 1
    ):
        """Record API usage for rate limiting"""
        today = datetime.now().date()
        cache_key = f"{connection_id}:{platform.value}:{action}:{today}"
        
        current_usage = self.usage_cache.get(cache_key, 0)
        self.usage_cache[cache_key] = current_usage + count

class WebhookVerifier:
    """Utility for verifying webhooks from social platforms"""
    
    @staticmethod
    def verify_instagram_webhook(signature: str, payload: bytes, secret: str) -> bool:
        """Verify Instagram webhook signature"""
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures securely
        return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    @staticmethod
    def verify_facebook_webhook(signature: str, payload: bytes, secret: str) -> bool:
        """Verify Facebook webhook signature"""
        return WebhookVerifier.verify_instagram_webhook(signature, payload, secret)
    
    @staticmethod
    def verify_whatsapp_webhook(signature: str, payload: bytes, secret: str) -> bool:
        """Verify WhatsApp webhook signature"""
        return WebhookVerifier.verify_instagram_webhook(signature, payload, secret)