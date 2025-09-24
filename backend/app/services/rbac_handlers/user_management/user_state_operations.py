"""
User State Operations for User Management.
Handles user activation and deactivation operations.
"""

import logging
from typing import Any, Dict

from sqlalchemy import and_, select

from ..base_handler import BaseRBACHandler

# Import RBAC models with fallback
try:
    from app.models.rbac import UserProfile, UserStatus

    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = UserStatus = None

# Import user and client models with fallback
try:
    from app.models.client_account import User

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    User = None

logger = logging.getLogger(__name__)


class UserStateOperations(BaseRBACHandler):
    """Handler for user state management operations (activate/deactivate)."""

    async def deactivate_user(
        self, user_id: str, deactivated_by: str, reason: str = None
    ) -> Dict[str, Any]:
        """Deactivate an active user."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get active user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.ACTIVE,
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()

            if not user_profile:
                return {"status": "error", "message": "User not found or not active"}

            # Deactivate the base User record
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                user.is_active = False

            # Update user profile to inactive
            user_profile.deactivate(deactivated_by, reason)

            await self.db.commit()

            # Log the deactivation - handle demo users properly
            log_user_id = self._get_log_user_id(deactivated_by)

            await self._log_access(
                user_id=log_user_id,
                action_type="user_deactivation",
                result="success",
                reason=f"User {user_id} deactivated: {reason or 'No reason provided'}",
                details={"deactivated_user": user_id, "deactivation_reason": reason},
            )

            return {
                "status": "success",
                "message": "User deactivated successfully",
                "user_id": user_id,
                "deactivation_reason": reason,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in deactivate_user: {e}")
            return {"status": "error", "message": f"Deactivation failed: {str(e)}"}

    async def activate_user(
        self, user_id: str, activated_by: str, reason: str = None
    ) -> Dict[str, Any]:
        """Activate a deactivated user."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get deactivated user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.DEACTIVATED,
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()

            if not user_profile:
                return {
                    "status": "error",
                    "message": "User not found or not deactivated",
                }

            # Activate the base User record
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                user.is_active = True

            # Update user profile to active
            user_profile.activate(activated_by, reason)

            await self.db.commit()

            # Log the activation - handle demo users properly
            log_user_id = self._get_log_user_id(activated_by)

            await self._log_access(
                user_id=log_user_id,
                action_type="user_activation",
                result="success",
                reason=f"User {user_id} activated: {reason or 'No reason provided'}",
                details={"activated_user": user_id, "activation_reason": reason},
            )

            return {
                "status": "success",
                "message": "User activated successfully",
                "user_id": user_id,
                "activation_reason": reason,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in activate_user: {e}")
            return {"status": "error", "message": f"Activation failed: {str(e)}"}

    def _get_log_user_id(self, user_id: str) -> str:
        """Get proper user ID for logging, handling demo users."""
        if user_id == "admin_user":
            # Use a valid UUID for demo admin user
            return "eef6ea50-6550-4f14-be2c-081d4eb23038"
        return user_id
