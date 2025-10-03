"""
Flow Execution Handlers for Unified Discovery

Handles flow execution and phase management.
"""

import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)

router = APIRouter()


async def _execute_data_cleansing_with_complete(
    flow_id: str,
    discovery_flow: DiscoveryFlow,
    db: AsyncSession,
    context: RequestContext,
) -> dict:
    """Execute data cleansing phase and mark as complete."""
    from app.services.master_flow_orchestrator import MasterFlowOrchestrator

    orchestrator = MasterFlowOrchestrator(db, context)

    # Prepare phase_input with data_import_id
    cleansing_input = {}
    if discovery_flow.data_import_id:
        cleansing_input["data_import_id"] = str(discovery_flow.data_import_id)
        logger.info(
            f"Passing data_import_id: {discovery_flow.data_import_id} to data_cleansing executor"
        )

    # Execute the data_cleansing phase
    exec_result = await orchestrator.execute_phase(
        flow_id=flow_id,
        phase_name="data_cleansing",
        phase_input=cleansing_input,
    )

    # Update the discovery flow state
    if exec_result.get("status") in ("success", "completed"):
        discovery_flow.data_cleansing_completed = True
        discovery_flow.current_phase = "asset_inventory"
        await db.commit()

        return {
            "success": True,
            "phase": "data_cleansing",
            "status": "completed",
            "message": "Data cleansing phase executed and completed",
            "data": exec_result.get("data", {}),
        }
    else:
        return exec_result


async def _execute_data_cleansing_regular(
    flow_id: str,
    discovery_flow: DiscoveryFlow,
    phase_input: dict,
    db: AsyncSession,
    context: RequestContext,
) -> dict:
    """Execute data cleansing phase with regular flow."""
    from app.services.master_flow_orchestrator import MasterFlowOrchestrator

    # Ensure data_import_id is in phase_input
    if discovery_flow.data_import_id and "data_import_id" not in phase_input:
        phase_input["data_import_id"] = str(discovery_flow.data_import_id)
        logger.info(
            f"Adding data_import_id: {discovery_flow.data_import_id} to phase_input"
        )

    orchestrator = MasterFlowOrchestrator(db, context)
    return await orchestrator.execute_phase(
        flow_id=flow_id,
        phase_name="data_cleansing",
        phase_input=phase_input,
    )


def _determine_next_phase(discovery_flow: DiscoveryFlow) -> str:
    """
    Determine the next phase to execute based on the current flow state.
    Check completion flags first to determine next phase.
    """
    # Check completion flags first to determine next phase
    if not discovery_flow.data_import_completed:
        return "field_mapping"
    if (
        discovery_flow.data_import_completed
        and not discovery_flow.field_mapping_completed
    ):
        return "field_mapping"
    if (
        discovery_flow.field_mapping_completed
        and not discovery_flow.data_cleansing_completed
    ):
        return "data_cleansing"
    if (
        discovery_flow.data_cleansing_completed
        and not discovery_flow.asset_inventory_completed
    ):
        return "asset_inventory"
    if discovery_flow.asset_inventory_completed:
        # Continue with remaining phases
        if not discovery_flow.dependency_analysis_completed:
            return "dependency_mapping"
        if discovery_flow.dependency_analysis_completed:
            return "recommendations"
    return "completed"


@router.post("/flows/{flow_id}/execute")
async def execute_flow(
    flow_id: str,
    request: dict = Body(
        default={}
    ),  # Per CLAUDE.md: POST requests MUST use Body() for request body params
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Execute a specific phase of a discovery flow or the next phase."""
    try:
        # Query the flow with proper tenant scoping
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        discovery_flow = result.scalar_one_or_none()
        if not discovery_flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")

        # Guard against deleted flows
        if discovery_flow.status == "archived":
            raise HTTPException(status_code=400, detail="Cannot process deleted flow")

        # Check if a specific phase was requested
        requested_phase = request.get("phase")
        phase_input = request.get("phase_input", {})

        # If a specific phase is requested, execute it
        if requested_phase:
            logger.info(
                safe_log_format(
                    "Executing requested phase '{phase}' for flow {flow_id}",
                    phase=requested_phase,
                    flow_id=mask_id(str(flow_id)),
                )
            )

            # Special handling for data_cleansing phase
            if requested_phase == "data_cleansing":
                # Check if it's just marking complete or actually executing
                if phase_input.get("complete"):
                    logger.info(
                        "Executing data_cleansing phase before marking complete"
                    )
                    return await _execute_data_cleansing_with_complete(
                        flow_id, discovery_flow, db, context
                    )
                else:
                    # Regular execution of data_cleansing
                    return await _execute_data_cleansing_regular(
                        flow_id, discovery_flow, phase_input, db, context
                    )
            else:
                # For other phases, use existing flow execution logic
                from app.services.discovery.flow_execution_service import (
                    execute_flow_phase as exec_phase,
                )

                # Override the phase determination to use requested phase
                discovery_flow.current_phase = requested_phase
                result = await exec_phase(flow_id, discovery_flow, context, db)
        else:
            # No specific phase requested, determine next phase
            next_phase = _determine_next_phase(discovery_flow)

            if not next_phase:
                return {
                    "success": True,
                    "message": "Flow execution completed - no more phases to execute",
                    "status": "completed",
                }

            # Execute the phase with correct signature
            from app.services.discovery.flow_execution_service import (
                execute_flow_phase as exec_phase,
            )

            result = await exec_phase(flow_id, discovery_flow, context, db)

        # FIX: Use requested_phase if provided, otherwise use next_phase
        phase_for_log = requested_phase or result.get(
            "next_phase", next_phase if "next_phase" in locals() else None
        )

        logger.info(
            safe_log_format(
                "Flow phase executed: flow_id={flow_id}, phase={phase}, success={success}",
                flow_id=mask_id(str(flow_id)),
                phase=phase_for_log,
                success=result.get("success", False),
            )
        )

        # Check for specific error codes that should trigger HTTP exceptions
        if result.get("error_code") == "CLEANSING_REQUIRED":
            # Return 422 for missing cleansed data
            raise HTTPException(
                status_code=422,
                detail={
                    "error_code": "CLEANSING_REQUIRED",
                    "message": result.get(
                        "message",
                        "No cleansed data available. Run data cleansing first.",
                    ),
                    "counts": result.get("counts", {}),
                    "requires_cleansing": True,
                    "flow_id": flow_id,
                    "phase": phase_for_log,
                },
            )

        # Check if result indicates an HTTP status code should be returned
        if not result.get("success") and result.get("http_status"):
            http_status = result.get("http_status")
            if http_status == 422:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error_code": result.get("error_code", "VALIDATION_ERROR"),
                        "message": result.get("message", "Request validation failed"),
                        "flow_id": flow_id,
                        "phase": phase_for_log,
                        **{
                            k: v
                            for k, v in result.items()
                            if k
                            not in [
                                "success",
                                "http_status",
                                "flow_id",
                                "message",
                                "error_code",
                            ]
                        },
                    },
                )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Flow execution failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail=str(e))
