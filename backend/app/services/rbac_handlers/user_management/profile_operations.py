"""
Profile Operations for User Management.
Handles user profile queries and updates.
"""

import logging
from datetime import datetime
from typing import Any, Dict
import uuid

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload, joinedload

from app.core.security.cache_encryption import secure_setattr
from ..base_handler import BaseRBACHandler

# Import RBAC models with fallback
try:
    from app.models.rbac import (
        AccessLevel,
        ClientAccess,
        EngagementAccess,
        UserProfile,
    )

    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = ClientAccess = EngagementAccess = None
    AccessLevel = None

# Import user and client models with fallback
try:
    from app.models.client_account import User

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    User = None

logger = logging.getLogger(__name__)


class ProfileOperations(BaseRBACHandler):
    """Handler for user profile operations (queries and updates)."""

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get user profile with related user data
            query = (
                select(UserProfile)
                .options(selectinload(UserProfile.user))
                .where(UserProfile.user_id == user_id)
            )

            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()

            if not user_profile:
                return {"status": "error", "message": "User profile not found"}

            # Convert to response format
            profile_data = self._format_profile_data(user_profile)

            return {"status": "success", "user_profile": profile_data}

        except Exception as e:
            logger.error(f"Error in get_user_profile: {e}")
            return {
                "status": "error",
                "message": f"Failed to get user profile: {str(e)}",
            }

    async def update_user_profile(
        self, user_id: str, profile_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user profile information with proper field mapping and automatic access creation."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get user profile with related user data - use joinedload for proper session tracking
            query = (
                select(UserProfile)
                .options(joinedload(UserProfile.user))
                .where(UserProfile.user_id == user_id)
            )

            result = await self.db.execute(query)
            user_profile = result.unique().scalar_one_or_none()

            if not user_profile:
                return {"status": "error", "message": "User profile not found"}

            # Track what client/engagement access needs to be created
            new_client_id = None
            new_engagement_id = None
            old_client_id = (
                user_profile.user.default_client_id if user_profile.user else None
            )
            old_engagement_id = (
                user_profile.user.default_engagement_id if user_profile.user else None
            )

            # Update profile fields
            await self._update_user_fields(user_profile, profile_updates)
            await self._update_profile_fields(user_profile, profile_updates)

            # Extract new client and engagement IDs for access creation
            new_client_id = self._extract_new_client_id(profile_updates)
            new_engagement_id = self._extract_new_engagement_id(profile_updates)

            # Update the updated_at timestamp
            user_profile.updated_at = datetime.utcnow()

            # Create access records for new client/engagement assignments
            access_records_created = await self._create_access_records(
                user_id,
                new_client_id,
                new_engagement_id,
                old_client_id,
                old_engagement_id,
            )

            await self.db.commit()
            await self.db.refresh(user_profile)

            # Log the update
            await self._log_access(
                user_id=user_id,
                action_type="user_profile_updated",
                result="success",
                reason="User profile updated successfully with automatic access creation",
                details={
                    "updated_fields": list(profile_updates.keys()),
                    "access_records_created": access_records_created,
                },
            )

            # Return updated profile data
            updated_profile = await self.get_user_profile(user_id)
            if updated_profile.get("status") == "success":
                updated_profile["access_records_created"] = access_records_created
            return updated_profile

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in update_user_profile: {e}")
            return {
                "status": "error",
                "message": f"Failed to update user profile: {str(e)}",
            }

    def _format_profile_data(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Format user profile data for response."""
        return {
            "user_id": str(user_profile.user_id),
            "email": user_profile.user.email if user_profile.user else "",
            "full_name": (
                f"{user_profile.user.first_name} {user_profile.user.last_name}".strip()
                if user_profile.user
                else ""
            ),
            "first_name": user_profile.user.first_name if user_profile.user else "",
            "last_name": user_profile.user.last_name if user_profile.user else "",
            "status": user_profile.status,
            "organization": user_profile.organization,
            "role_description": user_profile.role_description,
            "requested_access_level": user_profile.requested_access_level,
            "phone_number": user_profile.phone_number,
            "manager_email": user_profile.manager_email,
            "linkedin_profile": user_profile.linkedin_profile,
            "notification_preferences": user_profile.notification_preferences or {},
            "last_login_at": (
                user_profile.last_login_at.isoformat()
                if user_profile.last_login_at
                else None
            ),
            "login_count": user_profile.login_count or 0,
            "created_at": (
                user_profile.created_at.isoformat() if user_profile.created_at else None
            ),
            "updated_at": (
                user_profile.updated_at.isoformat() if user_profile.updated_at else None
            ),
            "is_active": (user_profile.user.is_active if user_profile.user else False),
        }

    async def _update_user_fields(
        self, user_profile: UserProfile, profile_updates: Dict[str, Any]
    ) -> None:
        """Update User model fields."""
        user_field_mapping = {
            "full_name": None,  # Special handling needed
            "first_name": "first_name",
            "last_name": "last_name",
            "email": "email",
            "default_client_id": "default_client_id",
            "default_engagement_id": "default_engagement_id",
        }

        if user_profile.user:
            for frontend_field, db_field in user_field_mapping.items():
                if (
                    frontend_field in profile_updates
                    and profile_updates[frontend_field] is not None
                ):
                    value = profile_updates[frontend_field]

                    if frontend_field == "full_name":
                        # Split full_name into first_name and last_name
                        name_parts = value.strip().split(" ", 1)
                        user_profile.user.first_name = (
                            name_parts[0] if len(name_parts) > 0 else ""
                        )
                        user_profile.user.last_name = (
                            name_parts[1] if len(name_parts) > 1 else ""
                        )
                    elif frontend_field in [
                        "default_client_id",
                        "default_engagement_id",
                    ]:
                        await self._update_uuid_field(
                            user_profile.user, db_field, value
                        )
                    elif db_field and hasattr(user_profile.user, db_field):
                        secure_setattr(user_profile.user, db_field, value)

    async def _update_profile_fields(
        self, user_profile: UserProfile, profile_updates: Dict[str, Any]
    ) -> None:
        """Update UserProfile model fields."""
        profile_field_mapping = {
            "organization": "organization",
            "role_description": "role_description",
            "phone_number": "phone_number",
            "manager_email": "manager_email",
            "linkedin_profile": "linkedin_profile",
            "notification_preferences": "notification_preferences",
        }

        for frontend_field, db_field in profile_field_mapping.items():
            if (
                frontend_field in profile_updates
                and profile_updates[frontend_field] is not None
            ):
                value = profile_updates[frontend_field]
                if hasattr(user_profile, db_field):
                    secure_setattr(user_profile, db_field, value)

    async def _update_uuid_field(self, user_obj, field_name: str, value: str) -> None:
        """Update UUID field with proper validation."""
        # Special handling for UUID fields - convert 'none' to None
        if value == "none" or value == "":
            secure_setattr(user_obj, field_name, None)
        else:
            # Validate UUID format
            try:
                uuid_value = uuid.UUID(value)
                secure_setattr(user_obj, field_name, uuid_value)
            except ValueError:
                logger.warning(f"Invalid UUID format for {field_name}: {value}")
                # Skip invalid UUIDs but don't fail the entire update

    def _extract_new_client_id(self, profile_updates: Dict[str, Any]):
        """Extract new client ID from profile updates."""
        if "default_client_id" in profile_updates:
            value = profile_updates["default_client_id"]
            if value and value != "none" and value != "":
                try:
                    return uuid.UUID(value)
                except ValueError:
                    pass
        return None

    def _extract_new_engagement_id(self, profile_updates: Dict[str, Any]):
        """Extract new engagement ID from profile updates."""
        if "default_engagement_id" in profile_updates:
            value = profile_updates["default_engagement_id"]
            if value and value != "none" and value != "":
                try:
                    return uuid.UUID(value)
                except ValueError:
                    pass
        return None

    async def _create_access_records(
        self,
        user_id: str,
        new_client_id,
        new_engagement_id,
        old_client_id,
        old_engagement_id,
    ) -> list:
        """Create access records for new client/engagement assignments."""
        access_records_created = []

        # Create client access if new client assigned and doesn't already exist
        if new_client_id and new_client_id != old_client_id:
            if not await self._client_access_exists(user_id, new_client_id):
                await self._create_client_access_record(user_id, new_client_id)
                access_records_created.append(f"client_access:{new_client_id}")

        # Create engagement access if new engagement assigned and doesn't already exist
        if new_engagement_id and new_engagement_id != old_engagement_id:
            if not await self._engagement_access_exists(user_id, new_engagement_id):
                await self._create_engagement_access_record(user_id, new_engagement_id)
                access_records_created.append(f"engagement_access:{new_engagement_id}")

        return access_records_created

    async def _client_access_exists(self, user_id: str, client_id) -> bool:
        """Check if client access already exists."""
        existing_client_access = await self.db.execute(
            select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == user_id,
                    ClientAccess.client_account_id == client_id,
                    ClientAccess.is_active,
                )
            )
        )
        return existing_client_access.scalar_one_or_none() is not None

    async def _engagement_access_exists(self, user_id: str, engagement_id) -> bool:
        """Check if engagement access already exists."""
        existing_engagement_access = await self.db.execute(
            select(EngagementAccess).where(
                and_(
                    EngagementAccess.user_profile_id == user_id,
                    EngagementAccess.engagement_id == engagement_id,
                    EngagementAccess.is_active,
                )
            )
        )
        return existing_engagement_access.scalar_one_or_none() is not None

    async def _create_client_access_record(self, user_id: str, client_id) -> None:
        """Create a new client access record."""
        client_access = ClientAccess(
            user_profile_id=user_id,
            client_account_id=client_id,
            access_level=AccessLevel.READ_WRITE,  # Default access level
            permissions={
                "can_view_data": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_manage_engagements": False,
                "can_configure_client_settings": False,
                "can_manage_client_users": False,
            },
            granted_by=user_id,  # Self-assigned through admin interface
        )
        self.db.add(client_access)
        logger.info(f"Created client access for user {user_id} to client {client_id}")

    async def _create_engagement_access_record(
        self, user_id: str, engagement_id
    ) -> None:
        """Create a new engagement access record."""
        engagement_access = EngagementAccess(
            user_profile_id=user_id,
            engagement_id=engagement_id,
            access_level=AccessLevel.READ_WRITE,  # Default access level
            engagement_role="architect",  # Default role
            permissions={
                "can_view_data": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_manage_sessions": False,
                "can_configure_agents": False,
                "can_access_sensitive_data": True,
                "can_approve_migration_decisions": False,
            },
            granted_by=user_id,  # Self-assigned through admin interface
        )
        self.db.add(engagement_access)
        logger.info(
            f"Created engagement access for user {user_id} to engagement {engagement_id}"
        )
