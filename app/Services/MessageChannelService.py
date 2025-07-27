# app/Services/MessageChannelService.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.communication_channels import CommunicationChannel
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
            List[CommunicationChannel]: List of all message channels
        """
        return db.query(CommunicationChannel).all()
    
    @staticmethod
    async def get_channel_by_id(channel_id: uuid.UUID, db: Session):
        """
        Get a message channel by ID
        
        Args:
            channel_id: ID of the message channel
            db: Database session
            
        Returns:
            CommunicationChannel: The message channel if found
        """
        channel = db.query(CommunicationChannel).filter(CommunicationChannel.id == channel_id).first()
        
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
            CommunicationChannel: The created message channel
        """
        try:
            # Check if channel with same code already exists
            existing_channel = db.query(CommunicationChannel).filter(
                CommunicationChannel.code == channel_data['code']
            ).first()
            
            if existing_channel:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Message channel with code '{channel_data['code']}' already exists"
                )
            
            # Create message channel
            channel = CommunicationChannel(**channel_data)
            
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
            CommunicationChannel: The updated message channel
        """
        try:
            channel = db.query(CommunicationChannel).filter(CommunicationChannel.id == channel_id).first()
            
            if not channel:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Message channel not found"
                )
            
            # Check for unique constraint if code is being updated
            if 'code' in update_data and update_data['code'] != channel.code:
                existing_channel = db.query(CommunicationChannel).filter(
                    CommunicationChannel.code == update_data['code'],
                    CommunicationChannel.id != channel_id
                ).first()
                
                if existing_channel:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Message channel with code '{update_data['code']}' already exists"
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
            channel = db.query(CommunicationChannel).filter(CommunicationChannel.id == channel_id).first()
            
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