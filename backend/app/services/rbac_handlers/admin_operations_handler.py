"""
Admin Operations Handler for RBAC operations.
Handles admin-specific operations like user creation and system management.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import select

from .base_handler import BaseRBACHandler

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


class AdminOperationsHandler(BaseRBACHandler):
    """Handler for admin operations and system management."""

    def _map_access_level(self, access_level: str) -> str:
        """Map common access level names to enum values."""
        mapping = {
            "analyst": AccessLevel.READ_WRITE,
            "manager": AccessLevel.ADMIN,
            "admin": AccessLevel.SUPER_ADMIN,
            "read_only": AccessLevel.READ_ONLY,
            "read_write": AccessLevel.READ_WRITE,
            "super_admin": AccessLevel.SUPER_ADMIN,
        }
        return mapping.get(access_level.lower(), AccessLevel.READ_WRITE)

    async def admin_create_user(
        self, user_data: Dict[str, Any], created_by: str
    ) -> Dict[str, Any]:
        """Admin direct user creation with immediate activation."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Check if user already exists
            email = user_data.get("email", "")
            if not email:
                return {"status": "error", "message": "Email is required"}

            from sqlalchemy import select

            from app.models.client_account import User

            existing_user = await self.db.execute(
                select(User).where(User.email == email)
            )
            if existing_user.scalar_one_or_none():
                return {
                    "status": "error",
                    "message": f"User with email {email} already exists",
                }

            # Generate UUID if not provided
            user_id = user_data.get("user_id", str(uuid.uuid4()))

            # Extract name components
            full_name = user_data.get("full_name", "")
            name_parts = full_name.split(" ", 1)
            first_name = (
                name_parts[0] if name_parts else user_data.get("first_name", "")
            )
            last_name = (
                name_parts[1] if len(name_parts) > 1 else user_data.get("last_name", "")
            )

            # Handle admin user identification - use actual authenticated user ID
            admin_user_uuid = None
            if created_by and created_by not in [
                "admin_user",
                "demo_user",
                "system",
                "system_setup",
            ]:
                try:
                    admin_user_uuid = uuid.UUID(created_by)
                except ValueError:
                    # If created_by is not a valid UUID, set to None
                    admin_user_uuid = None

            # SECURITY: Allow NULL for admin_user_uuid if no created_by provided
            # This allows platform admins to create users without foreign key dependency
            if admin_user_uuid is None:
                logger.info(
                    "No created_by user provided - using NULL for assigned_by (allowed for platform admin operations)"
                )
                admin_user_uuid = None  # Allow NULL assigned_by

            # Map access level to proper enum value
            access_level = self._map_access_level(
                user_data.get("access_level", "analyst")
            )

            # Hash the password
            password = user_data.get(
                "password", "defaultpassword123"
            )  # nosec B105 - Default fallback password
            import bcrypt

            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            # Create base User record
            user = User(
                id=user_id,
                email=user_data.get("email", ""),
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=user_data.get("is_active", True),
                is_verified=True,
                is_mock=False,
                # Use provided values or default to demo IDs
                default_client_id=user_data.get(
                    "default_client_id", "11111111-1111-1111-1111-111111111111"
                ),
                default_engagement_id=user_data.get(
                    "default_engagement_id", "22222222-2222-2222-2222-222222222222"
                ),
            )

            self.db.add(user)
            await self.db.flush()

            # Create UserProfile with active status
            user_profile = UserProfile(
                user_id=user_id,
                status=UserStatus.ACTIVE,
                organization=user_data.get("organization", ""),
                role_description=user_data.get("role_description", ""),
                requested_access_level=access_level,
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
                approved_by=admin_user_uuid,  # Use UUID or None (NULL allowed for first admin)
                approved_at=datetime.utcnow() if user_data.get("is_active") else None,
            )

            self.db.add(user_profile)
            await self.db.flush()

            # Create UserRole
            user_role = UserRole(
                user_id=user_id,
                role_type=self._determine_role_type(access_level),
                role_name=user_data.get("role_name", "Analyst"),
                description=user_data.get(
                    "role_description", f"Admin created user with {access_level} access"
                ),
                permissions=self._get_default_role_permissions(access_level),
                assigned_by=admin_user_uuid,  # Use UUID or None (NULL allowed for first admin)
                is_active=True,
            )

            self.db.add(user_role)

            # Automatically create ClientAccess if default_client_id is provided
            if user_data.get("default_client_id"):
                try:
                    default_client_access = ClientAccess(
                        user_profile_id=user_id,
                        client_account_id=user_data["default_client_id"],
                        access_level=access_level,
                        permissions=self._get_default_permissions(access_level),
                        granted_by=admin_user_uuid,
                        is_active=True,
                    )
                    self.db.add(default_client_access)
                    logger.info(
                        f"Created ClientAccess for user {user_id} to default client {user_data['default_client_id']}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create default client access: {e}")

            # Automatically create EngagementAccess if default_engagement_id is provided
            if user_data.get("default_engagement_id"):
                try:
                    default_engagement_access = EngagementAccess(
                        user_profile_id=user_id,
                        engagement_id=user_data["default_engagement_id"],
                        access_level=access_level,
                        engagement_role=user_data.get("role_name", "Analyst"),
                        permissions=self._get_default_permissions(access_level),
                        granted_by=admin_user_uuid,
                        is_active=True,
                    )
                    self.db.add(default_engagement_access)
                    logger.info(
                        f"Created EngagementAccess for user {user_id} to default engagement "
                        f"{user_data['default_engagement_id']}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to create default engagement access: {e}")

            # Create additional client access if specified
            client_accesses = user_data.get("client_access", [])
            created_access_count = 0

            for client_access_data in client_accesses:
                try:
                    # Skip if this is the same as default_client_id to avoid duplicates
                    if (
                        user_data.get("default_client_id")
                        and client_access_data["client_id"]
                        == user_data["default_client_id"]
                    ):
                        continue

                    client_access = ClientAccess(
                        user_profile_id=user_id,
                        client_account_id=client_access_data["client_id"],
                        access_level=access_level,
                        permissions=client_access_data.get(
                            "permissions", self._get_default_permissions(access_level)
                        ),
                        granted_by=admin_user_uuid,  # Use UUID or None
                        notes=client_access_data.get("notes", "Admin created access"),
                    )
                    self.db.add(client_access)
                    created_access_count += 1
                except Exception as e:
                    logger.warning(f"Failed to create client access: {e}")
                    continue

            await self.db.commit()
            await self.db.refresh(user_profile)

            # Log the creation
            await self._log_access(
                user_id=str(admin_user_uuid),  # Use UUID instead of created_by string
                action_type="admin_create_user",
                result="success",
                reason=f"Admin created user {user_id}",
                details={
                    "created_user": user_id,
                    "access_level": access_level,
                    "client_access_count": created_access_count,
                    "organization": user_data.get("organization", ""),
                },
            )

            return {
                "status": "success",
                "message": "User created successfully by admin",
                "user_profile_id": str(user_profile.user_id),
                "approval_status": "active",
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in admin_create_user: {e}")
            return {"status": "error", "message": f"User creation failed: {str(e)}"}

    async def get_admin_dashboard_stats(self, admin_user_id: str) -> Dict[str, Any]:
        """Get admin dashboard statistics."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            # Get user counts by status
            from sqlalchemy import func

            # Count users by status
            status_query = select(
                UserProfile.status, func.count(UserProfile.user_id)
            ).group_by(UserProfile.status)
            status_result = await self.db.execute(status_query)
            status_counts = dict(status_result.fetchall())

            # Count total client accesses
            access_query = select(func.count(ClientAccess.id)).where(
                ClientAccess.is_active is True
            )
            access_result = await self.db.execute(access_query)
            total_accesses = access_result.scalar() or 0

            # Count total roles
            role_query = select(func.count(UserRole.id)).where(
                UserRole.is_active is True
            )
            role_result = await self.db.execute(role_query)
            total_roles = role_result.scalar() or 0

            stats = {
                "user_counts": {
                    "active": status_counts.get(UserStatus.ACTIVE, 0),
                    "pending": status_counts.get(UserStatus.PENDING_APPROVAL, 0),
                    "rejected": status_counts.get(UserStatus.REJECTED, 0),
                    "inactive": status_counts.get(UserStatus.INACTIVE, 0),
                },
                "total_users": sum(status_counts.values()),
                "total_client_accesses": total_accesses,
                "total_roles": total_roles,
            }

            # Log the access
            await self._log_access(
                user_id=admin_user_id,
                action_type="view_admin_stats",
                result="success",
                reason="Viewed admin dashboard statistics",
            )

            return {"status": "success", "stats": stats}

        except Exception as e:
            logger.error(f"Error in get_admin_dashboard_stats: {e}")
            return {"status": "error", "message": f"Failed to get stats: {str(e)}"}

    async def bulk_user_operation(
        self,
        operation: str,
        user_ids: List[str],
        admin_user_id: str,
        operation_data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Perform bulk operations on multiple users."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}

        try:
            results = []
            success_count = 0
            error_count = 0

            for user_id in user_ids:
                try:
                    if operation == "approve":
                        # Use the user management handler for approval
                        from .user_management_handler import UserManagementHandler

                        user_mgmt = UserManagementHandler(self.db)
                        result = await user_mgmt.approve_user(
                            user_id, admin_user_id, operation_data or {}
                        )
                    elif operation == "reject":
                        from .user_management_handler import UserManagementHandler

                        user_mgmt = UserManagementHandler(self.db)
                        result = await user_mgmt.reject_user(
                            user_id,
                            admin_user_id,
                            operation_data.get("reason", "Bulk rejection"),
                        )
                    elif operation == "deactivate":
                        from .user_management_handler import UserManagementHandler

                        user_mgmt = UserManagementHandler(self.db)
                        result = await user_mgmt.deactivate_user(
                            user_id,
                            admin_user_id,
                            operation_data.get("reason", "Bulk deactivation"),
                        )
                    else:
                        result = {
                            "status": "error",
                            "message": f"Unknown operation: {operation}",
                        }

                    results.append({"user_id": user_id, "result": result})

                    if result.get("status") == "success":
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    results.append(
                        {
                            "user_id": user_id,
                            "result": {"status": "error", "message": str(e)},
                        }
                    )
                    error_count += 1

            # Log the bulk operation
            await self._log_access(
                user_id=admin_user_id,
                action_type=f"bulk_{operation}",
                result="success" if error_count == 0 else "partial",
                reason=f"Bulk {operation} on {len(user_ids)} users",
                details={
                    "operation": operation,
                    "total_users": len(user_ids),
                    "success_count": success_count,
                    "error_count": error_count,
                },
            )

            return {
                "status": "success",
                "message": f"Bulk {operation} completed",
                "total_processed": len(user_ids),
                "success_count": success_count,
                "error_count": error_count,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Error in bulk_user_operation: {e}")
            return {"status": "error", "message": f"Bulk operation failed: {str(e)}"}
