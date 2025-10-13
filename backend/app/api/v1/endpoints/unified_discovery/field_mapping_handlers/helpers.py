"""
Helper functions for field mapping operations.

CC: Extracted from field_mapping_handlers.py for modularity.
"""

import logging
from typing import Optional
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.schemas.field_mapping_schemas import FieldMappingType
from ..field_mapping_schemas import FieldMappingItem

logger = logging.getLogger(__name__)


async def get_discovery_flow(
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


async def check_and_mark_field_mapping_complete(
    data_import_id: str,
    db: AsyncSession,
    context: RequestContext,
    flow_id: Optional[str] = None,
) -> bool:
    """
    Check if ALL field mappings have a final status (approved/rejected).
    If yes, mark field_mapping_completed=true on the discovery flow.

    Args:
        data_import_id: The data import ID to check mappings for
        db: Database session
        context: Request context for tenant scoping
        flow_id: Optional flow ID to update (prevents duplicate flow issues)

    Returns:
        bool: True if phase was marked complete, False otherwise
    """
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
        # CC FIX: Query by flow_id (if provided) to avoid duplicate flow issues
        # Multiple flows can point to same data_import_id
        if flow_id:
            flow_stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                )
            )
        else:
            # Fallback to data_import_id query (legacy behavior)
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


async def ensure_field_mappings_exist(
    flow: DiscoveryFlow, db: AsyncSession, context: RequestContext
) -> None:
    """Auto-generate field mappings if they don't exist."""
    if not flow.data_import_id:
        return

    # Check if mappings exist
    count_stmt = select(func.count(ImportFieldMapping.id)).where(
        and_(
            ImportFieldMapping.data_import_id == flow.data_import_id,
            ImportFieldMapping.client_account_id == context.client_account_id,
        )
    )
    mapping_count = await db.scalar(count_stmt)

    if not mapping_count or mapping_count == 0:
        await generate_field_mappings(flow, db, context)


async def generate_field_mappings(
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


async def get_field_mappings_from_db(
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


def convert_mapping_type(mapping_type: str) -> FieldMappingType:
    """Convert string mapping type to enum."""
    if mapping_type == "direct":
        return FieldMappingType.DIRECT
    elif mapping_type == "inferred":
        return FieldMappingType.INFERRED
    elif mapping_type == "manual":
        return FieldMappingType.MANUAL
    else:
        return FieldMappingType.AUTO


def create_field_mapping_item(mapping) -> Optional[FieldMappingItem]:
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
