from datetime import datetime, timedelta
from typing import Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import Form
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from passlib.context import CryptContext

from db.session import SessionLocal
from db.models import User
from core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGO = "HS256"


# ---------------------- DB Dependency ---------------------- #
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------- Helpers ---------------------------- #
def _create_access_token(sub: str, minutes: int) -> str:
    exp = datetime.utcnow() + timedelta(minutes=minutes)
    payload = {"sub": sub, "exp": exp}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGO)

def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)

def _hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)

def get_current_user_id(token: str) -> Optional[int]:
    """
    Decode JWT and return user id or None.
    Other routers import this:  from routers.auth import get_current_user_id
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGO])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except JWTError:
        return None

__all__ = ["get_current_user_id"]


# ---------------------- Input Models ----------------------- #
class Credentials(BaseModel):
    email: EmailStr
    password: str


# We support both JSON and form. These helpers extract from either.
async def _extract_creds(request: Request, email: Optional[str], password: Optional[str]) -> Tuple[str, str]:
    """
    If email/password are provided via Form(...), use them.
    Otherwise try JSON body.
    """
    if email and password:
        return email.strip().lower(), password

    # Try JSON
    try:
        data = await request.json()
        e = (data.get("email") or "").strip().lower()
        p = data.get("password") or ""
        if e and p:
            return e, p
    except Exception:
        pass

    raise HTTPException(status_code=422, detail="Email and password are required")


# ---------------------- Endpoints -------------------------- #
@router.post("/register", response_model=None)
async def register(
    request: Request,
    email: Optional[EmailStr] = Form(default=None),
    password: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    email_str, password_str = await _extract_creds(request, email, password)

    # Basic guard
    if len(password_str) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    # Uniqueness
    existing = db.query(User).filter(User.email == email_str).first()
    if existing:
        raise HTTPException(400, "Email already registered")

    user = User(email=email_str, password_hash=_hash_password(password_str))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = _create_access_token(sub=str(user.id), minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=None)
async def login(
    request: Request,
    email: Optional[EmailStr] = Form(default=None),
    password: Optional[str] = Form(default=None),
    db: Session = Depends(get_db),
):
    email_str, password_str = await _extract_creds(request, email, password)

    user = db.query(User).filter(User.email == email_str).first()
    if not user or not _verify_password(password_str, user.password_hash):
        raise HTTPException(401, "Invalid email or password")

    token = _create_access_token(sub=str(user.id), minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=None)
def me(request: Request, db: Session = Depends(get_db)):
    """
    Returns minimal profile for the current user.
    Expect header: Authorization: Bearer <token>
    """
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(401, "Unauthorized")

    uid = get_current_user_id(auth.split(" ", 1)[1])
    if not uid:
        raise HTTPException(401, "Unauthorized")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(401, "Unauthorized")

    return {"id": user.id, "email": user.email, "is_pro": bool(getattr(user, "is_pro", False))}
