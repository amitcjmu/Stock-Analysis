"""
Field mapping approval route handlers.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format

from ..models.mapping_schemas import ApprovalRequest, FieldMappingUpdate
from ..services.mapping_service import MappingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/field-mappings/approval")


def get_mapping_service(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> MappingService:
    """Dependency injection for mapping service."""
    return MappingService(db, context)


@router.post("/approve-mappings")
async def approve_field_mappings(
    request: ApprovalRequest, service: MappingService = Depends(get_mapping_service)
):
    """Approve or reject multiple field mappings in a single transaction."""
    try:
        if not request.mapping_ids:
            raise HTTPException(status_code=400, detail="No mapping IDs provided")

        logger.info(
            f"Bulk approval request: {len(request.mapping_ids)} mappings, approved={request.approved}"
        )

        # Use bulk update method for better performance
        update_data = FieldMappingUpdate(is_approved=request.approved)
        bulk_result = await service.bulk_update_field_mappings(
            request.mapping_ids, update_data
        )

        # Transform result to match original API response
        results = []
        for mapping_id in bulk_result["updated_ids"]:
            results.append(
                {
                    "mapping_id": mapping_id,
                    "status": "approved" if request.approved else "rejected",
                    "success": True,
                }
            )

        for failure in bulk_result["failures"]:
            results.append(
                {
                    "mapping_id": failure["mapping_id"],
                    "status": "error",
                    "success": False,
                    "error": failure["error"],
                }
            )

        # Check for phase transition after approval
        if request.approved and bulk_result["updated_mappings"] > 0:
            # Get the flow ID from one of the updated mappings
            if bulk_result["updated_ids"]:
                from app.models.data_import.mapping import ImportFieldMapping
                from sqlalchemy import select

                # Get flow ID from first mapping
                first_mapping = await service.db.execute(
                    select(ImportFieldMapping.master_flow_id).where(
                        ImportFieldMapping.id == bulk_result["updated_ids"][0]
                    )
                )
                flow_id = first_mapping.scalar_one_or_none()

                if flow_id:
                    # Check and perform phase transition
                    from app.services.discovery.phase_transition_service import (
                        DiscoveryPhaseTransitionService,
                    )

                    transition_service = DiscoveryPhaseTransitionService(service.db)
                    next_phase = await transition_service.check_and_transition_from_attribute_mapping(
                        str(flow_id)
                    )

                    if next_phase:
                        logger.info(
                            f"✅ Phase transition triggered: flow {flow_id} -> {next_phase}"
                        )

        return {
            "total_mappings": bulk_result["total_mappings"],
            "successful_updates": bulk_result["updated_mappings"],
            "failed_updates": bulk_result["failed_updates"],
            "approval_status": "approved" if request.approved else "rejected",
            "approval_note": request.approval_note,
            "results": results,
        }

    except ValueError as e:
        logger.warning(safe_log_format("Bulk approval validation error: {e}", e=e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(safe_log_format("Error in bulk approval: {e}", e=e))
        raise HTTPException(
            status_code=500, detail="Failed to process approval request"
        )


@router.post("/approve-mapping/{mapping_id}")
async def approve_single_mapping(
    mapping_id: str,  # Changed to str to accept UUID
    approved: bool = True,
    approval_note: str = None,
    service: MappingService = Depends(get_mapping_service),
):
    """Approve or reject a single field mapping."""
    try:
        update_data = FieldMappingUpdate(is_approved=approved)
        updated_mapping = await service.update_field_mapping(mapping_id, update_data)

        # Check for phase transition after approval
        if approved and updated_mapping:
            # Get the flow ID from the updated mapping
            from app.models.data_import.mapping import ImportFieldMapping
            from sqlalchemy import select

            # Get flow ID from mapping
            result = await service.db.execute(
                select(ImportFieldMapping.master_flow_id).where(
                    ImportFieldMapping.id == mapping_id
                )
            )
            flow_id = result.scalar_one_or_none()

            if flow_id:
                # Check and perform phase transition
                from app.services.discovery.phase_transition_service import (
                    DiscoveryPhaseTransitionService,
                )

                transition_service = DiscoveryPhaseTransitionService(service.db)
                next_phase = await transition_service.check_and_transition_from_attribute_mapping(
                    str(flow_id)
                )

                if next_phase:
                    logger.info(
                        f"✅ Phase transition triggered: flow {flow_id} -> {next_phase}"
                    )

        return {
            "mapping_id": mapping_id,
            "status": "approved" if approved else "rejected",
            "approval_note": approval_note,
            "updated_mapping": updated_mapping,
        }

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Mapping {mapping_id} not found: {e}", mapping_id=mapping_id, e=e
            )
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error approving mapping {mapping_id}: {e}", mapping_id=mapping_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail="Failed to approve mapping")


@router.get("/pending-approvals")
async def get_pending_approvals(
    import_id: str = None, service: MappingService = Depends(get_mapping_service)
):
    """Get field mappings pending approval."""
    try:
        if import_id:
            mappings = await service.get_field_mappings(import_id)
            pending = [m for m in mappings if not m.is_approved]
        else:
            # TODO: Get all pending mappings across imports for the context
            pending = []

        return {"pending_count": len(pending), "pending_mappings": pending}

    except Exception as e:
        logger.error(safe_log_format("Error getting pending approvals: {e}", e=e))
        raise HTTPException(status_code=500, detail="Failed to get pending approvals")
