"""
Soft delete operations for Enhanced RBAC Service.
"""

from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from .base import DeletedItemType, SoftDeletedItems, logger


class RBACSoftDelete:
    """Soft delete operations for items."""

    async def soft_delete_item(
        self,
        user_id: str,
        item_type: DeletedItemType,
        item_id: str,
        item_name: str = None,
        client_account_id: str = None,
        engagement_id: str = None,
        reason: str = None,
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
                return {
                    "status": "error",
                    "message": "Insufficient permissions to delete data",
                }

            # Validate scope-based delete permissions
            if not await self._can_user_delete_item(
                user_profile, item_type, client_account_id, engagement_id
            ):
                return {
                    "status": "error",
                    "message": "Cannot delete items outside your scope",
                }

            # Create soft deleted item record
            soft_deleted_item = SoftDeletedItems(
                item_type=item_type,
                item_id=item_id,
                item_name=item_name or f"{item_type}_{item_id}",
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                deleted_by=user_id,
                delete_reason=reason,
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
                engagement_id=engagement_id,
            )

            return {
                "status": "success",
                "message": "Item soft deleted successfully. Awaiting platform admin review for permanent deletion.",
                "soft_delete_id": str(soft_deleted_item.id),
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error in soft delete: {e}")
            return {"status": "error", "message": f"Soft delete failed: {str(e)}"}

    async def get_pending_purge_items(
        self, platform_admin_user_id: str
    ) -> Dict[str, Any]:
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
                return {
                    "status": "error",
                    "message": "Only platform admins can view pending purge items",
                }

            # Get pending items
            query = (
                select(SoftDeletedItems)  # SKIP_TENANT_CHECK
                .where(SoftDeletedItems.status == "pending_review")
                .options(
                    selectinload(SoftDeletedItems.deleted_by_user),
                    selectinload(SoftDeletedItems.client_account),
                    selectinload(SoftDeletedItems.engagement),
                )
                .order_by(SoftDeletedItems.deleted_at.desc())
            )

            result = await self.db.execute(query)
            pending_items = result.scalars().all()

            # Convert to dict format
            items_data = []
            for item in pending_items:
                items_data.append(
                    {
                        "id": str(item.id),
                        "item_type": item.item_type,
                        "item_id": str(item.item_id),
                        "item_name": item.item_name,
                        "client_account_name": (
                            item.client_account.name if item.client_account else None
                        ),
                        "engagement_name": (
                            item.engagement.name if item.engagement else None
                        ),
                        "deleted_by_name": (
                            f"{item.deleted_by_user.first_name} {item.deleted_by_user.last_name}"
                            if item.deleted_by_user
                            else "Unknown"
                        ),
                        "deleted_by_email": (
                            item.deleted_by_user.email
                            if item.deleted_by_user
                            else "unknown@domain.com"
                        ),
                        "deleted_at": (
                            item.deleted_at.isoformat() if item.deleted_at else None
                        ),
                        "delete_reason": item.delete_reason,
                        "status": item.status,
                    }
                )

            return {
                "status": "success",
                "pending_items": items_data,
                "total_count": len(items_data),
            }

        except Exception as e:
            logger.error(f"Error getting pending purge items: {e}")
            return {
                "status": "error",
                "message": f"Failed to get pending items: {str(e)}",
            }

    async def approve_purge(
        self, platform_admin_user_id: str, soft_delete_id: str, notes: str = None
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
                return {
                    "status": "error",
                    "message": "Only platform admins can approve purges",
                }

            # Get soft deleted item
            query = select(SoftDeletedItems).where(  # SKIP_TENANT_CHECK
                and_(
                    SoftDeletedItems.id == soft_delete_id,
                    SoftDeletedItems.status == "pending_review",
                )
            )
            result = await self.db.execute(query)
            soft_deleted_item = result.scalar_one_or_none()

            if not soft_deleted_item:
                return {
                    "status": "error",
                    "message": "Soft deleted item not found or already processed",
                }

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
                resource_id=soft_deleted_item.item_id,
            )

            return {
                "status": "success",
                "message": "Item approved for permanent deletion",
                "item_type": soft_deleted_item.item_type,
                "item_name": soft_deleted_item.item_name,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error approving purge: {e}")
            return {"status": "error", "message": f"Failed to approve purge: {str(e)}"}

    async def reject_purge(
        self, platform_admin_user_id: str, soft_delete_id: str, notes: str = None
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
                return {
                    "status": "error",
                    "message": "Only platform admins can reject purges",
                }

            # Get soft deleted item
            query = select(SoftDeletedItems).where(  # SKIP_TENANT_CHECK
                and_(
                    SoftDeletedItems.id == soft_delete_id,
                    SoftDeletedItems.status == "pending_review",
                )
            )
            result = await self.db.execute(query)
            soft_deleted_item = result.scalar_one_or_none()

            if not soft_deleted_item:
                return {
                    "status": "error",
                    "message": "Soft deleted item not found or already processed",
                }

            # Reject purge
            soft_deleted_item.reject_purge(platform_admin_user_id, notes)

            # Restore the original item
            await self._restore_item_from_soft_delete(
                soft_deleted_item.item_type, soft_deleted_item.item_id
            )

            await self.db.commit()

            # Log the rejection
            await self._log_access(
                user_id=platform_admin_user_id,
                action_type="purge_rejected",
                result="success",
                reason="Platform admin rejected deletion and restored item",
                resource_type=soft_deleted_item.item_type,
                resource_id=soft_deleted_item.item_id,
            )

            return {
                "status": "success",
                "message": "Deletion rejected and item restored",
                "item_type": soft_deleted_item.item_type,
                "item_name": soft_deleted_item.item_name,
            }

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error rejecting purge: {e}")
            return {"status": "error", "message": f"Failed to reject purge: {str(e)}"}
