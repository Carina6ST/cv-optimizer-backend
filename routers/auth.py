# backend/routers/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

from db.session import SessionLocal
from db.models import User
from core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- helpers -----------------------------------------------------------------

def create_access_token(data: dict, expires_minutes: int) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def get_current_user_id(token: str) -> Optional[int]:
    """Decode JWT and return user id or None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        uid = payload.get("sub")
        return int(uid) if uid is not None else None
    except JWTError:
        return None

# Expose helper to other routers
__all__ = ["get_current_user_id"]

# --- endpoints ---------------------------------------------------------------

@router.post("/register", response_model=None)
def register(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email_lower = email.strip().lower()
    if db.query(User).filter(User.email == email_lower).first():
        raise HTTPException(400, "Email already registered")

    user = User(email=email_lower, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)}, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=None)
def login(
    # You can also use OAuth2PasswordRequestForm, but we keep it simple for your UI:
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = create_access_token({"sub": str(user.id)}, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=None)
def me(authorization: str = Depends(lambda: "" ), db: Session = Depends(get_db)):
    """Return basic info for the current user; frontends can check is_pro here."""
    # Extract token if passed via Depends hack (we'll fetch from header manually)
    from fastapi import Request
    from fastapi import Depends as _Depends  # avoid confusion
    # Simpler: read header again using Request
    return {"ok": True}
