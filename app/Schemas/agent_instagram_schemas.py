# app/Schemas/agent_instagram_schemas.py
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

# Instagram Business Account Schemas
class InstagramBusinessAccountInfo(BaseModel):
    instagram_account_id: str
    page_id: str
    page_name: str
    instagram_username: Optional[str] = None
    instagram_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    followers_count: Optional[int] = None
    media_count: Optional[int] = None
    is_connected: bool = False

class InstagramBusinessAccountsResponse(BaseModel):
    business_accounts: List[InstagramBusinessAccountInfo]
    count: int
    message: str

# Connected Instagram Account Schemas
class ConnectedInstagramAccount(BaseModel):
    connection_id: str
    instagram_account_id: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    facebook_page_id: Optional[str] = None
    facebook_page_name: Optional[str] = None
    connected_at: str
    last_updated: str
    connection_type: str

class ConnectedAccountsResponse(BaseModel):
    connected_accounts: List[ConnectedInstagramAccount]
    count: int
    user_id: str

# Instagram Conversation Schemas
class InstagramParticipant(BaseModel):
    id: str
    name: Optional[str] = None
    username: Optional[str] = None

class InstagramConversation(BaseModel):
    id: str
    updated_time: Optional[str] = None
    can_reply: Optional[bool] = None
    message_count: Optional[int] = None
    unread_count: Optional[int] = None
    participants: Optional[Dict[str, Any]] = None

class InstagramConversationsResponse(BaseModel):
    conversations: List[InstagramConversation]
    instagram_account_id: str
    count: int

# Instagram Message Schemas
class InstagramMessageFrom(BaseModel):
    id: str
    name: Optional[str] = None
    username: Optional[str] = None

class InstagramMessageAttachment(BaseModel):
    type: Optional[str] = None
    url: Optional[str] = None
    size: Optional[int] = None

class InstagramMessage(BaseModel):
    id: str
    created_time: Optional[str] = None
    message: Optional[str] = None
    attachments: Optional[List[InstagramMessageAttachment]] = None
    from_: Optional[InstagramMessageFrom] = None
    to: Optional[List[InstagramMessageFrom]] = None

    class Config:
        # Handle the 'from' field which is a Python keyword
        allow_population_by_field_name = True
        fields = {
            'from_': {'alias': 'from'}
        }

class InstagramMessagesResponse(BaseModel):
    messages: List[InstagramMessage]
    conversation_id: str
    instagram_account_id: str
    count: int
    limit: int

# Request Schemas
class ConnectBusinessAccountRequest(BaseModel):
    instagram_account_id: str
    page_id: str
    page_access_token: str
    instagram_username: str
    page_name: Optional[str] = "Unknown Page"
    
    @field_validator('instagram_account_id', 'page_id', 'page_access_token', 'instagram_username')
    @classmethod
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Field cannot be empty')
        return v.strip()

class SendMessageRequest(BaseModel):
    recipient_id: str
    message: str
    
    @field_validator('recipient_id')
    @classmethod
    def validate_recipient_id(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Recipient ID cannot be empty')
        return v.strip()
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Message cannot be empty')
        if len(v.strip()) > 1000:
            raise ValueError('Message too long (max 1000 characters)')
        return v.strip()

class SendMessageResponse(BaseModel):
    message: str
    result: Dict[str, Any]
    instagram_account_id: str
    recipient_id: str
    sent_message: str
    sent_by: str

# Analytics Schemas
class InstagramAccountInfo(BaseModel):
    id: str
    username: Optional[str] = None
    name: Optional[str] = None
    followers_count: Optional[int] = None
    media_count: Optional[int] = None
    profile_picture_url: Optional[str] = None

class InstagramInsightMetric(BaseModel):
    name: str
    period: str
    values: List[Dict[str, Any]]
    title: Optional[str] = None
    description: Optional[str] = None

class InstagramInsights(BaseModel):
    data: List[InstagramInsightMetric]
    paging: Optional[Dict[str, Any]] = None

class InstagramAnalyticsResponse(BaseModel):
    instagram_account_id: str
    account_info: Optional[InstagramAccountInfo] = None
    insights: Optional[InstagramInsights] = None
    connection_status: Optional[str] = None
    error: Optional[str] = None
    retrieved_at: str

# Connection Status Schemas
class ConnectionStatusResponse(BaseModel):
    instagram_account_id: str
    connection_status: str  # "connected" or "not_connected"
    connection_id: Optional[str] = None
    username: Optional[str] = None
    facebook_page_id: Optional[str] = None
    facebook_page_name: Optional[str] = None
    connected_at: Optional[str] = None
    last_updated: Optional[str] = None
    message: Optional[str] = None

# Disconnect Account Schemas
class DisconnectAccountResponse(BaseModel):
    message: str
    instagram_account_id: str
    disconnected_at: str

# Error Schemas
class InstagramErrorResponse(BaseModel):
    error: str
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    instagram_account_id: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

# Success Response
class InstagramSuccessResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
    instagram_account_id: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

# Health Check Schema
class InstagramHealthResponse(BaseModel):
    status: str
    service: str
    features: List[str]
    timestamp: datetime = datetime.utcnow()

# Query Parameters
class ConversationMessagesQuery(BaseModel):
    limit: int = 50
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        if v < 1:
            return 1
        if v > 100:
            return 100
        return v

class AnalyticsQuery(BaseModel):
    metrics: Optional[List[str]] = None
    period: Optional[str] = "day"
    
    @field_validator('period')
    @classmethod
    def validate_period(cls, v):
        valid_periods = ["day", "week", "days_28", "lifetime"]
        if v not in valid_periods:
            return "day"
        return v
    
    @field_validator('metrics')
    @classmethod
    def validate_metrics(cls, v):
        if not v:
            return ["impressions", "reach", "profile_views", "website_clicks", "follower_count"]
        
        valid_metrics = [
            "impressions", "reach", "profile_views", "website_clicks", 
            "follower_count", "email_contacts", "phone_call_clicks", 
            "text_message_clicks", "get_directions_clicks"
        ]
        
        # Filter out invalid metrics
        return [metric for metric in v if metric in valid_metrics]