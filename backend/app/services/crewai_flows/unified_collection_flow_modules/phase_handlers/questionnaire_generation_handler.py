"""
Questionnaire Generation Phase Handler

Handles the questionnaire generation phase of the collection flow with
enhanced workflow progression and bootstrap questionnaire prevention.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlowError,
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)
from app.services.crewai_flows.handlers.enhanced_error_handler import (
    enhanced_error_handler,
)
from app.services.crewai_flows.unified_collection_flow_modules.flow_utilities import (
    save_questionnaires_to_db,
)
from app.services.unified_discovery.collection_orchestrator import (
    CollectionOrchestrator,
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
            if not await self.collection_orchestrator.prevent_infinite_loops(
                state, "questionnaire_generation", max_iterations=2
            ):
                logger.warning(
                    f"Skipping questionnaire generation due to loop prevention for flow {state.flow_id}"
                )
                return {
                    "phase": "questionnaire_generation",
                    "status": "skipped",
                    "reason": "infinite_loop_prevention",
                    "next_phase": "manual_collection",
                }

            # Determine questionnaire type based on gap analysis
            identified_gaps = (
                gap_result.get("identified_gaps", []) if gap_result else []
            )
            questionnaire_type = "bootstrap" if not identified_gaps else "detailed"

            # Check if questionnaire should be generated using orchestrator
            should_generate, reason = (
                await self.collection_orchestrator.should_generate_questionnaire(
                    state, gap_result, questionnaire_type
                )
            )

            if not should_generate:
                logger.info(f"Skipping questionnaire generation: {reason}")

                # If bootstrap already exists, advance workflow and continue to next phase
                if questionnaire_type == "bootstrap":
                    advancement_result = (
                        await self.collection_orchestrator.advance_to_next_phase(state)
                    )
                    logger.info(
                        f"Advanced workflow after bootstrap check: {advancement_result}"
                    )

                return {
                    "phase": "questionnaire_generation",
                    "status": "skipped",
                    "reason": reason,
                    "questionnaires_generated": 0,
                    "next_phase": "manual_collection",
                    "workflow_advanced": questionnaire_type == "bootstrap",
                }

            # Skip only for Tier 1 (manual/template) flows for non-bootstrap questionnaires
            if (
                state.automation_tier == AutomationTier.TIER_1
                and questionnaire_type != "bootstrap"
            ):
                logger.info(
                    "Skipping detailed questionnaire generation for Tier 1 flow"
                )
                return None  # Signal to skip to validation

            # Update state
            state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
            state.current_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
            state.updated_at = datetime.utcnow()

            # Get gap analysis results - use both sources for identified gaps
            identified_gaps = (
                gap_result.get("identified_gaps", []) if gap_result else []
            )
            if not identified_gaps:
                identified_gaps = state.gap_analysis_results.get("identified_gaps", [])

            # Generate questionnaires with enhanced metadata
            questionnaire_config = {
                "data_gaps": identified_gaps,
                "business_context": config.get("client_requirements", {}).get(
                    "business_context", {}
                ),
                "automation_tier": state.automation_tier.value,
                "collection_flow_id": state.flow_id,
                "questionnaire_type": questionnaire_type,  # Include type metadata
                "workflow_context": {
                    "phase": state.current_phase.value,
                    "progress": state.progress,
                    "generation_timestamp": datetime.utcnow().isoformat(),
                },
            }

            questionnaires = (
                await self.services.questionnaire_generator.generate_questionnaires(
                    **questionnaire_config
                )
            )

            # Create adaptive forms
            form_configs = []
            for questionnaire in questionnaires:
                form_config = (
                    await self.services.adaptive_form_service.create_adaptive_form(
                        questionnaire_data=questionnaire,
                        gap_context=identified_gaps,
                        template_preferences=config.get("client_requirements", {}).get(
                            "form_preferences", {}
                        ),
                    )
                )
                form_configs.append(form_config)

            # Save questionnaires to database
            saved_questionnaires = await save_questionnaires_to_db(
                questionnaires,
                self.flow_context,
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

            state.next_phase = CollectionPhase.MANUAL_COLLECTION

            # Record questionnaire generation with orchestrator
            from app.services.unified_discovery.workflow_models import (
                QuestionnaireType,
            )

            q_type = (
                QuestionnaireType.BOOTSTRAP
                if questionnaire_type == "bootstrap"
                else QuestionnaireType.DETAILED
            )

            await self.collection_orchestrator.enhanced_orchestrator.record_questionnaire_submission(
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

            # Persist state
            await self.state_manager.save_state(state.to_dict())

            # Advance workflow if appropriate
            advancement_result = (
                await self.collection_orchestrator.advance_to_next_phase(state)
            )

            # Pause for user input
            state.pause_points.append("manual_collection_required")
            await self.unified_flow_management.pause_flow(
                reason=f"{questionnaire_type.title()} questionnaires generated - manual collection required",
                phase="questionnaire_generation",
            )

            return {
                "phase": "questionnaire_generation",
                "status": "completed",
                "questionnaire_type": questionnaire_type,
                "questionnaires_generated": len(questionnaires),
                "next_phase": "manual_collection",
                "requires_user_input": True,
                "workflow_advanced": advancement_result.get("advanced", False),
                "orchestration_applied": True,
            }

        except Exception as e:
            logger.error(f"❌ Questionnaire generation failed: {e}")
            state.add_error("questionnaire_generation", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Questionnaire generation failed: {e}")

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
