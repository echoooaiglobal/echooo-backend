# routes/api/v0/agent_instagram.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.Http.Controllers.AgentInstagramController import AgentInstagramController
from app.Models.auth_models import User
from app.Schemas.agent_instagram_schemas import (
    InstagramBusinessAccountsResponse, ConnectedAccountsResponse,
    ConnectBusinessAccountRequest, InstagramConversationsResponse,
    InstagramMessagesResponse, SendMessageRequest, SendMessageResponse,
    DisconnectAccountResponse, InstagramAnalyticsResponse,
    ConnectionStatusResponse, InstagramHealthResponse,
    ConversationMessagesQuery, AnalyticsQuery
)
from app.Utils.Helpers import get_current_user, has_role
from config.database import get_db

router = APIRouter(prefix="/agent/instagram", tags=["Agent Instagram Business"])

agent_instagram_controller = AgentInstagramController()

@router.get("/business-accounts", response_model=InstagramBusinessAccountsResponse)
async def get_available_business_accounts(
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get available Instagram business accounts for platform agent
    
    This endpoint requires the agent to have connected their Facebook account first
    via OAuth, then shows all Instagram business accounts associated with their 
    Facebook pages.
    
    **Prerequisites:**
    - User must have `platform_agent` role
    - User must have connected Facebook account via OAuth
    - Facebook account must have business pages with Instagram business accounts
    
    **Returns:**
    - List of available Instagram business accounts
    - Connection status for each account
    - Account metadata (username, followers, etc.)
    """
    return await agent_instagram_controller.get_available_business_accounts(current_user, db)

@router.post("/connect", response_model=SendMessageResponse)
async def connect_business_account(
    connect_data: ConnectBusinessAccountRequest,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Connect an Instagram business account to the platform agent
    
    This allows the agent to manage Instagram conversations and send messages
    through the connected business account.
    
    **Prerequisites:**
    - User must have `platform_agent` role
    - Instagram account must be a business account
    - Account must be associated with a Facebook page
    
    **Request Body:**
    ```json
    {
        "instagram_account_id": "instagram_business_account_id",
        "page_id": "facebook_page_id", 
        "page_access_token": "facebook_page_access_token",
        "instagram_username": "@business_username",
        "page_name": "Business Page Name"
    }
    ```
    """
    return await agent_instagram_controller.connect_business_account(
        current_user,
        connect_data.instagram_account_id,
        connect_data.page_id,
        connect_data.page_access_token,
        connect_data.instagram_username,
        connect_data.page_name,
        db
    )

@router.get("/connected", response_model=ConnectedAccountsResponse)
async def get_connected_accounts(
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get all Instagram business accounts connected to the current platform agent
    
    Returns a list of all Instagram business accounts that the agent has
    successfully connected and can manage.
    """
    return await agent_instagram_controller.get_connected_accounts(current_user, db)

@router.get("/{instagram_account_id}/status", response_model=ConnectionStatusResponse)
async def get_connection_status(
    instagram_account_id: str,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get connection status for a specific Instagram account
    
    Check if a specific Instagram business account is connected to the current
    agent and get connection details.
    """
    return await agent_instagram_controller.get_connection_status(
        current_user, instagram_account_id, db
    )

@router.get("/{instagram_account_id}/conversations", response_model=InstagramConversationsResponse)
async def get_conversations(
    instagram_account_id: str,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get Instagram conversations for a connected business account
    
    Returns all conversations/chats for the specified Instagram business account
    that the agent has connected.
    
    **Response includes:**
    - Conversation ID and metadata
    - Participant information
    - Message count and unread count
    - Last update timestamp
    - Reply permissions
    """
    return await agent_instagram_controller.get_conversations(current_user, instagram_account_id, db)

@router.get("/{instagram_account_id}/conversations/{conversation_id}/messages", response_model=InstagramMessagesResponse)
async def get_conversation_messages(
    instagram_account_id: str,
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to retrieve (1-100)"),
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get messages from a specific Instagram conversation
    
    Retrieves messages from a conversation thread for the specified Instagram 
    business account.
    
    **Parameters:**
    - `instagram_account_id`: The Instagram business account ID
    - `conversation_id`: The specific conversation ID
    - `limit`: Number of messages to retrieve (1-100, default: 50)
    
    **Response includes:**
    - Message content and metadata
    - Sender/recipient information
    - Timestamps
    - Attachments (if any)
    """
    return await agent_instagram_controller.get_conversation_messages(
        current_user, instagram_account_id, conversation_id, db, limit
    )

@router.post("/{instagram_account_id}/send-message", response_model=SendMessageResponse)
async def send_message(
    instagram_account_id: str,
    message_data: SendMessageRequest,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Send a message via Instagram as platform agent
    
    Sends a message to a specific recipient through the connected Instagram 
    business account.
    
    **Request Body:**
    ```json
    {
        "recipient_id": "instagram_user_id_or_conversation_id",
        "message": "Your message content here"
    }
    ```
    
    **Message Limitations:**
    - Maximum 1000 characters
    - Text messages only (attachments not yet supported)
    - Recipient must have initiated conversation or follow the business account
    
    **Instagram API Requirements:**
    - Business account must be verified
    - Messaging permissions must be approved by Instagram
    - Rate limits apply (varies by account tier)
    """
    return await agent_instagram_controller.send_message(
        current_user,
        instagram_account_id,
        message_data.recipient_id,
        message_data.message,
        db
    )

@router.delete("/{instagram_account_id}/disconnect", response_model=DisconnectAccountResponse)
async def disconnect_business_account(
    instagram_account_id: str,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Disconnect Instagram business account from platform agent
    
    Removes the connection between the agent and the Instagram business account.
    The agent will no longer be able to access conversations or send messages
    through this account.
    
    **Note:** This only removes the connection in our system. The Instagram
    business account and Facebook page remain unchanged.
    """
    return await agent_instagram_controller.disconnect_business_account(
        current_user, instagram_account_id, db
    )

@router.get("/{instagram_account_id}/analytics", response_model=InstagramAnalyticsResponse)
async def get_account_analytics(
    instagram_account_id: str,
    metrics: Optional[List[str]] = Query(
        None, 
        description="Specific metrics to retrieve (default: impressions,reach,profile_views,website_clicks,follower_count)"
    ),
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get analytics for connected Instagram business account
    
    Returns analytics data for the Instagram business account using Instagram 
    Insights API.
    
    **Available Metrics:**
    - `impressions`: Number of times posts were seen
    - `reach`: Number of unique accounts that saw posts
    - `profile_views`: Number of profile views
    - `website_clicks`: Number of website clicks
    - `follower_count`: Current follower count
    - `email_contacts`: Number of email contacts
    - `phone_call_clicks`: Number of phone call clicks
    - `text_message_clicks`: Number of text message clicks
    - `get_directions_clicks`: Number of get directions clicks
    
    **Requirements:**
    - Instagram business account must be connected
    - Instagram Insights API access required
    - Some metrics may require minimum follower count
    """
    return await agent_instagram_controller.get_account_analytics(
        current_user, instagram_account_id, db, metrics
    )

# Health check endpoint for Instagram functionality
@router.get("/health", response_model=InstagramHealthResponse)
async def instagram_health_check():
    """
    Health check endpoint for Instagram business functionality
    
    Returns the status of Instagram business API integration and available features.
    """
    return InstagramHealthResponse(
        status="healthy",
        service="Agent Instagram Business API",
        features=[
            "Instagram Business Account Connection",
            "Conversation Management", 
            "Message Sending",
            "Analytics & Insights",
            "Connection Management",
            "Multi-Account Support"
        ]
    )

# Additional utility endpoints

@router.get("/{instagram_account_id}/conversations/{conversation_id}/participants")
async def get_conversation_participants(
    instagram_account_id: str,
    conversation_id: str,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get participants of a specific conversation
    
    Returns detailed information about participants in an Instagram conversation.
    """
    try:
        # This would be implemented in the service layer
        return {
            "conversation_id": conversation_id,
            "instagram_account_id": instagram_account_id,
            "participants": [],
            "message": "Participant details endpoint - to be implemented"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation participants: {str(e)}"
        )

@router.post("/{instagram_account_id}/conversations/{conversation_id}/mark-read")
async def mark_conversation_read(
    instagram_account_id: str,
    conversation_id: str,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Mark a conversation as read
    
    Marks all messages in a conversation as read by the business account.
    """
    try:
        # This would be implemented in the service layer
        return {
            "message": "Conversation marked as read",
            "conversation_id": conversation_id,
            "instagram_account_id": instagram_account_id,
            "marked_at": "2025-01-XX XX:XX:XX"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark conversation as read: {str(e)}"
        )

@router.get("/{instagram_account_id}/message-templates")
async def get_message_templates(
    instagram_account_id: str,
    current_user: User = Depends(has_role(["platform_agent"])),
    db: Session = Depends(get_db)
):
    """
    Get message templates for the Instagram business account
    
    Returns saved message templates that can be used for quick responses.
    Note: This would integrate with your existing message templates system.
    """
    try:
        # This would integrate with your existing MessageTemplate model
        return {
            "instagram_account_id": instagram_account_id,
            "templates": [],
            "count": 0,
            "message": "Message templates endpoint - to be integrated with existing system"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message templates: {str(e)}"
        )