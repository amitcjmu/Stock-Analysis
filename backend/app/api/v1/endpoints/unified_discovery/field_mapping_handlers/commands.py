"""
Field Mapping Command Operations (Write operations).

CC: Extracted from field_mapping_handlers.py for modularity.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.models import User
from app.api.v1.auth.auth_utils import get_current_user
from ..field_mapping_schemas import FieldMappingApprovalResponse
from .helpers import (
    get_discovery_flow,
    check_and_mark_field_mapping_complete,
)

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
        await check_and_mark_field_mapping_complete(
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


@router.post("/flows/{flow_id}/approve-needs-review-as-custom-attributes")
async def approve_needs_review_as_custom_attributes(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Bulk approve all 'needs review' field mappings as custom_attributes.

    Needs review mappings are those with:
    - status = 'suggested' (not yet approved/rejected)
    - target_field is empty, UNMAPPED, or has low confidence

    This provides a quick path to map unmapped fields to custom_attributes
    without requiring individual user approval for each field.
    """
    try:
        logger.info(
            f"Bulk approving needs review mappings as custom_attributes for flow {flow_id}"
        )

        # Get the discovery flow
        flow = await get_discovery_flow(flow_id, db, context)

        if not flow.data_import_id:
            raise HTTPException(
                status_code=400,
                detail="No data import associated with this flow",
            )

        # Find all mappings that need review:
        # 1. Status is 'suggested' (not yet finalized)
        # 2. Target field is empty, UNMAPPED, or confidence < 0.7
        stmt = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.data_import_id == flow.data_import_id,
                ImportFieldMapping.client_account_id == context.client_account_id,
                ImportFieldMapping.status == "suggested",
            )
        )

        result = await db.execute(stmt)
        all_suggested = result.scalars().all()

        # Filter to only those needing review (UNMAPPED or low confidence)
        needs_review = []
        for mapping in all_suggested:
            if (
                not mapping.target_field
                or mapping.target_field == "UNMAPPED"
                or mapping.target_field == ""
                or (mapping.confidence_score and mapping.confidence_score < 0.7)
            ):
                needs_review.append(mapping)

        if not needs_review:
            return {
                "success": True,
                "flow_id": flow_id,
                "approved_count": 0,
                "message": "No mappings need review - all are already mapped or approved",
            }

        # Bulk approve all needs review mappings as custom_attributes
        approved_count = 0
        for mapping in needs_review:
            mapping.target_field = "custom_attributes"
            mapping.status = "approved"
            mapping.approved_by = str(current_user.id)
            mapping.approved_at = datetime.utcnow()
            mapping.confidence_score = 0.8  # Set reasonable confidence for custom attrs
            approved_count += 1

        await db.commit()

        logger.info(
            f"✅ Bulk approved {approved_count} needs review mappings as custom_attributes"
        )

        # Check if ALL mappings are now finalized
        await check_and_mark_field_mapping_complete(
            str(flow.data_import_id), db, context
        )

        return {
            "success": True,
            "flow_id": flow_id,
            "approved_count": approved_count,
            "message": f"Successfully approved {approved_count} mappings as custom_attributes",
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to bulk approve needs review: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to bulk approve: {str(e)}",
        )


@router.post("/flows/{flow_id}/trigger-field-mapping")
async def trigger_field_mapping(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> Dict[str, Any]:
    """Trigger field mapping generation for a discovery flow."""
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
