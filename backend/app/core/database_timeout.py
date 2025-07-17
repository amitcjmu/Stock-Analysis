"""
Extended database session management for long-running operations.
Provides configurable timeouts for different types of operations.
"""

import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import logging

from app.core.database import AsyncSessionLocal, connection_health

logger = logging.getLogger(__name__)

# Timeout configurations for different operation types
TIMEOUT_CONFIG = {
    "default": 60,          # Default 60 seconds
    "asset_list": 120,      # 2 minutes for asset listing
    "asset_analysis": 300,  # 5 minutes for AI analysis
    "bulk_operations": 180, # 3 minutes for bulk operations
    "report_generation": 240 # 4 minutes for reports
}

async def get_db_with_timeout(timeout_seconds: Optional[int] = None, operation_type: str = "default") -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with configurable timeout.
    
    Args:
        timeout_seconds: Override timeout in seconds
        operation_type: Type of operation to determine default timeout
        
    Yields:
        AsyncSession: Database session
    """
    # Determine timeout
    if timeout_seconds is None:
        timeout_seconds = TIMEOUT_CONFIG.get(operation_type, TIMEOUT_CONFIG["default"])
    
    start_time = datetime.utcnow()
    session = None
    
    logger.info(f"Creating DB session for {operation_type} with {timeout_seconds}s timeout")
    
    try:
        # Create session with extended timeout
        async with asyncio.timeout(timeout_seconds):
            session = AsyncSessionLocal()
            
            # Health check with shorter timeout
            async with asyncio.timeout(5):  # 5 second health check
                await session.execute(text("SELECT 1"))
            
            response_time = (datetime.utcnow() - start_time).total_seconds()
            connection_health.record_connection_attempt(True, response_time)
            
            yield session
            
            # Commit with timeout
            try:
                async with asyncio.timeout(10):  # 10 seconds for commit
                    await session.commit()
            except asyncio.TimeoutError:
                logger.warning(f"Commit timeout for {operation_type}")
                await session.rollback()
            except Exception as commit_error:
                logger.warning(f"Could not commit transaction: {commit_error}")
                await session.rollback()
    
    except asyncio.TimeoutError:
        logger.error(f"Database session timeout for {operation_type} after {timeout_seconds}s")
        connection_health.record_connection_attempt(False, timeout_seconds)
        if session:
            await session.rollback()
            await session.close()
        raise
    except Exception as e:
        logger.error(f"Database session error for {operation_type}: {e}")
        response_time = (datetime.utcnow() - start_time).total_seconds()
        connection_health.record_connection_attempt(False, response_time)
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()

# Dependency functions for specific operation types
async def get_db_for_asset_list() -> AsyncGenerator[AsyncSession, None]:
    """Get DB session optimized for asset listing operations."""
    async for session in get_db_with_timeout(operation_type="asset_list"):
        yield session

async def get_db_for_asset_analysis() -> AsyncGenerator[AsyncSession, None]:
    """Get DB session optimized for AI asset analysis operations."""
    async for session in get_db_with_timeout(operation_type="asset_analysis"):
        yield session

async def get_db_for_bulk_operations() -> AsyncGenerator[AsyncSession, None]:
    """Get DB session optimized for bulk operations."""
    async for session in get_db_with_timeout(operation_type="bulk_operations"):
        yield session