"""
User Management Handler for RBAC operations.
Handles user registration, approval, rejection, and basic user operations.

This is the main entry point that combines all user management operations
while maintaining backward compatibility with the original interface.
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from .registration_operations import RegistrationOperations
from .approval_operations import ApprovalOperations
from .user_state_operations import UserStateOperations
from .profile_operations import ProfileOperations

logger = logging.getLogger(__name__)


class UserManagementHandler:
    """
    Main handler for user registration, approval, and management operations.

    This handler orchestrates multiple specialized operation handlers while
    maintaining the same public API as the original monolithic handler.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

        # Initialize specialized operation handlers
        self._registration_ops = RegistrationOperations(db)
        self._approval_ops = ApprovalOperations(db)
        self._user_state_ops = UserStateOperations(db)
        self._profile_ops = ProfileOperations(db)

        # Expose availability status
        self.is_available = self._registration_ops.is_available

    # Registration Operations
    async def register_user_request(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user with pending approval status."""
        return await self._registration_ops.register_user_request(user_data)

    # Approval Operations
    async def approve_user(
        self, user_id: str, approved_by: str, approval_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Approve a pending user registration."""
        return await self._approval_ops.approve_user(
            user_id, approved_by, approval_data
        )

    async def reject_user(
        self, user_id: str, rejected_by: str, rejection_reason: str
    ) -> Dict[str, Any]:
        """Reject a pending user registration."""
        return await self._approval_ops.reject_user(
            user_id, rejected_by, rejection_reason
        )

    async def get_pending_approvals(self, admin_user_id: str) -> Dict[str, Any]:
        """Get all users pending approval."""
        return await self._approval_ops.get_pending_approvals(admin_user_id)

    # User State Operations
    async def deactivate_user(
        self, user_id: str, deactivated_by: str, reason: str = None
    ) -> Dict[str, Any]:
        """Deactivate an active user."""
        return await self._user_state_ops.deactivate_user(
            user_id, deactivated_by, reason
        )

    async def activate_user(
        self, user_id: str, activated_by: str, reason: str = None
    ) -> Dict[str, Any]:
        """Activate a deactivated user."""
        return await self._user_state_ops.activate_user(user_id, activated_by, reason)

    # Profile Operations
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information."""
        return await self._profile_ops.get_user_profile(user_id)

    async def update_user_profile(
        self, user_id: str, profile_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user profile information with proper field mapping and automatic access creation."""
        return await self._profile_ops.update_user_profile(user_id, profile_updates)
