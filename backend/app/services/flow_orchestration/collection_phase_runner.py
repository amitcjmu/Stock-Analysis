"""
Collection Phase Runner - Fallback for Non-CrewAI Environments

This module provides a fallback sequential phase execution mechanism for
collection flows when CrewAI is not available or for environments that
need a simpler execution model.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.flow_contracts.interfaces import IFlowOrchestrator
from app.api.v1.endpoints.collection_utils import (
    sync_collection_child_flow_state,
    log_collection_failure,
)

# TYPE_CHECKING block for circular dependency avoidance
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


async def start_collection_phase_loop_background(
    master_flow_id: UUID,
    context: RequestContext,
    initial_state: Dict[str, Any],
    orchestrator: Optional[IFlowOrchestrator] = None,
) -> None:
    """Background task for sequential phase execution when CrewAI unavailable.

    Args:
        master_flow_id: Master flow ID
        context: Request context
        initial_state: Initial state for the flow
        orchestrator: Optional injected flow orchestrator (avoids circular import)
    """
    phases = [
        "initialization",
        "platform_detection",
        "automated_collection",
        "gap_analysis",
        "manual_collection",
    ]

    logger.info(f"Starting fallback collection phase loop for flow {master_flow_id}")

    async with AsyncSessionLocal() as db:
        try:
            # Use injected orchestrator or lazy import MFO
            if orchestrator is None:
                from app.services.master_flow_orchestrator import (  # noqa: F811
                    MasterFlowOrchestrator,
                )

                mfo = MasterFlowOrchestrator(db, context)
            else:
                mfo = orchestrator

            for phase in phases:
                logger.info(f"Executing collection phase: {phase}")

                # Use empty dict for phase_input (phases use internal state)
                result = await mfo.execute_phase(
                    flow_id=str(master_flow_id), phase_name=phase, phase_input={}
                )

                # Sync child state after each phase
                await sync_collection_child_flow_state(
                    db, context, master_flow_id, result
                )

                # Stop on failure
                if result.get("status") == "failed":
                    logger.error(f"Phase {phase} failed: {result.get('error')}")
                    # Log failure with enhanced diagnostic data
                    await log_collection_failure(
                        db=db,
                        context=context,
                        source="collection_phase_runner",
                        operation=f"phase_{phase}",
                        payload={
                            "flow_id": str(master_flow_id),
                            "phase": phase,
                            "next_phase": result.get("next_phase"),
                            "agent_decision": result.get("agent_decision"),
                        },
                        error_message=result.get("error", "Unknown error"),
                    )
                    break

                # Check if flow was cancelled or paused
                stmt = select(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.flow_id == master_flow_id
                )
                result = await db.execute(stmt)
                master_flow = result.scalar_one_or_none()

                if master_flow and master_flow.flow_status in ["cancelled", "paused"]:
                    logger.info(
                        f"Flow {master_flow_id} {master_flow.flow_status}, stopping loop"
                    )
                    break

                # Add small delay between phases to prevent overload
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Fallback loop failed for {master_flow_id}: {e}")
            # Mark collection flow as failed
            async with AsyncSessionLocal() as error_db:
                failed_result = {
                    "status": "failed",
                    "error": f"Fallback loop error: {str(e)}",
                    "phase": "unknown",
                }
                await sync_collection_child_flow_state(
                    error_db, context, master_flow_id, failed_result
                )


async def execute_collection_phase_directly(
    db: AsyncSession,
    context: RequestContext,
    master_flow_id: UUID,
    phase_name: str,
    phase_input: Optional[Dict[str, Any]] = None,
    orchestrator: Optional[IFlowOrchestrator] = None,
) -> Dict[str, Any]:
    """Execute a single collection phase directly.

    This can be used for manual phase execution or testing.

    Args:
        db: Database session
        context: Request context
        master_flow_id: Master flow ID
        phase_name: Name of the phase to execute
        phase_input: Optional phase input
        orchestrator: Optional injected flow orchestrator (avoids circular import)

    Returns:
        Phase execution result
    """
    try:
        # Use injected orchestrator or lazy import MFO
        if orchestrator is None:
            from app.services.master_flow_orchestrator import (  # noqa: F811
                MasterFlowOrchestrator,
            )

            mfo = MasterFlowOrchestrator(db, context)
        else:
            mfo = orchestrator

        result = await mfo.execute_phase(
            flow_id=str(master_flow_id),
            phase_name=phase_name,
            phase_input=phase_input or {},
        )

        # Sync child state
        await sync_collection_child_flow_state(db, context, master_flow_id, result)

        return result

    except Exception as e:
        logger.error(f"Direct phase execution failed for {phase_name}: {e}")

        # Create failure result
        failed_result = {
            "phase": phase_name,
            "status": "failed",
            "error": str(e),
            "next_phase": None,
        }

        # Sync failure state
        await sync_collection_child_flow_state(
            db, context, master_flow_id, failed_result
        )

        # Log failure
        await log_collection_failure(
            db=db,
            context=context,
            source="collection_phase_runner",
            operation=f"direct_phase_{phase_name}",
            payload={"flow_id": str(master_flow_id), "phase": phase_name},
            error_message=str(e),
        )

        return failed_result


def get_collection_phases() -> list[str]:
    """Get the standard collection flow phases in order.

    Returns:
        List of phase names in execution order
    """
    return [
        "initialization",
        "platform_detection",
        "automated_collection",
        "gap_analysis",
        "manual_collection",
    ]


async def is_collection_flow_active(db: AsyncSession, master_flow_id: UUID) -> bool:
    """Check if a collection flow is still active.

    Args:
        db: Database session
        master_flow_id: Master flow ID

    Returns:
        True if flow is active, False otherwise
    """
    stmt = select(CrewAIFlowStateExtensions).where(
        CrewAIFlowStateExtensions.flow_id == master_flow_id
    )
    result = await db.execute(stmt)
    master_flow = result.scalar_one_or_none()

    if not master_flow:
        return False

    return master_flow.flow_status not in ["completed", "failed", "cancelled", "paused"]
