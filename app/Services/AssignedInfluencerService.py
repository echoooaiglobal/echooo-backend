# app/Services/AssignedInfluencerService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, asc
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid
from datetime import datetime, timedelta, timezone

from app.Models.assigned_influencers import AssignedInfluencer
from app.Models.campaign_influencers import CampaignInfluencer
from app.Models.agent_assignments import AgentAssignment
from app.Models.statuses import Status
from app.Models.message_templates import MessageTemplate
from app.Models.campaign_lists import CampaignList
from app.Models.influencer_outreach import InfluencerOutreach
from app.Utils.Logger import logger

class AssignedInfluencerService:
    """Service for managing assigned influencers"""

    @staticmethod
    async def create_assigned_influencer(
        data: Dict[str, Any],
        db: Session
    ) -> AssignedInfluencer:
        """Create a new assigned influencer"""
        try:
            # Validate campaign influencer exists
            campaign_influencer = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.id == data["campaign_influencer_id"]
            ).first()
            
            if not campaign_influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign influencer not found"
                )
            
            # Validate agent assignment exists
            agent_assignment = db.query(AgentAssignment).filter(
                AgentAssignment.id == data["agent_assignment_id"]
            ).first()
            
            if not agent_assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent assignment not found"
                )
          
            # Validate status
            status_obj = db.query(Status).filter(
                and_(
                    Status.id == data["status_id"],
                    Status.model == "assigned_influencer"
                )
            ).first()
            
            if not status_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid status for assigned influencer"
                )
            
            # Create assigned influencer
            assigned_influencer = AssignedInfluencer(**data)
            db.add(assigned_influencer)
            db.commit()
            db.refresh(assigned_influencer)
            
            # Update agent assignment counts
            await AssignedInfluencerService._update_agent_assignment_counts(
                agent_assignment.id, db
            )
            
            logger.info(f"Created assigned influencer {assigned_influencer.id}")
            return assigned_influencer
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating assigned influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating assigned influencer"
            )
    
    @staticmethod
    async def get_assigned_influencer_by_id(
        assigned_influencer_id: uuid.UUID,
        db: Session,
        include_relations: bool = True
    ) -> AssignedInfluencer:
        """Get an assigned influencer by ID"""
        try:
            query = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.id == assigned_influencer_id
            )
            
            if include_relations:
                query = query.options(
                    joinedload(AssignedInfluencer.campaign_influencer).joinedload(CampaignInfluencer.social_account),  # UPDATED: Added social account loading
                    joinedload(AssignedInfluencer.agent_assignment),
                    joinedload(AssignedInfluencer.status)
                )
            
            assigned_influencer = query.first()
            
            if not assigned_influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned influencer not found"
                )
            
            return assigned_influencer
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting assigned influencer {assigned_influencer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assigned influencer"
            )
    
    @staticmethod
    async def get_assigned_influencers(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        agent_assignment_id: Optional[uuid.UUID] = None,
        campaign_influencer_id: Optional[uuid.UUID] = None,
        status_id: Optional[uuid.UUID] = None,
        assignment_type: Optional[str] = None,
        type: Optional[str] = None,  # ADD this line
        include_relations: bool = False,
        sort_by: str = "assigned_at",
        sort_order: str = "desc"
    ) -> Tuple[List[AssignedInfluencer], int]:
        """Get assigned influencers with filtering and pagination"""
        try:
            query = db.query(AssignedInfluencer)
            
            # Apply filters
            if agent_assignment_id:
                query = query.filter(AssignedInfluencer.agent_assignment_id == agent_assignment_id)
            
            if campaign_influencer_id:
                query = query.filter(AssignedInfluencer.campaign_influencer_id == campaign_influencer_id)
            
            if status_id:
                query = query.filter(AssignedInfluencer.status_id == status_id)
            
            if assignment_type:
                query = query.filter(AssignedInfluencer.type == assignment_type)
            
            if type:  # ADD this filter
                query = query.filter(AssignedInfluencer.type == type)
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            if sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(AssignedInfluencer, sort_by)))
            else:
                query = query.order_by(asc(getattr(AssignedInfluencer, sort_by)))
            
            # Include relations if requested
            if include_relations:
                query = query.options(
                    joinedload(AssignedInfluencer.campaign_influencer).joinedload(CampaignInfluencer.social_account),
                    joinedload(AssignedInfluencer.agent_assignment),
                    joinedload(AssignedInfluencer.status)
                )
            
            # Apply pagination
            assigned_influencers = query.offset(skip).limit(limit).all()
            
            return assigned_influencers, total
            
        except Exception as e:
            logger.error(f"Error getting assigned influencers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assigned influencers"
            )
    
    @staticmethod
    async def update_assigned_influencer(
        assigned_influencer_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> AssignedInfluencer:
        """Update an assigned influencer"""
        try:
            assigned_influencer = await AssignedInfluencerService.get_assigned_influencer_by_id(
                assigned_influencer_id, db, include_relations=False
            )
            
            # Update fields
            for field, value in data.items():
                if hasattr(assigned_influencer, field):
                    setattr(assigned_influencer, field, value)
            
            db.commit()
            db.refresh(assigned_influencer)
            
            # Update agent assignment counts if relevant fields changed
            if any(field in data for field in ['status_id', 'type']):
                await AssignedInfluencerService._update_agent_assignment_counts(
                    assigned_influencer.agent_assignment_id, db
                )
            
            logger.info(f"Updated assigned influencer {assigned_influencer_id}")
            return assigned_influencer
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating assigned influencer {assigned_influencer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating assigned influencer"
            )
    
    @staticmethod
    async def update_contact_info(
        assigned_influencer_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> AssignedInfluencer:
        """Update contact information for an assigned influencer"""
        try:
            assigned_influencer = await AssignedInfluencerService.get_assigned_influencer_by_id(
                assigned_influencer_id, db, include_relations=False
            )
            
            # Update contact fields
            contact_fields = ['attempts_made', 'last_contacted_at', 'next_contact_at', 'responded_at', 'notes']
            
            for field in contact_fields:
                if field in data:
                    setattr(assigned_influencer, field, data[field])
            
            # If responded_at is set, update the campaign influencer's response count
            if 'responded_at' in data and data['responded_at'] and not assigned_influencer.responded_at:
                campaign_influencer = db.query(CampaignInfluencer).filter(
                    CampaignInfluencer.id == assigned_influencer.campaign_influencer_id
                ).first()
                
                if campaign_influencer:
                    campaign_influencer.total_contact_attempts = assigned_influencer.attempts_made
            
            db.commit()
            db.refresh(assigned_influencer)
            
            logger.info(f"Updated contact info for assigned influencer {assigned_influencer_id}")
            return assigned_influencer
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating contact info {assigned_influencer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating contact information"
            )
    
    @staticmethod
    async def bulk_update_status(
        influencer_ids: List[uuid.UUID],
        status_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """Bulk update status for multiple assigned influencers"""
        try:
            # Validate status
            status_obj = db.query(Status).filter(
                and_(
                    Status.id == status_id,
                    Status.model == "assigned_influencer"
                )
            ).first()
            
            if not status_obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Invalid status for assigned influencer"
                )
            
            # Update all influencers
            updated_count = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.id.in_(influencer_ids)
            ).update(
                {"status_id": status_id},
                synchronize_session="fetch"
            )
            
            db.commit()
            
            # Update agent assignment counts for affected assignments
            affected_assignments = db.query(AssignedInfluencer.agent_assignment_id).filter(
                AssignedInfluencer.id.in_(influencer_ids)
            ).distinct().all()
            
            for (assignment_id,) in affected_assignments:
                await AssignedInfluencerService._update_agent_assignment_counts(
                    assignment_id, db
                )
            
            logger.info(f"Bulk updated {updated_count} assigned influencers to status {status_id}")
            return {
                "updated_count": updated_count,
                "status": "success"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk updating status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error bulk updating status"
            )
    
    @staticmethod
    async def transfer_to_agent(
        assigned_influencer_id: uuid.UUID,
        new_agent_assignment_id: uuid.UUID,
        transfer_reason: Optional[str],
        transferred_by_user_id: uuid.UUID,
        db: Session
    ) -> AssignedInfluencer:
        """Transfer an assigned influencer to a different agent"""
        try:
            assigned_influencer = await AssignedInfluencerService.get_assigned_influencer_by_id(
                assigned_influencer_id, db, include_relations=False
            )
            
            # Validate new agent assignment
            new_agent_assignment = db.query(AgentAssignment).filter(
                AgentAssignment.id == new_agent_assignment_id
            ).first()
            
            if not new_agent_assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="New agent assignment not found"
                )
            
            old_agent_assignment_id = assigned_influencer.agent_assignment_id
            
            # Update assignment
            assigned_influencer.agent_assignment_id = new_agent_assignment_id
            assigned_influencer.notes = f"{assigned_influencer.notes or ''}\nTransferred: {transfer_reason or 'No reason provided'}"
            
            db.commit()
            
            # Update counts for both old and new assignments
            await AssignedInfluencerService._update_agent_assignment_counts(
                old_agent_assignment_id, db
            )
            await AssignedInfluencerService._update_agent_assignment_counts(
                new_agent_assignment_id, db
            )
            
            logger.info(f"Transferred assigned influencer {assigned_influencer_id} to new agent")
            return assigned_influencer
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error transferring assigned influencer {assigned_influencer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error transferring assigned influencer"
            )
    
    @staticmethod
    async def delete_assigned_influencer(
        assigned_influencer_id: uuid.UUID,
        db: Session
    ) -> None:
        """Delete an assigned influencer (soft delete by archiving)"""
        try:
            assigned_influencer = await AssignedInfluencerService.get_assigned_influencer_by_id(
                assigned_influencer_id, db, include_relations=False
            )
            
            # Soft delete by archiving
            assigned_influencer.type = "archived"
            assigned_influencer.archived_at = datetime.utcnow()
            
            db.commit()
            
            # Update agent assignment counts
            await AssignedInfluencerService._update_agent_assignment_counts(
                assigned_influencer.agent_assignment_id, db
            )
            
            logger.info(f"Archived assigned influencer {assigned_influencer_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error archiving assigned influencer {assigned_influencer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error archiving assigned influencer"
            )
    
    @staticmethod
    async def get_assigned_influencer_stats(
        db: Session,
        agent_assignment_id: Optional[uuid.UUID] = None,
        campaign_list_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Get statistics for assigned influencers"""
        try:
            query = db.query(AssignedInfluencer)
            
            # Apply filters
            if agent_assignment_id:
                query = query.filter(AssignedInfluencer.agent_assignment_id == agent_assignment_id)
            
            if campaign_list_id:
                query = query.join(CampaignInfluencer).filter(
                    CampaignInfluencer.campaign_list_id == campaign_list_id
                )
            
            # Get basic counts
            total_assigned = query.count()
            
            # Get counts by status
            status_counts = db.query(
                Status.name,
                func.count(AssignedInfluencer.id)
            ).join(
                AssignedInfluencer, Status.id == AssignedInfluencer.status_id
            ).group_by(Status.name).all()
            
            by_status = {name: count for name, count in status_counts}
            
            # Get counts by type
            type_counts = query.with_entities(
                AssignedInfluencer.type,
                func.count(AssignedInfluencer.id)
            ).group_by(AssignedInfluencer.type).all()
            
            by_type = {type_name: count for type_name, count in type_counts}
            
            # Get counts by agent
            agent_counts = query.join(AgentAssignment).with_entities(
                AgentAssignment.outreach_agent_id,
                func.count(AssignedInfluencer.id)
            ).group_by(AgentAssignment.outreach_agent_id).all()
            
            by_agent = {str(agent_id): count for agent_id, count in agent_counts}
            
            # Calculate averages
            avg_attempts = db.query(func.avg(AssignedInfluencer.attempts_made)).scalar() or 0
            
            # Calculate response rate
            responded_count = query.filter(AssignedInfluencer.responded_at.isnot(None)).count()
            response_rate = (responded_count / total_assigned * 100) if total_assigned > 0 else 0
            
            # Calculate completion rate
            completed_status = db.query(Status).filter(
                and_(Status.model == "assigned_influencer", Status.name == "completed")
            ).first()
            
            completion_rate = 0
            if completed_status:
                completed_count = query.filter(AssignedInfluencer.status_id == completed_status.id).count()
                completion_rate = (completed_count / total_assigned * 100) if total_assigned > 0 else 0
            
            return {
                "total_assigned": total_assigned,
                "by_status": by_status,
                "by_type": by_type,
                "by_agent": by_agent,
                "avg_attempts": round(avg_attempts, 2),
                "response_rate": round(response_rate, 2),
                "completion_rate": round(completion_rate, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting assigned influencer stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving statistics"
            )
    
    @staticmethod
    async def _update_agent_assignment_counts(
        agent_assignment_id: uuid.UUID,
        db: Session
    ) -> None:
        """Update counts for an agent assignment"""
        try:
            agent_assignment = db.query(AgentAssignment).filter(
                AgentAssignment.id == agent_assignment_id
            ).first()
            
            if not agent_assignment:
                return
            
            # Count active assigned influencers
            assigned_count = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.agent_assignment_id == agent_assignment_id,
                    AssignedInfluencer.type == "active"
                )
            ).count()
            
            # Count completed influencers
            completed_status = db.query(Status).filter(
                and_(Status.model == "assigned_influencer", Status.name == "completed")
            ).first()
            
            completed_count = 0
            if completed_status:
                completed_count = db.query(AssignedInfluencer).filter(
                    and_(
                        AssignedInfluencer.agent_assignment_id == agent_assignment_id,
                        AssignedInfluencer.status_id == completed_status.id,
                        AssignedInfluencer.type == "active"
                    )
                ).count()
            
            # Count pending influencers (assigned but not completed)
            pending_count = assigned_count - completed_count
            
            # Update the agent assignment
            agent_assignment.assigned_influencers_count = assigned_count
            agent_assignment.completed_influencers_count = completed_count
            agent_assignment.pending_influencers_count = pending_count
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating agent assignment counts: {str(e)}")
            # Don't raise here as this is a helper function

    @staticmethod
    async def get_outreach_history_for_assigned_influencer(
        assigned_influencer_id: uuid.UUID,
        db: Session
    ) -> List[InfluencerOutreach]:
        """Get outreach history for an assigned influencer"""
        try:
            outreach_records = db.query(InfluencerOutreach).filter(
                InfluencerOutreach.assigned_influencer_id == assigned_influencer_id
            ).order_by(InfluencerOutreach.created_at.desc()).all()
            
            return outreach_records
            
        except Exception as e:
            logger.error(f"Error fetching outreach history for assigned influencer {assigned_influencer_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching outreach history"
            )
        
    
    @staticmethod
    async def record_contact_attempt(
        assigned_influencer_id: uuid.UUID,
        contact_data: Optional[Dict[str, Any]],
        db: Session
    ) -> Dict[str, Any]:
        """
        Record a contact attempt and calculate next contact time based on templates
        """
        try:
            # Get assigned influencer with relationships
            assigned_influencer = await AssignedInfluencerService.get_assigned_influencer_by_id(
                assigned_influencer_id, db, include_relations=True
            )
            
            # Get campaign list through campaign influencer
            campaign_influencer = assigned_influencer.campaign_influencer
            campaign_list_id = campaign_influencer.campaign_list_id
            
            # Current attempt number (will be incremented)
            current_attempts = assigned_influencer.attempts_made
            next_attempt_number = current_attempts + 1
            
            # FIXED: Use timezone-aware datetime for consistency
            # Use the same timezone as your last_contacted_at field
            now = datetime.now(timezone.utc)  # or use your local timezone
            
            # Update contact info for assigned influencer
            assigned_influencer.attempts_made = next_attempt_number
            assigned_influencer.last_contacted_at = now
            
            # Update total_contact_attempts in campaign_influencers table
            campaign_influencer.total_contact_attempts = (campaign_influencer.total_contact_attempts or 0) + 1
            
            # ===== ADD THIS SECTION - UPDATE STATUSES FOR FIRST CONTACT =====
            status_updates = AssignedInfluencerService.update_statuses_for_contact_attempt(
                assigned_influencer, campaign_influencer, next_attempt_number, db
            )
            # ===== END OF ADDED SECTION =====
            
            # Add notes if provided
            if contact_data and contact_data.get('notes'):
                existing_notes = assigned_influencer.notes or ""
                new_note = f"[{now.strftime('%Y-%m-%d %H:%M')}] {contact_data['notes']}"
                assigned_influencer.notes = f"{existing_notes}\n{new_note}".strip()
            
            # Calculate next contact time based on message templates
            next_contact_info = await AssignedInfluencerService._calculate_next_contact_time(
                campaign_list_id, next_attempt_number, contact_data, now, db  # Pass current time
            )
            
            if next_contact_info['next_contact_at']:
                assigned_influencer.next_contact_at = next_contact_info['next_contact_at']
            
            db.commit()
            db.refresh(assigned_influencer)
            
            return {
                "success": True,
                "message": f"Contact attempt {next_attempt_number} recorded successfully",
                "assigned_influencer": assigned_influencer,
                "next_template_info": next_contact_info['template_info'],
                "status_updates": status_updates  # ADD THIS LINE
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error recording contact attempt: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error recording contact attempt: {str(e)}"
            )

    @staticmethod
    async def _calculate_next_contact_time(
        campaign_list_id: uuid.UUID,
        attempt_number: int,
        contact_data: Optional[Dict[str, Any]],
        current_time: datetime,  # NEW: Accept current time as parameter
        db: Session
    ) -> Dict[str, Any]:
        """
        Calculate next contact time based on message template sequence
        """
        try:
            # Check for custom override first
            if contact_data and contact_data.get('custom_next_contact_hours'):
                hours_delay = contact_data['custom_next_contact_hours']
                next_contact_at = current_time + timedelta(hours=hours_delay)
                return {
                    "next_contact_at": next_contact_at,
                    "template_info": {
                        "type": "custom_override",
                        "hours_delay": hours_delay,
                        "message": f"Custom delay of {hours_delay} hours applied",
                        "calculation_base_time": current_time.isoformat()
                    }
                }
            
            # Get campaign list to find the campaign_id
            campaign_list = db.query(CampaignList).filter(
                CampaignList.id == campaign_list_id
            ).first()
            
            if not campaign_list:
                return {
                    "next_contact_at": None,
                    "template_info": {
                        "type": "campaign_list_not_found",
                        "message": f"Campaign list {campaign_list_id} not found"
                    }
                }
            
            # Find initial template using campaign_id
            campaign_id = campaign_list.campaign_id
            
            initial_template = db.query(MessageTemplate).filter(
                MessageTemplate.campaign_id == campaign_id,
                MessageTemplate.template_type == 'initial',
                MessageTemplate.is_deleted == False
            ).first()
            
            if not initial_template:
                return {
                    "next_contact_at": None,
                    "template_info": {
                        "type": "no_initial_template",
                        "message": f"No initial template found for campaign {campaign_id}"
                    }
                }
            
            # Use attempt_number directly as followup_sequence
            followup_sequence = attempt_number
            
            # Find the corresponding follow-up template
            followup_template = db.query(MessageTemplate).filter(
                MessageTemplate.parent_template_id == initial_template.id,
                MessageTemplate.followup_sequence == followup_sequence,
                MessageTemplate.template_type == 'followup',
                MessageTemplate.is_deleted == False
            ).first()
            
            if not followup_template:
                all_followups = db.query(MessageTemplate).filter(
                    MessageTemplate.parent_template_id == initial_template.id,
                    MessageTemplate.template_type == 'followup',
                    MessageTemplate.is_deleted == False
                ).all()
                
                return {
                    "next_contact_at": None,
                    "template_info": {
                        "type": "no_followup_template",
                        "message": f"No follow-up template found for sequence {followup_sequence}",
                        "available_sequences": [ft.followup_sequence for ft in all_followups],
                        "requested_sequence": followup_sequence
                    }
                }
            
            # Calculate next contact time using followup_delay_hours
            delay_hours = followup_template.followup_delay_hours
            if delay_hours is None or delay_hours <= 0:
                delay_hours = 24
            
            # FIXED: Use the passed current_time instead of datetime.utcnow()
            next_contact_at = current_time + timedelta(hours=delay_hours)
            
            return {
                "next_contact_at": next_contact_at,
                "template_info": {
                    "type": "followup_scheduled",
                    "template_id": str(followup_template.id),
                    "followup_sequence": followup_sequence,
                    "delay_hours": delay_hours,
                    "subject": followup_template.subject,
                    "calculation_base_time": current_time.isoformat(),
                    "next_contact_at": next_contact_at.isoformat(),
                    "actual_hours_added": delay_hours,
                    "message": f"Next contact scheduled in {delay_hours} hours using follow-up template sequence {followup_sequence}"
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating next contact time: {str(e)}", exc_info=True)
            return {
                "next_contact_at": None,
                "template_info": {
                    "type": "calculation_error",
                    "message": f"Error calculating next contact time: {str(e)}"
                }
            }


    # Helper method for status management (MOVED TO SERVICE)
    @staticmethod
    def get_status_id(db: Session, model: str, name: str) -> Optional[uuid.UUID]:
        """
        Get status ID by model and name
        
        Args:
            db: Database session
            model: Status model (e.g., 'assigned_influencer', 'campaign_influencer')
            name: Status name (e.g., 'awaiting_response', 'contacted')
        
        Returns:
            UUID: Status ID if found, None otherwise
        """
        try:
            status = db.query(Status).filter(
                Status.model == model,
                Status.name == name
            ).first()
            return status.id if status else None
        except Exception as e:
            logger.error(f"Error getting status ID for {model}.{name}: {str(e)}")
            return None

    @staticmethod
    def update_statuses_for_contact_attempt(
        assigned_influencer: AssignedInfluencer,
        campaign_influencer: CampaignInfluencer,
        attempt_number: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Update statuses based on contact attempt number
        
        Args:
            assigned_influencer: AssignedInfluencer object
            campaign_influencer: CampaignInfluencer object  
            attempt_number: Current attempt number
            db: Database session
            
        Returns:
            Dict with status update information
        """
        status_updates = {
            "assigned_influencer_status_updated": False,
            "campaign_influencer_status_updated": False,
            "details": []
        }
        
        try:
            if attempt_number == 1:  # First contact
                # Update assigned_influencer to 'awaiting_response'
                awaiting_response_id = AssignedInfluencerService.get_status_id(
                    db, "assigned_influencer", "awaiting_response"
                )
                if awaiting_response_id:
                    old_status_id = assigned_influencer.status_id
                    assigned_influencer.status_id = awaiting_response_id
                    status_updates["assigned_influencer_status_updated"] = True
                    status_updates["details"].append(f"assigned_influencer: {old_status_id} → {awaiting_response_id} (awaiting_response)")
                    logger.info(f"Updated assigned_influencer {assigned_influencer.id} status to 'awaiting_response'")
                
                # Update campaign_influencer to 'contacted'
                contacted_id = AssignedInfluencerService.get_status_id(
                    db, "campaign_influencer", "contacted"
                )
                if contacted_id:
                    old_status_id = campaign_influencer.status_id
                    campaign_influencer.status_id = contacted_id
                    status_updates["campaign_influencer_status_updated"] = True
                    status_updates["details"].append(f"campaign_influencer: {old_status_id} → {contacted_id} (contacted)")
                    logger.info(f"Updated campaign_influencer {campaign_influencer.id} status to 'contacted'")
            
            # Future: Add logic for other attempt numbers if needed
            elif attempt_number >= 3:  # Max attempts reached
                max_attempts_id = AssignedInfluencerService.get_status_id(
                    db, "assigned_influencer", "max_attempts_reached"
                )
                if max_attempts_id:
                    assigned_influencer.status_id = max_attempts_id
            
            return status_updates
            
        except Exception as e:
            logger.error(f"Error updating statuses for attempt {attempt_number}: {str(e)}")
            return {
                "assigned_influencer_status_updated": False,
                "campaign_influencer_status_updated": False,
                "error": str(e)
            }       

    # ALTERNATIVE: If you want to use Pakistan timezone specifically
    # @staticmethod
    # async def _calculate_next_contact_time_with_local_timezone(
    #     campaign_list_id: uuid.UUID,
    #     attempt_number: int,
    #     contact_data: Optional[Dict[str, Any]],
    #     db: Session
    # ) -> Dict[str, Any]:
    #     """Version that explicitly uses Pakistan timezone"""
    #     try:
    #         # Set Pakistan timezone
    #         pakistan_tz = pytz.timezone('Asia/Karachi')  # +05:00
    #         current_time = datetime.now(pakistan_tz)
            
    #         # ... rest of the logic same as above but using pakistan timezone
            
    #         # Calculate next contact time
    #         delay_hours = followup_template.followup_delay_hours or 24
    #         next_contact_at = current_time + timedelta(hours=delay_hours)
            
    #         return {
    #             "next_contact_at": next_contact_at,
    #             "template_info": {
    #                 "type": "followup_scheduled",
    #                 "timezone": "Asia/Karachi",
    #                 "current_time_local": current_time.isoformat(),
    #                 "delay_hours": delay_hours,
    #                 "next_contact_at_local": next_contact_at.isoformat()
    #             }
    #         }
    #     except Exception as e:
    #         # ... error handling
    #         pass