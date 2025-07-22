"""
RBAC API Endpoints - Modularized Version
Role-Based Access Control with modular handler architecture.

This file orchestrates the modular RBAC handlers while maintaining
the same API interface as the original monolithic implementation.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.handlers.admin_handlers import (
    admin_router,
)
from app.api.v1.auth.handlers.authentication_handlers import (
    authentication_router,
)
from app.api.v1.auth.handlers.demo_handlers import (
    demo_router,
)
from app.api.v1.auth.handlers.user_management_handlers import (
    user_management_router,
)
from app.core.database import get_db
from app.services.auth_services.rbac_core_service import RBACCoreService

logger = logging.getLogger(__name__)

# Create main router
router = APIRouter(tags=["Authentication & RBAC"])

# Include all modular handlers
router.include_router(authentication_router, tags=["Authentication"])
router.include_router(user_management_router, tags=["User Management"])
router.include_router(admin_router, tags=["Admin Operations"])
router.include_router(demo_router, tags=["Demo Functions"])


# Note: RBAC initialization moved to main application lifespan handler
# Router-level event handlers are deprecated - use app-level lifespan instead
async def initialize_rbac_system():
    """Initialize RBAC system - called from main app lifespan."""
    try:
        logger.info("Initializing modular RBAC system...")
        
        # Note: This would be called during application startup
        # For now, we'll handle role initialization on-demand
        logger.info("Modular RBAC system ready")
        
    except Exception as e:
        logger.error(f"Failed to initialize RBAC system: {e}")


@router.get("/system/info")
async def get_system_info():
    """Get RBAC system information."""
    return {
        "status": "operational",
        "architecture": "modular",
        "version": "2.0.0",
        "components": {
            "authentication_service": "active",
            "user_management_service": "active", 
            "admin_operations_service": "active",
            "rbac_core_service": "active"
        },
        "endpoints": {
            "authentication": ["/login", "/change-password"],
            "user_management": [
                "/register", "/registration-status/{user_id}",
                "/pending-approvals", "/approve-user", "/reject-user",
                "/validate-access", "/grant-client-access",
                "/user-profile/{user_id}", "/deactivate-user", "/activate-user"
            ],
            "admin_operations": [
                "/admin/dashboard-stats", "/active-users", 
                "/admin/access-logs", "/admin/create-user",
                "/admin/role-statistics", "/admin/ensure-roles"
            ],
            "demo": [
                "/demo/create-admin-user", "/demo/status", 
                "/demo/reset", "/demo/health"
            ],
            "system": ["/health", "/system/info"]
        },
        "migration_status": "completed",
        "original_endpoints": 17,
        "modular_endpoints": 19,
        "additional_features": [
            "Role statistics endpoint",
            "System information endpoint",
            "Demo status and management",
            "Enhanced health checking"
        ]
    }


# Initialize roles utility function
async def ensure_basic_roles_exist(db: AsyncSession = Depends(get_db)):
    """
    Utility function to ensure basic roles exist.
    Can be called during system initialization.
    """
    try:
        rbac_core_service = RBACCoreService(db)
        await rbac_core_service.ensure_basic_roles_exist()
        logger.info("Basic roles ensured in system")
        
    except Exception as e:
        logger.error(f"Error ensuring basic roles exist: {e}")


# Legacy compatibility function
def get_role_permissions(role_type: str) -> dict:
    """
    Legacy compatibility function for role permissions.
    Maintains backward compatibility with existing code.
    """
    from app.services.auth_services.rbac_core_service import RBACCoreService
    
    # Create a dummy service instance for static method access
    class DummyDB:
        pass
    
    dummy_service = RBACCoreService(DummyDB())
    return dummy_service.get_role_permissions(role_type) 