# models.py
from sqlalchemy import Column, Integer, String, DateTime, func
from db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="player")  # owner/admin/mod/player
    created_at = Column(DateTime(timezone=True), server_default=func.now())