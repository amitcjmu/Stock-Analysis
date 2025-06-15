"""
Session Management Service for automatic session creation and lifecycle management.
Handles auto-naming, status management, and session reference for data imports.
Uses a modular handler pattern for better organization and maintainability.
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.data_import_session import DataImportSession, SessionType
from .session_handlers import ContextHandler, SessionHandler

logger = logging.getLogger(__name__)


class SessionManagementService:
    """
    Service for managing data import sessions with automatic creation and lifecycle management.
    
    Uses a modular handler pattern to keep the service focused and maintainable.
    Each major feature area is delegated to a dedicated handler class.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize session management service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._context_handler = ContextHandler(db)
        self._session_handler = SessionHandler(db)
    
    # Context Management Methods
    
    async def get_user_context(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get complete user context including default engagement and session.
        
        Delegates to the context handler for implementation.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dict containing user, client, engagement, and session info
        """
        return await self._context_handler.get_user_context(user_id)
    
    async def switch_session(self, user_id: UUID, session_id: UUID) -> Dict[str, Any]:
        """
        Switch user's current session.
        
        Delegates to the context handler for implementation.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session to switch to
            
        Returns:
            Updated user context with new session
        """
        return await self._context_handler.switch_session(user_id, session_id)
    
    # Session CRUD Methods
    
    async def create_session(
        self,
        client_account_id: str,
        engagement_id: str,
        session_name: Optional[str] = None,
        session_display_name: Optional[str] = None,
        description: Optional[str] = None,
        is_default: bool = False,
        session_type: str = SessionType.DATA_IMPORT,
        auto_created: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[UUID] = None
    ) -> DataImportSession:
        """
        Create a new session with auto-naming and default session handling.
        
        Delegates to the session handler for implementation.
        
        Args:
            client_account_id: The ID of the client account
            engagement_id: The ID of the engagement
            session_name: Optional custom session name
            session_display_name: Optional display name for the session
            description: Optional description of the session
            is_default: Whether this should be the default session
            session_type: Type of the session (default: DATA_IMPORT)
            auto_created: Whether the session was auto-created
            metadata: Optional metadata for the session
            created_by: ID of the user creating the session
            
        Returns:
            The newly created session
        """
        return await self._session_handler.create_session(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            session_name=session_name,
            session_display_name=session_display_name,
            description=description,
            is_default=is_default,
            session_type=session_type,
            auto_created=auto_created,
            metadata=metadata,
            created_by=created_by
        )
    
    async def update_session(
        self,
        session_id: str,
        session_data: Dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> DataImportSession:
        """
        Update an existing session.
        
        Delegates to the session handler for implementation.
        
        Args:
            session_id: The ID of the session to update
            session_data: Dictionary of fields to update
            updated_by: Optional ID of the user making the update
            
        Returns:
            The updated session
        """
        return await self._session_handler.update_session(
            session_id=session_id,
            session_data=session_data,
            updated_by=updated_by
        )
    
    async def get_session(self, session_id: str) -> Optional[DataImportSession]:
        """
        Get a session by ID.
        
        Delegates to the session handler for implementation.
        
        Args:
            session_id: The ID of the session to retrieve
            
        Returns:
            The session if found, None otherwise
        """
        return await self._session_handler.get_session(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session by ID.
        
        Delegates to the session handler for implementation.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if the session was deleted, False otherwise
        """
        return await self._session_handler.delete_session(session_id)
    
    # Session Management Methods
    
    async def get_or_create_active_session(
        self,
        client_account_id: str,
        engagement_id: str,
        auto_create: bool = True
    ) -> Optional[DataImportSession]:
        """
        Get the current active session for an engagement, or create one if needed.
        
        Delegates to the session handler for implementation.
        
        Args:
            client_account_id: Client account UUID
            engagement_id: Engagement UUID
            auto_create: Whether to auto-create a session if none exists
            
        Returns:
            Active DataImportSession or None if not found and auto_create=False
        """
        return await self._session_handler.get_or_create_active_session(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            auto_create=auto_create
        )
    
    async def complete_session(
        self,
        session_id: str,
        summary: Optional[str] = None,
        final_metrics: Optional[Dict[str, Any]] = None
    ) -> DataImportSession:
        """
        Mark a session as completed with optional summary and metrics.
        
        Delegates to the session handler for implementation.
        
        Args:
            session_id: Session UUID
            summary: Optional completion summary
            final_metrics: Optional final metrics for the session
            
        Returns:
            Updated DataImportSession instance
        """
        return await self._session_handler.complete_session(
            session_id=session_id,
            summary=summary,
            final_metrics=final_metrics
        )
        
    async def archive_session(self, session_id: str) -> DataImportSession:
        """
        Archive a completed session.
        
        Delegates to the session handler for implementation.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Updated DataImportSession instance
        """
        return await self._session_handler.archive_session(session_id)
    
    async def get_engagement_sessions(self, engagement_id: str) -> List[DataImportSession]:
        """
        Get all sessions for an engagement, ordered by creation date.
        
        Delegates to the session handler for implementation.
        
        Args:
            engagement_id: Engagement ID
            
        Returns:
            List of DataImportSession objects
        """
        return await self._session_handler.get_engagement_sessions(engagement_id)
        
    async def get_default_session(self, engagement_id: str) -> Optional[DataImportSession]:
        """
        Get the default session for an engagement.
        
        Delegates to the session handler for implementation.
        
        Args:
            engagement_id: Engagement ID
            
        Returns:
            Default DataImportSession or None if not found
        """
        return await self._session_handler.get_default_session(engagement_id)
        
    async def set_default_session(self, session_id: str) -> DataImportSession:
        """
        Set a session as the default for its engagement.
            
        Delegates to the session handler for implementation.
            
        Args:
            session_id: Session ID to set as default
            
        Returns:
            The updated session with is_default=True
        """
        return await self._session_handler.set_default_session(session_id)
    async def merge_sessions(
        self, 
        source_session_id: str, 
        target_session_id: str,
        merge_metadata: Optional[Dict[str, Any]] = None
    ) -> DataImportSession:
        """
        Merge data from one session into another.
        
        Delegates to the session handler for implementation.
        
        Args:
            source_session_id: ID of the session to merge from
            target_session_id: ID of the session to merge into
            merge_metadata: Additional metadata about the merge
            
        Returns:
            The target session with merged data
            
        Raises:
            ValueError: If either session is not found or sessions are from different engagements
        """
        return await self._session_handler.merge_sessions(
            source_session_id=source_session_id,
            target_session_id=target_session_id,
            merge_metadata=merge_metadata
        )
    
    async def get_sessions_for_engagement(
        self,
        engagement_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[DataImportSession]:
        """
        Get all sessions for an engagement, optionally filtered by status.
        
        Delegates to the session handler for implementation.
        
        Args:
            engagement_id: Engagement UUID
            status: Optional status filter (active/completed/archived)
            limit: Optional limit on number of sessions returned
            
        Returns:
            List of DataImportSession instances
        """
        return await self._session_handler.get_sessions_for_engagement(
            engagement_id=engagement_id,
            status=status,
            limit=limit
        )
    
    async def get_session_context(
        self,
        user_id: UUID,
        client_account_id: Optional[UUID] = None,
        engagement_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get the appropriate session context based on user permissions and provided IDs.
        
        Delegates to the context handler for implementation.
        
        Args:
            user_id: User ID
            client_account_id: Optional client ID to scope the context
            engagement_id: Optional engagement ID to scope the context
            session_id: Optional session ID to get specific session
            
        Returns:
            Dictionary with context information including available clients, engagements, and sessions
        """
        return await self._context_handler.get_session_context(
            user_id=user_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            session_id=session_id
        )
    
    async def create_data_import_session(
        self,
        engagement_id: str,
        user_id: str,
        session_name: Optional[str] = None,
        description: Optional[str] = None,
        is_default: bool = False,
        metadata: Optional[Dict] = None
    ) -> DataImportSession:
        """
        Create a new data import session.
        
        Delegates to the session handler for implementation.
        
        Args:
            engagement_id: Engagement ID
            user_id: User ID creating the session
            session_name: Optional custom session name
            description: Optional session description
            is_default: Whether this should be the default session
            metadata: Optional session metadata
            
        Returns:
            Created DataImportSession
        """
        return await self._session_handler.create_data_import_session(
            engagement_id=engagement_id,
            user_id=user_id,
            session_name=session_name,
            description=description,
            is_default=is_default,
            metadata=metadata
        )
    
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
        
        Delegates to the session handler for implementation.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Dictionary with session statistics
        """
        return await self._session_handler.get_session_statistics(session_id)
    
    async def update_session_metadata(
        self,
        session_id: str,
        metadata_updates: Dict[str, Any]
    ) -> DataImportSession:
        """
        Update session metadata with new information.
        
        Delegates to the session handler for implementation.
        
        Args:
            session_id: Session UUID
            metadata_updates: Dictionary of metadata updates to merge
            
        Returns:
            Updated DataImportSession instance
        """
        return await self._session_handler.update_session_metadata(
            session_id=session_id,
            metadata_updates=metadata_updates
        )


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