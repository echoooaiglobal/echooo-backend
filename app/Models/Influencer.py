from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from config.database import Base

class Influencer(Base):
    __tablename__ = 'influencers'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    sent_via = Column(String, default='None')
    message_status = Column(Boolean, default=False)
    message_sent_at = Column(DateTime, nullable=True)
    error_code = Column(String, nullable=True)
    error_reason = Column(String, nullable=True)  # New field for storing reason

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    client = relationship('Client', back_populates='influencers')
