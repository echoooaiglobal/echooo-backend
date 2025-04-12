from sqlalchemy.orm import Session
from app.Repositories.InfluencerRepository import InfluencerRepository
from app.Schemas.influencer import InfluencerCreate
import pandas as pd

class InfluencerService: 
    def __init__(self, db: Session):
        self.influencer_repo = InfluencerRepository(db)

    def create_influencer(self, influencer: InfluencerCreate):
        # Create the influencer using the repository
        new_influencer = self.influencer_repo.create_influencer(influencer)
        
        # Manually add client_name to the response
        if new_influencer.client:
            new_influencer.client_name = new_influencer.client.name
        return new_influencer
    
    def bulk_create_influencers_from_excel(self, file_path: str, client_id: int):
        df = pd.read_excel(file_path)
        df = df.where(pd.notnull(df), None)  # Replace NaN with None

        if 'name' not in df.columns or 'username' not in df.columns:
            raise Exception("Excel file must contain 'name' and 'username' columns")

        influencers = [
            {
                "name": row["name"],
                "username": row["username"],
                "client_id": client_id,
            }
            for _, row in df.iterrows()
        ]
        
        return self.influencer_repo.bulk_create_influencers(influencers)


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
        influencer = self.influencer_repo.delete_influencer(influencer_id)
        if influencer:
            return {"message": "Influencer deleted successfully"}
        else:
            return {"message": "Influencer not found"}
