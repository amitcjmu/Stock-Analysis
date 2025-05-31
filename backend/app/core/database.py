"""
Database configuration and session management for PostgreSQL.
Supports both local development and Railway.app deployment.
"""

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.pool import NullPool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    class AsyncSession:
        pass
    class NullPool:
        pass
    def declarative_base():
        return object
    def create_async_engine(*args, **kwargs):
        return None
    def async_sessionmaker(*args, **kwargs):
        return None

import logging

from app.core.config import settings, get_database_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine
if SQLALCHEMY_AVAILABLE:
    engine = create_async_engine(
        get_database_url(),
        echo=settings.DEBUG,  # Log SQL queries in debug mode
        poolclass=NullPool if settings.ENVIRONMENT == "development" else None,
        pool_pre_ping=True,
        pool_recycle=300,
    )

    # Create async session factory
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
else:
    engine = None
    AsyncSessionLocal = None
    logger.warning("SQLAlchemy not available. Database functionality will be limited.")

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get database session.
    Use this in FastAPI route dependencies.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered with Base
        from app.models import (
            migration, asset, assessment, sixr_analysis,  # Legacy models
            client_account, cmdb_asset, tags  # New multi-tenant models
        )
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")


class DatabaseManager:
    """Database manager for handling connections and transactions."""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
    
    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.session_factory() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        return self.session_factory()


# Global database manager instance
db_manager = DatabaseManager() 