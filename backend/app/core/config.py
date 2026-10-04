"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables or .env file.
No secrets are hardcoded.
"""

import sys
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "change-this-to-a-random-secret-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_env: str = "development"
    app_debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # --- Database & Cache ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/business_agent"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/business_agent"
    redis_url: str = "redis://localhost:6379/0"

    # --- JWT ---
    jwt_secret_key: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours

    # --- LLM ---
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"

    # --- CORS ---
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # --- SQL Safety ---
    sql_query_timeout_seconds: int = 30
    sql_max_rows: int = 10000

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()


def startup_security_check() -> None:
    """Check critical security settings at startup.

    - In production: halt if the default JWT secret is still in use.
    - In development: log a loud warning but continue.
    """
    if settings.jwt_secret_key == _DEFAULT_JWT_SECRET:
        if not settings.is_development:
            print(
                "[SECURITY ERROR] JWT_SECRET_KEY is set to the default value. "
                "This is a critical security vulnerability in production. "
                "Set a strong random secret in your .env file and restart.",
                flush=True,
            )
            sys.exit(1)
        else:
            print(
                "[SECURITY WARNING] JWT_SECRET_KEY is using the default insecure value. "
                "Set JWT_SECRET_KEY in your .env file before deploying to production.",
                flush=True,
            )
