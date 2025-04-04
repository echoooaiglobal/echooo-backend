from sqlalchemy.orm import Session
from app.Repositories.InfluencerRepository import InfluencerRepository
from app.Schemas.influencer import InfluencerCreate

class InfluencerService: 
    def __init__(self, db: Session):
        self.influencer_repo = InfluencerRepository(db)

    def create_influencer(self, influencer: InfluencerCreate):
        return self.influencer_repo.create_influencer(influencer)

    def get_influencer(self, influencer_id: int):
        influencer = self.influencer_repo.get_influencer(influencer_id)
        if influencer and influencer.client:
            influencer.client_name = influencer.client.name
        return influencer

    def get_influencers(self, skip: int = 0, limit: int = 10):
        # The repository now returns influencers with client_name
        return self.influencer_repo.get_influencers(skip, limit)

    def update_influencer(self, influencer_id: int, influencer: InfluencerCreate):
        return self.influencer_repo.update_influencer(influencer_id, influencer)

    def delete_influencer(self, influencer_id: int):
        return self.influencer_repo.delete_influencer(influencer_id)
