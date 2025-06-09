"""
Orchestrator for the Discovery Workflow
"""
import logging
from typing import Dict, Any, TYPE_CHECKING

from app.schemas.flow_schemas import DiscoveryFlowState
from .data_source_analysis import DataSourceAnalysisHandler
from .data_validation_handler import DataValidationHandler
from .field_mapping_handler import FieldMappingHandler
from .asset_classification_handler import AssetClassificationHandler
from .dependency_analysis_handler import DependencyAnalysisHandler
from .database_integration_handler import DatabaseIntegrationHandler

if TYPE_CHECKING:
    from app.services.crewai_flow_service import CrewAIFlowService

logger = logging.getLogger(__name__)

class DiscoveryWorkflowManager:
    def __init__(self, crewai_service: "CrewAIFlowService"):
        self.crewai_service = crewai_service
        # Initialize all the handlers for the discovery workflow
        self.data_source_analysis_handler = DataSourceAnalysisHandler()
        self.data_validation_handler = DataValidationHandler(crewai_service)
        self.field_mapping_handler = FieldMappingHandler(crewai_service)
        self.asset_classification_handler = AssetClassificationHandler(crewai_service)
        self.dependency_analysis_handler = DependencyAnalysisHandler(crewai_service)
        self.database_integration_handler = DatabaseIntegrationHandler(crewai_service)

    async def run_workflow(self, flow_state: DiscoveryFlowState, cmdb_data: Dict[str, Any], client_account_id: str, engagement_id: str, user_id: str) -> DiscoveryFlowState:
        """
        Executes the full discovery workflow by calling each handler in sequence.
        """
        logger.info(f"Starting discovery workflow for session: {flow_state.session_id}")

        flow_state = await self.data_source_analysis_handler.handle(flow_state, cmdb_data)
        flow_state = await self.data_validation_handler.handle(flow_state, cmdb_data)
        flow_state = await self.field_mapping_handler.handle(flow_state, cmdb_data)
        flow_state = await self.asset_classification_handler.handle(flow_state)
        flow_state = await self.dependency_analysis_handler.handle(flow_state)
        flow_state = await self.database_integration_handler.handle(flow_state, client_account_id, engagement_id, user_id)

        logger.info(f"Discovery workflow for session {flow_state.session_id} complete.")
        flow_state.current_phase = "completion"
        flow_state.completion_complete = True
        
        return flow_state 