"""
Flow Processing Response Converters
Utilities for converting between different response formats
"""

import logging
from types import SimpleNamespace
from typing import Any, Dict, List

from app.services.discovery.phase_persistence_helpers.base import (
    API_TO_DB_PHASE_MAP,
    DB_TO_API_PHASE_MAP,
)

from .flow_processing_models import (
    FlowContinuationResponse,
    PhaseStatus,
    RoutingContext,
    TaskResult,
    UserGuidance,
)

logger = logging.getLogger(__name__)


def convert_fast_path_to_api_response(
    fast_response: Dict[str, Any], flow_data: Dict[str, Any], execution_time: float
) -> FlowContinuationResponse:
    """Convert fast path response to proper API response format"""
    try:
        flow_id = flow_data.get("flow_id", "unknown")
        flow_type = flow_data.get("flow_type", "discovery")
        current_phase = flow_data.get("current_phase", "data_import")

        # Create routing context (FIX for Issue #6: collection uses /progress)
        default_route = (
            f"/{flow_type}/progress/{flow_id}"
            if flow_type == "collection"
            else f"/{flow_type}/overview"
        )

        # Log the routing decision for debugging
        routing_decision = fast_response.get("routing_decision", default_route)
        logger.info(
            f"🔍 ROUTE DEBUG - Fast path routing: flow_id={flow_id}, phase={current_phase}, route={routing_decision}"
        )

        routing_context = RoutingContext(
            target_page=routing_decision,
            recommended_page=routing_decision,
            flow_id=flow_id,
            phase=current_phase,
            flow_type=flow_type,
        )

        # Create user guidance
        user_guidance = UserGuidance(
            primary_message=fast_response.get(
                "user_guidance", "Continue with next step"
            ),
            action_items=[
                fast_response.get("user_guidance", "Continue with next step")
            ],
            user_actions=[
                fast_response.get("user_guidance", "Continue with next step")
            ],
            system_actions=["Fast path processing complete"],
            estimated_completion_time=1,  # Fast path
        )

        # Bug #557 FIX: Use full checklist with actual phase completion status
        # Instead of minimal checklist, show all phases with their completion state
        phases_completed = flow_data.get("phases_completed", {})

        # Create a minimal result object for compatibility with create_checklist_status
        # Use SimpleNamespace to create an object with attributes (not a dict)
        minimal_result = SimpleNamespace(
            current_phase=current_phase,
            next_phase=fast_response.get("next_phase"),
            confidence=fast_response.get("confidence", 0.95),
            success=True,
            user_guidance=fast_response.get("user_guidance", ""),
            next_actions=[],  # Empty list for fast path (no specific actions)
        )

        # Use the same function as AI path to ensure consistent phase display
        checklist_status = create_checklist_status(minimal_result, phases_completed)

        return FlowContinuationResponse(
            success=True,
            flow_id=flow_id,
            flow_type=flow_type,
            current_phase=current_phase,
            routing_context=routing_context,
            user_guidance=user_guidance,
            checklist_status=checklist_status,
            agent_insights=[
                {
                    "agent": "Fast Path Processor",
                    "analysis": (
                        f"Simple transition detected - "
                        f"{fast_response.get('completion_status', 'processing')}"
                    ),
                    "confidence": fast_response.get("confidence", 0.95),
                    "execution_time": execution_time,
                }
            ],
            confidence=fast_response.get("confidence", 0.95),
            reasoning="Fast path processing - no AI analysis required",
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Error converting fast path response: {e}")
        return create_fallback_response(
            flow_data.get("flow_id", "unknown"),
            f"Fast path conversion failed: {str(e)}",
        )


def create_simple_transition_response(flow_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create simple transition response without AI analysis"""
    flow_id = flow_data.get("flow_id", "unknown")
    flow_type = flow_data.get("flow_type", "discovery")

    # FIX for Issue #6: Use correct routing path based on flow type
    if flow_type == "collection":
        routing_decision = f"/{flow_type}/progress/{flow_id}"
    else:
        # For discovery flows, route to attribute-mapping (the typical starting point)
        # The frontend will auto-detect the flow from context
        routing_decision = "/discovery/attribute-mapping"

    return {
        "routing_decision": routing_decision,
        "user_guidance": f"Continue with {flow_type} flow processing",
        "action_type": "navigation",
        "confidence": 0.9,
        "completion_status": "processing",
        "fast_path": True,
    }


def convert_to_api_response(
    result: Any, flow_data: Dict[str, Any], execution_time: float
) -> FlowContinuationResponse:
    """Convert agent result to API response format with defensive access (FIX for Qodo review)"""
    try:
        # Defensive attribute access to prevent AttributeError
        if isinstance(result, dict):
            # If result is already a dict, use it directly
            routing_path = result.get("routing_decision", "/discovery/overview")
            flow_id = result.get("flow_id", "unknown")
            current_phase = result.get("current_phase", "data_import")
            flow_type = result.get("flow_type", "discovery")
            user_guidance_text = result.get("user_guidance", "Continue to next step")
            next_actions = result.get("next_actions", [])
            success = result.get("success", True)
            confidence = result.get("confidence", 0.9)
            reasoning = result.get("reasoning", "AI analysis completed")
            issues_found = result.get("issues_found", [])
        else:
            # If result is an object with attributes, safely access them
            routing_path = getattr(result, "routing_decision", "/discovery/overview")
            flow_id = getattr(result, "flow_id", "unknown")
            current_phase = getattr(result, "current_phase", "data_import")
            flow_type = getattr(result, "flow_type", "discovery")
            user_guidance_text = getattr(
                result, "user_guidance", "Continue to next step"
            )
            next_actions = getattr(result, "next_actions", [])
            success = getattr(result, "success", True)
            confidence = getattr(result, "confidence", 0.9)
            reasoning = getattr(result, "reasoning", "AI analysis completed")
            issues_found = getattr(result, "issues_found", [])

        # Create routing context
        routing_context = RoutingContext(
            target_page=routing_path,
            recommended_page=routing_path,
            flow_id=flow_id,
            phase=current_phase,
            flow_type=flow_type,
        )

        # Create user guidance
        user_guidance = UserGuidance(
            primary_message=user_guidance_text,
            action_items=[user_guidance_text],
            user_actions=(next_actions if next_actions else [user_guidance_text]),
            system_actions=["Continue background processing"],
            estimated_completion_time=30,  # Fast single agent
        )

        # Create checklist status based on ACTUAL phase completion from database (Issue #557 fix)
        checklist_status = create_checklist_status(
            result, flow_data.get("phases_completed", {})
        )

        return FlowContinuationResponse(
            success=success,
            flow_id=flow_id,
            flow_type=flow_type,
            current_phase=current_phase,
            routing_context=routing_context,
            user_guidance=user_guidance,
            checklist_status=checklist_status,
            agent_insights=[
                {
                    "agent": "Single Intelligent Flow Agent",
                    "analysis": reasoning,
                    "confidence": confidence,
                    "issues_found": issues_found,
                }
            ],
            confidence=confidence,
            reasoning=reasoning,
            execution_time=execution_time,
        )

    except Exception as e:
        logger.error(f"Failed to convert agent result: {e}")
        return create_fallback_response(
            result.flow_id, f"Response conversion failed: {str(e)}"
        )


def create_checklist_status(
    result: Any, phases_completed: Dict[str, bool] = None
) -> List[PhaseStatus]:
    """Create checklist status based on ACTUAL database phase completion (Issue #557 fix)"""
    try:
        # API phase names (used in response)
        phases = [
            "data_import",
            "attribute_mapping",
            "data_cleansing",
            "inventory",
            "dependencies",
            "tech_debt",
        ]
        checklist_status = []

        current_phase_index = 0
        try:
            # Convert current_phase from DB name to API name if needed
            current_phase_api = DB_TO_API_PHASE_MAP.get(
                result.current_phase, result.current_phase
            )
            current_phase_index = phases.index(current_phase_api)
        except ValueError:
            logger.warning(
                f"Unknown phase {result.current_phase}, defaulting to index 0"
            )
            current_phase_index = 0

        for i, phase in enumerate(phases):
            # ✅ FIX: Check ACTUAL completion from database using phase name mapping
            db_phase_name = API_TO_DB_PHASE_MAP.get(phase, phase)
            is_actually_completed = (
                phases_completed.get(db_phase_name, False)
                if phases_completed
                else False
            )

            # Determine status based on ACTUAL completion, not just index
            if is_actually_completed:
                # Phase is actually completed in database
                status = "completed"
                completion = 100.0
                task_status = "completed"
                tasks = [
                    TaskResult(
                        task_id=f"{phase}_main",
                        task_name=f"{phase.replace('_', ' ').title()} Complete",
                        status="completed",
                        confidence=0.9,
                        next_steps=[],
                    )
                ]
            elif i == current_phase_index:
                # Current phase - determine status from agent result
                if result.success and "completed successfully" in result.user_guidance:
                    status = "completed"
                    completion = 100.0
                    task_status = "completed"
                elif "ISSUE:" in result.user_guidance or not result.success:
                    status = (
                        "not_started"
                        if "No data" in result.user_guidance
                        else "in_progress"
                    )
                    completion = 0.0 if "No data" in result.user_guidance else 25.0
                    task_status = (
                        "not_started"
                        if "No data" in result.user_guidance
                        else "in_progress"
                    )
                else:
                    status = "in_progress"
                    completion = 50.0
                    task_status = "in_progress"

                # Create task based on agent guidance
                task_name = (
                    result.user_guidance.split(":")[1].strip()
                    if ":" in result.user_guidance
                    else phase.replace("_", " ").title()
                )
                if "ACTION NEEDED:" in result.user_guidance:
                    task_name = result.user_guidance.split("ACTION NEEDED:")[1].strip()

                tasks = [
                    TaskResult(
                        task_id=f"{phase}_main",
                        task_name=task_name,
                        status=task_status,
                        confidence=result.confidence,
                        next_steps=result.next_actions,
                    )
                ]
            else:
                status = "not_started"
                completion = 0.0
                tasks = [
                    TaskResult(
                        task_id=f"{phase}_main",
                        task_name=f"{phase.replace('_', ' ').title()}",
                        status="not_started",
                        confidence=0.0,
                        next_steps=[],
                    )
                ]

            checklist_status.append(
                PhaseStatus(
                    phase_id=phase,
                    phase_name=phase.replace("_", " ").title(),
                    status=status,
                    completion_percentage=completion,
                    tasks=tasks,
                    estimated_time_remaining=5 if status != "completed" else None,
                )
            )

        return checklist_status

    except Exception as e:
        logger.error(f"Failed to create checklist status: {e}")
        return []


def create_fallback_response(
    flow_id: str, error_message: str
) -> FlowContinuationResponse:
    """Create fallback response when agent fails"""
    return FlowContinuationResponse(
        success=False,
        flow_id=flow_id,
        flow_type="discovery",
        current_phase="data_import",
        routing_context=RoutingContext(
            target_page="/discovery/data-import",
            recommended_page="/discovery/data-import",
            flow_id=flow_id,
            phase="data_import",
            flow_type="discovery",
        ),
        user_guidance=UserGuidance(
            primary_message=f"System error: {error_message}",
            action_items=["Check system logs", "Retry flow processing"],
            user_actions=["Upload data file if needed"],
            system_actions=["Fix agent system"],
            estimated_completion_time=None,
        ),
        checklist_status=[],
        agent_insights=[
            {
                "agent": "Fallback System",
                "analysis": error_message,
                "confidence": 0.0,
                "issues_found": [error_message],
            }
        ],
        confidence=0.0,
        reasoning=f"Fallback response due to: {error_message}",
        execution_time=0.0,
    )
