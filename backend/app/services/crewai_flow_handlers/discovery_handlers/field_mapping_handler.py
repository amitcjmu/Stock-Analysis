"""
Field Mapping Handler for Discovery Flow
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

class FieldMappingHandler:
    def __init__(self, crewai_service: "CrewAIFlowService"):
        self.agents = crewai_service.agents
        self.Task = Task
        self.Crew = Crew

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def handle(self, flow_state: DiscoveryFlowState, cmdb_data: Dict[str, Any]) -> DiscoveryFlowState:
        """
        Runs the field mapping crew to suggest mappings from source to target schema.
        """
        if 'field_mapper' not in self.agents:
            logger.warning("Field mapper agent not available. Skipping field mapping.")
            flow_state.field_mapping_complete = True
            return flow_state

        logger.info("Executing Field Mapping phase.")
        task = self.Task(
            description="Based on the source columns, suggest the best field mappings to the target asset schema.",
            agent=self.agents['field_mapper'],
            expected_output="A JSON object with suggested field mappings from source to target."
        )
        crew = self.Crew(agents=[self.agents['field_mapper']], tasks=[task], verbose=1)
        
        # Use timeout to prevent hanging
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(crew.kickoff, inputs={'cmdb_data': cmdb_data}),
                timeout=120  # 2 minute timeout for field mapping
            )
        except asyncio.TimeoutError:
            logger.error("Field mapping timed out after 2 minutes")
            flow_state.suggested_field_mappings = {"error": "Field mapping timed out", "timeout": True}
            flow_state.field_mapping_complete = True
            return flow_state
        
        try:
            flow_state.suggested_field_mappings = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            logger.error(f"Failed to parse field mapping result: {result}")
            flow_state.suggested_field_mappings = {"error": "Failed to parse mapping output", "raw": result}

        flow_state.field_mapping_complete = True
        logger.info("Field Mapping phase complete.")
        return flow_state 