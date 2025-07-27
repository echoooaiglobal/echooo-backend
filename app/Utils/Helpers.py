# app/Utils/Helpers.py
from fastapi import Depends, HTTPException, status, Path, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import List, Optional, Union
import uuid
from app.Models.auth_models import User, Role, UserStatus
from app.Schemas.auth import TokenData
from config.database import get_db
from app.Utils.Logger import logger
from config.settings import settings

# Configuration for JWT
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v0/auth/login")

# app/Utils/Helpers.py
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User: The current authenticated user
        
    Raises:
        HTTPException: If authentication fails or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if email is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(email=email, user_id=user_id)
        
        # Convert the string user_id to UUID for database query
        try:
            uuid_user_id = uuid.UUID(user_id)
        except ValueError:
            logger.error(f"Invalid UUID format: {user_id}")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception
    
    # Get user from database using the UUID
    user = db.query(User).filter(User.id == uuid_user_id).first()
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if the current user is active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: The current active user
        
    Raises:
        HTTPException: If user is not active
    """
    if current_user.status != UserStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def has_role(required_roles: List[str]):
    """
    Dependency to check if a user has one of the required roles.
    
    Args:
        required_roles: List of role names that are allowed
        
    Returns:
        Callable: A dependency function that checks user roles
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        user_roles = [role.name for role in current_user.roles]
        
        for role in required_roles:
            if role in user_roles:
                return current_user
                
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return role_checker

def has_permission(permission_name: str):
    """
    Dependency to check if a user has a specific permission.
    
    Args:
        permission_name: The name of the required permission
        
    Returns:
        Callable: A dependency function that checks user permissions
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)) -> User:
        # Get user roles
        user_roles = current_user.roles
        
        # Check if any role has the required permission
        for role in user_roles:
            for role_permission in role.permissions:
                if role_permission.permission.name == permission_name:
                    return current_user
        
        # Permission not found
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    return permission_checker

def company_member(user: User = Depends(get_current_active_user), company_id: int = None) -> User:
    """
    Check if a user belongs to a specific company.
    
    Args:
        user: Current authenticated user
        company_id: ID of the company to check
        
    Returns:
        User: The current user if they belong to the company
        
    Raises:
        HTTPException: If user does not belong to the company
    """
    # Check if user is a platform admin (can access all companies)
    for role in user.roles:
        if role.name == "platform_admin":
            return user
    
    # Check if user belongs to the company
    for company in user.companies:
        if company.id == company_id:
            return user
    
    # User does not belong to the company
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to this company's resources"
    )

def is_influencer(user: User = Depends(get_current_active_user)) -> User:
    """
    Check if the user is an influencer.
    
    Args:
        user: Current authenticated user
        
    Returns:
        User: The current user if they are an influencer
        
    Raises:
        HTTPException: If user is not an influencer
    """
    for role in user.roles:
        if role.name == "influencer":
            return user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only influencers can access this resource"
    )

async def is_company_admin(
    request: Request,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Check if the user is an admin of the specified company.
    Gets the company_id from the request path.
    
    Args:
        request: FastAPI Request object
        current_user: Current authenticated user
        
    Returns:
        User: The current user if they are a company admin
        
    Raises:
        HTTPException: If user is not a company admin
    """
    # Extract company_id from path
    path_params = request.path_params
    company_id = path_params.get("company_id")
    
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company ID not provided in path"
        )
    
    # Try to convert to UUID
    try:
        company_id = uuid.UUID(company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid company ID format"
        )
    
    # Check if user is a platform admin (can access all companies)
    for role in current_user.roles:
        if role.name == "platform_admin":
            return current_user
    
    # Check if user is a company admin for this company
    for role in current_user.roles:
        if role.name == "b2c_company_admin":
            for company_user in current_user.company_associations:
                if company_user.company_id == company_id:
                    return current_user
    
    # User is not an admin of this company
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only company owner & admins can access this resource"
    )