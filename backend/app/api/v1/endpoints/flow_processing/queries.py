"""
Flow Processing Queries
Read operations and status queries for flow processing
"""

import logging
import time
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.flow_orchestration.transition_utils import (
    is_simple_transition,
    needs_ai_analysis,
)
from app.services.agents.agent_service_layer.handlers.flow_handler import FlowHandler

from .base import FlowProcessingMetrics
from .commands import (
    _execute_data_cleansing_if_needed,
    _handle_fast_path_processing,
    _handle_simple_logic_processing,
    _handle_ai_processing,
    _validate_flow_phase,
)
from ..flow_processing_models import (
    FlowContinuationRequest,
    FlowContinuationResponse,
)
from ..flow_processing_converters import create_fallback_response

logger = logging.getLogger(__name__)


async def process_flow_continuation(
    flow_id: str,
    request: FlowContinuationRequest,
    context: RequestContext,
    db: AsyncSession,
    flow_metrics: FlowProcessingMetrics,
) -> FlowContinuationResponse:
    """
    Optimized flow processing with fast path detection

    FAST PATH (< 1 second): Simple phase transitions without AI
    INTELLIGENT PATH (when needed): AI analysis for complex scenarios

    Performance goals:
    - Simple transitions: < 1 second response time
    - AI-required scenarios: Only when needed (field mapping, errors, etc.)
    - Uses TenantScopedAgentPool (ADR-015) for persistent agents
    """
    start_time = time.time()

    try:
        logger.info(f"🚀 OPTIMIZED FLOW PROCESSING: Starting for {flow_id}")

        # Step 1: Get flow status using FlowHandler
        flow_handler = FlowHandler(context)
        flow_status_result = await flow_handler.get_flow_status(flow_id)

        if not flow_status_result.get("flow_exists", False):
            logger.warning(f"Flow not found: {flow_id}")
            return create_fallback_response(flow_id, "Flow not found")

        flow_data = flow_status_result.get("flow", {})
        current_phase = flow_data.get("current_phase", "data_import")
        flow_type = flow_data.get("flow_type", "discovery")

        # Step 2: Derive validation from actual flow completion data
        validation_data = _validate_flow_phase(flow_data, flow_type)

        # Step 2.5: Resume flow if it's paused (e.g., after field mapping approval)
        flow_status = flow_data.get("status", "")
        if flow_status == "paused":
            await _resume_paused_flow(flow_id, flow_data, db, context)
            flow_data["status"] = "active"  # Update local copy

        # Step 3: Execute data cleansing if needed
        updated_flow_data, updated_validation_data = (
            await _execute_data_cleansing_if_needed(
                flow_id, flow_type, current_phase, request, db, context, flow_handler
            )
        )

        # Use updated data if cleansing was executed
        if updated_flow_data:
            flow_data = updated_flow_data
            validation_data = updated_validation_data

        # Step 4: DISABLE fast path for discovery flows - always ensure proper execution
        # Fast path was causing phases to be skipped without actual execution
        disable_fast_path = flow_type == "discovery"
        if not disable_fast_path and is_simple_transition(flow_data, validation_data):
            result = await _handle_fast_path_processing(
                flow_id,
                flow_data,
                validation_data,
                current_phase,
                db,
                context,
                start_time,
                flow_metrics,
            )
            if result:
                return result

        # Step 5: Check if AI analysis is actually needed
        requires_ai, ai_reason = needs_ai_analysis(flow_data, validation_data)

        if not requires_ai:
            return await _handle_simple_logic_processing(
                flow_id,
                flow_data,
                flow_type,
                current_phase,
                db,
                context,
                start_time,
                flow_metrics,
            )

        # Step 6: AI analysis is needed
        return await _handle_ai_processing(
            flow_id, context, start_time, flow_metrics, db, current_phase
        )

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            f"❌ FLOW PROCESSING ERROR: {flow_id} failed after "
            f"{execution_time:.3f}s - {str(e)}"
        )

        # Record error metrics
        await flow_metrics.record_error(execution_time)

        return create_fallback_response(flow_id, f"Processing failed: {str(e)}")


async def _resume_paused_flow(
    flow_id: str, flow_data: dict, db: AsyncSession, context: RequestContext
) -> None:
    """Resume a paused flow by updating both discovery_flows AND crewai_flow_state_extensions"""
    from datetime import datetime

    logger.info(f"🔄 Resuming paused flow {flow_id} for phase transition")

    from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
    from app.repositories.crewai_flow_state_extensions_repository import (
        CrewAIFlowStateExtensionsRepository,
    )

    # Update discovery_flows table
    flow_repo = DiscoveryFlowRepository(
        db, context.client_account_id, context.engagement_id
    )
    await flow_repo.update_flow_status(flow_id, "active")

    # Also update master flow status to ensure consistency
    # Get the master_flow_id from discovery flow
    discovery_flow = await flow_repo.get_by_flow_id(flow_id)
    if discovery_flow and discovery_flow.master_flow_id:
        master_repo = CrewAIFlowStateExtensionsRepository(
            db, context.client_account_id, context.engagement_id
        )
        await master_repo.update_flow_status(
            flow_id=str(discovery_flow.master_flow_id),
            flow_status="running",
            metadata={"resumed_at": datetime.utcnow().isoformat()},
        )
        logger.info(
            f"✅ Updated master flow {discovery_flow.master_flow_id} to running"
        )

    logger.info(f"✅ Flow {flow_id} resumed from paused state in both tables")


async def get_flow_processing_metrics(
    flow_metrics: FlowProcessingMetrics,
) -> Dict[str, Any]:
    """
    Get flow processing performance metrics (FIX for Issue #9)

    Returns statistics on fast-path vs AI-path usage and latencies
    """
    stats = await flow_metrics.get_stats()

    # Log current performance stats
    if stats["total_requests"] > 0:
        logger.info(
            f"📊 PERFORMANCE METRICS: "
            f"Total: {stats['total_requests']}, "
            f"Fast Path: {stats['fast_path']['percentage']:.1f}%, "
            f"Simple Logic: {stats['simple_logic']['percentage']:.1f}%, "
            f"AI Path: {stats['ai_path']['percentage']:.1f}%, "
            f"Fast P95: {stats['fast_path']['p95_latency']:.3f}s, "
            f"AI P95: {stats['ai_path']['p95_latency']:.3f}s"
        )

    return stats
