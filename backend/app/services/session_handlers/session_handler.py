"""
Handler for session CRUD operations.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func, desc, update
from sqlalchemy.orm import selectinload, joinedload

from .base_handler import BaseHandler
from app.models.data_import_session import DataImportSession, SessionType, SessionStatus
from app.models.client_account import Engagement, ClientAccount, User
from app.schemas.session import SessionCreate, SessionUpdate, Session

class SessionHandler(BaseHandler):
    """Handler for session CRUD operations."""
    
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
                DataImportSession.engagement_id == engagement_id,
                DataImportSession.status == SessionStatus.ACTIVE
            )
        ).order_by(DataImportSession.created_at.desc())
        
        result = await self.db.execute(query)
        session = result.scalars().first()
        
        if session or not auto_create:
            return session
            
        # Create a new active session
        return await self.create_session(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            auto_created=True,
            is_default=True
        )
        
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
        session = await self.get_session(UUID(session_id))
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        
        if summary:
            session.summary = summary
            
        if final_metrics:
            session.metadata = {**session.metadata, "final_metrics": final_metrics}
            
        await self.db.commit()
        await self.db.refresh(session)
        return session
        
    async def archive_session(self, session_id: str) -> DataImportSession:
        """
        Archive a completed session.
        
        Args:
            session_id: Session UUID
            
        Returns:
            Updated DataImportSession instance
        """
        session = await self.get_session(UUID(session_id))
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        if session.status != SessionStatus.COMPLETED:
            raise ValueError("Only completed sessions can be archived")
            
        session.status = SessionStatus.ARCHIVED
        session.archived_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_engagement_sessions(self, engagement_id: str) -> List[DataImportSession]:
        """
        Get all sessions for an engagement, ordered by creation date.
        
        Args:
            engagement_id: Engagement ID
            
        Returns:
            List of DataImportSession objects
        """
        query = (
            select(DataImportSession)
            .where(DataImportSession.engagement_id == engagement_id)
            .order_by(DataImportSession.created_at.desc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()
        
    async def get_default_session(self, engagement_id: str) -> Optional[DataImportSession]:
        """
        Get the default session for an engagement.
        
        Args:
            engagement_id: Engagement ID
            
        Returns:
            Default DataImportSession or None if not found
        """
        query = (
            select(DataImportSession)
            .where(
                and_(
                    DataImportSession.engagement_id == engagement_id,
                    DataImportSession.is_default == True  # noqa: E712
                )
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()
        
    async def set_default_session(self, session_id: str) -> DataImportSession:
        """
        Set a session as the default for its engagement.
        
        Args:
            session_id: Session ID to set as default
            
        Returns:
            Updated DataImportSession
            
        Raises:
            ValueError: If session not found
        """
        session = await self.get_session(UUID(session_id))
        if not session:
            raise ValueError(f"Session not found: {session_id}")
            
        # Unset any other default sessions for this engagement
        await self._unset_other_default_sessions(str(session.engagement_id), session_id)
        
        # Set this session as default
        session.is_default = True
        await self.db.commit()
        await self.db.refresh(session)
        return session
        
    async def _unset_other_default_sessions(
        self, 
        engagement_id: str, 
        exclude_session_id: Optional[str] = None
    ) -> None:
        """
        Unset any default sessions for an engagement.
        
        Args:
            engagement_id: Engagement ID
            exclude_session_id: Optional session ID to exclude from being unset
        """
        stmt = (
            update(DataImportSession)
            .where(
                and_(
                    DataImportSession.engagement_id == engagement_id,
                    DataImportSession.is_default == True,  # noqa: E712
                    DataImportSession.id != exclude_session_id
                )
            )
            .values(is_default=False)
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def merge_sessions(
        self,
        source_session_id: str,
        target_session_id: str,
        merge_metadata: Optional[Dict[str, Any]] = None
    ) -> DataImportSession:
        """
        Merge data from one session into another.
        
        Args:
            source_session_id: ID of the session to merge from
            target_session_id: ID of the session to merge into
            merge_metadata: Additional metadata about the merge
            
        Returns:
            The target session with merged data
            
        Raises:
            ValueError: If either session is not found
        """
        source = await self.get_session(UUID(source_session_id))
        target = await self.get_session(UUID(target_session_id))
        
        if not source or not target:
            raise ValueError("Both source and target sessions must exist")
            
        if source.engagement_id != target.engagement_id:
            raise ValueError("Cannot merge sessions from different engagements")
            
        # Update target session metadata
        if not target.metadata:
            target.metadata = {}
            
        target.metadata["merged_from"] = source.id
        
        if merge_metadata:
            target.metadata["merge_metadata"] = merge_metadata
            
        # Mark source as merged
        source.status = SessionStatus.MERGED
        source.metadata = source.metadata or {}
        source.metadata["merged_into"] = target.id
        
        await self.db.commit()
        await self.db.refresh(target)
        return target
        
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
        )
        
        if status:
            status_enum = SessionStatus[status.upper()]
            query = query.where(DataImportSession.status == status_enum)
            
        query = query.order_by(DataImportSession.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        result = await self.db.execute(query)
        return result.scalars().all()
        
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
            The created session
        """
        # Get the engagement to validate it exists and get the client
        engagement = await self.db.get(Engagement, engagement_id)
        if not engagement:
            raise ValueError(f"Engagement not found: {engagement_id}")
        
        # Generate a name if not provided
        if not session_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            session_name = f"session-{timestamp}"
        
        # Create the session
        session = DataImportSession(
            name=session_name,
            display_name=session_display_name or session_name,
            description=description,
            engagement_id=engagement_id,
            client_account_id=client_account_id,
            status=SessionStatus.ACTIVE,
            session_type=session_type,
            auto_created=auto_created,
            metadata=metadata or {},
            created_by=created_by,
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # If this is the default session, update the engagement
        if is_default:
            engagement.default_session_id = session.id
            await self.db.commit()
        
        return session
    
    async def update_session(
        self,
        session_id: UUID,
        updates: Dict[str, Any],
        updated_by: Optional[UUID] = None
    ) -> Optional[DataImportSession]:
        """
        Update an existing session.
        
        Args:
            session_id: The ID of the session to update
            updates: Dictionary of fields to update
            updated_by: ID of the user making the update
            
        Returns:
            The updated session, or None if not found
        """
        # Get the session
        session = await self.db.get(DataImportSession, session_id)
        if not session:
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(session, field) and field not in ["id", "created_at"]:
                setattr(session, field, value)
        
        # Update timestamps
        session.updated_at = datetime.utcnow()
        if updated_by:
            session.updated_by = updated_by
        
        await self.db.commit()
        await self.db.refresh(session)
        return session
    
    async def get_session(self, session_id: UUID) -> Optional[DataImportSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: The ID of the session to retrieve
            
        Returns:
            The session, or None if not found
        """
        query = (
            select(DataImportSession)
            .options(
                selectinload(DataImportSession.engagement)
                .selectinload(Engagement.client_account)
            )
            .where(DataImportSession.id == session_id)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_sessions(
        self,
        engagement_id: UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 100
    ) -> List[DataImportSession]:
        """
        List sessions for an engagement.
        
        Args:
            engagement_id: The ID of the engagement
            status: Optional status filter
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions
        """
        query = (
            select(DataImportSession)
            .where(DataImportSession.engagement_id == engagement_id)
            .order_by(desc(DataImportSession.created_at))
            .limit(limit)
        )
        
        if status:
            query = query.where(DataImportSession.status == status)
        
        result = await self.db.execute(query)
        return result.scalars().all()
