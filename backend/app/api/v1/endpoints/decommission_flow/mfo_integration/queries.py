"""
Decommission Flow MFO Integration - Query Operations

Handles read operations for decommission flows through Master Flow Orchestrator.
Part of modularized mfo_integration per pre-commit file length requirement.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decommission_flow import DecommissionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


async def get_decommission_status_via_mfo(
    flow_id: UUID,
    db: AsyncSession,
    client_account_id: Optional[UUID] = None,
    engagement_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    Get decommission status from both master and child tables.

    Per ADR-012: Returns unified view with:
    - Master flow: High-level lifecycle (running/paused/completed)
    - Child flow: Operational state (current_phase, progress, UI data)

    Frontend and agents should use child flow data for operational decisions.

    CRITICAL: This function returns child flow status as the primary operational state,
    with master flow status included for cross-flow coordination only.

    Args:
        flow_id: Decommission flow UUID
        db: Database session
        client_account_id: Optional client account ID for tenant scoping
        engagement_id: Optional engagement ID for tenant scoping

    Returns:
        Dict with unified state from both tables

    Raises:
        ValueError: If flow not found or tenant mismatch
        SQLAlchemyError: If database operations fail
    """
    try:
        # Query both master and child flows
        # Per two-table pattern: Join on flow_id with tenant scoping
        query = (
            select(CrewAIFlowStateExtensions, DecommissionFlow)
            .join(
                DecommissionFlow,
                DecommissionFlow.master_flow_id == CrewAIFlowStateExtensions.flow_id,
            )
            .where(CrewAIFlowStateExtensions.flow_id == flow_id)
        )

        # Add tenant scoping filters if provided (multi-tenant security)
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
            raise ValueError(f"Decommission flow {flow_id} not found")

        master_flow, child_flow = row

        # Per ADR-012: Return child flow operational data for UI/agents
        # Master flow status included for cross-flow coordination context
        return {
            "flow_id": str(child_flow.flow_id),
            "master_flow_id": str(master_flow.flow_id),
            # Operational state (from child flow - USE THIS for decisions)
            "status": child_flow.status,
            "current_phase": child_flow.current_phase,
            "phase_progress": {
                "decommission_planning": {
                    "status": child_flow.decommission_planning_status,
                    "completed_at": (
                        child_flow.decommission_planning_completed_at.isoformat()
                        if child_flow.decommission_planning_completed_at
                        else None
                    ),
                },
                "data_migration": {
                    "status": child_flow.data_migration_status,
                    "completed_at": (
                        child_flow.data_migration_completed_at.isoformat()
                        if child_flow.data_migration_completed_at
                        else None
                    ),
                },
                "system_shutdown": {
                    "status": child_flow.system_shutdown_status,
                    "started_at": (
                        child_flow.system_shutdown_started_at.isoformat()
                        if child_flow.system_shutdown_started_at
                        else None
                    ),
                    "completed_at": (
                        child_flow.system_shutdown_completed_at.isoformat()
                        if child_flow.system_shutdown_completed_at
                        else None
                    ),
                },
            },
            # Master flow state (for cross-flow coordination only)
            "master_status": master_flow.flow_status,
            "master_flow_type": master_flow.flow_type,
            # Metadata
            "selected_systems": len(child_flow.selected_system_ids or []),
            "system_count": child_flow.system_count,
            "created_at": child_flow.created_at,
            "updated_at": child_flow.updated_at,
            # Configuration
            "decommission_strategy": child_flow.decommission_strategy,
            "runtime_state": child_flow.runtime_state,
            # Metrics
            "total_systems_decommissioned": child_flow.total_systems_decommissioned,
            "estimated_annual_savings": (
                float(child_flow.estimated_annual_savings)
                if child_flow.estimated_annual_savings
                else None
            ),
            "compliance_score": child_flow.compliance_score,
        }

    except ValueError:
        # Re-raise flow not found errors
        raise
    except SQLAlchemyError as e:
        logger.error(
            safe_log_format(
                "Database error getting decommission status via MFO: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get decommission status via MFO: "
                "flow_id={flow_id}, error={str_e}",
                flow_id=str(flow_id),
                str_e=str(e),
            )
        )
        raise
