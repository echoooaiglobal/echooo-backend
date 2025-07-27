# app/Utils/dictionaries/default_reassignment_reasons.py

"""
Default reassignment reasons for the influencer marketing platform
"""

DEFAULT_REASSIGNMENT_REASONS = [
    {
        "code": "max_attempts_reached",
        "name": "Maximum Attempts Reached",
        "description": "Agent has reached the maximum number of contact attempts for this influencer",
        "is_system_triggered": True,
        "is_user_triggered": False,
        "is_active": True,
        "display_order": 1
    },
    {
        "code": "agent_unavailable",
        "name": "Agent Unavailable",
        "description": "Agent is temporarily unavailable or suspended",
        "is_system_triggered": True,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 2
    },
    {
        "code": "manual_reassignment",
        "name": "Manual Reassignment",
        "description": "Manual reassignment by admin or supervisor",
        "is_system_triggered": False,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 3
    },
    {
        "code": "load_balancing",
        "name": "Load Balancing",
        "description": "Reassignment for better workload distribution among agents",
        "is_system_triggered": True,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 4
    },
    {
        "code": "agent_request",
        "name": "Agent Request",
        "description": "Agent requested to transfer this assignment",
        "is_system_triggered": False,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 5
    },
    {
        "code": "performance_based",
        "name": "Performance Based",
        "description": "Reassignment due to agent performance metrics",
        "is_system_triggered": True,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 6
    },
    {
        "code": "strategy_change",
        "name": "Strategy Change",
        "description": "Campaign strategy or approach change requiring different agent skills",
        "is_system_triggered": False,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 7
    },
    {
        "code": "agent_specialization",
        "name": "Agent Specialization",
        "description": "Reassignment to agent with better specialization for this influencer type",
        "is_system_triggered": True,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 8
    },
    {
        "code": "technical_issues",
        "name": "Technical Issues",
        "description": "Technical problems preventing agent from contacting influencer",
        "is_system_triggered": True,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 9
    },
    {
        "code": "influencer_preference",
        "name": "Influencer Preference",
        "description": "Influencer requested different point of contact",
        "is_system_triggered": False,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 10
    },
    {
        "code": "timezone_optimization",
        "name": "Timezone Optimization",
        "description": "Reassignment to agent in better timezone for influencer",
        "is_system_triggered": True,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 11
    },
    {
        "code": "language_barrier",
        "name": "Language Barrier",
        "description": "Reassignment due to language or communication barriers",
        "is_system_triggered": False,
        "is_user_triggered": True,
        "is_active": True,
        "display_order": 12
    }
]