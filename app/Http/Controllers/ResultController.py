# app/Http/Controllers/ResultController.py

from fastapi import HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from math import ceil
import uuid

from app.Models.auth_models import User
from app.Schemas.results import (
    ResultCreate, ResultUpdate, ResultResponse, ResultListResponse,
    CampaignResultsResponse, ResultBrief, BulkUpdateRequest
)
from app.Services.ResultService import ResultService
from app.Utils.Logger import logger

class ResultController:
    """Controller for result-related endpoints"""
    
    @staticmethod
    async def get_all_results(
        db: Session,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Results per page"),
        sort_by: str = Query("created_at", description="Column to sort by"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
    ):
        """Get all results with pagination and sorting"""
        try:
            results, total = await ResultService.get_all_results(
                db, page, per_page, sort_by, sort_order
            )
            
            total_pages = ceil(total / per_page)
            
            return ResultListResponse(
                results=[ResultResponse.model_validate(result) for result in results],
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error in get_all_results controller: {str(e)}")
            raise

    @staticmethod
    async def get_result(result_id: uuid.UUID, db: Session):
        """Get a result by ID"""
        try:
            result = await ResultService.get_result_by_id(result_id, db)
            return ResultResponse.model_validate(result)
            
        except Exception as e:
            logger.error(f"Error in get_result controller: {str(e)}")
            raise

    @staticmethod
    async def get_campaign_results(
        campaign_id: uuid.UUID,
        db: Session,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Results per page")
    ):
        """Get all results for a specific campaign"""
        try:
            results, total = await ResultService.get_results_by_campaign(
                campaign_id, db, page, per_page
            )
            
            return CampaignResultsResponse(
                campaign_id=str(campaign_id),
                results=[ResultResponse.model_validate(result) for result in results],
                total_results=total
            )
            
        except Exception as e:
            logger.error(f"Error in get_campaign_results controller: {str(e)}")
            raise

    @staticmethod
    async def get_influencer_results(
        influencer_username: str,
        db: Session,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=100, description="Results per page")
    ):
        """Get all results for a specific influencer"""
        try:
            results, total = await ResultService.get_results_by_influencer(
                influencer_username, db, page, per_page
            )
            
            total_pages = ceil(total / per_page)
            
            return ResultListResponse(
                results=[ResultResponse.model_validate(result) for result in results],
                total=total,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
            
        except Exception as e:
            logger.error(f"Error in get_influencer_results controller: {str(e)}")
            raise

    @staticmethod
    async def create_result(result_data: ResultCreate, db: Session):
        """Create a new result"""
        try:
            result = await ResultService.create_result(
                result_data.model_dump(exclude_unset=True), db
            )
            return ResultResponse.model_validate(result)
            
        except Exception as e:
            logger.error(f"Error in create_result controller: {str(e)}")
            raise

    @staticmethod
    async def update_result(
        result_id: uuid.UUID, 
        result_data: ResultUpdate, 
        db: Session
    ):
        """Update a result"""
        try:
            result = await ResultService.update_result(
                result_id, result_data.model_dump(exclude_unset=True), db
            )
            return ResultResponse.model_validate(result)
            
        except Exception as e:
            logger.error(f"Error in update_result controller: {str(e)}")
            raise

    @staticmethod
    async def delete_result(result_id: uuid.UUID, db: Session):
        """Delete a result"""
        try:
            result = await ResultService.delete_result(result_id, db)
            return ResultResponse.model_validate(result)
            
        except Exception as e:
            logger.error(f"Error in delete_result controller: {str(e)}")
            raise

    @staticmethod
    async def bulk_create_results(results_data: List[ResultCreate], db: Session):
        """Create multiple results in bulk"""
        try:
            results_dict_list = [
                result_data.model_dump(exclude_unset=True) 
                for result_data in results_data
            ]
            
            results = await ResultService.bulk_create_results(results_dict_list, db)
            
            return {
                "message": f"Successfully created {len(results)} results",
                "results": [ResultResponse.model_validate(result) for result in results]
            }
            
        except Exception as e:
            logger.error(f"Error in bulk_create_results controller: {str(e)}")
            raise

    @staticmethod
    async def bulk_update_campaign_results(
        campaign_id: uuid.UUID,
        bulk_update_request: BulkUpdateRequest,
        db: Session
    ):
        """Bulk update multiple results in a campaign with individual data"""
        try:
            # Convert the request to the format expected by the service
            updates = []
            for update_item in bulk_update_request.updates:
                updates.append({
                    "result_id": update_item.result_id,
                    "update_data": update_item.update_data.model_dump(exclude_unset=True)
                })
            
            result = await ResultService.bulk_update_results_by_campaign(
                campaign_id,
                updates,
                db
            )
            
            # Convert updated results to response format
            from app.Schemas.results import BulkUpdateResponse, ResultResponse
            
            updated_results_response = [
                ResultResponse.model_validate(res) for res in result["updated_results"]
            ]
            
            return BulkUpdateResponse(
                success=result["success"],
                updated_count=result["updated_count"],
                failed_count=result["failed_count"],
                message=result["message"],
                updated_results=updated_results_response,
                errors=result["errors"]
            )
            
        except Exception as e:
            logger.error(f"Error in bulk_update_campaign_results controller: {str(e)}")
            raise

    @staticmethod
    async def get_results_stats(db: Session):
        """Get statistics about results"""
        try:
            # This would typically use additional service methods
            # For now, implementing basic stats directly
            from sqlalchemy import func
            from app.Models.results import Result
            
            total_results = db.query(Result).count()
            
            # Get aggregated stats
            stats_query = db.query(
                func.sum(Result.view_counts).label('total_views'),
                func.sum(Result.play_counts).label('total_plays'),
                func.sum(Result.comment_counts).label('total_comments')
            ).first()
            
            # Get results by campaign
            campaign_stats = db.query(
                Result.campaign_id,
                func.count(Result.id).label('count')
            ).group_by(Result.campaign_id).all()
            
            # Get top influencers by result count
            influencer_stats = db.query(
                Result.influencer_username,
                func.count(Result.id).label('result_count'),
                func.sum(Result.view_counts).label('total_views'),
                func.sum(Result.play_counts).label('total_plays')
            ).group_by(Result.influencer_username).order_by(
                func.count(Result.id).desc()
            ).limit(10).all()
            
            # Get recent results
            recent_results = db.query(Result).order_by(
                Result.created_at.desc()
            ).limit(5).all()
            
            return {
                "total_results": total_results,
                "total_views": stats_query.total_views or 0,
                "total_plays": stats_query.total_plays or 0,
                "total_comments": stats_query.total_comments or 0,
                "results_by_campaign": {
                    str(stat.campaign_id): stat.count 
                    for stat in campaign_stats
                },
                "top_influencers": [
                    {
                        "username": stat.influencer_username,
                        "result_count": stat.result_count,
                        "total_views": stat.total_views or 0,
                        "total_plays": stat.total_plays or 0
                    }
                    for stat in influencer_stats
                ],
                "recent_results": [
                    {
                        "id": str(result.id),
                        "influencer_username": result.influencer_username,
                        "post_id": result.post_id,
                        "title": result.title,
                        "view_counts": result.view_counts,
                        "created_at": result.created_at
                    }
                    for result in recent_results
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in get_results_stats controller: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error retrieving results statistics"
            )