"""
Dependency Analysis Handler for Discovery Flow
"""
import logging
from typing import Dict, Any, TYPE_CHECKING
from crewai import Task, Crew

from app.schemas.flow_schemas import DiscoveryFlowState

if TYPE_CHECKING:
    from app.services.crewai_flow_service import CrewAIFlowService

logger = logging.getLogger(__name__)

class DependencyAnalysisHandler:
    def __init__(self, crewai_service: "CrewAIFlowService"):
        self.crewai_service = crewai_service
        self.agents = crewai_service.agents
        self.Task = Task
        self.Crew = Crew
        logger.info("DependencyAnalysisHandler initialized.")

    async def handle(self, flow_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Runs the dependency analysis crew to identify relationships between assets.
        """
        logger.info(f"Starting dependency analysis for session: {flow_state.session_id}")
        flow_state.current_phase = "dependency_analysis"
        
        # Assume cmdb_data is in flow_state.processed_data
        cmdb_data = flow_state.processed_data.get("cmdb_data", {})
        if not cmdb_data:
            logger.warning("No CMDB data found in flow state for dependency analysis.")
            flow_state.log_entry("Skipping dependency analysis: No CMDB data available.")
            return flow_state

        try:
            task = self.Task(
                description=f"Analyze the following CMDB data to identify and map all dependencies between assets. Focus on network connections, software dependencies, and business process relationships. The data is: {cmdb_data}",
                agent=self.agents['cmdb_analyst'],
                expected_output="A JSON object detailing the dependencies between assets, including source, target, and dependency type."
            )

            crew = self.Crew(
                agents=[self.agents['cmdb_analyst']],
                tasks=[task],
                verbose=2
            )

            dependency_results = await self.crewai_service.run_crew(crew)
            
            flow_state.processed_data['dependency_analysis'] = dependency_results
            flow_state.log_entry(f"Dependency analysis completed successfully. Results: {dependency_results}")
            flow_state.dependency_analysis_complete = True
            logger.info(f"Dependency analysis for session {flow_state.session_id} successful.")

        except Exception as e:
            logger.error(f"Error during dependency analysis for session {flow_state.session_id}: {e}", exc_info=True)
            flow_state.log_entry(f"Error during dependency analysis: {e}")
            flow_state.has_errors = True

        return flow_state 