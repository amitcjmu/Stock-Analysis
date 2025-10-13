"""
Field Mapping Handlers for Unified Discovery

Handles field mapping operations for discovery flows.
Extracted from the main unified_discovery.py file for better maintainability.
"""

import logging
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.schemas.field_mapping_schemas import (
    FieldMappingType,
)
from .field_mapping_schemas import (
    FieldMappingItem,
    FieldMappingsResponse,
    FieldMappingApprovalResponse,
)
from app.core.security.secure_logging import safe_log_format
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.models import User
from app.api.v1.auth.auth_utils import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# Compatibility shim for frontend calls like /api/v1/field-mapping/learned/approve/{mapping_id}
@router.post("/field-mapping/learned/approve/{mapping_id}")
async def approve_field_mapping_compat(
    mapping_id: str,
    approved: bool = Query(
        default=True, description="Approve (true) or reject (false)"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """Compatibility endpoint that forwards to the standard approval endpoint."""
    try:
        return await approve_field_mapping(
            mapping_id=mapping_id,
            approved=approved,
            db=db,
            context=context,
            current_user=current_user,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Compat approve failed: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def _get_discovery_flow(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> DiscoveryFlow:
    """Get discovery flow with tenant scoping."""
    stmt = select(DiscoveryFlow).where(
        and_(
            DiscoveryFlow.flow_id == flow_id,
            DiscoveryFlow.client_account_id == context.client_account_id,
            DiscoveryFlow.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(
            status_code=404,
            detail="Flow not found or not accessible in current context",
        )
    return flow


async def _check_and_mark_field_mapping_complete(
    data_import_id: str, db: AsyncSession, context: RequestContext
) -> bool:
    """
    Check if ALL field mappings have a final status (approved/rejected).
    If yes, mark field_mapping_completed=true on the discovery flow.

    Returns:
        bool: True if phase was marked complete, False otherwise
    """
    from sqlalchemy import func

    # Count total mappings and those with final status
    count_stmt = select(
        func.count(ImportFieldMapping.id).label("total"),
        func.count(ImportFieldMapping.id)
        .filter(ImportFieldMapping.status.in_(["approved", "rejected"]))
        .label("finalized"),
    ).where(
        and_(
            ImportFieldMapping.data_import_id == data_import_id,
            ImportFieldMapping.client_account_id == context.client_account_id,
        )
    )

    result = await db.execute(count_stmt)
    counts = result.one()

    logger.info(
        f"Field mapping status for data_import {data_import_id}: "
        f"{counts.finalized}/{counts.total} finalized"
    )

    # Mark complete only if ALL mappings have final status
    if counts.total > 0 and counts.finalized == counts.total:
        # Find and update the discovery flow
        flow_stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.data_import_id == data_import_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        flow_result = await db.execute(flow_stmt)
        flow = flow_result.scalar_one_or_none()

        if flow:
            flow.field_mapping_completed = True
            await db.commit()
            logger.info(
                f"✅ Marked field_mapping_completed=true for flow {flow.flow_id} "
                f"(all {counts.total} mappings finalized)"
            )
            return True

    return False


async def _ensure_field_mappings_exist(
    flow: DiscoveryFlow, db: AsyncSession, context: RequestContext
) -> None:
    """Auto-generate field mappings if they don't exist."""
    if not flow.data_import_id:
        return

    # Check if mappings exist
    from sqlalchemy import func

    count_stmt = select(func.count(ImportFieldMapping.id)).where(
        and_(
            ImportFieldMapping.data_import_id == flow.data_import_id,
            ImportFieldMapping.client_account_id == context.client_account_id,
        )
    )
    mapping_count = await db.scalar(count_stmt)

    if not mapping_count or mapping_count == 0:
        await _generate_field_mappings(flow, db, context)


async def _generate_field_mappings(
    flow: DiscoveryFlow, db: AsyncSession, context: RequestContext
) -> None:
    """Generate field mappings for the flow."""
    logger.info(
        f"No field mappings found for import {flow.data_import_id}, auto-generating..."
    )

    try:
        from app.api.v1.endpoints.data_import.field_mapping.services.mapping_service import (
            MappingService,
        )

        mapping_service = MappingService(db, context)
        mapping_result = await mapping_service.generate_mappings_for_import(
            str(flow.data_import_id)
        )

        logger.info(
            f"✅ Auto-generated {mapping_result.get('mappings_created', 0)} field mappings"
        )

        # CC FIX: DON'T mark field mapping as completed after generation
        # Phase should only be complete when ALL mappings are approved/rejected
        await db.commit()

    except Exception as gen_error:
        logger.warning(f"Failed to auto-generate field mappings: {gen_error}")


async def _get_field_mappings_from_db(
    flow: DiscoveryFlow, db: AsyncSession, context: RequestContext
) -> list:
    """Get field mappings from database with tenant scoping."""
    if not flow.data_import_id:
        return []

    mapping_stmt = select(ImportFieldMapping).where(
        and_(
            ImportFieldMapping.data_import_id == flow.data_import_id,
            ImportFieldMapping.client_account_id == context.client_account_id,
        )
    )
    mapping_result = await db.execute(mapping_stmt)
    return mapping_result.scalars().all()


def _convert_mapping_type(mapping_type: str) -> FieldMappingType:
    """Convert string mapping type to enum."""
    if mapping_type == "direct":
        return FieldMappingType.DIRECT
    elif mapping_type == "inferred":
        return FieldMappingType.INFERRED
    elif mapping_type == "manual":
        return FieldMappingType.MANUAL
    else:
        return FieldMappingType.AUTO


def _create_field_mapping_item(mapping) -> Optional[FieldMappingItem]:
    """Create a FieldMappingItem from SQLAlchemy model.

    UNMAPPED fields are shown to allow users to manually map them.
    """
    try:
        # Ensure confidence score is valid
        confidence_score = getattr(mapping, "confidence_score", None)
        if confidence_score is None:
            confidence_score = 0.5

        # For UNMAPPED fields, show them with empty target to indicate they need mapping
        # This allows users to manually select appropriate target fields
        target_field = mapping.target_field
        if target_field == "UNMAPPED":
            target_field = ""  # Show empty target for unmapped fields
            confidence_score = 0.0  # Zero confidence for unmapped

        return FieldMappingItem(
            id=str(mapping.id),
            source_field=mapping.source_field,
            target_field=target_field,
            confidence_score=confidence_score,
            field_type=getattr(mapping, "field_type", None),
            status=getattr(mapping, "status", "suggested"),
            approved_by=getattr(mapping, "approved_by", None),
            approved_at=getattr(mapping, "approved_at", None),
            agent_reasoning=getattr(mapping, "agent_reasoning", None),
            transformation_rules=getattr(mapping, "transformation_rules", None),
        )

    except ValueError as validation_error:
        logger.warning(
            safe_log_format(
                "Validation error for field mapping {source_field}: {error}",
                source_field=getattr(mapping, "source_field", "unknown"),
                error=str(validation_error),
            )
        )
        return None
    except Exception as mapping_error:
        logger.error(
            safe_log_format(
                "Unexpected error processing field mapping {source_field}: {error}",
                source_field=getattr(mapping, "source_field", "unknown"),
                error=str(mapping_error),
            )
        )
        return None


@router.get("/flows/{flow_id}/field-mappings", response_model=FieldMappingsResponse)
async def get_field_mappings(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> FieldMappingsResponse:
    """Get field mappings for a discovery flow."""
    try:
        logger.info(
            safe_log_format(
                "Getting field mappings for flow: {flow_id}", flow_id=flow_id
            )
        )

        # Get the discovery flow with tenant scoping
        flow = await _get_discovery_flow(flow_id, db, context)

        # Ensure field mappings exist (auto-generate if needed)
        await _ensure_field_mappings_exist(flow, db, context)

        # Get field mappings from database
        mappings = await _get_field_mappings_from_db(flow, db, context)

        # Convert SQLAlchemy models to Pydantic field mappings
        field_mapping_items = []
        for mapping in mappings:
            item = _create_field_mapping_item(mapping)
            if item:
                field_mapping_items.append(item)

        # Return the response using Pydantic model
        return FieldMappingsResponse(
            success=True,
            flow_id=flow_id,
            field_mappings=field_mapping_items,
            count=len(field_mapping_items),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to get field mappings: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/field-mapping/approve/{mapping_id}",
    response_model=FieldMappingApprovalResponse,
)
async def approve_field_mapping(
    mapping_id: str,
    approved: bool = Query(
        True, description="Whether to approve or reject the mapping"
    ),
    approval_note: Optional[str] = Query(None, description="Optional approval note"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> FieldMappingApprovalResponse:
    """Approve or reject a field mapping."""
    try:
        logger.info(
            safe_log_format(
                "Processing field mapping approval for: {mapping_id}, approved: {approved}",
                mapping_id=mapping_id,
                approved=approved,
            )
        )

        # Get the field mapping with proper authorization checks
        stmt = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_id,
                ImportFieldMapping.client_account_id == context.client_account_id,
            )
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if not mapping:
            raise HTTPException(
                status_code=404,
                detail="Field mapping not found or not accessible in current context",
            )

        # Update the mapping status
        if approved:
            mapping.status = "approved"
            mapping.approved_by = str(current_user.id)
            mapping.approved_at = datetime.utcnow()
        else:
            mapping.status = "rejected"
            mapping.approved_by = str(current_user.id)
            mapping.approved_at = datetime.utcnow()

        # If there's an approval note, store it in transformation_rules
        if approval_note:
            if not mapping.transformation_rules:
                mapping.transformation_rules = {}
            elif not isinstance(mapping.transformation_rules, dict):
                # Ensure it's a mutable dictionary
                mapping.transformation_rules = dict(mapping.transformation_rules)
            mapping.transformation_rules["approval_note"] = approval_note

        await db.commit()
        await db.refresh(mapping)

        # CC FIX: Check if ALL mappings are now finalized, and mark phase complete if so
        await _check_and_mark_field_mapping_complete(
            str(mapping.data_import_id), db, context
        )

        return FieldMappingApprovalResponse(
            success=True,
            mapping_id=str(mapping.id),
            status=mapping.status,
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            approved_by=mapping.approved_by,
            approved_at=mapping.approved_at,
            message=f"Field mapping {mapping.source_field} -> {mapping.target_field} has been {mapping.status}",
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(safe_log_format("Failed to approve field mapping: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/trigger-field-mapping")
async def trigger_field_mapping(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """Trigger field mapping generation for a discovery flow."""
    from sqlalchemy import delete

    try:
        logger.info(f"Triggering field mapping for flow: {flow_id}")

        # Get the discovery flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(
                status_code=404,
                detail="Flow not found or not accessible in current context",
            )

        if not flow.data_import_id:
            raise HTTPException(
                status_code=400,
                detail="No data import associated with this flow",
            )

        # Generate field mappings
        from app.api.v1.endpoints.data_import.field_mapping.services.mapping_service import (
            MappingService,
        )

        mapping_service = MappingService(db, context)

        # CC: Force regeneration by deleting existing mappings first
        delete_stmt = delete(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == flow.data_import_id,
                ImportFieldMapping.client_account_id == context.client_account_id,
            )
        )
        await db.execute(delete_stmt)

        mapping_result = await mapping_service.generate_mappings_for_import(
            str(flow.data_import_id)
        )

        # CC FIX: DON'T mark field mapping as completed after generation
        # Phase should only be complete when ALL mappings are approved/rejected
        await db.commit()

        logger.info(
            f"✅ Generated {mapping_result.get('mappings_created', 0)} field mappings for flow {flow_id}"
        )

        return {
            "success": True,
            "flow_id": flow_id,
            "mappings_created": mapping_result.get("mappings_created", 0),
            "message": f"Successfully generated {mapping_result.get('mappings_created', 0)} field mappings",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering field mapping: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger field mapping: {str(e)}",
        )
