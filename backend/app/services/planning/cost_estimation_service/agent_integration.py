"""
CrewAI agent integration for Cost Estimation Service.

This module handles the interaction with CrewAI agents for cost estimation,
including task creation, execution, and observability tracking.

Per ADR-031: Full CallbackHandler integration for observability
Per ADR-024: CrewAI memory DISABLED
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional
from uuid import UUID

from crewai import Task

from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration,
)

logger = logging.getLogger(__name__)


class AgentIntegrationMixin:
    """Mixin for CrewAI agent integration methods."""

    async def generate_cost_estimate(
        self,
        planning_flow_id: UUID,
        phase_input: Optional[Dict[str, Any]] = None,
        custom_rate_cards: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive migration cost estimate using CrewAI agent.

        Args:
            planning_flow_id: UUID of the planning flow
            phase_input: Optional input data for cost estimation
            custom_rate_cards: Optional custom hourly rates by role

        Returns:
            Dict containing cost estimation data with breakdowns and
            confidence intervals
        """
        try:
            logger.info(
                f"Starting cost estimation for planning flow: {planning_flow_id}"
            )

            # Update phase status to in_progress
            await self.planning_repo.update_phase_status(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
                current_phase="cost_estimation",
                phase_status="in_progress",
            )

            # Get planning flow data
            planning_flow = await self.planning_repo.get_planning_flow_by_id(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
            )

            if not planning_flow:
                raise ValueError(f"Planning flow not found: {planning_flow_id}")

            # Extract required data
            wave_plan_data = planning_flow.wave_plan_data or {}
            resource_allocation_data = planning_flow.resource_allocation_data or {}
            timeline_data = planning_flow.timeline_data or {}

            # Validate prerequisites
            if not wave_plan_data.get("waves"):
                raise ValueError(
                    "Wave plan data required for cost estimation. "
                    "Please complete wave planning phase first."
                )

            if not resource_allocation_data.get("allocations"):
                logger.warning(
                    "No resource allocations found. "
                    "Cost estimate will be based on wave complexity."
                )

            # Setup observability (ADR-031)
            callback_handler = CallbackHandlerIntegration.create_callback_handler(
                flow_id=str(planning_flow.master_flow_id),
                context={
                    "client_account_id": str(self.client_account_uuid),
                    "engagement_id": str(self.engagement_uuid),
                    "flow_type": "planning",
                    "phase": "cost_estimation",
                    "planning_flow_id": str(planning_flow_id),
                },
            )
            callback_handler.setup_callbacks()

            # Get agent from pool (ADR-015: persistent agents)
            agent = await self.agent_pool.get_agent("cost_estimation_specialist")

            # Build context for agent
            rate_cards = custom_rate_cards or self.DEFAULT_RATE_CARDS
            context_data = self._build_cost_context(
                wave_plan_data,
                resource_allocation_data,
                timeline_data,
                rate_cards,
                phase_input,
            )

            # Create task
            wave_count = len(wave_plan_data.get("waves", []))
            task = Task(
                description=(
                    f"Calculate comprehensive migration costs for {wave_count} "
                    "waves. Include labor costs (by role and wave), "
                    "infrastructure costs, risk contingency (15-25% based on "
                    "complexity), and provide confidence intervals "
                    "(low/medium/high scenarios)."
                ),
                expected_output=(
                    "JSON object with cost structure: "
                    '{"labor_costs": {...}, "infrastructure_costs": {...}, '
                    '"risk_contingency": {...}, "total_cost": <float>, '
                    '"confidence_intervals": '
                    '{"low": <float>, "medium": <float>, "high": <float>}}'
                ),
                agent=(agent._agent if hasattr(agent, "_agent") else agent),
            )

            # Generate unique task ID
            task_id = str(uuid.uuid4())

            # Register task start (ADR-031)
            callback_handler._step_callback(
                {
                    "type": "starting",
                    "status": "starting",
                    "agent": "cost_estimation_specialist",
                    "task": "cost_estimation",
                    "task_id": task_id,
                    "content": f"Estimating costs for {wave_count} migration waves",
                }
            )

            # Execute task (wrapped for async)
            try:
                future = task.execute_async(context=str(context_data))
                result = await asyncio.wrap_future(future)

                # Parse result using safe JSON parser (ADR-029)
                from .parsers import parse_cost_result

                cost_data = parse_cost_result(result, self.DEFAULT_RATE_CARDS)

                # Persist to JSONB column
                await self.planning_repo.save_cost_estimation_data(
                    planning_flow_id=planning_flow_id,
                    client_account_id=self.client_account_uuid,
                    engagement_id=self.engagement_uuid,
                    cost_estimation_data=cost_data,
                )

                # Mark task completion (ADR-031)
                callback_handler._task_completion_callback(
                    {
                        "agent": "cost_estimation_specialist",
                        "task_name": "cost_estimation",
                        "status": "completed",
                        "task_id": task_id,
                        "output": cost_data,
                    }
                )

                # Update phase status to completed
                await self.planning_repo.update_phase_status(
                    planning_flow_id=planning_flow_id,
                    client_account_id=self.client_account_uuid,
                    engagement_id=self.engagement_uuid,
                    current_phase="cost_estimation",
                    phase_status="completed",
                )

                await self.db.commit()

                logger.info(
                    f"✅ Cost estimation completed for flow: {planning_flow_id}"
                )

                return {
                    "status": "success",
                    "cost_data": cost_data,
                    "message": "Cost estimation completed successfully",
                }

            except Exception as task_error:
                # Mark task failure (ADR-031)
                callback_handler._task_completion_callback(
                    {
                        "agent": "cost_estimation_specialist",
                        "task_name": "cost_estimation",
                        "status": "failed",
                        "task_id": task_id,
                        "error": str(task_error),
                    }
                )
                raise

        except Exception as e:
            logger.error(
                f"Cost estimation failed for flow {planning_flow_id}: {str(e)}",
                exc_info=True,
            )

            # Update phase status to failed
            try:
                await self.planning_repo.update_phase_status(
                    planning_flow_id=planning_flow_id,
                    client_account_id=self.client_account_uuid,
                    engagement_id=self.engagement_uuid,
                    current_phase="cost_estimation",
                    phase_status="failed",
                )
                await self.db.commit()
            except Exception as update_error:
                logger.error(
                    f"Failed to update phase status after error: {update_error}"
                )

            return {
                "status": "failed",
                "error": str(e),
                "message": "Cost estimation failed",
            }
