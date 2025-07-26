"""
Admin Handlers
Handles admin dashboard stats, active users, access logs, admin user creation, and health checks.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models.client_account import User
from app.schemas.auth_schemas import UserRegistrationResponse
from app.services.auth_services.admin_operations_service import AdminOperationsService
from app.services.auth_services.rbac_core_service import RBACCoreService
from app.services.auth_services.user_management_service import UserManagementService

logger = logging.getLogger(__name__)

# Removed hardcoded demo admin UUID for security

# Create admin router
admin_router = APIRouter()


@admin_router.get("/admin/dashboard-stats")
async def get_admin_dashboard_stats(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get admin dashboard statistics."""
    try:
        # Use authenticated user from dependency injection
        user_id_str = str(current_user.id)

        admin_service = AdminOperationsService(db)
        return await admin_service.get_admin_dashboard_stats(user_id_str)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_admin_dashboard_stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get dashboard stats: {str(e)}"
        )


@admin_router.get("/active-users")
async def get_active_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get active users for admin management."""
    try:
        # Use authenticated user from dependency injection
        user_id_str = str(current_user.id)

        admin_service = AdminOperationsService(db)
        return await admin_service.get_active_users(user_id_str, page, page_size)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_active_users: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get active users: {str(e)}"
        )


@admin_router.put("/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    user_updates: Dict[str, Any] = Body(...),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin endpoint to update user details including default client and engagement assignments.
    Requires admin privileges.
    """
    try:
        # Use authenticated user from dependency injection
        updated_by = str(current_user.id)

        # Check admin access first
        admin_service = AdminOperationsService(db)
        try:
            # This will raise 403 if user doesn't have admin access
            await admin_service.get_admin_dashboard_stats(updated_by)
        except HTTPException as e:
            if e.status_code == 403:
                raise
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to verify admin access: {str(e)}"
                )

        # Use user management service to update the user
        user_service = UserManagementService(db)
        result = await user_service.update_user_profile(user_id, user_updates)

        logger.info(f"User {user_id} updated by admin {updated_by}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin_update_user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@admin_router.get("/admin/access-logs")
async def get_access_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get access audit logs."""
    try:
        # Use authenticated user from dependency injection
        user_id_str = str(current_user.id)

        admin_service = AdminOperationsService(db)
        return await admin_service.get_access_logs(
            user_id_str, page, page_size, user_id, action_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_access_logs: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get access logs: {str(e)}"
        )


@admin_router.post("/admin/create-user", response_model=UserRegistrationResponse)
async def admin_create_user(
    user_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin endpoint to create users directly.
    Bypasses normal registration flow with instant approval.
    """
    try:
        # Use authenticated user from dependency injection
        created_by = str(current_user.id)

        request_data = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }

        admin_service = AdminOperationsService(db)
        return await admin_service.admin_create_user(
            user_data, created_by, request_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin_create_user: {e}")
        raise HTTPException(
            status_code=500, detail=f"Admin user creation failed: {str(e)}"
        )


@admin_router.get("/health")
async def rbac_health_check(db: AsyncSession = Depends(get_db)):
    """Health check for RBAC system."""
    try:
        admin_service = AdminOperationsService(db)
        return await admin_service.health_check()

    except Exception as e:
        logger.error(f"Error in rbac_health_check: {e}")
        return {
            "status": "unhealthy",
            "service": "RBAC Authentication System",
            "error": str(e),
        }


@admin_router.get("/admin/role-statistics")
async def get_role_statistics(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get role distribution statistics."""
    try:
        # Use authenticated user from dependency injection
        user_id_str = str(current_user.id)

        # Check admin access first
        admin_service = AdminOperationsService(db)
        try:
            # This will raise 403 if user doesn't have admin access
            await admin_service.get_admin_dashboard_stats(user_id_str)
        except HTTPException as e:
            if e.status_code == 403:
                raise
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to verify admin access: {str(e)}"
                )

        rbac_core_service = RBACCoreService(db)
        return await rbac_core_service.get_role_statistics()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_role_statistics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get role statistics: {str(e)}"
        )


@admin_router.post("/admin/ensure-roles")
async def ensure_basic_roles(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Ensure basic system roles exist."""
    try:
        # Use authenticated user from dependency injection
        user_id_str = str(current_user.id)

        # Check admin access first
        admin_service = AdminOperationsService(db)
        try:
            # This will raise 403 if user doesn't have admin access
            await admin_service.get_admin_dashboard_stats(user_id_str)
        except HTTPException as e:
            if e.status_code == 403:
                raise
            else:
                raise HTTPException(
                    status_code=500, detail=f"Failed to verify admin access: {str(e)}"
                )

        rbac_core_service = RBACCoreService(db)
        await rbac_core_service.ensure_basic_roles_exist()

        return {"status": "success", "message": "Basic roles ensured in system"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ensure_basic_roles: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to ensure basic roles: {str(e)}"
        )


@admin_router.get("/user-type")
async def get_user_type(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get user type information for access control."""
    try:
        # Use authenticated user from dependency injection
        user_id_str = str(current_user.id)

        # Check if user has platform admin role (no more hardcoded demo admin)
        is_platform_admin = False
        try:
            from sqlalchemy import select

            from app.models.rbac import RoleType, UserRole

            # Check if user has platform admin role
            query = (
                select(UserRole)
                .where(UserRole.user_id == current_user.id)
                .where(UserRole.role_type == RoleType.PLATFORM_ADMIN)
            )
            result = await db.execute(query)
            platform_admin_role = result.scalar_one_or_none()

            is_platform_admin = platform_admin_role is not None

        except Exception as e:
            logger.warning(f"Could not check user platform admin status: {e}")

        return {
            "status": "success",
            "user_type": {
                "user_id": user_id_str,
                "is_platform_admin": is_platform_admin,
                "is_mock_user": False,  # No more mock users needed
                "should_see_mock_data_only": False,  # Platform admin sees real data
                "access_level": "platform_admin" if is_platform_admin else "user",
            },
        }

    except Exception as e:
        logger.error(f"Error in get_user_type: {e}")
        return {"status": "error", "message": f"Failed to get user type: {str(e)}"}
