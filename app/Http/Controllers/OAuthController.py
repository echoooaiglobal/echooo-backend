# app/Http/Controllers/OAuthController.py - COMPLETE FIXED VERSION

import uuid
import secrets
import json
from typing import Dict, Optional
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.Services.OAuthService import OAuthService
from app.Http.Controllers.AuthController import AuthController
from app.Models.auth_models import User, Role
from app.Models.oauth_accounts import OAuthAccount
from app.Models.company_models import Company, CompanyUser
from app.Schemas.auth import RoleResponse, CompanyBriefResponse, UserResponse
from app.Utils.Logger import logger
from config.settings import settings

class OAuthController:
    def __init__(self):
        self.oauth_service = OAuthService()
        self.auth_controller = AuthController()
    
    async def get_oauth_providers(self) -> Dict:
        """Get available OAuth providers and their configuration"""
        try:
            providers = []
            for provider_name, config in self.oauth_service.providers.items():
                providers.append({
                    "provider": provider_name,
                    "client_id": config['client_id'],
                    "authorize_url": config['authorize_url'],
                    "scope": config['scope'],
                    "enabled": bool(config['client_id'] and config['client_secret'])
                })
            
            return {
                "providers": providers,
                "count": len(providers),
                "redirect_url": settings.OAUTH_REDIRECT_URL
            }
            
        except Exception as e:
            logger.error(f"Error getting OAuth providers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve OAuth providers"
            )
    
    async def initiate_oauth(self, provider: str, request: Request, link_mode: bool = False, user_type: str = None) -> Dict:
        """
        Initiate OAuth flow with complete user context stored in state
        
        FIXED: Now properly handles None user_type from login page
        """
        try:
            # Validate provider
            supported_providers = ['google', 'facebook', 'instagram', 'linkedin']
            if provider not in supported_providers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported provider. Supported: {', '.join(supported_providers)}"
                )
            
            # Generate state for CSRF protection
            base_state = secrets.token_urlsafe(24)
            
            # FIXED: Handle None user_type properly (from login page)
            role_name = None
            if user_type == 'b2c':
                role_name = 'b2c_company_admin'  # B2C registration creates admin
            elif user_type == 'influencer':
                role_name = 'influencer'     # Influencer registration creates influencer
            elif user_type == 'platform':
                role_name = 'platform_user'  # Platform user
            else:
                # user_type is None (from login page) - don't set role_name
                role_name = None
            
            # Store complete user context in state (encode as JSON)
            state_data = {
                'base': base_state,
                'user_type': user_type,  # Can be None for login page
                'role_name': role_name,  # Can be None for login page
                'link_mode': link_mode,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Encode state data as base64 JSON
            import base64
            state_json = json.dumps(state_data)
            encoded_state = base64.b64encode(state_json.encode()).decode()
            
            logger.info(f"OAuth initiation for {provider}: user_type={user_type}, role_name={role_name}, link_mode={link_mode}")
            
            # Get authorization URL
            authorization_url = await self.oauth_service.get_authorization_url(provider, encoded_state, link_mode)
            
            return {
                "authorization_url": authorization_url,
                "state": encoded_state,
                "provider": provider,
                "link_mode": link_mode
            }
            
        except Exception as e:
            logger.error(f"OAuth initiation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initiate OAuth flow: {str(e)}"
            )
    
    async def handle_oauth_callback(
        self, 
        provider: str, 
        code: str, 
        state: str,
        db: Session,
        link_mode: bool = False,
        current_user: Optional[User] = None
    ) -> Dict:
        """
        Handle OAuth callback with FIXED login/registration separation logic
        
        FIXED: Now properly implements login vs registration logic based on user_type in state
        """
        try:
            # Validate state and extract context
            if not state:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing state parameter"
                )
            
            # Decode state to get complete user context
            try:
                import base64
                decoded_state = base64.b64decode(state.encode()).decode()
                state_data = json.loads(decoded_state)
                user_type = state_data.get('user_type')  # Can be None from login page
                role_name = state_data.get('role_name')  # Can be None from login page
                original_link_mode = state_data.get('link_mode', False)
                
                logger.info(f"OAuth callback for {provider}: extracted user_type={user_type}, role_name={role_name}, link_mode={original_link_mode}")
            except Exception as e:
                logger.warning(f"Could not decode state: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid state parameter"
                )
            
            # Use the extracted link_mode or the parameter
            actual_link_mode = original_link_mode or link_mode
            
            # Exchange code for token
            token_data = await self.oauth_service.exchange_code_for_token(provider, code, actual_link_mode)
            
            # Get user info from provider
            user_info = await self.oauth_service.get_user_info(provider, token_data['access_token'])
            
            if actual_link_mode and current_user:
                # User is already logged in, link OAuth account
                oauth_account = await self.oauth_service.save_oauth_account(
                    db, current_user, provider, token_data, user_info
                )
                
                return {
                    "message": f"{provider.title()} account linked successfully",
                    "provider": provider,
                    "login_method": "oauth_link",
                    "oauth_account_id": str(oauth_account.id),
                    "linked_to_user": str(current_user.id),
                    "needs_completion": False,
                    "redirect_path": "/dashboard"
                }
            
            else:
                # STEP 1: Check if user exists with this OAuth account
                existing_oauth = db.query(OAuthAccount).filter(
                    OAuthAccount.provider == provider,
                    OAuthAccount.provider_id == str(user_info.get('id')),
                    OAuthAccount.is_active == True
                ).first()
                
                # STEP 2: Check if user exists by email
                existing_user_by_email = None
                if user_info.get('email'):
                    existing_user_by_email = db.query(User).filter(
                        User.email == user_info['email']
                    ).first()
                
                # STEP 3: Apply the FIXED login/registration logic
                if existing_oauth:
                    # Case 1: OAuth account exists - always allow login
                    user = existing_oauth.user
                    return await self._handle_existing_oauth_login(user, provider, token_data, user_info, db)
                    
                elif existing_user_by_email:
                    # Case 2: User exists by email but no OAuth link - always allow login and link
                    return await self._handle_existing_user_login(existing_user_by_email, provider, token_data, user_info, db)
                    
                else:
                    # Case 3: NEW USER - Apply login vs registration logic
                    if user_type is None:
                        # USER CAME FROM LOGIN PAGE - Cannot create account
                        logger.warning(f"OAuth login attempt for non-existent user: {user_info.get('email')}")
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Account not found. Please register first using the registration page."
                        )
                    else:
                        # USER CAME FROM REGISTRATION PAGE - Can create account
                        logger.info(f"Creating new OAuth user with type: {user_type}")
                        return await self._handle_new_user_registration(user_type, role_name, provider, token_data, user_info, db)
            
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to handle OAuth callback: {str(e)}"
            )

    async def _handle_existing_oauth_login(self, user: User, provider: str, token_data: Dict, user_info: Dict, db: Session) -> Dict:
        """Handle login for user with existing OAuth account"""
        # Update OAuth token
        await self.oauth_service.save_oauth_account(
            db, user, provider, token_data, user_info
        )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        # Create tokens like regular login
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.auth_controller.create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.auth_controller.create_refresh_token(user.id, db)
        
        # Get user roles in proper format
        roles = [RoleResponse.model_validate(role) for role in user.roles]
        
        # Get company info if user is a b2c user
        company = None
        if user.user_type == "b2c":
            company_user = db.query(CompanyUser).filter(CompanyUser.user_id == user.id).first()
            if company_user:
                company = db.query(Company).filter(Company.id == company_user.company_id).first()
        
        db.commit()
        
        # Return complete login response
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.model_validate(user),
            "roles": roles,
            "company": CompanyBriefResponse.model_validate(company) if company else None,
            "message": f"Logged in via {provider.title()}",
            "provider": provider,
            "login_method": "oauth_login",
            "needs_completion": False,
            "redirect_path": "/campaigns" if user.user_type == "b2c" else "/dashboard"
        }

    async def _handle_existing_user_login(self, user: User, provider: str, token_data: Dict, user_info: Dict, db: Session) -> Dict:
        """Handle login for existing user (by email) and link OAuth account"""
        # Link OAuth account to existing user
        oauth_account = await self.oauth_service.save_oauth_account(
            db, user, provider, token_data, user_info
        )
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        
        # Create tokens like regular login
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.auth_controller.create_access_token(
            data={"sub": user.email, "user_id": str(user.id)},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.auth_controller.create_refresh_token(user.id, db)
        
        # Get user roles
        roles = [RoleResponse.model_validate(role) for role in user.roles]
        
        # Get company info if user is a company user
        company = None
        if user.user_type == "b2c":
            company_user = db.query(CompanyUser).filter(CompanyUser.user_id == user.id).first()
            if company_user:
                company = db.query(Company).filter(Company.id == company_user.company_id).first()
        
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.model_validate(user),
            "roles": roles,
            "company": CompanyBriefResponse.model_validate(company) if company else None,
            "message": f"Logged in via {provider.title()} and linked account",
            "provider": provider,
            "login_method": "oauth_login_and_link",
            "needs_completion": False,
            "redirect_path": "/campaigns" if user.user_type == "b2c" else "/dashboard"
        }

    async def _handle_new_user_registration(self, user_type: str, role_name: str, provider: str, token_data: Dict, user_info: Dict, db: Session) -> Dict:
        """Handle registration for new user via OAuth"""
        # Get the appropriate role
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            logger.error(f"Role {role_name} not found for user_type {user_type}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Role configuration error"
            )
        
        # Create new user
        new_user = User(
            email=user_info.get('email'),
            full_name=user_info.get('name', ''),
            phone_number=None,  # OAuth doesn't provide phone
            hashed_password=None,  # OAuth users don't have passwords
            user_type=user_type,
            status='active',
            email_verified=True,  # OAuth emails are considered verified
            profile_image_url=user_info.get('picture'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_login_at=datetime.utcnow()
        )
        
        new_user.roles.append(role)
        db.add(new_user)
        db.flush()  # Get the user ID
        
        # Handle user type specific setup
        if user_type == "b2c":
            # For b2c users, create placeholder company
            try:
                from app.Services.CompanyService import CompanyService
                
                company_data = {
                    "name": f"{new_user.full_name}'s Company",  # Placeholder
                    "domain": None  # Will be updated later
                }
                
                company = await CompanyService.create_company(
                    company_data,
                    new_user.id,
                    db
                )
                
                logger.info(f"Created placeholder company for OAuth user: {company.id}")
                
            except Exception as e:
                logger.error(f"Error creating company during OAuth registration: {str(e)}")
                # Don't fail the registration, user can complete later
        
        elif user_type == "influencer":
            # Create influencer profile
            try:
                from app.Services.InfluencerService import InfluencerService
                await InfluencerService.create_influencer_profile(new_user.id, db)
                logger.info(f"Created influencer profile for OAuth user: {new_user.id}")
            except Exception as e:
                logger.warning(f"Could not create influencer profile: {str(e)}")
        
        # Create OAuth account
        oauth_account = await self.oauth_service.save_oauth_account(
            db, new_user, provider, token_data, user_info
        )
        
        # Create tokens like regular registration
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = self.auth_controller.create_access_token(
            data={"sub": new_user.email, "user_id": str(new_user.id)},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.auth_controller.create_refresh_token(new_user.id, db)
        
        db.commit()
        db.refresh(new_user)
        
        # Get user roles
        roles = [RoleResponse.model_validate(role) for role in new_user.roles]
        
        # Get company info if created
        company = None
        if user_type == "b2c":
            company_user = db.query(CompanyUser).filter(CompanyUser.user_id == new_user.id).first()
            if company_user:
                company = db.query(Company).filter(Company.id == company_user.company_id).first()
        
        # Determine completion needs
        needs_completion = user_type == "b2c"
        completion_type = "b2c" if user_type == "b2c" else None
        redirect_path = "/register/complete?type=b2c" if needs_completion else ("/campaigns" if user_type == "b2c" else "/dashboard")
        
        # Return complete registration response
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": UserResponse.model_validate(new_user),
            "roles": roles,
            "company": CompanyBriefResponse.model_validate(company) if company else None,
            "message": f"Account created via {provider.title()}",
            "provider": provider,
            "login_method": "oauth_register",
            "needs_completion": needs_completion,
            "completion_type": completion_type,
            "redirect_path": redirect_path
        }

    async def get_linked_accounts(self, current_user: User, db: Session) -> Dict:
        """Get user's linked OAuth accounts"""
        try:
            oauth_accounts = db.query(OAuthAccount).filter(
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.is_active == True
            ).all()
            
            accounts = []
            for account in oauth_accounts:
                accounts.append({
                    "id": str(account.id),
                    "provider": account.provider,
                    "username": account.username,
                    "display_name": account.display_name,
                    "email": account.email,
                    "profile_image_url": account.profile_image_url,
                    "connected_at": account.created_at.isoformat(),
                    "last_updated": account.updated_at.isoformat(),
                    "expires_at": account.expires_at.isoformat() if account.expires_at else None,
                    "scope": account.scope
                })
            
            return {
                "linked_accounts": accounts,
                "count": len(accounts)
            }
            
        except Exception as e:
            logger.error(f"Error getting linked accounts: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve linked accounts"
            )

    async def unlink_oauth_account(self, current_user: User, account_id: str, db: Session) -> Dict:
        """Unlink a social account"""
        try:
            # Validate account_id format
            try:
                account_uuid = uuid.UUID(account_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid account ID format"
                )
            
            # Find the OAuth account
            oauth_account = db.query(OAuthAccount).filter(
                OAuthAccount.id == account_uuid,
                OAuthAccount.user_id == current_user.id,
                OAuthAccount.is_active == True
            ).first()
            
            if not oauth_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="OAuth account not found"
                )
            
            # Deactivate the account
            oauth_account.is_active = False
            oauth_account.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "message": f"{oauth_account.provider.title()} account unlinked successfully",
                "provider": oauth_account.provider,
                "unlinked_at": datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error unlinking OAuth account: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unlink OAuth account"
            )