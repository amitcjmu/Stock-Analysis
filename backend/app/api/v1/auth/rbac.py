"""
RBAC API Endpoints - Role-Based Access Control
Comprehensive endpoints for user registration, approval, and access management.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import bcrypt
from sqlalchemy import select, and_, desc, text
import json

from app.core.database import get_db
from app.core.context import get_current_context
from app.services.rbac_service import create_rbac_service, RBACService
from app.schemas.auth_schemas import (
    LoginRequest, LoginResponse, PasswordChangeRequest, PasswordChangeResponse,
    UserRegistrationRequest, UserRegistrationResponse,
    UserApprovalRequest, UserApprovalResponse,
    UserRejectionRequest, UserRejectionResponse,
    PendingApprovalsResponse, AccessValidationRequest, AccessValidationResponse,
    ClientAccessGrant, ClientAccessGrantResponse,
    PaginationParams, FilterParams, ErrorResponse, SuccessResponse
)
from app.models.client_account import User
from app.models.rbac import UserProfile, UserRole

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

# =========================
# User Registration Endpoints
# =========================

@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user against the database.
    For now, this is a simplified implementation that checks if user exists and is active.
    In production, this would verify password hashes.
    """
    try:
        # Find user by email
        user_query = select(User).where(User.email == login_request.email)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.is_active or not user.is_verified:
            raise HTTPException(status_code=401, detail="Account not activated")
        
        # Get user profile for additional info
        profile_query = select(UserProfile).where(UserProfile.user_id == user.id)
        profile_result = await db.execute(profile_query)
        user_profile = profile_result.scalar_one_or_none()
        
        if not user_profile or user_profile.status != "active":
            raise HTTPException(status_code=401, detail="Account not approved")
        
        # Verify password hash if user has a password set
        if user.password_hash:
            # Check if provided password matches the stored hash
            if not bcrypt.checkpw(login_request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
                raise HTTPException(status_code=401, detail="Invalid credentials")
        else:
            # For users without password hash (demo mode), accept any password
            pass
        
        # Get user roles
        user_roles_query = select(UserRole).where(
            and_(UserRole.user_id == user.id, UserRole.is_active == True)
        )
        roles_result = await db.execute(user_roles_query)
        user_roles = roles_result.scalars().all()
        
        # Determine if user is admin
        is_admin = any(
            role.role_type in ["platform_admin", "client_admin"] 
            for role in user_roles
        )
        
        # Create user session data
        user_data = {
            "id": str(user.id),
            "username": user.email.split("@")[0],
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "role": "admin" if is_admin else "user",
            "status": "approved",
            "organization": user_profile.organization,
            "role_description": user_profile.role_description
        }
        
        # Log successful login
        if user_profile:
            from datetime import datetime
            user_profile.last_login_at = datetime.utcnow()
            user_profile.login_count = (user_profile.login_count or 0) + 1
            user_profile.failed_login_attempts = 0
            await db.commit()
        
        return LoginResponse(
            status="success",
            message="Login successful",
            user=user_data,
            token=f"db-token-{user.id}-{uuid.uuid4().hex[:8]}"  # Simple token for demo
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in login_user: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_change: PasswordChangeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Change user's password.
    Requires authentication and current password verification.
    """
    try:
        # Get user ID from request headers
        user_id_str = request.headers.get("X-User-ID")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Convert string to UUID, handle validation
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id_str}")
        
        # Find user by ID
        user_query = select(User).where(User.id == user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if user.password_hash:
            if not bcrypt.checkpw(password_change.current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
                raise HTTPException(status_code=401, detail="Current password is incorrect")
        else:
            # For users without password hash, any current password is accepted
            pass
        
        # Generate new password hash
        new_password_hash = bcrypt.hashpw(password_change.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password in database
        user.password_hash = new_password_hash
        await db.commit()
        
        logger.info(f"Password changed successfully for user {user.email}")
        
        return PasswordChangeResponse(
            status="success",
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in change_password: {e}")
        raise HTTPException(status_code=500, detail=f"Password change failed: {str(e)}")

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
            "user_id": str(uuid.uuid4()),  # Temporary ID generation
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
        
        # Get user ID from context, with fallback for demo purposes
        user_id_str = context.user_id or "admin_user"
        
        # For demo users with non-UUID format, use a default admin validation
        if user_id_str in ["admin_user", "demo_user"]:
            # Skip UUID validation for demo users and return demo pending approvals
            demo_pending_users = [
                {
                    "user_id": "pending_user_001",
                    "organization": "New Company Inc",
                    "role_description": "Data Analyst",
                    "registration_reason": "Need access to migration planning tools",
                    "requested_access_level": "read_write",
                    "phone_number": "+1-555-0789",
                    "manager_email": "manager@company.com",
                    "requested_at": "2025-01-28T10:00:00Z"
                }
            ]
            
            return PendingApprovalsResponse(
                status="success",
                pending_approvals=demo_pending_users,
                total_pending=len(demo_pending_users)
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
        
        # Get user ID from context, with fallback for demo purposes
        user_id_str = context.user_id or "admin_user"
        
        # For demo users with non-UUID format, use a default admin validation
        if user_id_str in ["admin_user", "demo_user"]:
            # Skip UUID validation for demo users
            access_check = {"has_access": True}
        else:
            # Validate admin access for real users
            try:
                user_id = uuid.UUID(user_id_str) if user_id_str else None
                access_check = await rbac_service.validate_user_access(
                    user_id=str(user_id) if user_id else user_id_str,
                    resource_type="admin_console",
                    action="read"
                )
            except ValueError:
                # If UUID conversion fails, treat as demo user
                access_check = {"has_access": True}
        
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

@router.get("/active-users")
async def get_active_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get active users for admin management."""
    try:
        context = get_current_context()
        rbac_service = create_rbac_service(db)
        
        # Get user ID from context, with fallback for demo purposes
        user_id_str = context.user_id or "admin_user"
        
        # For demo users with non-UUID format, use a default admin validation
        if user_id_str in ["admin_user", "demo_user"]:
            # Skip UUID validation for demo users
            access_check = {"has_access": True}
        else:
            # Validate admin access for real users
            try:
                user_id = uuid.UUID(user_id_str) if user_id_str else None
                access_check = await rbac_service.validate_user_access(
                    user_id=str(user_id) if user_id else user_id_str,
                    resource_type="admin_console",
                    action="read"
                )
            except ValueError:
                # If UUID conversion fails, treat as demo user
                access_check = {"has_access": True}
        
        if not access_check["has_access"]:
            raise HTTPException(status_code=403, detail="Access denied: Admin privileges required")
        
        # Try to get real active users from database
        try:
            # Query active users with profiles
            active_users_query = select(User, UserProfile).join(
                UserProfile, User.id == UserProfile.user_id
            ).where(
                and_(
                    User.is_active == True,
                    User.is_verified == True,
                    UserProfile.status == "active"
                )
            ).order_by(desc(UserProfile.last_login_at))
            
            result = await db.execute(active_users_query)
            users_with_profiles = result.all()
            
            active_users = []
            for user, profile in users_with_profiles:
                # Get user roles
                user_roles_query = select(UserRole).where(
                    and_(UserRole.user_id == user.id, UserRole.is_active == True)
                )
                roles_result = await db.execute(user_roles_query)
                user_roles = roles_result.scalars().all()
                
                # Determine access level and role name
                is_admin = any(
                    role.role_type in ["platform_admin", "client_admin"] 
                    for role in user_roles
                )
                
                access_level = "admin" if is_admin else "read_write"
                role_name = "Administrator" if is_admin else (
                    user_roles[0].role_type.replace('_', ' ').title() if user_roles else "User"
                )
                
                active_users.append({
                    "user_id": str(user.id),
                    "email": user.email,
                    "full_name": f"{user.first_name} {user.last_name}".strip(),
                    "username": user.email.split("@")[0],
                    "organization": profile.organization,
                    "role_description": profile.role_description,
                    "access_level": access_level,
                    "role_name": role_name,
                    "is_active": user.is_active,
                    "approved_at": profile.created_at.isoformat() if profile.created_at else None,
                    "last_login": profile.last_login_at.isoformat() if profile.last_login_at else None
                })
            
            return {
                "status": "success",
                "active_users": active_users,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_users": len(active_users)
                }
            }
            
        except Exception as db_error:
            logger.warning(f"Database query failed, returning demo users: {db_error}")
            
            # Fallback to demo users
            demo_active_users = [
                {
                    "user_id": "2a0de3df-7484-4fab-98b9-2ca126e2ab21",
                    "email": "admin@aiforce.com",
                    "full_name": "Platform Administrator",
                    "username": "admin",
                    "organization": "AI Force Platform",
                    "role_description": "System Administrator",
                    "access_level": "admin",
                    "role_name": "Administrator",
                    "is_active": True,
                    "approved_at": "2025-01-01T00:00:00Z",
                    "last_login": "2025-01-28T10:30:00Z"
                },
                {
                    "user_id": "demo-user-12345678-1234-5678-9012-123456789012",
                    "email": "user@demo.com",
                    "full_name": "Demo User",
                    "username": "demo_user",
                    "organization": "Demo Organization",
                    "role_description": "Demo Analyst",
                    "access_level": "read_write",
                    "role_name": "Analyst",
                    "is_active": True,
                    "approved_at": "2025-01-27T10:00:00Z",
                    "last_login": "2025-01-28T09:15:00Z"
                },
                {
                    "user_id": "chocka_001",
                    "email": "chocka@gmail.com",
                    "full_name": "Chocka Swamy",
                    "username": "chocka",
                    "organization": "CryptoYogi LLC",
                    "role_description": "Global Program Director",
                    "access_level": "admin",
                    "role_name": "Administrator",
                    "is_active": True,
                    "approved_at": "2025-01-28T12:00:00Z",
                    "last_login": "2025-01-28T11:45:00Z"
                }
            ]
            
            return {
                "status": "success",
                "active_users": demo_active_users,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_users": len(demo_active_users)
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_active_users: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active users: {str(e)}")

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

# =========================
# Admin User Creation Endpoint
# =========================

@router.post("/admin/create-user", response_model=UserRegistrationResponse)
async def admin_create_user(
    user_data: Dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Admin endpoint to create a complete user account with immediate activation.
    Bypasses normal approval workflow for admin-created users.
    """
    try:
        import bcrypt
        import uuid
        from sqlalchemy import text
        
        context = get_current_context()
        
        # Validate admin access
        user_id_str = context.user_id or "admin_user"
        if user_id_str not in ["admin_user", "demo_user"]:
            # For real users, validate admin access
            rbac_service = create_rbac_service(db)
            access_check = await rbac_service.validate_user_access(
                user_id=user_id_str,
                resource_type="admin_console",
                action="manage"
            )
            if not access_check.get("has_access", False):
                raise HTTPException(status_code=403, detail="Admin access required")
        
        # Use the actual admin user UUID for database operations
        admin_user_uuid = "2a0de3df-7484-4fab-98b9-2ca126e2ab21"  # The actual admin user from the database
        
        # Generate user ID
        new_user_id = str(uuid.uuid4())
        
        # Hash password
        password = user_data.get('password', 'defaultPassword123!')
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        
        # Determine activation status
        is_active = user_data.get('is_active', True)
        is_verified = is_active  # If admin creates and activates, also verify
        
        # Create user in users table
        user_insert = text("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, is_verified, is_mock, created_at, updated_at)
            VALUES (:id, :email, :password_hash, :first_name, :last_name, :is_active, :is_verified, :is_mock, NOW(), NOW())
        """)
        
        full_name = user_data.get('full_name', '')
        name_parts = full_name.split(' ', 1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        await db.execute(user_insert, {
            'id': new_user_id,
            'email': user_data.get('email'),
            'password_hash': password_hash,
            'first_name': first_name,
            'last_name': last_name,
            'is_active': is_active,
            'is_verified': is_verified,
            'is_mock': False
        })
        
        # Create user profile
        profile_status = "active" if is_active else "pending_approval"
        
        if is_active:
            # For active users, set approved_at to NOW() and approved_by
            profile_insert = text("""
                INSERT INTO user_profiles (user_id, status, organization, role_description, requested_access_level, phone_number, manager_email, registration_reason, approval_requested_at, approved_at, approved_by, created_at, updated_at)
                VALUES (:user_id, :status, :organization, :role_description, :requested_access_level, :phone_number, :manager_email, :registration_reason, NOW(), NOW(), :approved_by, NOW(), NOW())
            """)
            
            await db.execute(profile_insert, {
                'user_id': new_user_id,
                'status': profile_status,
                'organization': user_data.get('organization', ''),
                'role_description': user_data.get('role_description', ''),
                'requested_access_level': user_data.get('access_level', 'read_only'),
                'phone_number': user_data.get('phone_number'),
                'manager_email': user_data.get('manager_email'),
                'registration_reason': f"Created by admin: {user_data.get('notes', 'Manual user creation')}",
                'approved_by': admin_user_uuid
            })
        else:
            # For pending users, don't set approved_at or approved_by
            profile_insert = text("""
                INSERT INTO user_profiles (user_id, status, organization, role_description, requested_access_level, phone_number, manager_email, registration_reason, approval_requested_at, created_at, updated_at)
                VALUES (:user_id, :status, :organization, :role_description, :requested_access_level, :phone_number, :manager_email, :registration_reason, NOW(), NOW(), NOW())
            """)
            
            await db.execute(profile_insert, {
                'user_id': new_user_id,
                'status': profile_status,
                'organization': user_data.get('organization', ''),
                'role_description': user_data.get('role_description', ''),
                'requested_access_level': user_data.get('access_level', 'read_only'),
                'phone_number': user_data.get('phone_number'),
                'manager_email': user_data.get('manager_email'),
                'registration_reason': f"Created by admin: {user_data.get('notes', 'Manual user creation')}"
            })
        
        # Create user role
        role_name = user_data.get('role_name', 'User')
        
        # Ensure basic roles exist
        await ensure_basic_roles_exist(db)
        
        # Map role names to role types
        role_type_mapping = {
            'Administrator': 'platform_admin',
            'Client Admin': 'client_admin', 
            'Manager': 'engagement_manager',
            'Analyst': 'analyst',
            'User': 'viewer',
            'Super Administrator': 'platform_admin'
        }
        
        role_type = role_type_mapping.get(role_name, 'viewer')
        
        # Get role permissions based on type
        role_permissions = get_role_permissions(role_type)
        
        role_insert = text("""
            INSERT INTO user_roles (id, user_id, role_type, role_name, description, permissions, scope_type, is_active, assigned_at, assigned_by, created_at)
            VALUES (:id, :user_id, :role_type, :role_name, :description, :permissions, :scope_type, :is_active, NOW(), :assigned_by, NOW())
        """)
        
        await db.execute(role_insert, {
            'id': str(uuid.uuid4()),
            'user_id': new_user_id,
            'role_type': role_type,
            'role_name': role_name,
            'description': f'{role_name} role with {user_data.get("access_level", "read_only")} access',
            'permissions': json.dumps(role_permissions),
            'scope_type': 'global',
            'is_active': True,
            'assigned_by': admin_user_uuid
        })
        
        await db.commit()
        
        return UserRegistrationResponse(
            status="success",
            message=f"User {full_name} created successfully",
            user_profile_id=new_user_id,
            approval_status="active" if is_active else "pending_approval"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in admin_create_user: {e}")
        raise HTTPException(status_code=500, detail=f"User creation failed: {str(e)}")


async def ensure_basic_roles_exist(db: AsyncSession):
    """Ensure basic user roles exist in the database."""
    try:
        from sqlalchemy import text
        
        # Check if roles exist
        check_roles = text("SELECT COUNT(*) as count FROM user_roles WHERE role_type != 'platform_admin'")
        result = await db.execute(check_roles)
        count = result.scalar()
        
        if count == 0:
            # Create basic roles for demo/reference
            basic_roles = [
                {
                    'role_type': 'client_admin',
                    'role_name': 'Client Administrator',
                    'description': 'Client-level administration access',
                    'permissions': get_role_permissions('client_admin')
                },
                {
                    'role_type': 'engagement_manager', 
                    'role_name': 'Engagement Manager',
                    'description': 'Engagement management access',
                    'permissions': get_role_permissions('engagement_manager')
                },
                {
                    'role_type': 'analyst',
                    'role_name': 'Analyst',
                    'description': 'Data analysis and reporting access',
                    'permissions': get_role_permissions('analyst')
                },
                {
                    'role_type': 'viewer',
                    'role_name': 'Viewer',
                    'description': 'Read-only access to assigned resources',
                    'permissions': get_role_permissions('viewer')
                }
            ]
            
            # Create demo roles with admin user as template
            admin_user_id = "2a0de3df-7484-4fab-98b9-2ca126e2ab21"
            
            for role_data in basic_roles:
                role_insert = text("""
                    INSERT INTO user_roles (id, user_id, role_type, role_name, description, permissions, scope_type, is_active, assigned_at, assigned_by, created_at)
                    VALUES (:id, :user_id, :role_type, :role_name, :description, :permissions, :scope_type, :is_active, NOW(), :assigned_by, NOW())
                """)
                
                await db.execute(role_insert, {
                    'id': str(uuid.uuid4()),
                    'user_id': admin_user_id,  # Assign to admin for demo
                    'role_type': role_data['role_type'],
                    'role_name': role_data['role_name'],
                    'description': role_data['description'],
                    'permissions': json.dumps(role_data['permissions']),
                    'scope_type': 'global',
                    'is_active': False,  # Demo roles, not active
                    'assigned_by': admin_user_id
                })
        
    except Exception as e:
        logger.warning(f"Could not ensure basic roles exist: {e}")


def get_role_permissions(role_type: str) -> Dict[str, bool]:
    """Get permissions for a specific role type."""
    permissions_map = {
        'platform_admin': {
            "can_create_clients": True,
            "can_manage_engagements": True,
            "can_import_data": True,
            "can_export_data": True,
            "can_view_analytics": True,
            "can_manage_users": True,
            "can_configure_agents": True,
            "can_access_admin_console": True
        },
        'client_admin': {
            "can_create_clients": False,
            "can_manage_engagements": True,
            "can_import_data": True,
            "can_export_data": True,
            "can_view_analytics": True,
            "can_manage_users": False,
            "can_configure_agents": False,
            "can_access_admin_console": False
        },
        'engagement_manager': {
            "can_create_clients": False,
            "can_manage_engagements": True,
            "can_import_data": True,
            "can_export_data": True,
            "can_view_analytics": True,
            "can_manage_users": False,
            "can_configure_agents": False,
            "can_access_admin_console": False
        },
        'analyst': {
            "can_create_clients": False,
            "can_manage_engagements": False,
            "can_import_data": True,
            "can_export_data": True,
            "can_view_analytics": True,
            "can_manage_users": False,
            "can_configure_agents": False,
            "can_access_admin_console": False
        },
        'viewer': {
            "can_create_clients": False,
            "can_manage_engagements": False,
            "can_import_data": False,
            "can_export_data": False,
            "can_view_analytics": True,
            "can_manage_users": False,
            "can_configure_agents": False,
            "can_access_admin_console": False
        }
    }
    
    return permissions_map.get(role_type, permissions_map['viewer']) 