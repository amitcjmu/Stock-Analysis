"""
Logging Configuration for AI Modernize Migration Platform
Suppresses verbose LLM library logs while keeping application logs visible.
"""

import logging
import os


def configure_logging():
    """Configure logging levels to suppress verbose LLM library logs."""
    
    # Set up basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        force=True  # Override any existing logging configuration
    )
    
    # Suppress verbose LLM-related logs - set to ERROR to only show critical issues
    noisy_loggers = [
        # HTTP clients
        "httpx",
        "urllib3", 
        "requests",
        "httpcore",
        "h11",
        
        # LLM libraries
        "LiteLLM",
        "litellm", 
        "openai",
        "anthropic",
        
        # CrewAI
        "crewai",
        "CrewAI",
        
        # AI providers
        "deepinfra",
        
        # Database (unless errors)
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "sqlalchemy.dialects",
        "asyncpg",
        
        # Other noisy libraries
        "uvicorn.access",  # Reduce access logs
        "multipart",
        "charset_normalizer"
    ]
    
    # Set all noisy loggers to ERROR level
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Keep important application logs visible at INFO level
    important_loggers = [
        "app",              # Our application logs
        "uvicorn",          # Server logs (but not access)
        "fastapi",          # FastAPI logs
        "main",             # Main application logs
    ]
    
    for logger_name in important_loggers:
        logging.getLogger(logger_name).setLevel(logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    print("✅ Logging configured - LLM library logs suppressed to ERROR level")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


# Configure logging when module is imported
configure_logging() 