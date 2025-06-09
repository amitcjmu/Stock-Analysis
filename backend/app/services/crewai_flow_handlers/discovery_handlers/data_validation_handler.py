"""
Data Validation Handler for Discovery Flow
"""
import logging
import json
import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed
from typing import Dict, Any, TYPE_CHECKING
from crewai import Task, Crew

from app.schemas.flow_schemas import DiscoveryFlowState
# from app.schemas.agent_schemas import Task, Crew

if TYPE_CHECKING:
    from app.services.crewai_flow_service import CrewAIFlowService

logger = logging.getLogger(__name__)

class DataValidationHandler:
    def __init__(self, crewai_service: "CrewAIFlowService"):
        self.agents = crewai_service.agents
        self.Task = Task
        self.Crew = Crew

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def handle(self, flow_state: DiscoveryFlowState, cmdb_data: Dict[str, Any]) -> DiscoveryFlowState:
        """
        Runs the data validation crew to assess data quality.
        """
        if 'data_validator' not in self.agents:
            logger.warning("Data validator agent not available. Skipping validation.")
            flow_state.data_validation_complete = True
            return flow_state

        logger.info("Executing Data Validation phase.")
        task = self.Task(
            description="Analyze the provided CMDB data structure, validate its quality, and identify any structural issues.",
            agent=self.agents['data_validator'],
            expected_output="A JSON object summarizing data quality, including column analysis and validation status."
        )
        crew = self.Crew(agents=[self.agents['data_validator']], tasks=[task], verbose=1)
        
        result = await asyncio.to_thread(crew.kickoff, inputs={'cmdb_data': cmdb_data})
        
        try:
            flow_state.validated_structure = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Failed to parse data validation result: {result}")
            flow_state.validated_structure = {"error": "Failed to parse validation output", "raw": result}

        flow_state.data_validation_complete = True
        logger.info("Data Validation phase complete.")
        return flow_state 