# app/Utils/dictionaries/__init__.py
"""
Dictionary data for the influencer marketing platform
Contains reference data like categories, platforms, etc.
"""

from .categories import DEFAULT_CATEGORIES
from .platforms import DEFAULT_PLATFORMS
from .statuses import DEFAULT_STATUSES
from .messageChannels import DEFAULT_MESSAGE_CHANNNELS
from .roles import DEFAULT_ROLES
from .permissions import DEFAULT_PERMISSIONS


__all__ = [
    'DEFAULT_CATEGORIES',
    'DEFAULT_PLATFORMS',
    'DEFAULT_STATUSES',
    'DEFAULT_MESSAGE_CHANNNELS',
    'DEFAULT_ROLES',
    'DEFAULT_PERMISSIONS'
]