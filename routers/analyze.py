from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from db.session import SessionLocal
from db.models import Resume, Analysis
from routers.auth import get_current_user_id
from services import ai, ats, parser
from pydantic import BaseModel

router = APIRouter()

class AnalyzeRequest(BaseModel):
    resume_id: Optional[int] = None
    job_description: Optional[str] = ""
    resume_text: Optional[str] = None

class AnalyzeResponse(BaseModel):
    matched_keywords: list[str]
    missing_keywords: list[str]
    readability: dict
    ats_check: dict
    improved_summary: str
    improved_bullets: list[str]
    cover_letter: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_resume(
    payload: AnalyzeRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(401, "Missing Authorization")
    user_id = get_current_user_id(authorization.replace("Bearer ", ""))

    if not (payload.resume_id or payload.resume_text):
        raise HTTPException(400, "Provide resume_id or resume_text")

    if payload.resume_text:
        resume_text = payload.resume_text
    else:
        res = db.query(Resume).filter_by(id=payload.resume_id).first()
        if not res:
            raise HTTPException(404, "Resume not found")
        resume_text = res.text or parser.extract_text(res.path) or ""

    matched, missing = ats.find_keywords(resume_text, payload.job_description or "")
    readability = ats.readability(resume_text)
    ats_report = ats.ats_check(resume_text)
    ai_out = ai.improve_resume(resume_text, payload.job_description or "")

    result = AnalyzeResponse(
        matched_keywords=matched,
        missing_keywords=missing,
        readability=readability,
        ats_check=ats_report,
        improved_summary=ai_out["summary"],
        improved_bullets=ai_out["bullets"],
        cover_letter=ai_out["cover_letter"],
    )

    rec = Analysis(
        resume_id=payload.resume_id if payload.resume_id else None,
        owner_id=user_id,
        job_description=payload.job_description or "",
        result_json=result.model_dump_json(),
    )
    db.add(rec); db.commit()
    return result
