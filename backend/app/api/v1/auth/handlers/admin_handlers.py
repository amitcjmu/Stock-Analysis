"""
Admin Handlers  
Handles admin dashboard stats, active users, access logs, admin user creation, and health checks.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context
from app.schemas.auth_schemas import UserRegistrationResponse
from app.services.auth_services.admin_operations_service import AdminOperationsService
from app.services.auth_services.rbac_core_service import RBACCoreService

logger = logging.getLogger(__name__)

# Create admin router
admin_router = APIRouter()


@admin_router.get("/admin/dashboard-stats")
async def get_admin_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics."""
    try:
        context = get_current_context()
        
        # Get user ID from context, with fallback for demo purposes
        user_id_str = context.user_id or "admin_user"
        
        admin_service = AdminOperationsService(db)
        return await admin_service.get_admin_dashboard_stats(user_id_str)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_admin_dashboard_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")


@admin_router.get("/active-users")
async def get_active_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get active users for admin management."""
    try:
        context = get_current_context()
        
        # Get user ID from context, with fallback for demo purposes
        user_id_str = context.user_id or "admin_user"
        
        admin_service = AdminOperationsService(db)
        return await admin_service.get_active_users(user_id_str, page, page_size)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_active_users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active users: {str(e)}")


@admin_router.get("/admin/access-logs")
async def get_access_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get access audit logs."""
    try:
        context = get_current_context()
        
        user_id_str = context.user_id or "admin_user"
        
        admin_service = AdminOperationsService(db)
        return await admin_service.get_access_logs(user_id_str, page, page_size, user_id, action_type)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_access_logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get access logs: {str(e)}")


@admin_router.post("/admin/create-user", response_model=UserRegistrationResponse)
async def admin_create_user(
    user_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to create users directly.
    Bypasses normal registration flow with instant approval.
    """
    try:
        context = get_current_context()
        
        # Get the admin user creating this user
        created_by = context.user_id or "admin_user"
        
        request_data = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }
        
        admin_service = AdminOperationsService(db)
        return await admin_service.admin_create_user(user_data, created_by, request_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in admin_create_user: {e}")
        raise HTTPException(status_code=500, detail=f"Admin user creation failed: {str(e)}")


@admin_router.get("/health")
async def rbac_health_check(
    db: AsyncSession = Depends(get_db)
):
    """Health check for RBAC system."""
    try:
        admin_service = AdminOperationsService(db)
        return await admin_service.health_check()
        
    except Exception as e:
        logger.error(f"Error in rbac_health_check: {e}")
        return {
            "status": "unhealthy",
            "service": "RBAC Authentication System",
            "error": str(e)
        }


@admin_router.get("/admin/role-statistics")
async def get_role_statistics(
    db: AsyncSession = Depends(get_db)
):
    """Get role distribution statistics."""
    try:
        context = get_current_context()
        user_id_str = context.user_id or "admin_user"
        
        # Check admin access first
        admin_service = AdminOperationsService(db)
        stats_check = await admin_service.get_admin_dashboard_stats(user_id_str)
        
        if stats_check.get("status") != "success":
            raise HTTPException(status_code=403, detail="Access denied: Admin privileges required")
        
        rbac_core_service = RBACCoreService(db)
        return await rbac_core_service.get_role_statistics()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_role_statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get role statistics: {str(e)}")


@admin_router.post("/admin/ensure-roles")
async def ensure_basic_roles(
    db: AsyncSession = Depends(get_db)
):
    """Ensure basic system roles exist."""
    try:
        context = get_current_context()
        user_id_str = context.user_id or "admin_user"
        
        # Check admin access first
        admin_service = AdminOperationsService(db)
        stats_check = await admin_service.get_admin_dashboard_stats(user_id_str)
        
        if stats_check.get("status") != "success":
            raise HTTPException(status_code=403, detail="Access denied: Admin privileges required")
        
        rbac_core_service = RBACCoreService(db)
        await rbac_core_service.ensure_basic_roles_exist()
        
        return {
            "status": "success",
            "message": "Basic roles ensured in system"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ensure_basic_roles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to ensure basic roles: {str(e)}")


@admin_router.get("/user-type")
async def get_user_type(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get user type information for access control."""
    try:
        context = get_current_context()
        user_id_str = context.user_id or "admin_user"
        
        # Check if user is demo admin
        is_demo_admin = user_id_str in ["admin_user", "demo_user"]
        
        # For real users, check if they have demo/mock flag
        is_mock_user = False
        if not is_demo_admin and user_id_str:
            try:
                from sqlalchemy import select
                from app.models.rbac import User
                
                # Check if user has is_mock flag
                query = select(User).where(User.id == user_id_str)
                result = await db.execute(query)
                user = result.scalar_one_or_none()
                
                if user:
                    is_mock_user = getattr(user, 'is_mock', False)
                    
            except Exception as e:
                logger.warning(f"Could not check user mock status: {e}")
        
        return {
            "status": "success",
            "user_type": {
                "user_id": user_id_str,
                "is_demo_admin": is_demo_admin,
                "is_mock_user": is_mock_user,
                "should_see_mock_data_only": is_demo_admin or is_mock_user,
                "access_level": "demo" if (is_demo_admin or is_mock_user) else "production"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_type: {e}")
        return {
            "status": "success",
            "user_type": {
                "user_id": "unknown",
                "is_demo_admin": True,  # Default to demo for safety
                "is_mock_user": False,
                "should_see_mock_data_only": True,
                "access_level": "demo"
            }
        } 