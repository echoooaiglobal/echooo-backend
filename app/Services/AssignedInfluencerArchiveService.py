# app/Services/AssignedInfluencerArchiveService.py - Enhanced with range processing

"""
Enhanced service for automatically archiving assigned influencers
INCLUDES: Range-based processing for backlog management
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.Models.assigned_influencers import AssignedInfluencer
from app.Models.statuses import Status
from app.Utils.Logger import logger


class AssignedInfluencerArchiveService:
    """
    Enhanced service for handling automatic archival of assigned influencers
    INCLUDES: Backlog management and range-based processing
    """

    @staticmethod
    async def find_influencers_to_archive(
        db: Session,
        hours_threshold: int = 48,
        tolerance_hours: float = 0.5
    ) -> List[AssignedInfluencer]:
        """
        Find assigned influencers that should be archived based on criteria
        FIXED: Now properly filters by attempts_made >= 3
        """
        try:
            # Calculate time boundaries
            now = datetime.now(timezone.utc)
            min_time = now - timedelta(hours=hours_threshold + tolerance_hours)
            max_time = now - timedelta(hours=hours_threshold - tolerance_hours)
            
            logger.info(f"Finding influencers to archive with criteria:")
            logger.info(f"  - attempts_made >= 3")  # FIXED: Updated log message
            logger.info(f"  - archived_at IS NULL")
            logger.info(f"  - type != 'archived'")
            logger.info(f"  - last_contacted_at between {min_time} and {max_time}")
            
            # Query for influencers meeting criteria
            query = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.attempts_made >= 3,  # FIXED: Changed from == 3 to >= 3
                    AssignedInfluencer.archived_at.is_(None),
                    AssignedInfluencer.type != 'archived',
                    AssignedInfluencer.last_contacted_at.isnot(None),
                    AssignedInfluencer.last_contacted_at >= min_time,
                    AssignedInfluencer.last_contacted_at <= max_time
                )
            )
            
            influencers = query.all()
            
            logger.info(f"Found {len(influencers)} influencers eligible for archiving")
            
            return influencers
            
        except Exception as e:
            logger.error(f"Error finding influencers to archive: {str(e)}")
            raise

    @staticmethod
    async def find_influencers_in_range(
        db: Session,
        min_hours: float,
        max_hours: int,
        tolerance_hours: float = 0.5
    ) -> List[AssignedInfluencer]:
        """
        ENHANCED: Find assigned influencers within a specific time range
        FIXED: Now properly filters by attempts_made >= 3
        
        Args:
            db: Database session
            min_hours: Minimum hours since last contact
            max_hours: Maximum hours since last contact
            tolerance_hours: Tolerance window in hours
            
        Returns:
            List of AssignedInfluencer objects in the specified range
        """
        try:
            # Calculate time boundaries
            now = datetime.now(timezone.utc)
            min_time = now - timedelta(hours=max_hours + tolerance_hours)
            max_time = now - timedelta(hours=min_hours)
            
            logger.info(f"Finding influencers in range {min_hours}h to {max_hours}h:")
            logger.info(f"  - attempts_made >= 3")  # FIXED: Updated log message
            logger.info(f"  - archived_at IS NULL")
            logger.info(f"  - type != 'archived'")
            logger.info(f"  - last_contacted_at between {min_time} and {max_time}")
            
            # Query for influencers meeting criteria
            query = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.attempts_made >= 3,  # FIXED: Changed from == 3 to >= 3
                    AssignedInfluencer.archived_at.is_(None),
                    AssignedInfluencer.type != 'archived',
                    AssignedInfluencer.last_contacted_at.isnot(None),
                    AssignedInfluencer.last_contacted_at >= min_time,
                    AssignedInfluencer.last_contacted_at <= max_time
                )
            )
            
            influencers = query.all()
            
            logger.info(f"Found {len(influencers)} influencers in range {min_hours}h-{max_hours}h")
            
            return influencers
            
        except Exception as e:
            logger.error(f"Error finding influencers in range: {str(e)}")
            raise

    @staticmethod
    async def count_influencers_in_range(
        db: Session,
        min_hours: float,
        max_hours: int,
        tolerance_hours: float = 0.5
    ) -> int:
        """
        ENHANCED: Count assigned influencers within a specific time range
        """
        try:
            now = datetime.now(timezone.utc)
            min_time = now - timedelta(hours=max_hours + tolerance_hours)
            max_time = now - timedelta(hours=min_hours)
            
            count = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.attempts_made >= 3,
                    AssignedInfluencer.archived_at.is_(None),
                    AssignedInfluencer.type != 'archived',
                    AssignedInfluencer.last_contacted_at.isnot(None),
                    AssignedInfluencer.last_contacted_at >= min_time,
                    AssignedInfluencer.last_contacted_at <= max_time
                )
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting influencers in range: {str(e)}")
            return 0

    @staticmethod
    async def get_archived_status_id(db: Session) -> Optional[uuid.UUID]:
        """Get the status ID for 'archived' status in assigned_influencer model"""
        try:
            archived_status = db.query(Status).filter(
                and_(
                    Status.model == 'assigned_influencer',
                    Status.name == 'archived'
                )
            ).first()
            
            if not archived_status:
                logger.warning("Archived status not found for assigned_influencer model")
                return None
                
            return archived_status.id
            
        except Exception as e:
            logger.error(f"Error getting archived status ID: {str(e)}")
            raise

    @staticmethod
    async def archive_influencer_batch(
        db: Session,
        influencers: List[AssignedInfluencer],
        archived_status_id: uuid.UUID
    ) -> Tuple[int, List[str]]:
        """Archive a batch of influencers efficiently using bulk update"""
        try:
            if not influencers:
                return 0, []
                
            influencer_ids = [str(inf.id) for inf in influencers]
            now = datetime.now(timezone.utc)
            
            # Use bulk update for better performance
            result = db.execute(
                text("""
                    UPDATE assigned_influencers 
                    SET 
                        type = 'archived',
                        archived_at = :archived_at,
                        status_id = :status_id,
                        updated_at = :updated_at
                    WHERE id = ANY(:influencer_ids)
                    AND archived_at IS NULL
                """),
                {
                    'archived_at': now,
                    'status_id': str(archived_status_id),
                    'updated_at': now,
                    'influencer_ids': influencer_ids
                }
            )
            
            updated_count = result.rowcount
            db.commit()
            
            logger.info(f"Successfully archived {updated_count} influencers in batch")
            
            return updated_count, []
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error during batch archive: {str(e)}")
            return 0, [str(e)]
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error during batch archive: {str(e)}")
            return 0, [str(e)]

    @staticmethod
    async def process_auto_archive(
        db: Session,
        batch_size: int = 1000,
        hours_threshold: int = 48,
        tolerance_hours: float = 0.5
    ) -> Dict[str, Any]:
        """Main method to process automatic archiving of assigned influencers"""
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info("Starting automatic influencer archiving process")
            
            # Get archived status ID
            archived_status_id = await AssignedInfluencerArchiveService.get_archived_status_id(db)
            if not archived_status_id:
                return {
                    "success": False,
                    "error": "Archived status not found for assigned_influencer model",
                    "processed": 0,
                    "archived": 0,
                    "errors": ["Missing archived status in database"]
                }
            
            # Find influencers to archive
            influencers_to_archive = await AssignedInfluencerArchiveService.find_influencers_to_archive(
                db, hours_threshold, tolerance_hours
            )
            
            if not influencers_to_archive:
                return {
                    "success": True,
                    "message": "No influencers found for archiving",
                    "processed": 0,
                    "archived": 0,
                    "errors": [],
                    "execution_time_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
                }
            
            # Limit batch size to prevent overwhelming the database
            influencers_to_process = influencers_to_archive[:batch_size]
            
            if len(influencers_to_archive) > batch_size:
                logger.warning(f"Found {len(influencers_to_archive)} influencers, processing only {batch_size} in this batch")
            
            # Process archiving
            archived_count, errors = await AssignedInfluencerArchiveService.archive_influencer_batch(
                db, influencers_to_process, archived_status_id
            )
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": f"Processed {len(influencers_to_process)} influencers, archived {archived_count}",
                "processed": len(influencers_to_process),
                "archived": archived_count,
                "errors": errors,
                "execution_time_seconds": execution_time,
                "remaining_candidates": max(0, len(influencers_to_archive) - batch_size)
            }
            
            logger.info(f"Auto-archive process completed: {result}")
            return result
            
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Error in auto-archive process: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processed": 0,
                "archived": 0,
                "errors": [str(e)],
                "execution_time_seconds": execution_time
            }

    @staticmethod
    async def process_range_archive(
        db: Session,
        min_hours: float,
        max_hours: int,
        batch_size: int = 1000,
        tolerance_hours: float = 0.5
    ) -> Dict[str, Any]:
        """
        ENHANCED: Process archiving for influencers within a specific time range
        
        This is useful for:
        - Backlog processing when server was down
        - Processing very old records
        - Custom archiving scenarios
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Starting range-based archiving: {min_hours}h to {max_hours}h")
            
            # Get archived status ID
            archived_status_id = await AssignedInfluencerArchiveService.get_archived_status_id(db)
            if not archived_status_id:
                return {
                    "success": False,
                    "error": "Archived status not found for assigned_influencer model",
                    "processed": 0,
                    "archived": 0,
                    "errors": ["Missing archived status in database"]
                }
            
            # Find influencers in range
            influencers_to_archive = await AssignedInfluencerArchiveService.find_influencers_in_range(
                db, min_hours, max_hours, tolerance_hours
            )
            
            if not influencers_to_archive:
                return {
                    "success": True,
                    "message": f"No influencers found in range {min_hours}h-{max_hours}h",
                    "processed": 0,
                    "archived": 0,
                    "errors": [],
                    "execution_time_seconds": (datetime.now(timezone.utc) - start_time).total_seconds(),
                    "time_range": {"min_hours": min_hours, "max_hours": max_hours}
                }
            
            # Limit batch size
            influencers_to_process = influencers_to_archive[:batch_size]
            
            if len(influencers_to_archive) > batch_size:
                logger.warning(f"Found {len(influencers_to_archive)} influencers in range, processing only {batch_size} in this batch")
            
            # Process archiving
            archived_count, errors = await AssignedInfluencerArchiveService.archive_influencer_batch(
                db, influencers_to_process, archived_status_id
            )
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": f"Range archiving completed: {min_hours}h-{max_hours}h, archived {archived_count}",
                "processed": len(influencers_to_process),
                "archived": archived_count,
                "errors": errors,
                "execution_time_seconds": execution_time,
                "remaining_candidates": max(0, len(influencers_to_archive) - batch_size),
                "time_range": {"min_hours": min_hours, "max_hours": max_hours}
            }
            
            logger.info(f"Range archive process completed: {result}")
            return result
            
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Error in range archive process: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processed": 0,
                "archived": 0,
                "errors": [str(e)],
                "execution_time_seconds": execution_time,
                "time_range": {"min_hours": min_hours, "max_hours": max_hours}
            }

    @staticmethod
    async def get_archive_candidates_count(
        db: Session,
        hours_threshold: int = 48,
        tolerance_hours: float = 0.5
    ) -> int:
        """
        Get count of influencers eligible for archiving without loading full objects
        FIXED: Now properly filters by attempts_made >= 3
        """
        try:
            now = datetime.now(timezone.utc)
            min_time = now - timedelta(hours=hours_threshold + tolerance_hours)
            max_time = now - timedelta(hours=hours_threshold - tolerance_hours)
            
            count = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.attempts_made >= 3,  # FIXED: Changed from == 3 to >= 3
                    AssignedInfluencer.archived_at.is_(None),
                    AssignedInfluencer.type != 'archived',
                    AssignedInfluencer.last_contacted_at.isnot(None),
                    AssignedInfluencer.last_contacted_at >= min_time,
                    AssignedInfluencer.last_contacted_at <= max_time
                )
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting archive candidates count: {str(e)}")
            return 0

    @staticmethod
    async def get_backlog_analysis(db: Session) -> Dict[str, Any]:
        """
        ENHANCED: Analyze backlog of records that should have been archived
        
        This helps you understand the scope of missed archiving
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Define age brackets
            brackets = [
                {"name": "Regular (48h-7d)", "min_hours": 48, "max_hours": 24*7},
                {"name": "Extended (7d-30d)", "min_hours": 24*7, "max_hours": 24*30},
                {"name": "Old (30d-90d)", "min_hours": 24*30, "max_hours": 24*90},
                {"name": "Very Old (90d+)", "min_hours": 24*90, "max_hours": 24*365}
            ]
            
            analysis = {
                "total_candidates": 0,
                "brackets": [],
                "oldest_record": None,
                "analysis_timestamp": now.isoformat()
            }
            
            for bracket in brackets:
                # FIXED: Use the proper method that includes attempts_made = 3 filter
                count = await AssignedInfluencerArchiveService.count_influencers_in_range(
                    db, bracket["min_hours"], bracket["max_hours"]
                )
                
                analysis["brackets"].append({
                    "name": bracket["name"],
                    "count": count,
                    "min_hours": bracket["min_hours"],
                    "max_hours": bracket["max_hours"],
                    "age_description": f"{bracket['min_hours']/24:.1f} to {bracket['max_hours']/24:.1f} days old"
                })
                
                analysis["total_candidates"] += count
            
            # FIXED: Find oldest record with proper filtering (attempts_made = 3)
            oldest_record = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.attempts_made >= 3,  # FIXED: Use >= 3 instead of == 3
                    AssignedInfluencer.archived_at.is_(None),
                    AssignedInfluencer.type != 'archived',
                    AssignedInfluencer.last_contacted_at.isnot(None)
                )
            ).order_by(AssignedInfluencer.last_contacted_at.asc()).first()
            
            if oldest_record:
                age_hours = (now - oldest_record.last_contacted_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                analysis["oldest_record"] = {
                    "id": str(oldest_record.id),
                    "last_contacted_at": oldest_record.last_contacted_at.isoformat(),
                    "age_hours": round(age_hours, 1),
                    "age_days": round(age_hours / 24, 1),
                    "attempts_made": oldest_record.attempts_made  # ADDED: Show attempts_made for verification
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing backlog: {str(e)}")
            return {
                "error": str(e),
                "total_candidates": 0,
                "brackets": [],
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }

    @staticmethod
    async def emergency_cleanup(
        db: Session,
        max_age_days: int = 90,
        batch_size: int = 2000
    ) -> Dict[str, Any]:
        """
        ENHANCED: Emergency cleanup for very old records
        
        Use this when you have a large backlog that needs immediate attention
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.warning(f"Starting emergency cleanup for records older than {max_age_days} days")
            
            # Get archived status ID
            archived_status_id = await AssignedInfluencerArchiveService.get_archived_status_id(db)
            if not archived_status_id:
                return {
                    "success": False,
                    "error": "Archived status not found",
                    "processed": 0,
                    "archived": 0
                }
            
            # Find very old records
            max_hours = 24 * max_age_days
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(hours=max_hours)
            
            # Get count first
            old_count = db.query(AssignedInfluencer).filter(
                and_(
                    AssignedInfluencer.attempts_made >= 3,
                    AssignedInfluencer.archived_at.is_(None),
                    AssignedInfluencer.type != 'archived',
                    AssignedInfluencer.last_contacted_at.isnot(None),
                    AssignedInfluencer.last_contacted_at <= cutoff_time
                )
            ).count()
            
            if old_count == 0:
                return {
                    "success": True,
                    "message": f"No records older than {max_age_days} days found",
                    "processed": 0,
                    "archived": 0,
                    "execution_time_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
                }
            
            logger.warning(f"Found {old_count} records older than {max_age_days} days")
            
            # Process in batches
            total_archived = 0
            total_processed = 0
            
            while True:
                # Get batch
                old_records = db.query(AssignedInfluencer).filter(
                    and_(
                        AssignedInfluencer.attempts_made >= 3,
                        AssignedInfluencer.archived_at.is_(None),
                        AssignedInfluencer.type != 'archived',
                        AssignedInfluencer.last_contacted_at.isnot(None),
                        AssignedInfluencer.last_contacted_at <= cutoff_time
                    )
                ).limit(batch_size).all()
                
                if not old_records:
                    break
                
                # Archive batch
                archived_count, errors = await AssignedInfluencerArchiveService.archive_influencer_batch(
                    db, old_records, archived_status_id
                )
                
                total_processed += len(old_records)
                total_archived += archived_count
                
                logger.info(f"Emergency cleanup batch: processed {len(old_records)}, archived {archived_count}")
                
                # Safety break to prevent infinite loops
                if len(old_records) < batch_size:
                    break
            
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            result = {
                "success": True,
                "message": f"Emergency cleanup completed: archived {total_archived} old records",
                "processed": total_processed,
                "archived": total_archived,
                "execution_time_seconds": execution_time,
                "max_age_days": max_age_days,
                "cleanup_type": "emergency"
            }
            
            logger.warning(f"Emergency cleanup completed: {result}")
            return result
            
        except Exception as e:
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.error(f"Error in emergency cleanup: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processed": 0,
                "archived": 0,
                "execution_time_seconds": execution_time,
                "cleanup_type": "emergency"
            }