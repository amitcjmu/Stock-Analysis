"""
Assessment Flow MFO Integration - Query Operations

Handles read operations for assessment flows through Master Flow Orchestrator.
Part of modularized mfo_integration per pre-commit file length requirement.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


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
