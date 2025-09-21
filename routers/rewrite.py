from fastapi import APIRouter, HTTPException, Form, Header, Depends
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import User
from routers.auth import get_current_user_id
from services.ai import ai_rewrite

router = APIRouter(prefix="/rewrite", tags=["rewrite"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=dict)
def rewrite_cv(
    cv_text: str = Form(...),
    job_description: str = Form(...),
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
):
    uid = get_current_user_id(authorization.replace("Bearer ", "")) if authorization else None
    if not uid:
        raise HTTPException(401, "Unauthorized")

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(401, "Unauthorized")
    if not user.is_pro:
        raise HTTPException(status_code=402, detail="Upgrade required to use CV rewrite")

    rewritten = ai_rewrite(cv_text, job_description)
    return {"rewritten": rewritten}
