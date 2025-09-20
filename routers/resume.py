from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import os, shutil
from db.session import SessionLocal
from db.models import Resume
from services import parser
from routers.auth import get_current_user_id

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/resume/upload")
async def upload_resume(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(401, "Missing Authorization")
    token = authorization.replace("Bearer ", "")
    user_id = get_current_user_id(token)

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(400, "Only PDF or DOCX allowed")

    dest_path = os.path.join(UPLOAD_DIR, f"{user_id}_{file.filename}")
    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    text = parser.extract_text(dest_path)
    resume = Resume(filename=file.filename, path=dest_path, text=text, owner_id=user_id)
    db.add(resume); db.commit(); db.refresh(resume)

    return {"id": resume.id, "filename": resume.filename, "text_preview": (text or "")[:500]}
