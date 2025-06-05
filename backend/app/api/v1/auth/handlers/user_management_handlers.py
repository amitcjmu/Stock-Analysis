"""
User Management Handlers
Handles user registration, approvals, profile management, and user status operations.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context
from app.schemas.auth_schemas import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserApprovalRequest, UserApprovalResponse,
    UserRejectionRequest, UserRejectionResponse,
    PendingApprovalsResponse, AccessValidationRequest, AccessValidationResponse,
    ClientAccessGrant, ClientAccessGrantResponse,
    PaginationParams, FilterParams
)
from app.services.auth_services.user_management_service import UserManagementService

logger = logging.getLogger(__name__)

# Create user management router
user_management_router = APIRouter()


@user_management_router.post("/register", response_model=UserRegistrationResponse)
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
        # Extract additional request information
        request_data = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }
        
        user_service = UserManagementService(db)
        return await user_service.register_user_request(registration_request, request_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@user_management_router.get("/registration-status/{user_id}")
async def get_registration_status(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the registration/approval status of a user."""
    try:
        user_service = UserManagementService(db)
        return await user_service.get_registration_status(user_id)
        
    except Exception as e:
        logger.error(f"Error in get_registration_status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@user_management_router.get("/pending-approvals", response_model=PendingApprovalsResponse)
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
        
        # Get user ID from context, with fallback for demo purposes
        user_id_str = context.user_id or "admin_user"
        
        user_service = UserManagementService(db)
        return await user_service.get_pending_approvals(user_id_str, pagination, filters)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_pending_approvals: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pending approvals: {str(e)}")


@user_management_router.post("/approve-user", response_model=UserApprovalResponse)
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
        
        # For demo purposes, use a default admin user ID
        approved_by = context.user_id or "admin_user"
        
        approval_data = approval_request.dict()
        approval_data.update({
            "approved_by_ip": request.client.host if request.client else None,
            "approved_by_user_agent": request.headers.get("User-Agent")
        })
        
        user_service = UserManagementService(db)
        return await user_service.approve_user(approval_request, approved_by, approval_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in approve_user: {e}")
        raise HTTPException(status_code=500, detail=f"User approval failed: {str(e)}")


@user_management_router.post("/reject-user", response_model=UserRejectionResponse)
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
        
        # For demo purposes, use a default admin user ID
        rejected_by = context.user_id or "admin_user"
        
        user_service = UserManagementService(db)
        return await user_service.reject_user(rejection_request, rejected_by)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reject_user: {e}")
        raise HTTPException(status_code=500, detail=f"User rejection failed: {str(e)}")


@user_management_router.post("/validate-access", response_model=AccessValidationResponse)
async def validate_user_access(
    validation_request: AccessValidationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate user access permissions.
    """
    try:
        user_service = UserManagementService(db)
        return await user_service.validate_user_access(validation_request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in validate_user_access: {e}")
        raise HTTPException(status_code=500, detail=f"Access validation failed: {str(e)}")


@user_management_router.post("/grant-client-access", response_model=ClientAccessGrantResponse)
async def grant_client_access(
    access_grant: ClientAccessGrant,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Grant client access to a user.
    Requires admin privileges.
    """
    try:
        context = get_current_context()
        
        # For demo purposes, use a default admin user ID
        granted_by = context.user_id or "admin_user"
        
        request_data = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent")
        }
        
        user_service = UserManagementService(db)
        return await user_service.grant_client_access(access_grant, granted_by, request_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in grant_client_access: {e}")
        raise HTTPException(status_code=500, detail=f"Client access grant failed: {str(e)}")


@user_management_router.get("/user-profile/{user_id}")
async def get_user_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user profile information."""
    try:
        user_service = UserManagementService(db)
        return await user_service.get_user_profile(user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")


@user_management_router.put("/user-profile/{user_id}")
async def update_user_profile(
    user_id: str,
    profile_updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Update user profile information."""
    try:
        user_service = UserManagementService(db)
        return await user_service.update_user_profile(user_id, profile_updates)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_user_profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")


@user_management_router.post("/deactivate-user")
async def deactivate_user(
    request_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a user account."""
    try:
        context = get_current_context()
        
        # Get the user performing the deactivation
        deactivated_by = context.user_id or "admin_user"
        
        user_service = UserManagementService(db)
        return await user_service.deactivate_user(request_data, deactivated_by)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in deactivate_user: {e}")
        raise HTTPException(status_code=500, detail=f"User deactivation failed: {str(e)}")


@user_management_router.post("/activate-user")
async def activate_user(
    request_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Activate a user account."""
    try:
        context = get_current_context()
        
        # Get the user performing the activation
        activated_by = context.user_id or "admin_user"
        
        user_service = UserManagementService(db)
        return await user_service.activate_user(request_data, activated_by)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in activate_user: {e}")
        raise HTTPException(status_code=500, detail=f"User activation failed: {str(e)}") 