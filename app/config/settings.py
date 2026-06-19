from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "Route Optimization API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Stripe
    STRIPE_SECRET_KEY: str = None
    STRIPE_PUBLISHABLE_KEY: str = None
    STRIPE_WEBHOOK_SECRET: str = None

    # Password Reset
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    # TrendRoute
    TRENDROUTE_API_KEY: str = None
    TRENDROUTE_SERVICE_URL: str = "https://benchmarker.dev.trendroute.se"
    TRENDROUTE_SOLVE_ROUTE_OPTIMIZATION_ENDPOINT: str = (
        "/api/v1/route-optimization/multi"
    )
    TRENDROUTE_SOLVE_ROUTE_RECALCULATION_ENDPOINT: str = "/api/v1/route-recalculation/"
    TRENDROUTE_GEOSPATIAL_DIRECTIONS_ENDPOINT: str = "/api/v1/geospatial/direction"

    # CORS
    CORS_ORIGINS: list = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]

    # Security
    BCRYPT_LOG_ROUNDS: int = 12
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis (optional, for caching/sessions)
    REDIS_URL: Optional[str] = None

    # LLM Provider (openai, anthropic)
    LLM_PROVIDER: str = "openai"

    # OpenAI Configuration
    OPENAI_API_KEY: str = None

    # Anthropic Configuration
    ANTHROPIC_API_KEY: str = ""

    # Model Configuration
    MODEL_NAME: str = "gpt-4o-mini"
    SYSTEM_PROMPT: str = (
        """You are an OCR assistant. Extract text from images and return structured JSON data according to the provided schema."""
    )
    TEMPERATURE: int = 0
    SCHEMA_CONFIG_PATH: str = "/app/app/core/entities/ocr_config.yml"

    # Logging
    LOG_LEVEL: str = "INFO"

    # upload directory
    UPLOAD_DIR: str = Field(
        default="/app/uploads",  # ← Match the container path
        description="Upload directory for files",
    )

    # Email settings
    SENDING_EMAIL_ENABLED: bool = Field(
        default=True,
        description="Enable or disable sending emails",
    )
    SMTP_HOST: str = Field(
        default="systemmail.ecolosplus.se",
        description="SMTP server host",
    )
    SMTP_PORT: int = Field(
        default=465,
        description="SMTP server port",
    )
    SMTP_USER: str = Field(
        default="admin@systemmail.ecolosplus.se",
        description="SMTP server username",
    )
    SMTP_PASSWORD: str = Field(
        default=None,
        description="SMTP server password",
    )
    FROM_EMAIL: str = Field(
        default="admin@systemmail.ecolosplus.se",
        description="From email address",
    )
    IMAP_HOST: str = Field(
        default="systemmail.ecolosplus.se",
        description="IMAP server host",
    )
    IMAP_PORT: int = Field(
        default=993,
        description="IMAP server port",
    )
    IMAP_USER: str = Field(
        default="admin@systemmail.ecolosplus.se",
        description="IMAP server username",
    )
    IMAP_PASSWORD: str = Field(
        default=None,
        description="IMAP server password",
    )
    IMAP_SENT_FOLDER: str = Field(
        default="Sent",
        description="IMAP folder for sent emails",
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
