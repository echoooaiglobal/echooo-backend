# app/Http/Controllers/AgentInstagramController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import uuid

from app.Services.AgentInstagramService import AgentInstagramService
from app.Models.auth_models import User
from app.Models.oauth_models import AgentSocialConnection
from app.Utils.Logger import logger
from datetime import datetime

class AgentInstagramController:
    """Controller for platform agents to manage Instagram business accounts"""
    
    def __init__(self):
        self.instagram_service = AgentInstagramService()
    
    def _check_platform_agent_role(self, user: User) -> bool:
        """Check if user has platform_agent role"""
        return any(role.name == "platform_agent" for role in user.roles)
    
    async def get_available_business_accounts(self, current_user: User, db: Session) -> Dict:
        """Get available Instagram business accounts for platform agent"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can access Instagram business accounts"
                )
            
            business_accounts = await self.instagram_service.get_instagram_business_accounts_for_agent(current_user, db)
            
            return {
                "business_accounts": business_accounts,
                "count": len(business_accounts),
                "message": "Retrieved Instagram business accounts successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting Instagram business accounts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve Instagram business accounts: {str(e)}"
            )
    
    async def connect_business_account(
        self, 
        current_user: User, 
        instagram_account_id: str,
        page_id: str,
        page_access_token: str,
        instagram_username: str,
        page_name: str,
        db: Session
    ) -> Dict:
        """Connect Instagram business account to platform agent"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can connect Instagram business accounts"
                )
            
            # Validate inputs
            if not all([instagram_account_id, page_id, page_access_token, instagram_username]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing required parameters for connecting Instagram business account"
                )
            
            result = await self.instagram_service.connect_instagram_business_to_agent(
                current_user, instagram_account_id, page_id, page_access_token, 
                instagram_username, page_name, db
            )
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error connecting Instagram business account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect Instagram business account: {str(e)}"
            )
    
    async def get_connected_accounts(self, current_user: User, db: Session) -> Dict:
        """Get platform agent's connected Instagram business accounts"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can view connected accounts"
                )
            
            connected_accounts = await self.instagram_service.get_agent_connected_instagram_accounts(current_user, db)
            
            return {
                "connected_accounts": connected_accounts,
                "count": len(connected_accounts),
                "user_id": str(current_user.id)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting connected Instagram accounts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve connected Instagram accounts"
            )
    
    async def get_conversations(
        self, 
        current_user: User, 
        instagram_account_id: str,
        db: Session
    ) -> Dict:
        """Get Instagram conversations for agent's connected business account"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can access Instagram conversations"
                )
            
            conversations = await self.instagram_service.get_instagram_conversations_for_agent(
                current_user, instagram_account_id, db
            )
            
            return {
                "conversations": conversations,
                "instagram_account_id": instagram_account_id,
                "count": len(conversations)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting Instagram conversations: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve Instagram conversations: {str(e)}"
            )
    
    async def get_conversation_messages(
        self,
        current_user: User,
        instagram_account_id: str,
        conversation_id: str,
        db: Session,
        limit: int = 50
    ) -> Dict:
        """Get messages from a specific Instagram conversation"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can access Instagram messages"
                )
            
            # Validate limit
            if limit < 1 or limit > 100:
                limit = 50
            
            messages = await self.instagram_service.get_conversation_messages_for_agent(
                current_user, instagram_account_id, conversation_id, db, limit
            )
            
            return {
                "messages": messages,
                "conversation_id": conversation_id,
                "instagram_account_id": instagram_account_id,
                "count": len(messages),
                "limit": limit
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting Instagram conversation messages: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve Instagram messages: {str(e)}"
            )
    
    async def send_message(
        self,
        current_user: User,
        instagram_account_id: str,
        recipient_id: str,
        message: str,
        db: Session
    ) -> Dict:
        """Send a message via Instagram as platform agent"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can send Instagram messages"
                )
            
            # Validate message content
            if not message or len(message.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message content cannot be empty"
                )
            
            if len(message) > 1000:  # Instagram message limit
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Message content too long (max 1000 characters)"
                )
            
            # Validate recipient_id
            if not recipient_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Recipient ID is required"
                )
            
            result = await self.instagram_service.send_instagram_message_as_agent(
                current_user, instagram_account_id, recipient_id, message.strip(), db
            )
            
            return {
                "message": "Instagram message sent successfully",
                "result": result,
                "instagram_account_id": instagram_account_id,
                "recipient_id": recipient_id,
                "sent_message": message.strip(),
                "sent_by": str(current_user.id)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending Instagram message: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send Instagram message: {str(e)}"
            )
    
    async def disconnect_business_account(
        self,
        current_user: User,
        instagram_account_id: str,
        db: Session
    ) -> Dict:
        """Disconnect Instagram business account from platform agent"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can disconnect Instagram accounts"
                )
            
            result = await self.instagram_service.disconnect_instagram_from_agent(
                current_user, instagram_account_id, db
            )
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error disconnecting Instagram business account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to disconnect Instagram business account: {str(e)}"
            )
    
    async def get_account_analytics(
        self,
        current_user: User,
        instagram_account_id: str,
        db: Session,
        metrics: Optional[List[str]] = None
    ) -> Dict:
        """Get analytics for connected Instagram business account"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can access Instagram analytics"
                )
            
            # Default metrics if none provided
            if not metrics:
                metrics = ["impressions", "reach", "profile_views", "website_clicks", "follower_count"]
            
            analytics = await self.instagram_service.get_instagram_account_insights(
                current_user, instagram_account_id, db, metrics
            )
            
            return analytics
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting Instagram account analytics: {str(e)}")
            # Return basic connection info even if analytics fail
            try:
                connection = await self.instagram_service.get_agent_instagram_connection(
                    current_user, instagram_account_id, db
                )
                return {
                    "instagram_account_id": instagram_account_id,
                    "connection_status": "active" if connection else "not_connected",
                    "error": f"Could not retrieve analytics: {str(e)}",
                    "retrieved_at": datetime.utcnow().isoformat()
                }
            except:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retrieve Instagram analytics: {str(e)}"
                )
    
    async def get_connection_status(
        self,
        current_user: User,
        instagram_account_id: str,
        db: Session
    ) -> Dict:
        """Get connection status for a specific Instagram account"""
        try:
            # Check role
            if not self._check_platform_agent_role(current_user):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only platform agents can check connection status"
                )
            
            connection = await self.instagram_service.get_agent_instagram_connection(
                current_user, instagram_account_id, db
            )
            
            if connection:
                return {
                    "instagram_account_id": instagram_account_id,
                    "connection_status": "connected",
                    "connection_id": str(connection.id),
                    "username": connection.platform_username,
                    "facebook_page_id": connection.facebook_page_id,
                    "facebook_page_name": connection.facebook_page_name,
                    "connected_at": connection.created_at.isoformat(),
                    "last_updated": connection.updated_at.isoformat()
                }
            else:
                return {
                    "instagram_account_id": instagram_account_id,
                    "connection_status": "not_connected",
                    "message": "Instagram account is not connected to this agent"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking connection status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to check connection status: {str(e)}"
            )