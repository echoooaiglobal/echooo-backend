from sqlalchemy.orm import Session
from app.Models.Influencer import Influencer
from app.Schemas.influencer import InfluencerCreate

class InfluencerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_influencer(self, influencer: InfluencerCreate):
        db_influencer = Influencer(**influencer.dict())
        self.db.add(db_influencer)
        self.db.commit()
        self.db.refresh(db_influencer)
        return db_influencer

    def get_influencer(self, influencer_id: int):
        return self.db.query(Influencer).filter(Influencer.id == influencer_id).first()

    def get_influencers(self, skip: int, limit: int):
        influencers = self.db.query(Influencer).offset(skip).limit(limit).all()
        total_count = self.db.query(Influencer).count()
        return influencers, total_count

    def update_influencer(self, influencer_id: int, influencer: InfluencerCreate):
        db_influencer = self.get_influencer(influencer_id)
        if db_influencer:
            db_influencer.username = influencer.username
            db_influencer.client_id = influencer.client_id
            self.db.commit()
            self.db.refresh(db_influencer)
        return db_influencer

    def delete_influencer(self, influencer_id: int):
        db_influencer = self.get_influencer(influencer_id)
        if db_influencer:
            self.db.delete(db_influencer)
            self.db.commit()
        return db_influencer
