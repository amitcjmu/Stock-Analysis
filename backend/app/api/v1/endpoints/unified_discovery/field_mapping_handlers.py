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
from typing import Optional

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.schemas.field_mapping_schemas import (
    FieldMappingType,
)
from app.core.security.secure_logging import safe_log_format
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.models import User
from app.api.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/flows/{flow_id}/field-mappings")
async def get_field_mappings(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get field mappings for a discovery flow."""
    try:
        logger.info(
            safe_log_format(
                "Getting field mappings for flow: {flow_id}", flow_id=flow_id
            )
        )

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
            raise HTTPException(status_code=404, detail="Flow not found")

        # Get field mappings from the database using data_import_id
        # If flow has a data_import_id, use it to get mappings
        if flow.data_import_id:
            mapping_stmt = select(ImportFieldMapping).where(
                ImportFieldMapping.data_import_id == flow.data_import_id
            )
            mapping_result = await db.execute(mapping_stmt)
            mappings = mapping_result.scalars().all()
        else:
            # No data import, no mappings
            mappings = []

        # Convert SQLAlchemy models to Pydantic field mappings with proper type validation
        field_mapping_items = []
        for m in mappings:
            try:
                # Map SQLAlchemy model fields to Pydantic schema fields with proper validation
                mapping_type = getattr(m, "match_type", "auto")
                if mapping_type == "direct":
                    mapping_type = FieldMappingType.DIRECT
                elif mapping_type == "inferred":
                    mapping_type = FieldMappingType.INFERRED
                elif mapping_type == "manual":
                    mapping_type = FieldMappingType.MANUAL
                else:
                    mapping_type = FieldMappingType.AUTO

                # Ensure confidence score is valid (SQLAlchemy model uses nullable float)
                confidence_score = getattr(m, "confidence_score", None)
                if confidence_score is None:
                    confidence_score = 0.5

                # Get transformation rules from SQLAlchemy JSON field
                transformation_rules = getattr(m, "transformation_rules", None)
                transformation = None
                if transformation_rules and isinstance(transformation_rules, dict):
                    # Extract transformation logic from JSON structure
                    transformation = transformation_rules.get(
                        "rule"
                    ) or transformation_rules.get("logic")

                # Create a dictionary with the mapping data including the ID
                field_mapping_dict = {
                    "id": str(m.id),  # Add the mapping ID for approval operations
                    "source_field": m.source_field,
                    "target_field": m.target_field,
                    "confidence_score": confidence_score,
                    "mapping_type": mapping_type,
                    "transformation": transformation,
                    "validation_rules": None,  # SQLAlchemy model doesn't have validation_rules field
                    "status": getattr(
                        m, "status", "suggested"
                    ),  # Include status for UI
                    "approved_by": getattr(m, "approved_by", None),
                    "approved_at": getattr(m, "approved_at", None),
                }
                field_mapping_items.append(field_mapping_dict)

            except ValueError as validation_error:
                # Log validation errors but continue processing other mappings
                logger.warning(
                    safe_log_format(
                        "Validation error for field mapping {source_field}: {error}",
                        source_field=getattr(m, "source_field", "unknown"),
                        error=str(validation_error),
                    )
                )
                continue
            except Exception as mapping_error:
                # Log unexpected errors but continue processing
                logger.error(
                    safe_log_format(
                        "Unexpected error processing field mapping {source_field}: {error}",
                        source_field=getattr(m, "source_field", "unknown"),
                        error=str(mapping_error),
                    )
                )
                continue

        # Return the response as a dictionary to support additional fields
        return {
            "success": True,
            "flow_id": flow_id,
            "field_mappings": field_mapping_items,
            "count": len(field_mapping_items),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to get field mappings: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/field-mapping/approve/{mapping_id}")
async def approve_field_mapping(
    mapping_id: str,
    approved: bool = Query(
        True, description="Whether to approve or reject the mapping"
    ),
    approval_note: Optional[str] = Query(None, description="Optional approval note"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    current_user: User = Depends(get_current_user),
):
    """Approve or reject a field mapping."""
    try:
        logger.info(
            safe_log_format(
                "Processing field mapping approval for: {mapping_id}, approved: {approved}",
                mapping_id=mapping_id,
                approved=approved,
            )
        )

        # Get the field mapping
        stmt = select(ImportFieldMapping).where(
            and_(
                ImportFieldMapping.id == mapping_id,
                ImportFieldMapping.client_account_id == context.client_account_id,
            )
        )
        result = await db.execute(stmt)
        mapping = result.scalar_one_or_none()

        if not mapping:
            raise HTTPException(status_code=404, detail="Field mapping not found")

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
            mapping.transformation_rules["approval_note"] = approval_note

        await db.commit()
        await db.refresh(mapping)

        return {
            "success": True,
            "mapping_id": str(mapping.id),
            "status": mapping.status,
            "source_field": mapping.source_field,
            "target_field": mapping.target_field,
            "approved_by": mapping.approved_by,
            "approved_at": (
                mapping.approved_at.isoformat() if mapping.approved_at else None
            ),
            "message": f"Field mapping {mapping.source_field} -> {mapping.target_field} has been {mapping.status}",
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(safe_log_format("Failed to approve field mapping: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))
