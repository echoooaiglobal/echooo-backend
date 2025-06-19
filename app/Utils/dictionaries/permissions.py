# app/Utils/dictionaries/roles.py

"""
Default roles for the influencer marketing platform
"""

DEFAULT_PERMISSIONS = [
    {"name": "user:create", "description": "Create users"},
    {"name": "user:read", "description": "Read user details"},
    {"name": "user:update", "description": "Update user details"},
    {"name": "user:delete", "description": "Delete users"},
    {"name": "company:create", "description": "Create companies"},
    {"name": "company:read", "description": "Read company details"},
    {"name": "company:update", "description": "Update company details"},
    {"name": "company:delete", "description": "Delete companies"},
    {"name": "campaign:create", "description": "Create campaigns"},
    {"name": "campaign:read", "description": "Read campaign details"},
    {"name": "campaign:update", "description": "Update campaign details"},
    {"name": "campaign:delete", "description": "Delete campaigns"},
    {"name": "influencer:create", "description": "Create influencer profiles"},
    {"name": "influencer:read", "description": "Read influencer details"},
    {"name": "influencer:update", "description": "Update influencer details"},
    {"name": "influencer:delete", "description": "Delete influencer profiles"},
    # New influencer_contacts permissions
    {"name": "influencer_contacts:create", "description": "Create influencer contacts"},
    {"name": "influencer_contacts:read", "description": "Read influencer contact details"},
    {"name": "influencer_contacts:update", "description": "Update influencer contact details"},
    {"name": "influencer_contacts:delete", "description": "Delete influencer contacts"},
    # NEW: Analytics permissions
    {"name": "profile_analytics:create", "description": "Create profile analytics"},
    {"name": "profile_analytics:read", "description": "Read profile analytics"},
    {"name": "profile_analytics:update", "description": "Update profile analytics"},
    {"name": "profile_analytics:delete", "description": "Delete profile analytics"}
]