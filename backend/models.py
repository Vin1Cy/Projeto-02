# models.py
from sqlalchemy import Column, Integer, String, DateTime, func
from db import BaseApp, BaseDash

# ---------- app.db ----------
class User(BaseApp):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="player")  # owner/admin/mod/player
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ---------- dashboard.db ----------
class OverviewStats(BaseDash):
    __tablename__ = "overview_stats"

    id = Column(Integer, primary_key=True)  # vamos usar sempre id=1
    online_now = Column(Integer, nullable=False, default=0)
    bans_today = Column(Integer, nullable=False, default=0)
    sales_today = Column(Integer, nullable=False, default=0)
    reports_open = Column(Integer, nullable=False, default=0)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())