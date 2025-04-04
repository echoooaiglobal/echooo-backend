from pydantic import BaseModel
from typing import Optional

class InfluencerBase(BaseModel):
    username: str
    client_id: int
    sent_via: str
    message_status: bool

class InfluencerCreate(InfluencerBase):
    pass

class Influencer(InfluencerBase):
    id: int

    class Config:
        from_attributes = True
