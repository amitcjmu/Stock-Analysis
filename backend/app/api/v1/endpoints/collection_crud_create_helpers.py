"""
Collection Flow Create Helper Functions
Helper functions extracted from collection_crud_create_commands to reduce
complexity and file length while maintaining all functionality.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import CollectionFlow

logger = logging.getLogger(__name__)


def build_existing_flow_error_detail(
    existing_flow: CollectionFlow,
    flow_analysis: Dict[str, Any],
) -> Dict[str, Any]:
    """Build detailed error response for existing active flow conflict.

    Args:
        existing_flow: The existing active collection flow
        flow_analysis: Analysis results from lifecycle manager

    Returns:
        Detailed error information with resolution steps
    """
    # Calculate flow age
    last_activity = existing_flow.updated_at or existing_flow.created_at
    # Ensure timezone-aware datetime for calculation
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=timezone.utc)

    age_seconds = (datetime.now(timezone.utc) - last_activity).total_seconds()
    age_hours = round(age_seconds / 3600, 2)

    return {
        "error": "Active collection flow already exists",
        "message": (
            "Cannot create new flow while another is active. "
            "Please manage existing flows first."
        ),
        "existing_flow_id": str(existing_flow.flow_id),
        "existing_flow_name": existing_flow.flow_name,
        "existing_flow_status": existing_flow.status,
        "last_activity": last_activity.isoformat(),
        "age_hours": age_hours,
        "analysis": flow_analysis,
        "suggested_endpoints": {
            "analyze_flows": "/api/v1/collection/flows/analysis",
            "manage_flows": "/api/v1/collection/flows/manage",
            "resume_flow": f"/api/v1/collection/flows/{existing_flow.flow_id}/continue",
        },
        "resolution_steps": [
            "1. Call /api/v1/collection/flows/analysis to view all existing flows and their states",
            "2. Use /api/v1/collection/flows/manage to cancel, complete, or clean up flows as needed",
            "3. Retry flow creation or resume the existing flow using the continue endpoint",
        ],
        "user_action_required": True,
    }


async def create_data_gaps_for_missing_attributes(
    db: AsyncSession,
    collection_flow_id: int,
    missing_attributes: Dict[str, List[str]],
) -> int:
    """Create data gap records for missing critical attributes.

    Args:
        db: Database session
        collection_flow_id: ID of the collection flow
        missing_attributes: Dict mapping asset_id to list of missing attribute names

    Returns:
        Number of data gaps created
    """
    # Map critical attribute names to their categories
    from app.services.collection.critical_attributes import (
        CriticalAttributesDefinition,
    )

    ATTRIBUTE_CATEGORY_MAP = CriticalAttributesDefinition.get_attribute_category_map()

    gaps_created = 0
    for asset_id_str, missing_attrs in missing_attributes.items():
        try:
            asset_uuid = uuid.UUID(asset_id_str)
        except ValueError:
            logger.warning(
                f"Invalid asset_id format in missing_attributes: {asset_id_str}"
            )
            continue

        for attr_name in missing_attrs:
            # Determine category from mapping, default to "application" if not found
            category = ATTRIBUTE_CATEGORY_MAP.get(attr_name, "application")

            gap = CollectionDataGap(
                collection_flow_id=collection_flow_id,
                asset_id=asset_uuid,
                field_name=attr_name,
                gap_type="missing_critical_attribute",
                gap_category=category,
                impact_on_sixr="high",
                priority=10,
                resolution_status="identified",
                description=f"Missing critical attribute: {attr_name}",
                suggested_resolution=f"Provide value for {attr_name} via questionnaire",
                gap_metadata={
                    "source": "assessment_readiness",
                    "is_critical": True,
                    "required_for_assessment": True,
                    "asset_id": str(asset_uuid),
                },
            )
            db.add(gap)
            gaps_created += 1

    logger.info(
        f"✅ Created {gaps_created} data gaps for {len(missing_attributes)} assets"
    )
    return gaps_created


async def initialize_background_execution_if_needed(
    db: AsyncSession,
    context: RequestContext,
    collection_flow: CollectionFlow,
    master_flow_id: uuid.UUID,
    flow_input: Dict[str, Any],
    phases_requiring_user_input: List[str],
) -> None:
    """Initialize background execution if phase doesn't require user input.

    Args:
        db: Database session
        context: Request context
        collection_flow: The collection flow being created
        master_flow_id: Master flow orchestrator ID
        flow_input: Initial flow state
        phases_requiring_user_input: List of phase values that need user input
    """
    from app.api.v1.endpoints import collection_utils

    if collection_flow.current_phase in phases_requiring_user_input:
        logger.info(
            f"⏸️  Phase '{collection_flow.current_phase}' requires user input - "
            f"skipping automatic execution for flow {collection_flow.flow_id}"
        )
        return

    logger.info(
        f"🚀 Initializing background execution for collection flow {collection_flow.flow_id}"
    )

    try:
        execution_result = await collection_utils.initialize_mfo_flow_execution(
            db=db,
            context=context,
            master_flow_id=master_flow_id,
            flow_type="collection",
            initial_state=flow_input,
        )

        if execution_result.get("status") == "failed":
            logger.error(
                f"❌ Failed to initialize background execution: "
                f"{execution_result.get('error', 'Unknown error')}"
            )
        else:
            logger.info(
                f"✅ Background execution initialized for collection flow: {execution_result}"
            )
    except Exception as exec_error:
        logger.error(f"❌ Background execution initialization failed: {exec_error}")
        # Don't fail the entire flow creation - flow is already committed


async def handle_transaction_rollback(
    db: AsyncSession, exception_type: str = "unexpected error"
) -> None:
    """Handle database transaction rollback with proper error logging.

    Args:
        db: Database session
        exception_type: Type of exception that triggered rollback
    """
    try:
        await db.rollback()
        logger.info(f"🔄 Database transaction rolled back due to {exception_type}")
    except Exception as rollback_error:
        logger.error(f"❌ Failed to rollback transaction: {rollback_error}")
