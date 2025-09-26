"""
Flow Processing Processors
Core processing functions extracted from flow_processing.py for modularization
"""

import logging
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.flow_orchestration.transition_utils import (
    get_fast_path_response,
)
from .flow_processing_converters import (
    convert_fast_path_to_api_response,
    create_simple_transition_response,
    convert_to_api_response,
    create_fallback_response,
)

logger = logging.getLogger(__name__)

# Import metrics (will be injected)
flow_metrics = None


def set_flow_metrics(metrics_instance):
    """Set the flow metrics instance for processors"""
    global flow_metrics
    flow_metrics = metrics_instance


async def _execute_data_cleansing_if_needed(
    flow_id: str,
    flow_data: dict,
    db: AsyncSession,
    context: RequestContext,
) -> None:
    """Execute data cleansing if the phase has just been set to data_cleansing"""
    if flow_data.get("current_phase") != "data_cleansing":
        return

    # Check if we need to execute data cleansing
    if flow_data.get("phase_progress", {}).get("data_cleansing", {}).get("status") in [
        "completed",
        "running",
    ]:
        logger.info(f"🔄 Data cleansing already in progress or completed for {flow_id}")
        return

    try:
        from app.services.crewai_flows.handlers.phase_executors.data_cleansing_executor import (
            DataCleansingExecutor,
        )

        logger.info(f"🧹 Executing data cleansing for flow {flow_id}")

        executor = DataCleansingExecutor()
        result = await executor.execute_phase(flow_id, context, db)

        if result.get("success"):
            logger.info(f"✅ Data cleansing completed for flow {flow_id}")
        else:
            logger.warning(f"⚠️ Data cleansing had issues for flow {flow_id}: {result}")

    except Exception as e:
        logger.error(f"❌ Error executing data cleansing for flow {flow_id}: {e}")
        # Don't fail the entire flow - just log the error


async def _handle_fast_path_processing(
    flow_id: str,
    flow_data: dict,
    validation_data: dict,
    current_phase: str,
    db: AsyncSession,
    context: RequestContext,
    start_time: float,
) -> Any:
    """Handle fast path processing logic."""
    logger.info(f"⚡ FAST PATH: Simple transition detected for {flow_id}")

    # Get fast path response without AI (< 1 second)
    fast_response = get_fast_path_response(flow_data, validation_data)

    if fast_response:
        # Import here to avoid circular dependency
        from .flow_processing.commands import _update_phase_if_needed

        # Update current_phase in database if transitioning to next phase
        await _update_phase_if_needed(
            flow_id, fast_response.get("next_phase"), current_phase, db, context
        )

        execution_time = time.time() - start_time
        logger.info(f"✅ FAST PATH COMPLETE: {flow_id} in {execution_time:.3f}s")

        # Record metrics for observability
        if flow_metrics:
            await flow_metrics.record_fast_path(execution_time)

        # Convert to proper API response format
        return convert_fast_path_to_api_response(
            fast_response, flow_data, execution_time
        )
    return None


async def _handle_simple_logic_processing(
    flow_id: str,
    flow_data: dict,
    flow_type: str,
    current_phase: str,
    db: AsyncSession,
    context: RequestContext,
    start_time: float,
) -> Any:
    """Handle simple logic processing without AI."""
    logger.info(f"🔄 SIMPLE: Basic logic processing for {flow_id}")

    simple_result = None
    execution_time = time.time() - start_time

    try:
        # Phase-specific simple logic
        if current_phase == "asset_inventory":
            # For asset inventory, check if we have assets to process
            if flow_data.get("asset_data"):
                simple_result = {
                    "success": True,
                    "message": "Asset inventory data ready",
                    "next_phase": "field_mapping",
                    "can_continue": True,
                    "simple_logic": True,
                }

        elif current_phase == "field_mapping":
            # Check if field mappings are sufficiently approved (30% threshold)
            approval_stats = flow_data.get("field_mapping_stats", {})
            total_mappings = approval_stats.get("total", 0)
            approved_mappings = approval_stats.get("approved", 0)

            if total_mappings > 0:
                approval_rate = approved_mappings / total_mappings
                if approval_rate >= 0.3:  # 30% threshold
                    simple_result = {
                        "success": True,
                        "message": f"Field mapping {approval_rate:.1%} approved (≥30%)",
                        "next_phase": "data_cleansing",
                        "can_continue": True,
                        "simple_logic": True,
                        "approval_rate": approval_rate,
                    }
                else:
                    simple_result = {
                        "success": False,
                        "message": f"Field mapping only {approval_rate:.1%} approved (<30%)",
                        "can_continue": False,
                        "simple_logic": True,
                        "approval_rate": approval_rate,
                    }

        elif current_phase == "data_cleansing":
            # Check if data cleansing is complete
            cleansing_status = flow_data.get("phase_progress", {}).get(
                "data_cleansing", {}
            )
            if cleansing_status.get("status") == "completed":
                simple_result = {
                    "success": True,
                    "message": "Data cleansing completed",
                    "next_phase": "dependency_analysis",
                    "can_continue": True,
                    "simple_logic": True,
                }

        # If we have a simple result, process it
        if simple_result:
            # Import here to avoid circular dependency
            from .flow_processing.commands import _update_phase_if_needed

            # Update phase if transitioning
            if simple_result.get("next_phase"):
                await _update_phase_if_needed(
                    flow_id, simple_result["next_phase"], current_phase, db, context
                )

            # Execute data cleansing if we just moved to that phase
            if simple_result.get("next_phase") == "data_cleansing":
                await _execute_data_cleansing_if_needed(flow_id, flow_data, db, context)

            logger.info(f"✅ SIMPLE LOGIC COMPLETE: {flow_id} in {execution_time:.3f}s")

            # Record metrics
            if flow_metrics:
                await flow_metrics.record_simple_logic(execution_time)

            return create_simple_transition_response(
                simple_result, flow_data, execution_time
            )

    except Exception as e:
        logger.error(f"❌ Simple logic processing failed for {flow_id}: {e}")
        # Fall through to return None, which will trigger AI processing

    return None


async def _handle_ai_processing(
    flow_id: str,
    flow_data: dict,
    flow_type: str,
    current_phase: str,
    db: AsyncSession,
    context: RequestContext,
    start_time: float,
) -> Any:
    """Handle AI processing with intelligent agents."""
    logger.info(f"🧠 AI: Intelligent processing for {flow_id}")

    try:
        # Import here to avoid circular imports
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )

        # Get tenant-scoped agent pool (ADR-015)
        agent_pool = TenantScopedAgentPool(context.client_account_id)
        flow_agent = await agent_pool.get_agent("flow_processing")

        if not flow_agent:
            logger.error(
                f"❌ No flow processing agent available for tenant {context.client_account_id}"
            )
            raise Exception("Flow processing agent not available")

        # Create agent input
        agent_input = {
            "flow_id": flow_id,
            "flow_data": flow_data,
            "flow_type": flow_type,
            "current_phase": current_phase,
            "context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_id": getattr(context, "user_id", None),
            },
        }

        # Execute agent
        agent_result = await flow_agent.process_flow_continuation(agent_input)
        execution_time = time.time() - start_time

        logger.info(f"✅ AI PROCESSING COMPLETE: {flow_id} in {execution_time:.3f}s")

        # Record metrics
        if flow_metrics:
            await flow_metrics.record_ai_processing(execution_time)

        # Convert agent result to API response
        return convert_to_api_response(agent_result, flow_data, execution_time)

    except Exception as e:
        logger.error(f"❌ AI processing failed for {flow_id}: {e}")
        execution_time = time.time() - start_time

        # Return structured fallback response
        return create_fallback_response(flow_data, str(e), execution_time)
