from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import json

from db.session import SessionLocal
from db.models import Resume, Analysis
from routers.auth import get_current_user_id
from services import parser, ats, ai

router = APIRouter(prefix="/analyze", tags=["analyze"])

# Pydantic models
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

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("")
async def analyze_cv_file(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    authorization: str = Header(default=None),
    include_ai: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Analyze CV from uploaded file"""
    uid = get_current_user_id(authorization.replace("Bearer ", "")) if authorization else None
    if not uid:
        raise HTTPException(401, "Unauthorized")

    # Read and parse file
    content = await file.read()
    cv_text = parser.extract_text_bytes(content, filename=file.filename or "")
    if not cv_text.strip():
        raise HTTPException(400, "Could not extract text from the uploaded file")

    # Perform analysis
    matched, missing = ats.find_keywords(cv_text, job_description)
    readability = ats.readability(cv_text)
    ats_report = ats.ats_check(cv_text)
    
    # AI suggestions (conditional)
    ai_out = ai.improve_resume(cv_text, job_description) if include_ai else {
        "summary": "", "bullets": [], "cover_letter": ""
    }

    # Save to database
    analysis_rec = Analysis(
        owner_id=uid,
        job_description=job_description,
        result_json=json.dumps({
            "matched_keywords": matched,
            "missing_keywords": missing,
            "readability": readability,
            "ats_check": ats_report,
            "improved_summary": ai_out["summary"],
            "improved_bullets": ai_out["bullets"],
            "cover_letter": ai_out["cover_letter"],
        }),
        score=ats_score if (ats_score := ats_report.get('score', 0)) else None
    )
    db.add(analysis_rec)
    db.commit()

    return {
        "filename": file.filename,
        "length_cv_chars": len(cv_text),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "readability": readability,
        "ats_check": ats_report,
        "improved_summary": ai_out["summary"],
        "improved_bullets": ai_out["bullets"],
        "cover_letter": ai_out["cover_letter"],
        "analysis_id": analysis_rec.id  # Return the analysis ID for reference
    }

@router.post("/text")
async def analyze_text(
    cv_text: str = Form(...),
    job_description: str = Form(...),
    authorization: str = Header(default=None),
    include_ai: bool = Form(True),
    db: Session = Depends(get_db)
):
    """Analyze CV from text input"""
    uid = get_current_user_id(authorization.replace("Bearer ", "")) if authorization else None
    if not uid:
        raise HTTPException(401, "Unauthorized")

    # Perform analysis
    matched, missing = ats.find_keywords(cv_text, job_description)
    readability = ats.readability(cv_text)
    ats_report = ats.ats_check(cv_text)
    
    # AI suggestions (conditional)
    ai_out = ai.improve_resume(cv_text, job_description) if include_ai else {
        "summary": "", "bullets": [], "cover_letter": ""
    }

    # Save to database
    analysis_rec = Analysis(
        owner_id=uid,
        job_description=job_description,
        result_json=json.dumps({
            "matched_keywords": matched,
            "missing_keywords": missing,
            "readability": readability,
            "ats_check": ats_report,
            "improved_summary": ai_out["summary"],
            "improved_bullets": ai_out["bullets"],
            "cover_letter": ai_out["cover_letter"],
        }),
        score=ats_score if (ats_score := ats_report.get('score', 0)) else None
    )
    db.add(analysis_rec)
    db.commit()

    return {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "readability": readability,
        "ats_check": ats_report,
        "improved_summary": ai_out["summary"],
        "improved_bullets": ai_out["bullets"],
        "cover_letter": ai_out["cover_letter"],
        "analysis_id": analysis_rec.id
    }

@router.post("/resume", response_model=AnalyzeResponse)
def analyze_saved_resume(
    payload: AnalyzeRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Analyze a previously saved resume"""
    if not authorization:
        raise HTTPException(401, "Missing Authorization")
    user_id = get_current_user_id(authorization.replace("Bearer ", ""))

    if not (payload.resume_id or payload.resume_text):
        raise HTTPException(400, "Provide resume_id or resume_text")

    # Get resume text
    if payload.resume_text:
        resume_text = payload.resume_text
    else:
        res = db.query(Resume).filter(Resume.id == payload.resume_id, Resume.owner_id == user_id).first()
        if not res:
            raise HTTPException(404, "Resume not found")
        resume_text = res.text or parser.extract_text(res.path) or ""

    # Perform analysis
    matched, missing = ats.find_keywords(resume_text, payload.job_description or "")
    readability = ats.readability(resume_text)
    ats_report = ats.ats_check(resume_text)
    ai_out = ai.improve_resume(resume_text, payload.job_description or "")

    # Prepare response
    result = AnalyzeResponse(
        matched_keywords=matched,
        missing_keywords=missing,
        readability=readability,
        ats_check=ats_report,
        improved_summary=ai_out["summary"],
        improved_bullets=ai_out["bullets"],
        cover_letter=ai_out["cover_letter"],
    )

    # Save to database
    rec = Analysis(
        resume_id=payload.resume_id,
        owner_id=user_id,
        job_description=payload.job_description or "",
        result_json=result.model_dump_json(),
        score=ats_score if (ats_score := ats_report.get('score', 0)) else None,
        analysis_type="resume_analysis"
    )
    db.add(rec)
    db.commit()
    
    return result