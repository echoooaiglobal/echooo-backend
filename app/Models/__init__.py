# app/Models/__init__.py
from app.Models.base import Base
from app.Models.auth_models import (
    User, Role, Permission, RolePermission, RefreshToken,
    UserStatus, user_roles
)
from app.Models.company_models import (
    Company, CompanyUser, CompanyContact
)
from app.Models.influencer_models import (
    Influencer, InfluencerSocialAccount, InfluencerContact
)
from app.Models.support_models import (
    Platform, Category
)

# This makes it easier to import models elsewhere
__all__ = [
    'Base',
    'User', 'Role', 'Permission', 'RolePermission', 'RefreshToken', 'UserStatus',
    'user_roles',
    'Company', 'CompanyUser', 'CompanyContact',
    'Influencer', 'InfluencerSocialAccount', 'InfluencerContact',
    'Platform', 'Category'
]