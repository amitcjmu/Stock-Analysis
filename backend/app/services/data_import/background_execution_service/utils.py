"""
Background Execution Service - Utility Functions

Pure utility functions for status determination, progress calculation,
and flow status updates. These functions don't require instance state
and can be used independently.
"""

from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


def calculate_progress_percentage(phase) -> float:
    """
    Calculate progress percentage based on current phase.

    Args:
        phase: Flow phase object with .value attribute

    Returns:
        float: Progress percentage (0-100)
    """
    phase_progress_map = {
        "initialization": 10.0,
        "data_import_validation": 20.0,
        "field_mapping_suggestions": 30.0,
        "field_mapping_approval": 40.0,
        "data_cleansing": 50.0,
        "asset_inventory": 70.0,
        "dependency_analysis": 85.0,
        "tech_debt_assessment": 90.0,
        "finalization": 100.0,
    }
    return phase_progress_map.get(phase.value, 30.0)


def determine_final_status(result: Any) -> tuple[str, Dict[str, Any]]:
    """
    Determine the final status and phase data based on flow result (legacy).

    Args:
        result: Result string from the flow execution

    Returns:
        Tuple of (status, phase_data)
    """
    if result in [
        "paused_for_field_mapping_approval",
        "awaiting_user_approval_in_attribute_mapping",
    ]:
        return "waiting_for_approval", {
            "completion": result,
            "current_phase": "attribute_mapping",
            "progress_percentage": 60.0,
            "awaiting_user_approval": True,
        }
    elif result in ["discovery_completed"]:
        return "completed", {
            "completion": result,
            "current_phase": "completed",
            "progress_percentage": 100.0,
        }
    else:
        return "processing", {
            "completion": result,
            "current_phase": "processing",
            "progress_percentage": 30.0,
        }


def determine_final_status_from_phase_result(result) -> tuple[str, Dict[str, Any]]:
    """
    Determine the final status and phase data based on PhaseExecutionResult.

    Args:
        result: PhaseExecutionResult from phase controller

    Returns:
        Tuple of (status, phase_data)
    """
    if result.requires_user_input:
        return "waiting_for_approval", {
            "completion": result.status,
            "current_phase": result.phase.value,
            "progress_percentage": calculate_progress_percentage(result.phase),
            "awaiting_user_approval": True,
            "phase_data": result.data,
        }
    elif result.status == "failed":
        return "failed", {
            "completion": result.status,
            "current_phase": result.phase.value,
            "error": result.data.get("error", "Unknown error"),
            "phase_data": result.data,
        }
    elif result.status == "completed" and result.phase.value == "finalization":
        return "completed", {
            "completion": "discovery_completed",
            "current_phase": "completed",
            "progress_percentage": 100.0,
            "phase_data": result.data,
        }
    else:
        return "processing", {
            "completion": result.status,
            "current_phase": result.phase.value,
            "progress_percentage": calculate_progress_percentage(result.phase),
            "phase_data": result.data,
        }


async def update_flow_status(
    flow_id: str,
    status: str,
    phase_data: Dict[str, Any],
    context: RequestContext,
) -> None:
    """
    Update the flow status in the database using a fresh session.

    Args:
        flow_id: The flow ID to update
        status: New status for the flow
        phase_data: Phase data to update
        context: Request context with tenant information
    """
    try:
        async with AsyncSessionLocal() as fresh_db:
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            fresh_repo = CrewAIFlowStateExtensionsRepository(
                fresh_db,
                context.client_account_id,
                context.engagement_id,
                context.user_id,
            )

            await fresh_repo.update_flow_status(
                flow_id=flow_id, status=status, phase_data=phase_data
            )
            await fresh_db.commit()

    except Exception as e:
        logger.error(f"❌ Failed to update flow status: {e}")


async def get_execution_status(
    flow_id: str, context: RequestContext
) -> Optional[Dict[str, Any]]:
    """
    Get the current execution status of a flow.

    Args:
        flow_id: The flow ID to check
        context: Request context with tenant information

    Returns:
        Dict containing execution status information, or None if not found
    """
    try:
        async with AsyncSessionLocal() as fresh_db:
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            repo = CrewAIFlowStateExtensionsRepository(
                fresh_db,
                context.client_account_id,
                context.engagement_id,
                context.user_id,
            )

            flow_state = await repo.get_flow_state(flow_id)

            if flow_state:
                return {
                    "flow_id": flow_id,
                    "status": flow_state.status,
                    "phase_data": flow_state.phase_data,
                    "created_at": (
                        flow_state.created_at.isoformat()
                        if flow_state.created_at
                        else None
                    ),
                    "updated_at": (
                        flow_state.updated_at.isoformat()
                        if flow_state.updated_at
                        else None
                    ),
                }

            return None

    except Exception as e:
        logger.error(f"❌ Failed to get execution status: {e}")
        return None
