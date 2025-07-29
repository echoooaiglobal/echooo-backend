# app/Http/Controllers/CampaignInfluencerController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import math
from app.Models.auth_models import User
from app.Schemas.campaign_influencer import (
    CampaignInfluencerCreate, CampaignInfluencerUpdate, CampaignInfluencerResponse,
    SocialAccountBrief, StatusBrief,
    CampaignInfluencerBulkCreate, CampaignInfluencersPaginatedResponse, PaginationInfo, CampaignInfluencerPriceUpdate
)
from app.Models.assigned_influencers import AssignedInfluencer
from app.Models.influencer_outreach import InfluencerOutreach
from app.Services.CampaignInfluencerService import CampaignInfluencerService
from app.Utils.Logger import logger
from app.Services.BulkAssignmentService import BulkAssignmentService
from app.Models.agent_assignments import AgentAssignment

class CampaignInfluencerController:
    """Controller for campaign influencer-related endpoints"""
    
    @staticmethod
    async def update_influencer_status(
        influencer_id: uuid.UUID,
        status_id: uuid.UUID,
        db: Session
    ):
        """Update the status of a campaign influencer"""
        try:
            update_data = {"status_id": str(status_id)}
            influencer = await CampaignInfluencerService.update_influencer(
                influencer_id, update_data, db
            )
            return CampaignInfluencerController._format_influencer_response(influencer)
        except Exception as e:
            logger.error(f"Error in update_influencer_status controller: {str(e)}")
            raise

    @staticmethod
    async def mark_ready_for_onboarding(
        influencer_id: uuid.UUID,
        collaboration_price: Optional[float],
        db: Session
    ):
        """Mark an influencer as ready for onboarding"""
        try:
            update_data = {
                "is_ready_for_onboarding": True,
                "collaboration_price": collaboration_price
            }
            influencer = await CampaignInfluencerService.update_influencer(
                influencer_id, update_data, db
            )
            return CampaignInfluencerController._format_influencer_response(influencer)
        except Exception as e:
            logger.error(f"Error in mark_ready_for_onboarding controller: {str(e)}")
            raise

    @staticmethod
    def _format_influencer_response(influencer) -> CampaignInfluencerResponse:
        """Format a campaign influencer object into a response"""
        # Convert to response object
        response = CampaignInfluencerResponse.model_validate(influencer)
        
        # Add status details if available
        if influencer.status:
            response.status = StatusBrief.model_validate(influencer.status)
        
        # Add social account details if available
        if influencer.social_account:
            response.social_account = SocialAccountBrief.model_validate(influencer.social_account)
        
        return response
    async def get_list_influencers_paginated(
        campaign_list_id: uuid.UUID, 
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ):
        """Get paginated influencers of a campaign list"""
        try:
            influencers, total_count = await CampaignInfluencerService.get_list_influencers_paginated(
                campaign_list_id, page, page_size, db
            )
            
            # Format the response
            formatted_influencers = [
                CampaignInfluencerController._format_influencer_response(influencer)
                for influencer in influencers
            ]
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=page_size,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
            
            return CampaignInfluencersPaginatedResponse(
                influencers=formatted_influencers,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_list_influencers_paginated controller: {str(e)}")
            raise

    @staticmethod
    async def get_all_influencers_paginated(
        page: int = 1, 
        page_size: int = 10,
        db: Session = None
    ):
        """Get paginated influencers across all lists"""
        try:
            influencers, total_count = await CampaignInfluencerService.get_all_influencers_paginated(
                page, page_size, db
            )
            
            # Format the response
            formatted_influencers = [
                CampaignInfluencerController._format_influencer_response(influencer)
                for influencer in influencers
            ]
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
            
            pagination_info = PaginationInfo(
                page=page,
                page_size=page_size,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
            
            return CampaignInfluencersPaginatedResponse(
                influencers=formatted_influencers,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_all_influencers_paginated controller: {str(e)}")
            raise

    @staticmethod
    async def get_influencer(influencer_id: uuid.UUID, db: Session):
        """Get a campaign influencer by ID"""
        try:
            influencer = await CampaignInfluencerService.get_influencer_by_id(influencer_id, db)
            return CampaignInfluencerController._format_influencer_response(influencer)
        except Exception as e:
            logger.error(f"Error in get_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_influencer(
        campaign_list_id: uuid.UUID,
        influencer_data: Dict[str, Any],
        db: Session
    ):
        """Add an influencer to a campaign list with automatic agent assignment"""
        try:
            # Convert to dict if it's a Pydantic model
            data_dict = influencer_data if isinstance(influencer_data, dict) else influencer_data.model_dump(exclude_unset=True)

            # Ensure campaign_list_id from path is used
            data_dict['campaign_list_id'] = str(campaign_list_id)
            
            # Step 1: Add influencer to campaign_influencer table (existing logic)
            influencer = None
            if 'social_data' in data_dict and data_dict['social_data']:
                # Handle with social data (for bulk creation)
                platform_id = data_dict.get('platform_id')
                if not platform_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="platform_id is required when using social_data"
                    )
                
                # Call the service method that handles creating or finding the social account
                influencer = await CampaignInfluencerService.add_influencer_with_social_data(
                    campaign_list_id=uuid.UUID(data_dict['campaign_list_id']) if isinstance(data_dict['campaign_list_id'], str) else data_dict['campaign_list_id'],
                    platform_id=uuid.UUID(platform_id) if isinstance(platform_id, str) else platform_id,
                    social_data=data_dict['social_data'],
                    db=db
                )
            else:
                # Handle with social_account_id (traditional flow)
                if 'social_account_id' not in data_dict or not data_dict['social_account_id']:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="social_account_id is required when not using social_data"
                    )
                
                # Call the original method
                influencer = await CampaignInfluencerService.add_influencer(data_dict, db)
            
            # Step 2: Check if campaign list has existing agent assignments
            existing_assignments = db.query(AgentAssignment).filter(
                AgentAssignment.campaign_list_id == campaign_list_id,
                AgentAssignment.is_deleted == False
            ).first()
            
            # Step 3: If campaign list has assignments, auto-assign the new influencer
            if existing_assignments:
                try:
                    logger.info(f"Campaign list {campaign_list_id} has existing assignments. Auto-assigning new influencer {influencer.id}")
                    
                    # Use the existing BulkAssignmentService to assign this single influencer
                    assignment_result = await BulkAssignmentService.execute_bulk_assignment(
                        campaign_list_id=campaign_list_id,
                        strategy="load_balanced",  # Use load_balanced for better distribution
                        preferred_agent_ids=None,  # Let it find the best available agent
                        max_influencers_per_agent=None,  # Use default limits
                        force_new_assignments=False,  # Allow using existing assignments
                        db=db
                    )
                    
                    # Log the assignment result
                    if assignment_result.get("agent_assignments"):
                        assigned_count = sum([
                            assignment["assigned_influencers_count"] 
                            for assignment in assignment_result["agent_assignments"]
                        ])
                        logger.info(f"Successfully auto-assigned {assigned_count} influencer(s) to agents")
                    else:
                        logger.warning(f"No agents were available to assign the new influencer {influencer.id}")
                        
                except Exception as assignment_error:
                    # Log the error but don't fail the entire operation
                    logger.error(f"Failed to auto-assign influencer {influencer.id}: {str(assignment_error)}")
                    # The influencer was still added to the campaign list successfully
            else:
                logger.info(f"Campaign list {campaign_list_id} has no existing assignments. Skipping auto-assignment.")
            
            return CampaignInfluencerController._format_influencer_response(influencer)
            
        except Exception as e:
            logger.error(f"Error in add_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def add_bulk_influencers(
        campaign_list_id: uuid.UUID,
        platform_id: uuid.UUID,
        influencers_data: List[Dict[str, Any]],
        db: Session
    ):
        """Add multiple influencers to a campaign list in bulk with automatic agent assignment"""
        try:
            result_influencers = []
            successfully_added_count = 0
            
            # Step 1: Add all influencers to campaign_influencer table (existing logic)
            logger.info(f"Adding {len(influencers_data)} influencers to campaign list {campaign_list_id}")
            
            for influencer_data in influencers_data:
                try:
                    influencer = await CampaignInfluencerService.add_influencer_with_social_data(
                        campaign_list_id=campaign_list_id,
                        platform_id=platform_id,
                        social_data=influencer_data,
                        db=db
                    )
                    result_influencers.append(
                        CampaignInfluencerController._format_influencer_response(influencer)
                    )
                    successfully_added_count += 1
                except Exception as e:
                    # Log the error for this specific influencer but continue with others
                    logger.error(f"Error adding influencer {influencer_data.get('username', 'unknown')}: {str(e)}")
                    # Don't raise here to allow other influencers to be processed
            
            logger.info(f"Successfully added {successfully_added_count} out of {len(influencers_data)} influencers")
            
            # Step 2: Check if campaign list has existing agent assignments
            if successfully_added_count > 0:  # Only proceed if we added at least one influencer
                existing_assignments = db.query(AgentAssignment).filter(
                    AgentAssignment.campaign_list_id == campaign_list_id,
                    AgentAssignment.is_deleted == False
                ).first()
                
                # Step 3: If campaign list has assignments, auto-assign all new influencers
                if existing_assignments:
                    try:
                        logger.info(f"Campaign list {campaign_list_id} has existing assignments. Auto-assigning {successfully_added_count} new influencers")
                        
                        # Use the existing BulkAssignmentService to assign all newly added influencers
                        assignment_result = await BulkAssignmentService.execute_bulk_assignment(
                            campaign_list_id=campaign_list_id,
                            strategy="load_balanced",  # Use load_balanced for better distribution
                            preferred_agent_ids=None,  # Let it find the best available agents
                            max_influencers_per_agent=None,  # Use default limits
                            force_new_assignments=False,  # Allow using existing assignments
                            db=db
                        )
                        
                        # Log the assignment result
                        if assignment_result.get("agent_assignments"):
                            total_assigned = sum([
                                assignment["assigned_influencers_count"] 
                                for assignment in assignment_result["agent_assignments"]
                            ])
                            unassigned_count = len(assignment_result.get("unassigned_influencers", []))
                            
                            logger.info(f"Auto-assignment completed: {total_assigned} assigned, {unassigned_count} unassigned")
                            
                            if assignment_result.get("warnings"):
                                for warning in assignment_result["warnings"]:
                                    logger.warning(f"Assignment warning: {warning}")
                                    
                            if assignment_result.get("errors"):
                                for error in assignment_result["errors"]:
                                    logger.error(f"Assignment error: {error}")
                        else:
                            logger.warning(f"No agents were available to assign the {successfully_added_count} new influencers")
                            
                    except Exception as assignment_error:
                        # Log the error but don't fail the entire operation
                        logger.error(f"Failed to auto-assign {successfully_added_count} influencers: {str(assignment_error)}")
                        # The influencers were still added to the campaign list successfully
                else:
                    logger.info(f"Campaign list {campaign_list_id} has no existing assignments. Skipping auto-assignment for {successfully_added_count} influencers.")
            
            return result_influencers
            
        except Exception as e:
            logger.error(f"Error in add_bulk_influencers controller: {str(e)}")
            raise

    @staticmethod
    async def update_influencer(
        influencer_id: uuid.UUID,
        influencer_data: CampaignInfluencerUpdate,
        db: Session
    ):
        """Update a campaign influencer"""
        try:
            influencer = await CampaignInfluencerService.update_influencer(
                influencer_id,
                influencer_data.model_dump(exclude_unset=True),
                db
            )
            return CampaignInfluencerController._format_influencer_response(influencer)
        except Exception as e:
            logger.error(f"Error in update_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def remove_influencer(influencer_id: uuid.UUID, db: Session):
        """Remove an influencer from a campaign list"""
        try:
            await CampaignInfluencerService.remove_influencer(influencer_id, db)
            return {"message": "Influencer removed successfully"}
        except Exception as e:
            logger.error(f"Error in remove_influencer controller: {str(e)}")
            raise
    

    # Additional methods to ADD to CampaignInfluencerController.py

    @staticmethod
    async def bulk_update_status(
        influencer_ids: List[uuid.UUID],
        status_id: uuid.UUID,
        db: Session
    ):
        """Bulk update status for multiple campaign influencers"""
        try:
            updated_influencers = []
            for influencer_id in influencer_ids:
                try:
                    update_data = {"status_id": str(status_id)}
                    influencer = await CampaignInfluencerService.update_influencer(
                        influencer_id, update_data, db
                    )
                    updated_influencers.append(
                        CampaignInfluencerController._format_influencer_response(influencer)
                    )
                except Exception as e:
                    logger.error(f"Error updating influencer {influencer_id}: {str(e)}")
                    # Continue with other influencers
            return updated_influencers
        except Exception as e:
            logger.error(f"Error in bulk_update_status controller: {str(e)}")
            raise

    @staticmethod
    async def update_contact_attempts(
        influencer_id: uuid.UUID,
        increment: int,
        db: Session
    ):
        """Update contact attempts for a campaign influencer"""
        try:
            influencer = await CampaignInfluencerService.get_influencer_by_id(influencer_id, db)
            new_attempts = influencer.total_contact_attempts + increment
            
            update_data = {"total_contact_attempts": new_attempts}
            updated_influencer = await CampaignInfluencerService.update_influencer(
                influencer_id, update_data, db
            )
            return CampaignInfluencerController._format_influencer_response(updated_influencer)
        except Exception as e:
            logger.error(f"Error in update_contact_attempts controller: {str(e)}")
            raise

    @staticmethod
    async def get_contact_history(influencer_id: uuid.UUID, db: Session):
        """Get contact history for a campaign influencer"""
        try:
            # Find assigned influencers for this campaign influencer
            assigned_influencers = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.campaign_influencer_id == influencer_id
            ).all()
            
            assigned_influencer_ids = [ai.id for ai in assigned_influencers]
            
            # Get outreach records for these assigned influencers
            history = db.query(InfluencerOutreach).filter(
                InfluencerOutreach.assigned_influencer_id.in_(assigned_influencer_ids)
            ).order_by(InfluencerOutreach.created_at.desc()).all()
            
            return [
                {
                    "id": str(record.id),
                    "message_sent_at": record.message_sent_at,
                    "error_code": record.error_code,
                    "error_reason": record.error_reason,
                    "created_at": record.created_at,
                    "communication_channel_id": str(record.communication_channel_id) if record.communication_channel_id else None,
                    "outreach_agent_id": str(record.outreach_agent_id),
                    "assigned_influencer_id": str(record.assigned_influencer_id)
                }
                for record in history
            ]
        except Exception as e:
            logger.error(f"Error in get_contact_history controller: {str(e)}")
            raise

    @staticmethod
    async def get_onboarding_pipeline(campaign_list_id: Optional[uuid.UUID], db: Session):
        """Get influencers in the onboarding pipeline"""
        try:
            from app.Models.campaign_influencers import CampaignInfluencer
            
            query = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.is_ready_for_onboarding == True
            )
            
            if campaign_list_id:
                query = query.filter(CampaignInfluencer.campaign_list_id == campaign_list_id)
            
            influencers = query.order_by(CampaignInfluencer.created_at.desc()).all()
            
            return [
                CampaignInfluencerController._format_influencer_response(influencer)
                for influencer in influencers
            ]
        except Exception as e:
            logger.error(f"Error in get_onboarding_pipeline controller: {str(e)}")
            raise

    @staticmethod
    async def get_list_influencer_stats(campaign_list_id: uuid.UUID, db: Session):
        """Get detailed statistics for influencers in a campaign list"""
        try:
            from app.Models.campaign_influencers import CampaignInfluencer
            from sqlalchemy import func, and_
            
            # Basic counts
            total_count = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.campaign_list_id == campaign_list_id
            ).count()
            
            # Status breakdown
            status_breakdown = db.query(
                CampaignInfluencer.status_id,
                func.count(CampaignInfluencer.id).label('count')
            ).filter(
                CampaignInfluencer.campaign_list_id == campaign_list_id
            ).group_by(CampaignInfluencer.status_id).all()
            
            # Onboarding stats
            onboarded_count = db.query(CampaignInfluencer).filter(
                and_(
                    CampaignInfluencer.campaign_list_id == campaign_list_id,
                    CampaignInfluencer.is_ready_for_onboarding == True
                )
            ).count()
            
            # Contact attempts stats
            contact_stats = db.query(
                func.avg(CampaignInfluencer.total_contact_attempts).label('avg_attempts'),
                func.max(CampaignInfluencer.total_contact_attempts).label('max_attempts'),
                func.min(CampaignInfluencer.total_contact_attempts).label('min_attempts')
            ).filter(
                CampaignInfluencer.campaign_list_id == campaign_list_id
            ).first()
            
            # Price stats
            price_stats = db.query(
                func.avg(CampaignInfluencer.collaboration_price).label('avg_price'),
                func.max(CampaignInfluencer.collaboration_price).label('max_price'),
                func.min(CampaignInfluencer.collaboration_price).label('min_price'),
                func.count(CampaignInfluencer.collaboration_price).label('with_price_count')
            ).filter(
                and_(
                    CampaignInfluencer.campaign_list_id == campaign_list_id,
                    CampaignInfluencer.collaboration_price.isnot(None)
                )
            ).first()
            
            return {
                "campaign_list_id": str(campaign_list_id),
                "total_influencers": total_count,
                "onboarded_count": onboarded_count,
                "onboarding_rate": (onboarded_count / total_count * 100) if total_count > 0 else 0,
                "status_breakdown": [
                    {"status_id": str(item.status_id), "count": item.count}
                    for item in status_breakdown
                ],
                "contact_stats": {
                    "avg_attempts": float(contact_stats.avg_attempts) if contact_stats.avg_attempts else 0,
                    "max_attempts": contact_stats.max_attempts or 0,
                    "min_attempts": contact_stats.min_attempts or 0
                },
                "price_stats": {
                    "avg_price": float(price_stats.avg_price) if price_stats.avg_price else 0,
                    "max_price": float(price_stats.max_price) if price_stats.max_price else 0,
                    "min_price": float(price_stats.min_price) if price_stats.min_price else 0,
                    "with_price_count": price_stats.with_price_count or 0,
                    "without_price_count": total_count - (price_stats.with_price_count or 0)
                }
            }
        except Exception as e:
            logger.error(f"Error in get_list_influencer_stats controller: {str(e)}")
            raise

    @staticmethod
    async def get_price_analytics(campaign_list_id: uuid.UUID, db: Session):
        """Get collaboration price analytics for a campaign list"""
        try:
            from app.Models.campaign_influencers import CampaignInfluencer
            from sqlalchemy import func, and_
            
            # Price range breakdown
            price_ranges = [
                (0, 100, "0-100"),
                (100, 500, "100-500"),
                (500, 1000, "500-1000"),
                (1000, 5000, "1000-5000"),
                (5000, None, "5000+")
            ]
            
            range_breakdown = []
            for min_price, max_price, label in price_ranges:
                query = db.query(CampaignInfluencer).filter(
                    and_(
                        CampaignInfluencer.campaign_list_id == campaign_list_id,
                        CampaignInfluencer.collaboration_price >= min_price
                    )
                )
                
                if max_price:
                    query = query.filter(CampaignInfluencer.collaboration_price < max_price)
                
                count = query.count()
                range_breakdown.append({
                    "range": label,
                    "count": count,
                    "min_price": min_price,
                    "max_price": max_price
                })
            
            # Overall stats
            overall_stats = db.query(
                func.count(CampaignInfluencer.collaboration_price).label('total_with_price'),
                func.avg(CampaignInfluencer.collaboration_price).label('avg_price'),
                func.stddev(CampaignInfluencer.collaboration_price).label('std_dev'),
                func.percentile_cont(0.5).within_group(CampaignInfluencer.collaboration_price).label('median')
            ).filter(
                and_(
                    CampaignInfluencer.campaign_list_id == campaign_list_id,
                    CampaignInfluencer.collaboration_price.isnot(None)
                )
            ).first()
            
            return {
                "campaign_list_id": str(campaign_list_id),
                "overall_stats": {
                    "total_with_price": overall_stats.total_with_price or 0,
                    "avg_price": float(overall_stats.avg_price) if overall_stats.avg_price else 0,
                    "std_dev": float(overall_stats.std_dev) if overall_stats.std_dev else 0,
                    "median": float(overall_stats.median) if overall_stats.median else 0
                },
                "price_range_breakdown": range_breakdown
            }
        except Exception as e:
            logger.error(f"Error in get_price_analytics controller: {str(e)}")
            raise

    @staticmethod
    async def advanced_search(
        page: int,
        page_size: int,
        campaign_list_id: Optional[uuid.UUID],
        status_id: Optional[uuid.UUID],
        min_price: Optional[float],
        max_price: Optional[float],
        is_ready_for_onboarding: Optional[bool],
        min_contact_attempts: Optional[int],
        max_contact_attempts: Optional[int],
        db: Session
    ):
        """Advanced search for campaign influencers with multiple filters"""
        try:
            from app.Models.campaign_influencers import CampaignInfluencer
            from sqlalchemy import and_
            import math
            
            # Build query with filters
            query = db.query(CampaignInfluencer)
            
            filters = []
            if campaign_list_id:
                filters.append(CampaignInfluencer.campaign_list_id == campaign_list_id)
            if status_id:
                filters.append(CampaignInfluencer.status_id == status_id)
            if min_price is not None:
                filters.append(CampaignInfluencer.collaboration_price >= min_price)
            if max_price is not None:
                filters.append(CampaignInfluencer.collaboration_price <= max_price)
            if is_ready_for_onboarding is not None:
                filters.append(CampaignInfluencer.is_ready_for_onboarding == is_ready_for_onboarding)
            if min_contact_attempts is not None:
                filters.append(CampaignInfluencer.total_contact_attempts >= min_contact_attempts)
            if max_contact_attempts is not None:
                filters.append(CampaignInfluencer.total_contact_attempts <= max_contact_attempts)
            
            if filters:
                query = query.filter(and_(*filters))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            influencers = query.offset(offset).limit(page_size).all()
            
            # Format response
            formatted_influencers = [
                CampaignInfluencerController._format_influencer_response(influencer)
                for influencer in influencers
            ]
            
            # Calculate pagination info
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
            
            from app.Schemas.campaign_influencer import PaginationInfo, CampaignInfluencersPaginatedResponse
            pagination_info = PaginationInfo(
                page=page,
                page_size=page_size,
                total_items=total_count,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1
            )
            
            return CampaignInfluencersPaginatedResponse(
                influencers=formatted_influencers,
                pagination=pagination_info
            )
        except Exception as e:
            logger.error(f"Error in advanced_search controller: {str(e)}")
            raise

    @staticmethod
    async def batch_remove_influencers(influencer_ids: List[uuid.UUID], db: Session):
        """Remove multiple influencers from campaign lists"""
        try:
            removed_count = 0
            errors = []
            
            for influencer_id in influencer_ids:
                try:
                    await CampaignInfluencerService.remove_influencer(influencer_id, db)
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Error removing influencer {influencer_id}: {str(e)}")
                    errors.append({"influencer_id": str(influencer_id), "error": str(e)})
            
            return {
                "message": f"Batch removal completed",
                "removed_count": removed_count,
                "total_requested": len(influencer_ids),
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Error in batch_remove_influencers controller: {str(e)}")
            raise

    @staticmethod
    async def transfer_influencer_to_list(
        influencer_id: uuid.UUID,
        target_list_id: uuid.UUID,
        db: Session
    ):
        """Transfer an influencer to a different campaign list"""
        try:
            update_data = {"campaign_list_id": str(target_list_id)}
            influencer = await CampaignInfluencerService.update_influencer(
                influencer_id, update_data, db
            )
            return {
                "message": "Influencer transferred successfully",
                "influencer": CampaignInfluencerController._format_influencer_response(influencer)
            }
        except Exception as e:
            logger.error(f"Error in transfer_influencer_to_list controller: {str(e)}")
            raise

    @staticmethod
    async def copy_influencers_to_list(
        source_list_id: uuid.UUID,
        target_list_id: uuid.UUID,
        influencer_ids: Optional[List[uuid.UUID]],
        db: Session
    ):
        """Copy influencers from one list to another"""
        try:
            result = await CampaignInfluencerService.copy_influencers_to_list(
                source_list_id, target_list_id, influencer_ids, db
            )
            return result
        except Exception as e:
            logger.error(f"Error in copy_influencers_to_list controller: {str(e)}")
            raise

    @staticmethod
    async def update_collaboration_price(
        influencer_id: uuid.UUID,
        price_data: CampaignInfluencerPriceUpdate,
        db: Session
    ) -> bool:
        """
        Update collaboration price and currency from price update data
        
        Args:
            influencer_id: ID of the campaign influencer
            price_data: Pydantic model with collaboration_price and currency
            db: Database session
            
        Returns:
            bool: True if update was successful
            
        Raises:
            HTTPException: If validation fails or influencer not found
        """
        try:
            update_data = {}
            
            if price_data.collaboration_price is not None:
                update_data["collaboration_price"] = price_data.collaboration_price
                
            if price_data.currency is not None:
                # Validate currency format
                import re
                if not re.match(r'^[A-Z]{3}$', price_data.currency):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Currency must be a valid 3-letter ISO 4217 code (e.g., USD, EUR, GBP)"
                    )
                update_data["currency"] = price_data.currency
                
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one field (collaboration_price or currency) must be provided"
                )
                
            # Use existing service method
            await CampaignInfluencerService.update_influencer(
                influencer_id, update_data, db
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in update_collaboration_price controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating collaboration price and currency"
            ) from e

    @staticmethod
    async def update_status(
        influencer_id: uuid.UUID,
        status_id: str,
        assigned_influencer_id: Optional[str],
        db: Session
    ) -> bool:
        """
        Update status for campaign influencer and optionally assigned influencer
        Both updates happen in a single transaction - if either fails, both are reverted
        """
        try:
            # Use the new service method that handles transaction atomicity
            await CampaignInfluencerService.update_influencer_with_assigned_status(
                influencer_id, status_id, assigned_influencer_id, db
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_status controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating status"
            ) from e

    @staticmethod
    async def update_notes_only(
        influencer_id: uuid.UUID,
        notes: Optional[str],
        db: Session
    ) -> bool:
        """
        Update only the notes for a campaign influencer
        
        Args:
            influencer_id: ID of the campaign influencer
            notes: New notes content
            db: Database session
            
        Returns:
            bool: True if update was successful
            
        Raises:
            HTTPException: If influencer not found or update fails
        """
        try:
            update_data = {"notes": notes}
            
            # Use existing service method
            await CampaignInfluencerService.update_influencer(
                influencer_id, update_data, db
            )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_notes_only controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating notes"
            ) from e

    @staticmethod
    async def get_price_by_currency_stats(campaign_list_id: uuid.UUID, db: Session):
        """
        Get collaboration price statistics grouped by currency for analytics
        
        Args:
            campaign_list_id: ID of the campaign list
            db: Database session
            
        Returns:
            dict: Currency-grouped price statistics
        """
        try:
            from app.Models.campaign_influencers import CampaignInfluencer
            from sqlalchemy import func, and_
            
            # Price stats by currency
            currency_stats = db.query(
                CampaignInfluencer.currency,
                func.count(CampaignInfluencer.id).label('count'),
                func.avg(CampaignInfluencer.collaboration_price).label('avg_price'),
                func.min(CampaignInfluencer.collaboration_price).label('min_price'),
                func.max(CampaignInfluencer.collaboration_price).label('max_price'),
                func.sum(CampaignInfluencer.collaboration_price).label('total_value')
            ).filter(
                and_(
                    CampaignInfluencer.campaign_list_id == campaign_list_id,
                    CampaignInfluencer.collaboration_price.isnot(None),
                    CampaignInfluencer.currency.isnot(None)
                )
            ).group_by(CampaignInfluencer.currency).all()
            
            return {
                "campaign_list_id": str(campaign_list_id),
                "currency_breakdown": [
                    {
                        "currency": stat.currency,
                        "count": stat.count,
                        "avg_price": float(stat.avg_price) if stat.avg_price else 0,
                        "min_price": float(stat.min_price) if stat.min_price else 0,
                        "max_price": float(stat.max_price) if stat.max_price else 0,
                        "total_value": float(stat.total_value) if stat.total_value else 0
                    }
                    for stat in currency_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in get_price_by_currency_stats controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error getting currency statistics"
            ) from e
        
    @staticmethod
    async def mark_onboarded(
        campaign_list_id: str,
        influencer_ids: List[str],
        db: Session
    ) -> str:
        """
        Mark campaign influencers as onboarded with current timestamp
        
        Args:
            campaign_list_id: Campaign list ID
            influencer_ids: List of influencer IDs to mark as onboarded
            db: Database session
            
        Returns:
            Success message string
        """
        try:
            await CampaignInfluencerService.mark_influencers_onboarded(
                campaign_list_id, influencer_ids, db
            )
            
            count = len(influencer_ids)
            return f"Successfully marked {count} influencer{'s' if count != 1 else ''} as onboarded"
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in mark_onboarded controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error marking influencers as onboarded"
            ) from e

    @staticmethod
    async def remove_onboarded(
        campaign_list_id: str,
        influencer_ids: List[str],
        db: Session
    ) -> str:
        """
        Remove onboarded status from campaign influencers
        
        Args:
            campaign_list_id: Campaign list ID
            influencer_ids: List of influencer IDs to remove onboarded status from
            db: Database session
            
        Returns:
            Success message string
        """
        try:
            await CampaignInfluencerService.remove_influencers_onboarded_status(
                campaign_list_id, influencer_ids, db
            )
            
            count = len(influencer_ids)
            return f"Successfully removed {count} onboarded influencer{'s' if count != 1 else ''}"
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in remove_onboarded controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error removing onboarded status from influencers"
            ) from e