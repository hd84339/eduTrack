import os
from functools import lru_cache
from typing import Literal
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration managed through environment variables
    using Pydantic Settings v2.
    """
    APP_NAME: str = "EduTrack"
    APP_ENV: Literal["development", "testing", "staging", "production"] = "development"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/edutrack"
    API_V1_PREFIX: str = "/api/v1"

    # JWT Authentication & Cryptographic Security
    JWT_SECRET_KEY: str = "edutrack-insecure-dev-secret-key-replace-in-production-min32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 1800 seconds per API_DESIGN.md
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12  # Adaptive bcrypt rounds >= 12 per DATABASE_DESIGN.md

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Ensure default placeholder secret is not used in production."""
        if self.APP_ENV == "production":
            if (
                "insecure" in self.JWT_SECRET_KEY.lower()
                or len(self.JWT_SECRET_KEY) < 32
            ):
                raise ValueError(
                    "JWT_SECRET_KEY must be a cryptographically secure key of at least 32 characters in production"
                )
        return self

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached accessor for settings singleton instance.
    """
    return Settings()


settings = get_settings()

