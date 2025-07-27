# app/Models/__init__.py

from .base import Base

# Existing models
from app.Models.auth_models import (
    User, Role, Permission, RolePermission, RefreshToken, EmailVerificationToken,
    UserStatus, user_roles
)
from app.Models.oauth_accounts import OAuthAccount
from app.Models.company_models import Company, CompanyUser
from app.Models.influencers import Influencer
from app.Models.social_accounts import SocialAccount
from app.Models.influencer_contacts import InfluencerContact
from app.Models.campaigns import Campaign
from app.Models.message_templates import MessageTemplate
from app.Models.campaign_lists import CampaignList
from app.Models.statuses import Status
from app.Models.influencer_outreach import InfluencerOutreach
from app.Models.order_models import Order, OrderItem
from app.Models.platforms import Platform
from app.Models.categories import Category

# New outreach models
from app.Models.system_settings import Settings
from app.Models.communication_channels import CommunicationChannel
from app.Models.outreach_agents import OutreachAgent
from app.Models.agent_social_connections import AgentSocialConnection
from app.Models.agent_assignments import AgentAssignment
from app.Models.automation_sessions import AutomationSession
from app.Models.campaign_influencers import CampaignInfluencer
from app.Models.assigned_influencers import AssignedInfluencer
from app.Models.reassignment_reasons import ReassignmentReason
from app.Models.influencer_assignment_histories import InfluencerAssignmentHistory

__all__ = [
    'Base',
    # Existing models
    'User', 'Role', 'Permission', 'RolePermission', 'RefreshToken', 'UserStatus', 'EmailVerificationToken',
    'user_roles',
    'OAuthAccount',
    'Company', 'CompanyUser',
    'Influencer', 'SocialAccount', 'InfluencerContact',
    'Campaign', 'CampaignList', 'MessageTemplate',
    'Status', 'InfluencerOutreach',
    'Order', 'OrderItem',
    'Platform', 'Category', 'Permission', 'RolePermission',
    # New outreach models
    'Settings',
    'CommunicationChannel',
    'OutreachAgent',
    'AgentSocialConnection', 
    'AgentAssignment',
    'AutomationSession',
    'CampaignInfluencer',
    'AssignedInfluencer',
    'ReassignmentReason',
    'InfluencerAssignmentHistory'
]