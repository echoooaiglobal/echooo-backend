from fastapi import APIRouter
from app.Http.Controllers import InstagramController

router = APIRouter()
router.include_router(InstagramController.router, prefix="/instagram", tags=["Instagram Bot"])