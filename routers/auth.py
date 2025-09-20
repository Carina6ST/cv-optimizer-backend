from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import User
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
from core.config import settings

router = APIRouter()
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthPayload(BaseModel):
    email: EmailStr
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=TokenResponse)
def register(payload: AuthPayload, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(email=payload.email, password_hash=pwd.hash(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    token = _make_token(user.id)
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
def login(payload: AuthPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()
    if not user or not pwd.verify(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = _make_token(user.id)
    return TokenResponse(access_token=token)

def _make_token(user_id: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.SECRET_KEY, algorithm="HS256")

def get_current_user_id(token: str) -> int:
    try:
        data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return int(data.get("sub"))
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
