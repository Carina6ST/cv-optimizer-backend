# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from core.config import settings
from db.session import Base, engine
from routers import auth, resume, health, auth_reset
from routers import analyze as analyze_router, rewrite as rewrite_router

# --- DB bootstrap -------------------------------------------------------------
Base.metadata.create_all(bind=engine)

with engine.begin() as conn:
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_pro BOOLEAN DEFAULT FALSE"))
    except Exception as e:
        print(f"[users.is_pro] note: {e}")
    try:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    except Exception as e:
        print(f"[users.created_at] note: {e}")
    try:
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS original_filename VARCHAR"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_size INTEGER"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_type VARCHAR"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    except Exception as e:
        print(f"[resumes.*] note: {e}")
    try:
        conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS score INTEGER"))
        conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS analysis_type VARCHAR DEFAULT 'ats'"))
    except Exception as e:
        print(f"[analyses.*] note: {e}")

# --- App ----------------------------------------------------------------------
app = FastAPI(
    title="CV Optimizer API",
    version="1.0.0",
    description="AI-powered CV optimization and ATS scoring API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (no extra prefixes; they already have them)
app.include_router(health.router)          # /health
app.include_router(auth.router)            # /auth/*
app.include_router(auth_reset.router)      # /auth/*
app.include_router(resume.router)          # /resumes/*

# /api namespace for analyze & rewrite
app.include_router(analyze_router.router, prefix="/api")   # /api/analyze/*
app.include_router(rewrite_router.router, prefix="/api")   # /api/rewrite/*

# Legacy alias: also accept /resume/upload (singular)
from routers.resume import upload_resume as _resume_upload
app.add_api_route("/resume/upload", _resume_upload, methods=["POST"])

# Lifecycle & misc
@app.on_event("startup")
async def startup_event():
    print("🚀 CV Optimizer API starting…")
    print(f"🌐 ENV: {settings.ENV}")
    print(f"🔗 CORS origins: {origins}")
    try:
        print(f"🗄️  DB: {settings.DATABASE_URL.split('://', 1)[0]}")
    except Exception:
        pass
    print(f"🤖 AI Provider: {settings.AI_PROVIDER}")

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "CV Optimizer API", "version": "1.0.0", "docs": "/docs", "health": "/health"}

@app.on_event("shutdown")
async def shutdown_event():
    print("👋 CV Optimizer API shutting down…")

@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "success": False})
