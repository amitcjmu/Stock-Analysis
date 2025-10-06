"""Agent execution and helper methods for gap analysis.

Contains agent task execution, progress tracking, and result formatters.
Split from service.py for file length compliance (<400 lines per file).
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AgentHelperMixin:
    """Mixin providing agent execution and helper methods for GapAnalysisService."""

    async def _execute_agent_task(self, agent, task_description: str) -> Any:
        """Execute persistent agent WITHOUT creating new Crew/Task per call.

        Uses agent's internal execution method to avoid per-call Crew instantiation.
        Agent is already configured with temperature=0.2 for consistency (per ADR-024).

        Args:
            agent: TenantScoped AgentWrapper (persistent agent from pool)
            task_description: Task description string for gap enhancement

        Returns:
            Task output containing JSON response
        """
        from crewai import Task

        # Extract underlying CrewAI agent from AgentWrapper
        # AgentWrapper has _agent attribute containing the actual BaseAgent
        underlying_agent = agent._agent if hasattr(agent, "_agent") else agent

        # Create minimal Task wrapper (reuse agent config, no Crew creation)
        # Agent is already configured with max_iterations and temperature from pool
        task = Task(
            description=task_description,
            expected_output="JSON with enhanced gaps (confidence_score, ai_suggestions, suggested_resolution)",
            agent=underlying_agent,  # Pass underlying BaseAgent, not AgentWrapper
        )

        logger.debug("🤖 Executing agent task via persistent agent (no Crew creation)")

        # Execute task directly on agent (synchronous execution in thread pool)
        # Agent already has temperature=0.2 for consistency
        result = await asyncio.to_thread(agent.execute_task, task)

        logger.debug(f"📤 Agent task completed: {str(result)[:200]}...")

        return result

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when no assets found."""
        return {
            "gaps": {},
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 0, "assets_analyzed": 0, "gaps_persisted": 0},
        }

    def _error_result(self, error: str) -> Dict[str, Any]:
        """Return error result."""
        return {
            "status": "error",
            "error": error,
            "gaps": {},
            "questionnaire": {"sections": []},
            "summary": {"total_gaps": 0, "assets_analyzed": 0, "gaps_persisted": 0},
        }

    async def _update_progress(
        self,
        flow_id: str,
        processed: int,
        total: int,
        current_asset: str,
        redis_client,
    ):
        """Update progress in Redis for HTTP polling.

        Frontend polls /api/v1/collection/{flow_id}/enhancement-progress endpoint
        every 2-3 seconds during enhancement to get current progress.

        Args:
            flow_id: Collection flow ID
            processed: Number of assets processed so far
            total: Total number of assets to process
            current_asset: Name of current asset being processed
            redis_client: Redis client instance
        """
        progress_key = f"gap_enhancement_progress:{flow_id}"

        progress_data = {
            "processed": processed,
            "total": total,
            "current_asset": current_asset,
            "percentage": int((processed / total) * 100) if total > 0 else 0,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Store in Redis with 1-hour TTL
        try:
            await redis_client.set(
                progress_key,
                json.dumps(progress_data),
                ex=3600,  # 1 hour TTL
            )
            logger.debug(
                f"📊 Progress updated: {processed}/{total} ({progress_data['percentage']}%) - {current_asset}"
            )
        except Exception as e:
            logger.warning(f"Failed to update progress in Redis: {e}")
