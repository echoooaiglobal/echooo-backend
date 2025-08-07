# routes/api/v0/statuses.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.StatusController import StatusController
from app.Models.auth_models import User
from app.Schemas.campaign import (
    StatusCreate, StatusUpdate, StatusResponse
)
from app.Utils.Helpers import (
    has_role
)
from config.database import get_db

router = APIRouter(prefix="/statuses", tags=["Statuses"])

@router.get("/", response_model=List[StatusResponse])
async def get_all_statuses(
    db: Session = Depends(get_db)
):
    """Get all statuses"""
    return await StatusController.get_all_statuses(db)

@router.get("/model/{model}", response_model=List[StatusResponse])
async def get_statuses_by_model(
    model: str,
    db: Session = Depends(get_db)
):
    """Get all statuses for a specific model"""
    return await StatusController.get_statuses_by_model(model, db)

@router.get("/{status_id}", response_model=StatusResponse)
async def get_status(
    status_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a status by ID"""
    return await StatusController.get_status(status_id, db)

@router.post("/", response_model=StatusResponse)
async def create_status(
    status_data: StatusCreate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Create a new status"""
    return await StatusController.create_status(status_data, db)

@router.put("/{status_id}", response_model=StatusResponse)
async def update_status(
    status_id: uuid.UUID,
    status_data: StatusUpdate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update a status"""
    return await StatusController.update_status(status_id, status_data, db)

@router.delete("/{status_id}")
async def delete_status(
    status_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a status"""
    return await StatusController.delete_status(status_id, db)