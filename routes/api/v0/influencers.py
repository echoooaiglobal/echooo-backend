from fastapi import APIRouter
from app.Http.Controllers import InfluencerController

router = APIRouter()
router.include_router(InfluencerController.router, prefix="/influencers", tags=["Influencers"])
