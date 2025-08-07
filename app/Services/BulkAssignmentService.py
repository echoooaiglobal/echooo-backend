# app/Services/BulkAssignmentService.py

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Any, Optional, Tuple
import uuid
import math
from datetime import datetime

from app.Models.campaign_lists import CampaignList
from app.Models.campaign_influencers import CampaignInfluencer
from app.Models.outreach_agents import OutreachAgent
from app.Models.agent_assignments import AgentAssignment
from app.Models.assigned_influencers import AssignedInfluencer
from app.Models.influencer_assignment_histories import InfluencerAssignmentHistory
from app.Models.statuses import Status
from app.Models.system_settings import Settings
from app.Utils.Logger import logger

class BulkAssignmentService:
    """Service for handling bulk influencer assignments to agents"""
    
    @staticmethod
    async def validate_bulk_assignment(
        campaign_list_id: uuid.UUID,
        preferred_agent_ids: Optional[List[uuid.UUID]],
        db: Session
    ) -> Dict[str, Any]:
        """Validate if bulk assignment is possible and provide recommendations"""
        
        try:
            campaign_list = db.query(CampaignList).filter(
                CampaignList.id == campaign_list_id
            ).first()
            
            if not campaign_list:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Campaign list not found"
                )
            
            unassigned_influencers = await BulkAssignmentService._get_unassigned_influencers(
                campaign_list_id, db
            )
            
            available_agents = await BulkAssignmentService._get_available_agents(
                campaign_list_id, preferred_agent_ids, db
            )
            
            agent_capacities = []
            total_available_capacity = 0
            
            for agent in available_agents:
                capacity_info = await BulkAssignmentService._get_agent_capacity(
                    agent.id, campaign_list_id, db
                )
                agent_capacities.append(capacity_info)
                total_available_capacity += capacity_info["available_capacity"]
            
            recommendations = []
            can_assign_all = total_available_capacity >= len(unassigned_influencers)
            
            if not can_assign_all:
                shortage = len(unassigned_influencers) - total_available_capacity
                recommendations.append(f"Need {shortage} more agent capacity to assign all influencers")
                recommendations.append("Consider adding more agents or increasing agent limits")
            
            if len(available_agents) == 0:
                recommendations.append("No available agents found for this campaign list")
            
            return {
                "campaign_list_info": {
                    "id": str(campaign_list_id),
                    "name": campaign_list.name if hasattr(campaign_list, 'name') else None,
                    "total_influencers": len(unassigned_influencers)
                },
                "available_agents": agent_capacities,
                "total_unassigned_influencers": len(unassigned_influencers),
                "total_available_capacity": total_available_capacity,
                "can_assign_all": can_assign_all,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error in validate_bulk_assignment: {str(e)}")
            raise
    
    @staticmethod
    async def execute_bulk_assignment(
        campaign_list_id: uuid.UUID,
        strategy: str = "round_robin",
        preferred_agent_ids: Optional[List[uuid.UUID]] = None,
        max_influencers_per_agent: Optional[int] = None,
        force_new_assignments: bool = False,
        db: Session = None
    ) -> Dict[str, Any]:
        """Execute bulk assignment of influencers to agents"""
        
        try:
            unassigned_influencers = await BulkAssignmentService._get_unassigned_influencers(
                campaign_list_id, db
            )
            
            total_influencers_to_assign = len(unassigned_influencers)
            
            if not unassigned_influencers:
                return {
                    "assignment_summary": {
                        "total_influencers": 0,
                        "total_agents_assigned": 0,
                        "successful_assignments": 0,
                        "failed_assignments": 0
                    },
                    "agent_assignments": [],
                    "unassigned_influencers": [],
                    "warnings": ["No unassigned influencers found"],
                    "errors": [],
                    "success_message": "No influencers to assign"
                }
            
            available_agents = await BulkAssignmentService._get_available_agents(
                campaign_list_id, preferred_agent_ids, db
            )
            
            if not available_agents:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No available agents found for assignment"
                )
            
            if not max_influencers_per_agent:
                max_influencers_per_agent = await BulkAssignmentService._get_setting_value(
                    "max_influencers_per_assignment", db, default=20
                )
            
            distribution = await BulkAssignmentService._distribute_influencers(
                unassigned_influencers,
                available_agents,
                max_influencers_per_agent,
                strategy,
                force_new_assignments,
                campaign_list_id,
                db
            )
            
            result = await BulkAssignmentService._execute_assignments(
                distribution, campaign_list_id, total_influencers_to_assign, db
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in execute_bulk_assignment: {str(e)}")
            raise
    
    @staticmethod
    async def _execute_assignments(
        distribution: Dict[uuid.UUID, List[CampaignInfluencer]],
        campaign_list_id: uuid.UUID,
        total_influencers_to_assign: int,
        db: Session
    ) -> Dict[str, Any]:
        """Execute the actual assignments with proper counter management and unassigned tracking"""
        
        successful_assignments = 0
        failed_assignments = 0
        agent_assignments = []
        unassigned_influencers = []
        errors = []
        warnings = []
        
        # Track which influencers were distributed
        distributed_influencer_ids = set()
        for agent_id, influencers in distribution.items():
            for influencer in influencers:
                distributed_influencer_ids.add(influencer.id)
        
        # Find influencers that weren't distributed due to capacity limits
        all_unassigned = await BulkAssignmentService._get_unassigned_influencers(
            campaign_list_id, db
        )
        
        not_distributed_influencers = []
        for influencer in all_unassigned:
            if influencer.id not in distributed_influencer_ids:
                not_distributed_influencers.append(influencer)
        
        try:
            active_status = db.query(Status).filter(
                Status.model == "agent_assignment",
                Status.name == "active"
            ).first()
            
            assigned_status = db.query(Status).filter(
                Status.model == "assigned_influencer",
                Status.name == "assigned"
            ).first()
            
            for agent_id, influencers in distribution.items():
                try:
                    existing_assignment = db.query(AgentAssignment).filter(
                        AgentAssignment.outreach_agent_id == agent_id,
                        AgentAssignment.campaign_list_id == campaign_list_id,
                        AgentAssignment.is_deleted == False
                    ).first()
                    
                    if existing_assignment:
                        agent_assignment = existing_assignment
                        is_new_assignment = False
                        logger.info(f"Using existing assignment {agent_assignment.id} for agent {agent_id}")
                    else:
                        agent_assignment = AgentAssignment(
                            outreach_agent_id=agent_id,
                            campaign_list_id=campaign_list_id,
                            status_id=active_status.id if active_status else None,
                            assigned_at=datetime.utcnow()
                        )
                        db.add(agent_assignment)
                        db.flush()
                        is_new_assignment = True
                        logger.info(f"Created new assignment {agent_assignment.id} for agent {agent_id}")
                    
                    assigned_influencer_ids = []
                    for influencer in influencers:
                        try:
                            assigned_influencer = AssignedInfluencer(
                                campaign_influencer_id=influencer.id,
                                agent_assignment_id=agent_assignment.id,
                                status_id=assigned_status.id if assigned_status else None,
                                type='active',
                                assigned_at=datetime.utcnow()
                            )
                            db.add(assigned_influencer)
                            
                            influencer.is_assigned_to_agent = True
                            
                            assigned_influencer_ids.append(str(influencer.id))
                            successful_assignments += 1
                            
                        except Exception as e:
                            logger.error(f"Error assigning influencer {influencer.id}: {str(e)}")
                            failed_assignments += 1
                            unassigned_influencers.append(str(influencer.id))
                    
                    db.flush()
                    
                    actual_total_count = db.query(AssignedInfluencer).filter(
                        AssignedInfluencer.agent_assignment_id == agent_assignment.id,
                        AssignedInfluencer.type == 'active'
                    ).count()
                    
                    if existing_assignment:
                        logger.info(f"Updated existing assignment {agent_assignment.id} count to {actual_total_count}")
                    else:
                        logger.info(f"Set new assignment {agent_assignment.id} count to {actual_total_count}")
                    
                    agent_assignments.append({
                        "agent_id": str(agent_id),
                        "agent_assignment_id": str(agent_assignment.id),
                        "assigned_influencers_count": len(assigned_influencer_ids),
                        "total_influencers_in_assignment": actual_total_count,
                        "is_new_assignment": is_new_assignment,
                        "influencer_ids": assigned_influencer_ids
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing agent {agent_id}: {str(e)}")
                    failed_assignments += len(influencers)
                    unassigned_influencers.extend([str(inf.id) for inf in influencers])
                    errors.append(f"Failed to assign influencers to agent {agent_id}: {str(e)}")
            
            # Add not distributed influencers to unassigned list
            unassigned_influencers.extend([str(inf.id) for inf in not_distributed_influencers])
            
            # Generate user-friendly messages
            success_message = ""
            if successful_assignments > 0:
                if len(unassigned_influencers) == 0:
                    success_message = f"Successfully assigned all {successful_assignments} influencers to {len(agent_assignments)} agent(s)."
                else:
                    success_message = f"Successfully assigned {successful_assignments} out of {total_influencers_to_assign} influencers to {len(agent_assignments)} agent(s)."
            
            # Add capacity warnings for unassigned influencers
            if len(not_distributed_influencers) > 0:
                warnings.append(f"{len(not_distributed_influencers)} influencer(s) could not be assigned due to agent capacity limits.")
                warnings.append("Consider adding more agents or completing/archiving existing influencer outreach to free up capacity.")
            
            if failed_assignments > 0:
                warnings.append(f"{failed_assignments} influencer(s) failed to assign due to system errors.")
            
            await BulkAssignmentService._update_all_agent_counters(
                list(distribution.keys()), db
            )
            
            db.commit()
            
            return {
                "assignment_summary": {
                    "total_influencers": total_influencers_to_assign,
                    "total_agents_assigned": len(agent_assignments),
                    "successful_assignments": successful_assignments,
                    "failed_assignments": failed_assignments + len(not_distributed_influencers)
                },
                "agent_assignments": agent_assignments,
                "unassigned_influencers": unassigned_influencers,
                "warnings": warnings,
                "errors": errors,
                "success_message": success_message
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in _execute_assignments: {str(e)}")
            raise
    
    @staticmethod
    async def reassign_influencer(
        assigned_influencer_id: uuid.UUID,
        reason: str,
        prefer_existing_assignments: bool = True,
        reassigned_by: uuid.UUID = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Reassign a single influencer to a different agent"""
        
        try:
            current_assignment = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.id == assigned_influencer_id,
                AssignedInfluencer.type == 'active'
            ).first()
            
            if not current_assignment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active assigned influencer not found"
                )
            
            current_agent_assignment = current_assignment.agent_assignment
            current_agent_id = current_agent_assignment.outreach_agent_id
            campaign_list_id = current_agent_assignment.campaign_list_id
            
            best_agent, existing_assignment_id = await BulkAssignmentService._find_best_agent_for_reassignment(
                current_assignment.campaign_influencer_id,
                current_agent_id,
                campaign_list_id,
                prefer_existing_assignments,
                db
            )
            
            if not best_agent:
                return {
                    "success": False,
                    "new_assignment": None,
                    "assignment_history_id": None,
                    "message": "No available agent found for reassignment"
                }
            
            current_assignment.type = 'archived'
            current_assignment.archived_at = datetime.utcnow()
            
            campaign_influencer = current_assignment.campaign_influencer
            campaign_influencer.is_assigned_to_agent = False
            
            new_assignment = await BulkAssignmentService._assign_single_influencer_to_agent(
                current_assignment.campaign_influencer_id,
                best_agent.id,
                existing_assignment_id,
                campaign_list_id,
                db
            )
            
            history = await BulkAssignmentService._create_assignment_history(
                current_assignment.campaign_influencer_id,
                current_agent_assignment.id,
                current_agent_id,
                best_agent.id,
                current_assignment.attempts_made,
                "manual_reassignment",
                "user",
                reassigned_by,
                reason,
                db
            )
            
            db.commit()
            
            return {
                "success": True,
                "new_assignment": {
                    "agent_id": str(best_agent.id),
                    "agent_assignment_id": str(new_assignment.agent_assignment_id),
                    "assigned_influencers_count": 1,
                    "is_new_assignment": existing_assignment_id is None,
                    "influencer_ids": [str(current_assignment.campaign_influencer_id)]
                },
                "assignment_history_id": str(history.id),
                "message": "Influencer successfully reassigned"
            }
            
        except Exception as e:
            logger.error(f"Error in reassign_influencer: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    async def _get_unassigned_influencers(
        campaign_list_id: uuid.UUID,
        db: Session
    ) -> List[CampaignInfluencer]:
        """Get all unassigned influencers from a campaign list"""
        
        unassigned_influencers = db.query(CampaignInfluencer).filter(
            CampaignInfluencer.campaign_list_id == campaign_list_id,
            CampaignInfluencer.is_assigned_to_agent == False
        ).all()
        
        return unassigned_influencers
    
    @staticmethod
    async def _get_available_agents(
        campaign_list_id: uuid.UUID,
        preferred_agent_ids: Optional[List[uuid.UUID]],
        db: Session
    ) -> List[OutreachAgent]:
        """Get available agents for assignment based on company exclusivity rules"""
        
        campaign_list = db.query(CampaignList).join(
            CampaignList.campaign
        ).first()
        
        query = db.query(OutreachAgent).filter(
            OutreachAgent.is_available_for_assignment == True
        )
        
        if hasattr(campaign_list.campaign, 'company_id'):
            company_id = campaign_list.campaign.company_id
            query = query.filter(
                or_(
                    OutreachAgent.company_id == company_id,
                    and_(
                        OutreachAgent.company_id.is_(None),
                        OutreachAgent.is_company_exclusive == False
                    )
                )
            )
        
        if preferred_agent_ids:
            query = query.filter(OutreachAgent.id.in_(preferred_agent_ids))
        
        available_agents = query.all()
        return available_agents
    
    @staticmethod
    async def _get_agent_capacity(
        agent_id: uuid.UUID,
        campaign_list_id: uuid.UUID,
        db: Session
    ) -> Dict[str, Any]:
        """Calculate agent capacity using correct dual-limit logic"""
        
        max_concurrent = await BulkAssignmentService._get_setting_value(
            "max_concurrent_influencers", db, default=100
        )
        max_per_assignment = await BulkAssignmentService._get_setting_value(
            "max_influencers_per_assignment", db, default=20
        )
        
        # GLOBAL CAPACITY: Count only 'active' types across ALL assignments
        total_active_across_all_assignments = db.query(func.count(AssignedInfluencer.id)).join(
            AgentAssignment, AssignedInfluencer.agent_assignment_id == AgentAssignment.id
        ).filter(
            AgentAssignment.outreach_agent_id == agent_id,
            AgentAssignment.is_deleted == False,
            AssignedInfluencer.type == 'active'  # ONLY active types
        ).scalar() or 0
        
        global_available = max_concurrent - total_active_across_all_assignments
        
        # PER-ASSIGNMENT CAPACITY: Find existing assignment for this campaign list
        existing_assignment_for_list = db.query(AgentAssignment).filter(
            AgentAssignment.outreach_agent_id == agent_id,
            AgentAssignment.campaign_list_id == campaign_list_id,
            AgentAssignment.is_deleted == False
        ).first()
        
        available_capacity = 0
        existing_assignments_for_list = []
        assignment_status = "available"
        
        if existing_assignment_for_list:
            # Count ACTIVE influencers in this specific assignment
            active_count_in_assignment = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.agent_assignment_id == existing_assignment_for_list.id,
                AssignedInfluencer.type == 'active'
            ).count()
            
            # Total count for debugging (all types)
            total_count_in_assignment = db.query(AssignedInfluencer).filter(
                AssignedInfluencer.agent_assignment_id == existing_assignment_for_list.id
            ).count()
            
            logger.info(f"Agent {agent_id} assignment: active={active_count_in_assignment}, total={total_count_in_assignment}, limit={max_per_assignment}")
            
            # Per-assignment capacity based on ACTIVE count vs limit
            per_assignment_available = max_per_assignment - active_count_in_assignment
            
            if per_assignment_available > 0:
                # Has capacity in this assignment
                available_capacity = min(per_assignment_available, global_available)
                existing_assignments_for_list = [str(existing_assignment_for_list.id)]
                assignment_status = "available"
                logger.info(f"Agent {agent_id} has capacity: per_assignment={per_assignment_available}, global={global_available}, final={available_capacity}")
            else:
                # Assignment at capacity (20 active influencers)
                available_capacity = 0
                assignment_status = "at_limit"
                logger.info(f"Agent {agent_id} assignment at limit: {active_count_in_assignment} active influencers")
        else:
            # No existing assignment for this campaign list
            if global_available > 0:
                available_capacity = min(max_per_assignment, global_available)
                assignment_status = "available"
        
        return {
            "agent_id": str(agent_id),
            "current_influencers_count": total_active_across_all_assignments,  # Only active for display
            "max_concurrent_influencers": max_concurrent,
            "max_per_assignment": max_per_assignment,
            "available_capacity": max(0, available_capacity),
            "existing_assignments_for_list": existing_assignments_for_list,
            "can_accept_new": available_capacity > 0,
            "assignment_status": assignment_status
        }
    
    @staticmethod
    async def _calculate_optimal_agent_count(
        total_influencers: int,
        available_agents: int,
        max_per_assignment: int,
        agent_capacities: List[Tuple] = None
    ) -> int:
        """Calculate optimal number of agents for efficient distribution"""
        
        if total_influencers <= 0:
            return 0
        
        # If agent capacities are provided, use actual available capacity
        if agent_capacities:
            total_available_capacity = sum(info[1]["available_capacity"] for info in agent_capacities)
            
            # If we have enough total capacity, use all agents with capacity
            if total_available_capacity >= total_influencers:
                agents_with_capacity = len([info for info in agent_capacities if info[1]["available_capacity"] > 0])
                return min(agents_with_capacity, available_agents)
            else:
                # Use all available agents since we need maximum capacity
                return available_agents
        
        # Fallback to original logic if no capacity info provided
        min_agents_needed = math.ceil(total_influencers / max_per_assignment)
        min_agents_needed = min(min_agents_needed, available_agents)
        
        if total_influencers <= 5:
            return 1
        elif total_influencers <= 15:
            return min(2, min_agents_needed)
        elif total_influencers <= 30:
            return min(3, min_agents_needed)
        elif total_influencers <= 50:
            return min(4, min_agents_needed)
        else:
            reasonable_max = min(6, available_agents)
            return min(min_agents_needed, reasonable_max)
    
    @staticmethod
    async def _distribute_influencers(
        influencers: List[CampaignInfluencer],
        agents: List[OutreachAgent],
        max_per_assignment: int,
        strategy: str,
        force_new_assignments: bool,
        campaign_list_id: uuid.UUID,
        db: Session
    ) -> Dict[uuid.UUID, List[CampaignInfluencer]]:
        """Intelligent distribution with enhanced capacity management - FIXED agent selection"""
        
        total_influencers = len(influencers)
        distribution = {}
        
        agent_capacities = []
        agents_available = []
        agents_at_limit_with_non_active = []
        agents_at_limit = []
        
        for agent in agents:
            capacity_info = await BulkAssignmentService._get_agent_capacity(
                agent.id, campaign_list_id, db
            )
            
            if capacity_info["can_accept_new"]:
                if capacity_info["assignment_status"] == "available":
                    agents_available.append((agent, capacity_info))
                elif capacity_info["assignment_status"] == "at_limit_with_non_active":
                    agents_at_limit_with_non_active.append((agent, capacity_info))
                
                agent_capacities.append((agent, capacity_info))
            elif capacity_info["assignment_status"] == "at_limit":
                agents_at_limit.append((agent, capacity_info))
        
        if not agent_capacities:
            logger.warning("No agents with available capacity found")
            return distribution
        
        # Prioritize agents: available first, then at-limit with non-active
        prioritized_agents = agents_available + agents_at_limit_with_non_active
        
        if not prioritized_agents:
            logger.warning("All agents are at capacity with only active influencers")
            return distribution
        
        # FIXED: Pass agent capacities to get accurate optimal count
        optimal_agent_count = await BulkAssignmentService._calculate_optimal_agent_count(
            total_influencers, 
            len(prioritized_agents), 
            max_per_assignment,
            prioritized_agents  # Pass actual capacity info
        )
        
        agents_to_use = prioritized_agents[:optimal_agent_count]
        
        total_capacity = sum(info[1]["available_capacity"] for info in agents_to_use)
        
        logger.info(f"Distributing {total_influencers} influencers among {len(agents_to_use)} agents (optimal: {optimal_agent_count}, available: {len(prioritized_agents)}, total_capacity: {total_capacity})")
        
        # Log detailed capacity info for debugging
        for i, (agent, capacity_info) in enumerate(agents_to_use):
            logger.info(f"Agent {i+1} (ID: {agent.id}): capacity={capacity_info['available_capacity']}, status={capacity_info['assignment_status']}")
        
        if strategy == "round_robin":
            distribution = await BulkAssignmentService._distribute_round_robin(
                influencers, agents_to_use, distribution
            )
        elif strategy == "load_balanced":
            distribution = await BulkAssignmentService._distribute_load_balanced(
                influencers, agents_to_use, distribution
            )
        elif strategy == "manual":
            distribution = await BulkAssignmentService._distribute_manual(
                influencers, agents_to_use, distribution
            )
        else:
            logger.warning(f"Unknown strategy '{strategy}', defaulting to round_robin")
            distribution = await BulkAssignmentService._distribute_round_robin(
                influencers, agents_to_use, distribution
            )
        
        # Log final distribution
        for agent_id, assigned_influencers in distribution.items():
            logger.info(f"Agent {agent_id} assigned {len(assigned_influencers)} influencers")
        
        return distribution
    
    @staticmethod
    async def _distribute_round_robin(
        influencers: List[CampaignInfluencer],
        agent_capacities: List[Tuple],
        distribution: Dict[uuid.UUID, List[CampaignInfluencer]]
    ) -> Dict[uuid.UUID, List[CampaignInfluencer]]:
        """Distribute influencers evenly in round-robin fashion with capacity respect"""
        
        agent_capacities.sort(key=lambda x: (
            x[1]["assignment_status"] == "at_limit_with_non_active",
            -x[1]["available_capacity"]
        ))
        
        agent_index = 0
        available_agents = agent_capacities.copy()
        
        for influencer in influencers:
            if not available_agents:
                logger.warning("No more agents with capacity available")
                break
            
            agent, capacity_info = available_agents[agent_index]
            
            if agent.id not in distribution:
                distribution[agent.id] = []
            
            distribution[agent.id].append(influencer)
            
            if len(distribution[agent.id]) >= capacity_info["available_capacity"]:
                available_agents.pop(agent_index)
                if agent_index >= len(available_agents) and len(available_agents) > 0:
                    agent_index = 0
            else:
                agent_index = (agent_index + 1) % len(available_agents)
        
        return distribution
    
    @staticmethod
    async def _distribute_load_balanced(
        influencers: List[CampaignInfluencer],
        agent_capacities: List[Tuple],
        distribution: Dict[uuid.UUID, List[CampaignInfluencer]]
    ) -> Dict[uuid.UUID, List[CampaignInfluencer]]:
        """Distribute influencers to agents with highest available capacity first"""
        
        available_agents = agent_capacities.copy()
        
        for influencer in influencers:
            if not available_agents:
                break
            
            available_agents.sort(key=lambda x: (
                x[1]["assignment_status"] == "at_limit_with_non_active",
                -(x[1]["available_capacity"] - len(distribution.get(x[0].id, [])))
            ))
            
            agent, capacity_info = available_agents[0]
            
            if agent.id not in distribution:
                distribution[agent.id] = []
            
            distribution[agent.id].append(influencer)
            
            current_assigned = len(distribution[agent.id])
            if current_assigned >= capacity_info["available_capacity"]:
                available_agents.pop(0)
        
        return distribution
    
    @staticmethod
    async def _distribute_manual(
        influencers: List[CampaignInfluencer],
        agent_capacities: List[Tuple],
        distribution: Dict[uuid.UUID, List[CampaignInfluencer]]
    ) -> Dict[uuid.UUID, List[CampaignInfluencer]]:
        """Distribute influencers using manual strategy respecting preferred order"""
        
        available_agents = agent_capacities.copy()
        agent_index = 0
        
        for influencer in influencers:
            if not available_agents:
                break
            
            agent, capacity_info = available_agents[agent_index]
            
            if agent.id not in distribution:
                distribution[agent.id] = []
            
            distribution[agent.id].append(influencer)
            
            if len(distribution[agent.id]) >= capacity_info["available_capacity"]:
                available_agents.pop(agent_index)
                if agent_index >= len(available_agents) and len(available_agents) > 0:
                    agent_index = 0
            else:
                agent_index = (agent_index + 1) % len(available_agents)
        
        return distribution
    
    @staticmethod
    async def _assign_single_influencer_to_agent(
        campaign_influencer_id: uuid.UUID,
        agent_id: uuid.UUID,
        existing_assignment_id: Optional[uuid.UUID],
        campaign_list_id: uuid.UUID,
        db: Session
    ) -> Optional[AssignedInfluencer]:
        """Assign a single influencer to an agent for reassignment scenarios"""
        
        try:
            if existing_assignment_id:
                agent_assignment = db.query(AgentAssignment).filter(
                    AgentAssignment.id == existing_assignment_id
                ).first()
            else:
                agent_assignment = db.query(AgentAssignment).filter(
                    AgentAssignment.outreach_agent_id == agent_id,
                    AgentAssignment.campaign_list_id == campaign_list_id,
                    AgentAssignment.is_deleted == False
                ).first()
                
                if not agent_assignment:
                    active_status = db.query(Status).filter(
                        Status.model == "agent_assignment",
                        Status.name == "active"
                    ).first()
                    
                    agent_assignment = AgentAssignment(
                        outreach_agent_id=agent_id,
                        campaign_list_id=campaign_list_id,
                        status_id=active_status.id if active_status else None,
                        assigned_at=datetime.utcnow()
                    )
                    db.add(agent_assignment)
                    db.flush()
            
            assigned_status = db.query(Status).filter(
                Status.model == "assigned_influencer",
                Status.name == "assigned"
            ).first()
            
            assigned_influencer = AssignedInfluencer(
                campaign_influencer_id=campaign_influencer_id,
                agent_assignment_id=agent_assignment.id,
                status_id=assigned_status.id if assigned_status else None,
                type='active',
                assigned_at=datetime.utcnow()
            )
            db.add(assigned_influencer)
            
            campaign_influencer = db.query(CampaignInfluencer).filter(
                CampaignInfluencer.id == campaign_influencer_id
            ).first()
            campaign_influencer.is_assigned_to_agent = True
            
            return assigned_influencer
            
        except Exception as e:
            logger.error(f"Error in _assign_single_influencer_to_agent: {str(e)}")
            return None
    
    @staticmethod
    async def _find_best_agent_for_reassignment(
        campaign_influencer_id: uuid.UUID,
        exclude_agent_id: uuid.UUID,
        campaign_list_id: uuid.UUID,
        prefer_existing_assignments: bool,
        db: Session
    ) -> Tuple[Optional[OutreachAgent], Optional[uuid.UUID]]:
        """Find the best agent for reassignment with priority logic"""
        
        if prefer_existing_assignments:
            existing_agents = db.query(OutreachAgent).join(AgentAssignment).filter(
                AgentAssignment.campaign_list_id == campaign_list_id,
                AgentAssignment.is_deleted == False,
                OutreachAgent.id != exclude_agent_id,
                OutreachAgent.is_available_for_assignment == True
            ).all()
            
            for agent in existing_agents:
                capacity_info = await BulkAssignmentService._get_agent_capacity(
                    agent.id, campaign_list_id, db
                )
                if capacity_info["can_accept_new"]:
                    existing_assignment_id = (
                        capacity_info["existing_assignments_for_list"][0] 
                        if capacity_info["existing_assignments_for_list"] 
                        else None
                    )
                    return agent, uuid.UUID(existing_assignment_id) if existing_assignment_id else None
        
        available_agents = await BulkAssignmentService._get_available_agents(
            campaign_list_id, None, db
        )
        available_agents = [a for a in available_agents if a.id != exclude_agent_id]
        
        for agent in available_agents:
            capacity_info = await BulkAssignmentService._get_agent_capacity(
                agent.id, campaign_list_id, db
            )
            if capacity_info["can_accept_new"]:
                return agent, None
        
        return None, None
    
    @staticmethod
    async def _create_assignment_history(
        campaign_influencer_id: uuid.UUID,
        agent_assignment_id: uuid.UUID,
        from_agent_id: uuid.UUID,
        to_agent_id: uuid.UUID,
        attempts_before: int,
        reason_code: str,
        triggered_by: str,
        reassigned_by: Optional[uuid.UUID],
        notes: Optional[str],
        db: Session
    ) -> InfluencerAssignmentHistory:
        """Create assignment history record for audit trail"""
        
        reason = db.query(Status).filter(
            Status.model == "reassignment_reason",
            Status.name == reason_code
        ).first()
        
        history = InfluencerAssignmentHistory(
            campaign_influencer_id=campaign_influencer_id,
            agent_assignment_id=agent_assignment_id,
            from_outreach_agent_id=from_agent_id,
            to_outreach_agent_id=to_agent_id,
            reassignment_reason_id=reason.id if reason else None,
            attempts_before_reassignment=attempts_before,
            reassignment_triggered_by=triggered_by,
            reassigned_by=reassigned_by,
            reassignment_notes=notes
        )
        
        db.add(history)
        db.flush()
        
        return history
    
    @staticmethod
    async def _update_all_agent_counters(
        agent_ids: List[uuid.UUID],
        db: Session
    ) -> None:
        """Update counters for all agents with correct separate logic"""
        
        try:
            for agent_id in agent_ids:
                # First update all assignment counts for this agent (total counts)
                agent_assignments = db.query(AgentAssignment).filter(
                    AgentAssignment.outreach_agent_id == agent_id,
                    AgentAssignment.is_deleted == False
                ).all()
                
                for assignment in agent_assignments:
                    # Assignment counter: ALL types
                    total_count = db.query(AssignedInfluencer).filter(
                        AssignedInfluencer.agent_assignment_id == assignment.id
                    ).count()
                    
                    assignment.assigned_influencers_count = total_count
                
                # Now update agent counters (only active types)
                agent = db.query(OutreachAgent).filter(
                    OutreachAgent.id == agent_id
                ).first()
                
                if agent:
                    # Agent counter: ONLY active types across all assignments
                    total_active_influencers = db.query(func.count(AssignedInfluencer.id)).join(
                        AgentAssignment, AssignedInfluencer.agent_assignment_id == AgentAssignment.id
                    ).filter(
                        AgentAssignment.outreach_agent_id == agent_id,
                        AgentAssignment.is_deleted == False,
                        AssignedInfluencer.type == 'active'  # ONLY active types
                    ).scalar() or 0
                    
                    total_lists = db.query(func.count(AgentAssignment.id.distinct())).filter(
                        AgentAssignment.outreach_agent_id == agent_id,
                        AgentAssignment.is_deleted == False,
                        AgentAssignment.assigned_influencers_count > 0
                    ).scalar() or 0
                    
                    old_agent_count = agent.active_influencers_count
                    old_lists = agent.active_lists_count
                    
                    agent.active_influencers_count = total_active_influencers  # ONLY active
                    agent.active_lists_count = total_lists
                    
                    logger.info(f"Updated agent {agent_id} counters: active_influencers {old_agent_count}→{total_active_influencers}, lists {old_lists}→{total_lists}")
                
        except Exception as e:
            logger.error(f"Error in _update_all_agent_counters: {str(e)}")
    
    @staticmethod
    async def _get_setting_value(
        setting_key: str,
        db: Session,
        default: Any = None
    ) -> Any:
        """Get setting value from database with type conversion"""
        
        setting = db.query(Settings).filter(
            Settings.setting_key == setting_key
        ).first()
        
        if setting:
            if setting.setting_type == "integer":
                return int(setting.setting_value)
            elif setting.setting_type == "boolean":
                return setting.setting_value.lower() == "true"
            else:
                return setting.setting_value
        
        return default