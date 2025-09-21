# backend/routers/resume.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Depends
from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import Resume  # if you don't have this table, remove DB parts below
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
    uid = get_current_user_id(authorization.replace("Bearer ", "")) if authorization else None
    if not uid:
        raise HTTPException(401, "Unauthorized")

    content = await file.read()
    text = parser.extract_text_bytes(content, filename=file.filename or "")
    if not text.strip():
        raise HTTPException(400, "Could not extract text from the uploaded file")

    # OPTIONAL: persist a text snapshot (no binary storage)
    try:
        res = Resume(user_id=uid, filename=file.filename, path="", text=text)
        db.add(res)
        db.commit()
        db.refresh(res)
        saved_id = res.id
    except Exception:
        # If you don't have a Resume model or don't want to store it, ignore DB errors
        saved_id = None

    return {"filename": file.filename, "characters": len(text), "preview": text[:800]}
# Accept legacy singular path too: /resume/upload
router.add_api_route(
    "/resume/upload",  # singular
    upload_resume,
    methods=["POST"],
    response_model=None,
)