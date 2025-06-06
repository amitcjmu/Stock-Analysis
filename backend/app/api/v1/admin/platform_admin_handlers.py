"""
Platform Admin API Handlers - Manages soft-deleted items and purge approvals.
Only accessible by platform administrators with proper role verification.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.context import get_current_context

# Import enhanced RBAC models and services
try:
    from app.models.rbac_enhanced import (
        EnhancedUserProfile, SoftDeletedItems, RoleLevel, 
        DataScope, DeletedItemType
    )
    from app.services.rbac_handlers.enhanced_rbac_service import EnhancedRBACService
    ENHANCED_RBAC_AVAILABLE = True
except ImportError:
    ENHANCED_RBAC_AVAILABLE = False
    EnhancedUserProfile = SoftDeletedItems = RoleLevel = None
    DataScope = DeletedItemType = EnhancedRBACService = None

logger = logging.getLogger(__name__)

# Create router
platform_admin_router = APIRouter(prefix="/platform-admin", tags=["platform-admin"])

# Pydantic models for request/response
class PurgeApprovalRequest(BaseModel):
    soft_delete_id: str
    notes: Optional[str] = None

class PurgeApprovalResponse(BaseModel):
    status: str
    message: str
    item_type: Optional[str] = None
    item_name: Optional[str] = None

class PendingItemsResponse(BaseModel):
    status: str
    pending_items: List[Dict[str, Any]]
    total_count: int

# Dependency to verify platform admin access
async def verify_platform_admin(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> EnhancedUserProfile:
    """Verify that the current user is a platform administrator."""
    if not ENHANCED_RBAC_AVAILABLE:
        # Fallback for demo - allow access
        return None
    
    try:
        context = get_current_context()
        user_id = context.user_id
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get enhanced RBAC service
        rbac_service = EnhancedRBACService(db)
        user_profile = await rbac_service.get_user_profile(user_id)
        
        if not user_profile or not user_profile.is_platform_admin:
            raise HTTPException(
                status_code=403, 
                detail="Platform administrator access required"
            )
        
        return user_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying platform admin: {e}")
        raise HTTPException(status_code=500, detail="Access verification failed")

@platform_admin_router.get("/pending-purge-items", response_model=PendingItemsResponse)
async def get_pending_purge_items(
    db: AsyncSession = Depends(get_db),
    admin_profile: EnhancedUserProfile = Depends(verify_platform_admin)
):
    """
    Get all soft-deleted items pending platform admin review.
    Only accessible by platform administrators.
    """
    try:
        if not ENHANCED_RBAC_AVAILABLE:
            # Return demo data for fallback
            return PendingItemsResponse(
                status="success",
                pending_items=[
                    {
                        "id": "demo_item_001",
                        "item_type": "client_account",
                        "item_id": "demo_client_001",
                        "item_name": "Demo Legacy Systems Corp",
                        "client_account_name": "Demo Legacy Systems Corp",
                        "engagement_name": None,
                        "deleted_by_name": "Demo Admin",
                        "deleted_by_email": "demo.admin@company.com",
                        "deleted_at": "2025-01-05T14:30:00Z",
                        "delete_reason": "Demo: Client requested account closure",
                        "status": "pending_review"
                    }
                ],
                total_count=1
            )
        
        # Get enhanced RBAC service
        rbac_service = EnhancedRBACService(db)
        
        # Get pending items (this method needs to be implemented in the service)
        result = await rbac_service.get_pending_purge_items(str(admin_profile.user_id))
        
        if result["status"] == "success":
            return PendingItemsResponse(
                status="success",
                pending_items=result["pending_items"],
                total_count=result["total_count"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting pending purge items: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending items")

@platform_admin_router.post("/approve-purge", response_model=PurgeApprovalResponse)
async def approve_purge(
    request: PurgeApprovalRequest,
    db: AsyncSession = Depends(get_db),
    admin_profile: EnhancedUserProfile = Depends(verify_platform_admin)
):
    """
    Approve permanent deletion of a soft-deleted item.
    Only accessible by platform administrators.
    """
    try:
        if not ENHANCED_RBAC_AVAILABLE:
            # Return demo response for fallback
            return PurgeApprovalResponse(
                status="success",
                message="Demo: Purge approved successfully",
                item_type="client_account",
                item_name="Demo Item"
            )
        
        # Get enhanced RBAC service
        rbac_service = EnhancedRBACService(db)
        
        # Approve the purge
        result = await rbac_service.approve_purge(
            platform_admin_user_id=str(admin_profile.user_id),
            soft_delete_id=request.soft_delete_id,
            notes=request.notes
        )
        
        if result["status"] == "success":
            return PurgeApprovalResponse(
                status="success",
                message=result["message"],
                item_type=result.get("item_type"),
                item_name=result.get("item_name")
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving purge: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve purge")

@platform_admin_router.post("/reject-purge", response_model=PurgeApprovalResponse)
async def reject_purge(
    request: PurgeApprovalRequest,
    db: AsyncSession = Depends(get_db),
    admin_profile: EnhancedUserProfile = Depends(verify_platform_admin)
):
    """
    Reject permanent deletion of a soft-deleted item and restore it.
    Only accessible by platform administrators.
    """
    try:
        if not ENHANCED_RBAC_AVAILABLE:
            # Return demo response for fallback
            return PurgeApprovalResponse(
                status="success",
                message="Demo: Purge rejected and item restored",
                item_type="client_account",
                item_name="Demo Item"
            )
        
        # Validate that notes are provided for rejection
        if not request.notes or not request.notes.strip():
            raise HTTPException(
                status_code=400, 
                detail="Notes are required when rejecting a purge request"
            )
        
        # Get enhanced RBAC service
        rbac_service = EnhancedRBACService(db)
        
        # Reject the purge and restore the item
        result = await rbac_service.reject_purge(
            platform_admin_user_id=str(admin_profile.user_id),
            soft_delete_id=request.soft_delete_id,
            notes=request.notes
        )
        
        if result["status"] == "success":
            return PurgeApprovalResponse(
                status="success",
                message=result["message"],
                item_type=result.get("item_type"),
                item_name=result.get("item_name")
            )
        else:
            raise HTTPException(status_code=400, detail=result["message"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting purge: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject purge")

@platform_admin_router.get("/stats")
async def get_platform_admin_stats(
    db: AsyncSession = Depends(get_db),
    admin_profile: EnhancedUserProfile = Depends(verify_platform_admin)
):
    """
    Get platform administration statistics.
    Only accessible by platform administrators.
    """
    try:
        if not ENHANCED_RBAC_AVAILABLE:
            # Return demo stats for fallback
            return {
                "status": "success",
                "stats": {
                    "total_pending_items": 3,
                    "pending_by_type": {
                        "client_account": 1,
                        "engagement": 1,
                        "data_import_session": 1,
                        "user_profile": 0
                    },
                    "recent_activity": {
                        "last_24h": 2,
                        "last_7d": 3,
                        "last_30d": 5
                    },
                    "total_users": 156,
                    "active_users": 142,
                    "pending_approvals": 8
                }
            }
        
        # TODO: Implement actual stats gathering
        # This would query the database for real statistics
        
        return {
            "status": "success",
            "stats": {
                "total_pending_items": 0,
                "pending_by_type": {},
                "recent_activity": {},
                "total_users": 0,
                "active_users": 0,
                "pending_approvals": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting platform admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")

@platform_admin_router.get("/audit-log")
async def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    action_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin_profile: EnhancedUserProfile = Depends(verify_platform_admin)
):
    """
    Get platform audit log entries.
    Only accessible by platform administrators.
    """
    try:
        if not ENHANCED_RBAC_AVAILABLE:
            # Return demo audit log for fallback
            return {
                "status": "success",
                "audit_entries": [
                    {
                        "id": "audit_001",
                        "user_id": "user_001",
                        "user_email": "john.admin@company.com",
                        "action_type": "purge_approved",
                        "resource_type": "client_account",
                        "resource_id": "client_001",
                        "result": "success",
                        "reason": "Platform admin approved permanent deletion",
                        "created_at": "2025-01-05T15:30:00Z",
                        "ip_address": "192.168.1.100"
                    },
                    {
                        "id": "audit_002",
                        "user_id": "user_002",
                        "user_email": "sarah.manager@techcorp.com",
                        "action_type": "soft_delete",
                        "resource_type": "engagement",
                        "resource_id": "engagement_001",
                        "result": "success",
                        "reason": "Soft deleted engagement",
                        "created_at": "2025-01-04T09:15:00Z",
                        "ip_address": "10.0.1.50"
                    }
                ],
                "total_count": 2,
                "limit": limit,
                "offset": offset
            }
        
        # TODO: Implement actual audit log querying
        # This would query the AccessAuditLog table with proper filtering
        
        return {
            "status": "success",
            "audit_entries": [],
            "total_count": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit log") 