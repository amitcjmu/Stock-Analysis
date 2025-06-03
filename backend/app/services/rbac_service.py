"""
RBAC Service - Role-Based Access Control with Admin Approval Workflow
Comprehensive service for managing user registration, approval, and access control.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from app.core.context import get_current_context, RequestContext
from app.core.database import get_db

# Import RBAC models with fallback
try:
    from app.models.rbac import (
        UserProfile, UserRole, ClientAccess, EngagementAccess, AccessAuditLog,
        UserStatus, AccessLevel, RoleType
    )
    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = UserRole = ClientAccess = EngagementAccess = AccessAuditLog = None
    UserStatus = AccessLevel = RoleType = None

# Import user and client models with fallback
try:
    from app.models.client_account import ClientAccount, Engagement, User
    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    ClientAccount = Engagement = User = None

logger = logging.getLogger(__name__)

class RBACService:
    """Comprehensive RBAC service with admin approval workflow."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.is_available = RBAC_MODELS_AVAILABLE and CLIENT_MODELS_AVAILABLE
        
        if not self.is_available:
            logger.warning("RBAC Service initialized with limited functionality due to missing models")
    
    # =========================
    # User Registration & Approval
    # =========================
    
    async def register_user_request(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user with pending approval status."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Extract name from full_name for first_name/last_name
            full_name = user_data.get("full_name", "")
            name_parts = full_name.split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # First create the base User record
            user = User(
                id=user_data["user_id"],
                email=user_data.get("email", ""),
                first_name=first_name,
                last_name=last_name,
                is_active=False,  # Not active until approved
                is_verified=False,
                is_mock=False
            )
            
            self.db.add(user)
            await self.db.flush()  # Flush to ensure user exists before creating profile
            
            # Then create user profile with pending status
            user_profile = UserProfile(
                user_id=user_data["user_id"],
                status=UserStatus.PENDING_APPROVAL,
                registration_reason=user_data.get("registration_reason", ""),
                organization=user_data.get("organization", ""),
                role_description=user_data.get("role_description", ""),
                requested_access_level=user_data.get("requested_access_level", AccessLevel.READ_ONLY),
                phone_number=user_data.get("phone_number"),
                manager_email=user_data.get("manager_email"),
                linkedin_profile=user_data.get("linkedin_profile"),
                notification_preferences=user_data.get("notification_preferences", {
                    "email_notifications": True,
                    "system_alerts": True,
                    "learning_updates": False,
                    "weekly_reports": True
                })
            )
            
            self.db.add(user_profile)
            await self.db.commit()
            await self.db.refresh(user_profile)
            
            # Log the registration
            await self._log_access(
                user_id=user_data["user_id"],
                action_type="user_registration",
                result="success",
                reason="User registered and pending admin approval",
                details={"organization": user_data.get("organization", "")}
            )
            
            return {
                "status": "success",
                "message": "Registration submitted successfully. Awaiting admin approval.",
                "user_profile_id": str(user_profile.user_id),
                "approval_status": "pending"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in register_user_request: {e}")
            return {"status": "error", "message": f"Registration failed: {str(e)}"}
    
    async def approve_user(self, user_id: str, approved_by: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a pending user registration."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Get pending user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.PENDING_APPROVAL
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()
            
            if not user_profile:
                return {"status": "error", "message": "User not found or not pending approval"}
            
            # Get and activate the base User record
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if user:
                user.is_active = True
                user.is_verified = True
            
            # Update user profile
            user_profile.approve(approved_by)
            
            # Grant default access based on approval
            access_level = approval_data.get("access_level", user_profile.requested_access_level)
            client_accesses = approval_data.get("client_access", [])
            
            # Create client access records
            for client_access_data in client_accesses:
                client_access = ClientAccess(
                    user_profile_id=user_id,
                    client_account_id=client_access_data["client_id"],
                    access_level=access_level,
                    permissions=client_access_data.get("permissions", self._get_default_permissions(access_level)),
                    granted_by=approved_by
                )
                self.db.add(client_access)
            
            # Create default user role
            user_role = UserRole(
                user_id=user_id,
                role_type=self._determine_role_type(access_level),
                role_name=approval_data.get("role_name", "Analyst"),
                description=f"Default role assigned upon approval",
                permissions=self._get_default_role_permissions(access_level),
                assigned_by=approved_by
            )
            self.db.add(user_role)
            
            await self.db.commit()
            
            # Log the approval
            await self._log_access(
                user_id=approved_by,
                action_type="user_approval",
                result="success",
                reason=f"User {user_id} approved by admin",
                details={"approved_user": user_id, "access_level": access_level}
            )
            
            return {
                "status": "success",
                "message": "User approved successfully",
                "user_id": user_id,
                "access_level": access_level,
                "client_access_count": len(client_accesses)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in approve_user: {e}")
            return {"status": "error", "message": f"Approval failed: {str(e)}"}
    
    async def reject_user(self, user_id: str, rejected_by: str, rejection_reason: str) -> Dict[str, Any]:
        """Reject a pending user registration."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Get pending user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.PENDING_APPROVAL
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()
            
            if not user_profile:
                return {"status": "error", "message": "User not found or not pending approval"}
            
            # Update status to deactivated
            user_profile.status = UserStatus.DEACTIVATED
            
            await self.db.commit()
            
            # Log the rejection
            await self._log_access(
                user_id=rejected_by,
                action_type="user_rejection",
                result="success",
                reason=f"User {user_id} rejected: {rejection_reason}",
                details={"rejected_user": user_id, "reason": rejection_reason}
            )
            
            return {
                "status": "success",
                "message": "User registration rejected",
                "user_id": user_id,
                "reason": rejection_reason
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in reject_user: {e}")
            return {"status": "error", "message": f"Rejection failed: {str(e)}"}
    
    # =========================
    # Access Control Validation
    # =========================
    
    async def validate_user_access(self, user_id: str, resource_type: str, 
                                 resource_id: str = None, action: str = "read") -> Dict[str, Any]:
        """Validate if user has access to a specific resource and action."""
        if not self.is_available:
            return {"has_access": True, "reason": "RBAC validation bypassed (models unavailable)"}
        
        try:
            # Get user profile and access records
            user_profile_query = select(UserProfile).where(UserProfile.user_id == user_id)
            result = await self.db.execute(user_profile_query)
            user_profile = result.scalar_one_or_none()
            
            if not user_profile or not user_profile.is_approved:
                await self._log_access(
                    user_id=user_id,
                    action_type="access_denied",
                    result="denied",
                    reason="User not found or not approved",
                    resource_type=resource_type,
                    resource_id=resource_id
                )
                return {"has_access": False, "reason": "User not approved or not found"}
            
            # Get current context
            context = get_current_context()
            
            # Check resource-specific access
            if resource_type == "client":
                has_access = await self._validate_client_access(user_id, context.client_account_id, action)
            elif resource_type == "engagement":
                has_access = await self._validate_engagement_access(user_id, context.engagement_id, action)
            elif resource_type == "admin_console":
                has_access = await self._validate_admin_access(user_id)
            else:
                # Default access check
                has_access = await self._validate_default_access(user_id, action)
            
            # Log access attempt
            await self._log_access(
                user_id=user_id,
                action_type="access_validation",
                result="success" if has_access else "denied",
                reason=f"Access {'granted' if has_access else 'denied'} for {resource_type}:{action}",
                resource_type=resource_type,
                resource_id=resource_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id
            )
            
            return {
                "has_access": has_access,
                "reason": f"Access {'granted' if has_access else 'denied'} based on user permissions"
            }
            
        except Exception as e:
            logger.error(f"Error in validate_user_access: {e}")
            return {"has_access": False, "reason": f"Access validation error: {str(e)}"}
    
    async def _validate_client_access(self, user_id: str, client_id: str, action: str) -> bool:
        """Validate client-level access."""
        query = select(ClientAccess).where(
            and_(
                ClientAccess.user_profile_id == user_id,
                ClientAccess.client_account_id == client_id,
                ClientAccess.is_active == True
            )
        )
        result = await self.db.execute(query)
        client_access = result.scalar_one_or_none()
        
        if not client_access:
            return False
        
        # Check if access is expired
        if client_access.is_expired:
            return False
        
        # Check action-specific permissions
        permissions = client_access.permissions or {}
        permission_key = f"can_{action}_data" if action in ["view", "import", "export"] else f"can_{action}"
        
        return permissions.get(permission_key, False)
    
    async def _validate_engagement_access(self, user_id: str, engagement_id: str, action: str) -> bool:
        """Validate engagement-level access."""
        query = select(EngagementAccess).where(
            and_(
                EngagementAccess.user_profile_id == user_id,
                EngagementAccess.engagement_id == engagement_id,
                EngagementAccess.is_active == True
            )
        )
        result = await self.db.execute(query)
        engagement_access = result.scalar_one_or_none()
        
        if not engagement_access:
            return False
        
        # Check if access is expired
        if engagement_access.is_expired:
            return False
        
        # Check action-specific permissions
        permissions = engagement_access.permissions or {}
        permission_key = f"can_{action}_data" if action in ["view", "import", "export"] else f"can_{action}"
        
        return permissions.get(permission_key, False)
    
    async def _validate_admin_access(self, user_id: str) -> bool:
        """Validate admin console access."""
        query = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True,
                or_(
                    UserRole.role_type == RoleType.PLATFORM_ADMIN,
                    UserRole.role_type == RoleType.CLIENT_ADMIN
                )
            )
        )
        result = await self.db.execute(query)
        admin_role = result.scalar_one_or_none()
        
        if not admin_role:
            return False
        
        permissions = admin_role.permissions or {}
        return permissions.get("can_access_admin_console", False)
    
    async def _validate_default_access(self, user_id: str, action: str) -> bool:
        """Validate default access for general resources."""
        # For demo/development, allow read access for approved users
        if action == "read":
            return True
        
        # Check user roles for write access
        query = select(UserRole).where(
            and_(
                UserRole.user_id == user_id,
                UserRole.is_active == True
            )
        )
        result = await self.db.execute(query)
        roles = result.scalars().all()
        
        for role in roles:
            permissions = role.permissions or {}
            if action == "write" and permissions.get("can_import_data", False):
                return True
        
        return False
    
    # =========================
    # User & Access Management
    # =========================
    
    async def get_pending_approvals(self, admin_user_id: str) -> Dict[str, Any]:
        """Get list of users pending approval."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Verify admin access
            admin_access = await self._validate_admin_access(admin_user_id)
            if not admin_access:
                return {"status": "error", "message": "Access denied: Admin privileges required"}
            
            # Get pending users
            query = select(UserProfile).where(
                UserProfile.status == UserStatus.PENDING_APPROVAL
            ).order_by(desc(UserProfile.approval_requested_at))
            
            result = await self.db.execute(query)
            pending_users = result.scalars().all()
            
            pending_list = []
            for user in pending_users:
                pending_list.append({
                    "user_id": str(user.user_id),
                    "organization": user.organization,
                    "role_description": user.role_description,
                    "registration_reason": user.registration_reason,
                    "requested_access_level": user.requested_access_level,
                    "manager_email": user.manager_email,
                    "phone_number": user.phone_number,
                    "requested_at": user.approval_requested_at.isoformat() if user.approval_requested_at else None
                })
            
            return {
                "status": "success",
                "pending_approvals": pending_list,
                "total_pending": len(pending_list)
            }
            
        except Exception as e:
            logger.error(f"Error in get_pending_approvals: {e}")
            return {"status": "error", "message": f"Failed to get pending approvals: {str(e)}"}
    
    async def grant_client_access(self, user_id: str, client_id: str, access_data: Dict[str, Any], 
                                granted_by: str) -> Dict[str, Any]:
        """Grant or update client access for a user."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Check if access already exists
            query = select(ClientAccess).where(
                and_(
                    ClientAccess.user_profile_id == user_id,
                    ClientAccess.client_account_id == client_id
                )
            )
            result = await self.db.execute(query)
            existing_access = result.scalar_one_or_none()
            
            if existing_access:
                # Update existing access
                existing_access.access_level = access_data.get("access_level", existing_access.access_level)
                existing_access.permissions = access_data.get("permissions", existing_access.permissions)
                existing_access.is_active = True
                existing_access.granted_by = granted_by
                access_action = "updated"
            else:
                # Create new access
                client_access = ClientAccess(
                    user_profile_id=user_id,
                    client_account_id=client_id,
                    access_level=access_data.get("access_level", AccessLevel.READ_ONLY),
                    permissions=access_data.get("permissions", self._get_default_permissions(access_data.get("access_level", AccessLevel.READ_ONLY))),
                    granted_by=granted_by
                )
                self.db.add(client_access)
                access_action = "granted"
            
            await self.db.commit()
            
            # Log the access grant
            await self._log_access(
                user_id=granted_by,
                action_type="client_access_granted",
                result="success",
                reason=f"Client access {access_action} for user {user_id}",
                resource_type="client",
                resource_id=client_id,
                client_account_id=client_id,
                details={"target_user": user_id, "access_level": access_data.get("access_level")}
            )
            
            return {
                "status": "success",
                "message": f"Client access {access_action} successfully",
                "user_id": user_id,
                "client_id": client_id,
                "access_level": access_data.get("access_level")
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in grant_client_access: {e}")
            return {"status": "error", "message": f"Failed to grant client access: {str(e)}"}
    
    # =========================
    # Utility Methods
    # =========================
    
    def _get_default_permissions(self, access_level: str) -> Dict[str, bool]:
        """Get default permissions based on access level."""
        if access_level == AccessLevel.READ_ONLY:
            return {
                "can_view_data": True,
                "can_import_data": False,
                "can_export_data": False,
                "can_manage_engagements": False,
                "can_configure_client_settings": False,
                "can_manage_client_users": False
            }
        elif access_level == AccessLevel.READ_WRITE:
            return {
                "can_view_data": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_manage_engagements": False,
                "can_configure_client_settings": False,
                "can_manage_client_users": False
            }
        elif access_level == AccessLevel.ADMIN:
            return {
                "can_view_data": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_manage_engagements": True,
                "can_configure_client_settings": True,
                "can_manage_client_users": True
            }
        else:
            return {}
    
    def _get_default_role_permissions(self, access_level: str) -> Dict[str, bool]:
        """Get default role permissions based on access level."""
        if access_level == AccessLevel.READ_ONLY:
            return {
                "can_create_clients": False,
                "can_manage_engagements": False,
                "can_import_data": False,
                "can_export_data": True,
                "can_view_analytics": True,
                "can_manage_users": False,
                "can_configure_agents": False,
                "can_access_admin_console": False
            }
        elif access_level == AccessLevel.READ_WRITE:
            return {
                "can_create_clients": False,
                "can_manage_engagements": False,
                "can_import_data": True,
                "can_export_data": True,
                "can_view_analytics": True,
                "can_manage_users": False,
                "can_configure_agents": False,
                "can_access_admin_console": False
            }
        elif access_level == AccessLevel.ADMIN:
            return {
                "can_create_clients": True,
                "can_manage_engagements": True,
                "can_import_data": True,
                "can_export_data": True,
                "can_view_analytics": True,
                "can_manage_users": True,
                "can_configure_agents": True,
                "can_access_admin_console": True
            }
        else:
            return {}
    
    def _determine_role_type(self, access_level: str) -> str:
        """Determine role type based on access level."""
        if access_level == AccessLevel.ADMIN:
            return RoleType.CLIENT_ADMIN
        elif access_level == AccessLevel.READ_WRITE:
            return RoleType.ANALYST
        else:
            return RoleType.VIEWER
    
    async def _log_access(self, user_id: str, action_type: str, result: str, 
                         reason: str = None, **kwargs):
        """Log access attempt or administrative action."""
        if not self.is_available:
            return
        
        try:
            log_entry = AccessAuditLog(
                user_id=user_id,
                action_type=action_type,
                result=result,
                reason=reason,
                resource_type=kwargs.get("resource_type"),
                resource_id=kwargs.get("resource_id"),
                client_account_id=kwargs.get("client_account_id"),
                engagement_id=kwargs.get("engagement_id"),
                session_id=kwargs.get("session_id"),
                ip_address=kwargs.get("ip_address"),
                user_agent=kwargs.get("user_agent"),
                details=kwargs.get("details", {})
            )
            
            self.db.add(log_entry)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error logging access: {e}")
            # Don't fail the main operation if logging fails
            pass

# Factory function for dependency injection
def create_rbac_service(db: AsyncSession) -> RBACService:
    """Create RBAC service with database session."""
    return RBACService(db) 