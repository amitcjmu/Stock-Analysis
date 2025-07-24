import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

# Add audit logging
audit_logger = logging.getLogger("security_audit")


class UserApprovalHandler:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _log_security_event(
        self,
        event_type: str,
        user_id: str,
        target_user_id: str = None,
        details: Dict[str, Any] = None,
    ):
        """Log security-sensitive events for audit trail."""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "actor_user_id": user_id,
            "target_user_id": target_user_id,
            "details": details or {},
            "ip_address": getattr(self, "_current_ip", "unknown"),
            "user_agent": getattr(self, "_current_user_agent", "unknown"),
        }

        audit_logger.warning(f"SECURITY_EVENT: {event_type} - {audit_entry}")

        # Store in database if audit table exists
        try:
            from app.models.audit import SecurityAuditLog

            audit_log = SecurityAuditLog(**audit_entry)
            self.db.add(audit_log)
            await self.db.commit()
        except Exception as e:
            # Don't fail the operation if audit logging fails
            audit_logger.error(f"Failed to store audit log: {e}")

    async def _validate_role_change_permissions(
        self, actor_user_id: str, target_role: str
    ) -> bool:
        """Validate that the actor can assign the target role."""
        from app.models.rbac import UserRole
        from sqlalchemy import and_, select

        # Get actor's current roles
        actor_roles_query = select(UserRole).where(
            and_(UserRole.user_id == actor_user_id, UserRole.is_active is True)
        )
        actor_roles_result = await self.db.execute(actor_roles_query)
        actor_roles = actor_roles_result.scalars().all()

        # Only platform admins can create other platform admins
        if target_role == "platform_admin":
            is_platform_admin = any(
                role.role_type == "platform_admin" for role in actor_roles
            )
            if not is_platform_admin:
                await self._log_security_event(
                    "UNAUTHORIZED_PLATFORM_ADMIN_CREATION_ATTEMPT",
                    actor_user_id,
                    details={"attempted_role": target_role},
                )
                return False

        return True


# Create router for the handler
from fastapi import APIRouter

router = APIRouter(prefix="/admin/user-approval", tags=["admin", "user-approval"])
