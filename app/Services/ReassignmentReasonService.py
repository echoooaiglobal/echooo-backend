# app/Services/ReassignmentReasonService.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
import uuid

from app.Models.reassignment_reasons import ReassignmentReason
from app.Utils.Logger import logger

class ReassignmentReasonService:
    """Service for managing reassignment reasons"""

    @staticmethod
    async def get_all_reasons(db: Session, active_only: bool = True) -> List[ReassignmentReason]:
        """
        Get all reassignment reasons
        
        Args:
            db: Database session
            active_only: Return only active reasons
            
        Returns:
            List[ReassignmentReason]: List of reassignment reasons
        """
        try:
            query = db.query(ReassignmentReason)
            
            if active_only:
                query = query.filter(ReassignmentReason.is_active == True)
            
            return query.order_by(ReassignmentReason.display_order).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching reassignment reasons: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching reassignment reasons"
            )

    @staticmethod
    async def get_reasons_by_trigger(db: Session, triggered_by: str) -> List[ReassignmentReason]:
        """
        Get reassignment reasons by trigger type
        
        Args:
            db: Database session
            triggered_by: 'system', 'user', or 'both'
            
        Returns:
            List[ReassignmentReason]: List of filtered reassignment reasons
        """
        try:
            query = db.query(ReassignmentReason).filter(ReassignmentReason.is_active == True)
            
            if triggered_by == 'system':
                query = query.filter(ReassignmentReason.is_system_triggered == True)
            elif triggered_by == 'user':
                query = query.filter(ReassignmentReason.is_user_triggered == True)
            elif triggered_by == 'both':
                query = query.filter(
                    ReassignmentReason.is_system_triggered == True,
                    ReassignmentReason.is_user_triggered == True
                )
            
            return query.order_by(ReassignmentReason.display_order).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching reassignment reasons by trigger: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching reassignment reasons"
            )

    @staticmethod
    async def get_reason_by_code(db: Session, code: str) -> Optional[ReassignmentReason]:
        """
        Get reassignment reason by code
        
        Args:
            db: Database session
            code: Reason code
            
        Returns:
            Optional[ReassignmentReason]: Reassignment reason or None
        """
        try:
            return db.query(ReassignmentReason).filter(
                ReassignmentReason.code == code,
                ReassignmentReason.is_active == True
            ).first()
            
        except SQLAlchemyError as e:
            logger.error(f"Error fetching reassignment reason by code: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching reassignment reason"
            )

    @staticmethod
    async def create_reason(reason_data: Dict[str, Any], db: Session) -> ReassignmentReason:
        """
        Create a new reassignment reason
        
        Args:
            reason_data: Data for the new reason
            db: Database session
            
        Returns:
            ReassignmentReason: The created reason
        """
        try:
            # Check if code already exists
            existing_reason = db.query(ReassignmentReason).filter(
                ReassignmentReason.code == reason_data.get('code')
            ).first()
            
            if existing_reason:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Reassignment reason with code '{reason_data.get('code')}' already exists"
                )
            
            # Create new reason
            new_reason = ReassignmentReason(**reason_data)
            db.add(new_reason)
            db.commit()
            db.refresh(new_reason)
            
            logger.info(f"Created new reassignment reason: {new_reason.code}")
            return new_reason
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating reassignment reason: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating reassignment reason"
            )

    @staticmethod
    async def update_reason(reason_id: uuid.UUID, update_data: Dict[str, Any], db: Session) -> ReassignmentReason:
        """
        Update a reassignment reason
        
        Args:
            reason_id: ID of the reason to update
            update_data: Data to update
            db: Database session
            
        Returns:
            ReassignmentReason: The updated reason
        """
        try:
            reason = db.query(ReassignmentReason).filter(ReassignmentReason.id == reason_id).first()
            
            if not reason:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reassignment reason not found"
                )
            
            # Check for unique code constraint if code is being updated
            if 'code' in update_data and update_data['code'] != reason.code:
                existing_reason = db.query(ReassignmentReason).filter(
                    ReassignmentReason.code == update_data['code'],
                    ReassignmentReason.id != reason_id
                ).first()
                
                if existing_reason:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Reassignment reason with code '{update_data['code']}' already exists"
                    )
            
            # Update fields
            for key, value in update_data.items():
                if hasattr(reason, key) and value is not None:
                    setattr(reason, key, value)
            
            db.commit()
            db.refresh(reason)
            
            logger.info(f"Updated reassignment reason: {reason.code}")
            return reason
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating reassignment reason: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating reassignment reason"
            )

    @staticmethod
    async def deactivate_reason(reason_id: uuid.UUID, db: Session) -> ReassignmentReason:
        """
        Deactivate a reassignment reason (soft delete)
        
        Args:
            reason_id: ID of the reason to deactivate
            db: Database session
            
        Returns:
            ReassignmentReason: The deactivated reason
        """
        try:
            reason = db.query(ReassignmentReason).filter(ReassignmentReason.id == reason_id).first()
            
            if not reason:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reassignment reason not found"
                )
            
            reason.is_active = False
            db.commit()
            db.refresh(reason)
            
            logger.info(f"Deactivated reassignment reason: {reason.code}")
            return reason
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deactivating reassignment reason: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deactivating reassignment reason"
            )