"""
Data Validation Phase Handler

Handles the data validation and synthesis phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.collection_flow import CollectionFlowError, CollectionFlowState, CollectionPhase, CollectionStatus
from app.services.crewai_flows.handlers.enhanced_error_handler import enhanced_error_handler
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class ValidationHandler:
    """Handles data validation phase of collection flow"""
    
    def __init__(self, flow_context, state_manager, services, crewai_service):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.crewai_service = crewai_service
    
    async def validate_data(self, state: CollectionFlowState, config: Dict[str, Any],
                           previous_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 6: Data validation and synthesis"""
        try:
            logger.info("✅ Starting data validation phase")
            
            # Update state
            state.status = CollectionStatus.VALIDATING_DATA
            state.current_phase = CollectionPhase.DATA_VALIDATION
            state.updated_at = datetime.utcnow()
            
            # Gather all data
            automated_data = state.collected_data
            manual_data = state.manual_responses
            
            # Integrate data
            integrated_data = await self.services.data_integration.integrate_collection_data(
                automated_data=automated_data,
                manual_data=manual_data,
                integration_rules=config.get("client_requirements", {}).get("integration_rules", {}),
                conflict_resolution=config.get("client_requirements", {}).get("conflict_resolution", "priority_based")
            )
            
            # Create data synthesis crew
            from app.services.crewai_flows.crews.collection.data_synthesis_crew import create_data_synthesis_crew
            
            crew = create_data_synthesis_crew(
                crewai_service=self.crewai_service,
                automated_data=automated_data,
                manual_data=manual_data,
                context={
                    "validation_rules": config.get("client_requirements", {}).get("validation_rules", {}),
                    "automation_tier": state.automation_tier.value
                }
            )
            
            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "integrated_data": integrated_data
                }
            )
            
            # Generate quality report
            quality_report = await self.services.quality_assessment.generate_final_quality_report(
                synthesized_data=integrated_data,
                phase_results=state.phase_results,
                automation_tier=state.automation_tier.value
            )
            
            # Calculate SIXR readiness
            sixr_readiness_score = await self.services.business_analyzer.calculate_sixr_readiness(
                synthesized_data=integrated_data,
                quality_report=quality_report,
                sixr_requirements=config.get("client_requirements", {}).get("sixr_requirements", {})
            )
            
            # Store validation results
            state.validation_results = {
                "synthesized_data": integrated_data,
                "quality_report": quality_report,
                "sixr_readiness": sixr_readiness_score,
                "validation_summary": crew_result
            }
            
            # Update final scores
            state.collection_quality_score = quality_report.get("overall_quality_score", 0.0)
            state.confidence_score = await self.services.confidence_scoring.calculate_final_confidence(
                synthesized_data=integrated_data,
                quality_report=quality_report,
                phase_results=state.phase_results
            )
            
            # Update progress
            state.progress = 95.0
            state.next_phase = CollectionPhase.FINALIZATION
            
            # Persist state
            await self.state_manager.save_state(state.to_dict())
            
            return {
                "phase": "data_validation",
                "status": "completed",
                "data_quality_score": state.collection_quality_score,
                "sixr_readiness_score": sixr_readiness_score,
                "next_phase": "finalization"
            }
            
        except Exception as e:
            logger.error(f"❌ Data validation failed: {e}")
            state.add_error("data_validation", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Data validation failed: {e}")