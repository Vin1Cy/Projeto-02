# db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# DB 1: Auth/Login
APP_DB_URL = "sqlite:///./app.db"

# DB 2: Dashboard/Stats
DASHBOARD_DB_URL = "sqlite:///./dashboard.db"

app_engine = create_engine(APP_DB_URL, connect_args={"check_same_thread": False})
dashboard_engine = create_engine(DASHBOARD_DB_URL, connect_args={"check_same_thread": False})

AppSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)
DashboardSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=dashboard_engine)

BaseApp = declarative_base()
BaseDash = declarative_base()

def get_app_db():
  db = AppSessionLocal()
  try:
    yield db
  finally:
    db.close()

def get_dashboard_db():
  db = DashboardSessionLocal()
  try:
    yield db
  finally:
    db.close()