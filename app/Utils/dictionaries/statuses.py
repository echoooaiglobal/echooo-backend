# app/Utils/dictionaries/statuses.py

"""
Default statuses for the influencer marketing platform
"""

DEFAULT_STATUSES = [
    # list_member statuses
    {"model": "list_member", "name": "discovered"},
    {"model": "list_member", "name": "contacted"},
    {"model": "list_member", "name": "responded"},
    {"model": "list_member", "name": "negotiating"},
    {"model": "list_member", "name": "onboarded"},
    {"model": "list_member", "name": "accepted"},
    {"model": "list_member", "name": "declined"},
    
    # outreach statuses
    {"model": "outreach", "name": "sent"},
    {"model": "outreach", "name": "delivered"},
    {"model": "outreach", "name": "read"},
    {"model": "outreach", "name": "failed"},

    # campaign statuses
    {"model": "campaign", "name": "draft"},
    {"model": "campaign", "name": "planning"},
    {"model": "campaign", "name": "active"},
    {"model": "campaign", "name": "paused"},
    {"model": "campaign", "name": "completed"},
    {"model": "campaign", "name": "cancelled"},
    
    # list_assignment statuses
    {"model": "list_assignment", "name": "pending"},
    {"model": "list_assignment", "name": "active"},
    {"model": "list_assignment", "name": "completed"},
    {"model": "list_assignment", "name": "failed"},
    
    # NEW: agent statuses
    {"model": "agent", "name": "active"},
    {"model": "agent", "name": "inactive"},
    {"model": "agent", "name": "suspended"}
]