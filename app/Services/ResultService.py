# app/Services/ResultService.py

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, desc, asc
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
from math import ceil

from app.Models.results import Result
from app.Models.campaigns import Campaign
from app.Utils.Logger import logger
import uuid

class ResultService:
    """Service for managing campaign results"""

    @staticmethod
    async def get_all_results(
        db: Session, 
        page: int = 1, 
        per_page: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> Tuple[List[Result], int]:
        """
        Get all results with pagination and sorting
        
        Args:
            db: Database session
            page: Page number (1-indexed)
            per_page: Results per page
            sort_by: Column to sort by
            sort_order: Sort direction (asc/desc)
            
        Returns:
            Tuple[List[Result], int]: List of results and total count
        """
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Build sort criteria
            sort_column = getattr(Result, sort_by, Result.created_at)
            order = desc(sort_column) if sort_order.lower() == "desc" else asc(sort_column)
            
            # Get total count
            total = db.query(Result).count()
            
            # Get results with pagination and sorting - avoid loading campaign relationship
            results = db.query(Result).order_by(order).offset(offset).limit(per_page).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_all_results: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_all_results: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def get_result_by_id(result_id: uuid.UUID, db: Session) -> Result:
        """
        Get a result by ID
        
        Args:
            result_id: ID of the result
            db: Database session
            
        Returns:
            Result: The result if found
            
        Raises:
            HTTPException: If result not found
        """
        try:
            result = db.query(Result).filter(Result.id == result_id).first()
            
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Result with ID {result_id} not found"
                )
            
            return result
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_result_by_id: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_result_by_id: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def get_results_by_campaign(
        campaign_id: uuid.UUID, 
        db: Session,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Result], int]:
        """
        Get all results for a specific campaign
        
        Args:
            campaign_id: ID of the campaign
            db: Database session
            page: Page number (1-indexed)
            per_page: Results per page
            
        Returns:
            Tuple[List[Result], int]: List of results and total count
        """
        try:
            # Verify campaign exists
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campaign with ID {campaign_id} not found"
                )
            
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get total count for this campaign
            total = db.query(Result).filter(Result.campaign_id == campaign_id).count()
            
            # Get results with pagination - avoid loading campaign relationship to prevent datetime issues
            # results = db.query(Result).filter(
            #     Result.campaign_id == campaign_id
            # ).order_by(desc(Result.created_at)).offset(offset).limit(per_page).all()

            results = db.query(Result).filter(
                Result.campaign_id == campaign_id
            ).order_by(desc(Result.created_at)).offset(offset).all()
            
            return results, total
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_results_by_campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_results_by_campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def get_results_by_influencer(
        influencer_username: str, 
        db: Session,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Result], int]:
        """
        Get all results for a specific influencer
        
        Args:
            influencer_username: Username of the influencer
            db: Database session
            page: Page number (1-indexed)
            per_page: Results per page
            
        Returns:
            Tuple[List[Result], int]: List of results and total count
        """
        try:
            # Calculate offset
            offset = (page - 1) * per_page
            
            # Get total count for this influencer
            total = db.query(Result).filter(
                Result.influencer_username == influencer_username
            ).count()
            
            # Get results with pagination - avoid loading campaign relationship
            results = db.query(Result).filter(
                Result.influencer_username == influencer_username
            ).order_by(desc(Result.created_at)).offset(offset).limit(per_page).all()
            
            return results, total
            
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_results_by_influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_results_by_influencer: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def create_result(result_data: Dict[str, Any], db: Session) -> Result:
        """
        Create a new result
        
        Args:
            result_data: Dictionary containing result data
            db: Database session
            
        Returns:
            Result: The created result
        """
        try:
            # Verify campaign exists
            campaign_id = uuid.UUID(result_data['campaign_id'])
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campaign with ID {campaign_id} not found"
                )
            
            # Create new result
            result = Result(
                campaign_id=campaign_id,
                user_ig_id=result_data.get('user_ig_id'),
                full_name=result_data.get('full_name'),
                influencer_username=result_data['influencer_username'],
                profile_pic_url=result_data.get('profile_pic_url'),
                post_id=result_data.get('post_id'),
                title=result_data.get('title'),
                views_count=result_data.get('views_count'),
                likes_count=result_data.get('likes_count'),
                plays_count=result_data.get('plays_count'),
                comments_count=result_data.get('comments_count'),
                media_preview=result_data.get('media_preview'),
                duration=result_data.get('duration'),
                thumbnail=result_data.get('thumbnail'),
                post_created_at=result_data.get('post_created_at'),
                post_result_obj=result_data.get('post_result_obj')
            )
            
            db.add(result)
            db.commit()
            db.refresh(result)
            
            logger.info(f"Created new result with ID: {result.id}")
            return result
            
        except HTTPException:
            raise
        except ValueError as e:
            logger.error(f"Invalid UUID in create_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid campaign ID format"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in create_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error in create_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def update_result(
        result_id: uuid.UUID, 
        result_data: Dict[str, Any], 
        db: Session
    ) -> Result:
        """
        Update a result
        
        Args:
            result_id: ID of the result to update
            result_data: Dictionary containing updated result data
            db: Database session
            
        Returns:
            Result: The updated result
        """
        try:
            # Get existing result
            result = db.query(Result).filter(Result.id == result_id).first()
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Result with ID {result_id} not found"
                )
            
            # Update fields if provided
            if 'campaign_id' in result_data:
                campaign_id = uuid.UUID(result_data['campaign_id'])
                # Verify new campaign exists
                campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                if not campaign:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Campaign with ID {campaign_id} not found"
                    )
                result.campaign_id = campaign_id
            
            # Update all other fields
            fields_to_update = [
                'user_ig_id', 'full_name', 'influencer_username', 'profile_pic_url',
                'post_id', 'title', 'views_count', 'likes_count', 'plays_count', 'comments_count',
                'media_preview', 'duration', 'thumbnail', 'post_created_at', 'post_result_obj'
            ]
            
            for field in fields_to_update:
                if field in result_data:
                    setattr(result, field, result_data[field])
            
            db.commit()
            db.refresh(result)
            
            logger.info(f"Updated result with ID: {result_id}")
            return result
            
        except HTTPException:
            raise
        except ValueError as e:
            logger.error(f"Invalid UUID in update_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in update_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error in update_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def delete_result(result_id: uuid.UUID, db: Session) -> Result:
        """
        Delete a result
        
        Args:
            result_id: ID of the result to delete
            db: Database session
            
        Returns:
            Result: The deleted result
        """
        try:
            # Get existing result
            result = db.query(Result).filter(Result.id == result_id).first()
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Result with ID {result_id} not found"
                )
            
            # Delete result
            db.delete(result)
            db.commit()
            
            logger.info(f"Deleted result with ID: {result_id}")
            return result
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in delete_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error in delete_result: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def bulk_create_results(results_data: List[Dict[str, Any]], db: Session) -> List[Result]:
        """
        Create multiple results in bulk
        
        Args:
            results_data: List of dictionaries containing result data
            db: Database session
            
        Returns:
            List[Result]: List of created results
        """
        try:
            created_results = []
            
            for result_data in results_data:
                # Verify campaign exists
                campaign_id = uuid.UUID(result_data['campaign_id'])
                campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
                if not campaign:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Campaign with ID {campaign_id} not found"
                    )
                
                # Create new result
                result = Result(
                    campaign_id=campaign_id,
                    user_ig_id=result_data.get('user_ig_id'),
                    full_name=result_data.get('full_name'),
                    influencer_username=result_data['influencer_username'],
                    profile_pic_url=result_data.get('profile_pic_url'),
                    post_id=result_data.get('post_id'),
                    title=result_data.get('title'),
                    views_count=result_data.get('views_count'),
                    likes_count=result_data.get('likes_count'),
                    plays_count=result_data.get('plays_count'),
                    comments_count=result_data.get('comments_count'),
                    media_preview=result_data.get('media_preview'),
                    duration=result_data.get('duration'),
                    thumbnail=result_data.get('thumbnail'),
                    post_created_at=result_data.get('post_created_at'),
                    post_result_obj=result_data.get('post_result_obj')
                )
                
                db.add(result)
                created_results.append(result)
            
            db.commit()
            
            # Refresh all results to get IDs and timestamps
            for result in created_results:
                db.refresh(result)
            
            logger.info(f"Bulk created {len(created_results)} results")
            return created_results
            
        except HTTPException:
            raise
        except ValueError as e:
            db.rollback()
            logger.error(f"Invalid UUID in bulk_create_results: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format in one or more results"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in bulk_create_results: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error in bulk_create_results: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )

    @staticmethod
    async def bulk_update_results_by_campaign(
        campaign_id: uuid.UUID,
        updates: List[Dict[str, Any]],
        db: Session
    ) -> Dict[str, Any]:
        """
        Bulk update multiple results within a campaign with individual data
        
        Args:
            campaign_id: ID of the campaign
            updates: List of dictionaries containing result_id and update_data
            db: Database session
            
        Returns:
            Dict: Summary of the bulk update operation
        """
        try:
            # Verify campaign exists
            campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
            if not campaign:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Campaign with ID {campaign_id} not found"
                )
            
            # Extract and validate result IDs
            result_ids = []
            invalid_ids = []
            
            for update_item in updates:
                try:
                    result_uuid = uuid.UUID(update_item['result_id'])
                    result_ids.append(result_uuid)
                except ValueError:
                    invalid_ids.append(update_item['result_id'])
            
            if invalid_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid UUID format for result IDs: {invalid_ids}"
                )
            
            # Get all results that belong to the campaign and are in the provided IDs
            results_to_update = db.query(Result).filter(
                and_(
                    Result.id.in_(result_ids),
                    Result.campaign_id == campaign_id
                )
            ).all()
            
            if not results_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No results found for the provided IDs in this campaign"
                )
            
            # Create a mapping of result_id to result object for easy lookup
            results_map = {result.id: result for result in results_to_update}
            
            # Track updates
            updated_results = []
            failed_updates = []
            
            # Process each individual update
            for update_item in updates:
                try:
                    result_id = uuid.UUID(update_item['result_id'])
                    update_data = update_item['update_data']
                    
                    # Check if result exists in our map
                    if result_id not in results_map:
                        failed_updates.append({
                            "result_id": str(result_id),
                            "error": "Result not found in this campaign"
                        })
                        continue
                    
                    result = results_map[result_id]
                    
                    # Verify new campaign if being updated
                    if 'campaign_id' in update_data:
                        new_campaign_id = uuid.UUID(update_data['campaign_id'])
                        new_campaign = db.query(Campaign).filter(Campaign.id == new_campaign_id).first()
                        if not new_campaign:
                            failed_updates.append({
                                "result_id": str(result_id),
                                "error": f"Target campaign with ID {new_campaign_id} not found"
                            })
                            continue
                    
                    # Update fields for this specific result
                    fields_to_update = [
                        'user_ig_id', 'full_name', 'influencer_username', 'profile_pic_url',
                        'post_id', 'title', 'views_count', 'likes_count', 'plays_count', 'comments_count',
                        'media_preview', 'duration', 'thumbnail', 'post_created_at', 'post_result_obj'
                    ]
                    
                    if 'campaign_id' in update_data:
                        fields_to_update.append('campaign_id')
                    
                    # Apply updates only for fields that are provided and not None
                    for field in fields_to_update:
                        if field in update_data and update_data[field] is not None:
                            if field == 'campaign_id':
                                setattr(result, field, uuid.UUID(update_data[field]))
                            else:
                                setattr(result, field, update_data[field])
                    
                    updated_results.append(result)
                    
                except ValueError as e:
                    failed_updates.append({
                        "result_id": update_item.get('result_id', 'unknown'),
                        "error": f"Invalid UUID format: {str(e)}"
                    })
                except Exception as e:
                    failed_updates.append({
                        "result_id": update_item.get('result_id', 'unknown'),
                        "error": str(e)
                    })
                    logger.error(f"Failed to update result {update_item.get('result_id')}: {str(e)}")
            
            # Commit all updates
            if updated_results:
                db.commit()
                
                # Refresh all updated results
                for result in updated_results:
                    db.refresh(result)
            
            logger.info(f"Bulk updated {len(updated_results)} results in campaign {campaign_id}")
            
            return {
                "success": len(updated_results) > 0,
                "updated_count": len(updated_results),
                "failed_count": len(failed_updates),
                "message": f"Successfully updated {len(updated_results)} results, {len(failed_updates)} failed",
                "updated_results": updated_results,
                "errors": failed_updates
            }
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in bulk_update_results_by_campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error in bulk_update_results_by_campaign: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )