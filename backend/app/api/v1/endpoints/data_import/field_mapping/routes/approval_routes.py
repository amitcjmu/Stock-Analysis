"""
Field mapping approval route handlers.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from ..models.mapping_schemas import ApprovalRequest, FieldMappingUpdate
from ..services.mapping_service import MappingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approval", tags=["field-mapping-approval"])


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


@router.post("/approve-mappings")
async def approve_field_mappings(
    request: ApprovalRequest,
    service: MappingService = Depends(get_mapping_service)
):
    """Approve or reject multiple field mappings."""
    try:
        results = []
        
        for mapping_id in request.mapping_ids:
            try:
                update_data = FieldMappingUpdate(is_approved=request.approved)
                updated_mapping = await service.update_field_mapping(mapping_id, update_data)
                results.append({
                    "mapping_id": mapping_id,
                    "status": "approved" if request.approved else "rejected",
                    "success": True
                })
            except Exception as e:
                logger.error(f"Error updating mapping {mapping_id}: {e}")
                results.append({
                    "mapping_id": mapping_id,
                    "status": "error", 
                    "success": False,
                    "error": str(e)
                })
        
        success_count = len([r for r in results if r["success"]])
        
        return {
            "total_mappings": len(request.mapping_ids),
            "successful_updates": success_count,
            "failed_updates": len(request.mapping_ids) - success_count,
            "approval_status": "approved" if request.approved else "rejected",
            "approval_note": request.approval_note,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in bulk approval: {e}")
        raise HTTPException(status_code=500, detail="Failed to process approval request")


@router.post("/approve-mapping/{mapping_id}")
async def approve_single_mapping(
    mapping_id: str,  # Changed to str to accept UUID
    approved: bool = True,
    approval_note: str = None,
    service: MappingService = Depends(get_mapping_service)
):
    """Approve or reject a single field mapping."""
    try:
        update_data = FieldMappingUpdate(is_approved=approved)
        updated_mapping = await service.update_field_mapping(mapping_id, update_data)
        
        return {
            "mapping_id": mapping_id,
            "status": "approved" if approved else "rejected",
            "approval_note": approval_note,
            "updated_mapping": updated_mapping
        }
        
    except ValueError as e:
        logger.warning(f"Mapping {mapping_id} not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving mapping {mapping_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve mapping")


@router.get("/pending-approvals")
async def get_pending_approvals(
    import_id: str = None,
    service: MappingService = Depends(get_mapping_service)
):
    """Get field mappings pending approval."""
    try:
        if import_id:
            mappings = await service.get_field_mappings(import_id)
            pending = [m for m in mappings if not m.is_approved]
        else:
            # TODO: Get all pending mappings across imports for the context
            pending = []
        
        return {
            "pending_count": len(pending),
            "pending_mappings": pending
        }
        
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending approvals")