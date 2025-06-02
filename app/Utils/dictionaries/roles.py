# app/Utils/dictionaries/roles.py

"""
Default roles for the influencer marketing platform
"""


DEFAULT_ROLES = [
    
    # platform-specific roles
    {"name": "platform_admin", "description": "Platform administrator with full access"},
    {"name": "platform_user", "description": "Platform staff member"},
    {"name": "platform_manager", "description": "Platform manager with oversight across functions"},
    {"name": "platform_accountant", "description": "Handles platform financial matters"},
    {"name": "platform_developer", "description": "Technical developer role for platform"},
    {"name": "platform_customer_support", "description": "Customer support agent for platform"},
    {"name": "platform_content_moderator", "description": "Content moderation role for platform"},
    {"name": "platform_agent", "description": "Agent handeling company campaigns lists"},
    
    # company-specific roles
    {"name": "company_admin", "description": "Company administrator"},
    {"name": "company_user", "description": "Company user"},
    {"name": "company_manager", "description": "Manager role within a company"},
    {"name": "company_accountant", "description": "Handles company financial matters"},
    {"name": "company_marketer", "description": "Marketing specialist for company"},
    {"name": "company_content_creator", "description": "Content creation role for company"},

    # influencer-specific roles
    {"name": "influencer", "description": "Influencer user"},
    {"name": "influencer_manager", "description": "Influencer manager"},
]