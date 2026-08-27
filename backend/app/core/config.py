from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Application
    APP_ENV: str = Field(default="development")
    APP_NAME: str = Field(default="ai-course-video-generator")
    APP_DEBUG: bool = Field(default=True)

    BACKEND_PORT: int = Field(default=8000)
    FRONTEND_PORT: int = Field(default=5173)

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@postgres:5432/course_generator"
    )

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    OPENAI_TEMPERATURE: float = Field(default=0.2)
    OPENAI_TIMEOUT: int = Field(default=60)
    OPENAI_MAX_RETRIES: int = Field(default=3)

    # HeyGen
    HEYGEN_MODE: str = Field(default="mock")
    HEYGEN_API_KEY: Optional[str] = Field(default=None)
    HEYGEN_BASE_URL: str = Field(default="https://api.heygen.com")
    HEYGEN_AVATAR_ID: Optional[str] = Field(default=None)
    HEYGEN_VOICE_ID: Optional[str] = Field(default=None)
    HEYGEN_TEMPLATE_ID: Optional[str] = Field(default=None)
    HEYGEN_WEBHOOK_SECRET: Optional[str] = Field(default=None)
    HEYGEN_TIMEOUT: int = Field(default=120)
    HEYGEN_MAX_RETRIES: int = Field(default=3)

    # File Upload
    MAX_FILE_SIZE_MB: int = Field(default=50)
    STORAGE_BASE_PATH: str = Field(default="/app/storage")

    # Default Course
    DEFAULT_LANGUAGE: str = Field(default="es")
    DEFAULT_DURATION_MINUTES: int = Field(default=10)

    # QA
    QA_MIN_SCORE: int = Field(default=80)
    QA_MODEL: str = Field(default="gpt-4o-mini")

    # Prompt Versions
    ANALYZER_PROMPT_VERSION: str = Field(default="1.0")
    PEDAGOGICAL_PROMPT_VERSION: str = Field(default="1.0")
    SCRIPT_PROMPT_VERSION: str = Field(default="1.0")
    VIDEO_PROMPT_VERSION: str = Field(default="1.0")
    QA_PROMPT_VERSION: str = Field(default="1.0")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    # CORS
    CORS_ORIGINS: str | List[str] = Field(
        default="http://localhost:5173,http://frontend:5173"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS_ORIGINS: {v}")

    @property
    def is_mock_mode(self) -> bool:
        return self.HEYGEN_MODE.lower() == "mock"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
