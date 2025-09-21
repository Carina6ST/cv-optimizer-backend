# backend/routers/resume.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from db.session import SessionLocal
# If you don't have a Resume table, you can remove these 2 lines
from db.models import Resume
from routers.auth import get_current_user_id
from services import parser

router = APIRouter(prefix="/resumes", tags=["resumes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", response_model=None)
async def upload_resume(
    file: UploadFile = File(...),
    authorization: str = Header(default=None),
    db: Session = Depends(get_db),
):
    # Require JWT
    uid = get_current_user_id(authorization.replace("Bearer ", "")) if authorization else None
    if not uid:
        raise HTTPException(401, "Unauthorized")

    # Parse in memory (no file storage)
    content = await file.read()
    text = parser.extract_text_bytes(content, filename=file.filename or "")
    if not text.strip():
        raise HTTPException(400, "Could not extract text from the uploaded file")

    # OPTIONAL: persist a text snapshot (ignore errors if table not present)
    saved_id = None
    try:
        res = Resume(user_id=uid, filename=file.filename, path="", text=text)
        db.add(res)
        db.commit()
        db.refresh(res)
        saved_id = res.id
    except Exception:
        pass

    return {"id": saved_id, "filename": file.filename, "characters": len(text), "preview": text[:800]}
