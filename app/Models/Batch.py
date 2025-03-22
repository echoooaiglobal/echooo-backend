from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from config.database import Base
from datetime import datetime

class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
