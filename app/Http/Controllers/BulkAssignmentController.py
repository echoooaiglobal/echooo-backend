# app/Http/Controllers/BulkAssignmentController.py

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid

from app.Services.BulkAssignmentService import BulkAssignmentService
from app.Schemas.bulk_assignment import (
    BulkAssignmentValidationResponse, BulkAssignmentResponse,
    ReassignmentResponse, AgentCapacityInfo
)
from app.Utils.Logger import logger

class BulkAssignmentController:
    """Controller for bulk assignment operations"""
    
    @staticmethod
    async def validate_bulk_assignment(
        campaign_list_id: uuid.UUID,
        preferred_agent_ids: Optional[List[uuid.UUID]],
        db: Session
    ) -> BulkAssignmentValidationResponse:
        """Validate if bulk assignment is possible"""
        try:
            validation_result = await BulkAssignmentService.validate_bulk_assignment(
                campaign_list_id, preferred_agent_ids, db
            )
            
            # Format agent capacity info
            agent_capacities = []
            for agent_info in validation_result["available_agents"]:
                capacity_info = AgentCapacityInfo(
                    agent_id=uuid.UUID(agent_info["agent_id"]),
                    current_influencers_count=agent_info["current_influencers_count"],
                    max_concurrent_influencers=agent_info["max_concurrent_influencers"],
                    available_capacity=agent_info["available_capacity"],
                    existing_assignments_for_list=[
                        uuid.UUID(aid) for aid in agent_info["existing_assignments_for_list"]
                    ],
                    can_accept_new=agent_info["can_accept_new"]
                )
                agent_capacities.append(capacity_info)
            
            return BulkAssignmentValidationResponse(
                campaign_list_info=validation_result["campaign_list_info"],
                available_agents=agent_capacities,
                total_unassigned_influencers=validation_result["total_unassigned_influencers"],
                total_available_capacity=validation_result["total_available_capacity"],
                can_assign_all=validation_result["can_assign_all"],
                recommendations=validation_result["recommendations"]
            )
            
        except Exception as e:
            logger.error(f"Error in validate_bulk_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def execute_bulk_assignment(
        campaign_list_id: uuid.UUID,
        strategy: str = "round_robin",
        preferred_agent_ids: Optional[List[uuid.UUID]] = None,
        max_influencers_per_agent: Optional[int] = None,
        force_new_assignments: bool = False,
        db: Session = None
    ) -> BulkAssignmentResponse:
        """Execute bulk assignment of influencers to agents"""
        try:
            assignment_result = await BulkAssignmentService.execute_bulk_assignment(
                campaign_list_id=campaign_list_id,
                strategy=strategy,
                preferred_agent_ids=preferred_agent_ids,
                max_influencers_per_agent=max_influencers_per_agent,
                force_new_assignments=force_new_assignments,
                db=db
            )
            
            # Format agent assignments - FIXED: Include total_influencers_in_assignment
            agent_assignments = []
            for assignment in assignment_result["agent_assignments"]:
                if assignment["agent_assignment_id"]:  # Only include successful assignments
                    agent_assignments.append({
                        "agent_id": uuid.UUID(assignment["agent_id"]),
                        "agent_assignment_id": uuid.UUID(assignment["agent_assignment_id"]),
                        "assigned_influencers_count": assignment["assigned_influencers_count"],
                        "total_influencers_in_assignment": assignment["total_influencers_in_assignment"],  # ADDED this field
                        "is_new_assignment": assignment["is_new_assignment"],
                        "influencer_ids": [uuid.UUID(iid) for iid in assignment["influencer_ids"]]
                    })
            
            # Format unassigned influencers
            unassigned_influencers = [
                uuid.UUID(iid) for iid in assignment_result["unassigned_influencers"]
            ]
            
            return BulkAssignmentResponse(
                assignment_summary=assignment_result["assignment_summary"],
                agent_assignments=agent_assignments,
                unassigned_influencers=unassigned_influencers,
                warnings=assignment_result["warnings"],
                errors=assignment_result["errors"]
            )
            
        except Exception as e:
            logger.error(f"Error in execute_bulk_assignment controller: {str(e)}")
            raise
    
    @staticmethod
    async def reassign_influencer(
        assigned_influencer_id: uuid.UUID,
        reason: str,
        prefer_existing_assignments: bool = True,
        reassigned_by: uuid.UUID = None,
        db: Session = None
    ) -> ReassignmentResponse:
        """Reassign a single influencer to a different agent"""
        try:
            reassignment_result = await BulkAssignmentService.reassign_influencer(
                assigned_influencer_id=assigned_influencer_id,
                reason=reason,
                prefer_existing_assignments=prefer_existing_assignments,
                reassigned_by=reassigned_by,
                db=db
            )
            
            # Format new assignment if successful
            new_assignment = None
            if reassignment_result["success"] and reassignment_result["new_assignment"]:
                assignment_data = reassignment_result["new_assignment"]
                new_assignment = {
                    "agent_id": uuid.UUID(assignment_data["agent_id"]),
                    "agent_assignment_id": uuid.UUID(assignment_data["agent_assignment_id"]),
                    "assigned_influencers_count": assignment_data["assigned_influencers_count"],
                    "is_new_assignment": assignment_data["is_new_assignment"],
                    "influencer_ids": [uuid.UUID(iid) for iid in assignment_data["influencer_ids"]]
                }
            
            assignment_history_id = None
            if reassignment_result["assignment_history_id"]:
                assignment_history_id = uuid.UUID(reassignment_result["assignment_history_id"])
            
            return ReassignmentResponse(
                success=reassignment_result["success"],
                new_assignment=new_assignment,
                assignment_history_id=assignment_history_id,
                message=reassignment_result["message"]
            )
            
        except Exception as e:
            logger.error(f"Error in reassign_influencer controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_available_agents_for_campaign(
        campaign_list_id: uuid.UUID,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Get available agents for a specific campaign list with capacity info"""
        try:
            # Use service method to get available agents
            available_agents = await BulkAssignmentService._get_available_agents(
                campaign_list_id, None, db
            )
            
            # Get capacity info for each agent
            agents_with_capacity = []
            for agent in available_agents:
                capacity_info = await BulkAssignmentService._get_agent_capacity(
                    agent.id, campaign_list_id, db
                )
                
                agent_data = {
                    "id": str(agent.id),
                    "assigned_user_id": str(agent.assigned_user_id),
                    "is_automation_enabled": agent.is_automation_enabled,
                    "is_available_for_assignment": agent.is_available_for_assignment,
                    "is_company_exclusive": agent.is_company_exclusive,
                    "company_id": str(agent.company_id) if agent.company_id else None,
                    "capacity_info": capacity_info
                }
                agents_with_capacity.append(agent_data)
            
            return agents_with_capacity
            
        except Exception as e:
            logger.error(f"Error in get_available_agents_for_campaign controller: {str(e)}")
            raise
    
    @staticmethod
    async def get_assignment_recommendations(
        campaign_list_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """Get recommendations for optimal assignment strategy"""
        try:
            validation_result = await BulkAssignmentService.validate_bulk_assignment(
                campaign_list_id, None, db
            )
            
            unassigned_count = validation_result["total_unassigned_influencers"]
            available_capacity = validation_result["total_available_capacity"]
            available_agents = validation_result["available_agents"]
            
            recommendations = {
                "strategy": "round_robin",
                "estimated_agents_needed": 0,
                "can_complete_assignment": validation_result["can_assign_all"],
                "capacity_analysis": {
                    "total_unassigned": unassigned_count,
                    "total_available_capacity": available_capacity,
                    "shortage": max(0, unassigned_count - available_capacity)
                },
                "recommendations": validation_result["recommendations"]
            }
            
            # Calculate estimated agents needed
            if available_agents:
                max_per_assignment = await BulkAssignmentService._get_setting_value(
                    "max_influencers_per_assignment", db, default=20
                )
                recommendations["estimated_agents_needed"] = min(
                    len(available_agents),
                    (unassigned_count + max_per_assignment - 1) // max_per_assignment  # Ceiling division
                )
            
            # Add strategy recommendations
            if unassigned_count <= 20:
                recommendations["strategy"] = "single_agent"
                recommendations["recommendations"].append("Small list - assign to single agent for better coordination")
            elif available_capacity < unassigned_count:
                recommendations["strategy"] = "partial_assignment"
                recommendations["recommendations"].append("Partial assignment required - consider increasing agent capacity")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in get_assignment_recommendations controller: {str(e)}")
            raise