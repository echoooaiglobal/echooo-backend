# app/Utils/db_init.py
import uuid
import string
import secrets
from sqlalchemy.orm import Session
from app.Utils.Logger import logger
from app.Models import (
    User, Role, Permission, RolePermission,
    Platform, Category, UserStatus, user_roles, Status, MessageChannel
)

# Import dictionary data
from app.Utils.dictionaries import DEFAULT_CATEGORIES, DEFAULT_PLATFORMS, DEFAULT_STATUSES, DEFAULT_MESSAGE_CHANNNELS, DEFAULT_ROLES, DEFAULT_PERMISSIONS

def initialize_default_roles_permissions(db: Session):
    """
    Initialize database with default roles and permissions
    """
    try:
        # Create default roles if they don't exist
        for role_data in DEFAULT_ROLES:
            role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not role:
                role = Role(**role_data)
                db.add(role)
        
        # Create default permissions
        for perm_data in DEFAULT_PERMISSIONS:
            perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
            if not perm:
                perm = Permission(**perm_data)
                db.add(perm)
        
        db.commit()
        
        # Assign permissions to roles
        platform_admin = db.query(Role).filter(Role.name == "platform_admin").first()
        platform_user = db.query(Role).filter(Role.name == "platform_user").first()
        company_admin = db.query(Role).filter(Role.name == "company_admin").first()
        campaign_manager = db.query(Role).filter(Role.name == "company_campaign_manager").first()
        company_user = db.query(Role).filter(Role.name == "company_user").first()
        influencer = db.query(Role).filter(Role.name == "influencer").first()
        
        # Get all permissions
        all_permissions = db.query(Permission).all()
        
        # Assign all permissions to platform_admin
        if platform_admin:
            for perm in all_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_admin.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_admin.id, permission_id=perm.id)
                    db.add(role_perm)
        
        # Assign read permissions to platform_user
        if platform_user:
            read_permissions = db.query(Permission).filter(Permission.name.like("%:read")).all()
            for perm in read_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_user.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_user.id, permission_id=perm.id)
                    db.add(role_perm)
        
        # Assign company and campaign permissions to company_admin
        if company_admin:
            company_permissions = db.query(Permission).filter(
                (Permission.name.like("company:%")) | 
                (Permission.name.like("campaign:%")) |
                (Permission.name.like("influencer:read")) |
                (Permission.name.like("influencer_contacts:read"))
            ).all()
            
            for perm in company_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == company_admin.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=company_admin.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign campaign manager permissions to campaign_manager
        if campaign_manager:
            campaign_permissions = db.query(Permission).filter(
                (Permission.name.like("campaign:%")) |
                (Permission.name == "influencer:read") |
                (Permission.name == "influencer_contacts:read")
            ).all()
            
            for perm in campaign_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == campaign_manager.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=campaign_manager.id, permission_id=perm.id)
                    db.add(role_perm)
        
        # Assign read permissions to company_user
        if company_user:
            company_read_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") | 
                (Permission.name == "campaign:read") |
                (Permission.name == "influencer:read") |
                (Permission.name == "influencer_contacts:read")
            ).all()
            
            for perm in company_read_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == company_user.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=company_user.id, permission_id=perm.id)
                    db.add(role_perm)
        
        # Assign influencer permissions
        if influencer:
            influencer_permissions = db.query(Permission).filter(
                (Permission.name == "influencer:read") | 
                (Permission.name == "influencer:update") |
                (Permission.name == "influencer_contacts:read") |
                (Permission.name == "influencer_contacts:create") |
                (Permission.name == "influencer_contacts:update")
            ).all()
            
            for perm in influencer_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == influencer.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=influencer.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to platform_manager
        platform_manager = db.query(Role).filter(Role.name == "platform_manager").first()
        if platform_manager:
            manager_permissions = db.query(Permission).filter(
                ~Permission.name.like("%:delete")  # All except delete permissions
            ).all()
            
            for perm in manager_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_manager.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_manager.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to platform_accountant
        platform_accountant = db.query(Role).filter(Role.name == "platform_accountant").first()
        if platform_accountant:
            read_permissions = db.query(Permission).filter(
                Permission.name.like("%:read")
            ).all()
            
            for perm in read_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_accountant.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_accountant.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to platform_developer
        platform_developer = db.query(Role).filter(Role.name == "platform_developer").first()
        if platform_developer:
            dev_permissions = db.query(Permission).all()  # Developers need access to everything for testing
            
            for perm in dev_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_developer.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_developer.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to platform_customer_support
        platform_support = db.query(Role).filter(Role.name == "platform_customer_support").first()
        if platform_support:
            support_permissions = db.query(Permission).filter(
                Permission.name.like("%:read")
            ).all()
            
            for perm in support_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_support.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_support.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to platform_content_moderator
        platform_moderator = db.query(Role).filter(Role.name == "platform_content_moderator").first()
        if platform_moderator:
            moderator_permissions = db.query(Permission).filter(
                (Permission.name.like("%:read")) |
                (Permission.name == "influencer:update") |
                (Permission.name == "influencer_contacts:read") |
                (Permission.name == "influencer_contacts:update")
            ).all()
            
            for perm in moderator_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_moderator.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_moderator.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to platform_agent - INCLUDING NEW INFLUENCER_CONTACTS PERMISSIONS
        platform_agent = db.query(Role).filter(Role.name == "platform_agent").first()
        if platform_agent:
            agent_permissions = db.query(Permission).filter(
                (Permission.name.like("campaign:%")) |
                (Permission.name == "influencer:read") |
                (Permission.name == "influencer:update") |
                # NEW: Add influencer_contacts permissions for platform_agent
                (Permission.name == "influencer_contacts:read") |
                (Permission.name == "influencer_contacts:create") |
                (Permission.name == "influencer_contacts:update")
            ).all()
            
            for perm in agent_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == platform_agent.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=platform_agent.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to company_manager
        company_manager = db.query(Role).filter(Role.name == "company_manager").first()
        if company_manager:
            company_manager_permissions = db.query(Permission).filter(
                (Permission.name.like("company:%")) |
                (Permission.name.like("campaign:%")) |
                (Permission.name == "influencer:read") |
                (Permission.name == "influencer_contacts:read")
            ).all()
            
            for perm in company_manager_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == company_manager.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=company_manager.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to company_accountant
        company_accountant = db.query(Role).filter(Role.name == "company_accountant").first()
        if company_accountant:
            accountant_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name == "influencer_contacts:read")
            ).all()
            
            for perm in accountant_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == company_accountant.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=company_accountant.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to company_marketer
        company_marketer = db.query(Role).filter(Role.name == "company_marketer").first()
        if company_marketer:
            marketer_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name.like("campaign:%")) |
                (Permission.name == "influencer:read") |
                (Permission.name == "influencer_contacts:read")
            ).all()
            
            for perm in marketer_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == company_marketer.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=company_marketer.id, permission_id=perm.id)
                    db.add(role_perm)

        # Assign permissions to company_content_creator
        company_creator = db.query(Role).filter(Role.name == "company_content_creator").first()
        if company_creator:
            creator_permissions = db.query(Permission).filter(
                (Permission.name == "company:read") |
                (Permission.name == "campaign:read") |
                (Permission.name == "influencer:read") |
                (Permission.name == "influencer_contacts:read")
            ).all()
            
            for perm in creator_permissions:
                role_perm = db.query(RolePermission).filter(
                    RolePermission.role_id == company_creator.id,
                    RolePermission.permission_id == perm.id
                ).first()
                
                if not role_perm:
                    role_perm = RolePermission(role_id=company_creator.id, permission_id=perm.id)
                    db.add(role_perm)
        
        # Initialize platforms from dictionary
        logger.info("Initializing platforms from dictionary...")
        for platform_data in DEFAULT_PLATFORMS:
            platform = db.query(Platform).filter(Platform.name == platform_data["name"]).first()
            if not platform:
                platform = Platform(**platform_data)
                db.add(platform)

        # Initialize default categories from dictionary
        for category_data in DEFAULT_CATEGORIES:
            category = db.query(Category).filter(Category.name == category_data["name"]).first()
            if not category:
                category = Category(**category_data)
                db.add(category)
        
        # Initialize statuses from dictionary
        for status_data in DEFAULT_STATUSES:
            status = db.query(Status).filter(
                Status.model == status_data["model"],
                Status.name == status_data["name"]
            ).first()
            if not status:
                status = Status(**status_data)
                db.add(status)

        # Initialize default message channels from dictionary
        for channel_data in DEFAULT_MESSAGE_CHANNNELS:
            channel = db.query(MessageChannel).filter(MessageChannel.shortname == channel_data["shortname"]).first()
            if not channel:
                channel = MessageChannel(**channel_data)
                db.add(channel)
                
        # Create default super-admin if none exists
        try:
            # First check if platform_admin role exists
            admin_role = db.query(Role).filter(Role.name == "platform_admin").first()
            if admin_role:
                # Check if any user with platform_admin role already exists
                admin_exists = db.query(User).join(user_roles).filter(
                    user_roles.c.role_id == admin_role.id
                ).first()
                
                if not admin_exists:
                    # Import password utility for hashing
                    from app.Http.Controllers.AuthController import AuthController
                    
                    # Default admin credentials
                    admin_email = "admin@echooo.ai"
                    admin_password = "Admin@123"  # In production, use a more secure default or generate one
                    
                    # Create the super admin user
                    admin_user = User(
                        email=admin_email,
                        hashed_password=AuthController.get_password_hash(admin_password),
                        full_name="System Administrator",
                        user_type="platform",
                        status=UserStatus.ACTIVE.value,
                        email_verified=True
                    )
                    
                    # Add the platform_admin role
                    admin_user.roles.append(admin_role)
                    
                    db.add(admin_user)
                    db.commit()
                    db.refresh(admin_user)
                    
                    # Log the creation and credentials
                    logger.info("==========================================================")
                    logger.info("Default super-admin account created with the following credentials:")
                    logger.info(f"Email: {admin_email}")
                    logger.info(f"Password: {admin_password}")
                    logger.info("IMPORTANT: Change these credentials immediately after first login!")
                    logger.info("==========================================================")
                else:
                    logger.info("Super-admin already exists, skipping creation")
            else:
                logger.warning("Cannot create super-admin: platform_admin role not found")
        
        except Exception as e:
            logger.error(f"Error creating super-admin: {str(e)}")
            # Don't raise the exception here to allow the rest of the initialization to continue

        
        db.commit()
        logger.info("Default roles, permissions, platforms, and categories initialized successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing database defaults: {str(e)}")
        raise