"""
CrewAI agent integration for resource allocation.

Handles agent task creation, execution, and context building.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)
from app.utils.json_sanitization import sanitize_for_json

from .allocation_logic import AllocationLogic
from .base import CREWAI_AVAILABLE, BaseResourceAllocationService, Task

logger = logging.getLogger(__name__)


class AgentIntegration(BaseResourceAllocationService):
    """
    Handles CrewAI agent integration for resource allocation.

    This class manages agent task creation, execution, and result processing.
    """

    async def generate_ai_allocations(
        self,
        planning_flow_id: uuid.UUID,
        wave_plan_data: Dict[str, Any],
        resource_pools: Optional[Dict[str, Any]] = None,
        historical_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate AI-driven resource allocations for migration waves.

        This method:
        1. Creates CallbackHandler for observability (ADR-031)
        2. Gets resource_allocation_specialist agent from pool
        3. Builds context with wave plan and historical patterns
        4. Executes agent task with monitoring
        5. Parses and sanitizes LLM output (ADR-029)
        6. Persists to JSONB column in planning_flows table

        Args:
            planning_flow_id: UUID of the planning flow
            wave_plan_data: Generated wave plan with application groupings
            resource_pools: Available resource pools and constraints
            historical_data: Historical migration data for pattern matching

        Returns:
            Dict containing resource allocations with confidence scores

        Raises:
            ValueError: If planning flow not found or wave plan invalid
            RuntimeError: If agent execution fails
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI not available - cannot generate allocations")

        logger.info(
            f"Starting AI resource allocation for planning flow: {planning_flow_id}"
        )

        # Get planning flow for tenant context
        planning_flow = await self.planning_repo.get_planning_flow_by_id(
            planning_flow_id=planning_flow_id,
            client_account_id=self.client_account_uuid,
            engagement_id=self.engagement_uuid,
        )

        if not planning_flow:
            raise ValueError(f"Planning flow not found: {planning_flow_id}")

        # Extract master_flow_id for callback handler
        master_flow_id = str(planning_flow.master_flow_id)

        # Step 1: Create callback handler for observability (ADR-031)
        callback_handler = CallbackHandlerIntegration.create_callback_handler(
            flow_id=master_flow_id,
            context=self.context,
            metadata={
                "client_account_id": str(self.client_account_uuid),
                "engagement_id": str(self.engagement_uuid),
                "flow_type": "planning",
                "phase": "resource_allocation",
                "wave_count": len(wave_plan_data.get("waves", [])),
            },
        )
        callback_handler.setup_callbacks()

        # Step 2: Get persistent agent from pool (ADR-015)
        agent = await TenantScopedAgentPool.get_agent(
            context=self.context, agent_type="resource_allocation_specialist"
        )

        # Step 3: Build context for agent
        context_data = self._build_allocation_context(
            wave_plan_data, resource_pools, historical_data
        )

        # Step 4: Create task
        task = self._create_resource_allocation_task(
            agent, wave_plan_data, resource_pools, historical_data
        )

        # Step 5: Generate unique task ID
        task_id = str(uuid.uuid4())

        # Step 6: Register task start BEFORE execution
        callback_handler._step_callback(
            {
                "type": "starting",
                "status": "starting",
                "agent": "resource_allocation_specialist",
                "task": "resource_allocation",
                "task_id": task_id,
                "content": f"Generating resource allocations for {len(wave_plan_data.get('waves', []))} waves",
            }
        )

        # Step 7: Execute task with monitoring
        try:
            import asyncio

            future = task.execute_async(context=json.dumps(context_data))
            result = await asyncio.wrap_future(future)

            # Step 8: Parse and sanitize LLM output (ADR-029)
            allocations = AllocationLogic._parse_allocation_result(self, result)
            allocations_sanitized = sanitize_for_json(allocations)

            # Step 9: Persist to JSONB column
            await AllocationLogic._persist_allocations(
                self, planning_flow_id, allocations_sanitized
            )

            # Step 10: Mark task completion
            callback_handler._task_completion_callback(
                {
                    "agent": "resource_allocation_specialist",
                    "task_name": "resource_allocation",
                    "status": "completed",
                    "task_id": task_id,
                    "output": allocations_sanitized,
                }
            )

            logger.info(
                f"✅ Resource allocation completed for {len(allocations_sanitized.get('allocations', []))} waves"
            )
            return allocations_sanitized

        except Exception as e:
            # Mark task failure
            callback_handler._task_completion_callback(
                {
                    "agent": "resource_allocation_specialist",
                    "task_name": "resource_allocation",
                    "status": "failed",
                    "task_id": task_id,
                    "error": str(e),
                }
            )
            logger.error(f"❌ Resource allocation failed: {e}")
            raise

    def _build_allocation_context(
        self,
        wave_plan_data: Dict[str, Any],
        resource_pools: Optional[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build context data for resource allocation agent."""
        return {
            "wave_plan": wave_plan_data,
            "resource_pools": resource_pools or {},
            "historical_data": historical_data or {},
            "objectives": [
                "Calculate resource requirements per role for each wave",
                "Estimate effort hours based on application complexity",
                "Optimize resource leveling across parallel waves",
                "Generate confidence scores (0-100) for each allocation",
                "Provide rationale for resource decisions",
            ],
        }

    def _create_resource_allocation_task(
        self,
        agent: Any,
        wave_plan_data: Dict[str, Any],
        resource_pools: Optional[Dict[str, Any]],
        historical_data: Optional[Dict[str, Any]],
    ) -> Task:
        """
        Create CrewAI task for resource allocation generation.

        Args:
            agent: resource_allocation_specialist agent
            wave_plan_data: Wave plan with application groupings
            resource_pools: Available resource pools
            historical_data: Historical migration patterns

        Returns:
            CrewAI Task configured for resource allocation
        """
        wave_count = len(wave_plan_data.get("waves", []))

        description = f"""
Generate optimal resource allocations for {wave_count} migration waves.

For each wave, recommend:
1. Role-based resource assignments (architects, developers, testers, etc.)
2. Effort estimates per role (hours)
3. Confidence score (0-100) for each allocation
4. Rationale explaining the resource decisions

Consider:
- Application complexity and technology stack
- Wave dependencies and parallel execution opportunities
- Resource availability and constraints
- Historical patterns from similar migrations

Output Format (JSON):
{{
    "allocations": [
        {{
            "wave_id": "wave-1",
            "resources": [
                {{
                    "role": "cloud_architect",
                    "count": 2,
                    "effort_hours": 120,
                    "confidence_score": 85,
                    "rationale": "Complex architecture requires dedicated architects"
                }}
            ],
            "total_cost": 50000.00
        }}
    ],
    "metadata": {{
        "total_estimated_cost": 150000.00,
        "generated_at": "2025-11-26T10:00:00Z"
    }}
}}
"""

        expected_output = "JSON with resource allocations, confidence scores, and rationale for each wave"

        # Handle agent wrapper pattern
        agent_instance = agent._agent if hasattr(agent, "_agent") else agent

        return Task(
            description=description,
            expected_output=expected_output,
            agent=agent_instance,
        )
