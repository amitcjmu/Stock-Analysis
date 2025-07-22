"""
Session Handler for Discovery Flow
Handles database session management for crew executions with isolation
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class SessionHandler:
    """Handles database session management for crew executions"""
    
    def __init__(self):
        self.crew_sessions = {}
        self.session_pools = {}
        self.session_state = {
            "active_sessions": {},
            "session_history": [],
            "isolation_level": "crew_based",
            "cleanup_enabled": True,
            "max_sessions_per_crew": 3
        }
        self.db_session_enabled = False
        self.AsyncSessionLocal = None
    
    def setup_database_sessions(self):
        """Setup database session management for crew executions"""
        # Import AsyncSessionLocal for proper async database operations
        try:
            from app.core.database import AsyncSessionLocal
            self.AsyncSessionLocal = AsyncSessionLocal
            self.db_session_enabled = True
            logger.info("Database session management enabled with AsyncSessionLocal")
        except ImportError:
            logger.warning("AsyncSessionLocal not available, using fallback session management")
            self.AsyncSessionLocal = None
            self.db_session_enabled = False
        
        logger.info(f"Database session management initialized: {self.db_session_enabled}")
    
    async def get_crew_session(self, crew_name: str):
        """Get isolated database session for a specific crew"""
        if not self.db_session_enabled:
            return None
        
        try:
            # Create new session for crew if not exists
            if crew_name not in self.crew_sessions:
                session = self.AsyncSessionLocal()
                self.crew_sessions[crew_name] = session
                
                # Track session
                self.session_state["active_sessions"][crew_name] = {
                    "db_session_id": id(session),
                    "created_at": datetime.utcnow().isoformat(),
                    "transactions": 0,
                    "last_activity": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Created new database session for crew: {crew_name}")
            
            # Update last activity
            self.session_state["active_sessions"][crew_name]["last_activity"] = datetime.utcnow().isoformat()
            
            return self.crew_sessions[crew_name]
            
        except Exception as e:
            logger.error(f"Error creating database session for crew {crew_name}: {e}")
            return None
    
    async def close_crew_session(self, crew_name: str):
        """Close database session for a specific crew"""
        if not self.db_session_enabled or crew_name not in self.crew_sessions:
            return
        
        try:
            session = self.crew_sessions[crew_name]
            await session.close()
            
            # Move to history
            if crew_name in self.session_state["active_sessions"]:
                session_info = self.session_state["active_sessions"][crew_name]
                session_info["closed_at"] = datetime.utcnow().isoformat()
                self.session_state["session_history"].append(session_info)
                del self.session_state["active_sessions"][crew_name]
            
            del self.crew_sessions[crew_name]
            logger.info(f"Closed database session for crew: {crew_name}")
            
        except Exception as e:
            logger.error(f"Error closing database session for crew {crew_name}: {e}")
    
    async def cleanup_all_sessions(self):
        """Clean up all database sessions"""
        if not self.db_session_enabled:
            return
        
        cleanup_count = 0
        for crew_name in list(self.crew_sessions.keys()):
            await self.close_crew_session(crew_name)
            cleanup_count += 1
        
        logger.info(f"Cleaned up {cleanup_count} database sessions")
    
    async def execute_with_session(self, crew_name: str, operation):
        """Execute database operation with crew-specific session"""
        if not self.db_session_enabled:
            # Fallback for operations without database
            return await operation(None)
        
        session = await self.get_crew_session(crew_name)
        
        try:
            # Execute operation with session
            result = await operation(session)
            
            # Track transaction
            if crew_name in self.session_state["active_sessions"]:
                self.session_state["active_sessions"][crew_name]["transactions"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Database operation failed for crew {crew_name}: {e}")
            # Rollback session if available
            if session:
                try:
                    await session.rollback()
                except Exception:
                    pass
            raise
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current database session status"""
        return {
            "session_management_enabled": self.db_session_enabled,
            "active_sessions": len(self.session_state.get("active_sessions", {})),
            "session_history_count": len(self.session_state.get("session_history", [])),
            "crews_with_sessions": list(self.crew_sessions.keys()),
            "session_details": self.session_state
        } 