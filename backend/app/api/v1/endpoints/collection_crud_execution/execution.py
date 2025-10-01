"""
Collection Flow Execution Operations
Operations for executing collection flow phases through Master Flow Orchestrator.
"""

import logging
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.master_flow_sync_service import MasterFlowSyncService

# Import modular functions
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers
from .creation import create_master_flow_for_orphan

logger = logging.getLogger(__name__)


async def execute_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Execute a collection flow phase through Master Flow Orchestrator.

    This function triggers actual CrewAI execution of the collection flow,
    enabling phase progression and questionnaire generation.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Execution result dictionary
    """
    try:
        # Get the collection flow
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be executed
        await collection_validators.validate_flow_can_be_executed(collection_flow)

        # Execute the current phase using the master flow ID if available
        # If no current_phase is set or if it's the status value "initialized", use "initialization"
        current_phase = collection_flow.current_phase
        if not current_phase or current_phase == "initialized":
            current_phase = "initialization"

        # CRITICAL FIX: Handle orphaned flows without master_flow_id
        if not collection_flow.master_flow_id:
            logger.warning(
                safe_log_format(
                    "Collection flow {flow_id} has no master_flow_id - attempting to create one for execution",
                    flow_id=flow_id,
                )
            )

            try:
                # Create a new master flow for this orphaned collection flow
                master_flow = await create_master_flow_for_orphan(
                    collection_flow, db, context
                )

                logger.info(
                    safe_log_format(
                        "Successfully created master flow {master_flow_id} for orphaned "
                        "collection flow {flow_id} during execution",
                        master_flow_id=str(master_flow.flow_id),
                        flow_id=flow_id,
                    )
                )

                # Update local reference
                collection_flow.master_flow_id = master_flow.flow_id

            except Exception as repair_error:
                logger.error(
                    safe_log_format(
                        "Failed to repair orphaned collection flow {flow_id} during execution: {error}",
                        flow_id=flow_id,
                        error=str(repair_error),
                    )
                )
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "orphaned_flow_repair_failed",
                        "message": "Collection flow has no master flow and repair failed during execution",
                        "flow_id": flow_id,
                        "repair_error": str(repair_error),
                        "required_action": "contact_support",
                    },
                )

        execute_flow_id = str(collection_flow.master_flow_id)

        # Check if phase requires user input before executing
        # Get phase configuration from flow type registry
        from app.services.flow_type_registry import FlowTypeRegistry

        flow_registry = FlowTypeRegistry()
        flow_config = flow_registry.get_flow_config("collection")
        phase_config = (
            flow_config.get_phase_config(current_phase) if flow_config else None
        )

        if phase_config and phase_config.requires_user_input:
            logger.info(
                safe_log_format(
                    "⏸️  Phase {phase} requires user input - skipping automatic execution for flow {flow_id}",
                    phase=current_phase,
                    flow_id=flow_id,
                )
            )
            return {
                "status": "awaiting_user_input",
                "phase": current_phase,
                "flow_id": flow_id,
                "message": f"Phase '{current_phase}' requires user input before proceeding",
                "requires_user_input": True,
            }

        logger.info(
            safe_log_format(
                "Executing phase {phase} for collection flow {flow_id} "
                "using MFO flow {mfo_id}",
                phase=current_phase,
                flow_id=flow_id,
                mfo_id=execute_flow_id,
            )
        )

        # Execute through MasterFlowOrchestrator directly
        orchestrator = MasterFlowOrchestrator(db, context)
        execution_result = await orchestrator.execute_phase(
            flow_id=execute_flow_id, phase_name=current_phase, phase_input={}
        )

        # Sync master flow changes back to collection flow after execution
        try:
            sync_service = MasterFlowSyncService(db, context)
            await sync_service.sync_master_to_collection_flow(
                master_flow_id=execute_flow_id, collection_flow_id=flow_id
            )
        except Exception as sync_error:
            logger.warning(
                safe_log_format(
                    "Failed to sync master flow to collection flow: {error}",
                    error=str(sync_error),
                )
            )

        logger.info(
            f"Executed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return collection_serializers.build_execution_response(
            flow_id, execution_result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error executing collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
