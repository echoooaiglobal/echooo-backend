# app/Utils/dictionaries/roles.py

"""
Default roles for the influencer marketing platform
"""


DEFAULT_ROLES = [

    # ========== PLATFORM ROLES (Super Admin Level) ==========
    { "name": "platform_super_admin", "description": "Platform super administrator with full system access and control" },
    { "name": "platform_admin", "description": "Platform administrator with full access to manage companies, users, and settings" },
    { "name": "platform_manager", "description": "Platform manager with oversight across companies and operations" },
    { "name": "platform_developer", "description": "Technical developer role for platform development and maintenance" },
    { "name": "platform_customer_support", "description": "Customer support specialist handling company and influencer queries" },
    { "name": "platform_account_manager", "description": "Manages key platform clients and enterprise relationships" },
    { "name": "platform_financial_manager", "description": "Handles platform financial matters, payments, and subscriptions" },
    { "name": "platform_content_moderator", "description": "Content moderation and quality assurance specialist" },
    { "name": "platform_data_analyst", "description": "Platform-wide analytics and reporting specialist" },
    { "name": "platform_operations_manager", "description": "Oversees daily platform operations and workflow optimization" },
    { "name": "platform_agent", "description": "To handles outreach" },

    # ========== B2C COMPANY ROLES (Direct Campaign Management) ==========
    { "name": "b2c_company_owner", "description": "B2C company owner with full access to their company account and campaigns" },
    { "name": "b2c_company_admin", "description": "B2C company administrator with full company management access" },
    { "name": "b2c_marketing_director", "description": "B2C marketing director overseeing all marketing campaigns and strategy" },
    { "name": "b2c_campaign_manager", "description": "B2C campaign manager with full campaign creation and management access" },
    { "name": "b2c_campaign_executive", "description": "B2C campaign executive with campaign execution and influencer management" },
    { "name": "b2c_social_media_manager", "description": "B2C social media specialist managing influencer relationships and content" },
    { "name": "b2c_content_creator", "description": "B2C content creation specialist for campaign assets and briefs" },
    { "name": "b2c_brand_manager", "description": "B2C brand manager focusing on brand representation and guidelines" },
    { "name": "b2c_performance_analyst", "description": "B2C analyst focused on campaign performance and ROI analysis" },
    { "name": "b2c_finance_manager", "description": "B2C finance manager handling budgets, payments, and financial reporting" },
    { "name": "b2c_account_coordinator", "description": "B2C account coordinator for campaign coordination and communication" },
    { "name": "b2c_viewer", "description": "B2C read-only access for stakeholders and observers" },

    # ========== INFLUENCER ROLES ==========
    { "name": "influencer", "description": "Influencer with access to their profile, campaigns, and performance analytics" },
    { "name": "influencer_manager", "description": "Influencer manager representing and managing multiple influencer accounts" },

    # # ========== B2B AGENCY ROLES (Multi-Client Management) ==========
    # { "name": "b2b_agency_owner", "description": "B2B agency owner with full access to agency operations and all clients" },
    # { "name": "b2b_agency_admin", "description": "B2B agency administrator with full agency management capabilities" },
    # { "name": "b2b_operations_director", "description": "B2B operations director overseeing all client accounts and campaigns" },
    # { "name": "b2b_account_director", "description": "B2B account director managing multiple client relationships" },
    # { "name": "b2b_account_manager", "description": "B2B account manager handling specific client accounts and campaigns" },
    # { "name": "b2b_campaign_strategist", "description": "B2B campaign strategist creating and planning influencer marketing strategies" },
    # { "name": "b2b_campaign_manager", "description": "B2B campaign manager executing campaigns across multiple clients" },
    # { "name": "b2b_influencer_specialist", "description": "B2B influencer relationship specialist managing influencer partnerships" },
    # { "name": "b2b_creative_director", "description": "B2B creative director overseeing content strategy and creative campaigns" },
    # { "name": "b2b_performance_manager", "description": "B2B performance manager analyzing campaign results across all clients" },
    # { "name": "b2b_client_success_manager", "description": "B2B client success manager ensuring client satisfaction and retention" },
    # { "name": "b2b_financial_controller", "description": "B2B financial controller managing agency finances and client billing" },
    # { "name": "b2b_project_coordinator", "description": "B2B project coordinator managing campaign timelines and deliverables" },

    # # ========== B2B CLIENT ACCESS ROLES (Agency's Client Users) ==========
    # { "name": "b2b_client_admin", "description": "B2B client administrator with full access to their campaigns managed by agency" },
    # { "name": "b2b_client_manager", "description": "B2B client manager with management access to their specific campaigns" },
    # { "name": "b2b_client_marketer", "description": "B2B client marketer with campaign viewing and limited editing access" },
    # { "name": "b2b_client_analyst", "description": "B2B client analyst with access to campaign analytics and reporting" },
    # { "name": "b2b_client_viewer", "description": "B2B client viewer with read-only access to their campaigns" },
    # { "name": "b2b_client_approver", "description": "B2B client approver with ability to approve campaign content and strategies" }, 

    # # ========== AUTOMATION & OPERATIONS ROLES ==========
    # { "name": "automation_agent", "description": "Automated outreach agent role for system-driven communications" },
    # { "name": "automation_manager", "description": "Automation manager overseeing automated campaign processes" },
    # { "name": "outreach_specialist", "description": "Outreach specialist managing influencer communications" },
    # { "name": "relationship_manager", "description": "Relationship manager maintaining long-term influencer partnerships" },

    # # ========== SYSTEM & SUPPORT ROLES ==========
    # { "name": "system_auditor", "description": "System auditor with read-only access for compliance and monitoring" },
    # { "name": "api_user", "description": "API user role for third-party integrations and external systems" },
    # { "name": "webhook_service", "description": "Webhook service role for automated system integrations" },
    # { "name": "reporting_service", "description": "Automated reporting service for scheduled reports and analytics" },
]