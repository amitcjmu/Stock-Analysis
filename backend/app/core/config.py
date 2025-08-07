"""
Configuration settings for the AI Modernize Migration Platform.
Supports both local development and Railway.app deployment.
"""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings

import os

from pydantic import ConfigDict, Field, field_validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application settings
    APP_NAME: str = "AI Modernize Migration Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # Server settings
    HOST: str = Field(default="0.0.0.0", env="HOST")  # nosec B104
    PORT: int = Field(default=8000, env="PORT")
    API_V1_STR: str = "/api/v1"

    # Frontend URL
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")

    # Database settings
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/migration_db",
        env="DATABASE_URL",
    )
    DB_ECHO_LOG: bool = Field(default=False, env="DB_ECHO_LOG")

    # Railway.app specific database URL (if available)
    @property
    def database_url_async(self) -> str:
        """Convert DATABASE_URL to async format for SQLAlchemy."""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return self.DATABASE_URL

    # DeepInfra API Configuration
    DEEPINFRA_API_KEY: str = Field(default="", env="DEEPINFRA_API_KEY")
    DEEPINFRA_MODEL: str = Field(
        default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        env="DEEPINFRA_MODEL",
    )
    DEEPINFRA_BASE_URL: str = Field(
        default="https://api.deepinfra.com/v1/openai/chat/completions",
        env="DEEPINFRA_BASE_URL",
    )

    @property
    def deepinfra_model_url(self) -> str:
        """Get the full DeepInfra model URL."""
        return f"{self.DEEPINFRA_BASE_URL}/{self.DEEPINFRA_MODEL}"

    # Removed OpenAI support - using DeepInfra exclusively

    # Security settings
    SECRET_KEY: str = Field(default="", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    ALGORITHM: str = "HS256"

    # Cookie security settings
    COOKIE_SECURE: bool = Field(default=True, env="COOKIE_SECURE")
    COOKIE_SAMESITE: str = Field(default="lax", env="COOKIE_SAMESITE")
    COOKIE_HTTPONLY: bool = Field(default=True, env="COOKIE_HTTPONLY")

    @field_validator("DEEPINFRA_API_KEY")
    @classmethod
    def validate_api_key(cls, v):
        if not v:
            print("⚠️ WARNING: No DEEPINFRA_API_KEY environment variable set.")
            print(
                "⚠️ AI features may not work properly. Set DEEPINFRA_API_KEY for full functionality."
            )
            return "dummy_key_for_development"
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if not v or v == "your-secret-key-here":
            # For development, generate a temporary secret key
            import secrets

            temp_key = secrets.token_urlsafe(32)
            print(
                f"⚠️ WARNING: No SECRET_KEY environment variable set. Using temporary key: {temp_key}"
            )
            print("⚠️ Set SECRET_KEY environment variable for production!")
            return temp_key
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    # CORS settings
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8080",
        env="ALLOWED_ORIGINS",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert ALLOWED_ORIGINS string to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    # WebSocket settings
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, env="WS_HEARTBEAT_INTERVAL")

    # Redis Cache settings
    REDIS_ENABLED: bool = Field(default=True, env="REDIS_ENABLED")
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
    )
    REDIS_DEFAULT_TTL: int = Field(default=3600, env="REDIS_DEFAULT_TTL")  # 1 hour

    # Upstash Redis (for production) - unified configuration

    # CrewAI settings (using DeepInfra)
    CREWAI_ENABLED: bool = True
    CREWAI_FAST_MODE: bool = Field(
        default=False, env="CREWAI_FAST_MODE"
    )  # Disable fast mode by default for better accuracy
    CREWAI_MODEL: str = Field(
        default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", env="CREWAI_MODEL"
    )
    CREWAI_PLANNING_MODEL: str = Field(
        default="google/gemma-2-9b-it", env="CREWAI_PLANNING_MODEL"
    )
    CREWAI_TEMPERATURE: float = Field(default=0.7, env="CREWAI_TEMPERATURE")
    CREWAI_MAX_TOKENS: int = Field(default=2048, env="CREWAI_MAX_TOKENS")

    # LLM Model Configuration for different use cases (following user specifications)
    CREWAI_LLM_MODEL: str = Field(
        default="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        env="CREWAI_LLM_MODEL",
    )
    EMBEDDING_LLM_MODEL: str = Field(
        default="thenlper/gte-large", env="EMBEDDING_LLM_MODEL"
    )
    CHAT_LLM_MODEL: str = Field(default="google/gemma-3-4b-it", env="CHAT_LLM_MODEL")

    # Migration specific settings
    MAX_ASSETS_PER_SCAN: int = Field(default=1000, env="MAX_ASSETS_PER_SCAN")
    DEFAULT_MIGRATION_TIMELINE_DAYS: int = Field(
        default=90, env="DEFAULT_MIGRATION_TIMELINE_DAYS"
    )

    # Enhanced CrewAI Flow Service Configuration
    # Note: Removed timeout restrictions for agentic classification activities
    # These operations can take varying amounts of time based on data load
    # and should not be artificially limited by timeouts
    CREWAI_LLM_TEMPERATURE: float = Field(default=0.0, env="CREWAI_LLM_TEMPERATURE")
    CREWAI_LLM_MAX_TOKENS: int = Field(default=1500, env="CREWAI_LLM_MAX_TOKENS")
    CREWAI_LLM_BASE_URL: str = Field(
        default="https://api.deepinfra.com/v1/openai", env="CREWAI_LLM_BASE_URL"
    )
    CREWAI_RETRY_ATTEMPTS: int = Field(default=3, env="CREWAI_RETRY_ATTEMPTS")
    CREWAI_RETRY_WAIT_SECONDS: int = Field(default=2, env="CREWAI_RETRY_WAIT_SECONDS")
    CREWAI_FLOW_TTL_HOURS: int = Field(default=1, env="CREWAI_FLOW_TTL_HOURS")

    # Upstash Redis Configuration (for production) - moved up to remove duplicate
    UPSTASH_REDIS_URL: str = Field(default="", env="UPSTASH_REDIS_URL")
    UPSTASH_REDIS_TOKEN: str = Field(default="", env="UPSTASH_REDIS_TOKEN")

    model_config = ConfigDict(
        env_file=".env" if os.getenv("RAILWAY_ENVIRONMENT") is None else None,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra environment variables
    )


# Create global settings instance
settings = Settings()


def get_database_url() -> str:
    """Get the appropriate database URL for the current environment."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # Fallback to settings default
        database_url = settings.DATABASE_URL

    # Convert to async format if needed
    if database_url.startswith("postgresql://"):
        # Check if it's already async
        if "+asyncpg" not in database_url:
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

    # Railway.app specific adjustments
    if os.getenv("RAILWAY_ENVIRONMENT") or "railway.app" in database_url:
        # For Railway, don't add sslmode parameter as it's handled by asyncpg differently
        # asyncpg handles SSL automatically based on the connection
        pass

    return database_url


def is_production() -> bool:
    """Check if running in production environment."""
    return settings.ENVIRONMENT.lower() in ["production", "prod"]


def is_railway_deployment() -> bool:
    """Check if running on Railway.app."""
    return bool(os.getenv("RAILWAY_ENVIRONMENT"))
