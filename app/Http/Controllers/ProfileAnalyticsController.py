# app/Http/Controllers/ProfileAnalyticsController.py
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
import uuid
import math

from app.Models.profile_analytics import ProfileAnalytics
from app.Models.support_models import Platform, Category
from app.Models.influencer_models import SocialAccount
from app.Schemas.profile_analytics import (
    ProfileAnalyticsCreate, ProfileAnalyticsUpdate, ProfileAnalyticsResponse,
    ProfileAnalyticsListResponse, ProfileAnalyticsStatsResponse,
    ProfileAnalyticsBrief, ProfileAnalyticsWithSocialAccountCreate,
    ProfileAnalyticsWithSocialAccountResponse, SocialAccountWithAnalyticsResponse
)
from app.Schemas.influencer import SocialAccountResponse

class ProfileAnalyticsController:
    
    @staticmethod
    async def create_analytics_with_social_account(
        data: ProfileAnalyticsWithSocialAccountCreate, 
        db: Session
    ) -> ProfileAnalyticsWithSocialAccountResponse:
        """Create or update social account and create analytics record"""
        try:
            # Validate platform exists
            platform = db.query(Platform).filter(Platform.id == data.social_account_data.platform_id).first()
            if not platform:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Platform not found"
                )
            
            # Validate category if provided
            if data.social_account_data.category_id:
                category = db.query(Category).filter(Category.id == data.social_account_data.category_id).first()
                if not category:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Category not found"
                    )
            
            # Check if social account exists (by platform_id and platform_account_id)
            existing_social_account = db.query(SocialAccount).filter(
                and_(
                    SocialAccount.platform_id == data.social_account_data.platform_id,
                    SocialAccount.platform_account_id == data.social_account_data.platform_account_id
                )
            ).first()
            
            if existing_social_account:
                # Update existing social account (keep influencer_id and platform_account_id unchanged)
                update_data = data.social_account_data.model_dump(exclude={'platform_account_id'})
                
                for field, value in update_data.items():
                    if hasattr(existing_social_account, field):
                        setattr(existing_social_account, field, value)
                
                db.commit()
                db.refresh(existing_social_account)
                social_account = existing_social_account
                message = "Social account updated and analytics created"
                
            else:
                # Create new social account
                social_account_data = data.social_account_data.model_dump()
                social_account = SocialAccount(**social_account_data)
                
                db.add(social_account)
                db.commit()
                db.refresh(social_account)
                message = "Social account and analytics created"
            
            # Create analytics record
            analytics_record = ProfileAnalytics(
                social_account_id=social_account.id,
                analytics=data.analytics
            )
            
            db.add(analytics_record)
            db.commit()
            db.refresh(analytics_record)
            
            # Load relationships for response
            social_account = db.query(SocialAccount).options(
                joinedload(SocialAccount.platform),
                joinedload(SocialAccount.category),
                joinedload(SocialAccount.influencer)
            ).filter(SocialAccount.id == social_account.id).first()
            
            analytics_record = db.query(ProfileAnalytics).options(
                joinedload(ProfileAnalytics.social_account)
            ).filter(ProfileAnalytics.id == analytics_record.id).first()
            
            return ProfileAnalyticsWithSocialAccountResponse(
                social_account=SocialAccountResponse.model_validate(social_account).model_dump(),
                analytics=ProfileAnalyticsResponse.model_validate(analytics_record),
                message=message
            )
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating analytics with social account: {str(e)}"
            )
    
    @staticmethod
    async def get_analytics_by_handle_or_account_id(
        handle_or_account_id: str, 
        platform_id: Optional[str] = None,
        db: Session = Session
    ) -> SocialAccountWithAnalyticsResponse:
        """Get analytics by account handle or platform account ID"""
        try:
            # Build query to find social account
            query = db.query(SocialAccount).options(
                joinedload(SocialAccount.platform),
                joinedload(SocialAccount.category),
                joinedload(SocialAccount.influencer)
            )
            
            # Search by handle or platform_account_id
            conditions = [
                SocialAccount.account_handle.ilike(f"%{handle_or_account_id}%"),
                SocialAccount.platform_account_id == handle_or_account_id
            ]
            
            if platform_id:
                # If platform specified, add it to conditions
                query = query.filter(SocialAccount.platform_id == platform_id)
            
            social_account = query.filter(or_(*conditions)).first()
            
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )
            
            # Get all analytics for this social account
            analytics_records = db.query(ProfileAnalytics).options(
                joinedload(ProfileAnalytics.social_account)
            ).filter(
                ProfileAnalytics.social_account_id == social_account.id
            ).order_by(desc(ProfileAnalytics.created_at)).all()
            
            return SocialAccountWithAnalyticsResponse(
                social_account=SocialAccountResponse.model_validate(social_account).model_dump(),
                analytics=[ProfileAnalyticsResponse.model_validate(analytics) for analytics in analytics_records],
                analytics_count=len(analytics_records)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving analytics: {str(e)}"
            )
    
    @staticmethod
    async def create_analytics(analytics_data: ProfileAnalyticsCreate, db: Session) -> ProfileAnalyticsResponse:
        """Create new profile analytics directly"""
        try:
            # Validate social account exists
            social_account = db.query(SocialAccount).filter(
                SocialAccount.id == analytics_data.social_account_id
            ).first()
            if not social_account:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Social account not found"
                )
            
            # Create analytics
            db_analytics = ProfileAnalytics(
                social_account_id=analytics_data.social_account_id,
                analytics=analytics_data.analytics
            )
            
            db.add(db_analytics)
            db.commit()
            db.refresh(db_analytics)
            
            # Load relationships
            db_analytics = db.query(ProfileAnalytics).options(
                joinedload(ProfileAnalytics.social_account)
            ).filter(ProfileAnalytics.id == db_analytics.id).first()
            
            return ProfileAnalyticsResponse.model_validate(db_analytics)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating profile analytics: {str(e)}"
            )
    
    @staticmethod
    async def get_analytics_by_id(analytics_id: uuid.UUID, db: Session) -> ProfileAnalyticsResponse:
        """Get profile analytics by ID"""
        analytics = db.query(ProfileAnalytics).options(
            joinedload(ProfileAnalytics.social_account)
        ).filter(ProfileAnalytics.id == analytics_id).first()
        
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile analytics not found"
            )
        
        return ProfileAnalyticsResponse.model_validate(analytics)
    
    @staticmethod
    async def get_analytics_by_social_account(
        social_account_id: uuid.UUID, 
        db: Session
    ) -> List[ProfileAnalyticsResponse]:
        """Get all analytics for a social account"""
        analytics_list = db.query(ProfileAnalytics).options(
            joinedload(ProfileAnalytics.social_account)
        ).filter(
            ProfileAnalytics.social_account_id == social_account_id
        ).order_by(desc(ProfileAnalytics.created_at)).all()
        
        return [ProfileAnalyticsResponse.model_validate(analytics) for analytics in analytics_list]
    
    @staticmethod
    async def get_all_analytics(
        db: Session,
        social_account_id: Optional[uuid.UUID] = None,
        page: int = 1,
        per_page: int = 20
    ) -> ProfileAnalyticsListResponse:
        """Get paginated list of profile analytics with optional filters"""
        query = db.query(ProfileAnalytics).options(
            joinedload(ProfileAnalytics.social_account)
        )
        
        # Apply filters
        if social_account_id:
            query = query.filter(ProfileAnalytics.social_account_id == social_account_id)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        analytics_list = query.order_by(desc(ProfileAnalytics.created_at)).offset(offset).limit(per_page).all()
        
        # Calculate total pages
        total_pages = math.ceil(total / per_page)
        
        return ProfileAnalyticsListResponse(
            analytics=[ProfileAnalyticsResponse.model_validate(analytics) for analytics in analytics_list],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    
    @staticmethod
    async def update_analytics(
        analytics_id: uuid.UUID, 
        analytics_data: ProfileAnalyticsUpdate, 
        db: Session
    ) -> ProfileAnalyticsResponse:
        """Update profile analytics"""
        try:
            analytics = db.query(ProfileAnalytics).filter(ProfileAnalytics.id == analytics_id).first()
            
            if not analytics:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile analytics not found"
                )
            
            # Update fields
            update_data = analytics_data.model_dump(exclude_unset=True)
            
            # Apply updates
            for field, value in update_data.items():
                setattr(analytics, field, value)
            
            db.commit()
            db.refresh(analytics)
            
            # Load relationships
            analytics = db.query(ProfileAnalytics).options(
                joinedload(ProfileAnalytics.social_account)
            ).filter(ProfileAnalytics.id == analytics_id).first()
            
            return ProfileAnalyticsResponse.model_validate(analytics)
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating profile analytics: {str(e)}"
            )
    
    @staticmethod
    async def delete_analytics(analytics_id: uuid.UUID, db: Session) -> dict:
        """Delete profile analytics"""
        try:
            analytics = db.query(ProfileAnalytics).filter(ProfileAnalytics.id == analytics_id).first()
            
            if not analytics:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile analytics not found"
                )
            
            db.delete(analytics)
            db.commit()
            
            return {"message": "Profile analytics deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting profile analytics: {str(e)}"
            )
    
    @staticmethod
    async def get_analytics_stats(db: Session) -> ProfileAnalyticsStatsResponse:
        """Get profile analytics statistics"""
        # Total profiles with analytics
        total_profiles = db.query(ProfileAnalytics.social_account_id).distinct().count()
        
        # Profiles by platform
        platform_stats = db.query(
            Platform.name,
            func.count(ProfileAnalytics.id).label('count')
        ).join(SocialAccount).join(ProfileAnalytics).group_by(Platform.name).all()
        
        profiles_by_platform = {stat.name: stat.count for stat in platform_stats}
        
        # Recent analytics (last 10)
        recent_analytics = db.query(ProfileAnalytics).order_by(
            desc(ProfileAnalytics.created_at)
        ).limit(10).all()
        
        recent_analytics_brief = [
            ProfileAnalyticsBrief.model_validate(analytics) for analytics in recent_analytics
        ]
        
        # Top platforms by analytics count
        top_platforms = [
            {"platform": stat.name, "count": stat.count} 
            for stat in sorted(platform_stats, key=lambda x: x.count, reverse=True)[:5]
        ]
        
        return ProfileAnalyticsStatsResponse(
            total_profiles=total_profiles,
            profiles_by_platform=profiles_by_platform,
            recent_analytics=recent_analytics_brief,
            top_platforms=top_platforms
        )