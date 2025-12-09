"""
Command methods for Enhanced RBAC Service - write operations for user profiles and roles.
"""

from typing import Any, Dict

from .base import DataScope, EnhancedUserProfile, RoleLevel, UserStatus, logger


class RBACCommands:
    """Command methods for RBAC write operations."""

    async def create_user_profile(
        self,
        user_id: str,
        role_level: RoleLevel,
        data_scope: DataScope,
        scope_client_account_id: str = None,
        scope_engagement_id: str = None,
        **additional_data,
    ) -> Dict[str, Any]:
        """Create a new enhanced user profile with proper role and scope assignment."""
        if not self.is_available:
            return {"status": "error", "message": "Enhanced RBAC not available"}

        try:
            # Validate scope assignment
            validation_result = self._validate_scope_assignment(
                role_level, data_scope, scope_client_account_id, scope_engagement_id
            )

            if validation_result["status"] == "error":
                return validation_result

            # Create user profile
            user_profile = EnhancedUserProfile(
                user_id=user_id,
                role_level=role_level,
                data_scope=data_scope,
                scope_client_account_id=scope_client_account_id,
                scope_engagement_id=scope_engagement_id,
                status=UserStatus.PENDING_APPROVAL,
                **additional_data,
            )

            self.db.add(user_profile)
            await self.db.commit()
            await self.db.refresh(user_profile)

            # Log the creation
            await self._log_access(
                user_id=user_id,
                action_type="user_profile_created",
                result="success",
                details={
                    "role_level": role_level,
                    "data_scope": data_scope,
                    "scope_client_account_id": scope_client_account_id,
                    "scope_engagement_id": scope_engagement_id,
                },
            )

            return {
                "status": "success",
                "message": "User profile created successfully",
                "user_profile": user_profile,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user profile: {e}")
            return {
                "status": "error",
                "message": f"Failed to create user profile: {str(e)}",
            }

    async def _log_access(self, **kwargs):
        """Log access attempt to audit log."""
        if not self.is_available:
            return

        try:
            from .base import AccessAuditLog

            audit_log = AccessAuditLog(**kwargs)
            self.db.add(audit_log)
            await self.db.commit()
        except Exception as e:
            # Log warning instead of error - audit failure shouldn't block operations
            logger.warning(
                f"Failed to log access audit (table may not exist): {str(e)}"
            )
            await self.db.rollback()
