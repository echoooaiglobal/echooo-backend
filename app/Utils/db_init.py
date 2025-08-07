# app/Utils/db_init.py
import uuid
from sqlalchemy.orm import Session
from app.Utils.Logger import logger
from app.Models import (
    User, Role, Permission, RolePermission,
    Platform, Category, UserStatus, user_roles, Status
)
from app.Models.communication_channels import CommunicationChannel
from app.Models.reassignment_reasons import ReassignmentReason
from app.Models.system_settings import Settings
# Import dictionary data
from app.Utils.dictionaries import (
    DEFAULT_CATEGORIES, DEFAULT_PLATFORMS, DEFAULT_STATUSES, 
    DEFAULT_COMMUNICATION_CHANNELS, DEFAULT_ROLES, DEFAULT_PERMISSIONS,
    DEFAULT_REASSIGNMENT_REASONS, DEFAULT_SETTINGS, DEFAULT_ACCOUNTS
)

def initialize_default_roles(db: Session):
    """
    Initialize database with default roles only
    """
    try:
        logger.info("Initializing default roles...")
        
        # Create default roles if they don't exist
        for role_data in DEFAULT_ROLES:
            role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not role:
                role = Role(**role_data)
                db.add(role)
                logger.info(f"Added role: {role_data['name']}")
        
        db.commit()
        logger.info("Default roles initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing roles: {str(e)}")
        raise

def initialize_default_permissions(db: Session):
    """
    Initialize database with default permissions only
    """
    try:
        logger.info("Initializing default permissions...")
        
        # Create default permissions
        for perm_data in DEFAULT_PERMISSIONS:
            perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
            if not perm:
                perm = Permission(**perm_data)
                db.add(perm)
                logger.info(f"Added permission: {perm_data['name']}")
        
        db.commit()
        logger.info("Default permissions initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing permissions: {str(e)}")
        raise

def assign_permissions_to_roles(db: Session):
    """
    Assign permissions to roles based on role hierarchy
    Updated for Phase 1: Platform, B2C, and Influencer roles only
    """
    try:
        logger.info("Assigning permissions to roles...")
        
        # Get all roles
        platform_super_admin = db.query(Role).filter(Role.name == "platform_super_admin").first()
        platform_admin = db.query(Role).filter(Role.name == "platform_admin").first()
        platform_manager = db.query(Role).filter(Role.name == "platform_manager").first()
        platform_developer = db.query(Role).filter(Role.name == "platform_developer").first()
        platform_customer_support = db.query(Role).filter(Role.name == "platform_customer_support").first()
        platform_account_manager = db.query(Role).filter(Role.name == "platform_account_manager").first()
        platform_financial_manager = db.query(Role).filter(Role.name == "platform_financial_manager").first()
        platform_content_moderator = db.query(Role).filter(Role.name == "platform_content_moderator").first()
        platform_data_analyst = db.query(Role).filter(Role.name == "platform_data_analyst").first()
        platform_operations_manager = db.query(Role).filter(Role.name == "platform_operations_manager").first()
        platform_agent = db.query(Role).filter(Role.name == "platform_agent").first()
        
        # B2C Company roles
        b2c_company_owner = db.query(Role).filter(Role.name == "b2c_company_owner").first()
        b2c_company_admin = db.query(Role).filter(Role.name == "b2c_company_admin").first()
        b2c_marketing_director = db.query(Role).filter(Role.name == "b2c_marketing_director").first()
        b2c_campaign_manager = db.query(Role).filter(Role.name == "b2c_campaign_manager").first()
        b2c_campaign_executive = db.query(Role).filter(Role.name == "b2c_campaign_executive").first()
        b2c_social_media_manager = db.query(Role).filter(Role.name == "b2c_social_media_manager").first()
        b2c_content_creator = db.query(Role).filter(Role.name == "b2c_content_creator").first()
        b2c_brand_manager = db.query(Role).filter(Role.name == "b2c_brand_manager").first()
        b2c_performance_analyst = db.query(Role).filter(Role.name == "b2c_performance_analyst").first()
        b2c_finance_manager = db.query(Role).filter(Role.name == "b2c_finance_manager").first()
        b2c_account_coordinator = db.query(Role).filter(Role.name == "b2c_account_coordinator").first()
        b2c_viewer = db.query(Role).filter(Role.name == "b2c_viewer").first()
        
        # Influencer roles
        influencer = db.query(Role).filter(Role.name == "influencer").first()
        influencer_manager = db.query(Role).filter(Role.name == "influencer_manager").first()

        # Get all permissions
        all_permissions = db.query(Permission).all()
        
        # ========== UNIVERSAL PERMISSIONS FOR ALL ROLES ==========
        universal_permissions = db.query(Permission).filter(
            (Permission.name == "user:read") |              # Read own profile
            (Permission.name == "user:update") |            # Update own profile
            (Permission.name == "oauth:read") |             # Read own OAuth connections
            (Permission.name == "oauth:update") |           # Update own OAuth connections 
            (Permission.name == "oauth:delete") |           # Delete own OAuth connections
            (Permission.name == "oauth:refresh") |          # Refresh own OAuth tokens
            (Permission.name == "refresh_token:read") |     # Read own refresh tokens
            (Permission.name == "refresh_token:revoke") |   # Revoke own refresh tokens
            (Permission.name == "notification:read") |      # Read own notifications
            (Permission.name == "notification:update") |    # Update notification preferences
            (Permission.name == "email_verification:read") | # Read own email verification status
            (Permission.name == "email_verification:resend") # Resend own email verification
        ).all()

        # Helper function to assign permissions to role
        def assign_permissions_to_role(role, permissions):
            if role:
                for perm in permissions:
                    role_perm = db.query(RolePermission).filter(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id
                    ).first()
                    
                    if not role_perm:
                        role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                        db.add(role_perm)

        # Helper function to assign universal permissions to all roles
        def assign_universal_permissions_to_role(role):
            if role:
                assign_permissions_to_role(role, universal_permissions)
                logger.info(f"Assigned universal permissions to {role.name}")

        # ========== ASSIGN UNIVERSAL PERMISSIONS TO ALL ROLES ==========
        all_roles = [
            platform_super_admin, platform_admin, platform_manager, platform_developer,
            platform_customer_support, platform_account_manager, platform_financial_manager,
            platform_content_moderator, platform_data_analyst, platform_operations_manager,
            platform_agent, b2c_company_owner, b2c_company_admin, b2c_marketing_director,
            b2c_campaign_manager, b2c_campaign_executive, b2c_social_media_manager,
            b2c_content_creator, b2c_brand_manager, b2c_performance_analyst,
            b2c_finance_manager, b2c_account_coordinator, b2c_viewer,
            influencer, influencer_manager
        ]
        
        for role in all_roles:
            assign_universal_permissions_to_role(role)

        # ========== PLATFORM ROLE PERMISSIONS ==========
        
        # Platform Super Admin - ALL permissions
        if platform_super_admin:
            assign_permissions_to_role(platform_super_admin, all_permissions)
            logger.info("Assigned ALL permissions to platform_super_admin")

        # Platform Admin - ALL permissions except super admin specific ones
        if platform_admin:
            assign_permissions_to_role(platform_admin, all_permissions)
            logger.info("Assigned ALL permissions to platform_admin")

        # Platform Manager - All except delete permissions
        if platform_manager:
            manager_permissions = db.query(Permission).filter(
                ~Permission.name.like("%:delete")
            ).all()
            assign_permissions_to_role(platform_manager, manager_permissions)
            logger.info("Assigned manager permissions to platform_manager")

        # Platform Developer - ALL permissions for development
        if platform_developer:
            assign_permissions_to_role(platform_developer, all_permissions)
            logger.info("Assigned ALL permissions to platform_developer")

        # Platform Customer Support - Read permissions + specific support actions
        if platform_customer_support:
            support_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name == "user:verify") |
                (Permission.name == "user:reset_password") |
                (Permission.name == "support_ticket:create") |
                (Permission.name == "support_ticket:update")
            ).all()
            assign_permissions_to_role(platform_customer_support, support_permissions)
            logger.info("Assigned support permissions to platform_customer_support")

        # Platform Account Manager - Account and relationship management
        if platform_account_manager:
            account_mgr_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name.like("company:%")) |
                (Permission.name.like("campaign:%")) |
                (Permission.name.like("contract:%")) |
                (Permission.name.like("subscription:%"))
            ).all()
            assign_permissions_to_role(platform_account_manager, account_mgr_permissions)
            logger.info("Assigned account management permissions to platform_account_manager")

        # Platform Financial Manager - Financial operations
        if platform_financial_manager:
            finance_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name.like("payment:%")) |
                (Permission.name.like("invoice:%")) |
                (Permission.name.like("subscription:%")) |
                (Permission.name.like("financial_report:%"))
            ).all()
            assign_permissions_to_role(platform_financial_manager, finance_permissions)
            logger.info("Assigned financial permissions to platform_financial_manager")

        # Platform Content Moderator - Content moderation
        if platform_content_moderator:
            moderator_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name.like("content:%")) |
                (Permission.name.like("campaign:update")) |
                (Permission.name.like("influencer:update"))
            ).all()
            assign_permissions_to_role(platform_content_moderator, moderator_permissions)
            logger.info("Assigned moderation permissions to platform_content_moderator")

        # Platform Data Analyst - Analytics and reporting
        if platform_data_analyst:
            analyst_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name.like("analytics:%")) |
                (Permission.name.like("report:%"))
            ).all()
            assign_permissions_to_role(platform_data_analyst, analyst_permissions)
            logger.info("Assigned analytics permissions to platform_data_analyst")

        # Platform Operations Manager - Operations oversight
        if platform_operations_manager:
            ops_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name.like("%:update")) |
                (Permission.name.like("workflow:%")) |
                (Permission.name.like("system_settings:%"))
            ).all()
            assign_permissions_to_role(platform_operations_manager, ops_permissions)
            logger.info("Assigned operations permissions to platform_operations_manager")

        # Platform Agent - Outreach and communication
        if platform_agent:
            agent_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name.like("influencer_outreach:%")) |
                (Permission.name.like("communication:%")) |
                (Permission.name == "influencer:update") |
                (Permission.name == "influencer_contact:create") |
                (Permission.name == "influencer_contact:update") |
                (Permission.name == "assigned_influencer:read") |
                (Permission.name == "assigned_influencer:update") |
                (Permission.name == "assigned_influencer:transfer") |
                (Permission.name == "assigned_influencer:archive") |
                (Permission.name == "assigned_influencer:bulk_update") |
                (Permission.name == "campaign_influencer:update")
            ).all()
            assign_permissions_to_role(platform_agent, agent_permissions)
            logger.info("Assigned agent permissions to platform_agent")

        # ========== B2C COMPANY ROLE PERMISSIONS ==========
        
        # B2C Company Owner - Full access to their company's data
        if b2c_company_owner:
            owner_permissions = db.query(Permission).filter(
                (Permission.name.like("company:%")) |
                (Permission.name.like("campaign:%")) |
                (Permission.name.like("influencer:%")) |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name.like("contract:%")) |
                (Permission.name.like("payment:%")) |
                (Permission.name.like("analytics:%")) |
                (Permission.name.like("campaign_influencer:%"))
            ).all()
            assign_permissions_to_role(b2c_company_owner, owner_permissions)
            logger.info("Assigned owner permissions to b2c_company_owner")

        # B2C Company Admin - Administrative access
        if b2c_company_admin:
            admin_permissions = db.query(Permission).filter(
                (Permission.name.like("company:%")) |
                (Permission.name.like("campaign:%")) |
                (Permission.name.like("influencer:%")) |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name.like("analytics:%")) |
                (Permission.name.like("campaign_influencer:%"))
            ).all()
            assign_permissions_to_role(b2c_company_admin, admin_permissions)
            logger.info("Assigned admin permissions to b2c_company_admin")

        # B2C Marketing Director - Strategic marketing oversight
        if b2c_marketing_director:
            marketing_dir_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name.like("campaign:%")) |
                (Permission.name.like("influencer:%")) |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name.like("analytics:%")) |
                (Permission.name.like("strategy:%"))
            ).all()
            assign_permissions_to_role(b2c_marketing_director, marketing_dir_permissions)
            logger.info("Assigned marketing director permissions to b2c_marketing_director")

        # B2C Campaign Manager - Full campaign management
        if b2c_campaign_manager:
            campaign_mgr_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name.like("campaign:%")) |
                (Permission.name.like("influencer:%")) |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name.like("content:%")) |
                (Permission.name.like("analytics:read")) |
                (Permission.name.like("campaign_influencer:%"))
            ).all()
            assign_permissions_to_role(b2c_campaign_manager, campaign_mgr_permissions)
            logger.info("Assigned campaign manager permissions to b2c_campaign_manager")

        # B2C Campaign Executive - Campaign execution
        if b2c_campaign_executive:
            campaign_exec_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name == "campaign:update") |
                (Permission.name.like("influencer:%")) |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name == "content:read") |
                (Permission.name == "content:update")
            ).all()
            assign_permissions_to_role(b2c_campaign_executive, campaign_exec_permissions)
            logger.info("Assigned campaign executive permissions to b2c_campaign_executive")

        # B2C Social Media Manager - Social media and influencer management
        if b2c_social_media_manager:
            social_mgr_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name == "campaign:update") |
                (Permission.name.like("influencer:%")) |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name.like("social_account:%")) |
                (Permission.name.like("content:%"))
            ).all()
            assign_permissions_to_role(b2c_social_media_manager, social_mgr_permissions)
            logger.info("Assigned social media manager permissions to b2c_social_media_manager")

        # B2C Content Creator - Content creation and management
        if b2c_content_creator:
            content_creator_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name == "influencer:read") |
                (Permission.name == "influencer_contact:read") |
                (Permission.name.like("content:%")) |
                (Permission.name.like("asset:%"))
            ).all()
            assign_permissions_to_role(b2c_content_creator, content_creator_permissions)
            logger.info("Assigned content creator permissions to b2c_content_creator")

        # B2C Brand Manager - Brand management and guidelines
        if b2c_brand_manager:
            brand_mgr_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "company:update") |
                (Permission.name == "campaign:read") |
                (Permission.name == "campaign:update") |
                (Permission.name == "influencer:read") |
                (Permission.name.like("brand:%")) |
                (Permission.name.like("content:%"))
            ).all()
            assign_permissions_to_role(b2c_brand_manager, brand_mgr_permissions)
            logger.info("Assigned brand manager permissions to b2c_brand_manager")

        # B2C Performance Analyst - Analytics and performance
        if b2c_performance_analyst:
            performance_analyst_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name == "influencer:read") |
                (Permission.name.like("analytics:%")) |
                (Permission.name.like("report:%")) |
                (Permission.name.like("performance:%"))
            ).all()
            assign_permissions_to_role(b2c_performance_analyst, performance_analyst_permissions)
            logger.info("Assigned performance analyst permissions to b2c_performance_analyst")

        # B2C Finance Manager - Financial management
        if b2c_finance_manager:
            finance_mgr_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name.like("payment:%")) |
                (Permission.name.like("invoice:%")) |
                (Permission.name.like("budget:%")) |
                (Permission.name.like("financial_report:%"))
            ).all()
            assign_permissions_to_role(b2c_finance_manager, finance_mgr_permissions)
            logger.info("Assigned finance manager permissions to b2c_finance_manager")

        # B2C Account Coordinator - Coordination and communication
        if b2c_account_coordinator:
            coordinator_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name == "campaign:update") |
                (Permission.name == "influencer:read") |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name.like("communication:%"))
            ).all()
            assign_permissions_to_role(b2c_account_coordinator, coordinator_permissions)
            logger.info("Assigned coordinator permissions to b2c_account_coordinator")

        # B2C Viewer - Read-only access + universal permissions
        if b2c_viewer:
            viewer_permissions = db.query(Permission).filter(
                Permission.name.like("%:read")
            ).all()
            assign_permissions_to_role(b2c_viewer, viewer_permissions)
            logger.info("Assigned viewer permissions to b2c_viewer")

        # ========== INFLUENCER ROLE PERMISSIONS ==========
        
        # Influencer - Access to their own profile and campaigns
        if influencer:
            influencer_permissions = db.query(Permission).filter(
                (Permission.name == "influencer:read") | 
                (Permission.name == "influencer:update") |
                (Permission.name == "influencer_contact:read") |
                (Permission.name == "influencer_contact:create") |
                (Permission.name == "influencer_contact:update") |
                (Permission.name == "social_account:read") |
                (Permission.name == "social_account:update") |
                (Permission.name == "campaign:read") |
                (Permission.name == "analytics:read") |
                (Permission.name == "profile_analytics:read")
            ).all()
            assign_permissions_to_role(influencer, influencer_permissions)
            logger.info("Assigned influencer permissions to influencer role")

        # Influencer Manager - Manage multiple influencer accounts
        if influencer_manager:
            influencer_mgr_permissions = db.query(Permission).filter(
                (Permission.name.like("influencer:%")) |
                (Permission.name.like("influencer_contact:%")) |
                (Permission.name.like("social_account:%")) |
                (Permission.name == "campaign:read") |
                (Permission.name.like("analytics:read")) |
                (Permission.name.like("profile_analytics:%"))
            ).all()
            assign_permissions_to_role(influencer_manager, influencer_mgr_permissions)
            logger.info("Assigned influencer manager permissions to influencer_manager role")
        
        db.commit()
        logger.info("Permissions assigned to roles successfully for Phase 1 (Platform, B2C, Influencer) with universal permissions")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning permissions to roles: {str(e)}")
        raise

def initialize_default_platforms(db: Session):
    """
    Initialize database with default platforms
    """
    try:
        logger.info("Initializing default platforms...")
        
        for platform_data in DEFAULT_PLATFORMS:
            platform = db.query(Platform).filter(Platform.name == platform_data["name"]).first()
            if not platform:
                platform = Platform(**platform_data)
                db.add(platform)
                logger.info(f"Added platform: {platform_data['name']}")
        
        db.commit()
        logger.info("Default platforms initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing platforms: {str(e)}")
        raise

def initialize_default_categories(db: Session):
    """
    Initialize database with default categories
    """
    try:
        logger.info("Initializing default categories...")
        
        for category_data in DEFAULT_CATEGORIES:
            category = db.query(Category).filter(Category.name == category_data["name"]).first()
            if not category:
                category = Category(**category_data)
                db.add(category)
                logger.info(f"Added category: {category_data['name']}")
        
        db.commit()
        logger.info("Default categories initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing categories: {str(e)}")
        raise

def initialize_default_statuses(db: Session):
    """
    Initialize database with default statuses
    """
    try:
        logger.info("Initializing default statuses...")
        
        for status_data in DEFAULT_STATUSES:
            status = db.query(Status).filter(
                Status.model == status_data["model"],
                Status.name == status_data["name"]
            ).first()
            if not status:
                status = Status(**status_data)
                db.add(status)
                logger.info(f"Added status: {status_data['name']} for {status_data['model']}")
        
        db.commit()
        logger.info("Default statuses initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing statuses: {str(e)}")
        raise

def initialize_default_communication_channels(db: Session):
    """
    Initialize database with default communication channels
    """
    try:
        logger.info("Initializing default communication channels...")
        
        for channel_data in DEFAULT_COMMUNICATION_CHANNELS:
            # Resolve platform_id from platform name if it's not None
            platform_id = channel_data.get("platform_id")
            if platform_id is not None:
                # Look up platform by name (case-insensitive)
                platform = db.query(Platform).filter(
                    Platform.name.ilike(platform_id)
                ).first()
                
                if platform:
                    platform_id = platform.id
                    logger.info(f"Resolved platform name '{channel_data.get('platform_id')}' to UUID: {platform_id}")
                else:
                    logger.warning(f"Platform '{platform_id}' not found in database for channel '{channel_data['name']}'. Setting platform_id to None.")
                    platform_id = None
            
            # Check if channel already exists
            channel = db.query(CommunicationChannel).filter(
                CommunicationChannel.code == channel_data["code"]
            ).first()
            
            if not channel:
                # Create new channel with resolved platform_id
                channel = CommunicationChannel(
                    name=channel_data["name"],
                    code=channel_data["code"],
                    platform_id=platform_id,
                    is_active=channel_data.get("is_active", True),
                    order=channel_data.get("order", 0),
                    description=channel_data.get("description")
                )
                db.add(channel)
                logger.info(f"Added communication channel: {channel_data['name']}")
        
        db.commit()
        logger.info("Default communication channels initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing communication channels: {str(e)}")
        raise

def initialize_default_reassignment_reasons(db: Session):
    """
    Initialize database with default reassignment reasons
    """
    try:
        logger.info("Initializing default reassignment reasons...")
        
        for reason_data in DEFAULT_REASSIGNMENT_REASONS:
            reason = db.query(ReassignmentReason).filter(
                ReassignmentReason.code == reason_data["code"]
            ).first()
            if not reason:
                reason = ReassignmentReason(**reason_data)
                db.add(reason)
                logger.info(f"Added reassignment reason: {reason_data['name']}")
        
        db.commit()
        logger.info("Default reassignment reasons initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing reassignment reasons: {str(e)}")
        raise

def initialize_default_system_settings(db: Session):
    """
    Initialize database with default system settings
    """
    try:
        logger.info("Initializing default system settings...")
        
        for setting_data in DEFAULT_SETTINGS:
            # Get platform_id from settings data
            platform_id = setting_data.get("platform_id")
            
            # If platform_id is not None, look up the platform by name and get its UUID
            if platform_id is not None:
                # QUERY THE PLATFORM MODEL BY NAME
                platform = db.query(Platform).filter(
                    Platform.name.ilike(platform_id)
                ).first()
                
                if platform:
                    # GET THE ACTUAL UUID FROM THE PLATFORM MODEL
                    platform_id = platform.id
                    logger.info(f"Resolved platform name '{setting_data.get('platform_id')}' to UUID: {platform_id}")
                else:
                    logger.warning(f"Platform '{platform_id}' not found in database for setting '{setting_data['setting_key']}'. Setting platform_id to None.")
                    platform_id = None
            # If platform_id is None, keep it as None
            
            # Check if setting already exists
            existing = db.query(Settings).filter(
                Settings.setting_key == setting_data["setting_key"],
                Settings.platform_id == platform_id,
                Settings.applies_to_table == setting_data.get("applies_to_table")
            ).first()
            
            if not existing:
                # Handle created_by field
                created_by = setting_data.get("created_by")
                if isinstance(created_by, str) and created_by:
                    created_by = uuid.UUID(created_by)
                else:
                    created_by = None
                
                # Create new setting with the resolved platform_id
                new_setting = Settings(
                    setting_key=setting_data["setting_key"],
                    setting_value=setting_data["setting_value"],
                    setting_type=setting_data["setting_type"],
                    applies_to_table=setting_data.get("applies_to_table"),
                    applies_to_field=setting_data.get("applies_to_field"),
                    description=setting_data["description"],
                    platform_id=platform_id,  # This is now the UUID from Platform table
                    created_by=created_by,
                    created_by_type=setting_data.get("created_by_type", "system")
                )
                db.add(new_setting)
                logger.info(f"Added system setting: {setting_data['setting_key']}")
        
        db.commit()
        logger.info("Default system settings initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing system settings: {str(e)}")
        raise

def create_default_accounts(db: Session):
    """
    Create default accounts from the dictionary
    """
    try:
        logger.info("Creating default accounts...")
        
        for account_key, account_data in DEFAULT_ACCOUNTS.items():
            # Check if role exists
            role = db.query(Role).filter(Role.name == account_data["role_name"]).first()
            if not role:
                logger.warning(f"Cannot create {account_key}: role '{account_data['role_name']}' not found")
                continue
                
            # Check if user with this role already exists
            user_exists = db.query(User).join(user_roles).filter(
                user_roles.c.role_id == role.id
            ).first()
            
            if not user_exists:
                # Import password utility for hashing
                from app.Http.Controllers.AuthController import AuthController
                
                # Create the user
                user = User(
                    email=account_data["email"],
                    hashed_password=AuthController.get_password_hash(account_data["password"]),
                    full_name=account_data["full_name"],
                    user_type=account_data["user_type"],
                    phone_number=account_data.get("phone_number"),
                    status=UserStatus.ACTIVE.value,
                    email_verified=True
                )
                
                # Add the role
                user.roles.append(role)
                
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Log the creation and credentials
                logger.info("==========================================================")
                logger.info(f"Default {account_key} account created with the following credentials:")
                logger.info(f"Email: {account_data['email']}")
                logger.info(f"Password: {account_data['password']}")
                logger.info("IMPORTANT: Change these credentials immediately after first login!")
                logger.info("==========================================================")
            else:
                logger.info(f"{account_key} already exists, skipping creation")
                
    except Exception as e:
        logger.error(f"Error creating default accounts: {str(e)}")
        # Don't raise the exception here to allow the rest of the initialization to continue

def initialize_all_default_data(db: Session):
    """
    Master function to initialize all default data in proper order
    Call this from your main.py lifespan function
    """
    try:
        logger.info("Starting initialization of all default data...")
        
        # 1. Initialize roles first (required for permission assignments)
        initialize_default_roles(db)
        
        # 2. Initialize permissions (required for role-permission assignments)
        initialize_default_permissions(db)
        
        # 3. Assign permissions to roles (requires both roles and permissions to exist)
        assign_permissions_to_roles(db)
        
        # 4. Initialize platforms (may be referenced by other data)
        initialize_default_platforms(db)
        
        # 5. Initialize categories (may be referenced by other data)
        initialize_default_categories(db)
        
        # 6. Initialize system settings (may reference platforms)
        initialize_default_system_settings(db)
        
        # 7. Initialize statuses (for various models)
        initialize_default_statuses(db)
        
        # 8. Initialize communication channels
        initialize_default_communication_channels(db)
        
        # 9. Initialize reassignment reasons
        initialize_default_reassignment_reasons(db)
        
        # 10. Create default super admin (requires roles to exist)
        create_default_accounts(db)
        
        logger.info("All default data initialized successfully!")
        
    except Exception as e:
        logger.error(f"Error during default data initialization: {str(e)}")
        raise