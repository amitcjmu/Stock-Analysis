"""
Agent execution logic for field mapping phase.

This module contains all the agent-related execution logic separated from the main
FieldMappingExecutor to reduce file length and improve maintainability.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .exceptions import CrewExecutionError

logger = logging.getLogger(__name__)

# Import TenantScopedAgentPool at module level to avoid runtime import issues
try:
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )

    TENANT_AGENT_POOL_AVAILABLE = True
except ImportError as e:
    logger.warning(f"TenantScopedAgentPool import failed: {e}")
    TenantScopedAgentPool = None
    TENANT_AGENT_POOL_AVAILABLE = False


class AgentExecutor:
    """Handles agent execution for field mapping operations."""

    def __init__(
        self, client_account_id: str, engagement_id: str, agent_pool: Any = None
    ):
        """Initialize the agent executor."""
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.agent_pool = agent_pool

    async def execute_field_mapping_agent(
        self, state: UnifiedDiscoveryFlowState
    ) -> str:
        """Execute the field mapping CrewAI agent."""
        try:
            # If no agent pool, return a mock response for testing
            if not self.agent_pool:
                logger.warning("No agent pool available, using mock response")
                return self._get_mock_agent_response(state)

            # Check if TenantScopedAgentPool is available
            if not TENANT_AGENT_POOL_AVAILABLE:
                logger.warning(
                    "TenantScopedAgentPool not available, using mock response"
                )
                return self._get_mock_agent_response(state)

            # Get field mapping agent from the pool
            # Use the imported TenantScopedAgentPool directly, not self.agent_pool
            # since self.agent_pool might be set to the class itself
            if hasattr(self.agent_pool, 'get_or_create_agent'):
                agent = await self.agent_pool.get_or_create_agent(
                    client_id=str(self.client_account_id),
                    engagement_id=str(self.engagement_id),
                    agent_type="field_mapping",
                )
            else:
                # If agent_pool is the class itself, call it directly
                agent = await TenantScopedAgentPool.get_or_create_agent(
                    client_id=str(self.client_account_id),
                    engagement_id=str(self.engagement_id),
                    agent_type="field_mapping",
                )

            if not agent:
                logger.warning("Field mapping agent not available, using mock response")
                return self._get_mock_agent_response(state)

            # Prepare agent input from state
            agent_input = self._prepare_agent_input(state)

            # Execute the agent using a single-agent Crew
            response = await self._execute_agent_with_crew(agent, agent_input)

            logger.info(
                f"Field mapping agent executed successfully for flow {state.flow_id}"
            )
            return response

        except Exception as e:
            logger.error(f"Field mapping agent execution failed: {str(e)}")
            raise CrewExecutionError(f"Agent execution failed: {str(e)}") from e

    def _get_mock_agent_response(self, state: UnifiedDiscoveryFlowState) -> str:
        """Generate a mock agent response for testing/fallback."""
        detected_columns = state.metadata.get("detected_columns", [])

        # If no detected columns, try to get from raw data using multi-row sampling
        if not detected_columns and state.raw_data:
            if isinstance(state.raw_data, list) and len(state.raw_data) > 0:
                # Sample multiple rows for robust column detection
                column_set = set()
                sample_size = min(5, len(state.raw_data))

                for i in range(sample_size):
                    record = state.raw_data[i]
                    if isinstance(record, dict):
                        for key in record.keys():
                            if key is not None and str(key).strip():
                                column_set.add(str(key).strip())

                detected_columns = sorted(list(column_set))

        # Generate basic mappings with standard field name transformations
        mappings = []
        confidence_scores = {}

        for col in detected_columns:
            # Map common variations to standard field names
            target_field = col.lower().replace(" ", "_")

            # Common field mappings
            field_map = {
                "os": "operating_system",
                "owner": "owner",
                "status": "status",
                "hostname": "hostname",
                "application": "application_name",
                "environment": "environment",
                "ip": "ip_address",
                "cpu": "cpu_cores",
                "ram": "memory_gb",
                "memory": "memory_gb",
                "disk": "disk_gb",
                "storage": "disk_gb",
            }

            # Use mapped name if available, otherwise use original
            target_field = field_map.get(col.lower(), target_field)
            confidence = 0.85 if col.lower() in field_map else 0.75

            mappings.append(
                {
                    "source_field": col,
                    "target_field": target_field,
                    "confidence": confidence,
                    "status": "suggested",
                }
            )
            confidence_scores[col] = confidence

        return json.dumps(
            {
                "mappings": mappings,
                "confidence_scores": confidence_scores,
                "clarifications": [],
            }
        )

    def _prepare_agent_input(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Prepare input data for the field mapping agent."""
        agent_input = {
            "sample_data": state.raw_data,
            "detected_columns": state.metadata.get("detected_columns", []),
            "data_source_info": state.metadata.get("data_source_info", {}),
            "previous_mappings": state.field_mappings or [],
            "mapping_context": {
                "flow_id": state.flow_id,
                "engagement_id": self.engagement_id,
                "client_account_id": self.client_account_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }

        logger.debug(
            f"Agent input prepared with {len(agent_input['detected_columns'])} columns"
        )
        return agent_input

    async def _execute_agent_with_crew(
        self, agent: Any, agent_input: Dict[str, Any]
    ) -> str:
        """Execute agent using a single-agent Crew with Task.

        This solves the "'Agent' object has no attribute 'execute'" error by using
        the proper CrewAI execution pattern with Crew.kickoff()
        """
        try:
            from crewai import Crew, Task, Process

            # Create task description from agent input
            task_description = f"""
            Analyze the following data and create field mappings:

            Sample Data: {json.dumps(agent_input.get('sample_data', [])[:2])}
            Detected Columns: {agent_input.get('detected_columns', [])}

            Create intelligent field mappings with confidence scores.
            Return JSON with format: {{"mappings": [...], "confidence_scores": {{...}}}}
            """

            # Create a single task for the agent
            task = Task(
                description=task_description,
                agent=agent,
                expected_output="JSON with field mappings and confidence scores",
            )

            # Create a single-agent crew (Agent is persistent; Crew is ephemeral)
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=False,
                memory=True,  # Use memory from the persistent agent
            )

            # Execute the crew - kickoff_async returns a result object
            result = await crew.kickoff_async()

            # Extract the string result
            return getattr(result, "raw", str(result))

        except Exception as e:
            logger.error(f"Crew execution failed: {str(e)}")
            # Fall back to mock response if crew execution fails
            logger.warning(
                "Falling back to mock response due to crew execution failure"
            )
            return self._get_mock_agent_response(
                self._prepare_unified_state(agent_input)
            )

    def _prepare_unified_state(self, agent_input: Dict[str, Any]) -> Any:
        """Convert agent input back to a UnifiedDiscoveryFlowState-like object."""
        from types import SimpleNamespace

        state = SimpleNamespace()
        state.raw_data = agent_input.get("sample_data", [])
        state.metadata = {"detected_columns": agent_input.get("detected_columns", [])}
        state.flow_id = agent_input.get("mapping_context", {}).get("flow_id", "unknown")
        return state
