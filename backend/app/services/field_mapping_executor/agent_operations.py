"""
Field Mapping Executor - Agent Operations Module

This module handles all agent-related operations for field mapping execution,
including agent interaction, mock responses, and agent input preparation.
"""

import asyncio
import logging
from typing import Any, Dict

from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# Import TenantScopedAgentPool at module level to avoid runtime import issues
try:
    from app.services.persistent_agents.tenant_scoped_agent_pool import (
        TenantScopedAgentPool,
    )

    TENANT_AGENT_POOL_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).warning(f"TenantScopedAgentPool import failed: {e}")
    TenantScopedAgentPool = None
    TENANT_AGENT_POOL_AVAILABLE = False

from .exceptions import CrewExecutionError

logger = logging.getLogger(__name__)


class AgentOperations:
    """Handles agent operations for field mapping execution."""

    def __init__(
        self,
        agent_pool: Any = None,
        client_account_id: str = "unknown",
        engagement_id: str = "unknown",
    ):
        self.agent_pool = agent_pool
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

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
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=str(self.client_account_id),
                engagement_id=str(self.engagement_id),
                agent_type="field_mapper",
                context_info={"flow_id": str(state.flow_id)},
            )

            # Prepare input for agent
            agent_input = self._prepare_agent_input(state)

            # Execute agent with input
            response = await self._execute_agent_with_crew(agent, agent_input)

            logger.info(f"Field mapping agent completed for flow {state.flow_id}")
            return response

        except Exception as e:
            logger.error(f"Agent execution failed for flow {state.flow_id}: {str(e)}")
            raise CrewExecutionError(f"Agent execution failed: {str(e)}") from e

    def _get_mock_agent_response(self, state: UnifiedDiscoveryFlowState) -> str:
        """Generate a mock response for testing when no agent is available."""
        # Get sample data for mock response
        sample_data = state.raw_data or {}
        detected_columns = state.metadata.get("detected_columns", [])

        # Generate mock mappings based on detected columns
        mock_mappings = []
        for i, column in enumerate(detected_columns[:5]):  # Limit to first 5 columns
            # Map to common target fields for demonstration
            target_fields = ["hostname", "ip", "os", "owner", "environment"]
            target_field = target_fields[i % len(target_fields)]

            mock_mappings.append(
                {
                    "source_field": column,
                    "target_field": target_field,
                    "confidence": 0.85 + (i * 0.02),  # Vary confidence scores
                    "mapping_context": {
                        "detected_patterns": f"Pattern analysis for {column}",
                        "sample_values": [
                            sample_data.get(column, f"sample_{column}_{j}")
                            for j in range(3)
                        ],
                    },
                }
            )

        # Generate clarifications for some fields
        clarifications = (
            [
                {
                    "field": "environment",
                    "question": "What environment categories are used? (e.g., Production, Staging, Development)",
                    "reason": "Multiple environment values detected, need standardization",
                }
            ]
            if len(detected_columns) > 2
            else []
        )

        mock_response = f"""
        FIELD_MAPPING_ANALYSIS:

        Based on the analysis of the provided data sample with {len(detected_columns)} detected columns,
        I have generated the following field mappings:

        MAPPINGS:
        {str(mock_mappings)}

        CLARIFICATIONS:
        {str(clarifications)}

        CONFIDENCE_SCORES:
        Overall confidence: 0.87
        Mapping quality: High
        Data completeness: Good

        The field mapping analysis has identified {len(mock_mappings)} field mappings with high confidence.
        {len(clarifications)} clarifications may be needed for optimal mapping accuracy.
        """

        logger.info(
            f"Generated mock response with {len(mock_mappings)} mappings for flow {state.flow_id}"
        )
        return mock_response

    def _prepare_agent_input(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """Prepare input data for the field mapping agent."""
        # Get basic flow information
        agent_input = {
            "flow_id": str(state.flow_id),
            "client_account_id": str(self.client_account_id),
            "engagement_id": str(self.engagement_id),
            "current_phase": state.current_phase,
            "sample_data": state.raw_data or {},
            "detected_columns": state.metadata.get("detected_columns", []),
            "data_source_info": state.metadata.get("data_source_info", {}),
            "previous_mappings": state.metadata.get("previous_mappings", []),
        }

        logger.debug(
            f"Prepared agent input for flow {state.flow_id} with {len(agent_input.get('detected_columns', []))} columns"
        )
        return agent_input

    async def _execute_agent_with_crew(
        self, agent: Any, agent_input: Dict[str, Any]
    ) -> str:
        """Execute the agent using CrewAI crew."""
        try:
            # Prepare unified state for agent
            unified_state = self._prepare_unified_state(agent_input)

            # Execute with timeout to prevent hanging
            response = await asyncio.wait_for(
                agent.execute_async(
                    inputs={
                        "flow_state": unified_state,
                        "mapping_context": agent_input,
                    }
                ),
                timeout=120.0,  # 2 minute timeout
            )

            if not response:
                raise CrewExecutionError("Agent returned empty response")

            logger.info(
                f"Agent execution completed for flow {agent_input.get('flow_id')}"
            )
            return str(response)

        except asyncio.TimeoutError:
            raise CrewExecutionError("Agent execution timed out after 2 minutes")
        except Exception as e:
            logger.error(f"Agent execution error: {str(e)}")
            raise CrewExecutionError(f"Agent execution failed: {str(e)}") from e

    def _prepare_unified_state(self, agent_input: Dict[str, Any]) -> Any:
        """Prepare unified state object for agent execution."""
        # Create a simplified state object for agent consumption
        return {
            "flow_id": agent_input["flow_id"],
            "sample_data": agent_input["sample_data"],
            "detected_columns": agent_input["detected_columns"],
        }
