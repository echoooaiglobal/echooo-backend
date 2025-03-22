# app/Schemas/client.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class InfluencerBase(BaseModel):
    username: str

class InfluencerCreate(InfluencerBase):
    pass

class Influencer(InfluencerBase):
    id: int
    client_id: int

    model_config = ConfigDict(from_attributes=True)

class ClientBase(BaseModel):
    name: str
    company_name: str

class ClientCreate(ClientBase):
    influencers: List[InfluencerCreate] = []

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    influencers: Optional[List[InfluencerCreate]] = None

class Client(ClientBase):
    id: int
    influencers: List[Influencer] = []

    model_config = ConfigDict(from_attributes=True)
