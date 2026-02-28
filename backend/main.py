# main.py
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from db import Base, engine, get_db
from models import User

# ---------------- Config ----------------
SECRET_KEY = "troque-esse-segredo-antes-de-produção"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 dia (pra dev tá ok)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app = FastAPI(title="Projeto-02 API")

# CORS: em dev, libera tudo. Em produção, coloque seu domínio do painel.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # produção: ["https://seu-dominio.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria tabelas
Base.metadata.create_all(bind=engine)

# ---------------- Schemas ----------------
class LoginBody(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    email: str
    role: str

# ---------------- Auth helpers ----------------
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(db: Session = Depends(get_db), authorization: str | None = None):
    # FastAPI não injeta header automaticamente nesse formato sem Header(...)
    # então vamos ler de request via dependency do jeito simples:
    raise RuntimeError("Use get_current_user_via_header")

from fastapi import Header
def get_current_user_via_header(
    db: Session = Depends(get_db),
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

    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user

# ---------------- Seed (cria 1 user owner) ----------------
def ensure_seed_user(db: Session):
    # Usuário padrão pra você testar já
    email = "owner@local"
    password = "123456"

    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(
            email=email,
            password_hash=hash_password(password),
            role="owner"
        )
        db.add(u)
        db.commit()

@app.on_event("startup")
def startup():
    # cria user de seed no start
    from db import SessionLocal
    db = SessionLocal()
    try:
        ensure_seed_user(db)
    finally:
        db.close()

# ---------------- Endpoints ----------------
@app.post("/auth/login", response_model=TokenResponse)
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    token = create_access_token({"sub": user.email, "role": user.role})
    return TokenResponse(access_token=token)

@app.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user_via_header)):
    return MeResponse(email=user.email, role=user.role)

@app.get("/stats/overview")
def stats_overview(user: User = Depends(get_current_user_via_header)):
    # Por enquanto, valores fake (depois você puxa do banco do jogo/logs)
    # Esse endpoint já alimenta seus cards da Visão Geral.
    return {
        "online_now": 12,
        "bans_today": 1,
        "sales_today": 5,
        "reports_open": 2
    }