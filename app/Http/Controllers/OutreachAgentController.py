# app/Http/Controllers/OutreachAgentController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import math
from app.Models.auth_models import User
from app.Schemas.outreach_agent import (
    OutreachAgentCreate, OutreachAgentUpdate, OutreachAgentResponse,
    UserBrief, StatusBrief, AgentSocialConnectionBrief, AgentListAssignmentBrief,
    OutreachAgentsPaginatedResponse, PaginationInfo, AgentStatusUpdate,
    AgentAvailabilityUpdate, AgentAutomationUpdate, AgentStatistics,
    AgentPerformanceMetrics
)

from app.Services.OutreachAgentService import OutreachAgentService
from app.Utils.Logger import logger

class OutreachAgentController:
    """Controller for outreach agent-related endpoints"""
    
    @staticmethod
    async def get_all_agents_paginated(
        page: int = 1, 
        page_size: int = 10,
        status_filter: Optional[str] = None,
        availability_filter: Optional[bool] = None,
        automation_filter: Optional[bool] = None,
        db: Session = None
    ):
        """Get paginated outreach agents with optional filters"""
        try:
            agents, total_count = await OutreachAgentService.get_agents_paginated(
                page, page_size, status_filter, availability_filter, automation_filter, db
            )
            
            # Format the response
            formatted_agents = [
                OutreachAgentController._format_agent_response(agent)
                for agent in agents
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
            
            return OutreachAgentsPaginatedResponse(
                agents=formatted_agents,
                pagination=pagination_info
            )
            
        except Exception as e:
            logger.error(f"Error in get_all_agents_paginated controller: {str(e)}")
            raise

    @staticmethod
    async def get_agent(agent_id: uuid.UUID, db: Session):
        """Get an outreach agent by ID"""
        try:
            agent = await OutreachAgentService.get_agent_by_id(agent_id, db)
            return OutreachAgentController._format_agent_response(agent)
        except Exception as e:
            logger.error(f"Error in get_agent controller: {str(e)}")
            raise

    @staticmethod
    async def get_user_agents(user_id: uuid.UUID, db: Session):
        """Get all outreach agents for a specific user"""
        try:
            agents = await OutreachAgentService.get_agents_by_user(user_id, db)
            return [
                OutreachAgentController._format_agent_response(agent)
                for agent in agents
            ]
        except Exception as e:
            logger.error(f"Error in get_user_agents controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_agent(
        agent_data: OutreachAgentCreate,
        db: Session
    ):
        """Create a new outreach agent"""
        try:
            agent = await OutreachAgentService.create_agent(
                agent_data.model_dump(exclude_unset=True), db
            )
            return OutreachAgentController._format_agent_response(agent)
        except Exception as e:
            logger.error(f"Error in create_agent controller: {str(e)}")
            raise

    @staticmethod
    async def update_agent(
        agent_id: uuid.UUID,
        agent_data: OutreachAgentUpdate,
        db: Session
    ):
        """Update an outreach agent"""
        try:
            agent = await OutreachAgentService.update_agent(
                agent_id,
                agent_data.model_dump(exclude_unset=True),
                db
            )
            return OutreachAgentController._format_agent_response(agent)
        except Exception as e:
            logger.error(f"Error in update_agent controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_agent(agent_id: uuid.UUID, db: Session):
        """Delete an outreach agent"""
        try:
            await OutreachAgentService.delete_agent(agent_id, db)
            return {"message": "Outreach agent deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_agent controller: {str(e)}")
            raise

    @staticmethod
    async def update_agent_status(
        agent_id: uuid.UUID,
        status_data: AgentStatusUpdate,
        db: Session
    ):
        """Update agent status"""
        try:
            agent = await OutreachAgentService.update_agent_status(
                agent_id, uuid.UUID(status_data.status_id), db
            )
            return OutreachAgentController._format_agent_response(agent)
        except Exception as e:
            logger.error(f"Error in update_agent_status controller: {str(e)}")
            raise

    @staticmethod
    async def update_agent_availability(
        agent_id: uuid.UUID,
        availability_data: AgentAvailabilityUpdate,
        db: Session
    ):
        """Update agent availability"""
        try:
            update_data = {
                "is_available_for_assignment": availability_data.is_available_for_assignment
            }
            agent = await OutreachAgentService.update_agent(agent_id, update_data, db)
            return OutreachAgentController._format_agent_response(agent)
        except Exception as e:
            logger.error(f"Error in update_agent_availability controller: {str(e)}")
            raise

    @staticmethod
    async def update_agent_automation(
        agent_id: uuid.UUID,
        automation_data: AgentAutomationUpdate,
        db: Session
    ):
        """Update agent automation settings"""
        try:
            update_data = {
                "is_automation_enabled": automation_data.is_automation_enabled,
                "automation_settings": automation_data.automation_settings
            }
            agent = await OutreachAgentService.update_agent(agent_id, update_data, db)
            return OutreachAgentController._format_agent_response(agent)
        except Exception as e:
            logger.error(f"Error in update_agent_automation controller: {str(e)}")
            raise

    @staticmethod
    async def get_available_agents(
        platform_id: Optional[uuid.UUID] = None,
        db: Session = None
    ):
        """Get agents available for assignment"""
        try:
            agents = await OutreachAgentService.get_available_agents_for_assignment(platform_id, db)
            return [
                OutreachAgentController._format_agent_response(agent)
                for agent in agents
            ]
        except Exception as e:
            logger.error(f"Error in get_available_agents controller: {str(e)}")
            raise

    @staticmethod
    async def get_agent_statistics(db: Session):
        """Get overall agent statistics"""
        try:
            stats = await OutreachAgentService.get_agent_statistics(db)
            return AgentStatistics(**stats)
        except Exception as e:
            logger.error(f"Error in get_agent_statistics controller: {str(e)}")
            raise

    @staticmethod
    async def reset_daily_counters(db: Session):
        """Reset daily message counters for all agents"""
        try:
            await OutreachAgentService.reset_daily_counters(db)
            return {"message": "Daily counters reset successfully"}
        except Exception as e:
            logger.error(f"Error in reset_daily_counters controller: {str(e)}")
            raise

    @staticmethod
    async def get_agent_performance(
        agent_id: uuid.UUID,
        db: Session
    ):
        """Get performance metrics for a specific agent"""
        try:
            agent = await OutreachAgentService.get_agent_by_id(agent_id, db)
            
            # Calculate completion rate and response rate
            # These would typically be calculated from assignment and outreach data
            completion_rate = None
            response_rate = None
            
            # TODO: Implement actual calculations based on assignments and outreach results
            
            return AgentPerformanceMetrics(
                agent_id=str(agent.id),
                messages_sent_today=agent.messages_sent_today,
                active_lists_count=agent.active_lists_count,
                active_influencers_count=agent.active_influencers_count,
                completion_rate=completion_rate,
                response_rate=response_rate,
                last_activity_at=agent.last_activity_at
            )
        except Exception as e:
            logger.error(f"Error in get_agent_performance controller: {str(e)}")
            raise

    @staticmethod
    async def increment_agent_message_count(
        agent_id: uuid.UUID,
        db: Session
    ):
        """Increment daily message count for an agent"""
        try:
            await OutreachAgentService.increment_message_count(agent_id, db)
            return {"message": "Message count incremented successfully"}
        except Exception as e:
            logger.error(f"Error in increment_agent_message_count controller: {str(e)}")
            raise

    @staticmethod
    def _format_agent_response(agent) -> OutreachAgentResponse:
        """Format an outreach agent object into a response"""
        # Convert to response object
        response = OutreachAgentResponse.model_validate(agent)
        
        # Add assigned user details if available
        if agent.assigned_user:
            response.assigned_user = UserBrief.model_validate(agent.assigned_user)
        
        # Add status details if available
        if agent.status:
            response.status = StatusBrief.model_validate(agent.status)
        
        # Add social connections if available
        if agent.social_connections:
            response.social_connections = [
                AgentSocialConnectionBrief.model_validate(conn)
                for conn in agent.social_connections
            ]
        
        # Add list assignments if available
        if agent.agent_assignments:
            response.agent_assignments = [
                AgentListAssignmentBrief.model_validate(assignment)
                for assignment in agent.agent_assignments
            ]
        
        return response