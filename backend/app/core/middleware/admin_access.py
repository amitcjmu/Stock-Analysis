"""
Admin access control and audit logging for middleware.
Handles admin endpoint protection and security audit logging.
"""

import logging
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from ..security.secure_logging import safe_log_format
from .auth_utils import extract_user_id, check_platform_admin

logger = logging.getLogger(__name__)


def is_admin_endpoint(path: str) -> bool:
    """Check if endpoint is admin-only and should allow context exemption for platform admins."""
    admin_paths = [
        "/api/v1/admin/",  # All admin CRUD operations (admin_handlers)
        "/api/v1/auth/admin/",  # Admin dashboard and management (auth router) - FIXED PREFIX
        "/api/v1/auth/user-profile/",  # User profile management - FIXED PREFIX
        "/api/v1/auth/pending-approvals",  # User approval management - FIXED PREFIX
        "/api/v1/auth/approve-user",  # User approval actions - FIXED PREFIX
        "/api/v1/auth/reject-user",  # User rejection actions - FIXED PREFIX
        "/api/v1/auth/active-users",  # Active user management (admin_handlers) - FIXED PATH
        "/admin/",  # All other admin routes (client/engagement management)
    ]
    return any(path.startswith(admin_path) for admin_path in admin_paths)


async def handle_admin_access(request: Request, path: str) -> Optional[JSONResponse]:
    """Handle admin endpoint access control."""
    user_id = extract_user_id(request)

    if not user_id:
        logger.warning(f"Unauthenticated access blocked for admin endpoint: {path}")
        return JSONResponse(
            status_code=401, content={"error": "Authentication required"}
        )

    if not await check_platform_admin(user_id):
        logger.warning(
            safe_log_format(
                "Non-admin access blocked for {path} by user {user_id}",
                path=path,
                user_id=user_id,
            )
        )
        return JSONResponse(status_code=403, content={"error": "Access denied"})

    # Log successful admin access
    logger.info(
        safe_log_format(
            "Admin exemption granted for {path} to user {user_id}",
            path=path,
            user_id=user_id,
        )
    )

    # Security audit logging
    await audit_admin_access(user_id, path, request)
    return None  # Access granted


async def audit_admin_access(user_id: str, path: str, request: Request):
    """Log admin access for security audit."""
    try:
        from app.core.database import AsyncSessionLocal
        from app.services.security_audit_service import SecurityAuditService

        async with AsyncSessionLocal() as audit_db:
            audit_service = SecurityAuditService(audit_db)
            await audit_service.log_admin_access(
                user_id=user_id,
                endpoint=path,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
    except Exception as audit_error:
        logger.warning(
            safe_log_format(
                "Failed to log admin access audit: {audit_error}",
                audit_error=audit_error,
            )
        )
