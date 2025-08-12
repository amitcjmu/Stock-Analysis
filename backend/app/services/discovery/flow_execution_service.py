"""
Flow Execution Service for Discovery Flow Operations

This service handles the execution logic for discovery flows,
extracted from the unified_discovery endpoint to improve modularity.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.core.context import RequestContext
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.core.security.secure_logging import safe_log_format

logger = logging.getLogger(__name__)


async def determine_phase_to_execute(discovery_flow: DiscoveryFlow) -> str:
    """Determine which phase to execute based on flow status and current phase."""
    current_phase = discovery_flow.current_phase
    status = discovery_flow.status

    # Map the phase correctly to match PhaseController expectations
    if status == "initialized" and not current_phase:
        # Flow is initialized but hasn't started any phase yet
        return "field_mapping_suggestions"
    elif status in ["failed", "error", "paused", "waiting_for_approval"]:
        # For failed/paused flows, restart from current phase or field mapping
        return current_phase or "field_mapping_suggestions"
    elif status == "initialized":
        # Flow was initialized but needs to execute field mapping phase
        return "field_mapping_suggestions"
    elif current_phase:
        # Use the current phase from the flow
        return current_phase
    else:
        # Default phase mapping
        return "initialization"


async def handle_flow_initialization(
    discovery_flow: DiscoveryFlow,
    flow_id: str,
    context: RequestContext,
    db: AsyncSession,
) -> Optional[Dict[str, Any]]:
    """Handle flow initialization with persistent agents."""
    if discovery_flow.status != "initializing":
        return None

    logger.info(
        safe_log_format(
            "🔄 Performing proper initialization for flow {flow_id}",
            flow_id=flow_id,
        )
    )

    try:
        from app.services.persistent_agents.flow_initialization import (
            initialize_flow_with_persistent_agents,
        )

        result = await initialize_flow_with_persistent_agents(flow_id, context)

        if result.success:
            logger.info(
                f"✅ Flow {flow_id} initialization successful - transitioning to running"
            )
            logger.info(
                f"   Agent pool: {len(result.agent_pool or {})} agents initialized"
            )
            logger.info(f"   Initialization time: {result.initialization_time_ms}ms")
            discovery_flow.status = "running"
            await db.commit()
            return None
        else:
            logger.error(
                f"❌ Flow {flow_id} initialization failed - transitioning to failed"
            )
            discovery_flow.status = "failed"
            discovery_flow.error_message = result.error
            await db.commit()
            return {
                "message": f"Flow initialization failed: {result.error}",
                "flow_id": flow_id,
                "status": "failed",
                "initialization_details": result.validation_results,
            }

    except (ImportError, Exception) as e:
        logger.warning(f"⚠️ Persistent agents not available, using fallback: {e}")
        discovery_flow.status = "running"
        await db.commit()
        logger.info(f"✅ Flow {flow_id} using fallback - transitioning to running")
        return None


async def execute_field_mapping_phase(
    flow_id: str,
    context: RequestContext,
    db: AsyncSession,
    discovery_flow: DiscoveryFlow,
) -> Optional[Dict[str, Any]]:
    """Execute field mapping phase directly."""
    logger.info(f"🎯 Attempting direct field mapping execution for flow {flow_id}")

    try:
        from app.services.crewai_flow_service import CrewAIFlowService
        from app.services.crewai_flows.unified_discovery_flow.unified_discovery_flow import (
            UnifiedDiscoveryFlow,
        )
        from app.services.crewai_flows.unified_discovery_flow.phase_controller import (
            PhaseController,
            FlowPhase,
        )
        from app.repositories.crewai_flow_state_extensions_repository import (
            CrewAIFlowStateExtensionsRepository,
        )

        # Create flow instance for field mapping execution
        crewai_service = CrewAIFlowService()

        # Get flow persistence data from master flow if available
        master_repo = CrewAIFlowStateExtensionsRepository(
            db,
            context.client_account_id,
            context.engagement_id,
            context.user_id,
        )
        master_flow = await master_repo.get_by_flow_id(flow_id)

        initial_state = {}
        if master_flow and master_flow.flow_persistence_data:
            initial_state = master_flow.flow_persistence_data

        # Create UnifiedDiscoveryFlow instance
        flow_instance = UnifiedDiscoveryFlow(
            crewai_service,
            context=context,
            flow_id=flow_id,
            initial_state=initial_state,
            configuration=(master_flow.flow_configuration if master_flow else {}),
        )

        # Create PhaseController and execute field mapping
        phase_controller = PhaseController(flow_instance)

        # Force re-run the field mapping phase with existing data
        result = await phase_controller.force_rerun_phase(
            phase=FlowPhase.FIELD_MAPPING_SUGGESTIONS,
            use_existing_data=True,
        )

        logger.info(f"✅ Field mapping phase executed successfully for flow {flow_id}")

        # Update discovery flow status
        discovery_flow.status = "processing"
        discovery_flow.current_phase = "field_mapping_suggestions"
        await db.commit()

        return {
            "success": True,
            "flow_id": flow_id,
            "result": {
                "phase": result.phase.value,
                "status": result.status,
                "data": result.data,
                "requires_user_input": result.requires_user_input,
            },
            "phase_executed": "field_mapping_suggestions",
            "previous_status": discovery_flow.status,
            "message": "Field mapping phase executed successfully",
        }

    except Exception as direct_error:
        logger.warning(
            f"Direct field mapping execution failed, trying MFO: {direct_error}"
        )
        return None


async def execute_flow_phase(
    flow_id: str,
    discovery_flow: DiscoveryFlow,
    context: RequestContext,
    db: AsyncSession,
) -> Dict[str, Any]:
    """Execute a flow phase with proper error handling."""
    import traceback

    # Check if flow is already completed
    if discovery_flow.status == "completed":
        return {
            "success": False,
            "flow_id": flow_id,
            "message": "Flow is already completed",
            "current_status": discovery_flow.status,
            "current_phase": discovery_flow.current_phase,
        }

    # Determine the phase to execute
    phase_to_execute = await determine_phase_to_execute(discovery_flow)

    logger.info(
        safe_log_format(
            "Executing phase '{phase_to_execute}' for flow {flow_id} (status: {status})",
            phase_to_execute=phase_to_execute,
            flow_id=flow_id,
            status=discovery_flow.status,
        )
    )

    # Handle flow initialization if needed
    init_result = await handle_flow_initialization(discovery_flow, flow_id, context, db)
    if init_result:
        return init_result

    # Try to execute the phase
    # For field mapping suggestions phase, try direct execution first
    if phase_to_execute == "field_mapping_suggestions":
        field_mapping_result = await execute_field_mapping_phase(
            flow_id, context, db, discovery_flow
        )
        if field_mapping_result:
            return field_mapping_result

    # Try Master Flow Orchestrator as fallback or for other phases
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.execute_phase(flow_id, phase_to_execute, {})
        return {
            "success": True,
            "flow_id": flow_id,
            "result": result,
            "phase_executed": phase_to_execute,
            "previous_status": discovery_flow.status,
        }
    except Exception as orchestrator_error:
        logger.error(f"Flow execution failed: {orchestrator_error}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # Return a more informative error response
        return {
            "success": False,
            "flow_id": flow_id,
            "message": f"Flow execution failed: {str(orchestrator_error)}",
            "details": {
                "current_status": discovery_flow.status,
                "current_phase": discovery_flow.current_phase,
                "attempted_phase": phase_to_execute,
                "error": str(orchestrator_error),
            },
            "recommended_action": (
                "Please check flow status and retry later, "
                "or contact support for flow state synchronization"
            ),
        }
