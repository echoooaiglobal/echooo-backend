# app/Services/InfluencerOutreachService.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Dict, Any, Optional, Tuple
import uuid
import math
from datetime import datetime, timedelta

from app.Models.influencer_outreach import InfluencerOutreach
from app.Models.assigned_influencers import AssignedInfluencer
from app.Models.agent_assignments import AgentAssignment
from app.Models.outreach_agents import OutreachAgent
from app.Models.agent_social_connections import AgentSocialConnection
from app.Models.communication_channels import CommunicationChannel
from app.Models.statuses import Status
from app.Utils.Logger import logger

class InfluencerOutreachService:
    """Service layer for influencer outreach business logic"""
    
    @staticmethod
    async def create_outreach_record(
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerOutreach:
        """Create a new outreach record"""
        try:
            # Validate assigned influencer exists
            assigned_influencer = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.id == data['assigned_influencer_id']
            ).first()
            
            if not assigned_influencer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assigned influencer not found"
                )
            
            # Validate outreach agent exists
            outreach_agent = db.query(OutreachAgent).filter(
                OutreachAgent.id == data['outreach_agent_id']
            ).first()
            
            if not outreach_agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Outreach agent not found"
                )
            
            # Create outreach record
            outreach_record = InfluencerOutreach(**data)
            db.add(outreach_record)
            db.commit()
            db.refresh(outreach_record)
            
            logger.info(f"Created outreach record {outreach_record.id}")
            return outreach_record
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating outreach record: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating outreach record"
            )
    
    @staticmethod
    async def get_outreach_record_by_id(
        outreach_id: uuid.UUID,
        db: Session,
        include_relations: bool = False
    ) -> InfluencerOutreach:
        """Get outreach record by ID"""
        try:
            query = db.query(InfluencerOutreach).filter(
                InfluencerOutreach.id == outreach_id
            )
            
            if include_relations:
                query = query.options(
                    joinedload(InfluencerOutreach.assigned_influencer),
                    joinedload(InfluencerOutreach.agent_assignment),
                    joinedload(InfluencerOutreach.outreach_agent),
                    joinedload(InfluencerOutreach.agent_social_connection),
                    joinedload(InfluencerOutreach.communication_channel),
                    joinedload(InfluencerOutreach.message_status)
                )
            
            outreach_record = query.first()
            
            if not outreach_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Outreach record not found"
                )
            
            return outreach_record
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching outreach record {outreach_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching outreach record"
            )
    
    @staticmethod
    async def update_outreach_record(
        outreach_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerOutreach:
        """Update an outreach record"""
        try:
            outreach_record = await InfluencerOutreachService.get_outreach_record_by_id(
                outreach_id, db, include_relations=False
            )
            
            # Update fields
            for field, value in data.items():
                if hasattr(outreach_record, field) and value is not None:
                    setattr(outreach_record, field, value)
            
            db.commit()
            db.refresh(outreach_record)
            
            logger.info(f"Updated outreach record {outreach_id}")
            return outreach_record
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating outreach record {outreach_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating outreach record"
            )
    
    @staticmethod
    async def delete_outreach_record(
        outreach_id: uuid.UUID,
        db: Session
    ) -> bool:
        """Delete an outreach record"""
        try:
            outreach_record = await InfluencerOutreachService.get_outreach_record_by_id(
                outreach_id, db, include_relations=False
            )
            
            db.delete(outreach_record)
            db.commit()
            
            logger.info(f"Deleted outreach record {outreach_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting outreach record {outreach_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error deleting outreach record"
            )
    
    @staticmethod
    async def get_outreach_records_paginated(
        page: int = 1,
        size: int = 50,
        assigned_influencer_id: Optional[uuid.UUID] = None,
        agent_assignment_id: Optional[uuid.UUID] = None,
        outreach_agent_id: Optional[uuid.UUID] = None,
        message_status_id: Optional[uuid.UUID] = None,
        communication_channel_id: Optional[uuid.UUID] = None,
        include_relations: bool = False,
        db: Session = None
    ) -> Tuple[List[InfluencerOutreach], int]:
        """Get paginated outreach records with filters"""
        try:
            query = db.query(InfluencerOutreach)
            
            # Apply filters
            if assigned_influencer_id:
                query = query.filter(InfluencerOutreach.assigned_influencer_id == assigned_influencer_id)
            
            if agent_assignment_id:
                query = query.filter(InfluencerOutreach.agent_assignment_id == agent_assignment_id)
            
            if outreach_agent_id:
                query = query.filter(InfluencerOutreach.outreach_agent_id == outreach_agent_id)
            
            if message_status_id:
                query = query.filter(InfluencerOutreach.message_status_id == message_status_id)
            
            if communication_channel_id:
                query = query.filter(InfluencerOutreach.communication_channel_id == communication_channel_id)
            
            # Include relations if requested
            if include_relations:
                query = query.options(
                    joinedload(InfluencerOutreach.assigned_influencer),
                    joinedload(InfluencerOutreach.agent_assignment),
                    joinedload(InfluencerOutreach.outreach_agent),
                    joinedload(InfluencerOutreach.agent_social_connection),
                    joinedload(InfluencerOutreach.communication_channel),
                    joinedload(InfluencerOutreach.message_status)
                )
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            query = query.order_by(desc(InfluencerOutreach.created_at))
            query = query.offset((page - 1) * size).limit(size)
            
            outreach_records = query.all()
            
            return outreach_records, total
            
        except Exception as e:
            logger.error(f"Error fetching paginated outreach records: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error fetching outreach records"
            )
    
    @staticmethod
    async def bulk_create_outreach_records(
        records_data: List[Dict[str, Any]],
        db: Session
    ) -> List[InfluencerOutreach]:
        """Bulk create outreach records"""
        try:
            outreach_records = []
            
            for record_data in records_data:
                # Validate assigned influencer exists
                assigned_influencer = db.query(AssignedInfluencer).filter(
                    AssignedInfluencer.id == record_data['assigned_influencer_id']
                ).first()
                
                if not assigned_influencer:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Assigned influencer {record_data['assigned_influencer_id']} not found"
                    )
                
                outreach_record = InfluencerOutreach(**record_data)
                outreach_records.append(outreach_record)
            
            db.add_all(outreach_records)
            db.commit()
            
            for record in outreach_records:
                db.refresh(record)
            
            logger.info(f"Created {len(outreach_records)} outreach records")
            return outreach_records
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk creating outreach records: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error bulk creating outreach records"
            )
    
    @staticmethod
    async def bulk_update_outreach_records(
        outreach_ids: List[uuid.UUID],
        update_data: Dict[str, Any],
        db: Session
    ) -> List[InfluencerOutreach]:
        """Bulk update outreach records"""
        try:
            outreach_records = db.query(InfluencerOutreach).filter(
                InfluencerOutreach.id.in_(outreach_ids)
            ).all()
            
            if len(outreach_records) != len(outreach_ids):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Some outreach records not found"
                )
            
            for record in outreach_records:
                for field, value in update_data.items():
                    if hasattr(record, field) and value is not None:
                        setattr(record, field, value)
            
            db.commit()
            
            for record in outreach_records:
                db.refresh(record)
            
            logger.info(f"Updated {len(outreach_records)} outreach records")
            return outreach_records
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error bulk updating outreach records: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error bulk updating outreach records"
            )
    
    @staticmethod
    async def get_outreach_statistics(
        agent_assignment_id: Optional[uuid.UUID] = None,
        outreach_agent_id: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get outreach statistics"""
        try:
            query = db.query(InfluencerOutreach)
            
            # Apply filters
            if agent_assignment_id:
                query = query.filter(InfluencerOutreach.agent_assignment_id == agent_assignment_id)
            
            if outreach_agent_id:
                query = query.filter(InfluencerOutreach.outreach_agent_id == outreach_agent_id)
            
            if date_from:
                query = query.filter(InfluencerOutreach.created_at >= date_from)
            
            if date_to:
                query = query.filter(InfluencerOutreach.created_at <= date_to)
            
            # Calculate statistics
            total_records = query.count()
            
            successful_messages = query.filter(
                and_(
                    InfluencerOutreach.message_sent_at.isnot(None),
                    InfluencerOutreach.error_code.is_(None)
                )
            ).count()
            
            failed_messages = query.filter(
                InfluencerOutreach.error_code.isnot(None)
            ).count()
            
            pending_messages = query.filter(
                and_(
                    InfluencerOutreach.message_sent_at.is_(None),
                    InfluencerOutreach.error_code.is_(None)
                )
            ).count()
            
            success_rate = (successful_messages / total_records * 100) if total_records > 0 else 0
            
            # Most active agent
            most_active_agent = db.query(
                InfluencerOutreach.outreach_agent_id,
                func.count(InfluencerOutreach.id).label('count')
            ).group_by(InfluencerOutreach.outreach_agent_id).order_by(desc('count')).first()
            
            # Most used channel
            most_used_channel = db.query(
                InfluencerOutreach.communication_channel_id,
                func.count(InfluencerOutreach.id).label('count')
            ).filter(
                InfluencerOutreach.communication_channel_id.isnot(None)
            ).group_by(InfluencerOutreach.communication_channel_id).order_by(desc('count')).first()
            
            return {
                "total_outreach_records": total_records,
                "successful_messages": successful_messages,
                "failed_messages": failed_messages,
                "pending_messages": pending_messages,
                "success_rate": round(success_rate, 2),
                "most_active_agent": str(most_active_agent[0]) if most_active_agent else None,
                "most_used_channel": str(most_used_channel[0]) if most_used_channel else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating outreach statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error calculating outreach statistics"
            )