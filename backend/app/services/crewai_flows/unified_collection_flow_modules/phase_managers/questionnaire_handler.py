"""
Questionnaire Handler for Manual Collection

Handles questionnaire generation and adaptive form creation.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.collection_flow import CollectionPhase, CollectionStatus
from app.services.ai_analysis import AdaptiveQuestionnaireGenerator
from app.services.crewai_flows.handlers.unified_flow_management import (
    UnifiedFlowManagement,
)
from app.services.manual_collection import AdaptiveFormService

logger = logging.getLogger(__name__)


class QuestionnaireHandler:
    """Handles questionnaire generation for manual collection."""

    def __init__(self, flow_context, state_manager, audit_service):
        """Initialize questionnaire handler."""
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.audit_service = audit_service

        # Initialize services
        self.questionnaire_generator = AdaptiveQuestionnaireGenerator()
        self.adaptive_form_service = AdaptiveFormService(
            flow_context.db_session, flow_context
        )

    async def generate_questionnaires(
        self, flow_state, client_requirements
    ) -> Dict[str, Any]:
        """Generate adaptive questionnaires based on gaps"""
        logger.info("📝 Generating adaptive questionnaires")

        # Update state
        flow_state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
        flow_state.current_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
        flow_state.updated_at = datetime.utcnow()

        # Get gap analysis results
        identified_gaps = flow_state.gap_analysis_results.get("identified_gaps", [])

        # Generate questionnaires using AI
        questionnaires = await self.questionnaire_generator.generate_questionnaires(
            data_gaps=identified_gaps,
            business_context=client_requirements.get("business_context", {}),
            automation_tier=flow_state.automation_tier.value,
        )

        # Create adaptive forms
        form_configs = []
        for questionnaire in questionnaires:
            form_config = await self.adaptive_form_service.create_adaptive_form(
                questionnaire_data=questionnaire,
                gap_context=identified_gaps,
                template_preferences=client_requirements.get("form_preferences", {}),
            )
            form_configs.append(form_config)

        # Update state
        flow_state.questionnaires = questionnaires
        flow_state.phase_results["questionnaire_generation"] = {
            "questionnaires": questionnaires,
            "form_configs": form_configs,
            "generation_timestamp": datetime.utcnow().isoformat(),
        }

        # Update progress
        flow_state.progress = 70.0
        flow_state.next_phase = CollectionPhase.MANUAL_COLLECTION

        # Persist state
        await self.state_manager.save_state(flow_state.to_dict())

        # Log event
        await self.audit_service.log_flow_event(
            flow_id=self.flow_context.flow_id,
            event_type="questionnaires_generated",
            event_data={
                "questionnaire_count": len(questionnaires),
                "form_count": len(form_configs),
                "gap_count": len(identified_gaps),
            },
        )

        # Pause for user input
        flow_state.pause_points.append("manual_collection_required")
        unified_flow_management = UnifiedFlowManagement(flow_state)
        await unified_flow_management.pause_flow(
            reason="Questionnaires generated - manual collection required",
            phase="questionnaire_generation",
        )

        return {
            "phase": "questionnaire_generation",
            "status": "completed",
            "questionnaires_generated": len(questionnaires),
            "next_phase": "manual_collection",
            "requires_user_input": True,
            "pause_reason": "awaiting_manual_responses",
        }
