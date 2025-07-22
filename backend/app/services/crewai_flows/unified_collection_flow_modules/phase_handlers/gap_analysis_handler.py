"""
Gap Analysis Phase Handler

Handles the gap analysis phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Any, Dict

from app.models.collection_flow import (
    AutomationTier,
    CollectionFlowError,
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)
from app.services.crewai_flows.handlers.enhanced_error_handler import enhanced_error_handler
from app.services.crewai_flows.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


class GapAnalysisHandler:
    """Handles gap analysis phase of collection flow"""
    
    def __init__(self, flow_context, state_manager, services, crewai_service):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.crewai_service = crewai_service
    
    async def analyze_gaps(self, state: CollectionFlowState, config: Dict[str, Any],
                          collection_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Gap analysis"""
        try:
            logger.info("🔎 Starting gap analysis phase")
            
            # Update state
            state.status = CollectionStatus.ANALYZING_GAPS
            state.current_phase = CollectionPhase.GAP_ANALYSIS
            state.updated_at = datetime.utcnow()
            
            # Get collected data
            collected_data = state.collected_data
            collection_gaps = state.phase_results.get("automated_collection", {}).get("identified_gaps", [])
            
            # Perform AI gap analysis
            gap_analysis_result = await self.services.gap_analysis_agent.analyze_data_gaps(
                collected_data=collected_data,
                existing_gaps=collection_gaps,
                sixr_requirements=config.get("client_requirements", {}).get("sixr_requirements", {}),
                automation_tier=state.automation_tier.value
            )
            
            # Create gap analysis crew
            from app.services.crewai_flows.crews.collection.gap_analysis_crew import create_gap_analysis_crew
            
            crew = create_gap_analysis_crew(
                crewai_service=self.crewai_service,
                collected_data=collected_data,
                sixr_requirements=config.get("client_requirements", {}).get("sixr_requirements", {}),
                context={
                    "automation_tier": state.automation_tier.value,
                    "existing_gaps": collection_gaps
                }
            )
            
            # Execute crew
            crew_result = await retry_with_backoff(
                crew.kickoff,
                inputs={
                    "collected_data": collected_data,
                    "ai_analysis": gap_analysis_result
                }
            )
            
            # Process results
            identified_gaps = crew_result.get("data_gaps", [])
            gap_categories = crew_result.get("gap_categories", {})
            sixr_impact = crew_result.get("sixr_impact_analysis", {})
            
            # Store in state
            state.gap_analysis_results = {
                "identified_gaps": identified_gaps,
                "gap_categories": gap_categories,
                "sixr_impact": sixr_impact,
                "recommendations": crew_result.get("recommendations", [])
            }
            state.phase_results["gap_analysis"] = crew_result
            
            # Update progress
            state.progress = 55.0
            
            # Determine next phase based on gaps
            if not identified_gaps or state.automation_tier == AutomationTier.TIER_1:
                state.next_phase = CollectionPhase.DATA_VALIDATION
            else:
                state.next_phase = CollectionPhase.QUESTIONNAIRE_GENERATION
            
            # Persist state
            await self.state_manager.save_state(state.to_dict())
            
            return {
                "phase": "gap_analysis",
                "status": "completed",
                "gaps_identified": len(identified_gaps),
                "sixr_impact_score": sixr_impact.get("overall_impact_score", 0.0),
                "next_phase": state.next_phase.value
            }
            
        except Exception as e:
            logger.error(f"❌ Gap analysis failed: {e}")
            state.add_error("gap_analysis", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Gap analysis failed: {e}")