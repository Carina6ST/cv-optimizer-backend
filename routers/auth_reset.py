from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, EmailStr
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import User
from core.config import settings
from services.emailer import send_email
from passlib.context import CryptContext
import os

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET = settings.SECRET_KEY
SALT   = "password-reset"
TOKEN_MAX_AGE = 60 * 60 * 2  # 2 hours

def signer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(SECRET, salt=SALT)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ResetRequest(BaseModel):
    email: EmailStr

class ResetApply(BaseModel):
    token: str
    new_password: str

@router.post("/request-reset", response_model=dict)
def request_reset(payload: ResetRequest, bg: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        token = signer().dumps({"uid": user.id, "email": user.email})
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        reset_link = f"{frontend_url}/reset-password?token={token}"
        subject = "Reset your CV Optimizer password"
        html = f"""
        <h2>Reset your password</h2>
        <p>Click the link below to set a new password (valid for 2 hours):</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        """
        bg.add_task(send_email, user.email, subject, html)
    return {"ok": True}

@router.post("/reset-password", response_model=dict)
def reset_password(payload: ResetApply, db: Session = Depends(get_db)):
    try:
        data = signer().loads(payload.token, max_age=TOKEN_MAX_AGE)
    except SignatureExpired:
        raise HTTPException(400, "Reset link expired")
    except BadSignature:
        raise HTTPException(400, "Invalid reset link")

    uid = data.get("uid")
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(400, "Invalid user")

    user.password_hash = pwd_ctx.hash(payload.new_password)
    db.commit()
    return {"ok": True}
