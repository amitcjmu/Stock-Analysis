"""
Questionnaire Generation Utilities

Helper functions and utilities for questionnaire generation phase handlers,
extracted from questionnaire_generation_handler.py for better modularity.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlowError,
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)

logger = logging.getLogger(__name__)


def get_next_phase_name(state: CollectionFlowState, questionnaire_type: str) -> str:
    """
    Determine the appropriate next phase name based on current state and questionnaire type.

    Args:
        state: Current collection flow state
        questionnaire_type: Type of questionnaire (bootstrap or detailed)

    Returns:
        Next phase name string
    """
    # For bootstrap questionnaires, typically advance to basic collection
    if questionnaire_type == "bootstrap":
        return "manual_collection"  # Bootstrap leads to manual data collection
    # For detailed questionnaires, usually continue with manual collection
    return "manual_collection"


async def check_loop_prevention(
    collection_orchestrator, state: CollectionFlowState, gap_result: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Check for infinite loop prevention and return early exit if needed"""
    if not await collection_orchestrator.prevent_infinite_loops(
        state, "questionnaire_generation", max_iterations=2
    ):
        logger.warning(
            f"Skipping questionnaire generation due to loop prevention for flow {state.flow_id}"
        )
        # Determine questionnaire type for proper next phase
        identified_gaps = gap_result.get("identified_gaps", []) if gap_result else []
        questionnaire_type = "bootstrap" if not identified_gaps else "detailed"
        next_phase = get_next_phase_name(state, questionnaire_type)

        return {
            "phase": "questionnaire_generation",
            "status": "skipped",
            "reason": "infinite_loop_prevention",
            "next_phase": next_phase,
        }
    return None


async def check_should_generate(
    collection_orchestrator,
    state: CollectionFlowState,
    gap_result: Dict[str, Any],
    questionnaire_type: str,
) -> Optional[Dict[str, Any]]:
    """Check if questionnaire should be generated and return early exit if not"""
    (
        should_generate,
        reason,
    ) = await collection_orchestrator.should_generate_questionnaire(
        state, gap_result, questionnaire_type
    )

    if not should_generate:
        logger.info(f"Skipping questionnaire generation: {reason}")

        # Get appropriate next phase
        next_phase = get_next_phase_name(state, questionnaire_type)

        # If bootstrap already exists, advance workflow and continue to next phase
        if questionnaire_type == "bootstrap":
            advancement_result = await collection_orchestrator.advance_to_next_phase(
                state
            )
            logger.info(
                f"Advanced workflow after bootstrap check: {advancement_result}"
            )
            # Update next_phase based on advancement result if available
            if advancement_result.get("advanced") and advancement_result.get(
                "new_phase"
            ):
                next_phase = advancement_result["new_phase"]

        return {
            "phase": "questionnaire_generation",
            "status": "skipped",
            "reason": reason,
            "questionnaires_generated": 0,
            "next_phase": next_phase,
            "workflow_advanced": questionnaire_type == "bootstrap",
        }
    return None


def prepare_questionnaire_config(
    state: CollectionFlowState,
    config: Dict[str, Any],
    identified_gaps: list,
    questionnaire_type: str,
) -> Dict[str, Any]:
    """Prepare questionnaire configuration"""
    return {
        "data_gaps": identified_gaps,
        "business_context": config.get("client_requirements", {}).get(
            "business_context", {}
        ),
        "automation_tier": state.automation_tier.value,
        "collection_flow_id": str(state.flow_id),  # Ensure string for serialization
        "questionnaire_type": questionnaire_type,  # Include type metadata
        "workflow_context": {
            "phase": state.current_phase.value,
            "progress": state.progress,
            "generation_timestamp": datetime.utcnow().isoformat(),
        },
    }


async def generate_questionnaires_core(
    services, questionnaire_config: Dict[str, Any]
) -> list:
    """Core questionnaire generation logic"""
    # Validate questionnaire generation service availability
    if not hasattr(services, "questionnaire_generator"):
        raise CollectionFlowError("Questionnaire generator service not available")

    try:
        questionnaires = await services.questionnaire_generator.generate_questionnaires(
            **questionnaire_config
        )

        # Validate questionnaire generation results
        if not questionnaires or not isinstance(questionnaires, list):
            raise CollectionFlowError("Invalid questionnaire generation result")

        return questionnaires

    except Exception as generation_error:
        logger.error(
            f"❌ Questionnaire generation service error: {type(generation_error).__name__}"
        )
        raise CollectionFlowError(
            f"Questionnaire generation failed: {type(generation_error).__name__}"
        )


async def create_adaptive_forms(
    services, questionnaires: list, identified_gaps: list, config: Dict[str, Any]
) -> list:
    """Create adaptive forms with validation"""
    form_configs = []

    # Validate adaptive form service availability
    if not hasattr(services, "adaptive_form_service"):
        logger.warning("Adaptive form service not available, skipping form creation")
        return form_configs

    try:
        for i, questionnaire in enumerate(questionnaires):
            # Validate questionnaire structure before form creation
            if not isinstance(questionnaire, dict):
                logger.warning(
                    f"Invalid questionnaire structure at index {i}, skipping form creation"
                )
                continue

            form_config = await services.adaptive_form_service.create_adaptive_form(
                questionnaire_data=questionnaire,
                gap_context=identified_gaps,
                template_preferences=config.get("client_requirements", {}).get(
                    "form_preferences", {}
                ),
            )

            if form_config:  # Only add valid form configs
                form_configs.append(form_config)

    except Exception as form_error:
        logger.error(f"❌ Adaptive form creation error: {type(form_error).__name__}")
        # Continue without forms rather than failing entire questionnaire generation
        form_configs = []
        logger.warning("Continuing questionnaire generation without adaptive forms")

    return form_configs


async def save_and_update_state(
    flow_context,
    state_manager,
    state: CollectionFlowState,
    questionnaires: list,
    form_configs: list,
    questionnaire_type: str,
    identified_gaps: list,
) -> None:
    """Save questionnaires and update state"""
    from app.services.crewai_flows.unified_collection_flow_modules.flow_utilities import (
        save_questionnaires_to_db,
    )

    # Save questionnaires to database
    saved_questionnaires = await save_questionnaires_to_db(
        questionnaires,
        flow_context,
        state.flow_id,
        state.automation_tier,
        state.detected_platforms,
    )

    # Store in state with enhanced metadata
    state.questionnaires = saved_questionnaires
    state.phase_results["questionnaire_generation"] = {
        "questionnaires": saved_questionnaires,
        "form_configs": form_configs,
        "questionnaire_type": questionnaire_type,
        "generated_at": datetime.utcnow().isoformat(),
        "gap_count": len(identified_gaps),
        "orchestrated": True,  # Mark as orchestrated generation
    }

    # Update progress based on questionnaire type
    if questionnaire_type == "bootstrap":
        state.progress = 40.0  # Bootstrap is earlier in process
    else:
        state.progress = 70.0  # Detailed questionnaires are later

    # Set next phase based on questionnaire type and orchestrator state
    state.next_phase = (
        CollectionPhase.MANUAL_COLLECTION
    )  # Default to manual collection for now


async def record_orchestrator_submission(
    collection_orchestrator,
    state: CollectionFlowState,
    questionnaire_type: str,
    questionnaires: list,
    identified_gaps: list,
    form_configs: list,
) -> None:
    """Record questionnaire generation with orchestrator"""
    from app.services.unified_discovery.workflow_models import (
        QuestionnaireType,
    )

    q_type = (
        QuestionnaireType.BOOTSTRAP
        if questionnaire_type == "bootstrap"
        else QuestionnaireType.DETAILED
    )

    # Record questionnaire generation with enhanced orchestrator if available
    try:
        if (
            hasattr(collection_orchestrator, "enhanced_orchestrator")
            and collection_orchestrator.enhanced_orchestrator
        ):
            await collection_orchestrator.enhanced_orchestrator.record_questionnaire_submission(
                state,
                q_type,
                {
                    "questionnaires_generated": len(questionnaires),
                    "responses": {},  # Empty for generation, not submission
                    "completion_percentage": 0.0,  # Generation complete, not submission
                    "generation_metadata": {
                        "type": questionnaire_type,
                        "gaps_addressed": len(identified_gaps),
                        "forms_created": len(form_configs),
                    },
                },
            )
        else:
            logger.warning(
                "Enhanced orchestrator not available, skipping submission recording"
            )

    except Exception as orchestrator_error:
        logger.error(
            f"❌ Failed to record questionnaire submission: {type(orchestrator_error).__name__}"
        )
        # Continue execution rather than failing - this is non-critical


async def commit_database_transaction(flow_context) -> None:
    """Ensure database commit for successful operations"""
    try:
        if hasattr(flow_context, "db_session") and flow_context.db_session:
            await flow_context.db_session.commit()
            logger.info(
                "✅ Database transaction committed after questionnaire generation"
            )
    except Exception as commit_error:
        logger.error(f"❌ Failed to commit database transaction: {commit_error}")
        # Try to rollback after failed commit
        try:
            await flow_context.db_session.rollback()
        except Exception as rollback_error:
            logger.error(
                f"❌ Failed to rollback after commit failure: {rollback_error}"
            )
        raise CollectionFlowError(
            f"Failed to persist questionnaire generation: {type(commit_error).__name__}"
        )


async def finalize_generation(
    collection_orchestrator,
    unified_flow_management,
    state: CollectionFlowState,
    questionnaire_type: str,
) -> Dict[str, Any]:
    """Finalize questionnaire generation with workflow advancement and pause"""
    # Advance workflow if appropriate
    advancement_result = await collection_orchestrator.advance_to_next_phase(state)

    # Get next phase name
    next_phase_name = get_next_phase_name(state, questionnaire_type)

    # Pause for user input
    state.pause_points.append("manual_collection_required")
    await unified_flow_management.pause_flow(
        reason=f"{questionnaire_type.title()} questionnaires generated - manual collection required",
        phase="questionnaire_generation",
    )

    return {
        "phase": "questionnaire_generation",
        "status": "completed",
        "questionnaire_type": questionnaire_type,
        "next_phase": next_phase_name,
        "requires_user_input": True,
        "workflow_advanced": advancement_result.get("advanced", False),
        "orchestration_applied": True,
    }


async def handle_generation_error(
    flow_context, state: CollectionFlowState, e: Exception
) -> None:
    """Handle questionnaire generation errors with proper rollback and logging"""
    # Ensure database rollback on errors
    try:
        if hasattr(flow_context, "db_session") and flow_context.db_session:
            await flow_context.db_session.rollback()
            logger.info(
                "🔄 Database transaction rolled back due to questionnaire generation error"
            )
    except Exception as rollback_error:
        logger.error(f"❌ Failed to rollback database transaction: {rollback_error}")

    # Use secure logging for errors
    logger.error(
        safe_log_format(
            "❌ Questionnaire generation failed: {error_type}, Flow: {flow_id}",
            error_type=type(e).__name__,
            flow_id=str(state.flow_id),
        )
    )

    # Add error to state with sanitized message
    if hasattr(state, "add_error"):
        state.add_error(
            "questionnaire_generation", f"Generation failed: {type(e).__name__}"
        )

    raise CollectionFlowError(f"Questionnaire generation failed: {type(e).__name__}")


async def handle_no_questionnaires_generated(
    state: CollectionFlowState,
    questionnaire_type: str,
    flow_context=None,
    state_manager=None,
) -> Dict[str, Any]:
    """Handle the case when no questionnaires are generated"""
    logger.warning(f"No questionnaires generated for flow {state.flow_id}")

    # CC: Update state to mark questionnaire generation as completed with 0 questionnaires
    if hasattr(state, "set_phase_status"):
        state.set_phase_status("questionnaire_generation", "completed")

    # CC: Persist state changes before returning to maintain workflow consistency
    if flow_context and state_manager:
        try:
            await state_manager.save_state(state)
            # Commit database transaction if available
            if hasattr(flow_context, "db_session") and flow_context.db_session:
                await flow_context.db_session.commit()
                logger.debug("✅ State persisted after no questionnaires generated")
        except Exception as save_error:
            logger.error(
                f"❌ Failed to persist state before early return: {save_error}"
            )
            # Continue execution - this is not critical enough to fail the entire operation

    return {
        "phase": "questionnaire_generation",
        "status": "completed",
        "questionnaire_type": questionnaire_type,
        "questionnaires_generated": 0,
        "next_phase": get_next_phase_name(state, questionnaire_type),
        "requires_user_input": False,
        "warning": "No questionnaires were generated based on current data gaps",
    }


def should_skip_detailed_questionnaire(
    state: CollectionFlowState, questionnaire_type: str
) -> bool:
    """Check if detailed questionnaire generation should be skipped for Tier 1 flows"""
    return (
        state.automation_tier == AutomationTier.TIER_1
        and questionnaire_type != "bootstrap"
    )


def determine_questionnaire_type(identified_gaps: list) -> str:
    """Determine questionnaire type based on gap analysis"""
    return "bootstrap" if not identified_gaps else "detailed"


def update_state_for_generation(state: CollectionFlowState) -> None:
    """Update state for questionnaire generation phase"""
    state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
    state.current_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
    state.updated_at = datetime.utcnow()
