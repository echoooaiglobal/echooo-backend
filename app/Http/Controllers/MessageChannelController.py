# app/Http/Controllers/MessageChannelController.py
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid

from app.Models.auth_models import User
from app.Schemas.campaign import (
    MessageChannelCreate, MessageChannelUpdate, MessageChannelResponse
)
from app.Services.MessageChannelService import MessageChannelService
from app.Utils.Logger import logger

class MessageChannelController:
    """Controller for message channel-related endpoints"""
    
    @staticmethod
    async def get_all_channels(db: Session):
        """Get all message channels"""
        try:
            channels = await MessageChannelService.get_all_channels(db)
            return [MessageChannelResponse.model_validate(channel) for channel in channels]
        except Exception as e:
            logger.error(f"Error in get_all_channels controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_channel(channel_id: uuid.UUID, db: Session):
        """Get a message channel by ID"""
        try:
            channel = await MessageChannelService.get_channel_by_id(channel_id, db)
            return MessageChannelResponse.model_validate(channel)
        except Exception as e:
            logger.error(f"Error in get_channel controller: {str(e)}")
            raise
    
    @staticmethod
    async def create_channel(
        channel_data: MessageChannelCreate,
        db: Session
    ):
        """Create a new message channel"""
        try:
            channel = await MessageChannelService.create_channel(
                channel_data.model_dump(exclude_unset=True),
                db
            )
            return MessageChannelResponse.model_validate(channel)
        except Exception as e:
            logger.error(f"Error in create_channel controller: {str(e)}")
            raise
    
    @staticmethod
    async def update_channel(
        channel_id: uuid.UUID,
        channel_data: MessageChannelUpdate,
        db: Session
    ):
        """Update a message channel"""
        try:
            channel = await MessageChannelService.update_channel(
                channel_id,
                channel_data.model_dump(exclude_unset=True),
                db
            )
            return MessageChannelResponse.model_validate(channel)
        except Exception as e:
            logger.error(f"Error in update_channel controller: {str(e)}")
            raise
    
    @staticmethod
    async def delete_channel(channel_id: uuid.UUID, db: Session):
        """Delete a message channel"""
        try:
            await MessageChannelService.delete_channel(channel_id, db)
            return {"message": "Message channel deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_channel controller: {str(e)}")
            raise