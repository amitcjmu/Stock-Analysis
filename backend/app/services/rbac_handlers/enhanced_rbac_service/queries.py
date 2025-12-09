"""
Query methods for Enhanced RBAC Service - read operations for user profiles and permissions.
"""

from typing import Any, Dict, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from .base import DataScope, EnhancedUserProfile, logger


class RBACQueries:
    """Query methods for RBAC read operations."""

    async def get_user_profile(self, user_id: str) -> Optional[EnhancedUserProfile]:
        """Get enhanced user profile by user ID."""
        if not self.is_available:
            return None

        try:
            # EnhancedUserProfile is a user-scoped table, not tenant-scoped
            query = (
                select(EnhancedUserProfile)  # SKIP_TENANT_CHECK
                .where(
                    and_(
                        EnhancedUserProfile.user_id == user_id,
                        EnhancedUserProfile.is_deleted == False,  # noqa: E712
                    )
                )
                .options(
                    selectinload(EnhancedUserProfile.scope_client),
                    selectinload(EnhancedUserProfile.scope_engagement),
                )
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    async def get_user_accessible_data(
        self, user_id: str, include_demo: bool = True
    ) -> Dict[str, Any]:
        """
        Get all data that a user can access based on their role and scope.
        Returns client_account_ids and engagement_ids the user can access.
        """
        if not self.is_available:
            return {
                "client_account_ids": [],
                "engagement_ids": [],
                "scope": "all",
                "include_demo": include_demo,
            }

        try:
            user_profile = await self.get_user_profile(user_id)
            if not user_profile or not user_profile.is_active:
                return {
                    "client_account_ids": [],
                    "engagement_ids": [],
                    "scope": "none",
                    "include_demo": include_demo,
                }

            # Platform admin can access all data
            if user_profile.is_platform_admin:
                return {
                    "client_account_ids": [],  # Empty means all
                    "engagement_ids": [],  # Empty means all
                    "scope": "platform",
                    "include_demo": include_demo,
                }

            # Get accessible client and engagement IDs
            accessible_clients = user_profile.get_accessible_client_ids()
            accessible_engagements = user_profile.get_accessible_engagement_ids()

            # If engagement scope, also include the client
            if (
                user_profile.data_scope == DataScope.ENGAGEMENT
                and user_profile.scope_client_account_id
            ):
                if str(user_profile.scope_client_account_id) not in accessible_clients:
                    accessible_clients.append(str(user_profile.scope_client_account_id))

            return {
                "client_account_ids": accessible_clients,
                "engagement_ids": accessible_engagements,
                "scope": user_profile.data_scope,
                "role_level": user_profile.role_level,
                "include_demo": include_demo,
            }

        except Exception as e:
            logger.error(f"Error getting user accessible data: {e}")
            return {
                "client_account_ids": [],
                "engagement_ids": [],
                "scope": "error",
                "include_demo": include_demo,
            }
