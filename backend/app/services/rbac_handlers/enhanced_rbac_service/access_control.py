"""
Access control and permission checking for Enhanced RBAC Service.
"""

from typing import Any, Dict

from .base import logger


class RBACAccessControl:
    """Access control and permission checking methods."""

    async def check_access_permission(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str = None,
        client_account_id: str = None,
        engagement_id: str = None,
        action: str = "read",
    ) -> Dict[str, Any]:
        """
        Check if user has permission to access a specific resource.
        Implements hierarchical access control with proper scoping.
        """
        if not self.is_available:
            return {
                "allowed": True,
                "reason": "Enhanced RBAC not available - allowing access",
            }

        try:
            # Get user profile
            user_profile = await self.get_user_profile(user_id)
            if not user_profile:
                await self._log_access(
                    user_id=user_id,
                    action_type=f"access_denied_{resource_type}",
                    result="denied",
                    reason="User profile not found",
                    resource_type=resource_type,
                    resource_id=resource_id,
                )
                return {"allowed": False, "reason": "User profile not found"}

            # Check if user is active
            if not user_profile.is_active:
                await self._log_access(
                    user_id=user_id,
                    action_type=f"access_denied_{resource_type}",
                    result="denied",
                    reason="User account inactive or deleted",
                    resource_type=resource_type,
                    resource_id=resource_id,
                )
                return {"allowed": False, "reason": "User account inactive"}

            # Platform admins have access to everything
            if user_profile.is_platform_admin:
                await self._log_access(
                    user_id=user_id,
                    action_type=f"access_granted_{resource_type}",
                    result="success",
                    reason="Platform admin access",
                    resource_type=resource_type,
                    resource_id=resource_id,
                )
                return {"allowed": True, "reason": "Platform admin access"}

            # Check specific resource access based on scope
            access_result = await self._check_resource_access(
                user_profile,
                resource_type,
                resource_id,
                client_account_id,
                engagement_id,
                action,
            )

            # Log the access attempt
            await self._log_access(
                user_id=user_id,
                action_type=f"access_{'granted' if access_result['allowed'] else 'denied'}_{resource_type}",
                result="success" if access_result["allowed"] else "denied",
                reason=access_result["reason"],
                resource_type=resource_type,
                resource_id=resource_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_role_level=user_profile.role_level,
                user_data_scope=user_profile.data_scope,
            )

            return access_result

        except Exception as e:
            logger.error(f"Error checking access permission: {e}")
            return {"allowed": False, "reason": f"Permission check failed: {str(e)}"}
