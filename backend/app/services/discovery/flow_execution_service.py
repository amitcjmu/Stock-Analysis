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
from app.utils.flow_constants.flow_states import FlowType, PHASE_SEQUENCES
from .flow_state_helpers import load_flow_state_for_phase
from .phase_persistence_helpers import (
    persist_phase_completion,
    persist_field_mapping_completion,
)
from .field_mapping_helpers import (
    check_existing_field_mappings,
    auto_generate_field_mappings,
)

logger = logging.getLogger(__name__)


def validate_discovery_phase(phase: str) -> bool:
    """Validate that a phase is valid for discovery flows."""
    discovery_phases = PHASE_SEQUENCES.get(FlowType.DISCOVERY, [])
    valid_phase_names = [p.value for p in discovery_phases]
    return phase in valid_phase_names


async def determine_phase_to_execute(discovery_flow: DiscoveryFlow) -> str:
    """Determine which phase to execute based on flow status and current phase."""
    current_phase = discovery_flow.current_phase
    status = discovery_flow.status

    # Map variations of phase names to standard names
    phase_mapping = {
        "field_mapping_suggestions": "field_mapping",
        "data_cleaning": "data_cleansing",
        "assets": "asset_inventory",
    }

    # Normalize the current phase name if it exists
    if current_phase:
        current_phase = phase_mapping.get(current_phase, current_phase)

    # CC: Handle 'initialization' phase - map to field_mapping for discovery flows
    if current_phase == "initialization":
        logger.info(
            "Mapping 'initialization' phase to 'field_mapping' for discovery flow"
        )
        phase = "field_mapping"
    # Check if this is an asset_inventory phase request
    elif current_phase == "asset_inventory":
        logger.info(f"Processing asset_inventory phase request (status: {status})")
        phase = "asset_inventory"
    # Map the phase correctly to match Master Flow Orchestrator expectations
    # MFO expects "field_mapping" not "field_mapping_suggestions"
    elif status == "initialized" and not current_phase:
        # Flow is initialized but hasn't started any phase yet
        phase = "field_mapping"
    elif status in ["failed", "error", "paused", "waiting_for_approval"]:
        # For failed/paused flows, restart from current phase or field mapping
        phase = current_phase if current_phase != "initialization" else "field_mapping"
        if not phase:
            phase = "field_mapping"
    elif status == "initialized":
        # Flow was initialized but needs to execute field mapping phase
        phase = "field_mapping"
    elif current_phase:
        # Use the current phase from the flow if valid
        if validate_discovery_phase(current_phase):
            phase = current_phase
        else:
            logger.warning(
                f"Invalid phase '{current_phase}' for discovery flow, defaulting to field_mapping"
            )
            phase = "field_mapping"
    else:
        # Default phase mapping - field_mapping is the standard first operational phase
        phase = "field_mapping"

    # Defensive validation of the selected phase - but allow asset_inventory
    if phase == "asset_inventory":
        # Asset inventory is a valid phase, don't override it
        logger.info("Asset inventory phase is valid and will be executed")
    elif not validate_discovery_phase(phase):
        logger.error(
            f"Selected phase '{phase}' is not valid for discovery flows. Using field_mapping as fallback."
        )
        phase = "field_mapping"

    logger.info(
        f"Determined phase to execute: '{phase}' (status: {status}, current_phase: {current_phase})"
    )
    return phase


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

    # Check if field mapping has already been completed
    existing_mappings = await check_existing_field_mappings(db, discovery_flow, flow_id)
    if existing_mappings:
        return existing_mappings

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

        # Auto-generate field mappings if data_import_id exists
        await auto_generate_field_mappings(db, context, discovery_flow)

        # Update discovery flow status
        discovery_flow.status = "processing"
        discovery_flow.current_phase = "field_mapping_suggestions"
        await db.commit()

        # Persist field mapping completion
        await persist_field_mapping_completion(db, context, flow_id, result)

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
    # For field mapping phase, try direct execution first
    # CC: Check for both "field_mapping" and "field_mapping_suggestions" for compatibility
    if phase_to_execute in ["field_mapping", "field_mapping_suggestions"]:
        field_mapping_result = await execute_field_mapping_phase(
            flow_id, context, db, discovery_flow
        )
        if field_mapping_result:
            return field_mapping_result

    # For asset_inventory phase, use MFO which has the proper crew execution
    elif phase_to_execute == "asset_inventory":
        logger.info(
            safe_log_format(
                "🔄 Executing asset_inventory phase via MFO for flow {flow_id}",
                flow_id=flow_id,
            )
        )
        try:
            orchestrator = MasterFlowOrchestrator(db, context)

            # Load flow state data for asset_inventory phase
            phase_input = await load_flow_state_for_phase(
                db, context, flow_id, "asset_inventory"
            )

            logger.info(
                safe_log_format(
                    "📦 Passing {record_count} records to asset_inventory phase",
                    record_count=len(phase_input.get("raw_data", [])),
                )
            )

            # Pass asset_inventory as the phase to execute with populated data
            result = await orchestrator.execute_phase(
                flow_id, "asset_inventory", phase_input
            )

            # Check for CLEANSING_REQUIRED error
            if result.get("error_code") == "CLEANSING_REQUIRED":
                logger.warning(
                    safe_log_format(
                        "⚠️ Asset inventory phase requires cleansed data for flow {flow_id}",
                        flow_id=flow_id,
                    )
                )
                # Return a result that indicates the need for data cleansing
                return {
                    "success": False,
                    "flow_id": flow_id,
                    "error_code": "CLEANSING_REQUIRED",
                    "message": result.get(
                        "message",
                        "No cleansed data available. Run data cleansing first.",
                    ),
                    "counts": result.get("counts", {}),
                    "requires_cleansing": True,
                    "http_status": 422,  # Indicate that this should be a 422 response
                }

            if result.get("success"):
                # Update flow state after successful asset inventory
                discovery_flow.current_phase = "asset_inventory"
                discovery_flow.assets_generated = True
                await db.commit()
                logger.info(
                    safe_log_format(
                        "✅ Asset inventory phase completed for flow {flow_id}",
                        flow_id=flow_id,
                    )
                )
            return result
        except Exception as e:
            logger.error(
                safe_log_format(
                    "❌ Asset inventory phase failed for flow {flow_id}: {error}",
                    flow_id=flow_id,
                    error=str(e),
                )
            )

            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            return {
                "success": False,
                "flow_id": flow_id,
                "error": str(e),
                "phase": "asset_inventory",
            }

    # Try Master Flow Orchestrator as fallback or for other phases
    try:
        orchestrator = MasterFlowOrchestrator(db, context)

        # Load flow state data for the phase
        phase_input = await load_flow_state_for_phase(
            db, context, flow_id, phase_to_execute
        )

        logger.debug(
            safe_log_format(
                "📦 Passing flow state data to {phase} phase",
                phase=phase_to_execute,
            )
        )

        result = await orchestrator.execute_phase(
            flow_id, phase_to_execute, phase_input
        )

        # Persist phase completion after successful execution
        if result.get("status") != "failed":
            await persist_phase_completion(
                db, context, flow_id, phase_to_execute, result
            )

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
