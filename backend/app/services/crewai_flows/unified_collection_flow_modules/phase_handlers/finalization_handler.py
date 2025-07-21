"""
Finalization Phase Handler

Handles the finalization phase of the collection flow.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from app.models.collection_flow import (
    CollectionFlowState, CollectionPhase, CollectionStatus, CollectionFlowError
)
from app.services.crewai_flows.handlers.enhanced_error_handler import enhanced_error_handler

logger = logging.getLogger(__name__)


class FinalizationHandler:
    """Handles finalization phase of collection flow"""
    
    def __init__(self, flow_context, state_manager, services, unified_flow_management):
        self.flow_context = flow_context
        self.state_manager = state_manager
        self.services = services
        self.unified_flow_management = unified_flow_management
    
    async def finalize_collection(self, state: CollectionFlowState, config: Dict[str, Any],
                                 validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 7: Finalize collection and prepare for handoff"""
        try:
            logger.info("🏁 Starting collection finalization")
            
            # Update state
            state.status = CollectionStatus.COMPLETED
            state.current_phase = CollectionPhase.FINALIZATION
            state.completed_at = datetime.utcnow()
            state.updated_at = datetime.utcnow()
            
            # Prepare assessment package
            assessment_package = {
                "flow_id": state.flow_id,
                "client_account_id": state.client_account_id,
                "engagement_id": state.engagement_id,
                "collection_summary": {
                    "automation_tier": state.automation_tier.value,
                    "collection_quality_score": state.collection_quality_score,
                    "confidence_score": state.confidence_score,
                    "platforms_collected": len(state.detected_platforms),
                    "gap_analysis_complete": bool(state.gap_analysis_results)
                },
                "collected_data": state.validation_results.get("synthesized_data", {}),
                "gap_analysis": state.gap_analysis_results,
                "sixr_readiness": state.validation_results.get("sixr_readiness", 0.0),
                "completed_at": state.completed_at.isoformat()
            }
            
            # Determine assessment readiness
            state.assessment_ready = validation_result["sixr_readiness_score"] >= 0.75
            
            # Update final state
            state.progress = 100.0
            state.next_phase = None
            
            # Complete flow in database
            await self.services.state_service.complete_collection_flow(
                flow_id=state.flow_id,
                final_results=assessment_package,
                execution_time_ms=int((state.completed_at - state.created_at).total_seconds() * 1000)
            )
            
            # Persist final state
            await self.state_manager.save_state(state.to_dict())
            
            # Log completion
            await self.services.audit_logging.log_flow_event(
                flow_id=state.flow_id,
                event_type="flow_completed",
                event_data={
                    "quality_score": state.collection_quality_score,
                    "confidence_score": state.confidence_score,
                    "assessment_ready": state.assessment_ready
                }
            )
            
            # Notify master flow if linked
            master_flow_id = config.get("master_flow_id")
            if master_flow_id:
                await self.unified_flow_management.notify_phase_completion(
                    phase="collection",
                    results=assessment_package
                )
            
            return {
                "phase": "finalization",
                "status": "completed",
                "flow_completed": True,
                "assessment_ready": state.assessment_ready,
                "assessment_package": assessment_package
            }
            
        except Exception as e:
            logger.error(f"❌ Finalization failed: {e}")
            state.add_error("finalization", str(e))
            await enhanced_error_handler.handle_error(e, self.flow_context)
            raise CollectionFlowError(f"Finalization failed: {e}")