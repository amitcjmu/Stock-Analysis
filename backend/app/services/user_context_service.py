"""
User Context Service

This service handles user context operations including:
- Loading user relationships properly
- Getting user-specific flows
- Managing engagement context
- Providing fallback logic for missing context
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client_account import Engagement, User
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class UserContextService:
    """Service for managing user context and flow access"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_with_context(self, user_id: str) -> Optional[User]:
        """
        Get user with all relationships loaded properly.

        Args:
            user_id: The user ID

        Returns:
            User object with loaded relationships or None
        """
        try:
            # Convert user_id to UUID if needed
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                logger.warning(f"Invalid UUID format for user_id: {user_id}")
                return None

            # Query user with all necessary relationships
            stmt = (
                select(User)
                .options(
                    selectinload(User.default_client),
                    selectinload(User.default_engagement),
                )
                .where(User.id == user_uuid)
            )

            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                logger.info(
                    f"Loaded user {user.id} with engagement: {user.default_engagement_id}"
                )
            else:
                logger.warning(f"User {user_id} not found")

            return user

        except Exception as e:
            logger.error(f"Error loading user context: {e}", exc_info=True)
            return None

    async def get_user_flows(
        self, user_id: str, client_account_id: str, engagement_id: Optional[str] = None
    ) -> List[DiscoveryFlow]:
        """
        Get all flows accessible to a user.

        Args:
            user_id: The user ID
            client_account_id: The client account ID (UUID string)
            engagement_id: Optional engagement ID (will be derived from user if not provided)

        Returns:
            List of DiscoveryFlow objects
        """
        try:
            flows = []

            # If engagement_id not provided, try to get it from user context
            if not engagement_id:
                user = await self.get_user_with_context(user_id)
                if user:
                    # Use default_engagement_id instead of trying to access engagement.id
                    engagement_id = user.default_engagement_id
                    logger.info(f"Using user's default engagement: {engagement_id}")

            # Build query based on available context
            # Convert client_account_id to UUID for comparison
            try:
                client_account_uuid = uuid.UUID(client_account_id)
            except ValueError:
                logger.error(f"Invalid client_account_id format: {client_account_id}")
                return []

            stmt = select(DiscoveryFlow).where(
                DiscoveryFlow.client_account_id == client_account_uuid,
                DiscoveryFlow.status != "deleted",
                DiscoveryFlow.status != "cancelled",
            )

            # Add engagement filter if available
            if engagement_id:
                stmt = stmt.where(DiscoveryFlow.engagement_id == engagement_id)
                logger.info(f"Filtering flows by engagement: {engagement_id}")

            # Order by creation date
            stmt = stmt.order_by(DiscoveryFlow.created_at.desc())

            result = await self.db.execute(stmt)
            flows = result.scalars().all()

            logger.info(f"Found {len(flows)} flows for user {user_id}")
            return flows

        except AttributeError as e:
            logger.error(f"Context attribute error: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Error getting user flows: {e}", exc_info=True)
            return []

    async def validate_user_context(
        self, user_id: str, client_account_id: str, engagement_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate user context and permissions.

        Args:
            user_id: The user ID
            client_account_id: The client account ID (UUID string)
            engagement_id: Optional engagement ID

        Returns:
            Dict with validation results and resolved context
        """
        try:
            result = {
                "valid": False,
                "user_exists": False,
                "has_client_access": False,
                "has_engagement_access": False,
                "resolved_engagement_id": None,
                "error": None,
            }

            # Get user with context
            user = await self.get_user_with_context(user_id)
            if not user:
                result["error"] = "User not found"
                return result

            result["user_exists"] = True

            # Check client account access
            # Convert client_account_id to UUID for comparison
            try:
                client_account_uuid = uuid.UUID(client_account_id)
            except ValueError:
                result["error"] = (
                    f"Invalid client_account_id format: {client_account_id}"
                )
                return result

            if user.default_client_id == client_account_uuid:
                result["has_client_access"] = True
            else:
                result["error"] = "User does not have access to this client account"
                return result

            # Resolve engagement ID
            if engagement_id:
                # Validate provided engagement belongs to client
                stmt = select(Engagement).where(
                    Engagement.id == engagement_id,
                    Engagement.client_account_id == client_account_uuid,
                )
                eng_result = await self.db.execute(stmt)
                engagement = eng_result.scalar_one_or_none()

                if engagement:
                    result["has_engagement_access"] = True
                    result["resolved_engagement_id"] = str(engagement.id)
                else:
                    result["error"] = "Engagement not found or not accessible"
                    return result
            else:
                # Use user's default engagement
                if user.default_engagement_id:
                    result["resolved_engagement_id"] = str(user.default_engagement_id)
                    result["has_engagement_access"] = True
                else:
                    # User has no default engagement
                    logger.warning(f"User {user_id} has no default engagement")
                    result["has_engagement_access"] = False

            result["valid"] = True
            return result

        except Exception as e:
            logger.error(f"Error validating user context: {e}", exc_info=True)
            return {"valid": False, "error": str(e)}

    async def get_user_active_flows_count(
        self, user_id: str, client_account_id: str
    ) -> int:
        """
        Get count of active flows for a user.

        Args:
            user_id: The user ID
            client_account_id: The client account ID (UUID string)

        Returns:
            Count of active flows
        """
        try:
            flows = await self.get_user_flows(user_id, client_account_id)
            active_statuses = [
                "active",
                "running",
                "processing",
                "paused",
                "waiting_for_approval",
            ]
            active_flows = [f for f in flows if f.status in active_statuses]
            return len(active_flows)
        except Exception as e:
            logger.error(f"Error getting active flows count: {e}")
            return 0


async def get_user_context_service(db: AsyncSession) -> UserContextService:
    """Dependency to get user context service instance"""
    return UserContextService(db)
