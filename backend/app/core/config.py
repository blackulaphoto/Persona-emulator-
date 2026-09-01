"""Application configuration and settings."""
from functools import lru_cache
from typing import List, Optional
import os

from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    app_name: str = "Persona Evolution Simulator"
    
    # Database
    database_url: str = Field(default="sqlite:///./dev.db", env="DATABASE_URL")
    
    # OpenAI (optional to allow service startup without key). Accept OPENAI_API_KEY or OPENAI_KEY.
    openai_api_key: str | None = Field(
        default_factory=lambda: os.getenv("OPENAI_KEY"),
        validation_alias=AliasChoices("OPENAI_API_KEY", "OPENAI_KEY"),
    )
    
    # Security
    jwt_secret: str = Field(default="change-me", env="JWT_SECRET")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Frontend
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    additional_cors_origins_raw: Optional[str] = Field(default=None, env="ADDITIONAL_CORS_ORIGINS")

    # Firebase Authentication (read directly via os.getenv in app/core/auth.py,
    # not through this Settings object - declared here only so Config.extra =
    # "forbid" below doesn't crash Settings() the moment any of these are set
    # in a local backend/.env file, which is exactly how backend/.env.example
    # documents setting them up for local dev).
    firebase_service_account_json: Optional[str] = Field(default=None, env="FIREBASE_SERVICE_ACCOUNT_JSON")
    firebase_auth_emulator_host: Optional[str] = Field(default=None, env="FIREBASE_AUTH_EMULATOR_HOST")
    gcloud_project: Optional[str] = Field(default=None, env="GCLOUD_PROJECT")
    auth_dev_bypass: bool = Field(default=False, env="AUTH_DEV_BYPASS")

    # Research-preview access. These are Firebase UIDs, not frontend labels
    # or emails, and are compared only with the UID from a verified token.
    preview_limit_exempt_user_ids_raw: Optional[str] = Field(
        default=None,
        validation_alias="PREVIEW_LIMIT_EXEMPT_USER_IDS",
    )
    
    # Feature Flags - explicit env var names for clarity
    # Default to True in dev mode (can be overridden via .env)
    feature_clinical_templates: bool = Field(
        default=True,  # Enabled by default in dev
        env="FEATURE_CLINICAL_TEMPLATES"
    )
    feature_remix_timeline: bool = Field(
        default=True,  # Enabled by default in dev
        env="FEATURE_REMIX_TIMELINE"
    )
    
    @property
    def additional_cors_origins(self) -> List[str]:
        """
        Return parsed additional CORS origins from a comma-separated env var.
        Accepts empty/undefined values without failing JSON parsing.
        """
        if not self.additional_cors_origins_raw:
            return []
        return [
            origin.rstrip("/").strip()
            for origin in self.additional_cors_origins_raw.split(",")
            if origin and origin.strip()
        ]

    @property
    def preview_limit_exempt_user_ids(self) -> set[str]:
        if not self.preview_limit_exempt_user_ids_raw:
            return set()
        return {
            user_id.strip()
            for user_id in self.preview_limit_exempt_user_ids_raw.split(",")
            if user_id and user_id.strip()
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
