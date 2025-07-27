# app/Http/Controllers/InfluencerOutreachController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
import uuid
import math
from datetime import datetime

from app.Services.InfluencerOutreachService import InfluencerOutreachService
from app.Models.influencer_outreach import InfluencerOutreach
from app.Schemas.influencer_outreach import (
    InfluencerOutreachResponse, InfluencerOutreachListResponse, 
    PaginationInfo, InfluencerOutreachStats,
    AssignedInfluencerBrief, AgentAssignmentBrief, OutreachAgentBrief,
    AgentSocialConnectionBrief, CommunicationChannelBrief, StatusBrief
)
from app.Utils.Logger import logger

class InfluencerOutreachController:
    """Controller for influencer outreach endpoints"""
    
    @staticmethod
    async def create_outreach_record(
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerOutreachResponse:
        """Create a new outreach record"""
        try:
            outreach_record = await InfluencerOutreachService.create_outreach_record(data, db)
            return InfluencerOutreachController._format_outreach_response(outreach_record)
        except Exception as e:
            logger.error(f"Error in create_outreach_record controller: {str(e)}")
            raise

    @staticmethod
    async def get_outreach_record(
        outreach_id: uuid.UUID,
        include_relations: bool = False,
        db: Session = None
    ) -> InfluencerOutreachResponse:
        """Get an outreach record by ID"""
        try:
            outreach_record = await InfluencerOutreachService.get_outreach_record_by_id(
                outreach_id, db, include_relations
            )
            return InfluencerOutreachController._format_outreach_response(
                outreach_record, include_relations
            )
        except Exception as e:
            logger.error(f"Error in get_outreach_record controller: {str(e)}")
            raise

    @staticmethod
    async def update_outreach_record(
        outreach_id: uuid.UUID,
        data: Dict[str, Any],
        db: Session
    ) -> InfluencerOutreachResponse:
        """Update an outreach record"""
        try:
            outreach_record = await InfluencerOutreachService.update_outreach_record(
                outreach_id, data, db
            )
            return InfluencerOutreachController._format_outreach_response(outreach_record)
        except Exception as e:
            logger.error(f"Error in update_outreach_record controller: {str(e)}")
            raise

    @staticmethod
    async def delete_outreach_record(
        outreach_id: uuid.UUID,
        db: Session
    ) -> Dict[str, str]:
        """Delete an outreach record"""
        try:
            await InfluencerOutreachService.delete_outreach_record(outreach_id, db)
            return {"message": "Outreach record deleted successfully"}
        except Exception as e:
            logger.error(f"Error in delete_outreach_record controller: {str(e)}")
            raise

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
    ) -> InfluencerOutreachListResponse:
        """Get paginated outreach records"""
        try:
            outreach_records, total = await InfluencerOutreachService.get_outreach_records_paginated(
                page=page,
                size=size,
                assigned_influencer_id=assigned_influencer_id,
                agent_assignment_id=agent_assignment_id,
                outreach_agent_id=outreach_agent_id,
                message_status_id=message_status_id,
                communication_channel_id=communication_channel_id,
                include_relations=include_relations,
                db=db
            )
            
            pages = math.ceil(total / size) if total > 0 else 1
            
            response_items = [
                InfluencerOutreachController._format_outreach_response(record, include_relations)
                for record in outreach_records
            ]
            
            return InfluencerOutreachListResponse(
                items=response_items,
                pagination=PaginationInfo(
                    total=total,
                    page=page,
                    size=size,
                    pages=pages
                )
            )
        except Exception as e:
            logger.error(f"Error in get_outreach_records_paginated controller: {str(e)}")
            raise

    @staticmethod
    async def bulk_create_outreach_records(
        records_data: List[Dict[str, Any]],
        db: Session
    ) -> List[InfluencerOutreachResponse]:
        """Bulk create outreach records"""
        try:
            outreach_records = await InfluencerOutreachService.bulk_create_outreach_records(
                records_data, db
            )
            return [
                InfluencerOutreachController._format_outreach_response(record)
                for record in outreach_records
            ]
        except Exception as e:
            logger.error(f"Error in bulk_create_outreach_records controller: {str(e)}")
            raise

    @staticmethod
    async def bulk_update_outreach_records(
        outreach_ids: List[uuid.UUID],
        update_data: Dict[str, Any],
        db: Session
    ) -> List[InfluencerOutreachResponse]:
        """Bulk update outreach records"""
        try:
            outreach_records = await InfluencerOutreachService.bulk_update_outreach_records(
                outreach_ids, update_data, db
            )
            return [
                InfluencerOutreachController._format_outreach_response(record)
                for record in outreach_records
            ]
        except Exception as e:
            logger.error(f"Error in bulk_update_outreach_records controller: {str(e)}")
            raise

    @staticmethod
    async def get_outreach_statistics(
        agent_assignment_id: Optional[uuid.UUID] = None,
        outreach_agent_id: Optional[uuid.UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        db: Session = None
    ) -> InfluencerOutreachStats:
        """Get outreach statistics"""
        try:
            stats = await InfluencerOutreachService.get_outreach_statistics(
                agent_assignment_id=agent_assignment_id,
                outreach_agent_id=outreach_agent_id,
                date_from=date_from,
                date_to=date_to,
                db=db
            )
            return InfluencerOutreachStats(**stats)
        except Exception as e:
            logger.error(f"Error in get_outreach_statistics controller: {str(e)}")
            raise

    @staticmethod
    async def mark_message_as_sent(
        outreach_id: uuid.UUID,
        sent_at: Optional[datetime] = None,
        db: Session = None
    ) -> InfluencerOutreachResponse:
        """Mark a message as sent"""
        try:
            if sent_at is None:
                sent_at = datetime.utcnow()
            
            update_data = {
                "message_sent_at": sent_at,
                "error_code": None,
                "error_reason": None
            }
            
            outreach_record = await InfluencerOutreachService.update_outreach_record(
                outreach_id, update_data, db
            )
            return InfluencerOutreachController._format_outreach_response(outreach_record)
        except Exception as e:
            logger.error(f"Error in mark_message_as_sent controller: {str(e)}")
            raise

    @staticmethod
    async def mark_message_as_failed(
        outreach_id: uuid.UUID,
        error_code: str,
        error_reason: Optional[str] = None,
        db: Session = None
    ) -> InfluencerOutreachResponse:
        """Mark a message as failed"""
        try:
            update_data = {
                "error_code": error_code,
                "error_reason": error_reason,
                "message_sent_at": None
            }
            
            outreach_record = await InfluencerOutreachService.update_outreach_record(
                outreach_id, update_data, db
            )
            return InfluencerOutreachController._format_outreach_response(outreach_record)
        except Exception as e:
            logger.error(f"Error in mark_message_as_failed controller: {str(e)}")
            raise

    @staticmethod
    async def get_outreach_by_assigned_influencer(
        assigned_influencer_id: uuid.UUID,
        page: int = 1,
        size: int = 50,
        db: Session = None
    ) -> InfluencerOutreachListResponse:
        """Get outreach records for a specific assigned influencer"""
        try:
            return await InfluencerOutreachController.get_outreach_records_paginated(
                page=page,
                size=size,
                assigned_influencer_id=assigned_influencer_id,
                include_relations=True,
                db=db
            )
        except Exception as e:
            logger.error(f"Error in get_outreach_by_assigned_influencer controller: {str(e)}")
            raise

    @staticmethod
    async def get_outreach_by_agent(
        outreach_agent_id: uuid.UUID,
        page: int = 1,
        size: int = 50,
        message_status_id: Optional[uuid.UUID] = None,
        db: Session = None
    ) -> InfluencerOutreachListResponse:
        """Get outreach records for a specific agent"""
        try:
            return await InfluencerOutreachController.get_outreach_records_paginated(
                page=page,
                size=size,
                outreach_agent_id=outreach_agent_id,
                message_status_id=message_status_id,
                include_relations=True,
                db=db
            )
        except Exception as e:
            logger.error(f"Error in get_outreach_by_agent controller: {str(e)}")
            raise

    @staticmethod
    def _format_outreach_response(
        outreach_record: InfluencerOutreach,
        include_relations: bool = False
    ) -> InfluencerOutreachResponse:
        """Format outreach record response"""
        response_data = {
            "id": str(outreach_record.id),
            "assigned_influencer_id": str(outreach_record.assigned_influencer_id),
            "agent_assignment_id": str(outreach_record.agent_assignment_id) if outreach_record.agent_assignment_id else None,
            "outreach_agent_id": str(outreach_record.outreach_agent_id),
            "agent_social_connection_id": str(outreach_record.agent_social_connection_id) if outreach_record.agent_social_connection_id else None,
            "communication_channel_id": str(outreach_record.communication_channel_id) if outreach_record.communication_channel_id else None,
            "message_status_id": str(outreach_record.message_status_id) if outreach_record.message_status_id else None,
            "message_sent_at": outreach_record.message_sent_at,
            "error_code": outreach_record.error_code,
            "error_reason": outreach_record.error_reason,
            "created_at": outreach_record.created_at,
            "updated_at": outreach_record.updated_at
        }
        
        # Include related objects if requested and available
        if include_relations:
            if hasattr(outreach_record, 'assigned_influencer') and outreach_record.assigned_influencer:
                response_data["assigned_influencer"] = AssignedInfluencerBrief(
                    id=str(outreach_record.assigned_influencer.id),
                    campaign_influencer_id=str(outreach_record.assigned_influencer.campaign_influencer_id),
                    agent_assignment_id=str(outreach_record.assigned_influencer.agent_assignment_id),
                    status_id=str(outreach_record.assigned_influencer.status_id),
                    attempts_made=outreach_record.assigned_influencer.attempts_made,
                    created_at=outreach_record.assigned_influencer.created_at
                )
            
            if hasattr(outreach_record, 'agent_assignment') and outreach_record.agent_assignment:
                response_data["agent_assignment"] = AgentAssignmentBrief(
                    id=str(outreach_record.agent_assignment.id),
                    outreach_agent_id=str(outreach_record.agent_assignment.outreach_agent_id),
                    campaign_list_id=str(outreach_record.agent_assignment.campaign_list_id),
                    status_id=str(outreach_record.agent_assignment.status_id),
                    assigned_at=outreach_record.agent_assignment.assigned_at
                )
            
            if hasattr(outreach_record, 'outreach_agent') and outreach_record.outreach_agent:
                response_data["outreach_agent"] = OutreachAgentBrief(
                    id=str(outreach_record.outreach_agent.id),
                    user_id=str(outreach_record.outreach_agent.user_id),
                    status_id=str(outreach_record.outreach_agent.status_id),
                    name=getattr(outreach_record.outreach_agent, 'name', None),
                    is_active=outreach_record.outreach_agent.is_active
                )
            
            if hasattr(outreach_record, 'agent_social_connection') and outreach_record.agent_social_connection:
                response_data["agent_social_connection"] = AgentSocialConnectionBrief(
                    id=str(outreach_record.agent_social_connection.id),
                    outreach_agent_id=str(outreach_record.agent_social_connection.outreach_agent_id),
                    platform_id=str(outreach_record.agent_social_connection.platform_id),
                    status_id=str(outreach_record.agent_social_connection.status_id),
                    platform_account_id=outreach_record.agent_social_connection.platform_account_id
                )
            
            if hasattr(outreach_record, 'communication_channel') and outreach_record.communication_channel:
                response_data["communication_channel"] = CommunicationChannelBrief(
                    id=str(outreach_record.communication_channel.id),
                    name=outreach_record.communication_channel.name,
                    platform_id=str(outreach_record.communication_channel.platform_id),
                    is_active=outreach_record.communication_channel.is_active
                )
            
            if hasattr(outreach_record, 'message_status') and outreach_record.message_status:
                response_data["message_status"] = StatusBrief(
                    id=str(outreach_record.message_status.id),
                    name=outreach_record.message_status.name,
                    model=outreach_record.message_status.model
                )
        
        return InfluencerOutreachResponse(**response_data)