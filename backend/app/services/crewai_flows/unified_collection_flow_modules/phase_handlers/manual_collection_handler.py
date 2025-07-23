"""
Manual Collection Phase Handler

Handles the manual data collection phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.collection_flow import (CollectionFlowError,
                                        CollectionFlowState, CollectionPhase,
                                        CollectionStatus)
from app.services.crewai_flows.handlers.enhanced_error_handler import \
    enhanced_error_handler
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class ManualCollectionHandler:
    """Handles manual collection phase of collection flow"""

    def __init__(self, flow_context, state_manager, services, crewai_service):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.crewai_service = crewai_service

    async def manual_collection(
        self,
        state: CollectionFlowState,
        config: Dict[str, Any],
        questionnaire_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 5: Manual data collection"""
        try:
            logger.info("👤 Starting manual collection phase")

            # Update state
            state.status = CollectionStatus.MANUAL_COLLECTION
            state.current_phase = CollectionPhase.MANUAL_COLLECTION
            state.updated_at = datetime.utcnow()

            # Get questionnaires and gaps
            questionnaires = state.questionnaires
            identified_gaps = state.gap_analysis_results.get("identified_gaps", [])

            # Create manual collection crew
            from app.services.crewai_flows.crews.collection.manual_collection_crew import \
                create_manual_collection_crew

            crew = create_manual_collection_crew(
                crewai_service=self.crewai_service,
                questionnaires=questionnaires,
                data_gaps=identified_gaps,
                context={
                    "existing_data": state.collected_data,
                    "user_inputs": state.user_inputs,
                },
            )

            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "questionnaires": questionnaires,
                    "user_responses": state.user_inputs.get("manual_responses", {}),
                },
            )

            # Process responses
            responses = crew_result.get("responses", [])
            validation_results = crew_result.get("validation", {})

            # Validate responses
            validated_responses = (
                await self.services.validation_service.validate_questionnaire_responses(
                    responses=responses,
                    validation_rules=config.get("client_requirements", {}).get(
                        "validation_rules", {}
                    ),
                    gap_context=identified_gaps,
                )
            )

            # Store in state
            state.manual_responses = validated_responses
            state.phase_results["manual_collection"] = {
                "responses": validated_responses,
                "validation_results": validation_results,
                "remaining_gaps": crew_result.get("unresolved_gaps", []),
            }

            # Update progress
            state.progress = 85.0
            state.next_phase = CollectionPhase.DATA_VALIDATION

            # Persist state
            await self.state_manager.save_state(state.to_dict())

            return {
                "phase": "manual_collection",
                "status": "completed",
                "responses_collected": len(validated_responses),
                "validation_pass_rate": validation_results.get("pass_rate", 0.0),
                "next_phase": "data_validation",
            }

        except Exception as e:
            logger.error(f"❌ Manual collection failed: {e}")
            state.add_error("manual_collection", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Manual collection failed: {e}")
