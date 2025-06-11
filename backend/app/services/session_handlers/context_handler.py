"""
Handler for managing user context and session switching.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from .base_handler import BaseHandler
from app.models.data_import_session import DataImportSession
from app.models.client_account import Engagement, User, ClientAccount
from app.schemas.context import UserContext, ClientBase, EngagementBase, SessionBase

class ContextHandler(BaseHandler):
    """Handler for user context and session management."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the context handler."""
        super().__init__(db)
        self._current_session = None
        self._available_sessions = []
    
    async def get_user_context(self, user_id: UUID) -> UserContext:
        """
        Get the complete context for the current user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            UserContext containing all relevant context information
        """
        user = await self._get_user_with_relationships(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # If no default engagement, get the first available one
        engagement = user.default_engagement
        if not engagement and user.engagements:
            engagement = user.engagements[0]
            user.default_engagement = engagement
            await self.db.commit()
        
        # Get sessions for the engagement
        session = None
        available_sessions = []
        
        if engagement:
            # Get all sessions for the engagement
            sessions_query = (
                select(DataImportSession)
                .where(DataImportSession.engagement_id == engagement.id)
                .order_by(DataImportSession.created_at.desc())
            )
            sessions_result = await self.db.execute(sessions_query)
            available_sessions = sessions_result.scalars().all()
            
            # Set default session
            if engagement.default_session:
                session = engagement.default_session
            elif available_sessions:
                session = available_sessions[0]
        
        # Update instance state
        self._current_session = session
        self._available_sessions = available_sessions
        
        return UserContext(
            user=user,
            client=ClientBase.model_validate(engagement.client_account) if engagement else None,
            engagement=EngagementBase.model_validate(engagement) if engagement else None,
            session=SessionBase.model_validate(session) if session else None,
            available_sessions=[SessionBase.model_validate(s) for s in available_sessions]
        )
    
    async def switch_session(self, user_id: UUID, session_id: UUID) -> Dict[str, Any]:
        """
        Switch the current user's active session.
        
        Args:
            user_id: The ID of the user
            session_id: The ID of the session to switch to
            
        Returns:
            Updated context with the new session
        """
        # Verify the session exists and user has access
        query = (
            select(DataImportSession)
            .join(Engagement, DataImportSession.engagement_id == Engagement.id)
            .join(User, Engagement.users)
            .where(
                DataImportSession.id == session_id,
                User.id == user_id
            )
        )
        
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Update the current session
        self._current_session = session
        
        # Get the engagement to return in context
        engagement = await self.db.get(Engagement, session.engagement_id)
        
        return {
            "session": SessionBase.model_validate(session),
            "engagement": EngagementBase.model_validate(engagement) if engagement else None,
            "client": ClientBase.model_validate(engagement.client_account) if engagement and engagement.client_account else None
        }
