"""
Manual Collection Phase Manager

Handles the orchestration of manual data collection in the collection flow.
This manager coordinates questionnaire generation and response collection.
"""

import logging
from typing import Any, Dict, Optional

from app.services.collection_flow import QualityAssessmentService
from app.services.crewai_flows.handlers.enhanced_error_handler import (
    enhanced_error_handler,
)
from app.services.manual_collection import DataIntegrationService

from .collection_executor import CollectionExecutor
from .questionnaire_handler import QuestionnaireHandler
from .response_processor import ResponseProcessor

logger = logging.getLogger(__name__)


class ManualCollectionManager:
    """
    Manages the manual collection phase of the collection flow.

    This manager handles:
    - Questionnaire generation based on gaps
    - Manual collection crew execution
    - Response validation and integration
    - Progress tracking
    - Pause/resume for user input
    """

    def __init__(self, flow_context, state_manager, audit_service):
        """Initialize the manual collection manager."""
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.audit_service = audit_service

        # Initialize modular components
        self.questionnaire_handler = QuestionnaireHandler(
            flow_context, state_manager, audit_service
        )
        self.collection_executor = CollectionExecutor(flow_context, audit_service)
        self.response_processor = ResponseProcessor(flow_context, state_manager)

        # Initialize remaining services
        self.data_integration = DataIntegrationService(
            flow_context.db_session, flow_context
        )
        self.quality_assessment = QualityAssessmentService(
            flow_context.db_session, flow_context.context
        )

    async def execute(
        self,
        flow_state,
        crewai_service,
        client_requirements,
        skip_generation: bool = False,
    ) -> Dict[str, Any]:
        """Execute the manual collection phase."""
        try:
            logger.info(
                f"👤 Starting manual collection for flow {self.flow_context.flow_id}"
            )

            # Check if we need questionnaire generation
            if not skip_generation and not self._has_questionnaires(flow_state):
                return await self.questionnaire_handler.generate_questionnaires(
                    flow_state, client_requirements
                )

            # Execute manual collection
            return await self._execute_manual_collection(
                flow_state, crewai_service, client_requirements
            )

        except Exception as e:
            logger.error(f"❌ Manual collection failed: {e}")
            flow_state.add_error("manual_collection", str(e))
            await enhanced_error_handler.handle_critical_flow_error(
                flow_state.flow_id, e, flow_state
            )
            raise

    async def resume(
        self, flow_state, user_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resume manual collection with user responses."""
        return await self.collection_executor.resume_collection(flow_state, user_inputs)

    async def _execute_manual_collection(
        self, flow_state, crewai_service, client_requirements
    ) -> Dict[str, Any]:
        """Execute manual data collection with user responses"""
        # Execute collection crew
        crew_results = await self.collection_executor.execute_manual_collection(
            flow_state, crewai_service, client_requirements
        )

        # Get user responses and gaps
        user_responses = flow_state.user_inputs.get("manual_responses", {})
        identified_gaps = flow_state.gap_analysis_results.get("identified_gaps", [])

        # Process and validate responses
        validated_responses = await self.response_processor.process_responses(
            crew_results, user_responses, identified_gaps, client_requirements
        )

        # Update progress tracking
        await self.response_processor.update_progress_tracking(
            flow_state, validated_responses
        )

        # Update flow state
        await self.response_processor.update_flow_state(
            flow_state, validated_responses, crew_results
        )

        # Log completion
        await self.audit_service.log_flow_event(
            flow_id=self.flow_context.flow_id,
            event_type="manual_collection_completed",
            event_data={
                "responses_collected": len(validated_responses["responses"]),
                "validation_pass_rate": validated_responses["validation_results"][
                    "pass_rate"
                ],
                "remaining_gaps": len(validated_responses["remaining_gaps"]),
            },
        )

        return {
            "phase": "manual_collection",
            "status": "completed",
            "responses_collected": len(validated_responses["responses"]),
            "validation_pass_rate": validated_responses["validation_results"][
                "pass_rate"
            ],
            "next_phase": "data_validation",
            "collection_complete": True,
        }

    def _has_questionnaires(self, flow_state) -> bool:
        """Check if questionnaires are already generated"""
        return bool(getattr(flow_state, "questionnaires", None))
