from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from config.database import Base

class Influencer(Base):
    __tablename__ = 'influencers'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    sent_via = Column(String, default=None)
    message_status = Column(Boolean, default=False)

    # Establishing the inverse relationship with Client
    client = relationship('Client', back_populates='influencers')
