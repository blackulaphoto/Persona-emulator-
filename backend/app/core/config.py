"""Application configuration and settings."""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    app_name: str = "Persona Evolution Simulator"
    
    # Database
    database_url: str = Field(default="sqlite:///./dev.db", env="DATABASE_URL")
    
    # OpenAI (optional to allow service startup without key)
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    
    # Security
    jwt_secret: str = Field(default="change-me", env="JWT_SECRET")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Frontend
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    additional_cors_origins: List[str] = Field(
        default_factory=list,
        env="ADDITIONAL_CORS_ORIGINS",
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
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "forbid"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
