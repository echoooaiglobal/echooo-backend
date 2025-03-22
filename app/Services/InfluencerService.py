from sqlalchemy.orm import Session
from app.Repositories.InfluencerRepository import InfluencerRepository
from app.Schemas.influencer import InfluencerCreate

class InfluencerService: 
    def __init__(self, db: Session):
        self.influencer_repo = InfluencerRepository(db)

    def create_influencer(self, influencer: InfluencerCreate):
        return self.influencer_repo.create_influencer(influencer)

    def get_influencer(self, influencer_id: int):
        return self.influencer_repo.get_influencer(influencer_id)

    def get_influencers(self, skip: int = 0, limit: int = 10):
        return self.influencer_repo.get_influencers(skip, limit)

    def update_influencer(self, influencer_id: int, influencer: InfluencerCreate):
        return self.influencer_repo.update_influencer(influencer_id, influencer)

    def delete_influencer(self, influencer_id: int):
        return self.influencer_repo.delete_influencer(influencer_id)
