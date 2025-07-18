"""
Database configuration and session management for PostgreSQL with pgvector support.
Supports both local development and Railway.app deployment.
⚡ OPTIMIZED: Enhanced with connection pooling and timeout management.
🎯 UNIFIED: Single pgvector database for all operations including AI embeddings.
"""

try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.pool import NullPool, QueuePool
    from sqlalchemy import event, text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    class AsyncSession:
        pass
    class NullPool:
        pass
    class QueuePool:
        pass
    def declarative_base():
        return object
    def create_async_engine(*args, **kwargs):
        return None
    def async_sessionmaker(*args, **kwargs):
        return None
    def text(*args, **kwargs):
        return None

import logging
import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings, get_database_url

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ⚡ PERFORMANCE OPTIMIZATIONS: Connection pool configuration
OPTIMIZED_POOL_CONFIG = {
    # Connection pool settings for production performance
    "pool_size": 10,              # Base number of connections to maintain
    "max_overflow": 20,           # Additional connections when needed
    "pool_timeout": 10,           # Max seconds to wait for connection from pool
    "pool_recycle": 300,          # Recycle connections every 5 minutes
    "pool_pre_ping": True,        # Validate connections before use
    
    # Query timeout settings
    "connect_args": {
        "command_timeout": 10,    # Command timeout in seconds
        "server_settings": {
            "application_name": "migrate_ui_orchestrator",
            "statement_timeout": "10s",  # SQL statement timeout
            "idle_in_transaction_session_timeout": "30s"
        }
    }
}

# Create async engine with optimizations
if SQLALCHEMY_AVAILABLE:
    # Choose pool class based on environment
    if settings.ENVIRONMENT == "development":
        # Use NullPool for development to avoid connection issues
        pool_class = NullPool
        pool_config = {"poolclass": NullPool, "pool_pre_ping": True}
    else:
        # Use optimized connection pooling for production
        pool_class = QueuePool
        pool_config = {
            "poolclass": QueuePool,
            **OPTIMIZED_POOL_CONFIG
        }
        
        # Additional security configurations for production
        if settings.ENVIRONMENT == "production":
            # Enhanced security for production
            pool_config["connect_args"]["server_settings"].update({
                "log_statement": "none",  # Disable SQL statement logging for security
                "log_min_duration_statement": "1000",  # Only log slow queries
                "ssl_prefer_server_ciphers": "on",
                "ssl_ciphers": "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384",
            })
    
    logger.info(f"⚡ Creating unified pgvector database engine with {pool_class.__name__} pool")
    
    # Merge connect_args with pool_config if it exists
    if 'connect_args' in pool_config:
        pool_config['connect_args']['server_settings'] = pool_config['connect_args'].get('server_settings', {})
        pool_config['connect_args']['server_settings']['search_path'] = 'migration,public'
    else:
        pool_config['connect_args'] = {
            "server_settings": {
                "search_path": "migration,public"
            }
        }
    
    # Unified database engine with pgvector support
    engine = create_async_engine(
        get_database_url(),
        echo=settings.DB_ECHO_LOG,  # Use dedicated setting for SQL logging
        **pool_config
    )

    # ⚡ CONNECTION MONITORING: Add connection event listeners
    @event.listens_for(engine.sync_engine, "connect")
    def set_connection_pragma(dbapi_connection, connection_record):
        """Configure connection-level settings for performance and pgvector."""
        logger.debug("Unified pgvector database connection established")
    
    @event.listens_for(engine.sync_engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        """Log connection checkout for monitoring."""
        logger.debug("Database connection checked out from pool")
    
    @event.listens_for(engine.sync_engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        """Log connection checkin for monitoring."""
        logger.debug("Database connection returned to pool")

    # Create async session factory with optimizations
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
# Note: Schema is set at the session/engine level, not in metadata
Base = declarative_base()

# ⚡ CONNECTION HEALTH TRACKING
class ConnectionHealthTracker:
    """Track database connection health and performance metrics."""
    
    def __init__(self):
        self.connection_count = 0
        self.failed_connections = 0
        self.last_health_check = None
        self.avg_response_time = 0.0
        self.response_times = []
    
    def record_connection_attempt(self, success: bool, response_time: float):
        """Record connection attempt and performance."""
        self.connection_count += 1
        if not success:
            self.failed_connections += 1
        
        self.response_times.append(response_time)
        # Keep only last 100 measurements
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
        
        self.avg_response_time = sum(self.response_times) / len(self.response_times)
    
    def get_health_status(self) -> dict:
        """Get current connection health status."""
        success_rate = 1.0
        if self.connection_count > 0:
            success_rate = (self.connection_count - self.failed_connections) / self.connection_count
        
        return {
            "total_connections": self.connection_count,
            "failed_connections": self.failed_connections,
            "success_rate": success_rate,
            "avg_response_time_ms": self.avg_response_time * 1000,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "performance_status": "good" if success_rate > 0.95 and self.avg_response_time < 1.0 else "degraded"
        }

# Global connection health tracker
connection_health = ConnectionHealthTracker()

async def get_db() -> AsyncSession:
    """
    ⚡ OPTIMIZED: Dependency to get database session with timeout and health monitoring.
    🎯 UNIFIED: Single session for all operations including vector operations.
    Use this in FastAPI route dependencies.
    """
    start_time = datetime.utcnow()
    session = None
    
    try:
        # ⚡ TIMEOUT: Use database timeout configuration for different operation types
        from app.core.database_timeout import get_db_timeout
        timeout_seconds = get_db_timeout()  # Get timeout from configuration
        
        if timeout_seconds is not None:
            async with asyncio.timeout(timeout_seconds):
                session = AsyncSessionLocal()
                
                # ⚡ HEALTH CHECK: Quick ping to verify connection
                await session.execute(text("SELECT 1"))
        else:
            # No timeout for agentic activities
            session = AsyncSessionLocal()
            
            # ⚡ HEALTH CHECK: Quick ping to verify connection
            await session.execute(text("SELECT 1"))
        
        response_time = (datetime.utcnow() - start_time).total_seconds()
        connection_health.record_connection_attempt(True, response_time)
        
        yield session
        
        # Only commit if there's no active transaction error
        try:
            await session.commit()
        except Exception as commit_error:
            logger.warning(f"Could not commit transaction: {commit_error}")
            await session.rollback()
    
    except asyncio.TimeoutError:
        logger.error("Database session creation timeout")
        connection_health.record_connection_attempt(False, 10.0)
        if session:
            await session.rollback()
            await session.close()
        raise
    except Exception as e:
        logger.error(f"Database session error: {e}")
        response_time = (datetime.utcnow() - start_time).total_seconds()
        connection_health.record_connection_attempt(False, response_time)
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()

# Alias for backward compatibility - all operations use the same database now
get_vector_db = get_db



async def get_db_with_timeout(timeout_seconds: int = 5) -> AsyncSession:
    """
    ⚡ FAST DB: Get database session with custom timeout for performance-critical operations.
    """
    start_time = datetime.utcnow()
    
    try:
        async with asyncio.timeout(timeout_seconds):
            session = AsyncSessionLocal()
            await session.execute(text("SELECT 1"))  # Quick health check
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            connection_health.record_connection_attempt(True, response_time)
            
            return session
    except Exception as e:
        response_time = (datetime.utcnow() - start_time).total_seconds()
        connection_health.record_connection_attempt(False, response_time)
        logger.error(f"Fast DB session failed in {response_time:.2f}s: {e}")
        raise


async def init_db():
    """Initialize database tables. DEPRECATED for schema creation."""
    logger.warning(
        "'init_db' was called, but schema creation via 'create_all' is disabled. "
        "Database schema should be managed exclusively by Alembic migrations."
    )
    # The following code is commented out to prevent conflicts with Alembic.
    # async with engine.begin() as conn:
    #     from app import models
    #     await conn.run_sync(Base.metadata.create_all)
    #     logger.info("Database tables created successfully")
    pass


async def close_db():
    """Close database connections."""
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")


class DatabaseManager:
    """⚡ OPTIMIZED: Database manager with enhanced health monitoring and performance tracking."""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal
        self.health_tracker = connection_health
    
    async def health_check(self) -> bool:
        """⚡ OPTIMIZED: Check database connectivity with timeout."""
        start_time = datetime.utcnow()
        
        try:
            async with asyncio.timeout(5):  # 5 second timeout
                async with self.session_factory() as session:
                    # Test both regular and vector functionality
                    await session.execute(text("SELECT 1"))
                    # Test pgvector extension
                    await session.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
                    
                response_time = (datetime.utcnow() - start_time).total_seconds()
                self.health_tracker.record_connection_attempt(True, response_time)
                self.health_tracker.last_health_check = datetime.utcnow()
                
                logger.info(f"✅ Unified pgvector database health check passed in {response_time:.2f}s")
                return True
                
        except Exception as e:
            response_time = (datetime.utcnow() - start_time).total_seconds()
            self.health_tracker.record_connection_attempt(False, response_time)
            logger.error(f"❌ Database health check failed in {response_time:.2f}s: {e}")
            return False
    
    async def get_session(self) -> AsyncSession:
        """⚡ OPTIMIZED: Get a new database session with monitoring."""
        return await get_db_with_timeout(timeout_seconds=5)
    
    def get_performance_metrics(self) -> dict:
        """Get database performance metrics."""
        pool_status = {}
        if hasattr(self.engine.pool, 'size'):
            pool_status = {
                "pool_size": self.engine.pool.size(),
                "checked_in_connections": self.engine.pool.checkedin(),
                "checked_out_connections": self.engine.pool.checkedout(),
                "invalid_connections": self.engine.pool.invalidated(),
            }
        
        return {
            "connection_health": self.health_tracker.get_health_status(),
            "pool_status": pool_status,
            "engine_type": type(self.engine).__name__ if self.engine else "None",
            "database_type": "unified_pgvector"
        }


# Global database manager instance
db_manager = DatabaseManager() 