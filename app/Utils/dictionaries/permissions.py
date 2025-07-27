# app/Utils/dictionaries/permissions.py

DEFAULT_PERMISSIONS = [
    # ========== AUTH & USER MANAGEMENT ==========
    {"name": "user:create", "description": "Create users"},
    {"name": "user:read", "description": "Read user details"},
    {"name": "user:update", "description": "Update user details"},
    {"name": "user:delete", "description": "Delete users"},
    {"name": "user:verify", "description": "Verify user emails"},
    {"name": "user:reset_password", "description": "Reset user passwords"},
    {"name": "user:change_status", "description": "Change user status (active/inactive/suspended)"},
    
    # ========== ROLE & PERMISSION MANAGEMENT ==========
    {"name": "role:create", "description": "Create roles"},
    {"name": "role:read", "description": "Read role details"},
    {"name": "role:update", "description": "Update role details"},
    {"name": "role:delete", "description": "Delete roles"},
    {"name": "role:assign", "description": "Assign roles to users"},
    
    {"name": "permission:create", "description": "Create permissions"},
    {"name": "permission:read", "description": "Read permission details"},
    {"name": "permission:update", "description": "Update permission details"},
    {"name": "permission:delete", "description": "Delete permissions"},
    {"name": "permission:assign", "description": "Assign permissions to roles"},
    
    # ========== OAUTH & AUTHENTICATION ==========
    {"name": "oauth:create", "description": "Create OAuth connections"},
    {"name": "oauth:read", "description": "Read OAuth account details"},
    {"name": "oauth:update", "description": "Update OAuth connections"},
    {"name": "oauth:delete", "description": "Delete OAuth connections"},
    {"name": "oauth:refresh", "description": "Refresh OAuth tokens"},
    
    {"name": "refresh_token:create", "description": "Create refresh tokens"},
    {"name": "refresh_token:read", "description": "Read refresh token details"},
    {"name": "refresh_token:update", "description": "Update refresh tokens"},
    {"name": "refresh_token:delete", "description": "Delete refresh tokens"},
    {"name": "refresh_token:revoke", "description": "Revoke refresh tokens"},
    
    {"name": "email_verification:create", "description": "Create email verification tokens"},
    {"name": "email_verification:read", "description": "Read email verification details"},
    {"name": "email_verification:verify", "description": "Verify email verification tokens"},
    {"name": "email_verification:resend", "description": "Resend email verification"},
    
    # ========== COMPANY MANAGEMENT ==========
    {"name": "company:create", "description": "Create companies"},
    {"name": "company:read", "description": "Read company details"},
    {"name": "company:update", "description": "Update company details"},
    {"name": "company:delete", "description": "Delete companies"},
    {"name": "company:soft_delete", "description": "Soft delete companies"},
    {"name": "company:restore", "description": "Restore soft-deleted companies"},
    
    {"name": "company_user:create", "description": "Create company users"},
    {"name": "company_user:read", "description": "Read company user details"},
    {"name": "company_user:update", "description": "Update company users"},
    {"name": "company_user:delete", "description": "Delete company users"},
    {"name": "company_user:invite", "description": "Invite users to companies"},
    
    {"name": "company_contact:create", "description": "Create company contacts"},
    {"name": "company_contact:read", "description": "Read company contact details"},
    {"name": "company_contact:update", "description": "Update company contacts"},
    {"name": "company_contact:delete", "description": "Delete company contacts"},
    
    # ========== CAMPAIGN MANAGEMENT ==========
    {"name": "campaign:create", "description": "Create campaigns"},
    {"name": "campaign:read", "description": "Read campaign details"},
    {"name": "campaign:update", "description": "Update campaign details"},
    {"name": "campaign:delete", "description": "Delete campaigns"},
    {"name": "campaign:publish", "description": "Publish campaigns"},
    {"name": "campaign:archive", "description": "Archive campaigns"},
    {"name": "campaign:duplicate", "description": "Duplicate campaigns"},
    
    # ========== CAMPAIGN LISTS ==========
    {"name": "campaign_list:create", "description": "Create campaign lists"},
    {"name": "campaign_list:read", "description": "Read campaign list details"},
    {"name": "campaign_list:update", "description": "Update campaign lists"},
    {"name": "campaign_list:delete", "description": "Delete campaign lists"},
    {"name": "campaign_list:export", "description": "Export campaign lists"},
    {"name": "campaign_list:import", "description": "Import campaign lists"},
    
    # ========== CAMPAIGN INFLUENCERS ==========
    {"name": "campaign_influencer:create", "description": "Create campaign influencer records"},
    {"name": "campaign_influencer:read", "description": "Read campaign influencer details"},
    {"name": "campaign_influencer:update", "description": "Update campaign influencer records"},
    {"name": "campaign_influencer:delete", "description": "Delete campaign influencer records"},
    {"name": "campaign_influencer:onboard", "description": "Onboard campaign influencers"},
    {"name": "campaign_influencer:bulk_update", "description": "Bulk update campaign influencers"},
    
    # ========== MESSAGE TEMPLATES ==========
    {"name": "message_template:create", "description": "Create message templates"},
    {"name": "message_template:read", "description": "Read message template details"},
    {"name": "message_template:update", "description": "Update message templates"},
    {"name": "message_template:delete", "description": "Delete message templates"},
    {"name": "message_template:clone", "description": "Clone message templates"},
    
    # ========== INFLUENCER MANAGEMENT ==========
    {"name": "influencer:create", "description": "Create influencer profiles"},
    {"name": "influencer:read", "description": "Read influencer details"},
    {"name": "influencer:update", "description": "Update influencer profiles"},
    {"name": "influencer:delete", "description": "Delete influencer profiles"},
    {"name": "influencer:verify", "description": "Verify influencer profiles"},
    {"name": "influencer:ban", "description": "Ban influencer accounts"},
    {"name": "influencer:export", "description": "Export influencer data"},
    
    # ========== SOCIAL ACCOUNTS ==========
    {"name": "social_account:create", "description": "Create social account records"},
    {"name": "social_account:read", "description": "Read social account details"},
    {"name": "social_account:update", "description": "Update social account records"},
    {"name": "social_account:delete", "description": "Delete social account records"},
    {"name": "social_account:verify", "description": "Verify social accounts"},
    {"name": "social_account:refresh", "description": "Refresh social account data"},
    
    # ========== INFLUENCER CONTACTS ==========
    {"name": "influencer_contact:create", "description": "Create influencer contacts"},
    {"name": "influencer_contact:read", "description": "Read influencer contact details"},
    {"name": "influencer_contact:update", "description": "Update influencer contacts"},
    {"name": "influencer_contact:delete", "description": "Delete influencer contacts"},
    
    # ========== PLATFORMS & CATEGORIES ==========
    {"name": "platform:create", "description": "Create social media platforms"},
    {"name": "platform:read", "description": "Read platform details"},
    {"name": "platform:update", "description": "Update platform details"},
    {"name": "platform:delete", "description": "Delete platforms"},
    
    {"name": "category:create", "description": "Create categories"},
    {"name": "category:read", "description": "Read category details"},
    {"name": "category:update", "description": "Update categories"},
    {"name": "category:delete", "description": "Delete categories"},
    
    # ========== STATUSES ==========
    {"name": "status:create", "description": "Create status records"},
    {"name": "status:read", "description": "Read status details"},
    {"name": "status:update", "description": "Update status records"},
    {"name": "status:delete", "description": "Delete status records"},
    
    # ========== COMMUNICATION CHANNELS ==========
    {"name": "communication_channel:create", "description": "Create communication channels"},
    {"name": "communication_channel:read", "description": "Read communication channel details"},
    {"name": "communication_channel:update", "description": "Update communication channels"},
    {"name": "communication_channel:delete", "description": "Delete communication channels"},
    
    # ========== OUTREACH AGENTS ==========
    {"name": "outreach_agent:create", "description": "Create outreach agents"},
    {"name": "outreach_agent:read", "description": "Read outreach agent details"},
    {"name": "outreach_agent:update", "description": "Update outreach agents"},
    {"name": "outreach_agent:delete", "description": "Delete outreach agents"},
    {"name": "outreach_agent:activate", "description": "Activate/deactivate outreach agents"},
    {"name": "outreach_agent:performance", "description": "View outreach agent performance metrics"},
    
    # ========== AGENT SOCIAL CONNECTIONS ==========
    {"name": "agent_social_connection:create", "description": "Create agent social connections"},
    {"name": "agent_social_connection:read", "description": "Read agent social connection details"},
    {"name": "agent_social_connection:update", "description": "Update agent social connections"},
    {"name": "agent_social_connection:delete", "description": "Delete agent social connections"},
    {"name": "agent_social_connection:validate", "description": "Validate agent social connection tokens"},
    {"name": "agent_social_connection:refresh", "description": "Refresh agent social connection tokens"},
    
    # ========== AGENT ASSIGNMENTS ==========
    {"name": "agent_assignment:create", "description": "Create agent assignments"},
    {"name": "agent_assignment:read", "description": "Read agent assignment details"},
    {"name": "agent_assignment:update", "description": "Update agent assignments"},
    {"name": "agent_assignment:delete", "description": "Delete agent assignments"},
    {"name": "agent_assignment:transfer", "description": "Transfer agent assignments"},
    {"name": "agent_assignment:bulk_assign", "description": "Bulk assign agents"},
    
    # ========== ASSIGNED INFLUENCERS ==========
    {"name": "assigned_influencer:create", "description": "Create assigned influencer records"},
    {"name": "assigned_influencer:read", "description": "Read assigned influencer details"},
    {"name": "assigned_influencer:update", "description": "Update assigned influencer records"},
    {"name": "assigned_influencer:delete", "description": "Delete assigned influencer records"},
    {"name": "assigned_influencer:transfer", "description": "Transfer assigned influencers"},
    {"name": "assigned_influencer:archive", "description": "Archive assigned influencers"},
    {"name": "assigned_influencer:bulk_update", "description": "Bulk update assigned influencers"},
    
    # ========== INFLUENCER OUTREACH ==========
    {"name": "influencer_outreach:create", "description": "Create outreach records"},
    {"name": "influencer_outreach:read", "description": "Read outreach details"},
    {"name": "influencer_outreach:update", "description": "Update outreach records"},
    {"name": "influencer_outreach:delete", "description": "Delete outreach records"},
    {"name": "influencer_outreach:send", "description": "Send outreach messages"},
    {"name": "influencer_outreach:bulk_send", "description": "Bulk send outreach messages"},
    {"name": "influencer_outreach:retry", "description": "Retry failed outreach messages"},
    
    # ========== AUTOMATION SESSIONS ==========
    {"name": "automation_session:create", "description": "Create automation sessions"},
    {"name": "automation_session:read", "description": "Read automation session details"},
    {"name": "automation_session:update", "description": "Update automation sessions"},
    {"name": "automation_session:delete", "description": "Delete automation sessions"},
    {"name": "automation_session:start", "description": "Start automation sessions"},
    {"name": "automation_session:stop", "description": "Stop automation sessions"},
    {"name": "automation_session:pause", "description": "Pause automation sessions"},
    {"name": "automation_session:resume", "description": "Resume automation sessions"},
    {"name": "automation_session:monitor", "description": "Monitor automation sessions"},
    
    # ========== ASSIGNMENT HISTORY ==========
    {"name": "assignment_history:create", "description": "Create assignment history records"},
    {"name": "assignment_history:read", "description": "Read assignment history details"},
    {"name": "assignment_history:update", "description": "Update assignment history records"},
    {"name": "assignment_history:delete", "description": "Delete assignment history records"},
    {"name": "assignment_history:stats", "description": "View assignment history statistics"},
    
    # ========== REASSIGNMENT REASONS ==========
    {"name": "reassignment_reason:create", "description": "Create reassignment reasons"},
    {"name": "reassignment_reason:read", "description": "Read reassignment reason details"},
    {"name": "reassignment_reason:update", "description": "Update reassignment reasons"},
    {"name": "reassignment_reason:delete", "description": "Delete reassignment reasons"},
    
    # ========== ORDERS & E-COMMERCE ==========
    {"name": "order:create", "description": "Create orders"},
    {"name": "order:read", "description": "Read order details"},
    {"name": "order:update", "description": "Update order details"},
    {"name": "order:delete", "description": "Delete orders"},
    {"name": "order:refund", "description": "Process order refunds"},
    {"name": "order:cancel", "description": "Cancel orders"},
    {"name": "order:fulfill", "description": "Fulfill orders"},
    {"name": "order:export", "description": "Export order data"},
    
    {"name": "order_item:create", "description": "Create order items"},
    {"name": "order_item:read", "description": "Read order item details"},
    {"name": "order_item:update", "description": "Update order items"},
    {"name": "order_item:delete", "description": "Delete order items"},
    
    # ========== ANALYTICS & REPORTING ==========
    {"name": "profile_analytics:create", "description": "Create profile analytics"},
    {"name": "profile_analytics:read", "description": "Read profile analytics"},
    {"name": "profile_analytics:update", "description": "Update profile analytics"},
    {"name": "profile_analytics:delete", "description": "Delete profile analytics"},
    {"name": "profile_analytics:refresh", "description": "Refresh profile analytics data"},
    {"name": "profile_analytics:export", "description": "Export profile analytics"},
    
    {"name": "result:create", "description": "Create campaign results"},
    {"name": "result:read", "description": "Read campaign results"},
    {"name": "result:update", "description": "Update campaign results"},
    {"name": "result:delete", "description": "Delete campaign results"},
    {"name": "result:export", "description": "Export campaign results"},
    
    # ========== SYSTEM SETTINGS ==========
    {"name": "system_setting:create", "description": "Create system settings"},
    {"name": "system_setting:read", "description": "Read system settings"},
    {"name": "system_setting:update", "description": "Update system settings"},
    {"name": "system_setting:delete", "description": "Delete system settings"},
    {"name": "system_setting:backup", "description": "Backup system settings"},
    {"name": "system_setting:restore", "description": "Restore system settings"},
    
    # ========== ADVANCED REPORTING & ANALYTICS ==========
    {"name": "report:campaign_performance", "description": "View campaign performance reports"},
    {"name": "report:influencer_performance", "description": "View influencer performance reports"},
    {"name": "report:agent_performance", "description": "View agent performance reports"},
    {"name": "report:financial", "description": "View financial reports"},
    {"name": "report:export", "description": "Export reports"},
    {"name": "report:schedule", "description": "Schedule automated reports"},
    
    {"name": "analytics:dashboard", "description": "Access analytics dashboard"},
    {"name": "analytics:real_time", "description": "Access real-time analytics"},
    {"name": "analytics:custom", "description": "Create custom analytics queries"},
    
    # ========== DATA MANAGEMENT ==========
    {"name": "data:export", "description": "Export platform data"},
    {"name": "data:import", "description": "Import platform data"},
    {"name": "data:backup", "description": "Create data backups"},
    {"name": "data:restore", "description": "Restore data from backups"},
    {"name": "data:cleanup", "description": "Clean up old/unused data"},
    {"name": "data:audit", "description": "Audit data integrity"},
    
    # ========== SYSTEM ADMINISTRATION ==========
    {"name": "system:maintenance", "description": "Perform system maintenance"},
    {"name": "system:monitor", "description": "Monitor system health"},
    {"name": "system:logs", "description": "Access system logs"},
    {"name": "system:alerts", "description": "Manage system alerts"},
    {"name": "system:config", "description": "Configure system parameters"},
    
    # ========== API & WEBHOOK MANAGEMENT ==========
    {"name": "api:access", "description": "Access API endpoints"},
    {"name": "api:admin", "description": "Administer API settings"},
    {"name": "api:rate_limit", "description": "Manage API rate limits"},
    
    {"name": "webhook:create", "description": "Create webhooks"},
    {"name": "webhook:read", "description": "Read webhook details"},
    {"name": "webhook:update", "description": "Update webhooks"},
    {"name": "webhook:delete", "description": "Delete webhooks"},
    {"name": "webhook:test", "description": "Test webhook endpoints"},
    
    # ========== NOTIFICATION MANAGEMENT ==========
    {"name": "notification:create", "description": "Create notifications"},
    {"name": "notification:read", "description": "Read notifications"},
    {"name": "notification:update", "description": "Update notifications"},
    {"name": "notification:delete", "description": "Delete notifications"},
    {"name": "notification:send", "description": "Send notifications"},
    {"name": "notification:broadcast", "description": "Broadcast notifications"},
]