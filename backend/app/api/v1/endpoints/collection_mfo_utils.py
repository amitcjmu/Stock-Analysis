"""
Collection Master Flow Orchestrator Utilities
MFO integration utilities for collection flows including flow creation,
execution, resumption, deletion, and state synchronization.
"""

import asyncio
import logging
import os
from typing import Any, Dict, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.api.v1.endpoints.collection_status_utils import determine_next_phase_status
from app.api.v1.endpoints.collection_validation_utils import log_collection_failure

logger = logging.getLogger(__name__)


async def create_mfo_flow(
    db: AsyncSession,
    context: RequestContext,
    flow_type: str,
    initial_state: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    """Create a flow through Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_type: Type of flow to create
        initial_state: Initial state for the flow

    Returns:
        Tuple of (master_flow_id, master_flow_data)

    Raises:
        Exception: If flow creation fails
    """
    mfo = MasterFlowOrchestrator(db, context)
    return await mfo.create_flow(flow_type=flow_type, initial_state=initial_state)


async def execute_mfo_phase(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    phase_name: str,
    phase_input: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute a phase through Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow ID to execute
        phase_name: Name of phase to execute
        phase_input: Input data for the phase

    Returns:
        Execution result

    Raises:
        Exception: If execution fails
    """
    mfo = MasterFlowOrchestrator(db, context)
    return await mfo.execute_phase(
        flow_id=flow_id, phase_name=phase_name, phase_input=phase_input
    )


async def resume_mfo_flow(
    db: AsyncSession,
    context: RequestContext,
    flow_id: str,
    resume_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Resume a flow through Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow ID to resume
        resume_context: Context for resuming the flow

    Returns:
        Resume result

    Raises:
        Exception: If resume fails
    """
    mfo = MasterFlowOrchestrator(db, context)
    return await mfo.resume_flow(flow_id=flow_id, resume_context=resume_context)


async def delete_mfo_flow(
    db: AsyncSession, context: RequestContext, flow_id: str
) -> None:
    """Delete a flow from Master Flow Orchestrator.

    Args:
        db: Database session
        context: Request context
        flow_id: Flow ID to delete

    Note:
        This is best-effort and logs warnings on failure
    """
    try:
        mfo = MasterFlowOrchestrator(db, context)
        await mfo.delete_flow(flow_id)
    except Exception as e:
        logger.warning(
            safe_log_format(
                "MFO deletion failed for flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )


async def initialize_mfo_flow_execution(
    db: AsyncSession,
    context: RequestContext,
    master_flow_id: UUID,
    flow_type: str,
    initial_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Initialize background flow execution with idempotency check.

    Args:
        db: Database session
        context: Request context
        master_flow_id: Master flow ID (UUID type)
        flow_type: Type of flow to initialize
        initial_state: Initial state for the flow

    Returns:
        Initialization result
    """
    # Feature flag for staged rollout (optional)
    if not os.getenv("ENABLE_BACKGROUND_COLLECTION", "true").lower() == "true":
        logger.info("Background collection disabled by feature flag")
        return {"status": "skipped", "flow_id": str(master_flow_id)}

    # Check if already running (NOT "initialized")
    stmt = select(CrewAIFlowStateExtensions).where(
        CrewAIFlowStateExtensions.flow_id == master_flow_id,
        CrewAIFlowStateExtensions.flow_status.in_(["initializing", "running"]),
    )
    result = await db.execute(stmt)
    master_flow = result.scalar_one_or_none()

    if master_flow:
        logger.info("Flow %s already running, skipping duplicate start", master_flow_id)
        return {"status": "already_running", "flow_id": str(master_flow_id)}

    try:
        logger.info(
            "🚀 Starting MFO background execution for %s flow %s",
            flow_type,
            master_flow_id,
        )

        # Initialize MFO with detailed logging
        mfo = MasterFlowOrchestrator(db, context)
        logger.info("✅ MasterFlowOrchestrator created successfully")

        # Check if execution engine is available
        if not hasattr(mfo, "execution_engine") or mfo.execution_engine is None:
            raise RuntimeError("MFO execution engine not initialized")

        logger.info("✅ MFO execution engine available")

        # Initialize flow execution with comprehensive error context
        result = await mfo.execution_engine.initialize_flow_execution(
            flow_id=str(master_flow_id),
            flow_type=flow_type,
            initial_state=initial_state,
        )

        logger.info("✅ MFO flow execution initialized successfully: %s", result)
        return result

    except ImportError as e:
        logger.warning("CrewAI not available, using fallback loop: %s", e)
        try:
            from app.services.flow_orchestration.collection_phase_runner import (
                start_collection_phase_loop_background,
            )

            # Create MFO instance to inject into fallback runner
            mfo = MasterFlowOrchestrator(db, context)

            asyncio.create_task(
                start_collection_phase_loop_background(
                    master_flow_id, context, initial_state, orchestrator=mfo
                )
            )
            logger.info(
                "✅ Fallback collection phase loop started for flow %s", master_flow_id
            )
            return {"status": "started_fallback", "flow_id": str(master_flow_id)}

        except Exception as fallback_error:
            logger.error("❌ Fallback execution also failed: %s", fallback_error)
            return {
                "status": "failed",
                "flow_id": str(master_flow_id),
                "error": f"Both MFO and fallback execution failed: {str(fallback_error)}",
            }

    except RuntimeError as e:
        logger.error(
            "❌ MFO runtime error for flow %s: %s", master_flow_id, e, exc_info=True
        )
        return {
            "status": "failed",
            "flow_id": str(master_flow_id),
            "error": f"MFO runtime error: {str(e)}",
            "error_type": "RuntimeError",
        }

    except Exception as e:
        logger.error(
            "❌ Unexpected error initializing MFO flow execution for %s: %s: %s",
            master_flow_id,
            type(e).__name__,
            e,
        )
        # Log only metadata-safe context; do not log initial_state keys or sensitive identifiers
        logger.error(
            "❌ Flow init failed. Flow type: %s",
            flow_type,
        )

        # Return error details instead of silently failing
        return {
            "status": "failed",
            "flow_id": str(master_flow_id),
            "error": f"Flow execution initialization failed: {type(e).__name__}: {str(e)}",
            "error_type": type(e).__name__,
            "flow_type": flow_type,
        }


async def sync_collection_child_flow_state(
    db: AsyncSession,
    context: RequestContext,
    master_flow_id: UUID,
    phase_result: Dict[str, Any],
) -> None:
    """Sync child collection flow from master phase result with phase mapping.

    Args:
        db: Database session
        context: Request context
        master_flow_id: Master flow ID
        phase_result: Phase execution result
    """
    # Multi-tenant scoped query using async pattern
    stmt = select(CollectionFlow).where(
        CollectionFlow.master_flow_id == master_flow_id,
        CollectionFlow.client_account_id == context.client_account_id,
        CollectionFlow.engagement_id == context.engagement_id,
    )
    result = await db.execute(stmt)
    collection_flow = result.scalar_one_or_none()

    if not collection_flow:
        logger.warning(f"No collection flow found for master {master_flow_id}")
        return

    # Map registry phases to child model phases
    phase_mapping = {
        "synthesis": "finalization",
        "manual_collection": "manual_collection",
        "platform_detection": "platform_detection",
        "automated_collection": "automated_collection",
        "gap_analysis": "gap_analysis",
        "initialization": "initialization",
    }

    next_phase = phase_result.get("next_phase")

    # Handle completion and phase transitions
    if phase_result.get("status") == "completed" and not next_phase:
        # CRITICAL FIX (Issue #1066): Check current phase before marking flow COMPLETED
        # Phases like questionnaire_generation require user input and should PAUSE, not COMPLETE
        user_input_phases = [
            "asset_selection",
            "questionnaire_generation",
            "manual_collection",
        ]

        if collection_flow.current_phase in user_input_phases:
            # Phase execution completed, but flow needs user input - PAUSE it
            collection_flow.status = CollectionFlowStatus.PAUSED.value
            logger.info(
                f"Collection flow {collection_flow.flow_id} phase completed - "
                f"PAUSED at {collection_flow.current_phase} (user input required)"
            )
        else:
            # Flow completed successfully (e.g., reached finalization)
            collection_flow.status = CollectionFlowStatus.COMPLETED.value
            collection_flow.current_phase = "finalization"
            logger.info(f"Collection flow {collection_flow.flow_id} completed")

    elif next_phase:
        # Transition to next phase
        mapped_phase = phase_mapping.get(next_phase, next_phase)
        collection_flow.current_phase = mapped_phase
        collection_flow.status = determine_next_phase_status(
            mapped_phase, collection_flow.status
        )

    elif phase_result.get("status") == "failed":
        # Handle failure
        collection_flow.error_message = phase_result.get(
            "error", "Phase execution failed"
        )
        collection_flow.status = CollectionFlowStatus.FAILED.value

        # Enhanced logging for triage
        await log_collection_failure(
            db=db,
            context=context,
            source="sync_child_flow",
            operation="phase_failed",
            payload={
                "flow_id": str(collection_flow.flow_id),
                "phase": phase_result.get("phase"),
                "next_phase": phase_result.get("next_phase"),
                "agent_decision": phase_result.get("agent_decision"),
            },
            error_message=collection_flow.error_message,
        )

    # ✅ FIX Bug #8 (SQLAlchemy greenlet_spawn error):
    # Use __dict__ to avoid lazy-loading current_phase in background tasks
    # This prevents: "greenlet_spawn has not been called; can't call await_only() here"
    try:
        # Access current_phase directly from __dict__ to avoid lazy load
        current_phase = collection_flow.__dict__.get("current_phase", None)
        if current_phase:
            phase_weights = {
                "initialization": 0,
                "asset_selection": 15,
                "gap_analysis": 40,
                "questionnaire_generation": 60,
                "manual_collection": 80,
                "data_validation": 95,
                "finalization": 100,
            }
            collection_flow.progress_percentage = phase_weights.get(current_phase, 0.0)
    except Exception as e:
        logger.warning(f"Failed to update progress (non-critical): {e}")
        # Fallback to 0 progress
        collection_flow.progress_percentage = 0.0

    await db.commit()
