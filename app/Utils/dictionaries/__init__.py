# app/Utils/dictionaries/__init__.py
"""
Dictionary data for the influencer marketing platform
Contains reference data like categories, platforms, etc.
"""

from .categories import DEFAULT_CATEGORIES
from .platforms import DEFAULT_PLATFORMS
from .statuses import DEFAULT_STATUSES
from .communication_channels import DEFAULT_COMMUNICATION_CHANNELS
from .roles import DEFAULT_ROLES
from .permissions import DEFAULT_PERMISSIONS
from .settings import DEFAULT_SETTINGS
from .default_reassignment_reasons import DEFAULT_REASSIGNMENT_REASONS
from .default_accounts import DEFAULT_ACCOUNTS


__all__ = [
    'DEFAULT_CATEGORIES',
    'DEFAULT_PLATFORMS',
    'DEFAULT_STATUSES',
    'DEFAULT_COMMUNICATION_CHANNELS',
    'DEFAULT_ROLES',
    'DEFAULT_PERMISSIONS',
    'DEFAULT_SETTINGS',
    'DEFAULT_REASSIGNMENT_REASONS',
    'DEFAULT_ACCOUNTS'
]