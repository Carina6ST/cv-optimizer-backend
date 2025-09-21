# backend/routers/health.py
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health", response_model=None)
def health():
    return {"status": "ok"}
