# app/Services/MessageChannelService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.campaign_models import MessageChannel
from app.Utils.Logger import logger

class MessageChannelService:
    """Service for managing message channels"""

    @staticmethod
    async def get_all_channels(db: Session):
        """
        Get all message channels
        
        Args:
            db: Database session
            
        Returns:
            List[MessageChannel]: List of all message channels
        """
        return db.query(MessageChannel).all()
    
    @staticmethod
    async def get_channel_by_id(channel_id: uuid.UUID, db: Session):
        """
        Get a message channel by ID
        
        Args:
            channel_id: ID of the message channel
            db: Database session
            
        Returns:
            MessageChannel: The message channel if found
        """
        channel = db.query(MessageChannel).filter(MessageChannel.id == channel_id).first()
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message channel not found"
            )
            
        return channel
    
    @staticmethod
    async def create_channel(channel_data: Dict[str, Any], db: Session):
        """
        Create a new message channel
        
        Args:
            channel_data: Channel data
            db: Database session
            
        Returns:
            MessageChannel: The created message channel
        """
        try:
            # Check if channel with same shortname already exists
            existing_channel = db.query(MessageChannel).filter(
                MessageChannel.shortname == channel_data['shortname']
            ).first()
            
            if existing_channel:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Message channel with shortname '{channel_data['shortname']}' already exists"
                )
            
            # Create message channel
            channel = MessageChannel(**channel_data)
            
            db.add(channel)
            db.commit()
            db.refresh(channel)
            
            return channel
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating message channel: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating message channel"
            ) from e
    
    @staticmethod
    async def update_channel(
        channel_id: uuid.UUID,
        update_data: Dict[str, Any],
        db: Session
    ):
        """
        Update a message channel
        
        Args:
            channel_id: ID of the message channel
            update_data: Data to update
            db: Database session
            
        Returns:
            MessageChannel: The updated message channel
        """
        try:
            channel = db.query(MessageChannel).filter(MessageChannel.id == channel_id).first()
            
            if not channel:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message channel not found"
                )
            
            # Check for unique constraint if shortname is being updated
            if 'shortname' in update_data and update_data['shortname'] != channel.shortname:
                existing_channel = db.query(MessageChannel).filter(
                    MessageChannel.shortname == update_data['shortname'],
                    MessageChannel.id != channel_id
                ).first()
                
                if existing_channel:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Message channel with shortname '{update_data['shortname']}' already exists"
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(channel, key) and value is not None:
                    setattr(channel, key, value)
            
            db.commit()
            db.refresh(channel)
            
            return channel
        except HTTPException:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating message channel: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating message channel"
            ) from e
    
    @staticmethod
    async def delete_channel(channel_id: uuid.UUID, db: Session):
        """
        Delete a message channel
        
        Args:
            channel_id: ID of the message channel
            db: Database session
            
        Returns:
            bool: True if successful
        """
        try:
            channel = db.query(MessageChannel).filter(MessageChannel.id == channel_id).first()
            
            if not channel:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message channel not found"
                )
            
            # Check if channel is in use
            # Add checks here if needed
            
            db.delete(channel)
            db.commit()
            
            return True
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting message channel: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting message channel"
            ) from e