from fastapi_users.db import SQLAlchemyBaseUserTable
from config.database import Base
from sqlalchemy import Column, String

class User(Base, SQLAlchemyBaseUserTable):
    __tablename__ = "users"
    full_name = Column(String, nullable=False)
