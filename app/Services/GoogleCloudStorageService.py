# app/Services/GoogleCloudStorageService.py
import os
import uuid
import mimetypes
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from io import BytesIO
from PIL import Image
import logging

from google.cloud import storage
from google.oauth2 import service_account
from fastapi import HTTPException, UploadFile
from config.settings import settings

logger = logging.getLogger(__name__)

class GoogleCloudStorageService:
    """Service for handling Google Cloud Storage operations"""
    
    def __init__(self):
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.project_id = settings.GCS_PROJECT_ID
        self.service_account_path = settings.GCS_SERVICE_ACCOUNT_PATH
        self.base_url = settings.GCS_BASE_URL
        self.cdn_url = getattr(settings, 'GCS_CDN_URL', None)
        
        # Initialize client
        self._client = None
        self._bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Storage client"""
        try:
            if os.path.exists(self.service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    self.service_account_path
                )
                self._client = storage.Client(
                    credentials=credentials,
                    project=self.project_id
                )
            else:
                # Use default credentials (for production with IAM roles)
                self._client = storage.Client(project=self.project_id)
            
            self._bucket = self._client.bucket(self.bucket_name)
            logger.info(f"GCS client initialized for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize cloud storage"
            )
    
    async def upload_profile_image(
        self, 
        file: UploadFile, 
        user_id: str,
        optimize: bool = True
    ) -> Tuple[str, str]:
        """
        Upload profile image to GCS
        
        Args:
            file: Upload file object
            user_id: User ID for organizing files
            optimize: Whether to optimize the image
            
        Returns:
            Tuple of (file_path, public_url)
        """
        try:
            # Validate file
            self._validate_image_file(file)
            
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            # Optimize image if requested
            if optimize:
                file_content = self._optimize_image(file_content, file.content_type)
            
            # Generate unique filename
            file_extension = self._get_file_extension(file.filename, file.content_type)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{uuid.uuid4().hex}_{timestamp}{file_extension}"
            
            # Create file path
            file_path = f"profile-images/{user_id}/{unique_filename}"
            
            # Upload to GCS
            blob = self._bucket.blob(file_path)
            blob.upload_from_string(
                file_content,
                content_type=file.content_type
            )
            
            # Make blob publicly readable
            blob.make_public()
            
            # Get public URL
            public_url = self._get_public_url(file_path)
            
            logger.info(f"Profile image uploaded successfully: {file_path}")
            return file_path, public_url
            
        except Exception as e:
            logger.error(f"Failed to upload profile image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload image: {str(e)}"
            )
    
    async def delete_profile_image(self, file_path: str) -> bool:
        """Delete profile image from GCS"""
        try:
            blob = self._bucket.blob(file_path)
            if blob.exists():
                blob.delete()
                logger.info(f"Profile image deleted: {file_path}")
                return True
            else:
                logger.warning(f"Profile image not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete profile image: {str(e)}")
            return False
    
    async def get_signed_url(
        self, 
        file_path: str, 
        expiration_minutes: int = 60
    ) -> str:
        """Generate signed URL for private access"""
        try:
            blob = self._bucket.blob(file_path)
            expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)
            
            url = blob.generate_signed_url(
                expiration=expiration,
                method='GET'
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate signed URL"
            )
    
    def _validate_image_file(self, file: UploadFile):
        """Validate uploaded image file"""
        # Check file size
        max_size = getattr(settings, 'PROFILE_IMAGE_MAX_SIZE', 5242880)  # 5MB
        if hasattr(file, 'size') and file.size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB"
            )
        
        # Check file type
        allowed_types = getattr(
            settings, 
            'PROFILE_IMAGE_ALLOWED_TYPES', 
            'image/jpeg,image/jpg,image/png,image/webp'
        ).split(',')
        
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
    
    def _optimize_image(self, file_content: bytes, content_type: str) -> bytes:
        """Optimize image for web use"""
        try:
            # Open image
            image = Image.open(BytesIO(file_content))
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if too large (max 800x800 for profile images)
            max_size = (800, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = BytesIO()
            format_map = {
                'image/jpeg': 'JPEG',
                'image/jpg': 'JPEG',
                'image/png': 'PNG',
                'image/webp': 'WEBP'
            }
            
            image_format = format_map.get(content_type, 'JPEG')
            
            if image_format == 'JPEG':
                image.save(output, format=image_format, quality=85, optimize=True)
            elif image_format == 'PNG':
                image.save(output, format=image_format, optimize=True)
            elif image_format == 'WEBP':
                image.save(output, format=image_format, quality=85, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image optimization failed, using original: {str(e)}")
            return file_content
    
    def _get_file_extension(self, filename: str, content_type: str) -> str:
        """Get appropriate file extension"""
        if filename and '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        
        extension_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp'
        }
        return extension_map.get(content_type, '.jpg')
    
    def _get_public_url(self, file_path: str) -> str:
        """Get public URL for the file"""
        if self.cdn_url:
            return f"{self.cdn_url}/{file_path}"
        else:
            return f"{self.base_url}/{self.bucket_name}/{file_path}"
    
    async def list_user_images(self, user_id: str) -> List[str]:
        """List all images for a user"""
        try:
            prefix = f"profile-images/{user_id}/"
            blobs = self._bucket.list_blobs(prefix=prefix)
            return [blob.name for blob in blobs]
        except Exception as e:
            logger.error(f"Failed to list user images: {str(e)}")
            return []

# Create singleton instance
gcs_service = GoogleCloudStorageService()