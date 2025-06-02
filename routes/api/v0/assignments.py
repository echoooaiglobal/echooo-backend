# routes/api/v0/assignments.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.Http.Controllers.AssignmentController import AssignmentController
from app.Models.auth_models import User
from app.Schemas.assignment import AssignmentsResponse
from app.Schemas.campaign_list_member import CampaignListMembersPaginatedResponse
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/assignments", tags=["Assignments"])

@router.get("/", response_model=AssignmentsResponse)
async def get_assignments(
    user_id: Optional[str] = Query(None, description="User ID to get assignments for (admin only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get assignments for the current user or a specific user (admin only)
    
    - **For regular users**: Returns their own assignments
    - **For platform admins**: 
      - Without user_id: Returns all assignments
      - With user_id: Returns assignments for the specified user
    """
    try:
        # Convert user_id to UUID if provided
        target_user_id = None
        if user_id:
            try:
                target_user_id = uuid.UUID(user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid user ID format"
                )
        
        return await AssignmentController.get_assignments(
            current_user=current_user,
            user_id=target_user_id,
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assignments: {str(e)}"
        )

@router.get("/{assignment_id}/members", response_model=CampaignListMembersPaginatedResponse)
async def get_assignment_members(
    assignment_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated members for a specific assignment
    
    - **Access control**: Users can only access assignments for their agents
    - **Platform admins**: Can access any assignment
    - **Returns**: Paginated list of campaign list members with social account details
    """
    try:
        return await AssignmentController.get_assignment_members(
            assignment_id=assignment_id,
            page=page,
            page_size=page_size,
            current_user=current_user,
            db=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving assignment members: {str(e)}"
        )