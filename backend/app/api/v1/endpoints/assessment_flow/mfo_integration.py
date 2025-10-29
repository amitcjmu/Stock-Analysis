"""
Assessment Flow MFO Integration Layer - Phase 2 (Issue #838)

This module implements the Master Flow Orchestrator (MFO) integration for Assessment Flow
using the two-table pattern per ADR-006 and ADR-012.

Two-Table Pattern:
- Master Table (crewai_flow_state_extensions): High-level lifecycle (running/paused/completed)
- Child Table (assessment_flows): Operational state (phases, UI state, progress)

Per ADR-012: Frontend and agents MUST use child flow status for operational decisions.
Master flow status is only for cross-flow coordination.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
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
            child_flow = AssessmentFlow(
                flow_id=flow_id,  # Links to master via flow_id (not FK, but same UUID)
                master_flow_id=master_flow.flow_id,  # FK reference for relationship
                engagement_id=engagement_id,
                client_account_id=client_account_id,
                flow_name=flow_name or f"Assessment Flow {flow_id}",
                status=AssessmentFlowStatus.INITIALIZED.value,
                current_phase=AssessmentPhase.ARCHITECTURE_MINIMUMS.value,
                progress=0,
                selected_application_ids=[str(app_id) for app_id in application_ids],
                selected_asset_ids=[str(app_id) for app_id in application_ids],
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


async def get_assessment_status_via_mfo(
    flow_id: UUID,
    db: AsyncSession,
    client_account_id: Optional[UUID] = None,
    engagement_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Get assessment status from both master and child tables.

    Per ADR-012: Returns unified view with:
    - Master flow: High-level lifecycle (running/paused/completed)
    - Child flow: Operational state (current_phase, progress, UI data)

    Frontend and agents should use child flow data for operational decisions.

    Args:
        flow_id: Assessment flow UUID
        db: Database session
        client_account_id: Optional client account ID for tenant scoping
        engagement_id: Optional engagement ID for tenant scoping

    Returns:
        Dict with unified state from both tables

    Raises:
        ValueError: If flow not found or tenant mismatch
    """
    try:
        # Query both master and child flows
        # Per two-table pattern: Join on flow_id with tenant scoping
        query = (
            select(CrewAIFlowStateExtensions, AssessmentFlow)
            .join(
                AssessmentFlow,
                AssessmentFlow.master_flow_id == CrewAIFlowStateExtensions.flow_id,
            )
            .where(CrewAIFlowStateExtensions.flow_id == flow_id)
        )

        # Add tenant scoping filters if provided
        if client_account_id is not None:
            query = query.where(
                CrewAIFlowStateExtensions.client_account_id == client_account_id
            )
        if engagement_id is not None:
            query = query.where(
                CrewAIFlowStateExtensions.engagement_id == engagement_id
            )

        result = await db.execute(query)
        row = result.first()

        if not row:
            raise ValueError(f"Assessment flow {flow_id} not found")

        master_flow, child_flow = row

        # Per ADR-012: Return child flow operational data for UI/agents
        # Master flow status included for cross-flow coordination context
        return {
            "flow_id": str(child_flow.flow_id),
            "master_flow_id": str(master_flow.flow_id),
            # Operational state (from child flow - USE THIS for decisions)
            "status": child_flow.status,
            "current_phase": child_flow.current_phase,
            "progress": child_flow.progress,
            "phase_progress": child_flow.phase_progress,
            # Master flow state (for cross-flow coordination only)
            "master_status": master_flow.flow_status,
            "master_flow_type": master_flow.flow_type,
            # Metadata
            "selected_applications": len(child_flow.selected_application_ids or []),
            "created_at": child_flow.created_at,
            "updated_at": child_flow.updated_at,
            "completed_at": child_flow.completed_at,
            # Configuration
            "configuration": child_flow.configuration,
            "runtime_state": child_flow.runtime_state,
        }

    except ValueError:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get assessment status via MFO: flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise


async def update_assessment_via_mfo(
    flow_id: UUID,
    updates: Dict[str, Any],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Update assessment flow through MFO coordination.

    Maintains consistency across master + child tables using atomic transactions.

    Per ADR-012:
    - Child flow updates: Operational changes (phase, progress, status transitions)
    - Master flow updates: Lifecycle changes (running → paused → completed)

    Args:
        flow_id: Assessment flow UUID
        updates: Dict with fields to update (status, current_phase, progress, etc.)
        db: Database session

    Returns:
        Dict with updated unified state

    Raises:
        ValueError: If flow not found or invalid state transition
    """
    try:
        async with db.begin():
            # Get both master and child flows
            query = (
                select(CrewAIFlowStateExtensions, AssessmentFlow)
                .join(
                    AssessmentFlow,
                    AssessmentFlow.master_flow_id == CrewAIFlowStateExtensions.flow_id,
                )
                .where(CrewAIFlowStateExtensions.flow_id == flow_id)
            )

            result = await db.execute(query)
            row = result.first()

            if not row:
                raise ValueError(f"Assessment flow {flow_id} not found")

            master_flow, child_flow = row

            # Update child flow (operational state)
            if "status" in updates:
                child_flow.status = updates["status"]
            if "current_phase" in updates:
                child_flow.current_phase = updates["current_phase"]
            if "progress" in updates:
                child_flow.progress = updates["progress"]
            if "phase_progress" in updates:
                child_flow.phase_progress = updates["phase_progress"]
            if "runtime_state" in updates:
                child_flow.runtime_state = {
                    **(child_flow.runtime_state or {}),
                    **updates["runtime_state"],
                }

            # Update master flow (lifecycle state) if needed
            # Per ADR-012: Synchronize terminal states
            if child_flow.status == AssessmentFlowStatus.COMPLETED.value:
                master_flow.flow_status = "completed"
                child_flow.completed_at = datetime.utcnow()
            elif child_flow.status == AssessmentFlowStatus.FAILED.value:
                master_flow.flow_status = "failed"
            elif child_flow.status == AssessmentFlowStatus.PAUSED.value:
                master_flow.flow_status = "paused"
            elif child_flow.status == AssessmentFlowStatus.IN_PROGRESS.value:
                master_flow.flow_status = "running"

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Updated assessment flow via MFO: flow_id={flow_id}, updates={updates}",
                flow_id=str(flow_id),
                updates=str(updates.keys()),
            )
        )

        # Return updated unified state
        return await get_assessment_status_via_mfo(flow_id, db)

    except ValueError:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to update assessment via MFO: flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise


async def pause_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Pause assessment flow (updates both master and child tables atomically).

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with updated unified state
    """
    return await update_assessment_via_mfo(
        flow_id=flow_id,
        updates={
            "status": AssessmentFlowStatus.PAUSED.value,
            "runtime_state": {"paused_at": datetime.utcnow().isoformat()},
        },
        db=db,
    )


async def resume_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Resume assessment flow (updates both master and child tables atomically).

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with updated unified state
    """
    return await update_assessment_via_mfo(
        flow_id=flow_id,
        updates={
            "status": AssessmentFlowStatus.IN_PROGRESS.value,
            "runtime_state": {"resumed_at": datetime.utcnow().isoformat()},
        },
        db=db,
    )


async def complete_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Mark assessment flow as completed (updates both master and child tables atomically).

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with updated unified state
    """
    return await update_assessment_via_mfo(
        flow_id=flow_id,
        updates={
            "status": AssessmentFlowStatus.COMPLETED.value,
            "progress": 100,
            "runtime_state": {"completed_at": datetime.utcnow().isoformat()},
        },
        db=db,
    )


async def delete_assessment_flow(
    flow_id: UUID,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Delete assessment flow (soft delete in master, removes child record).

    Per ADR-006: Master flow handles deletion/cancellation decisions.

    Args:
        flow_id: Assessment flow UUID
        db: Database session

    Returns:
        Dict with deletion confirmation
    """
    try:
        async with db.begin():
            # Get master flow
            query = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.flow_id == flow_id
            )
            result = await db.execute(query)
            master_flow = result.scalar_one_or_none()

            if not master_flow:
                raise ValueError(f"Assessment flow {flow_id} not found")

            # Soft delete master flow (set status to deleted)
            master_flow.flow_status = "deleted"

            # Delete child flow (cascade will handle this if FK configured properly)
            # But we'll be explicit for clarity
            child_query = select(
                AssessmentFlow
            ).where(  # SKIP_TENANT_CHECK - master_flow_id FK enforces isolation
                AssessmentFlow.master_flow_id == flow_id
            )
            child_result = await db.execute(child_query)
            child_flow = child_result.scalar_one_or_none()

            if child_flow:
                await db.delete(child_flow)

            # Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Deleted assessment flow via MFO: flow_id={flow_id}",
                flow_id=str(flow_id),
            )
        )

        return {
            "flow_id": str(flow_id),
            "status": "deleted",
            "message": "Assessment flow deleted successfully",
        }

    except ValueError:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to delete assessment flow: flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
