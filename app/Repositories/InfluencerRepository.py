from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
from app.Models.Influencer import Influencer
from app.Schemas.influencer import InfluencerCreate
from app.Models.Client import Client 
from sqlalchemy import desc

class InfluencerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_influencer(self, influencer: InfluencerCreate):
        db_influencer = Influencer(**influencer.dict())
        self.db.add(db_influencer)
        self.db.commit()
        self.db.refresh(db_influencer)
        return db_influencer
    
    def bulk_create_influencers(self, influencers: list[dict], batch_size=10):
        created = []
        for i in range(0, len(influencers), batch_size):
            batch = influencers[i:i + batch_size]
            db_influencers = [Influencer(**data) for data in batch]
            self.db.add_all(db_influencers)
            self.db.commit()
            created.extend(db_influencers)
        return created  # Make sure you return something!



    def get_influencer(self, influencer_id: int):
        return self.db.query(Influencer)\
            .options(joinedload(Influencer.client))\
            .filter(Influencer.id == influencer_id)\
            .first()

    def get_influencers(self, skip: int, limit: int):
        # Query with join to get client name and order by descending ID
        query = self.db.query(
            Influencer,
            Client.name.label('client_name')
        ).join(
            Client,
            Influencer.client_id == Client.id
        ).order_by(desc(Influencer.id))
        
        total_count = query.count()
        results = query.offset(skip).limit(limit).all()
        
        # Combine influencer with client name
        influencers = []
        for influencer, client_name in results:
            influencer_dict = influencer.__dict__
            influencer_dict['client_name'] = client_name
            influencers.append(influencer_dict)
        
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
