"""
User Management Service
Handles user registration, profile management, approval workflows, and user status operations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, text
from fastapi import HTTPException

from app.models.client_account import User
from app.models.rbac import UserProfile, UserRole
from app.schemas.auth_schemas import (
    UserRegistrationRequest, UserRegistrationResponse,
    UserApprovalRequest, UserApprovalResponse,
    UserRejectionRequest, UserRejectionResponse,
    PendingApprovalsResponse, AccessValidationRequest, AccessValidationResponse,
    ClientAccessGrant, ClientAccessGrantResponse,
    PaginationParams, FilterParams
)
from app.services.rbac_service import create_rbac_service

logger = logging.getLogger(__name__)


class UserManagementService:
    """Service for handling user management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register_user_request(self, registration_request: UserRegistrationRequest, request_data: Dict[str, Any]) -> UserRegistrationResponse:
        """
        Register a new user with pending approval status.
        Creates user profile requiring admin approval before access is granted.
        """
        try:
            rbac_service = create_rbac_service(self.db)
            
            # Extract additional request information
            user_data = registration_request.dict()
            user_data.update({
                "user_id": str(uuid.uuid4()),  # Temporary ID generation
                "ip_address": request_data.get("ip_address"),
                "user_agent": request_data.get("user_agent")
            })
            
            result = await rbac_service.register_user_request(user_data)
            
            if result["status"] == "error":
                raise HTTPException(status_code=400, detail=result["message"])
            
            return UserRegistrationResponse(**result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in register_user_request: {e}")
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def get_registration_status(self, user_id: str) -> Dict[str, Any]:
        """Get the registration/approval status of a user."""
        try:
            rbac_service = create_rbac_service(self.db)
            
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
    
    async def get_pending_approvals(self, user_id_str: str, pagination: PaginationParams, filters: FilterParams) -> PendingApprovalsResponse:
        """
        Get list of users pending approval.
        Requires admin privileges.
        """
        try:
            rbac_service = create_rbac_service(self.db)
            
            # For demo users with non-UUID format, still query the real database but skip UUID validation
            if user_id_str in ["admin_user", "demo_user"]:
                # Skip UUID validation for demo users but query real database
                try:
                    result = await rbac_service.get_pending_approvals(user_id_str)
                    
                    if result["status"] == "error":
                        if "Access denied" in result["message"]:
                            # If access denied for demo user, return empty list instead of error
                            return PendingApprovalsResponse(
                                status="success",
                                pending_approvals=[],
                                total_pending=0
                            )
                        else:
                            raise HTTPException(status_code=500, detail=result["message"])
                    
                    return PendingApprovalsResponse(**result)
                except Exception as e:
                    logger.error(f"Error getting pending approvals for demo user: {e}")
                    # Fallback to empty list for demo users if there's an error
                    return PendingApprovalsResponse(
                        status="success",
                        pending_approvals=[],
                        total_pending=0
                    )
            else:
                # Validate admin access for real users
                try:
                    user_id = uuid.UUID(user_id_str) if user_id_str else None
                    result = await rbac_service.get_pending_approvals(str(user_id) if user_id else user_id_str)
                    
                    if result["status"] == "error":
                        if "Access denied" in result["message"]:
                            raise HTTPException(status_code=403, detail=result["message"])
                        else:
                            raise HTTPException(status_code=500, detail=result["message"])
                    
                    return PendingApprovalsResponse(**result)
                except ValueError:
                    # If UUID conversion fails, treat as demo user and return empty list
                    return PendingApprovalsResponse(
                        status="success",
                        pending_approvals=[],
                        total_pending=0
                    )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_pending_approvals: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get pending approvals: {str(e)}")
    
    async def approve_user(self, approval_request: UserApprovalRequest, approved_by: str, approval_data: Dict[str, Any]) -> UserApprovalResponse:
        """
        Approve a pending user registration.
        Requires admin privileges.
        """
        try:
            rbac_service = create_rbac_service(self.db)
            
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
    
    async def reject_user(self, rejection_request: UserRejectionRequest, rejected_by: str) -> UserRejectionResponse:
        """
        Reject a pending user registration.
        Requires admin privileges.
        """
        try:
            rbac_service = create_rbac_service(self.db)
            
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
    
    async def validate_user_access(self, validation_request: AccessValidationRequest) -> AccessValidationResponse:
        """
        Validate user access permissions.
        """
        try:
            rbac_service = create_rbac_service(self.db)
            
            result = await rbac_service.validate_access(validation_request.dict())
            
            if result["status"] == "error":
                raise HTTPException(status_code=400, detail=result["message"])
            
            return AccessValidationResponse(**result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in validate_user_access: {e}")
            raise HTTPException(status_code=500, detail=f"Access validation failed: {str(e)}")
    
    async def grant_client_access(self, access_grant: ClientAccessGrant, granted_by: str, request_data: Dict[str, Any]) -> ClientAccessGrantResponse:
        """
        Grant client access to a user.
        Requires admin privileges.
        """
        try:
            rbac_service = create_rbac_service(self.db)
            
            grant_data = access_grant.dict()
            grant_data.update({
                "granted_by": granted_by,
                "granted_by_ip": request_data.get("ip_address"),
                "granted_by_user_agent": request_data.get("user_agent")
            })
            
            result = await rbac_service.grant_client_access(grant_data)
            
            if result["status"] == "error":
                if "Access denied" in result["message"]:
                    raise HTTPException(status_code=403, detail=result["message"])
                elif "not found" in result["message"]:
                    raise HTTPException(status_code=404, detail=result["message"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])
            
            return ClientAccessGrantResponse(**result)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in grant_client_access: {e}")
            raise HTTPException(status_code=500, detail=f"Client access grant failed: {str(e)}")
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information."""
        try:
            rbac_service = create_rbac_service(self.db)
            
            result = await rbac_service.get_user_profile(user_id)
            
            if result["status"] == "error":
                if "not found" in result["message"]:
                    raise HTTPException(status_code=404, detail=result["message"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in get_user_profile: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")
    
    async def update_user_profile(self, user_id: str, profile_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile information."""
        try:
            rbac_service = create_rbac_service(self.db)
            
            result = await rbac_service.update_user_profile(user_id, profile_updates)
            
            if result["status"] == "error":
                if "not found" in result["message"]:
                    raise HTTPException(status_code=404, detail=result["message"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in update_user_profile: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update user profile: {str(e)}")
    
    async def deactivate_user(self, request_data: Dict[str, Any], deactivated_by: str) -> Dict[str, Any]:
        """Deactivate a user account."""
        try:
            rbac_service = create_rbac_service(self.db)
            
            result = await rbac_service.deactivate_user(
                user_id=request_data.get("user_id"),
                deactivated_by=deactivated_by,
                reason=request_data.get("reason")
            )
            
            if result["status"] == "error":
                if "Access denied" in result["message"]:
                    raise HTTPException(status_code=403, detail=result["message"])
                elif "not found" in result["message"]:
                    raise HTTPException(status_code=404, detail=result["message"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in deactivate_user: {e}")
            raise HTTPException(status_code=500, detail=f"User deactivation failed: {str(e)}")
    
    async def activate_user(self, request_data: Dict[str, Any], activated_by: str) -> Dict[str, Any]:
        """Activate a user account."""
        try:
            rbac_service = create_rbac_service(self.db)
            
            result = await rbac_service.activate_user(
                user_id=request_data.get("user_id"),
                activated_by=activated_by,
                reason=request_data.get("reason")
            )
            
            if result["status"] == "error":
                if "Access denied" in result["message"]:
                    raise HTTPException(status_code=403, detail=result["message"])
                elif "not found" in result["message"]:
                    raise HTTPException(status_code=404, detail=result["message"])
                else:
                    raise HTTPException(status_code=400, detail=result["message"])
            
            return result
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in activate_user: {e}")
            raise HTTPException(status_code=500, detail=f"User activation failed: {str(e)}") 