import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # MongoDB connection URL (use Atlas connection string for Vercel/Production deployment)
    DATABASE_URL: str = "mongodb://localhost:27017/resumeiq_db"
    JWT_SECRET: str = "super_secret_jwt_key_resumeiq_ai_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
