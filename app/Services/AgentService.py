# app/Services/AgentService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.campaign_models import Agent
from app.Utils.Logger import logger

class AgentService:
    """Service for managing agents"""

    @staticmethod
    async def get_all_agents(db: Session):
        """
        Get all agents
        
        Args:
            db: Database session
            
        Returns:
            List[Agent]: List of all agents
        """
        return db.query(Agent).all()
    
    @staticmethod
    async def get_available_agents(db: Session):
        """
        Get all available agents
        
        Args:
            db: Database session
            
        Returns:
            List[Agent]: List of available agents
        """
        return db.query(Agent).filter(Agent.is_available == True).all()
    
    @staticmethod
    async def get_platform_agents(platform_id: uuid.UUID, db: Session):
        """
        Get all agents for a specific platform
        
        Args:
            platform_id: ID of the platform
            db: Database session
            
        Returns:
            List[Agent]: List of platform agents
        """
        return db.query(Agent).filter(Agent.platform_id == platform_id).all()
    
    @staticmethod
    async def get_agent_by_id(agent_id: uuid.UUID, db: Session):
        """
        Get an agent by ID
        
        Args:
            agent_id: ID of the agent
            db: Database session
            
        Returns:
            Agent: The agent if found
        """
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
            
        return agent
    
    @staticmethod
    async def create_agent(agent_data: Dict[str, Any], db: Session):
        """
        Create a new agent
        
        Args:
            agent_data: Agent data
            db: Database session
            
        Returns:
            Agent: The created agent
        """
        try:
            # Create agent
            agent = Agent(**agent_data)
            
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            return agent
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating agent"
            ) from e
    
    @staticmethod
    async def update_agent(
        agent_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update an agent
        
        Args:
            agent_id: ID of the agent
            update_data: Data to update
            db: Database session
            
        Returns:
            Agent: The updated agent
        """
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(agent, key) and value is not None:
                    setattr(agent, key, value)
            
            db.commit()
            db.refresh(agent)
            
            return agent
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating agent"
            ) from e
    
    @staticmethod
    async def delete_agent(agent_id: uuid.UUID, db: Session):
        """
        Delete an agent
        
        Args:
            agent_id: ID of the agent
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            agent = db.query(Agent).filter(Agent.id == agent_id).first()
            
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found"
                )
            
            # Check if agent has active assignments
            if agent.current_assignment_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete agent with active assignments"
                )
            
            db.delete(agent)
            db.commit()
            
            return True
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting agent: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting agent"
            ) from e