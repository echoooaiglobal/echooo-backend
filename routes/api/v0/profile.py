# routes/api/v0/profile.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.Models.auth_models import User
from app.Schemas.auth import (
    ProfileImageResponse
)
from app.Services.GoogleCloudStorageService import gcs_service
from app.Utils.Helpers import get_current_active_user
from config.database import get_db
from app.Utils.Logger import logger

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.post("/upload-image", response_model=ProfileImageResponse)
async def upload_profile_image(
    file: UploadFile = File(..., description="Profile image file (max 5MB, jpg/png/webp)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload profile image to Google Cloud Storage"""
    try:
        # Upload image to GCS
        file_path, public_url = await gcs_service.upload_profile_image(
            file=file,
            user_id=str(current_user.id),
            optimize=True
        )
        
        # Delete old profile image if exists
        if current_user.profile_image_url:
            old_file_path = current_user.profile_image_url.split('/')[-2:]  # Extract path
            if len(old_file_path) == 2:
                old_path = f"profile-images/{old_file_path[0]}/{old_file_path[1]}"
                await gcs_service.delete_profile_image(old_path)
        
        # Update user profile image URL in database
        current_user.profile_image_url = public_url
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile image updated for user {current_user.id}")
        
        return ProfileImageResponse(
            message="Profile image uploaded successfully",
            profile_image_url=public_url,
            file_path=file_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload profile image for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload profile image"
        )

@router.delete("/delete-image")
async def delete_profile_image(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current profile image"""
    try:
        if not current_user.profile_image_url:
            raise HTTPException(
                status_code=400,
                detail="No profile image to delete"
            )
        
        # Extract file path from URL
        url_parts = current_user.profile_image_url.split('/')
        if len(url_parts) >= 2:
            file_path = f"profile-images/{url_parts[-2]}/{url_parts[-1]}"
            await gcs_service.delete_profile_image(file_path)
        
        # Update database
        current_user.profile_image_url = None
        db.commit()
        
        logger.info(f"Profile image deleted for user {current_user.id}")
        
        return {"message": "Profile image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile image for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete profile image"
        )