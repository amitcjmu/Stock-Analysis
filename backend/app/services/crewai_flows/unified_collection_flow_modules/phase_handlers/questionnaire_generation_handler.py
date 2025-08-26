"""
Questionnaire Generation Phase Handler

Handles the questionnaire generation phase of the collection flow with
enhanced workflow progression and bootstrap questionnaire prevention.
"""

import logging
from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.models.collection_flow import CollectionFlowState
from app.services.unified_discovery.collection_orchestrator import (
    CollectionOrchestrator,
)

# Import utility functions
from .questionnaire_utilities import (
    check_loop_prevention,
    check_should_generate,
    prepare_questionnaire_config,
    generate_questionnaires_core,
    create_adaptive_forms,
    save_and_update_state,
    record_orchestrator_submission,
    commit_database_transaction,
    finalize_generation,
    handle_generation_error,
    handle_no_questionnaires_generated,
    should_skip_detailed_questionnaire,
    determine_questionnaire_type,
    update_state_for_generation,
)

logger = logging.getLogger(__name__)


class QuestionnaireGenerationHandler:
    """Handles questionnaire generation phase of collection flow with orchestration"""

    def __init__(
        self,
        flow_context,
        state_manager,
        services,
        unified_flow_management,
        collection_orchestrator: Optional[CollectionOrchestrator] = None,
    ):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.unified_flow_management = unified_flow_management

        # Initialize collection orchestrator for workflow management
        if collection_orchestrator:
            self.collection_orchestrator = collection_orchestrator
        else:
            # Create orchestrator with context from flow_context
            context = RequestContext(
                client_account_id=flow_context.client_account_id,
                engagement_id=flow_context.engagement_id,
                user_id=flow_context.user_id,
            )
            self.collection_orchestrator = CollectionOrchestrator(
                db_session=flow_context.db_session, context=context
            )

    async def generate_questionnaires(
        self,
        state: CollectionFlowState,
        config: Dict[str, Any],
        gap_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Phase 4: Generate adaptive questionnaires with bootstrap prevention.

        Enhanced version that checks for existing bootstrap questionnaires
        to prevent regeneration and manages workflow progression.
        """
        try:
            logger.info("📝 Starting questionnaire generation phase with orchestration")

            # Check for infinite loop prevention
            loop_check = await check_loop_prevention(
                self.collection_orchestrator, state, gap_result
            )
            if loop_check:
                return loop_check

            # Determine questionnaire type based on gap analysis
            identified_gaps = (
                gap_result.get("identified_gaps", []) if gap_result else []
            )
            questionnaire_type = determine_questionnaire_type(identified_gaps)

            # Check if questionnaire should be generated
            should_generate_check = await check_should_generate(
                self.collection_orchestrator, state, gap_result, questionnaire_type
            )
            if should_generate_check:
                return should_generate_check

            # Skip only for Tier 1 (manual/template) flows for non-bootstrap questionnaires
            if should_skip_detailed_questionnaire(state, questionnaire_type):
                logger.info(
                    "Skipping detailed questionnaire generation for Tier 1 flow"
                )
                return None  # Signal to skip to validation

            # Update state
            update_state_for_generation(state)

            # Get gap analysis results - use both sources for identified gaps
            if not identified_gaps:
                identified_gaps = state.gap_analysis_results.get("identified_gaps", [])

            # Prepare questionnaire configuration
            questionnaire_config = prepare_questionnaire_config(
                state, config, identified_gaps, questionnaire_type
            )

            # Generate questionnaires
            questionnaires = await generate_questionnaires_core(
                self.services, questionnaire_config
            )

            # Handle case of no questionnaires generated
            if len(questionnaires) == 0:
                return handle_no_questionnaires_generated(state, questionnaire_type)

            # Create adaptive forms
            form_configs = await create_adaptive_forms(
                self.services, questionnaires, identified_gaps, config
            )

            # Save and update state
            await save_and_update_state(
                self.flow_context,
                self.state_manager,
                state,
                questionnaires,
                form_configs,
                questionnaire_type,
                identified_gaps,
            )

            # Record with orchestrator
            await record_orchestrator_submission(
                self.collection_orchestrator,
                state,
                questionnaire_type,
                questionnaires,
                identified_gaps,
                form_configs,
            )

            # Persist state and commit transaction
            await self.state_manager.save_state(state.to_dict())
            await commit_database_transaction(self.flow_context)

            # Finalize generation
            result = await finalize_generation(
                self.collection_orchestrator,
                self.unified_flow_management,
                state,
                questionnaire_type,
            )
            result["questionnaires_generated"] = len(questionnaires)
            return result

        except Exception as e:
            await handle_generation_error(self.flow_context, state, e)

    async def check_bootstrap_questionnaire_exists(
        self, state: CollectionFlowState
    ) -> bool:
        """
        Direct method to check if bootstrap questionnaire already exists.

        This is a convenience method that delegates to the collection orchestrator
        for consistent bootstrap questionnaire checking.

        Args:
            state: Current collection flow state

        Returns:
            True if bootstrap questionnaire exists, False otherwise
        """
        try:
            return (
                await self.collection_orchestrator.check_bootstrap_questionnaire_exists(
                    state
                )
            )
        except Exception as e:
            logger.error(f"Error checking bootstrap questionnaire: {e}")
            return False

    async def get_completion_detection_logic(
        self, state: CollectionFlowState
    ) -> Dict[str, Any]:
        """
        Get completion detection logic for the questionnaire generation phase.

        Returns comprehensive information about questionnaire completion status
        and readiness for next phase transitions.

        Args:
            state: Current collection flow state

        Returns:
            Dictionary with completion analysis
        """
        try:
            return await self.collection_orchestrator.detect_completion_status(state)
        except Exception as e:
            logger.error(f"Error getting completion detection logic: {e}")
            return {
                "flow_id": state.flow_id,
                "error": str(e),
                "completion_checks": {},
                "ready_for_next_phase": False,
            }
