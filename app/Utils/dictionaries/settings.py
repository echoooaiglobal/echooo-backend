# app/Utils/dictionaries/settings.py

"""
Default settings for the influencer marketing platform
"""
 
DEFAULT_SETTINGS = [
   # OUTREACH AGENTS - Capacity Settings
   {
       "setting_key": "max_concurrent_lists",
       "setting_value": "3",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "active_lists_count",
       "description": "Maximum lists per agent",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "max_concurrent_influencers",
       "setting_value": "100",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "active_influencers_count",
       "description": "Maximum influencers per agent",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "min_influencers_per_list",
       "setting_value": "5",
       "setting_type": "integer",
       "applies_to_table": "campaign_lists",
       "applies_to_field": None,
       "description": "Minimum influencers before assigning list to agent",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   { #need to
       "setting_key": "max_influencers_per_list",
       "setting_value": "200",
       "setting_type": "integer",
       "applies_to_table": "campaign_lists",
       "applies_to_field": None,
       "description": "Maximum influencers allowed in a single list",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   
   # AGENT ASSIGNMENTS - Capacity Settings
   {
        "setting_key": "max_influencers_per_assignment",
        "setting_value": "20",
        "setting_type": "integer",
        "applies_to_table": "agent_assignments",
        "applies_to_field": "assigned_influencers_count",
        "description": "Maximum influencers per single agent assignment",
        "platform_id": None,
        "created_by": None,
        "created_by_type": "system"
    },

   # OUTREACH AGENTS - Daily Message Limits
   {
       "setting_key": "daily_message_limit",
       "setting_value": "20",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "messages_sent_today",
       "description": "Daily message limit per agent (global default)",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "hourly_message_limit",
       "setting_value": "5",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "messages_sent_today",
       "description": "Maximum messages per hour per agent",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "weekly_message_limit",
       "setting_value": "150",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "messages_sent_today",
       "description": "Maximum messages per week per agent",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },

   # INFLUENCER ASSIGNMENTS - Assignment Rules
   {
       "setting_key": "max_attempts_per_agent",
       "setting_value": "3",
       "setting_type": "integer",
       "applies_to_table": "influencer_assignments",
       "applies_to_field": "attempts_made",
       "description": "Maximum attempts before reassignment to another agent",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "reassignment_cooldown_hours",
       "setting_value": "24",
       "setting_type": "integer",
       "applies_to_table": "influencer_assignments",
       "applies_to_field": "assigned_at",
       "description": "Hours before same influencer can be reassigned to same agent",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "auto_reassignment_enabled",
       "setting_value": "true",
       "setting_type": "boolean",
       "applies_to_table": "influencer_assignments",
       "applies_to_field": "assignment_type",
       "description": "Enable automatic reassignment when max attempts reached",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "max_reassignments_per_influencer",
       "setting_value": "5",
       "setting_type": "integer",
       "applies_to_table": "influencer_assignment_history",
       "applies_to_field": None,
       "description": "Maximum times an influencer can be reassigned",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },

   # AUTOMATION SESSIONS - Automation Settings
   {
       "setting_key": "min_delay_between_messages",
       "setting_value": "30",
       "setting_type": "integer",
       "applies_to_table": "automation_sessions",
       "applies_to_field": "automation_settings",
       "description": "Minimum seconds between automated messages",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "max_delay_between_messages",
       "setting_value": "120",
       "setting_type": "integer",
       "applies_to_table": "automation_sessions",
       "applies_to_field": "automation_settings",
       "description": "Maximum seconds between automated messages",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "automation_session_timeout",
       "setting_value": "300",
       "setting_type": "integer",
       "applies_to_table": "automation_sessions",
       "applies_to_field": "timeout_at",
       "description": "Playwright session timeout in minutes",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "max_automation_errors",
       "setting_value": "5",
       "setting_type": "integer",
       "applies_to_table": "automation_sessions",
       "applies_to_field": "max_errors_allowed",
       "description": "Maximum errors before stopping automation session",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "automation_retry_delay",
       "setting_value": "60",
       "setting_type": "integer",
       "applies_to_table": "automation_sessions",
       "applies_to_field": "automation_settings",
       "description": "Seconds to wait before retrying after automation error",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },

   # AGENT SOCIAL CONNECTIONS - OAuth & Token Management
   {
       "setting_key": "oauth_token_renewal_days",
       "setting_value": "7",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "expires_at",
       "description": "Days before token expiry to attempt renewal",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "oauth_token_check_interval",
       "setting_value": "24",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "last_oauth_check_at",
       "description": "Hours between OAuth token validity checks",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "max_oauth_retry_attempts",
       "setting_value": "3",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "automation_error_count",
       "description": "Maximum attempts to renew expired OAuth tokens",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "oauth_connection_timeout",
       "setting_value": "30",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": None,
       "description": "Seconds to wait for OAuth connection response",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "max_connection_errors",
       "setting_value": "5",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "automation_error_count",
       "description": "Maximum errors before disabling social connection",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },

   # GLOBAL SYSTEM SETTINGS
   {
       "setting_key": "working_hours_start",
       "setting_value": "09:00:00",
       "setting_type": "time",
       "applies_to_table": None,
       "applies_to_field": None,
       "description": "System-wide automation start time",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "working_hours_end",
       "setting_value": "18:00:00",
       "setting_type": "time",
       "applies_to_table": None,
       "applies_to_field": None,
       "description": "System-wide automation end time",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "working_days",
       "setting_value": "monday,tuesday,wednesday,thursday,friday",
       "setting_type": "string",
       "applies_to_table": None,
       "applies_to_field": None,
       "description": "Days when automation is allowed",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "system_timezone",
       "setting_value": "UTC",
       "setting_type": "string",
       "applies_to_table": None,
       "applies_to_field": None,
       "description": "Default timezone for all operations",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "daily_limit_reset_time",
       "setting_value": "00:00:00+00:00",
       "setting_type": "time",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "messages_sent_today",
       "description": "Time when daily message counters reset",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },

   # PERFORMANCE & MONITORING
   {
       "setting_key": "min_response_rate_threshold",
       "setting_value": "10",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": None,
       "description": "Minimum response rate percentage for agent performance",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "performance_review_period_days",
       "setting_value": "30",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": None,
       "description": "Days to calculate agent performance metrics",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "auto_pause_low_performers",
       "setting_value": "false",
       "setting_type": "boolean",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "status_id",
       "description": "Automatically pause underperforming agents",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "session_cleanup_hours",
       "setting_value": "24",
       "setting_type": "integer",
       "applies_to_table": "automation_sessions",
       "applies_to_field": "created_at",
       "description": "Hours after which to cleanup old automation sessions",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },

   # PLATFORM-SPECIFIC SETTINGS - INSTAGRAM
   {
       "setting_key": "daily_message_limit",
       "setting_value": "20",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "messages_sent_today",
       "description": "Instagram-specific daily message limit",
       "platform_id": "instagram",  # This would be replaced with actual UUID
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "daily_follow_limit",
       "setting_value": "50",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "automation_capabilities",
       "description": "Instagram daily follow limit",
       "platform_id": "instagram",
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "daily_like_limit",
       "setting_value": "100",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "automation_capabilities",
       "description": "Instagram daily like limit",
       "platform_id": "instagram",
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "story_view_limit",
       "setting_value": "200",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "automation_capabilities",
       "description": "Instagram daily story view limit",
       "platform_id": "instagram",
       "created_by": None,
       "created_by_type": "system"
   },

   # PLATFORM-SPECIFIC SETTINGS - WHATSAPP
#    {
#        "setting_key": "daily_message_limit",
#        "setting_value": "40",
#        "setting_type": "integer",
#        "applies_to_table": "outreach_agents",
#        "applies_to_field": "messages_sent_today",
#        "description": "WhatsApp-specific daily message limit",
#        "platform_id": "whatsapp",  # This would be replaced with actual UUID
#        "created_by": None,
#        "created_by_type": "system"
#    },
#    {
#        "setting_key": "group_message_limit",
#        "setting_value": "10",
#        "setting_type": "integer",
#        "applies_to_table": "agent_social_connections",
#        "applies_to_field": "automation_capabilities",
#        "description": "WhatsApp daily group message limit",
#        "platform_id": "whatsapp",
#        "created_by": None,
#        "created_by_type": "system"
#    },
#    {
#        "setting_key": "broadcast_limit",
#        "setting_value": "5",
#        "setting_type": "integer",
#        "applies_to_table": "agent_social_connections",
#        "applies_to_field": "automation_capabilities",
#        "description": "WhatsApp daily broadcast limit",
#        "platform_id": "whatsapp",
#        "created_by": None,
#        "created_by_type": "system"
#    },

   # PLATFORM-SPECIFIC SETTINGS - TIKTOK
   {
       "setting_key": "daily_message_limit",
       "setting_value": "20",
       "setting_type": "integer",
       "applies_to_table": "outreach_agents",
       "applies_to_field": "messages_sent_today",
       "description": "TikTok-specific daily message limit",
       "platform_id": "tiktok",  # This would be replaced with actual UUID
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "daily_comment_limit",
       "setting_value": "30",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "automation_capabilities",
       "description": "TikTok daily comment limit",
       "platform_id": "tiktok",
       "created_by": None,
       "created_by_type": "system"
   },

   # EMERGENCY & SAFETY SETTINGS
   {
       "setting_key": "emergency_stop_enabled",
       "setting_value": "true",
       "setting_type": "boolean",
       "applies_to_table": None,
       "applies_to_field": None,
       "description": "Global emergency stop for all automation",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "max_daily_errors_global",
       "setting_value": "100",
       "setting_type": "integer",
       "applies_to_table": None,
       "applies_to_field": None,
       "description": "Max errors across all agents before emergency stop",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "auto_pause_on_rate_limit",
       "setting_value": "true",
       "setting_type": "boolean",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "status_id",
       "description": "Automatically pause agents when rate limited",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   },
   {
       "setting_key": "rate_limit_pause_duration",
       "setting_value": "3600",
       "setting_type": "integer",
       "applies_to_table": "agent_social_connections",
       "applies_to_field": "last_error_at",
       "description": "Seconds to pause after rate limit detected",
       "platform_id": None,
       "created_by": None,
       "created_by_type": "system"
   }
]