"""
Session Management Service for automatic session creation and lifecycle management.
Handles auto-naming, status management, and session reference for data imports.
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, desc
from datetime import datetime, timezone
import uuid
import logging

from app.models.data_import_session import DataImportSession
from app.models.client_account import Engagement, ClientAccount
from app.core.context import get_current_context, RequestContext
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class SessionManagementService:
    """
    Service for managing data import sessions with automatic creation and lifecycle management.
    
    Features:
    - Auto-naming with format: client-engagement-timestamp
    - Session status management (active/completed/archived)
    - Context-aware session creation
    - Session reference tracking for imports
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize session management service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_session(
        self,
        client_account_id: str,
        engagement_id: str,
        session_name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataImportSession:
        """
        Create a new data import session with auto-naming.
        
        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            session_name: Optional custom session name (auto-generated if not provided)
            description: Optional session description
            metadata: Optional session metadata
            
        Returns:
            Created DataImportSession instance
        """
        # Get client and engagement info for auto-naming
        client_query = select(ClientAccount).where(ClientAccount.id == client_account_id)
        client_result = await self.db.execute(client_query)
        client = client_result.scalar_one_or_none()
        
        engagement_query = select(Engagement).where(Engagement.id == engagement_id)
        engagement_result = await self.db.execute(engagement_query)
        engagement = engagement_result.scalar_one_or_none()
        
        if not client:
            raise ValueError(f"Client account not found: {client_account_id}")
        if not engagement:
            raise ValueError(f"Engagement not found: {engagement_id}")
        
        # Generate auto-name if not provided
        if not session_name:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            client_name = client.name.lower().replace(" ", "-").replace(".", "")
            engagement_name = engagement.name.lower().replace(" ", "-").replace(".", "")
            session_name = f"{client_name}-{engagement_name}-{timestamp}"
        
        # Create session
        session = DataImportSession(
            session_name=session_name,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            description=description or f"Data import session for {engagement.name}",
            status="active",
            created_by="eef6ea50-6550-4f14-be2c-081d4eb23038"  # Use client_account_id as fallback for created_by
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Created session {session.session_name} for client {client.name}, engagement {engagement.name}")
        return session
    
    async def get_or_create_active_session(
        self,
        client_account_id: str,
        engagement_id: str,
        auto_create: bool = True
    ) -> Optional[DataImportSession]:
        """
        Get the current active session for an engagement, or create one if needed.
        
        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            auto_create: Whether to auto-create a session if none exists
            
        Returns:
            Active DataImportSession or None if not found and auto_create=False
        """
        # Look for active session
        query = select(DataImportSession).where(
            and_(
                DataImportSession.client_account_id == client_account_id,
                DataImportSession.engagement_id == engagement_id,
                DataImportSession.status == "active"
            )
        ).order_by(desc(DataImportSession.created_at))
        
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            logger.debug(f"Found active session: {session.session_name}")
            return session
        
        if auto_create:
            logger.info(f"No active session found, creating new session for engagement {engagement_id}")
            return await self.create_session(client_account_id, engagement_id)
        
        return None
    
    async def complete_session(
        self,
        session_id: str,
        summary: Optional[str] = None,
        final_metrics: Optional[Dict[str, Any]] = None
    ) -> DataImportSession:
        """
        Mark a session as completed with optional summary and metrics.
        
        Args:
            session_id: Session UUID
            summary: Optional completion summary
            final_metrics: Optional final metrics for the session
            
        Returns:
            Updated DataImportSession instance
        """
        query = select(DataImportSession).where(DataImportSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Update session status
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)
        
        if summary:
            session.description = f"{session.description}\n\nCompletion Summary: {summary}"
        
        if final_metrics:
            session.metadata = {**(session.metadata or {}), "final_metrics": final_metrics}
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Completed session {session.session_name}")
        return session
    
    async def archive_session(self, session_id: str) -> DataImportSession:
        """
        Archive a completed session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Updated DataImportSession instance
        """
        query = select(DataImportSession).where(DataImportSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        if session.status != "completed":
            raise ValueError(f"Can only archive completed sessions. Current status: {session.status}")
        
        session.status = "archived"
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Archived session {session.session_name}")
        return session
    
    async def get_sessions_for_engagement(
        self,
        engagement_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DataImportSession]:
        """
        Get all sessions for an engagement, optionally filtered by status.
        
        Args:
            engagement_id: Engagement UUID
            status: Optional status filter (active/completed/archived)
            limit: Optional limit on number of sessions returned
            
        Returns:
            List of DataImportSession instances
        """
        query = select(DataImportSession).where(
            DataImportSession.engagement_id == engagement_id
        ).order_by(desc(DataImportSession.created_at))
        
        if status:
            query = query.where(DataImportSession.status == status)
        
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        logger.debug(f"Found {len(sessions)} sessions for engagement {engagement_id}")
        return sessions
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dictionary with session statistics
        """
        query = select(DataImportSession).where(DataImportSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Calculate session duration
        duration = None
        if session.completed_at:
            duration = (session.completed_at - session.created_at).total_seconds()
        elif session.status == "active":
            duration = (datetime.now(timezone.utc) - session.created_at).total_seconds()
        
        # Get data import counts (would need to query related tables)
        # For now, return basic session info
        stats = {
            "session_id": session.id,
            "session_name": session.session_name,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "duration_seconds": duration,
            "metadata": session.metadata or {},
            "description": session.description
        }
        
        return stats
    
    async def update_session_metadata(
        self,
        session_id: str,
        metadata_updates: Dict[str, Any]
    ) -> DataImportSession:
        """
        Update session metadata with new information.
        
        Args:
            session_id: Session UUID
            metadata_updates: Dictionary of metadata updates to merge
            
        Returns:
            Updated DataImportSession instance
        """
        query = select(DataImportSession).where(DataImportSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        # Merge metadata
        current_metadata = session.metadata or {}
        updated_metadata = {**current_metadata, **metadata_updates}
        session.metadata = updated_metadata
        
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.debug(f"Updated metadata for session {session.session_name}")
        return session


async def get_session_management_service() -> SessionManagementService:
    """
    Factory function to create session management service with database session.
    
    Returns:
        SessionManagementService instance
    """
    async with AsyncSessionLocal() as db:
        return SessionManagementService(db)


def create_session_management_service(db: AsyncSession) -> SessionManagementService:
    """
    Create session management service with provided database session.
    
    Args:
        db: Database session
        
    Returns:
        SessionManagementService instance
    """
    return SessionManagementService(db) 