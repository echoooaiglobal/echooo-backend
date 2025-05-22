# routes/api/v0/message_channels.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.Http.Controllers.MessageChannelController import MessageChannelController
from app.Models.auth_models import User
from app.Schemas.campaign import (
    MessageChannelCreate, MessageChannelUpdate, MessageChannelResponse
)
from app.Utils.Helpers import (
    get_current_active_user, has_role, has_permission
)
from config.database import get_db

router = APIRouter(prefix="/message-channels", tags=["Message Channels"])

@router.get("/", response_model=List[MessageChannelResponse])
async def get_all_channels(
    db: Session = Depends(get_db)
):
    """Get all message channels"""
    return await MessageChannelController.get_all_channels(db)

@router.get("/{channel_id}", response_model=MessageChannelResponse)
async def get_channel(
    channel_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get a message channel by ID"""
    return await MessageChannelController.get_channel(channel_id, db)

@router.post("/", response_model=MessageChannelResponse)
async def create_channel(
    channel_data: MessageChannelCreate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Create a new message channel"""
    return await MessageChannelController.create_channel(channel_data, db)

@router.put("/{channel_id}", response_model=MessageChannelResponse)
async def update_channel(
    channel_id: uuid.UUID,
    channel_data: MessageChannelUpdate,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Update a message channel"""
    return await MessageChannelController.update_channel(channel_id, channel_data, db)

@router.delete("/{channel_id}")
async def delete_channel(
    channel_id: uuid.UUID,
    current_user: User = Depends(has_role(["platform_admin"])),
    db: Session = Depends(get_db)
):
    """Delete a message channel"""
    return await MessageChannelController.delete_channel(channel_id, db)