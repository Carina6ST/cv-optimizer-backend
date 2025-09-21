from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from core.config import settings
from db.session import Base, engine
from routers import auth, resume, health, auth_reset
from routers import analyze as analyze_router, rewrite as rewrite_router

# Create all tables first
Base.metadata.create_all(bind=engine)

# Add missing columns to existing tables
with engine.connect() as conn:
    try:
        # Add is_pro column to users table if it doesn't exist
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_pro BOOLEAN DEFAULT FALSE"))
        print("✓ Added is_pro column to users table")
    except Exception as e:
        print(f"Note: is_pro column may already exist: {e}")
    
    try:
        # Add created_at column to users table if it doesn't exist
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        print("✓ Added created_at column to users table")
    except Exception as e:
        print(f"Note: created_at column may already exist: {e}")
    
    try:
        # Add new columns to resumes table
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS original_filename VARCHAR"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_size INTEGER"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_type VARCHAR"))
        conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        print("✓ Added new columns to resumes table")
    except Exception as e:
        print(f"Note: Resume columns may already exist: {e}")
    
    try:
        # Add new columns to analyses table
        conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS score INTEGER"))
        conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS analysis_type VARCHAR DEFAULT 'ats'"))
        print("✓ Added new columns to analyses table")
    except Exception as e:
        print(f"Note: Analysis columns may already exist: {e}")
    
    conn.commit()

app = FastAPI(
    title="CV Optimizer API",
    version="1.0.0",
    description="AI-powered CV optimization and ATS scoring API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include all routers
app.include_router(health.router, prefix="", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(auth_reset.router, prefix="/auth", tags=["auth"])
app.include_router(resume.router, prefix="/resumes", tags=["resumes"])
app.include_router(analyze_router.router, prefix="/api", tags=["analysis"])
app.include_router(rewrite_router.router, prefix="/api", tags=["rewrite"])

# Optional: Add startup event for better initialization
@app.on_event("startup")
async def startup_event():
    print("🚀 CV Optimizer API starting up...")
    print(f"🌐 Environment: {settings.ENV}")
    print(f"🔗 CORS origins: {origins}")
    print(f"🗄️  Database: {settings.DATABASE_URL.split('://')[0]}")
    print(f"🤖 AI Provider: {settings.AI_PROVIDER}")

# Health check endpoint (additional to health router)
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "CV Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Optional: Add graceful shutdown
@app.on_event("shutdown")
async def shutdown_event():
    print("👋 CV Optimizer API shutting down...")

# Optional: Exception handler for uniform error responses
@app.exception_handler(500)
async def internal_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "success": False}
    )