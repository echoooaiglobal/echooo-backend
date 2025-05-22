# routes/api/v0/agents.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.AgentController import AgentController
from app.Models.auth_models import User
from app.Schemas.campaign import (
    AgentCreate, AgentUpdate, AgentResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("/", response_model=List[AgentResponse])
async def get_all_agents(
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get all agents"""
    return await AgentController.get_all_agents(db)

@router.get("/available", response_model=List[AgentResponse])
async def get_available_agents(
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get all available agents"""
    return await AgentController.get_available_agents(db)

@router.get("/platform/{platform_id}", response_model=List[AgentResponse])
async def get_platform_agents(
    platform_id: uuid.UUID,
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get all agents for a specific platform"""
    return await AgentController.get_platform_agents(platform_id, db)

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_permission("user:read")),
    db: Session = Depends(get_db)
):
    """Get an agent by ID"""
    return await AgentController.get_agent(agent_id, db)

@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(has_role(["platform_admin", "platform_user"])),
    db: Session = Depends(get_db)
):
    """Create a new agent"""
    return await AgentController.create_agent(agent_data, db)

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    agent_data: AgentUpdate,
    current_user: User = Depends(has_role(["platform_admin", "platform_user"])),
    db: Session = Depends(get_db)
):
    """Update an agent"""
    return await AgentController.update_agent(agent_id, agent_data, db)

@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete an agent"""
    return await AgentController.delete_agent(agent_id, db)