"""
Collection Executor for Manual Collection

Handles crew execution and orchestration for manual data collection.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.models.collection_flow import CollectionPhase, CollectionStatus
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class CollectionExecutor:
    """Executes manual data collection crews."""

    def __init__(self, flow_context, audit_service):
        """Initialize collection executor."""
        self.flow_context = flow_context
        self.audit_service = audit_service

    async def execute_manual_collection(
        self, flow_state, crewai_service, client_requirements
    ) -> Dict[str, Any]:
        """Execute manual data collection with user responses"""
        logger.info("📋 Executing manual data collection")

        # Update state
        flow_state.status = CollectionStatus.MANUAL_COLLECTION
        flow_state.current_phase = CollectionPhase.MANUAL_COLLECTION
        flow_state.updated_at = datetime.utcnow()

        # Get questionnaires and user inputs
        questionnaires = flow_state.questionnaires
        user_responses = flow_state.user_inputs.get("manual_responses", {})
        identified_gaps = flow_state.gap_analysis_results.get("identified_gaps", [])

        # Create manual collection crew
        crew_results = await self._execute_collection_crew(
            crewai_service,
            questionnaires,
            identified_gaps,
            flow_state.collected_data,
            user_responses,
        )

        # Log phase completion
        await self.audit_service.log_flow_event(
            flow_id=self.flow_context.flow_id,
            event_type="manual_collection_executed",
            event_data={
                "questionnaire_count": len(questionnaires),
                "response_count": len(user_responses),
                "gap_count": len(identified_gaps),
            },
        )

        return crew_results

    async def _execute_collection_crew(
        self, crewai_service, questionnaires, data_gaps, existing_data, user_responses
    ) -> Dict[str, Any]:
        """Create and execute the manual collection crew"""
        logger.info("🤖 Creating manual collection crew")

        # Import crew creation function
        from app.services.crewai_flows.crews.collection.manual_collection_crew import (
            create_manual_collection_crew,
        )

        # Create crew with context
        crew = create_manual_collection_crew(
            crewai_service=crewai_service,
            questionnaires=questionnaires,
            data_gaps=data_gaps,
            context={
                "existing_data": existing_data,
                "user_inputs": user_responses,
                "flow_id": self.flow_context.flow_id,
            },
        )

        # Execute with retry
        logger.info("🚀 Executing manual collection crew")
        crew_result = await retry_with_backoff(
            crew.kickoff,
            inputs={"questionnaires": questionnaires, "user_responses": user_responses},
        )

        return crew_result

    async def resume_collection(
        self, flow_state, user_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume manual collection with user responses.

        Args:
            flow_state: Current collection flow state
            user_inputs: User responses to questionnaires

        Returns:
            Dict containing resume results
        """
        logger.info(
            f"🔄 Resuming manual collection for flow {self.flow_context.flow_id}"
        )

        if not user_inputs or "manual_responses" not in user_inputs:
            return {
                "phase": "manual_collection",
                "status": "waiting_for_input",
                "message": "Manual responses required to continue",
                "requires_user_input": True,
            }

        # Store user responses
        flow_state.user_inputs["manual_responses"] = user_inputs["manual_responses"]
        flow_state.last_user_interaction = datetime.utcnow()

        # Execute manual collection with responses
        from app.services.crewai_flows.unified_collection_flow import (
            UnifiedCollectionFlow,
        )

        collection_flow = UnifiedCollectionFlow(
            crewai_service=None,  # Will be provided by execute method
            context=self.flow_context,
            flow_id=flow_state.flow_id,
        )

        # Continue with manual collection execution
        return await self.execute_manual_collection(
            flow_state,
            collection_flow.crewai_service,
            user_inputs.get("client_requirements", {}),
        )
