# app/Services/OAuthService.py
import json
import httpx
from typing import Dict, Optional, Tuple
from authlib.integrations.httpx_client import AsyncOAuth2Client
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.Models.oauth_accounts import OAuthAccount
from app.Models.auth_models import User
from config.settings import settings
from app.Utils.Logger import logger

class OAuthService:
    def __init__(self):
        self.cipher_suite = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
        
        self.providers = {
            'google': {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
                'scope': 'openid email profile'
            },
            'facebook': {
                'client_id': settings.FACEBOOK_APP_ID,
                'client_secret': settings.FACEBOOK_APP_SECRET,
                'authorize_url': 'https://www.facebook.com/v18.0/dialog/oauth',
                'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
                'userinfo_url': 'https://graph.facebook.com/v18.0/me',
                'scope': 'email,public_profile,pages_manage_posts,pages_read_engagement,instagram_basic,instagram_manage_messages'
            },
            'instagram': {
                'client_id': settings.INSTAGRAM_APP_ID,
                'client_secret': settings.INSTAGRAM_APP_SECRET,
                'authorize_url': 'https://api.instagram.com/oauth/authorize',
                'token_url': 'https://api.instagram.com/oauth/access_token',
                'userinfo_url': 'https://graph.instagram.com/me',
                'scope': 'user_profile,user_media'
            },
            'linkedin': {
                'client_id': settings.LINKEDIN_CLIENT_ID,
                'client_secret': settings.LINKEDIN_CLIENT_SECRET,
                'authorize_url': 'https://www.linkedin.com/oauth/v2/authorization',
                'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
                'userinfo_url': 'https://api.linkedin.com/v2/people/~',
                'scope': 'r_liteprofile r_emailaddress'
            }
        }
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage"""
        if not token:
            return None
        return self.cipher_suite.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token for use"""
        if not encrypted_token:
            return None
        return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
    
    def get_provider_config(self, provider: str) -> Dict:
        """Get provider configuration"""
        if provider not in self.providers:
            raise ValueError(f"Unsupported provider: {provider}")
        return self.providers[provider]
    
    async def get_authorization_url(self, provider: str, state: str, link_mode: bool = False) -> str:
        """Generate OAuth authorization URL"""
        provider_config = self.get_provider_config(provider)
        
        redirect_uri = f"{settings.OAUTH_REDIRECT_URL}/{provider}"
        if link_mode:
            redirect_uri += "?link=true"
        
        client = AsyncOAuth2Client(
            client_id=provider_config['client_id'],
            redirect_uri=redirect_uri
        )
        
        authorization_url, _ = client.create_authorization_url(
            provider_config['authorize_url'],
            scope=provider_config['scope'],
            state=state
        )
        
        return authorization_url
    
    async def exchange_code_for_token(self, provider: str, code: str, link_mode: bool = False) -> Dict:
        """Exchange authorization code for access token"""
        provider_config = self.get_provider_config(provider)
        
        redirect_uri = f"{settings.OAUTH_REDIRECT_URL}/{provider}"
        if link_mode:
            redirect_uri += "?link=true"
        
        client = AsyncOAuth2Client(
            client_id=provider_config['client_id'],
            client_secret=provider_config['client_secret'],
            redirect_uri=redirect_uri
        )
        
        try:
            token = await client.fetch_token(
                provider_config['token_url'],
                code=code
            )
            return token
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            raise
    
    async def get_user_info(self, provider: str, access_token: str) -> Dict:
        """Get user information from OAuth provider"""
        provider_config = self.get_provider_config(provider)
        
        async with httpx.AsyncClient() as client:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            try:
                if provider == 'facebook':
                    url = f"{provider_config['userinfo_url']}?fields=id,name,email,picture"
                elif provider == 'instagram':
                    url = f"{provider_config['userinfo_url']}?fields=id,username,account_type"
                elif provider == 'linkedin':
                    # LinkedIn requires different header format
                    headers = {'Authorization': f'Bearer {access_token}'}
                    url = provider_config['userinfo_url']
                else:  # Google
                    url = provider_config['userinfo_url']
                
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                user_data = response.json()
                
                # Normalize user data across providers
                normalized_data = self._normalize_user_data(provider, user_data)
                return normalized_data
                
            except Exception as e:
                logger.error(f"Error getting user info from {provider}: {str(e)}")
                raise
    
    def _normalize_user_data(self, provider: str, user_data: Dict) -> Dict:
        """Normalize user data across different providers"""
        normalized = {
            'id': str(user_data.get('id', '')),
            'email': user_data.get('email'),
            'name': user_data.get('name'),
            'username': user_data.get('username'),
            'picture': None
        }
        
        # Handle provider-specific picture formats
        if provider == 'facebook':
            picture_data = user_data.get('picture', {})
            if isinstance(picture_data, dict):
                normalized['picture'] = picture_data.get('data', {}).get('url')
        elif provider == 'google':
            normalized['picture'] = user_data.get('picture')
        elif provider == 'linkedin':
            # LinkedIn has more complex profile picture structure
            profile_pic = user_data.get('profilePicture', {})
            if profile_pic:
                normalized['picture'] = profile_pic.get('displayImage')
        
        return normalized
    
    async def save_oauth_account(
        self, 
        db: Session, 
        user: User, 
        provider: str, 
        token_data: Dict, 
        user_info: Dict
    ) -> OAuthAccount:
        """Save OAuth account information"""
        try:
            # Check if OAuth account already exists
            existing_account = db.query(OAuthAccount).filter(
                OAuthAccount.user_id == user.id,
                OAuthAccount.provider == provider
            ).first()
            
            if existing_account:
                # Update existing account
                existing_account.provider_id = str(user_info.get('id'))
                existing_account.email = user_info.get('email')
                existing_account.username = user_info.get('username') or user_info.get('name')
                existing_account.display_name = user_info.get('name') or user_info.get('username')
                existing_account.profile_image_url = user_info.get('picture')
                existing_account.access_token = self.encrypt_token(token_data['access_token'])
                
                if 'refresh_token' in token_data:
                    existing_account.refresh_token = self.encrypt_token(token_data['refresh_token'])
                
                if 'expires_in' in token_data:
                    existing_account.expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                
                existing_account.scope = token_data.get('scope', '')
                existing_account.is_active = True
                existing_account.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(existing_account)
                return existing_account
            
            # Create new OAuth account
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_id=str(user_info.get('id')),
                email=user_info.get('email'),
                username=user_info.get('username') or user_info.get('name'),
                display_name=user_info.get('name') or user_info.get('username'),
                profile_image_url=user_info.get('picture'),
                access_token=self.encrypt_token(token_data['access_token']),
                refresh_token=self.encrypt_token(token_data['refresh_token']) if 'refresh_token' in token_data else None,
                expires_at=datetime.utcnow() + timedelta(seconds=token_data['expires_in']) if 'expires_in' in token_data else None,
                scope=token_data.get('scope', ''),
                is_active=True
            )
            
            db.add(oauth_account)
            db.commit()
            db.refresh(oauth_account)
            
            return oauth_account
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving OAuth account: {str(e)}")
            raise
    
    async def refresh_access_token(self, oauth_account: OAuthAccount, db: Session) -> bool:
        """Refresh access token if expired"""
        try:
            if not oauth_account.refresh_token:
                return False
            
            provider_config = self.get_provider_config(oauth_account.provider)
            refresh_token = self.decrypt_token(oauth_account.refresh_token)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    provider_config['token_url'],
                    data={
                        'grant_type': 'refresh_token',
                        'refresh_token': refresh_token,
                        'client_id': provider_config['client_id'],
                        'client_secret': provider_config['client_secret']
                    }
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    oauth_account.access_token = self.encrypt_token(token_data['access_token'])
                    if 'refresh_token' in token_data:
                        oauth_account.refresh_token = self.encrypt_token(token_data['refresh_token'])
                    if 'expires_in' in token_data:
                        oauth_account.expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                    
                    oauth_account.updated_at = datetime.utcnow()
                    db.commit()
                    
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False
    
    def is_token_expired(self, oauth_account: OAuthAccount) -> bool:
        """Check if access token is expired"""
        if not oauth_account.expires_at:
            return False
        
        # Add 5 minute buffer
        return oauth_account.expires_at <= datetime.utcnow() + timedelta(minutes=5)
    
    async def get_valid_access_token(self, oauth_account: OAuthAccount, db: Session) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        try:
            if self.is_token_expired(oauth_account):
                success = await self.refresh_access_token(oauth_account, db)
                if not success:
                    return None
            
            return self.decrypt_token(oauth_account.access_token)
            
        except Exception as e:
            logger.error(f"Error getting valid access token: {str(e)}")
            return None