# app/Http/Controllers/AgentController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.Models.auth_models import User
from app.Schemas.campaign import (
    AgentCreate, AgentUpdate, AgentResponse
)
from app.Services.AgentService import AgentService
from app.Utils.Logger import logger

class AgentController:
    """Controller for agent-related endpoints"""
    
    @staticmethod
    async def get_all_agents(db: Session):
        """Get all agents"""
        try:
            agents = await AgentService.get_all_agents(db)
            return [AgentResponse.model_validate(agent) for agent in agents]
        except Exception as e:
            logger.error(f"Error in get_all_agents controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_available_agents(db: Session):
        """Get all available agents"""
        try:
            agents = await AgentService.get_available_agents(db)
            return [AgentResponse.model_validate(agent) for agent in agents]
        except Exception as e:
            logger.error(f"Error in get_available_agents controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_platform_agents(platform_id: uuid.UUID, db: Session):
        """Get all agents for a specific platform"""
        try:
            agents = await AgentService.get_platform_agents(platform_id, db)
            return [AgentResponse.model_validate(agent) for agent in agents]
        except Exception as e:
            logger.error(f"Error in get_platform_agents controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_agent(agent_id: uuid.UUID, db: Session):
        """Get an agent by ID"""
        try:
            agent = await AgentService.get_agent_by_id(agent_id, db)
            return AgentResponse.model_validate(agent)
        except Exception as e:
            logger.error(f"Error in get_agent controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_agent(
        agent_data: AgentCreate,
        db: Session
    ):
        """Create a new agent"""
        try:
            agent = await AgentService.create_agent(
                agent_data.model_dump(exclude_unset=True),
                db
            )
            return AgentResponse.model_validate(agent)
        except Exception as e:
            logger.error(f"Error in create_agent controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_agent(
        agent_id: uuid.UUID,
        agent_data: AgentUpdate,
        db: Session
    ):
        """Update an agent"""
        try:
            agent = await AgentService.update_agent(
                agent_id,
                agent_data.model_dump(exclude_unset=True),
                db
            )
            return AgentResponse.model_validate(agent)
        except Exception as e:
            logger.error(f"Error in update_agent controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_agent(agent_id: uuid.UUID, db: Session):
        """Delete an agent"""
        try:
            await AgentService.delete_agent(agent_id, db)
            return {"message": "Agent deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_agent controller: {str(e)}")
            raise