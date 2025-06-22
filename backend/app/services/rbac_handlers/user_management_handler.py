"""
User Management Handler for RBAC operations.
Handles user registration, approval, rejection, and basic user operations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from .base_handler import BaseRBACHandler

# Import RBAC models with fallback
try:
    from app.models.rbac import (
        UserProfile, UserRole, ClientAccess, EngagementAccess,
        UserStatus, AccessLevel, RoleType
    )
    RBAC_MODELS_AVAILABLE = True
except ImportError:
    RBAC_MODELS_AVAILABLE = False
    UserProfile = UserRole = ClientAccess = EngagementAccess = None
    UserStatus = AccessLevel = RoleType = None

# Import user and client models with fallback
try:
    from app.models.client_account import User
    CLIENT_MODELS_AVAILABLE = True
except ImportError:
    CLIENT_MODELS_AVAILABLE = False
    User = None

logger = logging.getLogger(__name__)

class UserManagementHandler(BaseRBACHandler):
    """Handler for user registration, approval, and management operations."""
    
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
            
            # Update user profile to rejected
            user_profile.reject(rejected_by, rejection_reason)
            
            await self.db.commit()
            
            # Log the rejection
            await self._log_access(
                user_id=rejected_by,
                action_type="user_rejection",
                result="success",
                reason=f"User {user_id} rejected: {rejection_reason}",
                details={"rejected_user": user_id, "rejection_reason": rejection_reason}
            )
            
            return {
                "status": "success",
                "message": "User registration rejected",
                "user_id": user_id,
                "rejection_reason": rejection_reason
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in reject_user: {e}")
            return {"status": "error", "message": f"Rejection failed: {str(e)}"}
    
    async def deactivate_user(self, user_id: str, deactivated_by: str, reason: str = None) -> Dict[str, Any]:
        """Deactivate an active user."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Get active user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.ACTIVE
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()
            
            if not user_profile:
                return {"status": "error", "message": "User not found or not active"}
            
            # Deactivate the base User record
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if user:
                user.is_active = False
            
            # Update user profile to inactive
            user_profile.deactivate(deactivated_by, reason)
            
            await self.db.commit()
            
            # Log the deactivation - handle demo users properly
            log_user_id = deactivated_by
            if deactivated_by == "admin_user":
                # Use a valid UUID for demo admin user
                log_user_id = "eef6ea50-6550-4f14-be2c-081d4eb23038"
            
            await self._log_access(
                user_id=log_user_id,
                action_type="user_deactivation",
                result="success",
                reason=f"User {user_id} deactivated: {reason or 'No reason provided'}",
                details={"deactivated_user": user_id, "deactivation_reason": reason}
            )
            
            return {
                "status": "success",
                "message": "User deactivated successfully",
                "user_id": user_id,
                "deactivation_reason": reason
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in deactivate_user: {e}")
            return {"status": "error", "message": f"Deactivation failed: {str(e)}"}
    
    async def activate_user(self, user_id: str, activated_by: str, reason: str = None) -> Dict[str, Any]:
        """Activate a deactivated user."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Get deactivated user profile
            query = select(UserProfile).where(
                and_(
                    UserProfile.user_id == user_id,
                    UserProfile.status == UserStatus.DEACTIVATED
                )
            )
            result = await self.db.execute(query)
            user_profile = result.scalar_one_or_none()
            
            if not user_profile:
                return {"status": "error", "message": "User not found or not deactivated"}
            
            # Activate the base User record
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if user:
                user.is_active = True
            
            # Update user profile to active
            user_profile.activate(activated_by, reason)
            
            await self.db.commit()
            
            # Log the activation - handle demo users properly
            log_user_id = activated_by
            if activated_by == "admin_user":
                # Use a valid UUID for demo admin user
                log_user_id = "eef6ea50-6550-4f14-be2c-081d4eb23038"
            
            await self._log_access(
                user_id=log_user_id,
                action_type="user_activation",
                result="success",
                reason=f"User {user_id} activated: {reason or 'No reason provided'}",
                details={"activated_user": user_id, "activation_reason": reason}
            )
            
            return {
                "status": "success",
                "message": "User activated successfully",
                "user_id": user_id,
                "activation_reason": reason
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in activate_user: {e}")
            return {"status": "error", "message": f"Activation failed: {str(e)}"}
    
    async def get_pending_approvals(self, admin_user_id: str) -> Dict[str, Any]:
        """Get all users pending approval."""
        if not self.is_available:
            return {"status": "error", "message": "RBAC models not available"}
        
        try:
            # Get all pending user profiles with related user data
            query = (
                select(UserProfile)
                .options(selectinload(UserProfile.user))
                .where(UserProfile.status == UserStatus.PENDING_APPROVAL)
                .order_by(UserProfile.created_at.desc())
            )
            
            result = await self.db.execute(query)
            pending_profiles = result.scalars().all()
            
            pending_users = []
            for profile in pending_profiles:
                user_info = {
                    "user_id": str(profile.user_id),
                    "email": profile.user.email if profile.user else "",
                    "full_name": f"{profile.user.first_name} {profile.user.last_name}".strip() if profile.user else "",
                    "organization": profile.organization,
                    "role_description": profile.role_description,
                    "registration_reason": profile.registration_reason,
                    "requested_access_level": profile.requested_access_level,
                    "phone_number": profile.phone_number,
                    "manager_email": profile.manager_email,
                    "linkedin_profile": profile.linkedin_profile,
                    "created_at": profile.created_at.isoformat() if profile.created_at else None,
                    "notification_preferences": profile.notification_preferences
                }
                pending_users.append(user_info)
            
            # Log the access
            await self._log_access(
                user_id=admin_user_id,
                action_type="view_pending_approvals",
                result="success",
                reason=f"Viewed {len(pending_users)} pending approvals"
            )
            
            return {
                "status": "success",
                "pending_approvals": pending_users,
                "total_pending": len(pending_users)
            }
            
        except Exception as e:
            logger.error(f"Error in get_pending_approvals: {e}")
            return {"status": "error", "message": f"Failed to get pending approvals: {str(e)}"} 