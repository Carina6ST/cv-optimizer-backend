# backend/routers/analyze.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from db.session import SessionLocal
from routers.auth import get_current_user_id
from services import parser
from services.ats import ats_score
from services.ai import ai_suggestions

router = APIRouter(prefix="/analyze", tags=["analyze"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=None)
async def analyze_cv(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    authorization: str = Header(default=None),
    include_ai: bool = True,
    db: Session = Depends(get_db),
):
    uid = get_current_user_id(authorization.replace("Bearer ", "")) if authorization else None
    if not uid:
        raise HTTPException(401, "Unauthorized")

    content = await file.read()
    cv_text = parser.extract_text_bytes(content, filename=file.filename or "")
    if not cv_text.strip():
        raise HTTPException(400, "Could not extract text from the uploaded file")

    ats = ats_score(cv_text, job_description)
    ai = ai_suggestions(cv_text, job_description) if include_ai else None

    return {
        "filename": file.filename,
        "length_cv_chars": len(cv_text),
        "ats": ats,
        "ai": ai,
    }

@router.post("/text", response_model=None)
async def analyze_text(
    cv_text: str = Form(...),
    job_description: str = Form(...),
    authorization: str = Header(default=None),
    include_ai: bool = True,
    db: Session = Depends(get_db),
):
    uid = get_current_user_id(authorization.replace("Bearer ", "")) if authorization else None
    if not uid:
        raise HTTPException(401, "Unauthorized")

    ats = ats_score(cv_text, job_description)
    ai = ai_suggestions(cv_text, job_description) if include_ai else None
    return {"ats": ats, "ai": ai}
