"""
User Management Handlers
Handles user registration, approvals, profile management, and user status operations.
"""

import logging
from typing import Any, Dict

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.models.client_account import User
from app.schemas.auth_schemas import (
    AccessValidationRequest,
    AccessValidationResponse,
    ClientAccessGrant,
    ClientAccessGrantResponse,
    FilterParams,
    PaginationParams,
    PendingApprovalsResponse,
    UserApprovalRequest,
    UserApprovalResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
    UserRejectionRequest,
    UserRejectionResponse,
)
from app.services.auth_services.user_management_service import UserManagementService
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Create user management router
user_management_router = APIRouter()


@user_management_router.post("/register", response_model=UserRegistrationResponse)
async def register_user(
    registration_request: UserRegistrationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user with pending approval status.
    Creates user profile requiring admin approval before access is granted.
    """
    try:
        # Extract additional request information
        request_data = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }

        user_service = UserManagementService(db)
        return await user_service.register_user_request(
            registration_request, request_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@user_management_router.get("/registration-status/{user_id}")
async def get_registration_status(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get registration status for a user."""
    try:
        user_service = UserManagementService(db)
        return await user_service.get_registration_status(user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_registration_status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@user_management_router.get(
    "/pending-approvals", response_model=PendingApprovalsResponse
)
async def get_pending_approvals(
    pagination: PaginationParams = Depends(),
    filters: FilterParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get list of users pending approval.
    Requires admin privileges.
    """
    try:
        # Use authenticated user from dependency injection
        user_id_str = str(current_user.id)

        user_service = UserManagementService(db)
        return await user_service.get_pending_approvals(
            user_id_str, pagination, filters
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_pending_approvals: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get pending approvals: {str(e)}"
        )


@user_management_router.post("/approve-user", response_model=UserApprovalResponse)
async def approve_user(
    approval_request: UserApprovalRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve a pending user registration.
    Requires admin privileges.
    """
    try:
        # Use authenticated user from dependency injection
        approved_by = str(current_user.id)

        approval_data = approval_request.dict()
        approval_data.update(
            {
                "approved_by_ip": request.client.host if request.client else None,
                "approved_by_user_agent": request.headers.get("User-Agent"),
            }
        )

        user_service = UserManagementService(db)
        return await user_service.approve_user(
            approval_request, approved_by, approval_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in approve_user: {e}")
        raise HTTPException(status_code=500, detail=f"User approval failed: {str(e)}")


@user_management_router.post("/reject-user", response_model=UserRejectionResponse)
async def reject_user(
    rejection_request: UserRejectionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reject a pending user registration.
    Requires admin privileges.
    """
    try:
        # Use authenticated user from dependency injection
        rejected_by = str(current_user.id)

        user_service = UserManagementService(db)
        return await user_service.reject_user(rejection_request, rejected_by)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reject_user: {e}")
        raise HTTPException(status_code=500, detail=f"User rejection failed: {str(e)}")


@user_management_router.post(
    "/validate-access", response_model=AccessValidationResponse
)
async def validate_user_access(
    validation_request: AccessValidationRequest, db: AsyncSession = Depends(get_db)
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
        raise HTTPException(
            status_code=500, detail=f"Access validation failed: {str(e)}"
        )


@user_management_router.post(
    "/grant-client-access", response_model=ClientAccessGrantResponse
)
async def grant_client_access(
    access_grant: ClientAccessGrant,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Grant client access to a user.
    Requires admin privileges.
    """
    try:
        # Use authenticated user from dependency injection
        granted_by = str(current_user.id)

        request_data = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }

        user_service = UserManagementService(db)
        return await user_service.grant_client_access(
            access_grant, granted_by, request_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in grant_client_access: {e}")
        raise HTTPException(
            status_code=500, detail=f"Client access grant failed: {str(e)}"
        )


@user_management_router.get("/user-profile/{user_id}")
async def get_user_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get user profile information."""
    try:
        user_service = UserManagementService(db)
        return await user_service.get_user_profile(user_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_user_profile: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get user profile: {str(e)}"
        )


@user_management_router.put("/user-profile/{user_id}")
async def update_user_profile(
    user_id: str, profile_updates: Dict[str, Any], db: AsyncSession = Depends(get_db)
):
    """Update user profile information."""
    try:
        user_service = UserManagementService(db)
        return await user_service.update_user_profile(user_id, profile_updates)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_user_profile: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update user profile: {str(e)}"
        )


@user_management_router.post("/deactivate-user")
async def deactivate_user(
    request_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate a user account."""
    try:
        # Use authenticated user from dependency injection
        deactivated_by = str(current_user.id)

        user_service = UserManagementService(db)
        return await user_service.deactivate_user(request_data, deactivated_by)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in deactivate_user: {e}")
        raise HTTPException(
            status_code=500, detail=f"User deactivation failed: {str(e)}"
        )


@user_management_router.post("/activate-user")
async def activate_user(
    request_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a user account."""
    try:
        # Use authenticated user from dependency injection
        activated_by = str(current_user.id)

        user_service = UserManagementService(db)
        return await user_service.activate_user(request_data, activated_by)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in activate_user: {e}")
        raise HTTPException(status_code=500, detail=f"User activation failed: {str(e)}")
