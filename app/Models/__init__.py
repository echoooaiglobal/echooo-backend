# app/Models/__init__.py
from app.Models.base import Base
from app.Models.auth_models import (
    User, Role, Permission, RolePermission, RefreshToken, EmailVerificationToken,
    UserStatus, user_roles
)
from app.Models.company_models import (
    Company, CompanyUser, CompanyContact
)
from app.Models.influencer_models import (
    Influencer, SocialAccount, InfluencerContact
)
from app.Models.support_models import (
    Platform, Category
)
from app.Models.campaign_models import (
    Status, MessageChannel, Agent, Campaign, 
    CampaignList, 
    ListAssignment, InfluencerOutreach
)
from app.Models.message_templates import (
    MessageTemplate
)

from app.Models.campaign_list_members import (
    CampaignListMember
)

from app.Models.results import (
    Result
)

from app.Models.profile_analytics import ProfileAnalytics


# This makes it easier to import models elsewhere
__all__ = [
    'Base',
    'User', 'Role', 'Permission', 'RolePermission', 'RefreshToken', 'UserStatus', 'EmailVerificationToken',
    'user_roles',
    'Company', 'CompanyUser', 'CompanyContact',
    'Influencer', 'SocialAccount', 'InfluencerContact',
    'Platform', 'Category',
    'Status', 'MessageChannel', 'Agent', 'Campaign',
    'CampaignList', 'CampaignListMember', 'MessageTemplate',
    'ListAssignment', 'InfluencerOutreach', 'Result', 'ProfileAnalytics'
]