# routes/api/v0/list_assignments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.ListAssignmentController import ListAssignmentController
from app.Models.auth_models import User
from app.Schemas.campaign import (
    ListAssignmentCreate, ListAssignmentUpdate, ListAssignmentResponse,
    ListAssignmentStatusUpdate
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/list-assignments", tags=["List Assignments"])

@router.get("/", response_model=List[ListAssignmentResponse])
async def get_all_assignments(
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all list assignments"""
    return await ListAssignmentController.get_all_assignments(db)

@router.get("/list/{list_id}", response_model=List[ListAssignmentResponse])
async def get_assignments_by_list(
    list_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all assignments for a specific list"""
    return await ListAssignmentController.get_assignments_by_list(list_id, db)

@router.get("/agent/{agent_id}", response_model=List[ListAssignmentResponse])
async def get_assignments_by_agent(
    agent_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get all assignments for a specific agent"""
    return await ListAssignmentController.get_assignments_by_agent(agent_id, db)

@router.get("/{assignment_id}", response_model=ListAssignmentResponse)
async def get_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:read")),
    db: Session = Depends(get_db)
):
    """Get a list assignment by ID"""
    return await ListAssignmentController.get_assignment(assignment_id, db)

@router.post("/", response_model=ListAssignmentResponse)
async def create_assignment(
    assignment_data: ListAssignmentCreate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Create a new list assignment
    
    - If agent_id is provided, assigns that specific agent
    - If agent_id is not provided, automatically assigns an available agent
    - If status_id is not provided, defaults to 'pending' status
    """
    return await ListAssignmentController.create_assignment(assignment_data, current_user, db)

@router.put("/{assignment_id}", response_model=ListAssignmentResponse)
async def update_assignment(
    assignment_id: uuid.UUID,
    assignment_data: ListAssignmentUpdate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Update a list assignment (including status changes)"""
    return await ListAssignmentController.update_assignment(assignment_id, assignment_data, db)

@router.patch("/{assignment_id}/status", response_model=ListAssignmentResponse)
async def update_assignment_status(
    assignment_id: uuid.UUID,
    status_data: ListAssignmentStatusUpdate,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """
    Update assignment status specifically
    
    This endpoint handles status transitions and agent availability:
    - 'active': Makes assignment active, marks agent as unavailable
    - 'inactive': Makes assignment inactive, marks agent as available  
    - 'completed': Completes assignment, frees up agent
    - 'failed': Fails assignment, frees up agent
    - 'pending': Sets assignment to pending
    """
    return await ListAssignmentController.update_assignment_status(
        assignment_id, status_data.status_id, db
    )

@router.post("/{assignment_id}/activate", response_model=ListAssignmentResponse)
async def activate_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Activate an assignment (convenience endpoint)"""
    return await ListAssignmentController.activate_assignment(assignment_id, db)

@router.post("/{assignment_id}/deactivate", response_model=ListAssignmentResponse)
async def deactivate_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Deactivate an assignment (convenience endpoint)"""
    return await ListAssignmentController.deactivate_assignment(assignment_id, db)

@router.post("/{assignment_id}/complete", response_model=ListAssignmentResponse)
async def complete_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Mark an assignment as completed"""
    return await ListAssignmentController.complete_assignment(assignment_id, db)

@router.post("/{assignment_id}/fail", response_model=ListAssignmentResponse)
async def fail_assignment(
    assignment_id: uuid.UUID,
    reason: str,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Mark an assignment as failed"""
    return await ListAssignmentController.fail_assignment(assignment_id, reason, db)

@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: uuid.UUID,
    current_user: User = Depends(has_permission("campaign:update")),
    db: Session = Depends(get_db)
):
    """Delete a list assignment"""
    return await ListAssignmentController.delete_assignment(assignment_id, db)