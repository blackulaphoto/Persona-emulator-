"""Application configuration and settings."""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Application
    app_name: str = "Persona Evolution Simulator"
    
    # Database
    database_url: str
    
    # OpenAI
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Security
    jwt_secret: str
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Frontend
    frontend_url: str = "http://localhost:3000"
    
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
