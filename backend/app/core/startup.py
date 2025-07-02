"""
Application Startup Module
Handles initialization tasks when the application starts.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.database import AsyncSessionLocal
from app.core.database_initialization import initialize_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs initialization on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("🚀 Starting application...")
    
    try:
        # Initialize database (ensure platform admin, user profiles, etc.)
        logger.info("🔧 Running database initialization...")
        async with AsyncSessionLocal() as db:
            await initialize_database(db)
        logger.info("✅ Database initialization completed")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Don't prevent app startup, just log the error
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down application...")


def configure_startup(app: FastAPI):
    """
    Configure application startup handlers.
    
    Usage in main.py:
        from app.core.startup import configure_startup
        
        app = FastAPI()
        configure_startup(app)
    """
    # For FastAPI >= 0.93.0, use lifespan
    app.router.lifespan_context = lifespan
    
    logger.info("✅ Startup configuration completed")