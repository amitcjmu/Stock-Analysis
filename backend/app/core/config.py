"""
Configuration settings for the AI Force Migration Platform.
Supports both local development and Railway.app deployment.
"""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings

from pydantic import Field
import os
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    APP_NAME: str = "AI Force Migration Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Frontend URL
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    
    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/migration_db",
        env="DATABASE_URL"
    )
    
    # Railway.app specific database URL (if available)
    @property
    def database_url_async(self) -> str:
        """Convert DATABASE_URL to async format for SQLAlchemy."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL
    
    # DeepInfra API Configuration
    DEEPINFRA_API_KEY: str = Field(
        default="U8JskPYWXprQvw2PGbv4lyxfcJQggI48", 
        env="DEEPINFRA_API_KEY"
    )
    DEEPINFRA_MODEL: str = Field(
        default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        env="DEEPINFRA_MODEL"
    )
    DEEPINFRA_BASE_URL: str = Field(
        default="https://api.deepinfra.com/v1/inference",
        env="DEEPINFRA_BASE_URL"
    )
    
    @property
    def deepinfra_model_url(self) -> str:
        """Get the full DeepInfra model URL."""
        return f"{self.DEEPINFRA_BASE_URL}/{self.DEEPINFRA_MODEL}"
    
    # Removed OpenAI support - using DeepInfra exclusively
    
    # Security settings
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS settings
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8080",
        env="ALLOWED_ORIGINS"
    )
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert ALLOWED_ORIGINS string to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")
    
    # CrewAI settings (using DeepInfra)
    CREWAI_ENABLED: bool = Field(default=True, env="CREWAI_ENABLED")
    CREWAI_MODEL: str = Field(
        default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", 
        env="CREWAI_MODEL"
    )
    CREWAI_TEMPERATURE: float = Field(default=0.7, env="CREWAI_TEMPERATURE")
    CREWAI_MAX_TOKENS: int = Field(default=2048, env="CREWAI_MAX_TOKENS")
    
    # Migration specific settings
    MAX_ASSETS_PER_SCAN: int = Field(default=1000, env="MAX_ASSETS_PER_SCAN")
    DEFAULT_MIGRATION_TIMELINE_DAYS: int = Field(default=90, env="DEFAULT_MIGRATION_TIMELINE_DAYS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


# Create global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the appropriate database URL for the current environment."""
    # Railway.app provides DATABASE_URL automatically
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return settings.database_url_async
    
    # Local development
    return settings.database_url_async


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENVIRONMENT.lower() in ["production", "prod"]


def is_railway_deployment() -> bool:
    """Check if running on Railway.app."""
    return bool(os.getenv("RAILWAY_ENVIRONMENT")) 