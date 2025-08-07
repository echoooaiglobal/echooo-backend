# app/Services/InfluencerAssignmentHistoryService.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, asc, extract
from typing import List, Dict, Any, Optional, Tuple
import uuid
from datetime import datetime

from app.Models.influencer_assignment_histories import InfluencerAssignmentHistory
from app.Models.reassignment_reasons import ReassignmentReason
from app.Models.campaign_influencers import CampaignInfluencer
from app.Models.agent_assignments import AgentAssignment
from app.Models.outreach_agents import OutreachAgent
from app.Models.auth_models import User
from app.Utils.Logger import logger

class InfluencerAssignmentHistoryService:
    """Service for managing influencer assignment history"""
    
    @staticmethod
    async def create_assignment_history(
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerAssignmentHistory:
        """Create a new assignment history record"""
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
            
            # Validate reassignment reason exists
            reason = db.query(ReassignmentReason).filter(
                ReassignmentReason.id == data["reassignment_reason_id"]
            ).first()
            
            if not reason:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reassignment reason not found"
                )
            
            # Validate agents exist
            if data.get("from_outreach_agent_id"):
                from_agent = db.query(OutreachAgent).filter(
                    OutreachAgent.id == data["from_outreach_agent_id"]
                ).first()
                
                if not from_agent:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="From agent not found"
                    )
            
            to_agent = db.query(OutreachAgent).filter(
                OutreachAgent.id == data["to_outreach_agent_id"]
            ).first()
            
            if not to_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="To agent not found"
                )
            
            # Validate user if provided
            if data.get("reassigned_by"):
                user = db.query(User).filter(
                    User.id == data["reassigned_by"]
                ).first()
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Reassigning user not found"
                    )
            
            # Create assignment history
            history = InfluencerAssignmentHistory(**data)
            db.add(history)
            db.commit()
            db.refresh(history)
            
            logger.info(f"Created assignment history {history.id}")
            return history
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating assignment history: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating assignment history"
            )
    
    @staticmethod
    async def get_assignment_history_by_id(
        history_id: uuid.UUID,
        db: Session,
        include_relations: bool = True
    ) -> InfluencerAssignmentHistory:
        """Get assignment history by ID"""
        try:
            query = db.query(InfluencerAssignmentHistory).filter(
                InfluencerAssignmentHistory.id == history_id
            )
            
            if include_relations:
                query = query.options(
                    joinedload(InfluencerAssignmentHistory.campaign_influencer),
                    joinedload(InfluencerAssignmentHistory.agent_assignment),
                    joinedload(InfluencerAssignmentHistory.reassignment_reason),
                    joinedload(InfluencerAssignmentHistory.from_agent),
                    joinedload(InfluencerAssignmentHistory.to_agent),
                    joinedload(InfluencerAssignmentHistory.reassigned_by_user)
                )
            
            history = query.first()
            
            if not history:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment history not found"
                )
            
            return history
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting assignment history {history_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assignment history"
            )
    
    @staticmethod
    async def get_assignment_histories(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        campaign_influencer_id: Optional[uuid.UUID] = None,
        agent_assignment_id: Optional[uuid.UUID] = None,
        from_agent_id: Optional[uuid.UUID] = None,
        to_agent_id: Optional[uuid.UUID] = None,
        reassignment_reason_id: Optional[uuid.UUID] = None,
        triggered_by: Optional[str] = None,
        reassigned_by: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_relations: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[InfluencerAssignmentHistory], int]:
        """Get assignment histories with filtering and pagination"""
        try:
            query = db.query(InfluencerAssignmentHistory)
            
            # Apply filters
            if campaign_influencer_id:
                query = query.filter(
                    InfluencerAssignmentHistory.campaign_influencer_id == campaign_influencer_id
                )
            
            if agent_assignment_id:
                query = query.filter(
                    InfluencerAssignmentHistory.agent_assignment_id == agent_assignment_id
                )
            
            if from_agent_id:
                query = query.filter(
                    InfluencerAssignmentHistory.from_outreach_agent_id == from_agent_id
                )
            
            if to_agent_id:
                query = query.filter(
                    InfluencerAssignmentHistory.to_outreach_agent_id == to_agent_id
                )
            
            if reassignment_reason_id:
                query = query.filter(
                    InfluencerAssignmentHistory.reassignment_reason_id == reassignment_reason_id
                )
            
            if triggered_by:
                query = query.filter(
                    InfluencerAssignmentHistory.reassignment_triggered_by == triggered_by
                )
            
            if reassigned_by:
                query = query.filter(
                    InfluencerAssignmentHistory.reassigned_by == reassigned_by
                )
            
            if start_date:
                query = query.filter(
                    InfluencerAssignmentHistory.created_at >= start_date
                )
            
            if end_date:
                query = query.filter(
                    InfluencerAssignmentHistory.created_at <= end_date
                )
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            if sort_order.lower() == "desc":
                query = query.order_by(desc(getattr(InfluencerAssignmentHistory, sort_by)))
            else:
                query = query.order_by(asc(getattr(InfluencerAssignmentHistory, sort_by)))
            
            # Include relations if requested
            if include_relations:
                query = query.options(
                    joinedload(InfluencerAssignmentHistory.campaign_influencer),
                    joinedload(InfluencerAssignmentHistory.agent_assignment),
                    joinedload(InfluencerAssignmentHistory.reassignment_reason),
                    joinedload(InfluencerAssignmentHistory.from_agent),
                    joinedload(InfluencerAssignmentHistory.to_agent),
                    joinedload(InfluencerAssignmentHistory.reassigned_by_user)
                )
            
            # Apply pagination
            histories = query.offset(skip).limit(limit).all()
            
            return histories, total
            
        except Exception as e:
            logger.error(f"Error getting assignment histories: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving assignment histories"
            )
    
    @staticmethod
    async def update_assignment_history(
        history_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerAssignmentHistory:
        """Update assignment history (limited fields)"""
        try:
            history = await InfluencerAssignmentHistoryService.get_assignment_history_by_id(
                history_id, db, include_relations=False
            )
            
            # Only allow updating certain fields
            allowed_fields = ['reassignment_notes', 'previous_assignment_data']
            
            for field, value in data.items():
                if field in allowed_fields and hasattr(history, field):
                    setattr(history, field, value)
            
            db.commit()
            db.refresh(history)
            
            logger.info(f"Updated assignment history {history_id}")
            return history
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating assignment history {history_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating assignment history"
            )
    
    @staticmethod
    async def bulk_create_assignment_histories(
        histories_data: List[Dict[str, Any]],
        db: Session
    ) -> List[InfluencerAssignmentHistory]:
        """Bulk create assignment history records"""
        try:
            created_histories = []
            
            for data in histories_data:
                try:
                    history = InfluencerAssignmentHistory(**data)
                    db.add(history)
                    created_histories.append(history)
                except Exception as e:
                    logger.error(f"Error creating individual history record: {str(e)}")
                    # Continue with other records
                    continue
            
            db.commit()
            
            # Refresh all created histories
            for history in created_histories:
                db.refresh(history)
            
            logger.info(f"Bulk created {len(created_histories)} assignment histories")
            return created_histories
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk creating assignment histories: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error bulk creating assignment histories"
            )
    
    @staticmethod
    async def get_assignment_history_stats(
        db: Session,
        campaign_influencer_id: Optional[uuid.UUID] = None,
        agent_assignment_id: Optional[uuid.UUID] = None,
        from_agent_id: Optional[uuid.UUID] = None,
        to_agent_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get statistics for assignment histories"""
        try:
            query = db.query(InfluencerAssignmentHistory)
            
            # Apply filters
            if campaign_influencer_id:
                query = query.filter(
                    InfluencerAssignmentHistory.campaign_influencer_id == campaign_influencer_id
                )
            
            if agent_assignment_id:
                query = query.filter(
                    InfluencerAssignmentHistory.agent_assignment_id == agent_assignment_id
                )
            
            if from_agent_id:
                query = query.filter(
                    InfluencerAssignmentHistory.from_outreach_agent_id == from_agent_id
                )
            
            if to_agent_id:
                query = query.filter(
                    InfluencerAssignmentHistory.to_outreach_agent_id == to_agent_id
                )
            
            if start_date:
                query = query.filter(
                    InfluencerAssignmentHistory.created_at >= start_date
                )
            
            if end_date:
                query = query.filter(
                    InfluencerAssignmentHistory.created_at <= end_date
                )
            
            # Total reassignments
            total_reassignments = query.count()
            
            # By trigger type
            trigger_stats = query.with_entities(
                InfluencerAssignmentHistory.reassignment_triggered_by,
                func.count(InfluencerAssignmentHistory.id).label('count')
            ).group_by(InfluencerAssignmentHistory.reassignment_triggered_by).all()
            
            by_trigger = {stat.reassignment_triggered_by: stat.count for stat in trigger_stats}
            
            # By reason
            reason_stats = db.query(
                ReassignmentReason.name,
                func.count(InfluencerAssignmentHistory.id).label('count')
            ).join(
                InfluencerAssignmentHistory,
                ReassignmentReason.id == InfluencerAssignmentHistory.reassignment_reason_id
            )
            
            # Apply same filters to reason stats
            if campaign_influencer_id:
                reason_stats = reason_stats.filter(
                    InfluencerAssignmentHistory.campaign_influencer_id == campaign_influencer_id
                )
            
            reason_stats = reason_stats.group_by(ReassignmentReason.name).all()
            by_reason = {stat.name: stat.count for stat in reason_stats}
            
            # Average attempts before reassignment
            avg_attempts = query.with_entities(
                func.avg(InfluencerAssignmentHistory.attempts_before_reassignment)
            ).scalar() or 0.0
            
            # Most common reasons (top 5)
            most_common_reasons = db.query(
                ReassignmentReason.name,
                ReassignmentReason.code,
                func.count(InfluencerAssignmentHistory.id).label('count')
            ).join(
                InfluencerAssignmentHistory,
                ReassignmentReason.id == InfluencerAssignmentHistory.reassignment_reason_id
            ).group_by(
                ReassignmentReason.name, ReassignmentReason.code
            ).order_by(
                desc(func.count(InfluencerAssignmentHistory.id))
            ).limit(5).all()
            
            most_common_list = [
                {
                    "reason_name": reason.name,
                    "reason_code": reason.code,
                    "count": reason.count
                }
                for reason in most_common_reasons
            ]
            
            # Reassignments by month (last 12 months)
            monthly_stats = query.with_entities(
                extract('year', InfluencerAssignmentHistory.created_at).label('year'),
                extract('month', InfluencerAssignmentHistory.created_at).label('month'),
                func.count(InfluencerAssignmentHistory.id).label('count')
            ).group_by(
                extract('year', InfluencerAssignmentHistory.created_at),
                extract('month', InfluencerAssignmentHistory.created_at)
            ).order_by(
                extract('year', InfluencerAssignmentHistory.created_at),
                extract('month', InfluencerAssignmentHistory.created_at)
            ).all()
            
            reassignments_by_month = [
                {
                    "year": int(stat.year),
                    "month": int(stat.month),
                    "count": stat.count
                }
                for stat in monthly_stats
            ]
            
            # By agent (agents who received reassignments)
            agent_stats = query.with_entities(
                InfluencerAssignmentHistory.to_outreach_agent_id,
                func.count(InfluencerAssignmentHistory.id).label('count')
            ).group_by(InfluencerAssignmentHistory.to_outreach_agent_id).all()
            
            by_agent = {str(stat.to_outreach_agent_id): stat.count for stat in agent_stats}
            
            return {
                "total_reassignments": total_reassignments,
                "by_trigger": by_trigger,
                "by_reason": by_reason,
                "by_agent": by_agent,
                "avg_attempts_before_reassignment": round(avg_attempts, 2),
                "most_common_reasons": most_common_list,
                "reassignments_by_month": reassignments_by_month
            }
            
        except Exception as e:
            logger.error(f"Error getting assignment history stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving statistics"
            )

class ReassignmentReasonService:
    """Service for managing reassignment reasons"""
    
    @staticmethod
    async def get_all_reasons(
        db: Session,
        active_only: bool = True,
        triggered_by: Optional[str] = None
    ) -> List[ReassignmentReason]:
        """Get all reassignment reasons"""
        try:
            query = db.query(ReassignmentReason)
            
            if active_only:
                query = query.filter(ReassignmentReason.is_active == True)
            
            if triggered_by == "system":
                query = query.filter(ReassignmentReason.is_system_triggered == True)
            elif triggered_by == "user":
                query = query.filter(ReassignmentReason.is_user_triggered == True)
            
            return query.order_by(ReassignmentReason.display_order).all()
            
        except Exception as e:
            logger.error(f"Error getting reassignment reasons: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving reassignment reasons"
            )
    
    @staticmethod
    async def get_reason_by_id(
        reason_id: uuid.UUID,
        db: Session
    ) -> ReassignmentReason:
        """Get reassignment reason by ID"""
        try:
            reason = db.query(ReassignmentReason).filter(
                ReassignmentReason.id == reason_id
            ).first()
            
            if not reason:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reassignment reason not found"
                )
            
            return reason
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting reassignment reason {reason_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving reassignment reason"
            )
    
    @staticmethod
    async def create_reason(
        data: Dict[str, Any],
        db: Session
    ) -> ReassignmentReason:
        """Create a new reassignment reason"""
        try:
            # Check if code already exists
            existing = db.query(ReassignmentReason).filter(
                ReassignmentReason.code == data["code"]
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reassignment reason code already exists"
                )
            
            reason = ReassignmentReason(**data)
            db.add(reason)
            db.commit()
            db.refresh(reason)
            
            logger.info(f"Created reassignment reason {reason.id}")
            return reason
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating reassignment reason: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating reassignment reason"
            )
    
    @staticmethod
    async def update_reason(
        reason_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> ReassignmentReason:
        """Update a reassignment reason"""
        try:
            reason = await ReassignmentReasonService.get_reason_by_id(reason_id, db)
            
            # Check if code is being updated and already exists
            if "code" in data and data["code"] != reason.code:
                existing = db.query(ReassignmentReason).filter(
                    and_(
                        ReassignmentReason.code == data["code"],
                        ReassignmentReason.id != reason_id
                    )
                ).first()
                
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Reassignment reason code already exists"
                    )
            
            # Update fields
            for field, value in data.items():
                if hasattr(reason, field):
                    setattr(reason, field, value)
            
            db.commit()
            db.refresh(reason)
            
            logger.info(f"Updated reassignment reason {reason_id}")
            return reason
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating reassignment reason {reason_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating reassignment reason"
            )
    
    @staticmethod
    async def delete_reason(
        reason_id: uuid.UUID,
        db: Session
    ) -> None:
        """Delete (deactivate) a reassignment reason"""
        try:
            reason = await ReassignmentReasonService.get_reason_by_id(reason_id, db)
            
            # Check if reason is used in any histories
            history_count = db.query(InfluencerAssignmentHistory).filter(
                InfluencerAssignmentHistory.reassignment_reason_id == reason_id
            ).count()
            
            if history_count > 0:
                # Soft delete by deactivating
                reason.is_active = False
                db.commit()
                logger.info(f"Deactivated reassignment reason {reason_id} (used in {history_count} histories)")
            else:
                # Hard delete if not used
                db.delete(reason)
                db.commit()
                logger.info(f"Deleted reassignment reason {reason_id}")
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting reassignment reason {reason_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting reassignment reason"
            )