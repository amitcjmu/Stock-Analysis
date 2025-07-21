"""
Questionnaire Generation Phase Handler

Handles the questionnaire generation phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from app.models.collection_flow import (
    CollectionFlowState, CollectionPhase, CollectionStatus, 
    CollectionFlowError, AutomationTier
)
from app.services.crewai_flows.handlers.enhanced_error_handler import enhanced_error_handler
from app.services.crewai_flows.unified_collection_flow_modules.flow_utilities import save_questionnaires_to_db

logger = logging.getLogger(__name__)


class QuestionnaireGenerationHandler:
    """Handles questionnaire generation phase of collection flow"""
    
    def __init__(self, flow_context, state_manager, services, unified_flow_management):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.unified_flow_management = unified_flow_management
    
    async def generate_questionnaires(self, state: CollectionFlowState, config: Dict[str, Any],
                                     gap_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Generate adaptive questionnaires"""
        # Skip if no gaps or tier 1
        if gap_result["gaps_identified"] == 0 or state.automation_tier == AutomationTier.TIER_1:
            # Delegate to validation handler
            return None  # Signal to skip to validation
        
        try:
            logger.info("📝 Starting questionnaire generation phase")
            
            # Update state
            state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
            state.current_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
            state.updated_at = datetime.utcnow()
            
            # Get gap analysis results
            identified_gaps = state.gap_analysis_results.get("identified_gaps", [])
            
            # Generate questionnaires
            questionnaires = await self.services.questionnaire_generator.generate_questionnaires(
                data_gaps=identified_gaps,
                business_context=config.get("client_requirements", {}).get("business_context", {}),
                automation_tier=state.automation_tier.value
            )
            
            # Create adaptive forms
            form_configs = []
            for questionnaire in questionnaires:
                form_config = await self.services.adaptive_form_service.create_adaptive_form(
                    questionnaire_data=questionnaire,
                    gap_context=identified_gaps,
                    template_preferences=config.get("client_requirements", {}).get("form_preferences", {})
                )
                form_configs.append(form_config)
            
            # Save questionnaires to database
            saved_questionnaires = await save_questionnaires_to_db(
                questionnaires,
                self.flow_context,
                state.flow_id,
                state.automation_tier,
                state.detected_platforms
            )
            
            # Store in state
            state.questionnaires = saved_questionnaires
            state.phase_results["questionnaire_generation"] = {
                "questionnaires": saved_questionnaires,
                "form_configs": form_configs
            }
            
            # Update progress
            state.progress = 70.0
            state.next_phase = CollectionPhase.MANUAL_COLLECTION
            
            # Persist state
            await self.state_manager.save_state(state.to_dict())
            
            # Pause for user input
            state.pause_points.append("manual_collection_required")
            await self.unified_flow_management.pause_flow(
                reason="Questionnaires generated - manual collection required",
                phase="questionnaire_generation"
            )
            
            return {
                "phase": "questionnaire_generation",
                "status": "completed",
                "questionnaires_generated": len(questionnaires),
                "next_phase": "manual_collection",
                "requires_user_input": True
            }
            
        except Exception as e:
            logger.error(f"❌ Questionnaire generation failed: {e}")
            state.add_error("questionnaire_generation", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Questionnaire generation failed: {e}")