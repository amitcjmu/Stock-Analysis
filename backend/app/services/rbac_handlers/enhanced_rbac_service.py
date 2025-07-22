"""
Enhanced RBAC Service - Hierarchical role-based access control with proper data scoping.
Implements the correct role hierarchy: Platform Admin > Client Admin > Engagement Manager > Analyst > Viewer.
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Import enhanced RBAC models
try:
    from app.models.client_account import ClientAccount, Engagement, User
    from app.models.rbac_enhanced import (
        DEFAULT_ROLE_PERMISSIONS,
        AccessAuditLog,
        DataScope,
        DeletedItemType,
        EnhancedUserProfile,
        RoleLevel,
        RolePermissions,
        SoftDeletedItems,
        UserStatus,
    )
    ENHANCED_RBAC_AVAILABLE = True
except ImportError:
    ENHANCED_RBAC_AVAILABLE = False
    EnhancedUserProfile = RolePermissions = SoftDeletedItems = AccessAuditLog = None
    User = ClientAccount = Engagement = None
    RoleLevel = DataScope = UserStatus = DeletedItemType = DEFAULT_ROLE_PERMISSIONS = None

logger = logging.getLogger(__name__)

class EnhancedRBACService:
    """
    Enhanced RBAC service implementing hierarchical role-based access control.
    Provides proper data scoping, soft delete management, and platform admin oversight.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.is_available = ENHANCED_RBAC_AVAILABLE
        
        if not self.is_available:
            logger.warning("Enhanced RBAC models not available - running in fallback mode")
    
    async def get_user_profile(self, user_id: str) -> Optional[EnhancedUserProfile]:
        """Get enhanced user profile by user ID."""
        if not self.is_available:
            return None
        
        try:
            query = select(EnhancedUserProfile).where(
                and_(
                    EnhancedUserProfile.user_id == user_id,
                    EnhancedUserProfile.is_deleted is False
                )
            ).options(
                selectinload(EnhancedUserProfile.scope_client),
                selectinload(EnhancedUserProfile.scope_engagement)
            )
            
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    async def create_user_profile(
        self, 
        user_id: str, 
        role_level: RoleLevel, 
        data_scope: DataScope,
        scope_client_account_id: str = None,
        scope_engagement_id: str = None,
        **additional_data
    ) -> Dict[str, Any]:
        """Create a new enhanced user profile with proper role and scope assignment."""
        if not self.is_available:
            return {"status": "error", "message": "Enhanced RBAC not available"}
        
        try:
            # Validate scope assignment
            validation_result = self._validate_scope_assignment(
                role_level, data_scope, scope_client_account_id, scope_engagement_id
            )
            
            if validation_result["status"] == "error":
                return validation_result
            
            # Create user profile
            user_profile = EnhancedUserProfile(
                user_id=user_id,
                role_level=role_level,
                data_scope=data_scope,
                scope_client_account_id=scope_client_account_id,
                scope_engagement_id=scope_engagement_id,
                status=UserStatus.PENDING_APPROVAL,
                **additional_data
            )
            
            self.db.add(user_profile)
            await self.db.commit()
            await self.db.refresh(user_profile)
            
            # Log the creation
            await self._log_access(
                user_id=user_id,
                action_type="user_profile_created",
                result="success",
                details={
                    "role_level": role_level,
                    "data_scope": data_scope,
                    "scope_client_account_id": scope_client_account_id,
                    "scope_engagement_id": scope_engagement_id
                }
            )
            
            return {
                "status": "success",
                "message": "User profile created successfully",
                "user_profile": user_profile
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating user profile: {e}")
            return {"status": "error", "message": f"Failed to create user profile: {str(e)}"}
    
    async def check_access_permission(
        self, 
        user_id: str, 
        resource_type: str, 
        resource_id: str = None,
        client_account_id: str = None,
        engagement_id: str = None,
        action: str = "read"
    ) -> Dict[str, Any]:
        """
        Check if user has permission to access a specific resource.
        Implements hierarchical access control with proper scoping.
        """
        if not self.is_available:
            return {"allowed": True, "reason": "Enhanced RBAC not available - allowing access"}
        
        try:
            # Get user profile
            user_profile = await self.get_user_profile(user_id)
            if not user_profile:
                await self._log_access(
                    user_id=user_id,
                    action_type=f"access_denied_{resource_type}",
                    result="denied",
                    reason="User profile not found",
                    resource_type=resource_type,
                    resource_id=resource_id
                )
                return {"allowed": False, "reason": "User profile not found"}
            
            # Check if user is active
            if not user_profile.is_active:
                await self._log_access(
                    user_id=user_id,
                    action_type=f"access_denied_{resource_type}",
                    result="denied",
                    reason="User account inactive or deleted",
                    resource_type=resource_type,
                    resource_id=resource_id
                )
                return {"allowed": False, "reason": "User account inactive"}
            
            # Platform admins have access to everything
            if user_profile.is_platform_admin:
                await self._log_access(
                    user_id=user_id,
                    action_type=f"access_granted_{resource_type}",
                    result="success",
                    reason="Platform admin access",
                    resource_type=resource_type,
                    resource_id=resource_id
                )
                return {"allowed": True, "reason": "Platform admin access"}
            
            # Check specific resource access based on scope
            access_result = await self._check_resource_access(
                user_profile, resource_type, resource_id, client_account_id, engagement_id, action
            )
            
            # Log the access attempt
            await self._log_access(
                user_id=user_id,
                action_type=f"access_{'granted' if access_result['allowed'] else 'denied'}_{resource_type}",
                result="success" if access_result['allowed'] else "denied",
                reason=access_result['reason'],
                resource_type=resource_type,
                resource_id=resource_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_role_level=user_profile.role_level,
                user_data_scope=user_profile.data_scope
            )
            
            return access_result
            
        except Exception as e:
            logger.error(f"Error checking access permission: {e}")
            return {"allowed": False, "reason": f"Permission check failed: {str(e)}"}
    
    async def get_user_accessible_data(
        self, 
        user_id: str, 
        include_demo: bool = True
    ) -> Dict[str, Any]:
        """
        Get all data that a user can access based on their role and scope.
        Returns client_account_ids and engagement_ids the user can access.
        """
        if not self.is_available:
            return {
                "client_account_ids": [],
                "engagement_ids": [],
                "scope": "all",
                "include_demo": include_demo
            }
        
        try:
            user_profile = await self.get_user_profile(user_id)
            if not user_profile or not user_profile.is_active:
                return {
                    "client_account_ids": [],
                    "engagement_ids": [], 
                    "scope": "none",
                    "include_demo": include_demo
                }
            
            # Platform admin can access all data
            if user_profile.is_platform_admin:
                return {
                    "client_account_ids": [],  # Empty means all
                    "engagement_ids": [],      # Empty means all
                    "scope": "platform",
                    "include_demo": include_demo
                }
            
            # Get accessible client and engagement IDs
            accessible_clients = user_profile.get_accessible_client_ids()
            accessible_engagements = user_profile.get_accessible_engagement_ids()
            
            # If engagement scope, also include the client
            if user_profile.data_scope == DataScope.ENGAGEMENT and user_profile.scope_client_account_id:
                if str(user_profile.scope_client_account_id) not in accessible_clients:
                    accessible_clients.append(str(user_profile.scope_client_account_id))
            
            return {
                "client_account_ids": accessible_clients,
                "engagement_ids": accessible_engagements,
                "scope": user_profile.data_scope,
                "role_level": user_profile.role_level,
                "include_demo": include_demo
            }
            
        except Exception as e:
            logger.error(f"Error getting user accessible data: {e}")
            return {
                "client_account_ids": [],
                "engagement_ids": [],
                "scope": "error",
                "include_demo": include_demo
            }
    
    async def soft_delete_item(
        self, 
        user_id: str,
        item_type: DeletedItemType,
        item_id: str,
        item_name: str = None,
        client_account_id: str = None,
        engagement_id: str = None,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Perform soft delete of an item (only admins at appropriate level can do this).
        Creates entry in soft_deleted_items for platform admin review.
        """
        if not self.is_available:
            return {"status": "error", "message": "Enhanced RBAC not available"}
        
        try:
            # Check user permissions
            user_profile = await self.get_user_profile(user_id)
            if not user_profile or not user_profile.can_delete_data:
                return {"status": "error", "message": "Insufficient permissions to delete data"}
            
            # Validate scope-based delete permissions
            if not await self._can_user_delete_item(user_profile, item_type, client_account_id, engagement_id):
                return {"status": "error", "message": "Cannot delete items outside your scope"}
            
            # Create soft deleted item record
            soft_deleted_item = SoftDeletedItems(
                item_type=item_type,
                item_id=item_id,
                item_name=item_name or f"{item_type}_{item_id}",
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                deleted_by=user_id,
                delete_reason=reason
            )
            
            self.db.add(soft_deleted_item)
            
            # Perform the actual soft delete on the target item
            await self._perform_item_soft_delete(item_type, item_id)
            
            await self.db.commit()
            
            # Log the soft delete
            await self._log_access(
                user_id=user_id,
                action_type="soft_delete",
                result="success",
                reason=f"Soft deleted {item_type}",
                resource_type=item_type,
                resource_id=item_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            
            return {
                "status": "success",
                "message": "Item soft deleted successfully. Awaiting platform admin review for permanent deletion.",
                "soft_delete_id": str(soft_deleted_item.id)
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in soft delete: {e}")
            return {"status": "error", "message": f"Soft delete failed: {str(e)}"}
    
    async def get_pending_purge_items(self, platform_admin_user_id: str) -> Dict[str, Any]:
        """
        Get all soft-deleted items pending platform admin review.
        Only platform admins can access this.
        """
        if not self.is_available:
            return {"status": "error", "message": "Enhanced RBAC not available"}
        
        try:
            # Verify platform admin
            user_profile = await self.get_user_profile(platform_admin_user_id)
            if not user_profile or not user_profile.is_platform_admin:
                return {"status": "error", "message": "Only platform admins can view pending purge items"}
            
            # Get pending items
            query = select(SoftDeletedItems).where(
                SoftDeletedItems.status == 'pending_review'
            ).options(
                selectinload(SoftDeletedItems.deleted_by_user),
                selectinload(SoftDeletedItems.client_account),
                selectinload(SoftDeletedItems.engagement)
            ).order_by(SoftDeletedItems.deleted_at.desc())
            
            result = await self.db.execute(query)
            pending_items = result.scalars().all()
            
            # Convert to dict format
            items_data = []
            for item in pending_items:
                items_data.append({
                    "id": str(item.id),
                    "item_type": item.item_type,
                    "item_id": str(item.item_id),
                    "item_name": item.item_name,
                    "client_account_name": item.client_account.name if item.client_account else None,
                    "engagement_name": item.engagement.name if item.engagement else None,
                    "deleted_by_name": f"{item.deleted_by_user.first_name} {item.deleted_by_user.last_name}" if item.deleted_by_user else "Unknown",
                    "deleted_by_email": item.deleted_by_user.email if item.deleted_by_user else "unknown@domain.com",
                    "deleted_at": item.deleted_at.isoformat() if item.deleted_at else None,
                    "delete_reason": item.delete_reason,
                    "status": item.status
                })
            
            return {
                "status": "success",
                "pending_items": items_data,
                "total_count": len(items_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting pending purge items: {e}")
            return {"status": "error", "message": f"Failed to get pending items: {str(e)}"}
    
    async def approve_purge(
        self, 
        platform_admin_user_id: str, 
        soft_delete_id: str, 
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Approve permanent deletion of a soft-deleted item.
        Only platform admins can do this.
        """
        if not self.is_available:
            return {"status": "error", "message": "Enhanced RBAC not available"}
        
        try:
            # Verify platform admin
            user_profile = await self.get_user_profile(platform_admin_user_id)
            if not user_profile or not user_profile.is_platform_admin:
                return {"status": "error", "message": "Only platform admins can approve purges"}
            
            # Get soft deleted item
            query = select(SoftDeletedItems).where(
                and_(
                    SoftDeletedItems.id == soft_delete_id,
                    SoftDeletedItems.status == 'pending_review'
                )
            )
            result = await self.db.execute(query)
            soft_deleted_item = result.scalar_one_or_none()
            
            if not soft_deleted_item:
                return {"status": "error", "message": "Soft deleted item not found or already processed"}
            
            # Approve for purge
            soft_deleted_item.approve_for_purge(platform_admin_user_id, notes)
            
            await self.db.commit()
            
            # Log the approval
            await self._log_access(
                user_id=platform_admin_user_id,
                action_type="purge_approved",
                result="success",
                reason="Platform admin approved permanent deletion",
                resource_type=soft_deleted_item.item_type,
                resource_id=soft_deleted_item.item_id
            )
            
            return {
                "status": "success",
                "message": "Item approved for permanent deletion",
                "item_type": soft_deleted_item.item_type,
                "item_name": soft_deleted_item.item_name
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error approving purge: {e}")
            return {"status": "error", "message": f"Failed to approve purge: {str(e)}"}
    
    async def reject_purge(
        self, 
        platform_admin_user_id: str, 
        soft_delete_id: str, 
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Reject permanent deletion of a soft-deleted item and restore it.
        Only platform admins can do this.
        """
        if not self.is_available:
            return {"status": "error", "message": "Enhanced RBAC not available"}
        
        try:
            # Verify platform admin
            user_profile = await self.get_user_profile(platform_admin_user_id)
            if not user_profile or not user_profile.is_platform_admin:
                return {"status": "error", "message": "Only platform admins can reject purges"}
            
            # Get soft deleted item
            query = select(SoftDeletedItems).where(
                and_(
                    SoftDeletedItems.id == soft_delete_id,
                    SoftDeletedItems.status == 'pending_review'
                )
            )
            result = await self.db.execute(query)
            soft_deleted_item = result.scalar_one_or_none()
            
            if not soft_deleted_item:
                return {"status": "error", "message": "Soft deleted item not found or already processed"}
            
            # Reject purge
            soft_deleted_item.reject_purge(platform_admin_user_id, notes)
            
            # Restore the original item
            await self._restore_item_from_soft_delete(soft_deleted_item.item_type, soft_deleted_item.item_id)
            
            await self.db.commit()
            
            # Log the rejection
            await self._log_access(
                user_id=platform_admin_user_id,
                action_type="purge_rejected",
                result="success",
                reason="Platform admin rejected deletion and restored item",
                resource_type=soft_deleted_item.item_type,
                resource_id=soft_deleted_item.item_id
            )
            
            return {
                "status": "success",
                "message": "Deletion rejected and item restored",
                "item_type": soft_deleted_item.item_type,
                "item_name": soft_deleted_item.item_name
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error rejecting purge: {e}")
            return {"status": "error", "message": f"Failed to reject purge: {str(e)}"}
    
    # Private helper methods
    
    def _validate_scope_assignment(
        self, 
        role_level: RoleLevel, 
        data_scope: DataScope,
        scope_client_account_id: str = None,
        scope_engagement_id: str = None
    ) -> Dict[str, Any]:
        """Validate that role and scope assignment is logical."""
        
        # Platform admins must have platform scope
        if role_level == RoleLevel.PLATFORM_ADMIN and data_scope != DataScope.PLATFORM:
            return {"status": "error", "message": "Platform admins must have platform data scope"}
        
        # Client admins must have client scope with client ID
        if role_level == RoleLevel.CLIENT_ADMIN:
            if data_scope != DataScope.CLIENT or not scope_client_account_id:
                return {"status": "error", "message": "Client admins must have client scope with client account ID"}
        
        # Engagement managers must have engagement scope with both IDs
        if role_level == RoleLevel.ENGAGEMENT_MANAGER:
            if data_scope != DataScope.ENGAGEMENT or not scope_engagement_id or not scope_client_account_id:
                return {"status": "error", "message": "Engagement managers must have engagement scope with both client and engagement IDs"}
        
        return {"status": "success"}
    
    async def _check_resource_access(
        self, 
        user_profile: EnhancedUserProfile, 
        resource_type: str, 
        resource_id: str = None,
        client_account_id: str = None,
        engagement_id: str = None,
        action: str = "read"
    ) -> Dict[str, Any]:
        """Check if user can access specific resource based on their scope."""
        
        # Anonymous users can only access demo data
        if user_profile.role_level == RoleLevel.ANONYMOUS:
            if resource_type == "demo" or (client_account_id and await self._is_demo_client(client_account_id)):
                return {"allowed": True, "reason": "Demo data access"}
            return {"allowed": False, "reason": "Anonymous users can only access demo data"}
        
        # Check client access if client_account_id provided
        if client_account_id:
            if not user_profile.can_access_client(client_account_id):
                return {"allowed": False, "reason": "No access to this client account"}
        
        # Check engagement access if engagement_id provided
        if engagement_id:
            if not user_profile.can_access_engagement(engagement_id, client_account_id):
                return {"allowed": False, "reason": "No access to this engagement"}
        
        # Check action-specific permissions
        if action in ["create", "update", "delete"] and user_profile.role_level == RoleLevel.VIEWER:
            return {"allowed": False, "reason": "Viewers have read-only access"}
        
        return {"allowed": True, "reason": f"Access granted based on {user_profile.role_level} role"}
    
    async def _can_user_delete_item(
        self, 
        user_profile: EnhancedUserProfile, 
        item_type: DeletedItemType,
        client_account_id: str = None,
        engagement_id: str = None
    ) -> bool:
        """Check if user can delete items based on their role and scope."""
        
        # Platform admins can delete anything
        if user_profile.is_platform_admin:
            return True
        
        # Client admins can delete within their client scope
        if user_profile.is_client_admin and user_profile.data_scope == DataScope.CLIENT:
            if client_account_id and user_profile.can_access_client(client_account_id):
                return True
        
        # Engagement managers can delete within their engagement scope
        if user_profile.is_engagement_manager and user_profile.data_scope == DataScope.ENGAGEMENT:
            if engagement_id and user_profile.can_access_engagement(engagement_id, client_account_id):
                return True
        
        return False
    
    async def _perform_item_soft_delete(self, item_type: DeletedItemType, item_id: str):
        """Perform the actual soft delete on the target item."""
        # This would implement the actual soft delete logic for each item type
        # For now, just log the action
        logger.info(f"Performing soft delete on {item_type} with ID {item_id}")
        
        # TODO: Implement actual soft delete for each model type
        # if item_type == DeletedItemType.CLIENT_ACCOUNT:
        #     # Update ClientAccount.is_active = False
        # elif item_type == DeletedItemType.ENGAGEMENT:
        #     # Update Engagement.is_active = False
        # etc.
    
    async def _restore_item_from_soft_delete(self, item_type: DeletedItemType, item_id: str):
        """Restore an item from soft delete."""
        # This would implement the actual restore logic for each item type
        logger.info(f"Restoring {item_type} with ID {item_id} from soft delete")
        
        # TODO: Implement actual restore for each model type
    
    async def _is_demo_client(self, client_account_id: str) -> bool:
        """Check if a client account is demo/mock data."""
        try:
            query = select(ClientAccount).where(
                and_(
                    ClientAccount.id == client_account_id,
                    ClientAccount.is_mock is True
                )
            )
            result = await self.db.execute(query)
            return result.scalar_one_or_none() is not None
        except Exception:
            return False
    
    async def _log_access(self, **kwargs):
        """Log access attempt to audit log."""
        if not self.is_available:
            return
        
        try:
            audit_log = AccessAuditLog(**kwargs)
            self.db.add(audit_log)
            await self.db.commit()
        except Exception as e:
            # Log warning instead of error - audit failure shouldn't block operations
            logger.warning(f"Failed to log access audit (table may not exist): {str(e)}")
            await self.db.rollback() 