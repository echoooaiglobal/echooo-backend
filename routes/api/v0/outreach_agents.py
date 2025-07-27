# routes/api/v0/outreach_agents.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.Http.Controllers.OutreachAgentController import OutreachAgentController
from app.Models.auth_models import User
from app.Schemas.outreach_agent import (
    OutreachAgentCreate, OutreachAgentUpdate, OutreachAgentResponse,
    OutreachAgentsPaginatedResponse, AgentStatusUpdate, AgentAvailabilityUpdate,
    AgentAutomationUpdate, AgentStatistics, AgentPerformanceMetrics
)

from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/outreach-agents", tags=["Outreach Agents"])

@router.get("/", response_model=OutreachAgentsPaginatedResponse)
async def get_all_outreach_agents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status (active, inactive, suspended, etc.)"),
    availability_filter: Optional[bool] = Query(None, description="Filter by availability"),
    automation_filter: Optional[bool] = Query(None, description="Filter by automation enabled"),
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """
    Get paginated outreach agents with optional filters
    """
    return await OutreachAgentController.get_all_agents_paginated(
        page, page_size, status_filter, availability_filter, automation_filter, db
    ) 

@router.post("/", response_model=OutreachAgentResponse)
async def create_outreach_agent(
    agent_data: OutreachAgentCreate,
    current_user: User = Depends(has_permission("outreach_agent:create")),
    db: Session = Depends(get_db)
):
    """
    Create a new outreach agent
    
    Example request:
    {
        "assigned_user_id": "uuid-here",
        "is_automation_enabled": false,
        "automation_settings": {
            "max_daily_messages": 30,
            "delay_between_messages": 60,
            "working_hours": "09:00-17:00"
        },
        "is_available_for_assignment": true,
        "status_id": "uuid-here"
    }
    """
    return await OutreachAgentController.create_agent(agent_data, db)

@router.get("/statistics", response_model=AgentStatistics)
async def get_agent_statistics(
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get overall agent statistics"""
    return await OutreachAgentController.get_agent_statistics(db)

@router.get("/available", response_model=List[OutreachAgentResponse])
async def get_available_agents(
    platform_id: Optional[uuid.UUID] = Query(None, description="Filter by platform ID"),
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get agents available for assignment, optionally filtered by platform"""
    return await OutreachAgentController.get_available_agents(platform_id, db)

@router.get("/user/{user_id}", response_model=List[OutreachAgentResponse])
async def get_user_agents(
    user_id: uuid.UUID,
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get all outreach agents assigned to a specific user"""
    return await OutreachAgentController.get_user_agents(user_id, db)

@router.get("/{agent_id}", response_model=OutreachAgentResponse)
async def get_outreach_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get an outreach agent by ID"""
    return await OutreachAgentController.get_agent(agent_id, db)

@router.put("/{agent_id}", response_model=OutreachAgentResponse)
async def update_outreach_agent(
    agent_id: uuid.UUID,
    agent_data: OutreachAgentUpdate,
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Update an outreach agent"""
    return await OutreachAgentController.update_agent(agent_id, agent_data, db)

@router.delete("/{agent_id}")
async def delete_outreach_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_permission("outreach:delete")),
    db: Session = Depends(get_db)
):
    """Soft delete an outreach agent"""
    return await OutreachAgentController.delete_agent(agent_id, db)

# Status management endpoints
@router.patch("/{agent_id}/status", response_model=OutreachAgentResponse)
async def update_agent_status(
    agent_id: uuid.UUID,
    status_data: AgentStatusUpdate,
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Update the status of an outreach agent"""
    return await OutreachAgentController.update_agent_status(agent_id, status_data, db)

@router.patch("/{agent_id}/availability", response_model=OutreachAgentResponse)
async def update_agent_availability(
    agent_id: uuid.UUID,
    availability_data: AgentAvailabilityUpdate,
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Update agent availability for assignments"""
    return await OutreachAgentController.update_agent_availability(agent_id, availability_data, db)

@router.patch("/{agent_id}/automation", response_model=OutreachAgentResponse)
async def update_agent_automation(
    agent_id: uuid.UUID,
    automation_data: AgentAutomationUpdate,
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Update agent automation settings"""
    return await OutreachAgentController.update_agent_automation(agent_id, automation_data, db)

# Performance and analytics endpoints
@router.get("/{agent_id}/performance", response_model=AgentPerformanceMetrics)
async def get_agent_performance(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_permission("outreach:read")),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a specific agent"""
    return await OutreachAgentController.get_agent_performance(agent_id, db)

@router.post("/{agent_id}/increment-messages")
async def increment_agent_messages(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Increment daily message count for an agent (used by automation)"""
    return await OutreachAgentController.increment_agent_message_count(agent_id, db)

# Admin endpoints
@router.post("/reset-daily-counters")
async def reset_daily_counters(
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Reset daily message counters for all agents (admin only)"""
    return await OutreachAgentController.reset_daily_counters(db)

# Bulk operations
@router.patch("/bulk/status")
async def bulk_update_agent_status(
    agent_ids: List[uuid.UUID] = Body(..., description="List of agent IDs"),
    status_id: uuid.UUID = Body(..., description="New status ID"),
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Bulk update status for multiple agents"""
    results = []
    errors = []
    
    for agent_id in agent_ids:
        try:
            status_data = AgentStatusUpdate(status_id=str(status_id))
            result = await OutreachAgentController.update_agent_status(agent_id, status_data, db)
            results.append(result)
        except Exception as e:
            errors.append({"agent_id": str(agent_id), "error": str(e)})
    
    return {
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }

@router.patch("/bulk/availability")
async def bulk_update_agent_availability(
    agent_ids: List[uuid.UUID] = Body(..., description="List of agent IDs"),
    is_available: bool = Body(..., description="Availability status"),
    current_user: User = Depends(has_permission("outreach:update")),
    db: Session = Depends(get_db)
):
    """Bulk update availability for multiple agents"""
    results = []
    errors = []
    
    for agent_id in agent_ids:
        try:
            availability_data = AgentAvailabilityUpdate(is_available_for_assignment=is_available)
            result = await OutreachAgentController.update_agent_availability(agent_id, availability_data, db)
            results.append(result)
        except Exception as e:
            errors.append({"agent_id": str(agent_id), "error": str(e)})
    
    return {
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }