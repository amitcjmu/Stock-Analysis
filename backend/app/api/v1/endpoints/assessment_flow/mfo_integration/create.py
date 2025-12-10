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


async def _find_previously_accepted_treatments(
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    application_ids: List[UUID],
) -> tuple[Dict[str, Any], List[UUID]]:
    """
    Issue #719: Find previously accepted treatments for the given applications.

    Returns:
        Tuple of (previously_accepted_treatments dict, apps_requiring_assessment list)
    """
    from sqlalchemy import select, and_

    previously_accepted_treatments: Dict[str, Any] = {}
    apps_requiring_assessment = list(application_ids)

    # Query for any previous assessment flows with accepted treatments for these apps
    stmt = select(AssessmentFlow).where(
        and_(
            AssessmentFlow.client_account_id == client_account_id,
            AssessmentFlow.engagement_id == engagement_id,
            AssessmentFlow.status == "completed",
        )
    )
    result = await db.execute(stmt)
    previous_flows = result.scalars().all()

    for prev_flow in previous_flows:
        phase_results = prev_flow.phase_results or {}
        rec_gen = phase_results.get("recommendation_generation", {})
        rec_results = rec_gen.get("results", {})
        inner_rec = rec_results.get("recommendation_generation", {})
        applications = inner_rec.get("applications", [])

        for app in applications:
            app_id_str = str(app.get("application_id", ""))
            # Check if this app was accepted (finalized)
            if app.get("is_accepted"):
                # Check if this app_id is in our requested list
                for req_app_id in application_ids:
                    if str(req_app_id) == app_id_str:
                        previously_accepted_treatments[app_id_str] = app
                        if req_app_id in apps_requiring_assessment:
                            apps_requiring_assessment.remove(req_app_id)
                        break

    return previously_accepted_treatments, apps_requiring_assessment


async def create_assessment_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    application_ids: List[UUID],
    user_id: str,
    flow_name: Optional[str],
    source_collection_id: Optional[UUID],
    db: AsyncSession,
    force_reassessment: bool = False,
) -> Dict[str, Any]:
    """
    Create assessment flow through MFO using two-table pattern.

    Steps (ADR-006):
    1. Create master flow in crewai_flow_state_extensions (lifecycle management)
    2. Create child assessment flow in assessment_flows table (operational state)
    3. Link via flow_id
    4. Return unified state

    Issue #719: If an app has a previously accepted treatment and force_reassessment=False,
    we copy the accepted treatment to the new flow instead of re-running agent analysis.

    Args:
        client_account_id: Client account UUID for multi-tenant isolation
        engagement_id: Engagement UUID for multi-tenant isolation
        application_ids: List of application UUIDs to assess
        user_id: User who initiated the flow
        flow_name: Optional name for the flow
        source_collection_id: Optional UUID of source collection flow (for Issue #861)
        db: Database session
        force_reassessment: If True, force re-assessment even for apps with accepted treatments

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

    # Issue #719: Look up previously accepted treatments for these applications
    # If force_reassessment=False, we reuse accepted treatments instead of re-running agents
    previously_accepted_treatments: Dict[str, Any] = {}
    apps_requiring_assessment = list(application_ids)

    if not force_reassessment:
        previously_accepted_treatments, apps_requiring_assessment = (
            await _find_previously_accepted_treatments(
                db, client_account_id, engagement_id, application_ids
            )
        )
        if previously_accepted_treatments:
            logger.info(
                safe_log_format(
                    "Issue #719: Found {count} apps with accepted treatments, "
                    "{remaining} apps need assessment",
                    count=len(previously_accepted_treatments),
                    remaining=len(apps_requiring_assessment),
                )
            )

    # Generate flow IDs
    flow_id = uuid4()

    try:
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

        # Issue #719: Store info about previously accepted treatments
        if previously_accepted_treatments:
            flow_metadata["previously_accepted_treatments"] = {
                app_id: {
                    "overall_strategy": treatment.get("overall_strategy"),
                    "accepted_at": treatment.get("accepted_at"),
                    "accepted_by": treatment.get("accepted_by"),
                }
                for app_id, treatment in previously_accepted_treatments.items()
            }
            flow_metadata["apps_requiring_assessment"] = [
                str(app_id) for app_id in apps_requiring_assessment
            ]
            flow_metadata["force_reassessment"] = force_reassessment

        # Issue #719: Pre-populate phase_results with previously accepted treatments
        # So when the UI loads, it shows the accepted treatments without re-running agents
        initial_phase_results = {}
        if previously_accepted_treatments:
            initial_phase_results["recommendation_generation"] = {
                "results": {
                    "recommendation_generation": {
                        "applications": [
                            treatment
                            for treatment in previously_accepted_treatments.values()
                        ],
                        "previously_accepted": True,  # Flag to indicate these are cached
                    }
                }
            }

        child_flow = AssessmentFlow(
            # AssessmentFlow uses 'id' as PK, not 'flow_id' (CodeRabbit fix)
            master_flow_id=master_flow.flow_id,  # FK reference for relationship
            engagement_id=engagement_id,
            client_account_id=client_account_id,
            flow_name=flow_name or f"Assessment Flow {flow_id}",
            status=AssessmentFlowStatus.INITIALIZED.value,
            # Per ADR-027: Use INITIALIZATION not deprecated ARCHITECTURE_MINIMUMS
            current_phase=AssessmentPhase.INITIALIZATION.value,
            progress=0,
            selected_application_ids=[str(app_id) for app_id in application_ids],
            selected_asset_ids=[str(app_id) for app_id in application_ids],
            flow_metadata=flow_metadata,  # Store source collection link
            phase_results=initial_phase_results,  # Issue #719: Pre-populate with accepted
            configuration={
                "application_count": len(application_ids),
                "auto_progression_enabled": True,
                "force_reassessment": force_reassessment,  # Issue #719
            },
            runtime_state={
                "initialized_at": datetime.utcnow().isoformat(),
            },
        )
        db.add(child_flow)

        # Step 3: Commit the transaction (FastAPI will handle rollback on error)
        await db.commit()

        # Refresh instances to get database-generated values
        await db.refresh(master_flow)
        await db.refresh(child_flow)

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
        response = {
            "flow_id": str(flow_id),
            "master_flow_id": str(master_flow.flow_id),
            "status": child_flow.status,  # Per ADR-012: Use child status for operations
            "current_phase": child_flow.current_phase,
            "progress": child_flow.progress,
            "selected_applications": len(application_ids),
            "message": "Assessment flow created through Master Flow Orchestrator",
        }

        # Issue #719: Include info about previously accepted treatments
        if previously_accepted_treatments:
            response["previously_accepted_count"] = len(previously_accepted_treatments)
            response["apps_requiring_assessment"] = len(apps_requiring_assessment)
            response["message"] = (
                f"Assessment flow created. {len(previously_accepted_treatments)} app(s) "
                f"have accepted treatments (will be reused). "
                f"{len(apps_requiring_assessment)} app(s) require assessment."
            )

        return response

    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to create assessment flow via MFO: {str_e}",
                str_e=str(e),
            )
        )
        raise
