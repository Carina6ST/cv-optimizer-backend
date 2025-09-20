from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    DATABASE_URL: str = "sqlite:///./dev.db"
    AI_PROVIDER: str = "mock" # 'openai' or 'mock'
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    ENV: str = "development"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
