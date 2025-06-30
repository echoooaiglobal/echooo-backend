# app/Services/AgentInstagramService.py
import httpx
import json
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.Models.oauth_models import AgentSocialConnection, OAuthAccount
from app.Models.auth_models import User
from app.Services.OAuthService import OAuthService
from app.Utils.Logger import logger

class AgentInstagramService:
    """Service for platform agents to manage Instagram business accounts"""
    
    def __init__(self):
        self.oauth_service = OAuthService()
        self.base_url = "https://graph.instagram.com"
        self.facebook_graph_url = "https://graph.facebook.com/v18.0"
    
    async def get_agent_facebook_oauth_account(self, user: User, db: Session) -> Optional[OAuthAccount]:
        """Get agent's Facebook OAuth account (needed for Instagram Business API)"""
        return db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user.id,
            OAuthAccount.provider == "facebook",
            OAuthAccount.is_active == True
        ).first()
    
    async def get_instagram_business_accounts_for_agent(self, user: User, db: Session) -> List[Dict]:
        """Get Instagram business accounts available to platform agent"""
        try:
            # Get agent's Facebook OAuth account
            facebook_oauth = await self.get_agent_facebook_oauth_account(user, db)
            
            if not facebook_oauth:
                raise Exception("Facebook account not connected. Please connect your Facebook account first to access Instagram Business accounts.")
            
            # Get valid access token
            access_token = await self.oauth_service.get_valid_access_token(facebook_oauth, db)
            if not access_token:
                raise Exception("Facebook access token expired or invalid. Please reconnect your Facebook account.")
            
            # Get user's Facebook pages
            async with httpx.AsyncClient() as client:
                pages_response = await client.get(
                    f"{self.facebook_graph_url}/me/accounts",
                    params={"access_token": access_token}
                )
                pages_response.raise_for_status()
                pages_data = pages_response.json()
                
                instagram_accounts = []
                
                for page in pages_data.get('data', []):
                    page_access_token = page['access_token']
                    page_id = page['id']
                    page_name = page['name']
                    
                    # Check if page has Instagram business account
                    try:
                        instagram_response = await client.get(
                            f"{self.facebook_graph_url}/{page_id}",
                            params={
                                "fields": "instagram_business_account",
                                "access_token": page_access_token
                            }
                        )
                        
                        if instagram_response.status_code == 200:
                            instagram_data = instagram_response.json()
                            
                            if 'instagram_business_account' in instagram_data:
                                ig_account_id = instagram_data['instagram_business_account']['id']
                                
                                # Get Instagram account details
                                ig_details_response = await client.get(
                                    f"{self.facebook_graph_url}/{ig_account_id}",
                                    params={
                                        "fields": "id,username,name,profile_picture_url,followers_count,media_count",
                                        "access_token": page_access_token
                                    }
                                )
                                
                                if ig_details_response.status_code == 200:
                                    ig_details = ig_details_response.json()
                                    
                                    # Check if already connected
                                    is_connected = await self.is_instagram_connected_to_agent(user, ig_account_id, db)
                                    
                                    instagram_accounts.append({
                                        "instagram_account_id": ig_account_id,
                                        "page_id": page_id,
                                        "page_name": page_name,
                                        "page_access_token": page_access_token,  # Don't store this, just use for connection
                                        "instagram_username": ig_details.get('username'),
                                        "instagram_name": ig_details.get('name'),
                                        "profile_picture_url": ig_details.get('profile_picture_url'),
                                        "followers_count": ig_details.get('followers_count'),
                                        "media_count": ig_details.get('media_count'),
                                        "is_connected": is_connected
                                    })
                    except Exception as e:
                        logger.warning(f"Could not get Instagram account for page {page_id}: {str(e)}")
                        continue
                
                return instagram_accounts
                
        except Exception as e:
            logger.error(f"Error getting Instagram business accounts for agent: {str(e)}")
            raise
    
    async def is_instagram_connected_to_agent(self, user: User, instagram_account_id: str, db: Session) -> bool:
        """Check if Instagram account is already connected to this agent"""
        connection = db.query(AgentSocialConnection).filter(
            AgentSocialConnection.user_id == user.id,
            AgentSocialConnection.platform == "instagram",
            AgentSocialConnection.instagram_business_account_id == instagram_account_id,
            AgentSocialConnection.is_active == True
        ).first()
        
        return connection is not None
    
    async def connect_instagram_business_to_agent(
        self,
        user: User,
        instagram_account_id: str,
        page_id: str,
        page_access_token: str,
        instagram_username: str,
        page_name: str,
        db: Session
    ) -> Dict:
        """Connect Instagram business account to platform agent"""
        try:
            # Check if already connected
            existing_connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.user_id == user.id,
                AgentSocialConnection.platform == "instagram",
                AgentSocialConnection.instagram_business_account_id == instagram_account_id
            ).first()
            
            if existing_connection:
                # Update existing connection
                existing_connection.facebook_page_access_token = self.oauth_service.encrypt_token(page_access_token)
                existing_connection.facebook_page_id = page_id
                existing_connection.facebook_page_name = page_name
                existing_connection.platform_username = instagram_username
                existing_connection.is_active = True
                existing_connection.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(existing_connection)
                
                return {
                    "message": "Instagram business account connection updated successfully",
                    "connection_id": str(existing_connection.id),
                    "instagram_account_id": instagram_account_id,
                    "instagram_username": instagram_username
                }
            
            # Create new connection
            new_connection = AgentSocialConnection(
                user_id=user.id,
                platform="instagram",
                platform_user_id=instagram_account_id,
                platform_username=instagram_username,
                display_name=page_name,
                instagram_business_account_id=instagram_account_id,
                facebook_page_id=page_id,
                facebook_page_name=page_name,
                facebook_page_access_token=self.oauth_service.encrypt_token(page_access_token),
                connection_type="business_api",
                is_active=True
            )
            
            db.add(new_connection)
            db.commit()
            db.refresh(new_connection)
            
            return {
                "message": "Instagram business account connected successfully",
                "connection_id": str(new_connection.id),
                "instagram_account_id": instagram_account_id,
                "instagram_username": instagram_username
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error connecting Instagram business account to agent: {str(e)}")
            raise
    
    async def get_agent_instagram_connection(self, user: User, instagram_account_id: str, db: Session) -> Optional[AgentSocialConnection]:
        """Get agent's Instagram connection"""
        return db.query(AgentSocialConnection).filter(
            AgentSocialConnection.user_id == user.id,
            AgentSocialConnection.platform == "instagram",
            AgentSocialConnection.instagram_business_account_id == instagram_account_id,
            AgentSocialConnection.is_active == True
        ).first()
    
    async def get_instagram_conversations_for_agent(
        self, 
        user: User,
        instagram_account_id: str, 
        db: Session
    ) -> List[Dict]:
        """Get Instagram conversations for agent's connected business account"""
        try:
            # Get agent's Instagram connection
            connection = await self.get_agent_instagram_connection(user, instagram_account_id, db)
            
            if not connection:
                raise Exception("Instagram business account not connected to this agent")
            
            page_access_token = self.oauth_service.decrypt_token(connection.facebook_page_access_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.facebook_graph_url}/{instagram_account_id}/conversations",
                    params={
                        "fields": "id,updated_time,can_reply,message_count,unread_count,participants",
                        "access_token": page_access_token
                    }
                )
                response.raise_for_status()
                
                conversations_data = response.json()
                return conversations_data.get('data', [])
                
        except Exception as e:
            logger.error(f"Error getting Instagram conversations for agent: {str(e)}")
            raise
    
    async def get_conversation_messages_for_agent(
        self, 
        user: User,
        instagram_account_id: str,
        conversation_id: str, 
        db: Session,
        limit: int = 50
    ) -> List[Dict]:
        """Get messages from a specific conversation for agent"""
        try:
            # Get agent's Instagram connection
            connection = await self.get_agent_instagram_connection(user, instagram_account_id, db)
            
            if not connection:
                raise Exception("Instagram business account not connected to this agent")
            
            page_access_token = self.oauth_service.decrypt_token(connection.facebook_page_access_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.facebook_graph_url}/{conversation_id}/messages",
                    params={
                        "fields": "id,created_time,from,to,message,attachments",
                        "limit": limit,
                        "access_token": page_access_token
                    }
                )
                response.raise_for_status()
                
                messages_data = response.json()
                return messages_data.get('data', [])
                
        except Exception as e:
            logger.error(f"Error getting conversation messages for agent: {str(e)}")
            raise
    
    async def send_instagram_message_as_agent(
        self,
        user: User,
        instagram_account_id: str,
        recipient_id: str,
        message: str,
        db: Session
    ) -> Dict:
        """Send a message via Instagram as platform agent"""
        try:
            # Get agent's Instagram connection
            connection = await self.get_agent_instagram_connection(user, instagram_account_id, db)
            
            if not connection:
                raise Exception("Instagram business account not connected to this agent")
            
            page_access_token = self.oauth_service.decrypt_token(connection.facebook_page_access_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.facebook_graph_url}/me/messages",
                    json={
                        "recipient": {"id": recipient_id},
                        "message": {"text": message}
                    },
                    headers={
                        "Authorization": f"Bearer {page_access_token}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Log the sent message
                logger.info(f"Message sent by agent {user.id} via Instagram account {instagram_account_id} to {recipient_id}")
                
                return result
                
        except Exception as e:
            logger.error(f"Error sending Instagram message as agent: {str(e)}")
            raise
    
    async def disconnect_instagram_from_agent(
        self,
        user: User,
        instagram_account_id: str,
        db: Session
    ) -> Dict:
        """Disconnect Instagram business account from platform agent"""
        try:
            connection = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.user_id == user.id,
                AgentSocialConnection.platform == "instagram",
                AgentSocialConnection.instagram_business_account_id == instagram_account_id
            ).first()
            
            if not connection:
                raise Exception("Instagram business account not found or not connected")
            
            connection.is_active = False
            connection.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "message": "Instagram business account disconnected successfully",
                "instagram_account_id": instagram_account_id,
                "disconnected_at": connection.updated_at.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error disconnecting Instagram account from agent: {str(e)}")
            raise
    
    async def get_agent_connected_instagram_accounts(self, user: User, db: Session) -> List[Dict]:
        """Get all Instagram accounts connected to the agent"""
        try:
            connections = db.query(AgentSocialConnection).filter(
                AgentSocialConnection.user_id == user.id,
                AgentSocialConnection.platform == "instagram",
                AgentSocialConnection.is_active == True
            ).all()
            
            connected_accounts = []
            for connection in connections:
                connected_accounts.append({
                    "connection_id": str(connection.id),
                    "instagram_account_id": connection.instagram_business_account_id,
                    "username": connection.platform_username,
                    "display_name": connection.display_name,
                    "facebook_page_id": connection.facebook_page_id,
                    "facebook_page_name": connection.facebook_page_name,
                    "connected_at": connection.created_at.isoformat(),
                    "last_updated": connection.updated_at.isoformat(),
                    "connection_type": connection.connection_type
                })
            
            return connected_accounts
            
        except Exception as e:
            logger.error(f"Error getting agent's connected Instagram accounts: {str(e)}")
            raise
    
    async def get_instagram_account_insights(
        self,
        user: User,
        instagram_account_id: str,
        db: Session,
        metric_types: List[str] = None
    ) -> Dict:
        """Get Instagram account insights/analytics"""
        try:
            # Get agent's Instagram connection
            connection = await self.get_agent_instagram_connection(user, instagram_account_id, db)
            
            if not connection:
                raise Exception("Instagram business account not connected to this agent")
            
            page_access_token = self.oauth_service.decrypt_token(connection.facebook_page_access_token)
            
            # Default metrics if none provided
            if not metric_types:
                metric_types = [
                    "impressions", "reach", "profile_views", 
                    "website_clicks", "follower_count"
                ]
            
            async with httpx.AsyncClient() as client:
                # Get account insights
                insights_response = await client.get(
                    f"{self.facebook_graph_url}/{instagram_account_id}/insights",
                    params={
                        "metric": ",".join(metric_types),
                        "period": "day",
                        "access_token": page_access_token
                    }
                )
                
                insights_data = {}
                if insights_response.status_code == 200:
                    insights_data = insights_response.json()
                
                # Get basic account info
                account_response = await client.get(
                    f"{self.facebook_graph_url}/{instagram_account_id}",
                    params={
                        "fields": "followers_count,media_count,name,username,profile_picture_url",
                        "access_token": page_access_token
                    }
                )
                account_response.raise_for_status()
                account_data = account_response.json()
                
                return {
                    "instagram_account_id": instagram_account_id,
                    "account_info": account_data,
                    "insights": insights_data,
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting Instagram account insights: {str(e)}")
            # Return basic info even if insights fail
            connection = await self.get_agent_instagram_connection(user, instagram_account_id, db)
            return {
                "instagram_account_id": instagram_account_id,
                "connection_status": "active" if connection else "not_connected",
                "error": f"Could not retrieve insights: {str(e)}",
                "retrieved_at": datetime.utcnow().isoformat()
            }