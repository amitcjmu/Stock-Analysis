"""
Engagement Service

Business logic for engagement-related operations.
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client_account import Engagement
from app.models.rbac import ClientAccess

from ..models.context_schemas import EngagementResponse, EngagementsListResponse

logger = logging.getLogger(__name__)


class EngagementService:
    """Service for engagement-related business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_client_engagements(
        self, client_id: str, user_id: UUID, is_platform_admin: bool
    ) -> EngagementsListResponse:
        """
        Get engagements for a specific client.

        Args:
            client_id: The client ID to get engagements for
            user_id: The current user ID
            is_platform_admin: Whether the user is a platform admin

        Returns:
            List of engagements for the client
        """
        engagements = []

        try:
            # Validate user has access to this client
            if not is_platform_admin:
                has_access = await self._user_has_client_access(user_id, client_id)
                if not has_access:
                    return EngagementsListResponse(engagements=[])

            # Get engagements for the client
            if client_id == "11111111-1111-1111-1111-111111111111":
                # Return demo engagements
                engagements = self._get_demo_engagements(client_id)
            else:
                # Get real engagements
                engagements = await self._get_real_engagements(client_id)

        except Exception as e:
            logger.error(f"Error fetching engagements: {e}")
            # Return demo data as fallback for demo client
            if client_id == "11111111-1111-1111-1111-111111111111":
                engagements = self._get_demo_engagements(client_id)

        return EngagementsListResponse(engagements=engagements)

    async def _user_has_client_access(self, user_id: UUID, client_id: str) -> bool:
        """Check if user has access to the specified client"""
        try:
            # Convert client_id string to UUID if needed
            client_uuid = UUID(client_id)

            query = select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == str(user_id),
                    ClientAccess.client_account_id == client_uuid,
                    ClientAccess.is_active is True,
                )
            )
            result = await self.db.execute(query)
            access = result.scalar_one_or_none()
            return access is not None
        except Exception as e:
            logger.error(f"Error checking client access: {e}")
            return False

    def _get_demo_engagements(self, client_id: str) -> List[EngagementResponse]:
        """Get demo engagements"""
        return [
            EngagementResponse(
                id="22222222-2222-2222-2222-222222222222",
                name="Cloud Migration 2024",
                client_id=client_id,
                status="active",
                type="migration",
            )
        ]

    async def _get_real_engagements(self, client_id: str) -> List[EngagementResponse]:
        """Get real engagements from database"""
        engagements = []

        try:
            client_uuid = UUID(client_id)

            query = select(Engagement).where(
                and_(
                    Engagement.client_account_id == client_uuid,
                    Engagement.is_active is True,
                )
            )
            result = await self.db.execute(query)
            engagement_records = result.scalars().all()

            for engagement in engagement_records:
                engagements.append(
                    EngagementResponse(
                        id=str(engagement.id),
                        name=engagement.name,
                        client_id=client_id,
                        status=(
                            engagement.status
                            if hasattr(engagement, "status")
                            else ("active" if engagement.is_active else "inactive")
                        ),
                        type=(
                            engagement.engagement_type
                            if hasattr(engagement, "engagement_type")
                            else "migration"
                        ),
                        start_date=(
                            engagement.start_date.isoformat()
                            if hasattr(engagement, "start_date")
                            and engagement.start_date
                            else None
                        ),
                        end_date=(
                            engagement.target_completion_date.isoformat()
                            if hasattr(engagement, "target_completion_date")
                            and engagement.target_completion_date
                            else None
                        ),
                    )
                )
        except Exception as e:
            logger.error(f"Error fetching real engagements: {e}")

        return engagements
