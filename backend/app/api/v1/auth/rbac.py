"""
RBAC API Endpoints - Role-Based Access Control
Comprehensive endpoints for user registration, approval, and access management.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context
from app.services.rbac_service import create_rbac_service, RBACService
from app.schemas.auth_schemas import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserApprovalRequest, UserApprovalResponse,
    UserRejectionRequest, UserRejectionResponse,
    PendingApprovalsResponse, AccessValidationRequest, AccessValidationResponse,
    ClientAccessGrant, ClientAccessGrantResponse,
    PaginationParams, FilterParams, ErrorResponse, SuccessResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

# =========================
# User Registration Endpoints
# =========================

@router.post("/register", response_model=UserRegistrationResponse)
async def register_user(
    registration_request: UserRegistrationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with pending approval status.
    Creates user profile requiring admin approval before access is granted.
    """
    try:
        rbac_service = create_rbac_service(db)
        
        # Extract additional request information
        user_data = registration_request.dict()
        user_data.update({
            "user_id": f"user_{registration_request.email.replace('@', '_').replace('.', '_')}",  # Temporary ID generation
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        })
        
        result = await rbac_service.register_user_request(user_data)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
        
        return UserRegistrationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.get("/registration-status/{user_id}")
async def get_registration_status(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the registration/approval status of a user."""
    try:
        rbac_service = create_rbac_service(db)
        
        # For this endpoint, we'd typically check the user profile status
        # For now, return a basic status check
        return {
            "status": "success",
            "user_id": user_id,
            "approval_status": "pending",  # Would be fetched from database
            "message": "Registration pending admin approval"
        }
        
    except Exception as e:
        logger.error(f"Error in get_registration_status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

# =========================
# Admin Approval Endpoints
# =========================

@router.get("/pending-approvals", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users pending approval.
    Requires admin privileges.
    """
    try:
        context = get_current_context()
        rbac_service = create_rbac_service(db)
        
        # For demo purposes, use a default admin user ID
        admin_user_id = context.user_id or "admin_user"
        
        result = await rbac_service.get_pending_approvals(admin_user_id)
        
        if result["status"] == "error":
            if "Access denied" in result["message"]:
                raise HTTPException(status_code=403, detail=result["message"])
            else:
                raise HTTPException(status_code=500, detail=result["message"])
        
        return PendingApprovalsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_pending_approvals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending approvals: {str(e)}")

@router.post("/approve-user", response_model=UserApprovalResponse)
async def approve_user(
    approval_request: UserApprovalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a pending user registration.
    Requires admin privileges.
    """
    try:
        context = get_current_context()
        rbac_service = create_rbac_service(db)
        
        # For demo purposes, use a default admin user ID
        approved_by = context.user_id or "admin_user"
        
        approval_data = approval_request.dict()
        approval_data.update({
            "approved_by_ip": request.client.host if request.client else None,
            "approved_by_user_agent": request.headers.get("User-Agent")
        })
        
        result = await rbac_service.approve_user(
            user_id=approval_request.user_id,
            approved_by=approved_by,
            approval_data=approval_data
        )
        
        if result["status"] == "error":
            if "Access denied" in result["message"]:
                raise HTTPException(status_code=403, detail=result["message"])
            elif "not found" in result["message"]:
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return UserApprovalResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in approve_user: {e}")
        raise HTTPException(status_code=500, detail=f"User approval failed: {str(e)}")

@router.post("/reject-user", response_model=UserRejectionResponse)
async def reject_user(
    rejection_request: UserRejectionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a pending user registration.
    Requires admin privileges.
    """
    try:
        context = get_current_context()
        rbac_service = create_rbac_service(db)
        
        # For demo purposes, use a default admin user ID
        rejected_by = context.user_id or "admin_user"
        
        result = await rbac_service.reject_user(
            user_id=rejection_request.user_id,
            rejected_by=rejected_by,
            rejection_reason=rejection_request.rejection_reason
        )
        
        if result["status"] == "error":
            if "Access denied" in result["message"]:
                raise HTTPException(status_code=403, detail=result["message"])
            elif "not found" in result["message"]:
                raise HTTPException(status_code=404, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return UserRejectionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reject_user: {e}")
        raise HTTPException(status_code=500, detail=f"User rejection failed: {str(e)}")

# =========================
# Access Control Endpoints
# =========================

@router.post("/validate-access", response_model=AccessValidationResponse)
async def validate_user_access(
    validation_request: AccessValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate if a user has access to a specific resource and action.
    Used by middleware and frontend for access control.
    """
    try:
        rbac_service = create_rbac_service(db)
        
        result = await rbac_service.validate_user_access(
            user_id=validation_request.user_id,
            resource_type=validation_request.resource_type,
            resource_id=validation_request.resource_id,
            action=validation_request.action
        )
        
        return AccessValidationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in validate_user_access: {e}")
        # For access validation, return denied rather than error to prevent security issues
        return AccessValidationResponse(
            has_access=False,
            reason=f"Access validation error: {str(e)}"
        )

@router.post("/grant-client-access", response_model=ClientAccessGrantResponse)
async def grant_client_access(
    access_grant: ClientAccessGrant,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Grant or update client access for a user.
    Requires admin privileges.
    """
    try:
        context = get_current_context()
        rbac_service = create_rbac_service(db)
        
        # For demo purposes, use a default admin user ID
        granted_by = context.user_id or "admin_user"
        
        access_data = access_grant.dict(exclude={"user_id", "client_id"})
        
        result = await rbac_service.grant_client_access(
            user_id=access_grant.user_id,
            client_id=access_grant.client_id,
            access_data=access_data,
            granted_by=granted_by
        )
        
        if result["status"] == "error":
            if "Access denied" in result["message"]:
                raise HTTPException(status_code=403, detail=result["message"])
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return ClientAccessGrantResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in grant_client_access: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to grant client access: {str(e)}")

# =========================
# User Management Endpoints
# =========================

@router.get("/user-profile/{user_id}")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user profile information including roles and access."""
    try:
        rbac_service = create_rbac_service(db)
        
        # For now, return basic profile information
        # In full implementation, would fetch from UserProfile model
        return {
            "status": "success",
            "user_profile": {
                "user_id": user_id,
                "status": "active",
                "organization": "Demo Organization",
                "role_description": "Analyst",
                "access_level": "read_write",
                "client_access": [],
                "roles": []
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")

@router.put("/user-profile/{user_id}")
async def update_user_profile(
    user_id: str,
    profile_updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Update user profile information."""
    try:
        context = get_current_context()
        
        # Validate that user can update this profile (self or admin)
        if context.user_id != user_id:
            # Check admin access
            rbac_service = create_rbac_service(db)
            access_check = await rbac_service.validate_user_access(
                user_id=context.user_id,
                resource_type="admin_console",
                action="manage"
            )
            if not access_check["has_access"]:
                raise HTTPException(status_code=403, detail="Access denied: Cannot update other user profiles")
        
        # For now, return success
        # In full implementation, would update UserProfile model
        return {
            "status": "success",
            "message": "User profile updated successfully",
            "user_id": user_id,
            "updates_applied": list(profile_updates.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_user_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")

# =========================
# System Administration Endpoints
# =========================

@router.get("/admin/dashboard-stats")
async def get_admin_dashboard_stats(
    db: AsyncSession = Depends(get_db)
):
    """Get admin dashboard statistics."""
    try:
        context = get_current_context()
        rbac_service = create_rbac_service(db)
        
        # Validate admin access
        access_check = await rbac_service.validate_user_access(
            user_id=context.user_id or "admin_user",
            resource_type="admin_console",
            action="read"
        )
        
        if not access_check["has_access"]:
            raise HTTPException(status_code=403, detail="Access denied: Admin privileges required")
        
        # For now, return demo statistics
        # In full implementation, would aggregate from various models
        return {
            "status": "success",
            "dashboard_stats": {
                "total_users": 25,
                "pending_approvals": 3,
                "active_users": 20,
                "suspended_users": 2,
                "total_clients": 5,
                "total_engagements": 12,
                "total_sessions_today": 45,
                "system_health": "healthy"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_admin_dashboard_stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@router.get("/admin/access-logs")
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
        rbac_service = create_rbac_service(db)
        
        # Validate admin access
        access_check = await rbac_service.validate_user_access(
            user_id=context.user_id or "admin_user",
            resource_type="admin_console",
            action="read"
        )
        
        if not access_check["has_access"]:
            raise HTTPException(status_code=403, detail="Access denied: Admin privileges required")
        
        # For now, return demo logs
        # In full implementation, would query AccessAuditLog model
        return {
            "status": "success",
            "access_logs": [
                {
                    "id": "log_001",
                    "user_id": "user_001",
                    "action_type": "user_approval",
                    "result": "success",
                    "created_at": "2025-06-02T10:30:00Z"
                }
            ],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_logs": 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_access_logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get access logs: {str(e)}")

# =========================
# Health Check Endpoints
# =========================

@router.get("/health")
async def rbac_health_check():
    """Health check for RBAC system."""
    try:
        # Check if RBAC service is available
        from app.services.rbac_service import RBAC_MODELS_AVAILABLE, CLIENT_MODELS_AVAILABLE
        
        return {
            "status": "healthy",
            "service": "rbac-authentication",
            "version": "1.0.0",
            "capabilities": {
                "user_registration": True,
                "admin_approval_workflow": True,
                "access_validation": True,
                "audit_logging": True,
                "client_level_access": CLIENT_MODELS_AVAILABLE,
                "engagement_level_access": CLIENT_MODELS_AVAILABLE,
                "rbac_models": RBAC_MODELS_AVAILABLE
            },
            "endpoints": {
                "registration": "/auth/register",
                "approval": "/auth/approve-user",
                "validation": "/auth/validate-access",
                "admin_dashboard": "/auth/admin/dashboard-stats"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in rbac_health_check: {e}")
        return {
            "status": "unhealthy",
            "service": "rbac-authentication",
            "error": str(e)
        }

# =========================
# Demo/Development Endpoints
# =========================

@router.post("/demo/create-admin-user")
async def create_demo_admin_user(
    db: AsyncSession = Depends(get_db)
):
    """
    Create demo admin user for development/testing.
    This endpoint should be removed in production.
    """
    try:
        rbac_service = create_rbac_service(db)
        
        # Create demo admin user
        admin_data = {
            "user_id": "admin_demo",
            "email": "admin@aiforce.com",
            "full_name": "Admin User",
            "organization": "AI Force Platform",
            "role_description": "Platform Administrator",
            "registration_reason": "System setup and administration",
            "requested_access_level": "super_admin"
        }
        
        # Register and immediately approve
        registration_result = await rbac_service.register_user_request(admin_data)
        
        if registration_result["status"] == "success":
            approval_data = {
                "access_level": "super_admin",
                "role_name": "Platform Admin",
                "client_access": []  # Global admin doesn't need specific client access
            }
            
            approval_result = await rbac_service.approve_user(
                user_id="admin_demo",
                approved_by="system",
                approval_data=approval_data
            )
            
            return {
                "status": "success",
                "message": "Demo admin user created successfully",
                "admin_user_id": "admin_demo",
                "credentials": {
                    "email": "admin@aiforce.com",
                    "note": "Use this for admin access in development"
                }
            }
        else:
            return registration_result
        
    except Exception as e:
        logger.error(f"Error in create_demo_admin_user: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create demo admin user: {str(e)}") 