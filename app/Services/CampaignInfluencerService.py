# app/Services/CampaignInfluencerService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid
from datetime import datetime
from app.Models.campaign_influencers import CampaignInfluencer
from app.Models.assigned_influencers import AssignedInfluencer
from app.Models.campaign_lists import CampaignList
from app.Models.statuses import Status
from app.Models.influencers import Influencer
from app.Models.social_accounts import SocialAccount
from app.Models.platforms import Platform
from app.Utils.Logger import logger

class CampaignInfluencerService:
    """Service for managing campaign influencers"""

    @staticmethod
    async def get_all_influencers(db: Session):
        """
        Get all campaign influencers across all lists
        """
        return db.query(CampaignInfluencer).options(
            joinedload(CampaignInfluencer.social_account),
            joinedload(CampaignInfluencer.status)
        ).all()
    
    @staticmethod
    async def get_list_influencers_paginated(
        campaign_list_id: uuid.UUID, 
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ) -> Tuple[List, int]:
        """
        Get paginated influencers of a campaign list
        
        Args:
            campaign_list_id: ID of the campaign list
            page: Page number (1-based)
            page_size: Number of items per page
            db: Database session
            
        Returns:
            Tuple[List[CampaignInfluencer], int]: List of influencers and total count
        """
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = db.query(CampaignInfluencer).filter(
            CampaignInfluencer.campaign_list_id == campaign_list_id
        ).count()
        
        # Get paginated influencers
        influencers = db.query(CampaignInfluencer).options(
            joinedload(CampaignInfluencer.social_account),
            joinedload(CampaignInfluencer.status)
        ).filter(
            CampaignInfluencer.campaign_list_id == campaign_list_id
        ).offset(offset).limit(page_size).all()
        
        return influencers, total_count
    
    @staticmethod
    async def get_all_influencers_paginated(
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ) -> Tuple[List, int]:
        """
        Get paginated influencers across all lists
        """
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get total count
        total_count = db.query(CampaignInfluencer).count()
        
        # Get paginated influencers
        influencers = db.query(CampaignInfluencer).options(
            joinedload(CampaignInfluencer.social_account),
            joinedload(CampaignInfluencer.status)
        ).offset(offset).limit(page_size).all()
        
        return influencers, total_count
    
    @staticmethod
    async def get_influencer_by_id(influencer_id: uuid.UUID, db: Session):
        """
        Get a campaign influencer by ID
        """
        # Get influencer with eager loading relationships
        influencer = db.query(CampaignInfluencer).options(
            joinedload(CampaignInfluencer.social_account),
            joinedload(CampaignInfluencer.status)
        ).filter(CampaignInfluencer.id == influencer_id).first()
        
        if not influencer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign influencer not found"
            )
            
        return influencer

    @staticmethod
    async def add_influencer_with_social_data(
        campaign_list_id: uuid.UUID, 
        platform_id: uuid.UUID, 
        social_data: Dict[str, Any], 
        db: Session
    ):
        """
        Add a member to a campaign list with social account data.
        Finds or creates a social account directly without creating a new influencer.
        """
        try:
            # Verify list exists
            campaign_list = db.query(CampaignList).filter(CampaignList.id == campaign_list_id).first()
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Verify platform exists
            platform = db.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            # Validate required fields in social_data
            if not social_data.get('id'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social data must include 'id' field"
                )
            
            if not social_data.get('username'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Social data must include 'username' field"
                )
            
            # Try to find existing social account by platform_account_id
            platform_account_id = str(social_data.get('id'))
            existing_account = db.query(SocialAccount).filter(
                SocialAccount.platform_id == platform_id,
                SocialAccount.platform_account_id == platform_account_id
            ).first()
            
            social_account_id = None
            
            # Prepare social account data mapping
            social_account_data = {
                "platform_id": platform_id,
                "platform_account_id": platform_account_id,
                "account_handle": social_data.get('username', ''),
                "full_name": social_data.get('name', ''),
                "profile_pic_url": social_data.get('profileImage', ''),
                "is_verified": social_data.get('isVerified', False),
                "account_url": social_data.get('account_url', ''),
                "additional_metrics": social_data.get('additional_metrics', {}),
                "followers_count": social_data.get('followers', ''),
            }
            
            # If social account exists, update it with new data
            if existing_account:
                social_account_id = existing_account.id
                
                # Always update all fields (except platform_id and platform_account_id)
                for field, new_value in social_account_data.items():
                    # Skip platform_id and platform_account_id as they shouldn't change
                    if field in ['platform_id', 'platform_account_id']:
                        continue
                    
                    setattr(existing_account, field, new_value)
                
                logger.info(f"Updating social account data for {existing_account.account_handle} (ID: {existing_account.id})")
                db.commit()
                db.refresh(existing_account)
                    
            else:
                # Create new social account
                social_account_data["influencer_id"] = None  # This field needs to be nullable in the database
                
                new_social_account = SocialAccount(**social_account_data)
                db.add(new_social_account)
                db.commit()
                db.refresh(new_social_account)
                
                social_account_id = new_social_account.id
                logger.info(f"Created new social account: {new_social_account.account_handle} (ID: {new_social_account.id})")
            
            # Check if member already exists in this list
            existing_campaign_influencer = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.campaign_list_id == campaign_list_id,
                CampaignInfluencer.social_account_id == social_account_id
            ).first()
            
            if existing_campaign_influencer:
                logger.info(f"Social account is already a member of this list: list_id={campaign_list_id}, social_account_id={social_account_id}")
                # Load relationships for proper response
                existing_campaign_influencer = db.query(CampaignInfluencer).options(
                    joinedload(CampaignInfluencer.social_account),
                    joinedload(CampaignInfluencer.status),
                ).filter(CampaignInfluencer.id == existing_campaign_influencer.id).first()
                return existing_campaign_influencer
            
            # Get default status
            default_status = db.query(Status).filter(
                Status.model == "campaign_influencer",
                Status.name == "discovered"
            ).first()
            
            if not default_status:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Default status 'discovered' not found"
                )
            
            # Create list member
            influencer_data = {
                "campaign_list_id": campaign_list_id,
                "social_account_id": social_account_id,
                "status_id": default_status.id,
                "total_contact_attempts": 0,
                # "is_ready_for_onboarding": False,
                "notes": social_data.get('notes', None)
            }
            
            campaign_influencer = CampaignInfluencer(**influencer_data)
            db.add(campaign_influencer)
            db.commit()
            db.refresh(campaign_influencer)
            
            logger.info(f"Created campaign influencer: id={campaign_influencer.id}, social_account_id={social_account_id}, campaign_list_id={campaign_list_id}")
            
            # Load relationships for proper response
            campaign_influencer = db.query(CampaignInfluencer).options(
                joinedload(CampaignInfluencer.social_account),
                joinedload(CampaignInfluencer.status),
            ).filter(CampaignInfluencer.id == campaign_influencer.id).first()
            
            return campaign_influencer
                
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding list member with social data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error adding list member: {str(e)}"
            ) from e

    @staticmethod
    async def add_influencer(influencer_data: Dict[str, Any], db: Session):
        """
        Add an influencer to a campaign list using existing social_account_id
        """
        try:
            # Verify campaign list exists
            campaign_list = db.query(CampaignList).filter(
                CampaignList.id == uuid.UUID(influencer_data['campaign_list_id'])
            ).first()
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Verify social account exists
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == uuid.UUID(influencer_data['social_account_id'])
            ).first()
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )
            
            # Check if influencer is already in this campaign list
            existing = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.campaign_list_id == uuid.UUID(influencer_data['campaign_list_id']),
                CampaignInfluencer.social_account_id == uuid.UUID(influencer_data['social_account_id'])
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Influencer is already in this campaign list"
                )
            
            # Get default status if not provided
            if not influencer_data.get('status_id'):
                default_status = db.query(Status).filter(
                    Status.model == "campaign_influencer",
                    Status.name == "discovered"
                ).first()
                
                if default_status:
                    influencer_data['status_id'] = str(default_status.id)
            
            # Create campaign influencer
            campaign_influencer = CampaignInfluencer(**influencer_data)
            db.add(campaign_influencer)
            db.commit()
            db.refresh(campaign_influencer)
            
            # Reload with relationships
            return db.query(CampaignInfluencer).options(
                joinedload(CampaignInfluencer.social_account),
                joinedload(CampaignInfluencer.status)
            ).filter(CampaignInfluencer.id == campaign_influencer.id).first()
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error adding influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error adding influencer to campaign list"
            ) from e

    @staticmethod
    async def update_influencer(
        influencer_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update a campaign influencer
        """
        try:
            influencer = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.id == influencer_id
            ).first()
            
            if not influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign influencer not found"
                )
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(influencer, field) and value is not None:
                    setattr(influencer, field, value)
            
            db.commit()
            db.refresh(influencer)
            
            # Reload with relationships
            return db.query(CampaignInfluencer).options(
                joinedload(CampaignInfluencer.social_account),
                joinedload(CampaignInfluencer.status)
            ).filter(CampaignInfluencer.id == influencer.id).first()
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating campaign influencer"
            ) from e
        
    @staticmethod
    async def update_influencer_with_assigned_status(
        influencer_id: uuid.UUID,
        status_id: str,
        assigned_influencer_id: Optional[str],
        db: Session
    ):
        """
        Update campaign influencer status and conditionally update assigned influencer status
        Only updates assigned influencer to 'completed' if campaign influencer status is 'completed'
        """
        try:
            from app.Models.assigned_influencers import AssignedInfluencer
            from app.Models.statuses import Status
            
            # 1. Find the new status by ID to check its name (for campaign_influencer model)
            new_status = db.query(Status).filter(
                Status.id == status_id,
                Status.model == 'campaign_influencer'  # Filter by model
            ).first()
            
            if not new_status:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign influencer status not found"
                )
            
            # 2. Update campaign influencer status
            influencer = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.id == influencer_id
            ).first()
            
            if not influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign influencer not found"
                )
            
            influencer.status_id = status_id
            
            # 3. Only update assigned influencer if new status is 'completed' AND assigned_influencer_id is provided
            should_update_assigned = (
                assigned_influencer_id and 
                new_status.name.lower() == 'completed'
            )
            
            if should_update_assigned:
                # Find the assigned influencer
                assigned_influencer = db.query(AssignedInfluencer).filter(
                    AssignedInfluencer.id == uuid.UUID(assigned_influencer_id)
                ).first()
                
                if not assigned_influencer:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assigned influencer not found"
                    )
                
                # Find the 'completed' status for assigned_influencer model
                completed_status = db.query(Status).filter(
                    Status.name.ilike('completed'),
                    Status.model == 'assigned_influencer'  # Filter by model
                ).first()
                
                if not completed_status:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Completed status not found for assigned influencer model"
                    )
                
                # Update both status_id and type to 'completed'
                assigned_influencer.status_id = completed_status.id
                assigned_influencer.type = 'completed'  # Update type field
            
            # Commit both updates together
            db.commit()
            
            # Refresh objects
            db.refresh(influencer)
            if should_update_assigned:
                db.refresh(assigned_influencer)
            
            # Reload with relationships
            return db.query(CampaignInfluencer).options(
                joinedload(CampaignInfluencer.social_account),
                joinedload(CampaignInfluencer.status)
            ).filter(CampaignInfluencer.id == influencer.id).first()
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating influencer and assigned status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating statuses - all changes reverted"
            ) from e
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating statuses: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating statuses - all changes reverted"
            ) from e
        
    @staticmethod
    async def remove_influencer(influencer_id: uuid.UUID, db: Session):
        """
        Remove an influencer from a campaign list
        """
        try:
            influencer = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.id == influencer_id
            ).first()
            
            if not influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign influencer not found"
                )
            
            db.delete(influencer)
            db.commit()
            
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error removing influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error removing influencer from campaign list"
            ) from e

    @staticmethod
    def _parse_followers_count(followers_str: str) -> int:
        """
        Parse followers count from string format (e.g., "1.2K", "1M")
        """
        if not followers_str:
            return 0
        
        followers_str = followers_str.upper().replace(',', '')
        
        try:
            if 'K' in followers_str:
                return int(float(followers_str.replace('K', '')) * 1000)
            elif 'M' in followers_str:
                return int(float(followers_str.replace('M', '')) * 1000000)
            else:
                return int(float(followers_str))
        except (ValueError, TypeError):
            logger.warning(f"Could not parse followers count: {followers_str}")
            return 0
        
    
    @staticmethod
    async def copy_influencers_to_list(
        source_list_id: uuid.UUID,
        target_list_id: uuid.UUID,
        influencer_ids: Optional[List[uuid.UUID]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Copy influencers from one list to another"""
        try:
            # Verify both lists exist
            source_list = db.query(CampaignList).filter(CampaignList.id == source_list_id).first()
            target_list = db.query(CampaignList).filter(CampaignList.id == target_list_id).first()
            
            if not source_list or not target_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Source or target campaign list not found"
                )
            
            # Get influencers to copy
            query = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.campaign_list_id == source_list_id
            )
            
            if influencer_ids:
                query = query.filter(CampaignInfluencer.id.in_(influencer_ids))
            
            source_influencers = query.all()
            
            copied_count = 0
            skipped_count = 0
            errors = []
            
            for source_influencer in source_influencers:
                try:
                    # Check if already exists in target list
                    existing = db.query(CampaignInfluencer).filter(
                        CampaignInfluencer.campaign_list_id == target_list_id,
                        CampaignInfluencer.social_account_id == source_influencer.social_account_id
                    ).first()
                    
                    if existing:
                        skipped_count += 1
                        continue
                    
                    # Create copy
                    new_influencer = CampaignInfluencer(
                        campaign_list_id=target_list_id,
                        social_account_id=source_influencer.social_account_id,
                        status_id=source_influencer.status_id,
                        total_contact_attempts=0,  # Reset contact attempts
                        collaboration_price=source_influencer.collaboration_price,
                        # is_ready_for_onboarding=False,  # Reset onboarding
                        notes=source_influencer.notes
                    )
                    
                    db.add(new_influencer)
                    copied_count += 1
                    
                except Exception as e:
                    errors.append({
                        "social_account_id": str(source_influencer.social_account_id),
                        "error": str(e)
                    })
            
            db.commit()
            
            return {
                "message": "Copy operation completed",
                "copied_count": copied_count,
                "skipped_count": skipped_count,
                "total_processed": len(source_influencers),
                "errors": errors
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error copying influencers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error copying influencers between lists"
            ) from e

    @staticmethod
    async def mark_influencers_onboarded(
        campaign_list_id: str,
        influencer_ids: List[str],
        db: Session
    ) -> None:
        """
        Mark multiple campaign influencers as onboarded with current timestamp
        
        Args:
            campaign_list_id: Campaign list ID
            influencer_ids: List of influencer IDs to mark as onboarded
            db: Database session
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            from datetime import datetime
            
            campaign_list_uuid = uuid.UUID(campaign_list_id)
            influencer_uuids = [uuid.UUID(id_str) for id_str in influencer_ids]
            
            # Verify campaign list exists
            campaign_list = db.query(CampaignList).filter(
                CampaignList.id == campaign_list_uuid
            ).first()
            
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Get target influencers
            target_influencers = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.id.in_(influencer_uuids),
                CampaignInfluencer.campaign_list_id == campaign_list_uuid
            ).all()
            
            # Validate all requested influencers exist
            found_ids = {inf.id for inf in target_influencers}
            missing_ids = set(influencer_uuids) - found_ids
            
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campaign influencers not found in this list: {[str(id) for id in missing_ids]}"
                )
            
            # Get current timestamp and update all influencers
            current_timestamp = datetime.utcnow()
            
            for influencer in target_influencers:
                influencer.onboarded_at = current_timestamp
            
            # Commit all changes
            db.commit()
            logger.info(f"Successfully marked {len(target_influencers)} influencers as onboarded in campaign list {campaign_list_id}")
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in mark_influencers_onboarded: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error marking influencers as onboarded"
            ) from e
        except Exception as e:
            db.rollback()
            logger.error(f"Error in mark_influencers_onboarded: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error marking influencers as onboarded"
            ) from e

    @staticmethod
    async def remove_influencers_onboarded_status(
        campaign_list_id: str,
        influencer_ids: List[str],
        db: Session
    ) -> None:
        """
        Remove onboarded status from multiple campaign influencers
        
        Args:
            campaign_list_id: Campaign list ID
            influencer_ids: List of influencer IDs to remove onboarded status from
            db: Database session
            
        Raises:
            HTTPException: If validation fails or database error occurs
        """
        try:
            campaign_list_uuid = uuid.UUID(campaign_list_id)
            influencer_uuids = [uuid.UUID(id_str) for id_str in influencer_ids]
            
            # Verify campaign list exists
            campaign_list = db.query(CampaignList).filter(
                CampaignList.id == campaign_list_uuid
            ).first()
            
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            # Get target influencers
            target_influencers = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.id.in_(influencer_uuids),
                CampaignInfluencer.campaign_list_id == campaign_list_uuid
            ).all()
            
            # Validate all requested influencers exist
            found_ids = {inf.id for inf in target_influencers}
            missing_ids = set(influencer_uuids) - found_ids
            
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campaign influencers not found in this list: {[str(id) for id in missing_ids]}"
                )
            
            # Clear onboarded_at timestamp for all influencers
            for influencer in target_influencers:
                influencer.onboarded_at = None
            
            # Commit all changes
            db.commit()
            logger.info(f"Successfully removed onboarded status from {len(target_influencers)} influencers in campaign list {campaign_list_id}")
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in remove_influencers_onboarded_status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error removing onboarded status"
            ) from e
        except Exception as e:
            db.rollback()
            logger.error(f"Error in remove_influencers_onboarded_status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error removing onboarded status from influencers"
            ) from e  

    # @staticmethod
    # async def get_contact_history_via_assignments(
    #     campaign_influencer_id: uuid.UUID,
    #     db: Session
    # ) -> List[Dict[str, Any]]:
    #     """Get contact history through assigned influencers"""
    #     try:
    #         from app.Models.assigned_influencers import AssignedInfluencer
    #         from app.Models.influencer_outreach import InfluencerOutreach
            
    #         # Get assigned influencers for this campaign influencer
    #         assigned_influencers = db.query(AssignedInfluencer).filter(
    #             AssignedInfluencer.campaign_influencer_id == campaign_influencer_id
    #         ).all()
            
    #         assigned_influencer_ids = [ai.id for ai in assigned_influencers]
            
    #         # Get outreach records
    #         outreach_records = db.query(InfluencerOutreach).filter(
    #             InfluencerOutreach.assigned_influencer_id.in_(assigned_influencer_ids)
    #         ).order_by(InfluencerOutreach.created_at.desc()).all()
            
    #         return [
    #             {
    #                 "id": str(record.id),
    #                 "assigned_influencer_id": str(record.assigned_influencer_id),
    #                 "outreach_agent_id": str(record.outreach_agent_id),
    #                 "message_sent_at": record.message_sent_at,
    #                 "error_code": record.error_code,
    #                 "error_reason": record.error_reason,
    #                 "created_at": record.created_at,
    #                 "communication_channel_id": str(record.communication_channel_id) if record.communication_channel_id else None
    #             }
    #             for record in outreach_records
    #         ]
            
    #     except Exception as e:
    #         logger.error(f"Error fetching contact history for campaign influencer {campaign_influencer_id}: {str(e)}")
    #         raise HTTPException(
    #             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #             detail="Error fetching contact history"
    #         )