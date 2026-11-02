"""Configuration settings loaded from environment variables."""

import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PayPal Configuration
    PAYPAL_CLIENT_ID: str = Field(default="test", description="PayPal REST Client ID")
    PAYPAL_CLIENT_SECRET: str = Field(default="test", description="PayPal REST Secret")
    PAYPAL_MODE: str = Field(default="sandbox", description="PayPal Mode: sandbox or live")
    PAYPAL_WEBHOOK_ID: str = Field(default="test-webhook-id", description="Subscribed Webhook ID")
    PAYPAL_API_BASE: str = Field(
        default="https://api-m.sandbox.paypal.com",
        description="PayPal API Endpoint Base URL",
    )

    # Database
    DATABASE_URL: str = Field(
        default="sqlite:///./promiseloop.db",
        description="Database connection URL (PostgreSQL in production, SQLite in test/dev)",
    )

    # External Provider Keys (optional, graceful fallback if empty)
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    OPENROUTER_API_KEY: str = Field(default="", description="OpenRouter API Key")
    CHANNEL3_API_KEY: str = Field(default="", description="Channel3 API Key")

    # Application settings
    APP_NAME: str = "PromiseLoop"
    ENVIRONMENT: str = Field(default="development", description="development | staging | production | test")
    DEMO_MODE: bool = Field(default=True, description="Enable simulated fallback and synthetic test harnesses")
    ADMIN_TOKEN: str = Field(default="", description="Token for seed/admin endpoints; empty disables them")
    LLM_RATE_LIMIT_PER_MIN: int = Field(default=10, description="Per-IP requests/min on LLM-backed endpoints")
    SECRET_KEY: str = Field(default="promiseloop-dev-secret-key-change-in-prod")
    CORS_ORIGINS: Union[str, List[str]] = Field(default=["*"])
    PORT: int = Field(default=8000)

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    return json.loads(s)
                except Exception:
                    pass
            return [x.strip() for x in s.split(",") if x.strip()]
        return v


settings = Settings()
