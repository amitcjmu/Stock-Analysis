"""
Decommission Flow MFO Integration - Creation Operations

Handles creation of decommission flows through Master Flow Orchestrator.
Part of modularized mfo_integration per pre-commit file length requirement.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decommission_flow import DecommissionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


async def create_decommission_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    system_ids: List[UUID],
    user_id: str,
    flow_name: Optional[str],
    decommission_strategy: Optional[Dict[str, Any]],
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Create decommission flow through MFO using two-table pattern.

    Steps (ADR-006):
    1. Create master flow in crewai_flow_state_extensions (lifecycle management)
    2. Create child decommission flow in decommission_flows table (operational state)
    3. Link via flow_id
    4. Return unified state

    CRITICAL: This function uses an atomic transaction to ensure both master and child
    flows are created together or rolled back on failure.

    Args:
        client_account_id: Client account UUID for multi-tenant isolation
        engagement_id: Engagement UUID for multi-tenant isolation
        system_ids: List of Asset UUIDs to decommission
        user_id: User who initiated the flow
        flow_name: Optional name for the flow
        decommission_strategy: Optional strategy configuration
        db: Database session

    Returns:
        Dict with flow_id, master_flow_id, status, and initial phase

    Raises:
        ValueError: If system_ids is empty or exceeds limits
        SQLAlchemyError: If database operations fail
    """
    # Validate inputs
    if not system_ids:
        raise ValueError("At least one system ID is required for decommission")

    if len(system_ids) > 100:
        raise ValueError("Cannot decommission more than 100 systems at once")

    # Generate flow ID (same for both master and child)
    flow_id = uuid4()

    try:
        # ATOMIC TRANSACTION: Both master and child created together
        async with db.begin():
            # Step 1: Create master flow in crewai_flow_state_extensions
            # Per ADR-006: Master flow is the single source of truth for lifecycle
            master_flow = CrewAIFlowStateExtensions(
                flow_id=flow_id,
                flow_type="decommission",
                flow_name=flow_name or f"Decommission Flow {flow_id}",
                flow_status="running",  # High-level lifecycle status
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                flow_configuration={
                    "system_count": len(system_ids),
                    "created_via": "decommission_flow_api",
                    "mfo_integrated": True,
                    "strategy": decommission_strategy or {},
                },
                flow_persistence_data={},
            )
            db.add(master_flow)

            # Flush to make master_flow.flow_id available for foreign key
            await db.flush()

            # Step 2: Create child decommission flow in decommission_flows table
            # Per ADR-012: Child flow contains operational state for UI and agents
            child_flow = DecommissionFlow(
                flow_id=flow_id,  # Links to master via flow_id (not FK, but same UUID)
                master_flow_id=master_flow.flow_id,  # FK reference for relationship
                engagement_id=engagement_id,
                client_account_id=client_account_id,
                flow_name=flow_name or f"Decommission Flow {flow_id}",
                created_by=user_id,
                status="initialized",  # Child operational status
                current_phase="decommission_planning",  # First phase per ADR-027
                selected_system_ids=system_ids,
                system_count=len(system_ids),
                decommission_strategy=decommission_strategy or {},
                runtime_state={
                    "initialized_at": datetime.utcnow().isoformat(),
                    "current_agent": None,
                },
                # Phase status tracking (per ADR-027 FlowTypeConfig)
                decommission_planning_status="pending",
                data_migration_status="pending",
                system_shutdown_status="pending",
            )
            db.add(child_flow)

            # Step 3: Transaction commits automatically on context exit

        logger.info(
            safe_log_format(
                "Created decommission flow via MFO: flow_id={flow_id}, "
                "client={client_id}, systems={system_count}",
                flow_id=str(flow_id),
                client_id=str(client_account_id),
                system_count=len(system_ids),
            )
        )

        # Step 4: Return unified state
        return {
            "flow_id": str(flow_id),
            "master_flow_id": str(master_flow.flow_id),
            "status": child_flow.status,  # Per ADR-012: Use child status for operations
            "current_phase": child_flow.current_phase,
            "selected_systems": len(system_ids),
            "message": "Decommission flow created through Master Flow Orchestrator",
        }

    except ValueError:
        # Re-raise validation errors without logging
        raise
    except SQLAlchemyError as e:
        logger.error(
            safe_log_format(
                "Database error creating decommission flow via MFO: {str_e}",
                str_e=str(e),
            )
        )
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to create decommission flow via MFO: {str_e}",
                str_e=str(e),
            )
        )
        raise
