# main.py
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from db import (
    BaseApp, BaseDash,
    app_engine, dashboard_engine,
    get_app_db, get_dashboard_db,
    AppSessionLocal, DashboardSessionLocal
)
from models import User, OverviewStats

# ---------------- CONFIG ----------------
SECRET_KEY = "troque-esse-segredo-antes-de-produção"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 dia

# bcrypt costuma dar dor no Python 3.14 -> PBKDF2 funciona liso
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app = FastAPI(title="Projeto-02 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # produção: coloque seu domínio do painel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria as tabelas em CADA DB
BaseApp.metadata.create_all(bind=app_engine)
BaseDash.metadata.create_all(bind=dashboard_engine)

# ---------------- SCHEMAS ----------------
class LoginBody(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    email: str
    role: str

class OverviewStatsResponse(BaseModel):
    online_now: int
    bans_today: int
    sales_today: int
    reports_open: int

class OverviewStatsUpdate(BaseModel):
    online_now: int | None = None
    bans_today: int | None = None
    sales_today: int | None = None
    reports_open: int | None = None

# ---------------- HELPERS ----------------
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(plain: str) -> str:
    # simples proteção contra inputs absurdos
    if len(plain.encode("utf-8")) > 72:
        plain = plain[:72]
    return pwd_context.hash(plain)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    app_db: Session = Depends(get_app_db),
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = app_db.query(User).filter(User.email == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

def require_roles(user: User, allowed: set[str]):
    if user.role not in allowed:
        raise HTTPException(status_code=403, detail="Sem permissão")

# ---------------- SEED ----------------
def ensure_seed_users(app_db: Session):
    # mantém login funcionando no app.db
    email = "owner@local"
    password = "123456"

    u = app_db.query(User).filter(User.email == email).first()
    if not u:
        u = User(email=email, password_hash=hash_password(password), role="owner")
        app_db.add(u)
        app_db.commit()

def ensure_seed_overview(dash_db: Session):
    # cria linha id=1 no dashboard.db
    row = dash_db.query(OverviewStats).filter(OverviewStats.id == 1).first()
    if not row:
        row = OverviewStats(id=1, online_now=0, bans_today=0, sales_today=0, reports_open=0)
        dash_db.add(row)
        dash_db.commit()

@app.on_event("startup")
def startup():
    app_db = AppSessionLocal()
    dash_db = DashboardSessionLocal()
    try:
        ensure_seed_users(app_db)
        ensure_seed_overview(dash_db)
    finally:
        app_db.close()
        dash_db.close()

# ---------------- ENDPOINTS ----------------
@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginBody, app_db: Session = Depends(get_app_db)):
    user = app_db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    token = create_access_token({"sub": user.email, "role": user.role})
    return TokenResponse(access_token=token)

@app.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return MeResponse(email=user.email, role=user.role)

@app.get("/stats/overview", response_model=OverviewStatsResponse)
def stats_overview(
    user: User = Depends(get_current_user),
    dash_db: Session = Depends(get_dashboard_db),
):
    row = dash_db.query(OverviewStats).filter(OverviewStats.id == 1).first()
    if not row:
        raise HTTPException(status_code=500, detail="overview_stats não inicializado")

    return {
        "online_now": row.online_now,
        "bans_today": row.bans_today,
        "sales_today": row.sales_today,
        "reports_open": row.reports_open,
    }

# opcional: editar stats pela API (owner/admin)
@app.put("/stats/overview", response_model=OverviewStatsResponse)
def update_stats_overview(
    body: OverviewStatsUpdate,
    user: User = Depends(get_current_user),
    dash_db: Session = Depends(get_dashboard_db),
):
    require_roles(user, {"owner", "admin"})

    row = dash_db.query(OverviewStats).filter(OverviewStats.id == 1).first()
    if not row:
        raise HTTPException(status_code=500, detail="overview_stats não inicializado")

    if body.online_now is not None: row.online_now = body.online_now
    if body.bans_today is not None: row.bans_today = body.bans_today
    if body.sales_today is not None: row.sales_today = body.sales_today
    if body.reports_open is not None: row.reports_open = body.reports_open

    dash_db.commit()
    dash_db.refresh(row)

    return {
        "online_now": row.online_now,
        "bans_today": row.bans_today,
        "sales_today": row.sales_today,
        "reports_open": row.reports_open,
    }