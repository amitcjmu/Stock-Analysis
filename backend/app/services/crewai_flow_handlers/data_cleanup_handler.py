"""
Data Cleanup Handler for CrewAI Flow
Orchestrates data quality and cleanup operations.
"""
import logging
from typing import Dict, List, Any, Optional

from app.services.data_cleanup_handlers.agent_analysis_handler import AgentAnalysisHandler
from app.services.data_cleanup_handlers.agent_processing_handler import AgentProcessingHandler
from app.services.data_cleanup_handlers.quality_assessment_handler import QualityAssessmentHandler
from app.services.data_cleanup_handlers.cleanup_operations_handler import CleanupOperationsHandler

logger = logging.getLogger(__name__)

class DataCleanupHandler:
    def __init__(self, config):
        self.config = config
        self.quality_thresholds = {
            "excellent": 90.0,
            "good": 75.0, 
            "acceptable": 60.0,
            "needs_work": 0.0
        }
        self.agent_analysis_handler = AgentAnalysisHandler(self.quality_thresholds)
        self.agent_processing_handler = AgentProcessingHandler()
        self.quality_assessment_handler = QualityAssessmentHandler(self.quality_thresholds)
        self.cleanup_operations_handler = CleanupOperationsHandler()

    async def analyze_data_quality(self, flow_state: "DiscoveryFlowState") -> Dict[str, Any]:
        """Analyzes data quality for the data in the flow state."""
        try:
            return await self.agent_analysis_handler.analyze_data_quality(
                flow_state.sample_data, 
                "data-cleansing", 
                flow_state.flow_context.get('client_account_id'), 
                flow_state.flow_context.get('engagement_id')
            )
        except Exception as e:
            logger.error(f"Error in analyze_data_quality: {e}")
            return {"analysis_type": "error", "error": str(e)}

    def assess_cleanup_readiness(self, flow_state: "DiscoveryFlowState") -> Dict[str, Any]:
        """Assess readiness for data cleanup phase."""
        return self.quality_assessment_handler.assess_cleanup_readiness(flow_state.sample_data) 