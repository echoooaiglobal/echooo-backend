# app/Utils/dictionaries/statuses.py

"""
Default statuses for the influencer marketing platform
"""

DEFAULT_STATUSES = [
   # campaign_lists statuses
   {"model": "campaign_list", "name": "draft"},        # List is being created/edited
   {"model": "campaign_list", "name": "active"},       # List is ready for agent assignment
   {"model": "campaign_list", "name": "paused"},       # List work temporarily stopped
   {"model": "campaign_list", "name": "completed"},    # All influencers processed
   {"model": "campaign_list", "name": "cancelled"},    # List work permanently stopped
   
   # campaign_influencers statuses
   {"model": "campaign_influencer", "name": "discovered"},      # Found and added to list
   {"model": "campaign_influencer", "name": "unreachable"},     # Cannot contact (bad profile, blocked, etc.)
   {"model": "campaign_influencer", "name": "contacted"},       # Agent sent first message
   {"model": "campaign_influencer", "name": "responded"},       # Influencer replied to contact
   {"model": "campaign_influencer", "name": "info_requested"},  # Asked for collaboration details/rates
   {"model": "campaign_influencer", "name": "completed"},       # Got phone number and rates - PURPOSE COMPLETE
   {"model": "campaign_influencer", "name": "declined"},        # Refused to provide information
   {"model": "campaign_influencer", "name": "inactive"},        # No longer responsive after multiple attempts
   
   # assigned_influencers statuses
   # {"model": "assigned_influencer", "name": "in_progress"},         # Agent actively working on influencer
   {"model": "assigned_influencer", "name": "assigned"},            # Just assigned to agent
   {"model": "assigned_influencer", "name": "awaiting_response"},   # Waiting for influencer reply
   {"model": "assigned_influencer", "name": "max_attempts_reached"}, # Ready for reassignment to another agent
   {"model": "assigned_influencer", "name": "archived"},            # No longer active for this agent
   {"model": "assigned_influencer", "name": "completed"},           # Successfully got response/info
   {"model": "assigned_influencer", "name": "transferred"},         # Manually moved to another agent
   {"model": "assigned_influencer", "name": "failed"},              # Technical or other failure
   
   # outreach_agents statuses
   {"model": "outreach_agent", "name": "active"},       # Available for assignments and work
   {"model": "outreach_agent", "name": "inactive"},     # User-controlled, no new assignments
   {"model": "outreach_agent", "name": "suspended"},    # Admin suspended, all work paused
   {"model": "outreach_agent", "name": "maintenance"},  # System maintenance mode
   {"model": "outreach_agent", "name": "training"},     # Agent in training, limited assignments
   
   # agent_social_connections statuses
   {"model": "agent_social_connection", "name": "not_connected"},      # No OAuth connection established
   {"model": "agent_social_connection", "name": "connected"},          # OAuth active and working
   {"model": "agent_social_connection", "name": "expired"},            # OAuth token expired, needs renewal
   {"model": "agent_social_connection", "name": "error"},              # Connection has technical issues
   {"model": "agent_social_connection", "name": "suspended"},          # Temporarily disabled by admin
   {"model": "agent_social_connection", "name": "rate_limited"},       # Platform imposed rate limits
   {"model": "agent_social_connection", "name": "permission_revoked"}, # User revoked OAuth permissions
   
   # agent_assignments statuses
   {"model": "agent_assignment", "name": "active"},      # Agent actively working on this list
   {"model": "agent_assignment", "name": "paused"},      # Temporarily stopped work on list
   {"model": "agent_assignment", "name": "completed"},   # All assigned influencers finished
   {"model": "agent_assignment", "name": "cancelled"},   # Assignment removed/cancelled
   {"model": "agent_assignment", "name": "overloaded"},  # Agent has too many assignments
   
   # automation_sessions statuses
   {"model": "automation_session", "name": "starting"},   # Playwright session initializing
   {"model": "automation_session", "name": "active"},     # Automation currently running
   {"model": "automation_session", "name": "paused"},     # Automation temporarily stopped
   {"model": "automation_session", "name": "completed"},  # Session finished successfully
   {"model": "automation_session", "name": "failed"},     # Session failed due to errors
   {"model": "automation_session", "name": "timeout"},    # Session exceeded time limit
   {"model": "automation_session", "name": "cancelled"},  # Session manually stopped
   
   # influencer_outreach statuses (existing - for message tracking)
   {"model": "influencer_outreach", "name": "sent"},       # Message successfully sent
   {"model": "influencer_outreach", "name": "delivered"},  # Message delivered to recipient
   {"model": "influencer_outreach", "name": "read"},       # Message read by recipient
   {"model": "influencer_outreach", "name": "failed"},     # Message failed to send

   # campaign statuses (existing - for campaign management)
   {"model": "campaign", "name": "draft"},      # Campaign being created
   {"model": "campaign", "name": "planning"},   # Campaign being planned
   {"model": "campaign", "name": "active"},     # Campaign currently running
   {"model": "campaign", "name": "paused"},     # Campaign temporarily stopped
   {"model": "campaign", "name": "completed"},  # Campaign finished
   {"model": "campaign", "name": "cancelled"},  # Campaign permanently stopped
   
]