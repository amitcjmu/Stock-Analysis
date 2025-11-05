"""
Assessment Flow MFO Integration - Creation Operations

Handles creation of assessment flows through Master Flow Orchestrator.
Part of modularized mfo_integration per pre-commit file length requirement.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import (
    AssessmentFlow,
    AssessmentFlowStatus,
    AssessmentPhase,
)
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


async def create_assessment_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    application_ids: List[UUID],
    user_id: str,
    flow_name: Optional[str],
    source_collection_id: Optional[UUID],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Create assessment flow through MFO using two-table pattern.

    Steps (ADR-006):
    1. Create master flow in crewai_flow_state_extensions (lifecycle management)
    2. Create child assessment flow in assessment_flows table (operational state)
    3. Link via flow_id
    4. Return unified state

    Args:
        client_account_id: Client account UUID for multi-tenant isolation
        engagement_id: Engagement UUID for multi-tenant isolation
        application_ids: List of application UUIDs to assess
        user_id: User who initiated the flow
        flow_name: Optional name for the flow
        source_collection_id: Optional UUID of source collection flow (for Issue #861)
        db: Database session

    Returns:
        Dict with flow_id, master_flow_id, status, and initial phase

    Raises:
        ValueError: If application_ids is empty or exceeds limits
        HTTPException: If database operations fail
    """
    # Validate inputs
    if not application_ids:
        raise ValueError("At least one application ID is required")

    if len(application_ids) > 100:
        raise ValueError("Cannot assess more than 100 applications at once")

    # Generate flow IDs
    flow_id = uuid4()

    try:
        async with db.begin():
            # Step 1: Create master flow in crewai_flow_state_extensions
            # Per ADR-006: Master flow is the single source of truth for lifecycle
            master_flow = CrewAIFlowStateExtensions(
                flow_id=flow_id,
                flow_type="assessment",
                flow_name=flow_name or f"Assessment Flow {flow_id}",
                flow_status="running",  # High-level lifecycle status
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                flow_configuration={
                    "application_count": len(application_ids),
                    "created_via": "assessment_flow_api",
                    "mfo_integrated": True,
                },
                flow_persistence_data={},
            )
            db.add(master_flow)

            # Flush to make master_flow.flow_id available for foreign key
            await db.flush()

            # Step 2: Create child assessment flow in assessment_flows table
            # Per ADR-012: Child flow contains operational state for UI and agents

            # Build flow_metadata (Issue #861: Store source_collection for app loading)
            flow_metadata = {}
            if source_collection_id:
                flow_metadata["source_collection"] = {
                    "collection_flow_id": str(source_collection_id),
                    "linked_at": datetime.utcnow().isoformat(),
                }

            child_flow = AssessmentFlow(
                # AssessmentFlow uses 'id' as PK, not 'flow_id' (CodeRabbit fix)
                master_flow_id=master_flow.flow_id,  # FK reference for relationship
                engagement_id=engagement_id,
                client_account_id=client_account_id,
                flow_name=flow_name or f"Assessment Flow {flow_id}",
                status=AssessmentFlowStatus.INITIALIZED.value,
                current_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS.value,
                progress=0,
                selected_application_ids=[str(app_id) for app_id in application_ids],
                selected_asset_ids=[str(app_id) for app_id in application_ids],
                flow_metadata=flow_metadata,  # Store source collection link
                configuration={
                    "application_count": len(application_ids),
                    "auto_progression_enabled": True,
                },
                runtime_state={
                    "initialized_at": datetime.utcnow().isoformat(),
                },
            )
            db.add(child_flow)

            # Step 3: Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Created assessment flow via MFO: flow_id={flow_id}, "
                "client={client_id}, apps={app_count}",
                flow_id=str(flow_id),
                client_id=str(client_account_id),
                app_count=len(application_ids),
            )
        )

        # Step 4: Return unified state
        return {
            "flow_id": str(flow_id),
            "master_flow_id": str(master_flow.flow_id),
            "status": child_flow.status,  # Per ADR-012: Use child status for operations
            "current_phase": child_flow.current_phase,
            "progress": child_flow.progress,
            "selected_applications": len(application_ids),
            "message": "Assessment flow created through Master Flow Orchestrator",
        }

    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to create assessment flow via MFO: {str_e}",
                str_e=str(e),
            )
        )
        raise
