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

@router.post("")
async def rewrite_cv(
    cv_text: str = Form(..., min_length=10, description="CV text to rewrite (min 10 chars)"),
    job_description: str = Form(..., min_length=5, description="Job description for context"),
    authorization: str = Header(..., description="Bearer token"),
    db: Session = Depends(get_db)
):
    """
    Rewrite CV text using AI (Pro feature only)
    
    Returns:
        HTTP 402 if user is not a Pro subscriber
        HTTP 200 with rewritten text if successful
    """
    # Validate authorization
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    uid = get_current_user_id(token)
    
    if not uid:
        raise HTTPException(401, "Invalid token")

    # Get user and check Pro status
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(401, "User not found")
    
    if not user.is_pro:
        raise HTTPException(
            status_code=402, 
            detail="Upgrade to Pro to use AI rewrite features"
        )

    # Validate input
    if not cv_text.strip():
        raise HTTPException(400, "CV text cannot be empty")
    
    if not job_description.strip():
        raise HTTPException(400, "Job description cannot be empty")

    try:
        # Call AI service
        rewritten = await ai_rewrite(cv_text, job_description)
        
        if not rewritten or not rewritten.strip():
            raise HTTPException(500, "AI service returned empty response")
            
        return {
            "success": True,
            "rewritten": rewritten,
            "original_length": len(cv_text),
            "rewritten_length": len(rewritten)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error for debugging
        print(f"AI rewrite error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="AI rewrite service temporarily unavailable. Please try again later."
        )