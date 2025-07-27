# app/Utils/dictionaries/default_accounts.py

"""
Default accounts for the influencer marketing platform
Contains default user accounts that should be created during system initialization
"""

DEFAULT_ACCOUNTS = {
    "platform_super_admin": {
        "email": "superadmin@echooo.ai",
        "password": "SuperAdmin@123",  # In production, use environment variable or generated password
        "full_name": "Platform Super Administrator",
        "user_type": "platform",
        "role_name": "platform_super_admin",
        "phone_number": None,
        "description": "Default platform super administrator account with full system access"
    }
    # Future accounts can be added here like:
    # "platform_developer": {
    #     "email": "developer@echooo.ai",
    #     "password": "Developer@123",
    #     "full_name": "Platform Developer",
    #     "user_type": "platform", 
    #     "role_name": "platform_developer",
    #     "phone_number": None,
    #     "description": "Default platform developer account"
    # },
    # "platform_support": {
    #     "email": "support@echooo.ai",
    #     "password": "Support@123",
    #     "full_name": "Customer Support",
    #     "user_type": "platform",
    #     "role_name": "platform_customer_support", 
    #     "phone_number": None,
    #     "description": "Default customer support account"
    # }
}