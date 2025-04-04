from pydantic import BaseModel
from typing import Optional

class InfluencerBase(BaseModel):
    username: str
    client_id: int
    client_name: Optional[str] = None
    sent_via: Optional[str] = None 
    message_status: Optional[bool] = False
    error_code: Optional[str] = None
    error_reason: Optional[str] = None
    # message_sent_at = Column(DateTime, nullable=True, default=None)

class InfluencerCreate(InfluencerBase):
    pass

class Influencer(InfluencerBase):
    id: int

    class Config:
        from_attributes = True
