"""
Database session management utilities.
Provides centralized session handling with context awareness and timeout management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncContextManager, Dict, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, connection_health

logger = logging.getLogger(__name__)

# Custom exceptions for better error handling
class DatabaseError(Exception):
    """Base exception for database operations."""
    pass

class SessionTimeoutError(DatabaseError):
    """Exception raised when session operations timeout."""
    pass

class ConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    pass

@dataclass
class SessionConfig:
    """Configuration for database sessions."""
    timeout_seconds: int = 30
    enable_health_check: bool = True
    auto_commit: bool = True
    client_account_id: Optional[str] = None
    engagement_id: Optional[str] = None
    user_id: Optional[str] = None
    session_metadata: Optional[Dict[str, Any]] = None

class DatabaseSessionManager:
    """
    Centralized database session manager with enhanced error handling and monitoring.
    """
    
    def __init__(self, config: Optional[SessionConfig] = None):
        self.config = config or SessionConfig()
        self.active_sessions: Dict[str, AsyncSession] = {}
        self.session_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "failed_sessions": 0,
            "avg_session_duration": 0.0
        }
    
    @asynccontextmanager
    async def get_session(self, session_id: Optional[str] = None) -> AsyncContextManager[AsyncSession]:
        """
        Get a database session with comprehensive error handling and monitoring.
        
        Args:
            session_id: Optional session identifier for tracking
            
        Yields:
            AsyncSession: Database session
            
        Raises:
            SessionTimeoutError: If session creation times out
            ConnectionError: If database connection fails
        """
        session = None
        start_time = datetime.utcnow()
        
        try:
            # Create session with timeout
            async with asyncio.timeout(self.config.timeout_seconds):
                session = AsyncSessionLocal()
                
                # Store session for tracking
                if session_id:
                    self.active_sessions[session_id] = session
                
                self.session_stats["total_sessions"] += 1
                self.session_stats["active_sessions"] += 1
                
                # Health check if enabled
                if self.config.enable_health_check:
                    await self._health_check(session)
                
                logger.debug(f"Database session created (ID: {session_id})")
                yield session
                
                # Auto-commit if enabled
                if self.config.auto_commit:
                    await session.commit()
                    
        except asyncio.TimeoutError:
            error_msg = f"Database session timeout after {self.config.timeout_seconds}s"
            logger.error(error_msg)
            self.session_stats["failed_sessions"] += 1
            
            if session:
                await self._cleanup_session(session)
                
            raise SessionTimeoutError(error_msg)
            
        except SQLAlchemyError as e:
            error_msg = f"Database session error: {str(e)}"
            logger.error(error_msg)
            self.session_stats["failed_sessions"] += 1
            
            if session:
                await session.rollback()
                await self._cleanup_session(session)
                
            raise ConnectionError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected session error: {str(e)}"
            logger.error(error_msg)
            self.session_stats["failed_sessions"] += 1
            
            if session:
                await session.rollback()
                await self._cleanup_session(session)
                
            raise DatabaseError(error_msg)
            
        finally:
            # Cleanup and statistics
            if session:
                await self._cleanup_session(session)
                
            if session_id and session_id in self.active_sessions:
                del self.active_sessions[session_id]
                
            self.session_stats["active_sessions"] -= 1
            
            # Update average session duration
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._update_avg_duration(duration)
    
    async def _health_check(self, session: AsyncSession) -> None:
        """Perform health check on database session."""
        try:
            await session.execute(text("SELECT 1"))
            logger.debug("Database session health check passed")
        except Exception as e:
            logger.error(f"Database session health check failed: {e}")
            raise ConnectionError(f"Health check failed: {str(e)}")
    
    async def _cleanup_session(self, session: AsyncSession) -> None:
        """Clean up database session."""
        try:
            await session.close()
            logger.debug("Database session cleaned up successfully")
        except Exception as e:
            logger.warning(f"Error cleaning up session: {e}")
    
    def _update_avg_duration(self, duration: float) -> None:
        """Update average session duration statistics."""
        total_sessions = self.session_stats["total_sessions"]
        if total_sessions > 0:
            current_avg = self.session_stats["avg_session_duration"]
            self.session_stats["avg_session_duration"] = (
                (current_avg * (total_sessions - 1) + duration) / total_sessions
            )
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        return {
            **self.session_stats,
            "connection_health": connection_health.get_health_status()
        }
    
    async def close_all_sessions(self) -> None:
        """Close all active sessions."""
        for session_id, session in self.active_sessions.items():
            logger.info(f"Closing active session: {session_id}")
            await self._cleanup_session(session)
        
        self.active_sessions.clear()
        self.session_stats["active_sessions"] = 0

# Global session manager instance
session_manager = DatabaseSessionManager()

# Convenience functions
async def get_session_with_context(
    client_account_id: Optional[str] = None,
    engagement_id: Optional[str] = None,
    user_id: Optional[str] = None,
    timeout_seconds: int = 30
) -> AsyncContextManager[AsyncSession]:
    """
    Get database session with multi-tenant context.
    
    Args:
        client_account_id: Client account ID for multi-tenant filtering
        engagement_id: Engagement ID for scoping
        user_id: User ID for audit logging
        timeout_seconds: Session timeout in seconds
        
    Returns:
        AsyncContextManager[AsyncSession]: Database session with context
    """
    config = SessionConfig(
        timeout_seconds=timeout_seconds,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        session_metadata={
            "created_at": datetime.utcnow().isoformat(),
            "context": {
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "user_id": user_id
            }
        }
    )
    
    manager = DatabaseSessionManager(config)
    return manager.get_session()

async def get_session_with_timeout(timeout_seconds: int = 10) -> AsyncContextManager[AsyncSession]:
    """
    Get database session with custom timeout for performance-critical operations.
    
    Args:
        timeout_seconds: Custom timeout in seconds
        
    Returns:
        AsyncContextManager[AsyncSession]: Database session with timeout
    """
    config = SessionConfig(timeout_seconds=timeout_seconds, enable_health_check=False)
    manager = DatabaseSessionManager(config)
    return manager.get_session()