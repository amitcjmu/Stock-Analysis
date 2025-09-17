"""
Activity buffering and management for Authentication Cache Service

Handles user activity buffering for batched operations, activity retrieval,
and buffer maintenance for efficient activity tracking and storage.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.core.logging import get_logger

from .base import CacheKeys, CacheTTL

logger = get_logger(__name__)


class ActivityManagementMixin:
    """
    Mixin providing activity buffering and batching functionality

    Handles:
    - User activity buffering for batched storage
    - Activity buffer retrieval and clearing
    - Periodic buffer flushing

    Requires:
    - self._get_from_cache()
    - self._set_to_cache()
    - self._delete_from_cache()
    - self.activity_buffers (Dict[str, List[Dict[str, Any]]])
    - self.last_buffer_flush (datetime)
    """

    # Activity Buffering for Batched Operations

    async def buffer_user_activity(
        self, user_id: str, activity: Dict[str, Any]
    ) -> bool:
        """Buffer user activity for batched storage"""
        # Add timestamp if not present
        if "timestamp" not in activity:
            activity["timestamp"] = datetime.utcnow().isoformat()

        # Add to in-memory buffer first
        self.activity_buffers[user_id].append(activity)

        # Also try to add to Redis buffer
        key = CacheKeys.ACTIVITY_BUFFER.format(user_id=user_id)

        try:
            # Get existing buffer from cache
            existing_buffer = await self._get_from_cache(key, use_secure=False) or []
            existing_buffer.append(activity)

            # Keep buffer size manageable (max 100 activities)
            if len(existing_buffer) > 100:
                existing_buffer = existing_buffer[-100:]

            success = await self._set_to_cache(
                key, existing_buffer, ttl=CacheTTL.ACTIVITY_BUFFER, use_secure=False
            )

            logger.debug(f"Buffered activity for user {user_id}")
            return success

        except Exception as e:
            logger.error(f"Error buffering activity for user {user_id}: {e}")
            return False

    async def get_buffered_activities(
        self, user_id: str, clear_buffer: bool = True
    ) -> List[Dict[str, Any]]:
        """Get and optionally clear buffered activities for a user"""
        activities = []

        # Get from in-memory buffer
        if user_id in self.activity_buffers:
            activities.extend(self.activity_buffers[user_id])
            if clear_buffer:
                self.activity_buffers[user_id].clear()

        # Get from Redis buffer
        key = CacheKeys.ACTIVITY_BUFFER.format(user_id=user_id)
        cached_activities = await self._get_from_cache(key, use_secure=False)

        if cached_activities:
            activities.extend(cached_activities)
            if clear_buffer:
                await self._delete_from_cache(key)

        # Remove duplicates based on timestamp
        seen_timestamps = set()
        unique_activities = []

        for activity in activities:
            timestamp = activity.get("timestamp")
            if timestamp not in seen_timestamps:
                seen_timestamps.add(timestamp)
                unique_activities.append(activity)

        return unique_activities

    async def flush_activity_buffers(self, max_age_minutes: int = 5) -> int:
        """Flush old activity buffers and return count of flushed activities"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        total_flushed = 0

        # Flush in-memory buffers
        for user_id in list(self.activity_buffers.keys()):
            activities = self.activity_buffers[user_id]

            # Keep only recent activities
            recent_activities = []
            for activity in activities:
                try:
                    activity_time = datetime.fromisoformat(
                        activity.get("timestamp", "")
                    )
                    if activity_time > cutoff_time:
                        recent_activities.append(activity)
                    else:
                        total_flushed += 1
                except (ValueError, TypeError):
                    # Invalid timestamp, remove it
                    total_flushed += 1

            self.activity_buffers[user_id] = recent_activities

            # Clean up empty buffers
            if not recent_activities:
                del self.activity_buffers[user_id]

        self.last_buffer_flush = datetime.utcnow()

        if total_flushed > 0:
            logger.info(f"Flushed {total_flushed} old activity buffer entries")

        return total_flushed
