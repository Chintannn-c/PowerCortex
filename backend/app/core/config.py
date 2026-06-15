"""
PowerCortex – Application Configuration

Reads environment variables via pydantic-settings and exposes
a singleton ``Settings`` instance consumed throughout the app.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List


class Settings(BaseSettings):
    """Typed, validated application settings sourced from ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── MongoDB ────────────────────────────────────────────────
    MONGODB_URL: str = "mongodb://mongo:27017" # Default to docker service name
    DATABASE_NAME: str = "powercortex"

    # ── JWT ────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── App Metadata ──────────────────────────────────────────
    APP_NAME: str = "PowerCortex"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── SMTP Settings ──────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SENDER: str = ""

    # ── External API Keys ──────────────────────────────────────
    OPENWEATHER_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ── API / Deployment ──────────────────────────────────────
    API_BASE_URL: str = ""
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://10.0.2.2:8000", "http://127.0.0.1:8000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    ALLOW_DEMO_DATA: bool = False
    ALLOW_MODEL_FALLBACKS: bool = False
    REQUIRE_WEATHER_FOR_FORECASTS: bool = True

    # ── Default Location ──────────────────────────────────────
    DEFAULT_CITY: str = "Ahmedabad"
    DEFAULT_LATITUDE: float = 23.0225
    DEFAULT_LONGITUDE: float = 72.5714

    @model_validator(mode='after')
    def validate_security(self) -> 'Settings':
        if not self.DEBUG:
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production.")
            if "*" in self.CORS_ORIGINS:
                raise ValueError("Wildcard CORS_ORIGINS are forbidden in production.")
        return self


# Global singleton – import this wherever settings are needed.
settings = Settings()
