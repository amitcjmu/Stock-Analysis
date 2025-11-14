"""
Assessment Flow Continuation
Handles continuation and resumption of assessment flows including agent execution.
"""

import asyncio
import logging
from typing import Any, Dict

from app.core.security.secure_logging import safe_log_format
from app.models.assessment_flow import AssessmentPhase
from app.core.database import get_db

logger = logging.getLogger(__name__)


async def continue_assessment_flow(
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    phase: AssessmentPhase,
    user_id: str,
) -> None:
    """
    Continue assessment flow execution by triggering CrewAI agent analysis.

    This function connects the API endpoint to the actual agent execution engine.
    Called as a background task from the resume endpoint.

    Args:
        flow_id: Assessment flow identifier
        client_account_id: Client account ID for multi-tenant scoping
        engagement_id: Engagement ID for multi-tenant scoping
        phase: Current assessment phase to execute
        user_id: User identifier for audit trail
    """
    try:
        logger.info(
            safe_log_format(
                "[ISSUE-999] 🚀 BACKGROUND TASK STARTED: Assessment flow agent execution "
                "for flow_id={flow_id}, phase={phase_value}, "
                "client={client_id}, engagement={eng_id}, user={user_id}",
                flow_id=flow_id,
                phase_value=phase.value,
                client_id=client_account_id,
                eng_id=engagement_id,
                user_id=user_id,
            )
        )

        # Get database session
        async for db in get_db():
            try:
                # Get master flow and assessment flow
                from app.repositories.crewai_flow_state_extensions_repository import (
                    CrewAIFlowStateExtensionsRepository,
                )
                from app.models.assessment_flow import AssessmentFlow
                from sqlalchemy import select

                # Query assessment flow to get master_flow_id
                result = await db.execute(
                    select(AssessmentFlow.master_flow_id).where(
                        AssessmentFlow.id == flow_id
                    )
                )
                master_flow_id = result.scalar_one_or_none()

                if not master_flow_id:
                    logger.error(
                        f"Assessment flow {flow_id} not found or has no master_flow_id"
                    )
                    return

                # Get master flow state and initialize repositories
                from app.repositories.assessment_flow_repository import (
                    AssessmentFlowRepository,
                )

                master_repo = CrewAIFlowStateExtensionsRepository(
                    db, client_account_id, engagement_id
                )
                assessment_repo = AssessmentFlowRepository(
                    db, client_account_id, engagement_id
                )

                master_flow = await master_repo.get_by_flow_id(str(master_flow_id))
                if not master_flow:
                    logger.error(f"Master flow not found for assessment {flow_id}")
                    return

                # Get phase configuration from flow config
                from app.services.flow_configs.assessment_flow_config import (
                    get_assessment_flow_config,
                )

                flow_config = get_assessment_flow_config()

                # Find the matching phase config
                phase_config = None
                for p in flow_config.phases:
                    if p.name == phase.value:
                        phase_config = p
                        break

                if not phase_config:
                    logger.error(f"No configuration found for phase {phase.value}")
                    return

                # Initialize execution engine
                from app.services.flow_orchestration.execution_engine_crew_assessment import (
                    ExecutionEngineAssessmentCrews,
                )
                from app.services.flow_orchestration.execution_engine_crew_utils import (
                    ExecutionEngineCrewUtils,
                )

                crew_utils = ExecutionEngineCrewUtils()
                crew_utils.db = db  # Add db attribute for execution engine
                execution_engine = ExecutionEngineAssessmentCrews(crew_utils)

                # Get assessment flow data for selected applications
                assessment_result = await db.execute(
                    select(AssessmentFlow.selected_application_ids).where(
                        AssessmentFlow.id == flow_id
                    )
                )
                selected_app_ids = assessment_result.scalar_one_or_none() or []

                # Build phase input from assessment flow data
                phase_input = {
                    "selected_application_ids": selected_app_ids,
                    "user_input": {},
                    "flow_id": flow_id,
                }

                # Execute the phase with CrewAI agents
                logger.info(f"🤖 Executing {phase.value} phase with CrewAI agents...")
                result = await execution_engine.execute_assessment_phase(
                    master_flow=master_flow,
                    phase_config=phase_config,
                    phase_input=phase_input,
                )

                # CRITICAL FIX (Issue #1048): Check if phase execution succeeded
                # execute_assessment_phase returns error dict instead of raising exception
                if result.get("status") == "error" or "error" in result:
                    error_msg = result.get(
                        "error", result.get("message", "Unknown error")
                    )
                    logger.error(
                        safe_log_format(
                            "[ISSUE-1048] ❌ BACKGROUND TASK FAILED: Assessment flow {flow_id} "
                            "phase {phase_value} execution failed: {error_msg}",
                            flow_id=flow_id,
                            phase_value=phase.value,
                            error_msg=error_msg,
                        )
                    )
                    # Keep flow in progress (phase failed but flow continues)
                    # Note: Using "in_progress" not "error" - AssessmentFlowStatus enum
                    await assessment_repo.update_flow_status(
                        flow_id,
                        "in_progress",
                    )
                    return  # Exit without logging success

                logger.info(
                    safe_log_format(
                        "[ISSUE-999] ✅ BACKGROUND TASK COMPLETED: Assessment flow {flow_id} "
                        "phase {phase_value} completed successfully. Agents executed and results stored.",
                        flow_id=flow_id,
                        phase_value=phase.value,
                    )
                )

                # Update flow status to reflect completion
                await assessment_repo.update_flow_status(
                    flow_id,
                    "in_progress",  # Keep in progress for next phase
                )

                break  # Exit the async for loop

            except Exception as e:
                logger.error(
                    safe_log_format(
                        "Assessment flow agent execution failed: {str_e}", str_e=str(e)
                    ),
                    exc_info=True,
                )
                # Keep flow in progress (agent execution failed)
                try:
                    await assessment_repo.update_flow_status(
                        flow_id,
                        "in_progress",
                    )
                except Exception:
                    pass  # Best effort
                break

    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to initialize assessment flow execution: {str_e}", str_e=str(e)
            ),
            exc_info=True,
        )


async def resume_assessment_flow_execution(
    flow_id: str,
    phase: AssessmentPhase,
    user_input: Dict[str, Any],
    client_account_id: str,
) -> None:
    """Resume assessment flow execution from specific phase.

    DEPRECATED: Use continue_assessment_flow instead for real agent execution.
    This stub remains for backward compatibility.

    Args:
        flow_id: Assessment flow identifier
        phase: Current assessment phase
        user_input: User input data for resuming the flow
        client_account_id: Client account ID
    """
    try:
        logger.warning(
            safe_log_format(
                "DEPRECATED: resume_assessment_flow_execution called for {flow_id}. "
                "Use continue_assessment_flow instead.",
                flow_id=flow_id,
            )
        )

        # This would integrate with the actual UnifiedAssessmentFlow
        # For now, simulate resume work
        await asyncio.sleep(2)  # Simulate resume work

        logger.info(
            safe_log_format(
                "Assessment flow {flow_id} resumed successfully", flow_id=flow_id
            )
        )

    except Exception as e:
        logger.error(
            safe_log_format("Assessment flow resume failed: {str_e}", str_e=str(e))
        )
        # await update_flow_error_state(flow_id, str(e))
