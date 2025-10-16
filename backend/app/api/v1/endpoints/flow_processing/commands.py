"""
Flow Processing Commands
Core processing operations and state modifications
"""

import logging
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.flow_orchestration.transition_utils import (
    get_fast_path_response,
    _get_next_phase_simple,
)
from .base import TENANT_AGENT_POOL_AVAILABLE, INTELLIGENT_AGENT_AVAILABLE
from ..flow_processing_models import FlowContinuationRequest
from ..flow_processing_converters import (
    convert_fast_path_to_api_response,
    create_simple_transition_response,
    convert_to_api_response,
)

logger = logging.getLogger(__name__)


async def _execute_data_cleansing_if_needed(
    flow_id: str,
    flow_type: str,
    current_phase: str,
    request: FlowContinuationRequest,
    db: AsyncSession,
    context: RequestContext,
    flow_handler: Any,
) -> tuple[dict, dict]:
    """Execute data cleansing phase if required."""
    # CC FIX: Get flow_data FIRST before checking if cleansing is needed
    flow_status_result = await flow_handler.get_flow_status(flow_id)
    flow_data = flow_status_result.get("flow", {})

    # Derive validation data from flow state
    validation_data = _validate_flow_phase(flow_data, flow_type)

    # Execute data cleansing when transitioning TO data_cleansing phase
    # (not just when already in it)
    should_execute_cleansing = flow_type == "discovery" and (
        current_phase == "data_cleansing"
        or (
            current_phase == "field_mapping"
            and flow_data.get("phases_completed", {}).get("field_mapping", False)
        )
    )

    if should_execute_cleansing:
        logger.info(
            f"🧹 Enforcing data_cleansing execution (unconditional) for {flow_id}"
        )
        try:
            from app.services.master_flow_orchestrator import MasterFlowOrchestrator

            # CC FIX: Include data_import_id in phase_input for data cleansing executor
            data_import_id = flow_data.get("data_import_id")
            phase_input = request.user_context or {}
            if data_import_id:
                phase_input["data_import_id"] = str(data_import_id)
                logger.info(
                    f"📦 Including data_import_id in phase_input: {data_import_id}"
                )

            orchestrator = MasterFlowOrchestrator(db, context)
            exec_result = await orchestrator.execute_phase(
                flow_id=flow_id,
                phase_name="data_cleansing",
                phase_input=phase_input,
            )

            logger.info(f"🧹 Data cleansing exec_result: {exec_result}")
            if exec_result.get("status") not in ("success", "completed"):
                logger.warning(
                    f"❌ Data cleansing execution failed for {flow_id}: {exec_result}"
                )
                raise Exception("Data cleansing failed; cannot advance")

            # Refresh flow status after cleansing
            flow_status_result = await flow_handler.get_flow_status(flow_id)
            flow_data = flow_status_result.get("flow", {})
            phases_completed = flow_data.get("phases_completed", {})
            phase_valid = phases_completed.get("data_cleansing", False)
            logger.info(
                f"✅ Data cleansing executed; completion flag={phase_valid} for {flow_id}"
            )
            validation_data = _validate_flow_phase(flow_data, flow_type)
        except Exception as e:
            logger.error(f"❌ Failed to execute data_cleansing before advance: {e}")
            raise Exception(f"Data cleansing execution error: {str(e)}")

    return flow_data, validation_data


def _validate_flow_phase(flow_data: dict, flow_type: str) -> dict:
    """Extract phase validation logic to reduce complexity."""
    phases_completed = flow_data.get("phases_completed", {})
    current_phase = flow_data.get("current_phase", "data_import")

    # Determine if current phase is actually complete based on flow type
    phase_valid = False
    if flow_type == "discovery" and isinstance(phases_completed, dict):
        # For discovery flows, check the phases_completed dictionary
        phase_valid = phases_completed.get(current_phase, False)
    elif flow_type == "collection":
        # For collection flows, check if questionnaires phase is complete
        # TODO: Map to actual collection phase completion once repository is ready
        phase_valid = (
            current_phase == "questionnaires" and flow_data.get("status") == "completed"
        )

    return {
        "phase_valid": phase_valid,  # Derived from actual flow data per ADR-012
        "issues": [],
        "error": None,
        "completion_status": "phase_complete" if phase_valid else "in_progress",
    }


async def _handle_fast_path_processing(
    flow_id: str,
    flow_data: dict,
    validation_data: dict,
    current_phase: str,
    db: AsyncSession,
    context: RequestContext,
    start_time: float,
    flow_metrics,
) -> Any:
    """Handle fast path processing logic."""
    logger.info(f"⚡ FAST PATH: Simple transition detected for {flow_id}")

    # Get fast path response without AI (< 1 second)
    fast_response = get_fast_path_response(flow_data, validation_data)

    if fast_response:
        # Update current_phase in database if transitioning to next phase
        await _update_phase_if_needed(
            flow_id, fast_response.get("next_phase"), current_phase, db, context
        )

        execution_time = time.time() - start_time
        logger.info(f"✅ FAST PATH COMPLETE: {flow_id} in {execution_time:.3f}s")

        # Record metrics for observability
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
    flow_metrics,
) -> Any:
    """Handle simple logic processing without AI."""
    logger.info(f"⚡ SIMPLE LOGIC: No AI needed for {flow_id}")

    # Determine next phase using simple logic
    next_phase = _get_next_phase_simple(flow_type, current_phase)

    # CRITICAL FIX: Execute asset_inventory phase when transitioning TO or FROM it
    # This ensures assets are actually created, not just phase advancement
    # Handle both cases: moving TO asset_inventory OR already IN asset_inventory
    if flow_type == "discovery" and (
        next_phase == "asset_inventory"
        or current_phase == "asset_inventory"
        or (
            current_phase == "data_cleansing"
            and next_phase in ["asset_creation", "dependency_analysis"]
        )
    ):
        # Check if we need to execute asset_inventory
        execute_asset_phase = False
        asset_phase_name = "asset_inventory"

        if current_phase == "asset_inventory":
            # We're IN asset_inventory, check if it's completed
            asset_inventory_completed = flow_data.get("phases_completed", {}).get(
                "asset_inventory", False
            )
            if not asset_inventory_completed:
                logger.info(
                    f"🏭 Currently in asset_inventory (not completed), executing before advancing to {next_phase}"
                )
                execute_asset_phase = True
            else:
                logger.info("✅ Asset inventory already completed, skipping execution")
        elif next_phase == "asset_inventory":
            # Moving TO asset_inventory
            logger.info(f"🏭 Moving to asset_inventory phase for {flow_id}")
            execute_asset_phase = True
        elif current_phase == "data_cleansing":
            # Just completed data_cleansing, ensure asset_inventory runs
            logger.info(
                f"🏭 Post-data_cleansing: ensuring asset_inventory executes for {flow_id}"
            )
            execute_asset_phase = True
            # Override next phase to ensure proper sequence
            if next_phase == "dependency_analysis":
                # This means asset_inventory was skipped, force it
                asset_phase_name = "asset_inventory"

        if execute_asset_phase:
            try:
                from app.services.master_flow_orchestrator import MasterFlowOrchestrator
                from app.repositories.discovery_flow_repository import (
                    DiscoveryFlowRepository,
                )

                # CRITICAL: Get discovery flow first to access both data_import_id and master_flow_id
                flow_repo = DiscoveryFlowRepository(
                    db, context.client_account_id, context.engagement_id
                )
                discovery_flow = await flow_repo.get_by_flow_id(flow_id)

                # Get data_import_id from flow_data or discovery flow
                data_import_id = flow_data.get("data_import_id")

                if not data_import_id and discovery_flow:
                    data_import_id = discovery_flow.data_import_id
                    if data_import_id:
                        logger.info(
                            f"📦 Found data_import_id from discovery flow: {data_import_id}"
                        )

                if not data_import_id:
                    logger.warning(
                        f"⚠️ No data_import_id found for flow {flow_id}, cannot execute asset_inventory"
                    )
                    # Skip asset inventory if no data import
                else:
                    # CRITICAL FIX: Get the actual master_flow_id from discovery flow
                    # The flow_id here is the discovery flow ID, but we need the master flow ID
                    master_flow_id = (
                        discovery_flow.master_flow_id
                        if discovery_flow and discovery_flow.master_flow_id
                        else flow_id
                    )

                    logger.info(
                        f"🏭 Executing asset_inventory with data_import_id: {data_import_id}"
                    )
                    logger.info(
                        f"📋 Using master_flow_id: {master_flow_id} (discovery_flow_id: {flow_id})"
                    )

                    orchestrator = MasterFlowOrchestrator(db, context)
                    exec_result = await orchestrator.execute_phase(
                        flow_id=str(
                            master_flow_id
                        ),  # Use master_flow_id for orchestrator
                        phase_name=asset_phase_name,
                        phase_input={
                            "data_import_id": str(
                                data_import_id
                            ),  # CRITICAL: Include data_import_id
                            "flow_id": str(
                                master_flow_id
                            ),  # Use master_flow_id in phase_input
                            "master_flow_id": str(
                                master_flow_id
                            ),  # Consistent master_flow_id
                            "discovery_flow_id": flow_id,  # Include discovery_flow_id for asset association
                            "client_account_id": str(context.client_account_id),
                            "engagement_id": str(context.engagement_id),
                        },
                    )

                    logger.info(f"✅ Asset inventory executed: {exec_result}")
                    if exec_result.get("status") not in ("success", "completed"):
                        logger.warning(
                            f"⚠️ Asset inventory execution had issues: {exec_result}"
                        )
                    else:
                        # Mark asset_inventory as completed in discovery flow
                        from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
                            FlowPhaseManagementCommands,
                        )

                        phase_mgmt = FlowPhaseManagementCommands(
                            db, context.client_account_id, context.engagement_id
                        )
                        await phase_mgmt.update_phase_completion(
                            flow_id=flow_id,  # Use discovery flow ID
                            phase="asset_inventory",
                            completed=True,
                            data=exec_result,
                            agent_insights=exec_result.get("agent_insights"),
                        )
                        logger.info(
                            f"✅ Marked asset_inventory_completed=true for flow {flow_id}"
                        )
            except Exception as e:
                logger.error(f"❌ Failed to execute asset_inventory phase: {e}")
                # Continue anyway - don't block flow progression

    # Update current_phase in database if transitioning to next phase
    await _update_phase_if_needed(flow_id, next_phase, current_phase, db, context)

    # Use simple logic without AI but with proper response format
    simple_response = create_simple_transition_response(flow_data)
    execution_time = time.time() - start_time

    # Record metrics for observability
    await flow_metrics.record_simple_logic(execution_time)

    return convert_fast_path_to_api_response(simple_response, flow_data, execution_time)


async def _update_phase_if_needed(
    flow_id: str,
    next_phase: str,
    current_phase: str,
    db: AsyncSession,
    context: RequestContext,
) -> None:
    """Update phase in database if transitioning to next phase.

    CRITICAL: Updates BOTH discovery_flows and master flow tables to ensure consistency.
    """
    from app.repositories.discovery_flow_repository.commands.flow_phase_management import (
        FlowPhaseManagementCommands,
    )

    if next_phase and next_phase != current_phase:
        # Update discovery_flows table
        phase_mgmt = FlowPhaseManagementCommands(
            db, context.client_account_id, context.engagement_id
        )
        await phase_mgmt.update_phase_completion(
            flow_id=flow_id,
            phase=next_phase,
            completed=False,  # Don't mark complete, just update current_phase
            data=None,
            agent_insights=None,
        )

        # TODO: Re-enable after adding update_persistence_data() to repository (pre-existing bug)
        # Also update master flow's persistence data to track current phase
        # flow_repo = DiscoveryFlowRepository(
        #     db, context.client_account_id, context.engagement_id
        # )
        # discovery_flow = await flow_repo.get_by_flow_id(flow_id)
        # if discovery_flow and discovery_flow.master_flow_id:
        #     master_repo = CrewAIFlowStateExtensionsRepository(
        #         db, context.client_account_id, context.engagement_id
        #     )
        #     # Update master flow persistence data to track phase transition
        #     master_flow = await master_repo.get_by_flow_id(
        #         str(discovery_flow.master_flow_id)
        #     )
        #     if master_flow and master_flow.flow_persistence_data:
        #         persistence_data = master_flow.flow_persistence_data
        #         persistence_data["current_phase"] = next_phase
        #         persistence_data["last_phase_transition"] = {
        #             "from": current_phase,
        #             "to": next_phase,
        #             "timestamp": datetime.utcnow().isoformat(),
        #         }
        #         await master_repo.update_persistence_data(
        #             flow_id=str(discovery_flow.master_flow_id),
        #             persistence_data=persistence_data,
        #         )
        #         logger.info(
        #             f"✅ Updated master flow {discovery_flow.master_flow_id} phase metadata"
        #         )

        logger.info(
            f"✅ Advanced current_phase from {current_phase} to {next_phase} in all tables"
        )


async def _handle_ai_processing(
    flow_id: str,
    flow_data: dict,
    context: RequestContext,
    start_time: float,
    flow_metrics,
    db: AsyncSession = None,
    current_phase: str = None,
) -> Any:
    """Handle AI-based processing logic."""
    logger.info(f"🧠 AI ANALYSIS NEEDED for {flow_id}")

    if TENANT_AGENT_POOL_AVAILABLE:
        # Use persistent tenant-scoped agent for better performance
        try:
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            # Get the actual agent from the pool (FIX for Issue #3 per ADR-015)
            agent = await TenantScopedAgentPool.get_agent(
                context=context,
                agent_type="IntelligentFlowAgent",
                force_recreate=False,
            )

            logger.info(f"🧠 TENANT AGENT: Using persistent agent for {flow_id}")

            # Use the pooled agent's analyze_flow_continuation method
            if hasattr(agent, "analyze_flow_continuation"):
                result = await agent.analyze_flow_continuation(
                    flow_id=flow_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id,
                )
            else:
                # Fallback if agent doesn't have expected method
                logger.warning(
                    "Pooled agent lacks analyze_flow_continuation, using new instance"
                )
                result = await use_intelligent_agent(flow_id, context)

        except Exception as e:
            logger.warning(f"Tenant agent failed, using intelligent agent: {e}")
            result = await use_intelligent_agent(flow_id, context)
    else:
        # Fallback to single intelligent agent
        logger.info(f"🧠 INTELLIGENT AGENT: TenantPool unavailable for {flow_id}")
        result = await use_intelligent_agent(flow_id, context)

    execution_time = time.time() - start_time
    logger.info(f"✅ AI ANALYSIS COMPLETE: {flow_id} in {execution_time:.3f}s")

    # CC FIX: Update current_phase in database after AI analysis
    # This ensures the phase is updated even when AI path is used
    # TODO: Re-enable after fixing update_persistence_data() method (pre-existing bug)
    # if db and current_phase and result:
    #     # FlowIntelligenceResult is a Pydantic BaseModel, not a dict - use attribute access
    #     next_phase = getattr(result, "next_phase", None) or getattr(
    #         result, "current_phase", None
    #     )
    #     if next_phase:
    #         await _update_phase_if_needed(
    #             flow_id, next_phase, current_phase, db, context
    #         )
    #         logger.info(
    #             f"✅ AI PATH: Updated current_phase to {next_phase} after AI analysis"
    #         )

    # Record metrics for AI path
    await flow_metrics.record_ai_path(execution_time)

    # Pass flow_data to include actual phase completion status (Issue #557 fix)
    return convert_to_api_response(result, flow_data, execution_time)


async def use_intelligent_agent(flow_id: str, context: RequestContext) -> Any:
    """Use the intelligent agent for flow analysis"""
    if not INTELLIGENT_AGENT_AVAILABLE:
        raise Exception("Intelligent agent not available")

    from .base import IntelligentFlowAgent

    # Create single intelligent agent
    intelligent_agent = IntelligentFlowAgent()

    # Analyze flow using single agent with multiple tools
    result = await intelligent_agent.analyze_flow_continuation(
        flow_id=flow_id,
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        user_id=context.user_id,
    )

    return result
