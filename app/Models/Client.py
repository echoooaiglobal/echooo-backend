from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from config.database import Base
import datetime

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    company_name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Establishing a one-to-many relationship with Influencer
    influencers = relationship('Influencer', back_populates='client')
