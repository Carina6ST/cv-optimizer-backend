from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    ENV: str = "development"
    
    # CORS - Convert string to list for FastAPI
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"
    
    # AI Configuration
    AI_PROVIDER: str = "mock"  # "openai" or "mock"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Storage Configuration
    STORAGE_PROVIDER: str = "local"  # "local" or "s3"
    
    # S3 Configuration (only needed if STORAGE_PROVIDER=s3)
    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str = "us-east-1"
    S3_BUCKET: str = "cv-optimizer-files"
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_PUBLIC_BASE_URL: str | None = None
    
    # Email (optional - for notifications)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_FROM: str = "noreply@cv-optimizer.com"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def cors_origins(self) -> List[str]:
        """Convert CORS origins string to list for FastAPI"""
        return [origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Global settings instance
settings = get_settings()