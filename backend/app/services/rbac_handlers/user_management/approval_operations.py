"""
Approval Operations for User Management.
Handles user approval and rejection workflows.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from ..base_handler import BaseRBACHandler

# Import RBAC models with fallback
try:
    from app.models.rbac import (
        AccessLevel,
        ClientAccess,
        EngagementAccess,
        RoleType,
        UserProfile,
        UserRole,
        UserStatus,
    )

    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = UserRole = ClientAccess = EngagementAccess = None
    UserStatus = AccessLevel = RoleType = None

# Import user and client models with fallback
try:
    from app.models.client_account import User

    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    User = None

logger = logging.getLogger(__name__)

# Demo client and engagement IDs - ALL approved users get access to these by default
DEMO_CLIENT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"


class ApprovalOperations(BaseRBACHandler):
    """Handler for user approval and rejection operations."""

    async def approve_user(
        self, user_id: str, approved_by: str, approval_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Approve a pending user registration."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get pending user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.PENDING_APPROVAL,
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()

            if not user_profile:
                return {
                    "status": "error",
                    "message": "User not found or not pending approval",
                }

            # Get and activate the base User record
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                user.is_active = True
                user.is_verified = True
                # CRITICAL: Set defaults to Demo client/engagement for all approved users
                # This ensures users always have a "sandbox" environment they can access
                user.default_client_id = DEMO_CLIENT_ID
                user.default_engagement_id = DEMO_ENGAGEMENT_ID
                logger.info(f"Set user {user_id} defaults to Demo client/engagement")

            # Update user profile
            user_profile.approve(approved_by)

            # Grant default access based on approval
            access_level = approval_data.get(
                "access_level", user_profile.requested_access_level
            )
            client_accesses = approval_data.get("client_access", [])

            # CRITICAL: Grant Demo client and engagement access to ALL approved users
            # This ensures users can never be locked out - they always have sandbox access
            # Additional clients/engagements can be added by admin through user management
            await self._grant_demo_access(user_id, access_level, approved_by)

            # Activate pending access records
            await self._activate_pending_access_records(user_id, approved_by)

            # Create additional access records if specified
            await self._create_additional_client_access(
                user_id, client_accesses, access_level, approved_by
            )

            # Create default user role
            await self._create_default_user_role(
                user_id, access_level, approval_data, approved_by
            )

            await self.db.commit()

            # Log the approval
            await self._log_access(
                user_id=approved_by,
                action_type="user_approval",
                result="success",
                reason=f"User {user_id} approved by admin",
                details={"approved_user": user_id, "access_level": access_level},
            )

            return {
                "status": "success",
                "message": "User approved successfully",
                "user_id": user_id,
                "access_level": access_level,
                "client_access_count": len(client_accesses),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in approve_user: {e}")
            return {"status": "error", "message": f"Approval failed: {str(e)}"}

    async def reject_user(
        self, user_id: str, rejected_by: str, rejection_reason: str
    ) -> Dict[str, Any]:
        """Reject a pending user registration."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get pending user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.PENDING_APPROVAL,
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()

            if not user_profile:
                return {
                    "status": "error",
                    "message": "User not found or not pending approval",
                }

            # Update user profile to rejected
            user_profile.reject(rejected_by, rejection_reason)

            await self.db.commit()

            # Log the rejection
            await self._log_access(
                user_id=rejected_by,
                action_type="user_rejection",
                result="success",
                reason=f"User {user_id} rejected: {rejection_reason}",
                details={
                    "rejected_user": user_id,
                    "rejection_reason": rejection_reason,
                },
            )

            return {
                "status": "success",
                "message": "User registration rejected",
                "user_id": user_id,
                "reason": rejection_reason,  # Changed to match schema
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in reject_user: {e}")
            return {"status": "error", "message": f"Rejection failed: {str(e)}"}

    async def get_pending_approvals(self, admin_user_id: str) -> Dict[str, Any]:
        """Get all users pending approval."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get all pending user profiles with related user data
            query = (
                select(UserProfile)
                .options(selectinload(UserProfile.user))
                .where(UserProfile.status == UserStatus.PENDING_APPROVAL)
                .order_by(UserProfile.created_at.desc())
            )

            result = await self.db.execute(query)
            pending_profiles = result.scalars().all()

            pending_users = []
            for profile in pending_profiles:
                # Build full name from user first/last name
                full_name = ""
                if profile.user:
                    first = profile.user.first_name or ""
                    last = profile.user.last_name or ""
                    full_name = f"{first} {last}".strip()
                    # Fallback to username or email prefix if no name provided
                    if not full_name:
                        if profile.user.username:
                            full_name = profile.user.username
                        elif profile.user.email:
                            full_name = profile.user.email.split("@")[0]
                        else:
                            full_name = "Unknown User"

                user_info = {
                    "user_id": str(profile.user_id),
                    "email": profile.user.email if profile.user else "",
                    "username": (
                        profile.user.username
                        if profile.user and profile.user.username
                        else ""
                    ),
                    "full_name": full_name,
                    "first_name": profile.user.first_name if profile.user else "",
                    "last_name": profile.user.last_name if profile.user else "",
                    "organization": profile.organization or "",
                    "role_description": profile.role_description or "",
                    "registration_reason": profile.registration_reason or "",
                    "requested_access_level": profile.requested_access_level
                    or "read_only",
                    "phone_number": profile.phone_number or "",
                    "manager_email": profile.manager_email or "",
                    "linkedin_profile": profile.linkedin_profile or "",
                    "created_at": (
                        profile.created_at.isoformat() if profile.created_at else None
                    ),
                    "registration_requested_at": (
                        profile.created_at.isoformat() if profile.created_at else None
                    ),  # For frontend compatibility
                    "notification_preferences": profile.notification_preferences or {},
                    "status": "pending_approval",  # Explicitly set status
                }
                pending_users.append(user_info)

            # Log the access
            await self._log_access(
                user_id=admin_user_id,
                action_type="view_pending_approvals",
                result="success",
                reason=f"Viewed {len(pending_users)} pending approvals",
            )

            return {
                "status": "success",
                "pending_approvals": pending_users,
                "total_pending": len(pending_users),
            }

        except Exception as e:
            logger.error(f"Error in get_pending_approvals: {e}")
            return {
                "status": "error",
                "message": f"Failed to get pending approvals: {str(e)}",
            }

    async def _activate_pending_access_records(
        self, user_id: str, approved_by: str
    ) -> None:
        """Activate pending access records from registration."""
        # Activate pending ClientAccess records
        pending_client_access = await self.db.execute(
            select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == user_id,
                    not ClientAccess.is_active,
                )
            )
        )
        for access in pending_client_access.scalars():
            access.is_active = True
            access.granted_by = approved_by
            access.granted_at = datetime.utcnow()
            logger.info(
                f"Activated pending ClientAccess {access.id} for user {user_id}"
            )

        # Activate pending EngagementAccess records
        pending_engagement_access = await self.db.execute(
            select(EngagementAccess).where(
                and_(
                    EngagementAccess.user_profile_id == user_id,
                    not EngagementAccess.is_active,
                )
            )
        )
        for access in pending_engagement_access.scalars():
            access.is_active = True
            access.granted_by = approved_by
            access.granted_at = datetime.utcnow()
            logger.info(
                f"Activated pending EngagementAccess {access.id} for user {user_id}"
            )

    async def _grant_demo_access(
        self, user_id: str, access_level: str, approved_by: str
    ) -> None:
        """
        Grant Demo client and engagement access to newly approved user.

        This ensures ALL approved users have a sandbox environment they can access.
        Additional clients/engagements must be granted by admin through user management.
        """
        # Check if user already has Demo client access (avoid duplicates)
        existing_client_access = await self.db.execute(
            select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == user_id,
                    ClientAccess.client_account_id == DEMO_CLIENT_ID,
                )
            )
        )
        demo_client_access = existing_client_access.scalar_one_or_none()

        # Create Demo client access if doesn't exist
        if not demo_client_access:
            demo_client_access = ClientAccess(
                user_profile_id=user_id,
                client_account_id=DEMO_CLIENT_ID,
                access_level=access_level,
                permissions=self._get_default_permissions(access_level),
                granted_by=approved_by,
                is_active=True,
                granted_at=datetime.utcnow(),
            )
            self.db.add(demo_client_access)
            logger.info(
                f"✅ Created Demo ClientAccess for user {user_id} (access_level: {access_level})"
            )
        else:
            # If exists but inactive, activate it
            if not demo_client_access.is_active:
                demo_client_access.is_active = True
                demo_client_access.granted_by = approved_by
                demo_client_access.granted_at = datetime.utcnow()
                logger.info(
                    f"✅ Activated existing Demo ClientAccess for user {user_id}"
                )

        # Check if user already has Demo engagement access (avoid duplicates)
        existing_engagement_access = await self.db.execute(
            select(EngagementAccess).where(
                and_(
                    EngagementAccess.user_profile_id == user_id,
                    EngagementAccess.engagement_id == DEMO_ENGAGEMENT_ID,
                )
            )
        )
        demo_engagement_access = existing_engagement_access.scalar_one_or_none()

        # Create Demo engagement access if doesn't exist
        if not demo_engagement_access:
            demo_engagement_access = EngagementAccess(
                user_profile_id=user_id,
                engagement_id=DEMO_ENGAGEMENT_ID,
                access_level=access_level,
                engagement_role="Analyst",  # Default role for demo access
                permissions=self._get_default_permissions(access_level),
                granted_by=approved_by,
                is_active=True,
                granted_at=datetime.utcnow(),
            )
            self.db.add(demo_engagement_access)
            logger.info(
                f"✅ Created Demo EngagementAccess for user {user_id} (access_level: {access_level})"
            )
        else:
            # If exists but inactive, activate it
            if not demo_engagement_access.is_active:
                demo_engagement_access.is_active = True
                demo_engagement_access.granted_by = approved_by
                demo_engagement_access.granted_at = datetime.utcnow()
                logger.info(
                    f"✅ Activated existing Demo EngagementAccess for user {user_id}"
                )

    async def _create_additional_client_access(
        self, user_id: str, client_accesses: list, access_level: str, approved_by: str
    ) -> None:
        """Create additional client access records if specified."""
        for client_access_data in client_accesses:
            client_access = ClientAccess(
                user_profile_id=user_id,
                client_account_id=client_access_data["client_id"],
                access_level=access_level,
                permissions=client_access_data.get(
                    "permissions", self._get_default_permissions(access_level)
                ),
                granted_by=approved_by,
            )
            self.db.add(client_access)

    async def _create_default_user_role(
        self,
        user_id: str,
        access_level: str,
        approval_data: Dict[str, Any],
        approved_by: str,
    ) -> None:
        """Create default user role."""
        user_role = UserRole(
            user_id=user_id,
            role_type=self._determine_role_type(access_level),
            role_name=approval_data.get("role_name", "Analyst"),
            description="Default role assigned upon approval",
            permissions=self._get_default_role_permissions(access_level),
            assigned_by=approved_by,
        )
        self.db.add(user_role)
