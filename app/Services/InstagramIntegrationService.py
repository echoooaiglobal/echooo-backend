# app/Services/InstagramIntegrationService.py
import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.Models.agent_social_connections import AgentSocialConnection
from app.Models.auth_models import User
from app.Services.OAuthService import OAuthService
from app.Utils.Logger import logger
from app.Utils.encryption import decrypt_token
from config.settings import settings

class InstagramIntegrationService:
    """Service for Instagram Business API integration"""
    
    def __init__(self):
        self.oauth_service = OAuthService()
        self.graph_api_url = "https://graph.facebook.com/v19.0"
        self.instagram_api_url = "https://graph.instagram.com/v19.0"
        
    async def get_instagram_profile_info(
        self, 
        connection: AgentSocialConnection,
        db: Session
    ) -> Dict[str, Any]:
        """Get Instagram profile information"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            # Get basic profile info
            profile_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}"
            params = {
                "fields": "account_type,id,media_count,followers_count,follows_count,name,username,profile_picture_url,biography,website",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(profile_url, params=params)
                response.raise_for_status()
                
            profile_data = response.json()
            
            return {
                "instagram_account_id": profile_data.get("id"),
                "username": profile_data.get("username"),
                "name": profile_data.get("name"),
                "biography": profile_data.get("biography"),
                "followers_count": profile_data.get("followers_count", 0),
                "follows_count": profile_data.get("follows_count", 0),
                "media_count": profile_data.get("media_count", 0),
                "profile_picture_url": profile_data.get("profile_picture_url"),
                "website": profile_data.get("website"),
                "account_type": profile_data.get("account_type"),
                "is_business_account": profile_data.get("account_type") == "BUSINESS",
                "is_professional_account": profile_data.get("account_type") in ["BUSINESS", "CREATOR"]
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Instagram profile: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get Instagram profile: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error getting Instagram profile: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Instagram profile information"
            )

    async def get_instagram_conversations(
        self,
        connection: AgentSocialConnection,
        limit: int = 25,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get Instagram direct message conversations"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            conversations_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}/conversations"
            params = {
                "platform": "instagram",
                "limit": limit,
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(conversations_url, params=params)
                response.raise_for_status()
                
            data = response.json()
            conversations = []
            
            for conversation in data.get("data", []):
                # Get conversation details with participants
                conv_details = await self._get_conversation_details(
                    conversation["id"], access_token
                )
                conversations.append(conv_details)
            
            return conversations
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Instagram conversations: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get Instagram conversations: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error getting Instagram conversations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Instagram conversations"
            )

    async def get_conversation_messages(
        self,
        connection: AgentSocialConnection,
        conversation_id: str,
        limit: int = 25,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a specific Instagram conversation"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            messages_url = f"{self.instagram_api_url}/{conversation_id}/messages"
            params = {
                "fields": "id,created_time,from,to,message,attachments",
                "limit": limit,
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(messages_url, params=params)
                response.raise_for_status()
                
            data = response.json()
            messages = []
            
            for message in data.get("data", []):
                formatted_message = {
                    "id": message.get("id"),
                    "created_time": message.get("created_time"),
                    "from_id": message.get("from", {}).get("id"),
                    "from_username": message.get("from", {}).get("username"),
                    "to_id": message.get("to", {}).get("id"),
                    "to_username": message.get("to", {}).get("username"),
                    "message": message.get("message"),
                    "attachments": message.get("attachments", [])
                }
                messages.append(formatted_message)
            
            return messages
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Instagram messages: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get Instagram messages: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error getting Instagram messages: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Instagram messages"
            )

    async def send_instagram_message(
        self,
        connection: AgentSocialConnection,
        recipient_id: str,
        message_text: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """Send a direct message on Instagram"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            messages_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}/messages"
            
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": message_text},
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(messages_url, json=payload)
                response.raise_for_status()
                
            result = response.json()
            
            # Update connection last use
            connection.last_automation_use_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Sent Instagram message from {connection.platform_username} to {recipient_id}")
            
            return {
                "message_id": result.get("id"),
                "sent_at": datetime.utcnow().isoformat(),
                "recipient_id": recipient_id,
                "message_text": message_text,
                "status": "sent"
            }
            
        except httpx.HTTPStatusError as e:
            # Update error count
            connection.automation_error_count += 1
            connection.last_error_message = f"Failed to send message: {e.response.text}"
            connection.last_error_at = datetime.utcnow()
            db.commit()
            
            logger.error(f"HTTP error sending Instagram message: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to send Instagram message: {e.response.text}"
            )
        except Exception as e:
            # Update error count
            connection.automation_error_count += 1
            connection.last_error_message = f"Failed to send message: {str(e)}"
            connection.last_error_at = datetime.utcnow()
            db.commit()
            
            logger.error(f"Error sending Instagram message: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send Instagram message"
            )

    async def get_instagram_media(
        self,
        connection: AgentSocialConnection,
        limit: int = 25,
        media_type: Optional[str] = None,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get Instagram media posts"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            media_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}/media"
            params = {
                "fields": "id,media_type,media_url,thumbnail_url,permalink,caption,timestamp,like_count,comments_count",
                "limit": limit,
                "access_token": access_token
            }
            
            if media_type:
                params["media_type"] = media_type
            
            async with httpx.AsyncClient() as client:
                response = await client.get(media_url, params=params)
                response.raise_for_status()
                
            data = response.json()
            media_posts = []
            
            for post in data.get("data", []):
                formatted_post = {
                    "id": post.get("id"),
                    "media_type": post.get("media_type"),
                    "media_url": post.get("media_url"),
                    "thumbnail_url": post.get("thumbnail_url"),
                    "permalink": post.get("permalink"),
                    "caption": post.get("caption"),
                    "timestamp": post.get("timestamp"),
                    "like_count": post.get("like_count", 0),
                    "comments_count": post.get("comments_count", 0)
                }
                media_posts.append(formatted_post)
            
            return media_posts
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Instagram media: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get Instagram media: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error getting Instagram media: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Instagram media"
            )

    async def post_instagram_media(
        self,
        connection: AgentSocialConnection,
        image_url: str,
        caption: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Post media to Instagram"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            # Step 1: Create media container
            container_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}/media"
            container_payload = {
                "image_url": image_url,
                "caption": caption or "",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                container_response = await client.post(container_url, json=container_payload)
                container_response.raise_for_status()
                
            container_data = container_response.json()
            creation_id = container_data.get("id")
            
            # Step 2: Publish the media
            publish_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}/media_publish"
            publish_payload = {
                "creation_id": creation_id,
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                publish_response = await client.post(publish_url, json=publish_payload)
                publish_response.raise_for_status()
                
            publish_data = publish_response.json()
            
            # Update connection last use
            connection.last_automation_use_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Posted Instagram media from {connection.platform_username}")
            
            return {
                "media_id": publish_data.get("id"),
                "creation_id": creation_id,
                "posted_at": datetime.utcnow().isoformat(),
                "status": "published",
                "caption": caption,
                "image_url": image_url
            }
            
        except httpx.HTTPStatusError as e:
            # Update error count
            connection.automation_error_count += 1
            connection.last_error_message = f"Failed to post media: {e.response.text}"
            connection.last_error_at = datetime.utcnow()
            db.commit()
            
            logger.error(f"HTTP error posting Instagram media: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to post Instagram media: {e.response.text}"
            )
        except Exception as e:
            # Update error count
            connection.automation_error_count += 1
            connection.last_error_message = f"Failed to post media: {str(e)}"
            connection.last_error_at = datetime.utcnow()
            db.commit()
            
            logger.error(f"Error posting Instagram media: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to post Instagram media"
            )

    async def get_instagram_insights(
        self,
        connection: AgentSocialConnection,
        metrics: List[str] = None,
        period: str = "day",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get Instagram account insights and analytics"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            # Default metrics for account insights
            if not metrics:
                metrics = [
                    "follower_count",
                    "impressions",
                    "reach",
                    "profile_views",
                    "website_clicks"
                ]
            
            insights_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}/insights"
            params = {
                "metric": ",".join(metrics),
                "period": period,
                "access_token": access_token
            }
            
            if since:
                params["since"] = int(since.timestamp())
            if until:
                params["until"] = int(until.timestamp())
            
            async with httpx.AsyncClient() as client:
                response = await client.get(insights_url, params=params)
                response.raise_for_status()
                
            data = response.json()
            
            # Format insights data
            insights = {}
            for insight in data.get("data", []):
                metric_name = insight.get("name")
                values = insight.get("values", [])
                insights[metric_name] = {
                    "title": insight.get("title"),
                    "description": insight.get("description"),
                    "values": values,
                    "period": insight.get("period")
                }
            
            return {
                "account_id": connection.instagram_business_account_id,
                "insights": insights,
                "period": period,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Instagram insights: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get Instagram insights: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error getting Instagram insights: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Instagram insights"
            )

    async def _get_conversation_details(
        self, 
        conversation_id: str, 
        access_token: str
    ) -> Dict[str, Any]:
        """Get detailed information about a conversation"""
        try:
            conversation_url = f"{self.instagram_api_url}/{conversation_id}"
            params = {
                "fields": "id,updated_time,can_reply,message_count,unread_count,participants",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(conversation_url, params=params)
                response.raise_for_status()
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting conversation details: {str(e)}")
            return {
                "id": conversation_id,
                "error": "Failed to get conversation details"
            }

    async def validate_instagram_connection(
        self,
        connection: AgentSocialConnection,
        db: Session
    ) -> Dict[str, Any]:
        """Validate Instagram connection and token"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            # Test connection with basic profile request
            test_url = f"{self.instagram_api_url}/{connection.instagram_business_account_id}"
            params = {
                "fields": "id,username",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(test_url, params=params)
                response.raise_for_status()
                
            data = response.json()
            
            # Update last check time
            connection.last_oauth_check_at = datetime.utcnow()
            connection.automation_error_count = 0  # Reset error count on successful validation
            db.commit()
            
            return {
                "is_valid": True,
                "account_id": data.get("id"),
                "username": data.get("username"),
                "last_check": connection.last_oauth_check_at.isoformat(),
                "message": "Connection is valid"
            }
            
        except httpx.HTTPStatusError as e:
            # Update error information
            connection.automation_error_count += 1
            connection.last_error_message = f"Connection validation failed: {e.response.text}"
            connection.last_error_at = datetime.utcnow()
            db.commit()
            
            return {
                "is_valid": False,
                "error_code": e.response.status_code,
                "error_message": e.response.text,
                "last_check": datetime.utcnow().isoformat(),
                "message": "Connection validation failed"
            }
        except Exception as e:
            # Update error information
            connection.automation_error_count += 1
            connection.last_error_message = f"Connection validation failed: {str(e)}"
            connection.last_error_at = datetime.utcnow()
            db.commit()
            
            return {
                "is_valid": False,
                "error_message": str(e),
                "last_check": datetime.utcnow().isoformat(),
                "message": "Connection validation failed"
            }

    async def setup_instagram_webhooks(
        self,
        connection: AgentSocialConnection,
        webhook_url: str,
        db: Session
    ) -> Dict[str, Any]:
        """Setup webhooks for Instagram to receive real-time updates"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            # Subscribe to Instagram webhooks
            webhook_subscription_url = f"{self.graph_api_url}/{settings.FACEBOOK_APP_ID}/subscriptions"
            
            payload = {
                "object": "instagram",
                "callback_url": webhook_url,
                "fields": "messages,messaging_seen,messaging_postbacks",
                "verify_token": settings.WEBHOOK_VERIFY_TOKEN,
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(webhook_subscription_url, json=payload)
                response.raise_for_status()
                
            result = response.json()
            
            # Update connection with webhook information
            if not connection.additional_data:
                connection.additional_data = {}
            
            connection.additional_data["webhook_subscribed"] = True
            connection.additional_data["webhook_url"] = webhook_url
            connection.additional_data["webhook_setup_at"] = datetime.utcnow().isoformat()
            
            db.commit()
            
            logger.info(f"Setup Instagram webhooks for {connection.platform_username}")
            
            return {
                "success": result.get("success", False),
                "webhook_url": webhook_url,
                "subscribed_fields": ["messages", "messaging_seen", "messaging_postbacks"],
                "setup_at": datetime.utcnow().isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error setting up Instagram webhooks: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to setup Instagram webhooks: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error setting up Instagram webhooks: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to setup Instagram webhooks"
            )

    async def get_instagram_automation_capabilities(
        self,
        connection: AgentSocialConnection
    ) -> Dict[str, Any]:
        """Get automation capabilities for Instagram connection"""
        
        # Check if this is a business account
        is_business = connection.instagram_business_account_id is not None
        
        # Basic capabilities available to all accounts
        capabilities = {
            "can_send_messages": is_business,
            "can_receive_messages": is_business,
            "can_post_media": is_business,
            "can_get_insights": is_business,
            "can_manage_comments": is_business,
            "can_view_profile": True,
            "can_get_media": True,
            "daily_limits": {
                "messages": 100 if is_business else 0,
                "posts": 25 if is_business else 0,
                "api_calls": 200 if is_business else 100
            },
            "supported_media_types": ["IMAGE", "VIDEO", "CAROUSEL_ALBUM"] if is_business else [],
            "webhook_support": is_business,
            "real_time_messaging": is_business
        }
        
        # Add Instagram-specific rate limits based on your project settings
        if is_business:
            capabilities["automation_features"] = {
                "auto_reply": True,
                "scheduled_posts": True,
                "bulk_messaging": True,
                "follower_automation": True,
                "story_interactions": True,
                "comment_management": True,
                "hashtag_monitoring": True,
                "user_engagement": True
            }
        else:
            capabilities["automation_features"] = {
                "auto_reply": False,
                "scheduled_posts": False,
                "bulk_messaging": False,
                "follower_automation": False,
                "story_interactions": False,
                "comment_management": False,
                "hashtag_monitoring": False,
                "user_engagement": False
            }
        
        return capabilities

    async def get_instagram_rate_limits(
        self,
        connection: AgentSocialConnection
    ) -> Dict[str, Any]:
        """Get current rate limit status for Instagram connection"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            # Instagram doesn't provide a direct rate limit endpoint
            # But we can estimate based on recent usage and platform limits
            
            # Check app-level rate limits
            rate_limit_url = f"{self.graph_api_url}/{settings.FACEBOOK_APP_ID}"
            params = {
                "fields": "rate_limit_info",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(rate_limit_url, params=params)
                
            if response.status_code == 200:
                data = response.json()
                rate_limit_info = data.get("rate_limit_info", {})
            else:
                rate_limit_info = {}
            
            # Estimate based on your platform settings and usage
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # These would come from your usage tracking
            estimated_usage = {
                "messages_sent_today": 0,  # Track this in your database
                "posts_created_today": 0,  # Track this in your database
                "api_calls_today": 0,      # Track this in your database
            }
            
            return {
                "account_id": connection.instagram_business_account_id,
                "rate_limits": {
                    "messages_per_day": 100,
                    "posts_per_day": 25,
                    "api_calls_per_hour": 200
                },
                "current_usage": estimated_usage,
                "remaining": {
                    "messages": 100 - estimated_usage["messages_sent_today"],
                    "posts": 25 - estimated_usage["posts_created_today"],
                    "api_calls": 200 - estimated_usage["api_calls_today"]
                },
                "reset_time": (today_start + timedelta(days=1)).isoformat(),
                "app_rate_limit_info": rate_limit_info
            }
            
        except Exception as e:
            logger.error(f"Error getting Instagram rate limits: {str(e)}")
            return {
                "error": "Failed to get rate limit information",
                "message": str(e)
            }

    async def handle_instagram_webhook(
        self,
        webhook_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Handle incoming Instagram webhook notifications"""
        try:
            # Verify webhook authenticity
            if not self._verify_webhook_signature(webhook_data):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            processed_events = []
            
            for entry in webhook_data.get("entry", []):
                instagram_id = entry.get("id")
                
                # Find connection by Instagram ID
                connection = db.query(AgentSocialConnection).filter(
                    AgentSocialConnection.instagram_business_account_id == instagram_id
                ).first()
                
                if not connection:
                    logger.warning(f"Received webhook for unknown Instagram account: {instagram_id}")
                    continue
                
                # Process messaging events
                for messaging in entry.get("messaging", []):
                    event_type = None
                    
                    if "message" in messaging:
                        event_type = "message_received"
                        await self._handle_message_received(messaging, connection, db)
                    elif "read" in messaging:
                        event_type = "message_read"
                        await self._handle_message_read(messaging, connection, db)
                    elif "postback" in messaging:
                        event_type = "postback_received"
                        await self._handle_postback(messaging, connection, db)
                    
                    if event_type:
                        processed_events.append({
                            "instagram_id": instagram_id,
                            "event_type": event_type,
                            "timestamp": messaging.get("timestamp")
                        })
            
            return {
                "processed_events": len(processed_events),
                "events": processed_events,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error handling Instagram webhook: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process Instagram webhook"
            )

    async def _handle_message_received(
        self,
        messaging_event: Dict[str, Any],
        connection: AgentSocialConnection,
        db: Session
    ):
        """Handle incoming message from Instagram"""
        message = messaging_event.get("message", {})
        sender = messaging_event.get("sender", {})
        
        # Store message in your database or trigger automation
        logger.info(f"Received Instagram message from {sender.get('id')} to {connection.platform_username}")
        
        # Update connection last activity
        connection.last_automation_use_at = datetime.utcnow()
        db.commit()
        
        # Here you could trigger auto-reply logic or store the message
        # This would integrate with your broader messaging/automation system

    async def _handle_message_read(
        self,
        messaging_event: Dict[str, Any],
        connection: AgentSocialConnection,
        db: Session
    ):
        """Handle message read receipt"""
        read_info = messaging_event.get("read", {})
        logger.info(f"Message read on Instagram account {connection.platform_username}")

    async def _handle_postback(
        self,
        messaging_event: Dict[str, Any],
        connection: AgentSocialConnection,
        db: Session
    ):
        """Handle postback from Instagram (button clicks, etc.)"""
        postback = messaging_event.get("postback", {})
        logger.info(f"Postback received on Instagram account {connection.platform_username}")

    def _verify_webhook_signature(self, webhook_data: Dict[str, Any]) -> bool:
        """Verify Instagram webhook signature for security"""
        # Implementation would verify the X-Hub-Signature-256 header
        # against your app secret using HMAC-SHA256
        # For now, returning True - implement proper verification in production
        return True

    async def get_instagram_story_insights(
        self,
        connection: AgentSocialConnection,
        story_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get insights for a specific Instagram story"""
        try:
            access_token = decrypt_token(connection.access_token)
            
            story_insights_url = f"{self.instagram_api_url}/{story_id}/insights"
            params = {
                "metric": "impressions,reach,replies,exits,taps_forward,taps_back",
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(story_insights_url, params=params)
                response.raise_for_status()
                
            data = response.json()
            
            # Format story insights
            insights = {}
            for insight in data.get("data", []):
                metric_name = insight.get("name")
                values = insight.get("values", [])
                insights[metric_name] = {
                    "value": values[0].get("value", 0) if values else 0,
                    "end_time": values[0].get("end_time") if values else None
                }
            
            return {
                "story_id": story_id,
                "insights": insights,
                "retrieved_at": datetime.utcnow().isoformat()
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting Instagram story insights: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to get Instagram story insights: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Error getting Instagram story insights: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve Instagram story insights"
            )