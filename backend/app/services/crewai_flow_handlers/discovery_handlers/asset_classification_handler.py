"""
Asset Classification Handler for Discovery Flow
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

class AssetClassificationHandler:
    def __init__(self, crewai_service: "CrewAIFlowService"):
        self.agents = crewai_service.agents
        self.Task = Task
        self.Crew = Crew

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def handle(self, flow_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Runs the asset classification crew to classify assets and suggest 6R strategies.
        """
        if 'asset_classifier' not in self.agents:
            logger.warning("Asset classifier agent not available. Skipping classification.")
            flow_state.asset_classification_complete = True
            return flow_state
            
        logger.info("Executing Asset Classification phase.")
        task = self.Task(
            description="Classify each asset based on its properties and suggest a 6R migration strategy.",
            agent=self.agents['asset_classifier'],
            expected_output="A list of JSON objects, each representing an asset with its classification and recommended 6R strategy."
        )
        crew = self.Crew(agents=[self.agents['asset_classifier']], tasks=[task], verbose=1)
        
        # Use timeout to prevent hanging
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(crew.kickoff, inputs={'validated_data': flow_state.validated_structure}),
                timeout=180  # 3 minute timeout for asset classification
            )
        except asyncio.TimeoutError:
            logger.error("Asset classification timed out after 3 minutes")
            flow_state.asset_classification_results = {"error": "Asset classification timed out", "timeout": True}
            flow_state.asset_classification_complete = True
            return flow_state
        
        try:
            flow_state.asset_classifications = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Failed to parse asset classification result: {result}")
            flow_state.asset_classifications = [{"error": "Failed to parse classification output", "raw": result}]

        flow_state.asset_classification_complete = True
        logger.info("Asset Classification phase complete.")
        return flow_state 