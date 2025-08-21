"""
Field Mapping Handlers for Unified Discovery

Handles field mapping operations for discovery flows.
Extracted from the main unified_discovery.py file for better maintainability.
"""

import logging
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.schemas.field_mapping_schemas import (
    FieldMappingsResponse,
    FieldMappingItem,
    FieldMappingType,
)
from app.core.security.secure_logging import safe_log_format
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow

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

                field_mapping_item = FieldMappingItem(
                    source_field=m.source_field,
                    target_field=m.target_field,
                    confidence_score=confidence_score,
                    mapping_type=mapping_type,
                    transformation=transformation,
                    validation_rules=None,  # SQLAlchemy model doesn't have validation_rules field
                )
                field_mapping_items.append(field_mapping_item)

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
