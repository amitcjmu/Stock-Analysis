"""
Collection Flow Creation Operations
Operations for creating master flows for orphaned collection flows.
"""

import logging
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import CollectionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)


async def create_master_flow_for_orphan(
    collection_flow: CollectionFlow,
    db: AsyncSession,
    context: RequestContext,
) -> CrewAIFlowStateExtensions:
    """Create a new master flow for an orphaned collection flow.

    This handles cases where a collection flow exists without a master_flow_id,
    likely due to incomplete flow creation or data corruption.

    Args:
        collection_flow: The orphaned collection flow
        db: Database session
        context: Request context

    Returns:
        The newly created master flow

    Raises:
        HTTPException: If master flow creation fails
    """
    try:
        from datetime import datetime, timezone
        from uuid import uuid4

        # Generate new master flow ID
        master_flow_id = uuid4()

        logger.info(
            safe_log_format(
                "Creating master flow {master_flow_id} for orphaned collection flow {collection_flow_id}",
                master_flow_id=str(master_flow_id),
                collection_flow_id=str(collection_flow.flow_id),
            )
        )

        # Create master flow with collection flow's metadata
        master_flow = CrewAIFlowStateExtensions(
            flow_id=master_flow_id,
            flow_type="collection",
            flow_name=f"Recovered Collection Flow - {collection_flow.flow_name}",
            flow_status="running",  # Resume as running
            flow_configuration={
                "current_phase": collection_flow.current_phase or "initialization",
                "progress_percentage": collection_flow.progress_percentage or 0.0,
                "recovery_mode": True,
                "original_collection_flow_id": str(collection_flow.flow_id),
                "recovery_timestamp": datetime.now(timezone.utc).isoformat(),
                "automation_tier": (
                    collection_flow.automation_tier.value
                    if collection_flow.automation_tier
                    else "tier_1"
                ),
                **collection_flow.collection_config,
            },
            flow_persistence_data={
                "recovery_metadata": {
                    "recovered_at": datetime.now(timezone.utc).isoformat(),
                    "recovery_reason": "orphaned_collection_flow",
                    "original_flow_data": {
                        "flow_id": str(collection_flow.flow_id),
                        "status": (
                            collection_flow.status.value
                            if collection_flow.status
                            else "unknown"
                        ),
                        "current_phase": collection_flow.current_phase,
                        "progress_percentage": collection_flow.progress_percentage,
                    },
                },
                "collection_state": {
                    # Per ADR-028: phase_state field removed from collection_flow
                    "user_inputs": collection_flow.user_inputs,
                    "phase_results": collection_flow.phase_results,
                    "collection_results": collection_flow.collection_results,
                    "gap_analysis_results": collection_flow.gap_analysis_results,
                },
            },
            client_account_id=collection_flow.client_account_id,
            engagement_id=collection_flow.engagement_id,
            user_id=str(collection_flow.user_id or context.user_id),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Add to session and flush to get the ID
        db.add(master_flow)
        await db.flush()

        # Update collection flow with the new master_flow_id
        collection_flow.master_flow_id = master_flow.flow_id
        collection_flow.updated_at = datetime.now(timezone.utc)

        # Add recovery note to collection flow metadata
        if not collection_flow.flow_metadata:
            collection_flow.flow_metadata = {}
        collection_flow.flow_metadata["recovery_info"] = {
            "recovered_at": datetime.now(timezone.utc).isoformat(),
            "master_flow_created": str(master_flow.flow_id),
            "recovery_reason": "orphaned_flow_repair",
        }

        # Commit the transaction
        await db.commit()

        logger.info(
            safe_log_format(
                "Successfully created master flow {master_flow_id} and linked to collection flow {collection_flow_id}",
                master_flow_id=str(master_flow.flow_id),
                collection_flow_id=str(collection_flow.flow_id),
            )
        )

        return master_flow

    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to create master flow for orphaned collection flow {collection_flow_id}: {error}",
                collection_flow_id=str(collection_flow.flow_id),
                error=str(e),
            )
        )
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create master flow for orphaned collection flow: {str(e)}",
        )
