"""
Base handler class for service handlers.
"""

from typing import Any, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

class BaseHandler:
    """Base class for service handlers."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the handler with a database session."""
        self.db = db
        
    async def _get_user_with_relationships(self, user_id: UUID):
        """
        Get a user with their relationships loaded.
        
        Args:
            user_id: The ID of the user to fetch
            
        Returns:
            User object with relationships loaded
        """
        from sqlalchemy.future import select
        from sqlalchemy.orm import selectinload
        from app.models import User, Engagement
        
        query = (
            select(User)
            .options(
                selectinload(User.default_engagement)
                .selectinload(Engagement.client_account),
                selectinload(User.default_engagement)
                .selectinload(Engagement.default_session),
                selectinload(User.engagements)
            )
            .where(User.id == user_id)
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
