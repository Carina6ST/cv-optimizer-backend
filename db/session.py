# backend/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Add sslmode=require automatically if you're on an External Postgres URL without it
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

use_ssl = DATABASE_URL.startswith("postgresql://") and "sslmode=" not in DATABASE_URL and (
    "render.com" in DATABASE_URL or "amazonaws.com" in DATABASE_URL or "compute" in DATABASE_URL
)

if use_ssl:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # avoid stale connections after idle/suspend
    pool_recycle=1800,           # recycle every 30 min
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
