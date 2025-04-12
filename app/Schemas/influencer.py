from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class InfluencerBase(BaseModel):
    username: str
    client_id: int
    name: Optional[str] = None
    sent_via: Optional[str] = None 
    message_status: Optional[bool] = False
    error_code: Optional[str] = None
    error_reason: Optional[str] = None
    message_sent_at: Optional[datetime] = None

class InfluencerCreate(InfluencerBase):
    pass

class Influencer(InfluencerBase):
    id: int
    client_name: Optional[str]  # Optional client_name field

    class Config:
        orm_mode = True
        from_attributes = True

class BulkInfluencerSchema(BaseModel):
    name: str
    username: str