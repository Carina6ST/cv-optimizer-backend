from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from db.session import Base, engine
from routers import auth, resume, analyze, health
from routers import auth_reset


Base.metadata.create_all(bind=engine)

app = FastAPI(title="CV Optimizer API", version="1.0.0")

origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="", tags=["health"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(resume.router, tags=["resume"])
app.include_router(analyze.router, tags=["analyze"])
app.include_router(auth_reset.router)