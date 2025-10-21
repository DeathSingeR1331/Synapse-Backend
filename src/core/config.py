from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    # ---------------- Core App ----------------
    PROJECT_NAME: str = "Synapse Project"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "production"

    # ---------------- PostgreSQL ----------------
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_DSN: Optional[str] = None

    @field_validator("DATABASE_DSN", mode="before")
    @classmethod
    def assemble_db_connection(cls, v, info):
        if isinstance(v, str):
            return v
        # Check if we have all required PostgreSQL fields
        if not all([info.data.get("POSTGRES_USER"), info.data.get("POSTGRES_PASSWORD"), 
                   info.data.get("POSTGRES_SERVER"), info.data.get("POSTGRES_DB")]):
            return None
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data["POSTGRES_USER"],
            password=info.data["POSTGRES_PASSWORD"],
            host=info.data["POSTGRES_SERVER"],
            path=f"{info.data['POSTGRES_DB']}",
        ))

    # ---------------- Redis ----------------
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v, info):
        if isinstance(v, str):
            return v
        # Check if we have Redis host
        if not info.data.get("REDIS_HOST"):
            return None
        return str(RedisDsn.build(
            scheme="redis",
            host=info.data["REDIS_HOST"],
            port=info.data.get("REDIS_PORT", 6379),
            path=f"/{info.data.get('REDIS_DB', 0)}",
        ))

    # ---------------- Celery ----------------
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v, info):
        if isinstance(v, str):
            return v
        # Check if we have Redis host
        if not info.data.get("REDIS_HOST"):
            return None
        return str(RedisDsn.build(
            scheme="redis",
            host=info.data["REDIS_HOST"],
            port=info.data.get("REDIS_PORT", 6379),
            path="/1",  # Broker uses Redis DB 1
        ))

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v, info):
        if isinstance(v, str):
            return v
        # Check if we have Redis host
        if not info.data.get("REDIS_HOST"):
            return None
        return str(RedisDsn.build(
            scheme="redis",
            host=info.data["REDIS_HOST"],
            port=info.data.get("REDIS_PORT", 6379),
            path="/2",  # Results use Redis DB 2
        ))
        
    # ---------------- Authentication ----------------
    JWT_SECRET_KEY: Optional[str] = None
    JWT_REFRESH_SECRET_KEY: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---------------- Google OAuth2 ----------------
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # ---------------- Session Management ----------------
    SESSION_SECRET_KEY: Optional[str] = None

    # ---------------- Qdrant ----------------
    QDRANT_HOST: Optional[str] = None
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    
    # ---------------- ML / AI Worker ----------------
    ML_DEVICE: str = "cpu"
    USE_API_LLM: bool = False
    GEMINI_API_KEY: Optional[str] = None
    ML_MODEL_PATH: Optional[str] = None

    # ---------------- Pydantic Settings Config ----------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Global settings instance
settings = Settings()
# Add this line for debugging
print(f"[DEBUG] JWT Refresh Secret Key Loaded: {'Yes' if settings.JWT_REFRESH_SECRET_KEY else 'NO!!!'}")