from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.Services.InfluencerService import InfluencerService
from app.Schemas.influencer import InfluencerCreate, Influencer
from config.database import get_db

router = APIRouter()

def get_influencer_service(db: Session = Depends(get_db)):
    return InfluencerService(db)

@router.post("/", response_model=Influencer)
def create_influencer(influencer: InfluencerCreate, influencer_service: InfluencerService = Depends(get_influencer_service)):
    return influencer_service.create_influencer(influencer)

@router.get("/{influencer_id}", response_model=Influencer)
def read_influencer(influencer_id: int, influencer_service: InfluencerService = Depends(get_influencer_service)):
    db_influencer = influencer_service.get_influencer(influencer_id)
    if db_influencer is None:
        raise HTTPException(status_code=404, detail="Influencer not found")
    return db_influencer

@router.get("/", response_model=dict)
def read_influencers(
    page: int = 1,  # Changed from skip to page (default 1)
    limit: int = 10, 
    influencer_service: InfluencerService = Depends(get_influencer_service)
):
    # Calculate skip offset
    skip = (page - 1) * limit
    
    influencers, total_count = influencer_service.get_influencers(skip, limit)
    
    # Convert ORM models to Pydantic schema
    influencers_data = [Influencer.model_validate(i) for i in influencers]
    
    return {
        "influencers": influencers_data, 
        "total_count": total_count,
        "page": page,  # Add current page for reference
        "limit": limit  # Add limit for reference
    }

@router.put("/{influencer_id}", response_model=Influencer)
def update_influencer(influencer_id: int, influencer: InfluencerCreate, influencer_service: InfluencerService = Depends(get_influencer_service)):
    db_influencer = influencer_service.update_influencer(influencer_id, influencer)
    if db_influencer is None:
        raise HTTPException(status_code=404, detail="Influencer not found")
    return db_influencer

@router.delete("/{influencer_id}", response_model=Influencer)
def delete_influencer(influencer_id: int, influencer_service: InfluencerService = Depends(get_influencer_service)):
    db_influencer = influencer_service.delete_influencer(influencer_id)
    if db_influencer is None:
        raise HTTPException(status_code=404, detail="Influencer not found")
    return db_influencer
