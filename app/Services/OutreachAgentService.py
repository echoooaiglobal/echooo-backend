# app/Services/OutreachAgentService.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
import uuid
from datetime import datetime
from app.Models.outreach_agents import OutreachAgent
from app.Models.agent_assignments import AgentAssignment
from app.Models.agent_social_connections import AgentSocialConnection
from app.Models.auth_models import User
from app.Models.statuses import Status
from app.Utils.Logger import logger
from app.Models.influencer_outreach import InfluencerOutreach

class OutreachAgentService:
    """Service for managing outreach agents"""

    @staticmethod
    async def get_all_agents(db: Session, include_deleted: bool = False):
        """
        Get all outreach agents with relationships
        """
        query = db.query(OutreachAgent).options(
            joinedload(OutreachAgent.assigned_user),
            joinedload(OutreachAgent.status),
            joinedload(OutreachAgent.social_connections),
            joinedload(OutreachAgent.agent_assignments)
        )
        
        if not include_deleted:
            query = query.filter(OutreachAgent.deleted_at.is_(None))
            
        return query.all()
    
    @staticmethod
    async def get_agents_paginated(
        page: int = 1, 
        page_size: int = 10,
        status_filter: Optional[str] = None,
        availability_filter: Optional[bool] = None,
        automation_filter: Optional[bool] = None,
        db: Session = None
    ) -> Tuple[List, int]:
        """
        Get paginated outreach agents with filters
        """
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query with filters
        query = db.query(OutreachAgent).options(
            joinedload(OutreachAgent.assigned_user),
            joinedload(OutreachAgent.status),
            joinedload(OutreachAgent.social_connections),
            joinedload(OutreachAgent.agent_assignments)
        ).filter(OutreachAgent.deleted_at.is_(None))
        
        # Apply filters
        if status_filter:
            status = db.query(Status).filter(
                Status.model == "outreach_agent",
                Status.name == status_filter
            ).first()
            if status:
                query = query.filter(OutreachAgent.status_id == status.id)
        
        if availability_filter is not None:
            query = query.filter(OutreachAgent.is_available_for_assignment == availability_filter)
        
        if automation_filter is not None:
            query = query.filter(OutreachAgent.is_automation_enabled == automation_filter)
        
        # Get total count
        total_count = query.count()
        
        # Get paginated agents
        agents = query.offset(offset).limit(page_size).all()
        
        return agents, total_count
    
    @staticmethod
    async def get_agent_by_id(agent_id: uuid.UUID, db: Session):
        """
        Get an outreach agent by ID with all relationships
        """
        agent = db.query(OutreachAgent).options(
            joinedload(OutreachAgent.assigned_user),
            joinedload(OutreachAgent.status),
            joinedload(OutreachAgent.social_connections),
            joinedload(OutreachAgent.agent_assignments),
            joinedload(OutreachAgent.automation_sessions)
        ).filter(
            OutreachAgent.id == agent_id,
            OutreachAgent.deleted_at.is_(None)
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Outreach agent not found"
            )
            
        return agent

    @staticmethod
    async def get_agents_by_user(user_id: uuid.UUID, db: Session):
        """
        Get all outreach agents assigned to a specific user
        """
        return db.query(OutreachAgent).options(
            joinedload(OutreachAgent.assigned_user),
            joinedload(OutreachAgent.status),
            joinedload(OutreachAgent.social_connections),
            joinedload(OutreachAgent.agent_assignments)
        ).filter(
            OutreachAgent.assigned_user_id == user_id,
            OutreachAgent.deleted_at.is_(None)
        ).all()

    @staticmethod
    async def create_agent(agent_data: Dict[str, Any], db: Session):
        """
        Create a new outreach agent
        """
        try:
            # Verify assigned user exists
            user = db.query(User).filter(User.id == uuid.UUID(agent_data['assigned_user_id'])).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned user not found"
                )
            
            # Get default status if not provided
            if not agent_data.get('status_id'):
                default_status = db.query(Status).filter(
                    Status.model == "outreach_agent",
                    Status.name == "active"
                ).first()
                
                if default_status:
                    agent_data['status_id'] = str(default_status.id)
            
            # Create outreach agent
            agent = OutreachAgent(**agent_data)
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            # Reload with relationships
            return db.query(OutreachAgent).options(
                joinedload(OutreachAgent.assigned_user),
                joinedload(OutreachAgent.status),
                joinedload(OutreachAgent.social_connections),
                joinedload(OutreachAgent.agent_assignments)
            ).filter(OutreachAgent.id == agent.id).first()
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating outreach agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating outreach agent"
            ) from e

    @staticmethod
    async def update_agent(
        agent_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update an outreach agent
        """
        try:
            agent = db.query(OutreachAgent).filter(
                OutreachAgent.id == agent_id,
                OutreachAgent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Outreach agent not found"
                )
            
            # Verify assigned user exists if being updated
            if 'assigned_user_id' in update_data:
                user = db.query(User).filter(User.id == uuid.UUID(update_data['assigned_user_id'])).first()
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Assigned user not found"
                    )
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(agent, field) and value is not None:
                    setattr(agent, field, value)
            
            # Update last activity when agent becomes available
            if update_data.get('is_available_for_assignment'):
                agent.last_activity_at = datetime.utcnow()
            
            db.commit()
            db.refresh(agent)
            
            # Reload with relationships
            return db.query(OutreachAgent).options(
                joinedload(OutreachAgent.assigned_user),
                joinedload(OutreachAgent.status),
                joinedload(OutreachAgent.social_connections),
                joinedload(OutreachAgent.agent_assignments)
            ).filter(OutreachAgent.id == agent.id).first()
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating outreach agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating outreach agent"
            ) from e

    @staticmethod
    async def delete_agent(agent_id: uuid.UUID, db: Session):
        """
        Soft delete an outreach agent
        """
        try:
            agent = db.query(OutreachAgent).filter(
                OutreachAgent.id == agent_id,
                OutreachAgent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Outreach agent not found"
                )
            
            # Check if agent has active assignments
            active_assignments = db.query(AgentAssignment).filter(
                AgentAssignment.outreach_agent_id == agent_id,
                AgentAssignment.assignment_status == 'active'
            ).count()
            
            if active_assignments > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete agent with active assignments. Please reassign or complete them first."
                )
            
            # Soft delete
            agent.deleted_at = datetime.utcnow()
            agent.is_available_for_assignment = False
            
            db.commit()
            
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting outreach agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting outreach agent"
            ) from e

    @staticmethod
    async def update_agent_status(
        agent_id: uuid.UUID,
        status_id: uuid.UUID,
        db: Session
    ):
        """
        Update agent status
        """
        try:
            # Verify status exists and is for outreach_agent
            status_obj = db.query(Status).filter(
                Status.id == status_id,
                Status.model == "outreach_agent"
            ).first()
            
            if not status_obj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status for outreach agent"
                )
            
            agent = db.query(OutreachAgent).filter(
                OutreachAgent.id == agent_id,
                OutreachAgent.deleted_at.is_(None)
            ).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Outreach agent not found"
                )
            
            agent.status_id = status_id
            agent.last_activity_at = datetime.utcnow()
            
            # Update availability based on status
            if status_obj.name in ['inactive', 'suspended', 'maintenance']:
                agent.is_available_for_assignment = False
            elif status_obj.name == 'active':
                agent.is_available_for_assignment = True
            
            db.commit()
            db.refresh(agent)
            
            return agent
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating agent status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating agent status"
            ) from e

    @staticmethod
    async def reset_daily_counters(db: Session):
        """
        Reset daily message counters for all agents (called daily)
        """
        try:
            db.query(OutreachAgent).update({
                OutreachAgent.messages_sent_today: 0
            })
            db.commit()
            
            logger.info("Daily message counters reset for all agents")
            return True
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error resetting daily counters: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error resetting daily counters"
            ) from e

    @staticmethod
    async def get_agent_statistics(db: Session) -> Dict[str, Any]:
        """
        Get overall agent statistics
        """
        try:
            stats = db.query(
                func.count(OutreachAgent.id).label('total_agents'),
                func.sum(func.case([(OutreachAgent.status_id != None, 1)], else_=0)).label('active_agents'),
                func.sum(func.case([(OutreachAgent.is_available_for_assignment == True, 1)], else_=0)).label('available_agents'),
                func.sum(func.case([(OutreachAgent.is_automation_enabled == True, 1)], else_=0)).label('automation_enabled_agents'),
                func.sum(OutreachAgent.messages_sent_today).label('total_messages_today'),
                func.sum(OutreachAgent.active_lists_count).label('total_active_lists'),
                func.sum(OutreachAgent.active_influencers_count).label('total_active_influencers')
            ).filter(OutreachAgent.deleted_at.is_(None)).first()
            
            return {
                'total_agents': stats.total_agents or 0,
                'active_agents': stats.active_agents or 0,
                'available_agents': stats.available_agents or 0,
                'automation_enabled_agents': stats.automation_enabled_agents or 0,
                'total_messages_today': stats.total_messages_today or 0,
                'total_active_lists': stats.total_active_lists or 0,
                'total_active_influencers': stats.total_active_influencers or 0
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting agent statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error getting agent statistics"
            ) from e

    @staticmethod
    async def get_available_agents_for_assignment(
        platform_id: Optional[uuid.UUID] = None,
        db: Session = None
    ) -> List[OutreachAgent]:
        """
        Get agents available for new assignments, optionally filtered by platform
        """
        query = db.query(OutreachAgent).options(
            joinedload(OutreachAgent.assigned_user),
            joinedload(OutreachAgent.status),
            joinedload(OutreachAgent.social_connections)
        ).filter(
            OutreachAgent.is_available_for_assignment == True,
            OutreachAgent.deleted_at.is_(None)
        )
        
        # Filter by platform if specified
        if platform_id:
            query = query.join(OutreachAgent.social_connections).filter(
                AgentSocialConnection.platform_id == platform_id,
                AgentSocialConnection.is_active == True
            )
        
        # Order by workload (fewer active lists first)
        query = query.order_by(OutreachAgent.active_lists_count.asc())
        
        return query.all()

    @staticmethod
    async def increment_message_count(agent_id: uuid.UUID, db: Session):
        """
        Increment the daily message count for an agent
        """
        try:
            agent = db.query(OutreachAgent).filter(OutreachAgent.id == agent_id).first()
            if agent:
                agent.messages_sent_today += 1
                agent.last_activity_at = datetime.utcnow()
                db.commit()
                
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error incrementing message count for agent {agent_id}: {str(e)}")

    @staticmethod
    async def update_agent_workload(
        agent_id: uuid.UUID,
        lists_delta: int = 0,
        influencers_delta: int = 0,
        db: Session = None
    ):
        """
        Update agent's workload counters
        """
        try:
            agent = db.query(OutreachAgent).filter(OutreachAgent.id == agent_id).first()
            if agent:
                agent.active_lists_count = max(0, agent.active_lists_count + lists_delta)
                agent.active_influencers_count = max(0, agent.active_influencers_count + influencers_delta)
                agent.last_activity_at = datetime.utcnow()
                db.commit()
                
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating agent workload for agent {agent_id}: {str(e)}")


    # Static methods for outreach records related to agents
    @staticmethod
    async def get_agent_outreach_records(
        outreach_agent_id: uuid.UUID,
        page: int = 1,
        size: int = 50,
        db: Session = None
    ) -> Tuple[List[InfluencerOutreach], int]:
        """Get outreach records for a specific agent"""
        try:
            from app.Services.InfluencerOutreachService import InfluencerOutreachService
            
            return await InfluencerOutreachService.get_outreach_records_paginated(
                page=page,
                size=size,
                outreach_agent_id=outreach_agent_id,
                include_relations=True,
                db=db
            )
            
        except Exception as e:
            logger.error(f"Error fetching outreach records for agent {outreach_agent_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching agent outreach records"
            )
    
    @staticmethod
    async def get_agent_performance_stats(
        outreach_agent_id: uuid.UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get performance statistics for an agent"""
        try:
            from app.Services.InfluencerOutreachService import InfluencerOutreachService
            
            stats = await InfluencerOutreachService.get_outreach_statistics(
                outreach_agent_id=outreach_agent_id,
                date_from=date_from,
                date_to=date_to,
                db=db
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching performance stats for agent {outreach_agent_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching agent performance statistics"
            )