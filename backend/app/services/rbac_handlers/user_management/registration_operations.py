"""
Registration Operations for User Management.
Handles user registration requests and initial setup.
"""

import logging
from typing import Any, Dict

import bcrypt

from ..base_handler import BaseRBACHandler

# Import RBAC models with fallback
try:
    from app.models.rbac import (
        AccessLevel,
        ClientAccess,
        EngagementAccess,
        UserProfile,
        UserStatus,
    )

    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = ClientAccess = EngagementAccess = None
    UserStatus = AccessLevel = None

# Import user and client models with fallback
try:
    from app.models.client_account import User

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    User = None

logger = logging.getLogger(__name__)


class RegistrationOperations(BaseRBACHandler):
    """Handler for user registration operations."""

    async def register_user_request(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user with pending approval status."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Extract name from full_name for first_name/last_name
            full_name = user_data.get("full_name", "")
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""

            # Hash the password if provided
            password_hash = None
            if user_data.get("password"):
                password_hash = bcrypt.hashpw(
                    user_data["password"].encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
                logger.info(f"Password hash created for user {user_data['user_id']}")
            else:
                logger.warning(
                    f"No password provided for user {user_data['user_id']} during registration"
                )

            # First create the base User record
            user = User(
                id=user_data["user_id"],
                email=user_data.get("email", ""),
                password_hash=password_hash,  # Store the hashed password
                first_name=first_name,
                last_name=last_name,
                is_active=False,  # Not active until approved
                is_verified=False,
                # Use provided default client/engagement IDs, fallback to demo IDs for sandbox access
                default_client_id=user_data.get(
                    "default_client_id", "11111111-1111-1111-1111-111111111111"
                ),  # DEMO_CLIENT_ID as fallback
                default_engagement_id=user_data.get(
                    "default_engagement_id", "22222222-2222-2222-2222-222222222222"
                ),  # DEMO_ENGAGEMENT_ID as fallback
            )

            self.db.add(user)
            await self.db.flush()  # Flush to ensure user exists before creating profile

            # Then create user profile with pending status
            user_profile = UserProfile(
                user_id=user_data["user_id"],
                status=UserStatus.PENDING_APPROVAL,
                registration_reason=user_data.get("registration_reason", ""),
                organization=user_data.get("organization", ""),
                role_description=user_data.get("role_description", ""),
                requested_access_level=user_data.get(
                    "requested_access_level", AccessLevel.READ_ONLY
                ),
                phone_number=user_data.get("phone_number"),
                manager_email=user_data.get("manager_email"),
                linkedin_profile=user_data.get("linkedin_profile"),
                notification_preferences=user_data.get(
                    "notification_preferences",
                    {
                        "email_notifications": True,
                        "system_alerts": True,
                        "learning_updates": False,
                        "weekly_reports": True,
                    },
                ),
            )

            self.db.add(user_profile)

            # Create pending access records
            await self._create_pending_client_access(user_data)
            await self._create_pending_engagement_access(user_data)

            await self.db.commit()
            await self.db.refresh(user_profile)

            # Log the registration
            await self._log_access(
                user_id=user_data["user_id"],
                action_type="user_registration",
                result="success",
                reason="User registered and pending admin approval",
                details={"organization": user_data.get("organization", "")},
            )

            return {
                "status": "success",
                "message": "Registration submitted successfully. Awaiting admin approval.",
                "user_profile_id": str(user_profile.user_id),
                "approval_status": "pending",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in register_user_request: {e}")
            return {"status": "error", "message": f"Registration failed: {str(e)}"}

    async def _create_pending_client_access(self, user_data: Dict[str, Any]) -> None:
        """Create pending ClientAccess if default_client_id is provided."""
        if user_data.get("default_client_id"):
            client_access = ClientAccess(
                user_profile_id=user_data["user_id"],
                client_account_id=user_data["default_client_id"],
                access_level=user_data.get(
                    "requested_access_level", AccessLevel.READ_ONLY
                ),
                permissions=self._get_default_permissions(
                    user_data.get("requested_access_level", AccessLevel.READ_ONLY)
                ),
                granted_by=None,  # Will be set when approved
                is_active=False,  # Not active until approved
            )
            self.db.add(client_access)
            logger.info(
                f"Created pending ClientAccess for user {user_data['user_id']} to client "
                f"{user_data['default_client_id']}"
            )

    async def _create_pending_engagement_access(
        self, user_data: Dict[str, Any]
    ) -> None:
        """Create pending EngagementAccess if default_engagement_id is provided."""
        if user_data.get("default_engagement_id"):
            engagement_access = EngagementAccess(
                user_profile_id=user_data["user_id"],
                engagement_id=user_data["default_engagement_id"],
                access_level=user_data.get(
                    "requested_access_level", AccessLevel.READ_ONLY
                ),
                engagement_role=user_data.get("role_description", "Analyst"),
                permissions=self._get_default_permissions(
                    user_data.get("requested_access_level", AccessLevel.READ_ONLY)
                ),
                granted_by=None,  # Will be set when approved
                is_active=False,  # Not active until approved
            )
            self.db.add(engagement_access)
            logger.info(
                f"Created pending EngagementAccess for user {user_data['user_id']} to engagement "
                f"{user_data['default_engagement_id']}"
            )
