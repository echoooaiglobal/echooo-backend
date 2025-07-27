# app/Services/CounterSyncService.py - Helper service for counter synchronization

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import uuid

from app.Models.outreach_agents import OutreachAgent
from app.Models.agent_assignments import AgentAssignment
from app.Models.assigned_influencers import AssignedInfluencer
from app.Utils.Logger import logger

class CounterSyncService:
    """Service for synchronizing counters across related tables"""
    
    @staticmethod
    async def sync_all_agent_counters(db: Session) -> dict:
        """
        Synchronize all agent counters with actual data
        Use this if counters get out of sync
        """
        
        try:
            agents = db.query(OutreachAgent).all()
            updated_agents = 0
            
            for agent in agents:
                # Calculate active_influencers_count
                active_influencers = db.query(func.sum(AgentAssignment.assigned_influencers_count)).filter(
                    AgentAssignment.outreach_agent_id == agent.id,
                    AgentAssignment.is_deleted == False
                ).scalar() or 0
                
                # Calculate active_lists_count
                active_lists = db.query(func.count(AgentAssignment.id.distinct())).filter(
                    AgentAssignment.outreach_agent_id == agent.id,
                    AgentAssignment.is_deleted == False,
                    AgentAssignment.assigned_influencers_count > 0
                ).scalar() or 0
                
                # Update if different
                if (agent.active_influencers_count != active_influencers or 
                    agent.active_lists_count != active_lists):
                    
                    old_influencers = agent.active_influencers_count
                    old_lists = agent.active_lists_count
                    
                    agent.active_influencers_count = active_influencers
                    agent.active_lists_count = active_lists
                    updated_agents += 1
                    
                    logger.info(f"Updated agent {agent.id}: influencers {old_influencers}→{active_influencers}, lists {old_lists}→{active_lists}")
            
            db.commit()
            
            return {
                "success": True,
                "updated_agents": updated_agents,
                "total_agents": len(agents),
                "message": f"Synchronized counters for {updated_agents} agents"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in sync_all_agent_counters: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def sync_agent_assignment_counters(db: Session) -> dict:
        """
        Synchronize all agent assignment counters with actual assigned influencers
        """
        
        try:
            assignments = db.query(AgentAssignment).filter(
                AgentAssignment.is_deleted == False
            ).all()
            
            updated_assignments = 0
            
            for assignment in assignments:
                # Calculate actual assigned influencers count
                actual_count = db.query(AssignedInfluencer).filter(
                    AssignedInfluencer.agent_assignment_id == assignment.id,
                    AssignedInfluencer.type == 'active'
                ).count()
                
                # Update if different
                if assignment.assigned_influencers_count != actual_count:
                    old_count = assignment.assigned_influencers_count
                    assignment.assigned_influencers_count = actual_count
                    updated_assignments += 1
                    
                    logger.info(f"Updated assignment {assignment.id}: {old_count}→{actual_count}")
            
            db.commit()
            
            return {
                "success": True,
                "updated_assignments": updated_assignments,
                "total_assignments": len(assignments),
                "message": f"Synchronized counters for {updated_assignments} assignments"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in sync_agent_assignment_counters: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def sync_single_agent_counters(agent_id: uuid.UUID, db: Session) -> dict:
        """
        Synchronize counters for a single agent
        """
        
        try:
            agent = db.query(OutreachAgent).filter(OutreachAgent.id == agent_id).first()
            
            if not agent:
                return {
                    "success": False,
                    "error": "Agent not found"
                }
            
            # Calculate active_influencers_count
            active_influencers = db.query(func.sum(AgentAssignment.assigned_influencers_count)).filter(
                AgentAssignment.outreach_agent_id == agent.id,
                AgentAssignment.is_deleted == False
            ).scalar() or 0
            
            # Calculate active_lists_count
            active_lists = db.query(func.count(AgentAssignment.id.distinct())).filter(
                AgentAssignment.outreach_agent_id == agent.id,
                AgentAssignment.is_deleted == False,
                AgentAssignment.assigned_influencers_count > 0
            ).scalar() or 0
            
            # Update counters
            old_influencers = agent.active_influencers_count
            old_lists = agent.active_lists_count
            
            agent.active_influencers_count = active_influencers
            agent.active_lists_count = active_lists
            
            db.commit()
            
            return {
                "success": True,
                "agent_id": str(agent_id),
                "changes": {
                    "influencers": f"{old_influencers}→{active_influencers}",
                    "lists": f"{old_lists}→{active_lists}"
                },
                "message": f"Synchronized counters for agent {agent_id}"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in sync_single_agent_counters: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def validate_counter_integrity(db: Session) -> dict:
        """
        Validate that all counters are accurate without updating them
        Returns discrepancies found
        """
        
        try:
            discrepancies = []
            
            # Check agent counters
            agents = db.query(OutreachAgent).all()
            
            for agent in agents:
                # Check active_influencers_count
                actual_influencers = db.query(func.sum(AgentAssignment.assigned_influencers_count)).filter(
                    AgentAssignment.outreach_agent_id == agent.id,
                    AgentAssignment.is_deleted == False
                ).scalar() or 0
                
                if agent.active_influencers_count != actual_influencers:
                    discrepancies.append({
                        "type": "agent_influencers_count",
                        "agent_id": str(agent.id),
                        "stored": agent.active_influencers_count,
                        "actual": actual_influencers
                    })
                
                # Check active_lists_count
                actual_lists = db.query(func.count(AgentAssignment.id.distinct())).filter(
                    AgentAssignment.outreach_agent_id == agent.id,
                    AgentAssignment.is_deleted == False,
                    AgentAssignment.assigned_influencers_count > 0
                ).scalar() or 0
                
                if agent.active_lists_count != actual_lists:
                    discrepancies.append({
                        "type": "agent_lists_count",
                        "agent_id": str(agent.id),
                        "stored": agent.active_lists_count,
                        "actual": actual_lists
                    })
            
            # Check assignment counters
            assignments = db.query(AgentAssignment).filter(
                AgentAssignment.is_deleted == False
            ).all()
            
            for assignment in assignments:
                actual_count = db.query(AssignedInfluencer).filter(
                    AssignedInfluencer.agent_assignment_id == assignment.id,
                    AssignedInfluencer.type == 'active'
                ).count()
                
                if assignment.assigned_influencers_count != actual_count:
                    discrepancies.append({
                        "type": "assignment_influencers_count",
                        "assignment_id": str(assignment.id),
                        "agent_id": str(assignment.outreach_agent_id),
                        "stored": assignment.assigned_influencers_count,
                        "actual": actual_count
                    })
            
            return {
                "success": True,
                "discrepancies_found": len(discrepancies),
                "discrepancies": discrepancies,
                "is_valid": len(discrepancies) == 0
            }
            
        except Exception as e:
            logger.error(f"Error in validate_counter_integrity: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }