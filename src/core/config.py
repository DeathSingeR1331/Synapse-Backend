from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # ---------------- Core App ----------------
    PROJECT_NAME: str = "Synapse Project"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "production"

    # ---------------- PostgreSQL ----------------
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str
    DATABASE_DSN: Optional[str] = None

    @field_validator("DATABASE_DSN", mode="before")
    @classmethod
    def assemble_db_connection(cls, v, info):
        if isinstance(v, str):
            return v
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data["POSTGRES_USER"],
            password=info.data["POSTGRES_PASSWORD"],
            host=info.data["POSTGRES_SERVER"],
            path=f"{info.data['POSTGRES_DB']}",
        ))

    # ---------------- Redis ----------------
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v, info):
        if isinstance(v, str):
            return v
        return str(RedisDsn.build(
            scheme="redis",
            host=info.data["REDIS_HOST"],
            port=info.data["REDIS_PORT"],
            path=f"/{info.data['REDIS_DB']}",
        ))

    # ---------------- Celery ----------------
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v, info):
        if isinstance(v, str):
            return v
        return str(RedisDsn.build(
            scheme="redis",
            host=info.data["REDIS_HOST"],
            port=info.data["REDIS_PORT"],
            path="/1",  # Broker uses Redis DB 1
        ))

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v, info):
        if isinstance(v, str):
            return v
        return str(RedisDsn.build(
            scheme="redis",
            host=info.data["REDIS_HOST"],
            port=info.data["REDIS_PORT"],
            path="/2",  # Results use Redis DB 2
        ))
        
    # ---------------- Authentication ----------------
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # ---------------- Google OAuth2 ----------------
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    # ---------------- Session Management ----------------
    SESSION_SECRET_KEY: str

    # ---------------- Qdrant ----------------
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_GRPC_PORT: int
    
    # ---------------- ML / AI Worker ----------------
    ML_DEVICE: str = "cpu"
    USE_API_LLM: bool = False
    GEMINI_API_KEY: str | None = None
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