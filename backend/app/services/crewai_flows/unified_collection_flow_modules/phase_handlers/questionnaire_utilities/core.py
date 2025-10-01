"""
Questionnaire Utilities - Core Logic

Core questionnaire generation and validation functions.
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlowError,
    CollectionFlowState,
)
from .utils import get_next_phase_name

logger = logging.getLogger(__name__)


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


async def generate_questionnaires_core(
    services, questionnaire_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
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
            f"❌ Questionnaire generation service error: {type(generation_error).__name__}",
            exc_info=True,  # Include stack trace for debugging
        )
        raise CollectionFlowError(
            f"Questionnaire generation failed: {type(generation_error).__name__}: {str(generation_error)}"
        ) from generation_error  # Preserve original exception context


async def create_adaptive_forms(
    services,
    questionnaires: List[Dict[str, Any]],
    identified_gaps: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
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


def should_skip_detailed_questionnaire(
    questionnaire_type: str, state: CollectionFlowState
) -> bool:
    """
    Determine if detailed questionnaire should be skipped based on automation tier.

    Args:
        questionnaire_type: Type of questionnaire being generated
        state: Current collection flow state

    Returns:
        True if questionnaire should be skipped, False otherwise
    """
    # Only detailed questionnaires can be skipped based on automation tier
    if questionnaire_type != "detailed":
        return False

    # Skip detailed questionnaires for high automation tiers
    if state.automation_tier in [AutomationTier.PREMIUM, AutomationTier.ENTERPRISE]:
        logger.info(
            safe_log_format(
                "Skipping detailed questionnaire for high automation tier",
                automation_tier=state.automation_tier.value,
                flow_id=str(state.flow_id),
            )
        )
        return True

    return False
