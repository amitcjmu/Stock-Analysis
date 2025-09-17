"""
Session and context management for Authentication Cache Service

Handles user session caching, user context management, and related operations
for maintaining user state and preferences across application sessions.
"""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.core.security.cache_encryption import secure_setattr

from .base import CacheKeys, CacheTTL, UserContext, UserSession

logger = get_logger(__name__)


class SessionManagementMixin:
    """
    Mixin providing user session and context management functionality

    Handles:
    - User session caching and retrieval
    - User context management and updates
    - Session invalidation

    Requires:
    - self._get_from_cache()
    - self._set_to_cache()
    - self._delete_from_cache()
    """

    # User Session Management

    async def get_user_session(self, user_id: str) -> Optional[UserSession]:
        """Get user session data from cache"""
        key = CacheKeys.USER_SESSION.format(user_id=user_id)
        data = await self._get_from_cache(key, use_secure=True)

        if data:
            try:
                # Convert back to UserSession object
                if isinstance(data, dict):
                    # Handle datetime fields
                    if "created_at" in data and isinstance(data["created_at"], str):
                        data["created_at"] = datetime.fromisoformat(data["created_at"])
                    if "last_accessed" in data and isinstance(
                        data["last_accessed"], str
                    ):
                        data["last_accessed"] = datetime.fromisoformat(
                            data["last_accessed"]
                        )

                    return UserSession(**data)
                return data
            except Exception as e:
                logger.error(f"Error deserializing user session for {user_id}: {e}")
                # Invalidate corrupted cache entry
                await self._delete_from_cache(key)

        return None

    async def set_user_session(self, session: UserSession) -> bool:
        """Set user session data in cache"""
        key = CacheKeys.USER_SESSION.format(user_id=session.user_id)

        # Update last accessed time
        session.last_accessed = datetime.utcnow()

        # Convert to dict for serialization
        session_data = asdict(session)

        # Convert datetime objects to ISO strings for JSON serialization
        if session_data.get("created_at"):
            session_data["created_at"] = session_data["created_at"].isoformat()
        if session_data.get("last_accessed"):
            session_data["last_accessed"] = session_data["last_accessed"].isoformat()

        success = await self._set_to_cache(
            key, session_data, ttl=CacheTTL.USER_SESSION, use_secure=True
        )

        if success:
            logger.debug(f"Cached user session for {session.user_id}")

        return success

    async def invalidate_user_session(self, user_id: str) -> bool:
        """Invalidate user session cache"""
        key = CacheKeys.USER_SESSION.format(user_id=user_id)
        success = await self._delete_from_cache(key)

        if success:
            logger.info(f"Invalidated user session cache for {user_id}")

        return success

    # User Context Management

    async def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """Get user context data from cache"""
        key = CacheKeys.USER_CONTEXT.format(user_id=user_id)
        data = await self._get_from_cache(key, use_secure=True)

        if data:
            try:
                if isinstance(data, dict):
                    # Handle datetime fields
                    if "last_updated" in data and isinstance(data["last_updated"], str):
                        data["last_updated"] = datetime.fromisoformat(
                            data["last_updated"]
                        )

                    return UserContext(**data)
                return data
            except Exception as e:
                logger.error(f"Error deserializing user context for {user_id}: {e}")
                await self._delete_from_cache(key)

        return None

    async def set_user_context(self, context: UserContext) -> bool:
        """Set user context data in cache"""
        key = CacheKeys.USER_CONTEXT.format(user_id=context.user_id)

        # Update last updated time
        context.last_updated = datetime.utcnow()

        # Convert to dict for serialization
        context_data = context.to_dict()

        # Convert datetime objects to ISO strings
        if context_data.get("last_updated"):
            context_data["last_updated"] = context_data["last_updated"].isoformat()

        success = await self._set_to_cache(
            key, context_data, ttl=CacheTTL.USER_CONTEXT, use_secure=True
        )

        if success:
            logger.debug(f"Cached user context for {context.user_id}")

        return success

    async def update_user_context(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in user context"""
        # Get existing context
        context = await self.get_user_context(user_id)

        if context is None:
            # Create new context with updates
            context = UserContext(user_id=user_id, **updates)
        else:
            # Update existing context
            for field, value in updates.items():
                if hasattr(context, field):
                    secure_setattr(context, field, value)

        return await self.set_user_context(context)

    async def invalidate_user_context(self, user_id: str) -> bool:
        """Invalidate user context cache"""
        key = CacheKeys.USER_CONTEXT.format(user_id=user_id)
        success = await self._delete_from_cache(key)

        if success:
            logger.info(f"Invalidated user context cache for {user_id}")

        return success
