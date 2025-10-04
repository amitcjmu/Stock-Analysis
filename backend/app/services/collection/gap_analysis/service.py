"""Main gap analysis service using single persistent agent."""

import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from .data_loader import load_assets, resolve_collection_flow_id
from .gap_persistence import persist_gaps
from .output_parser import parse_task_output
from .task_builder import build_task_description

logger = logging.getLogger(__name__)


class GapAnalysisService:
    """
    Lean gap analysis using single persistent agent.

    Loads REAL assets from database, compares against 22 critical attributes,
    identifies gaps, and generates questionnaires - all in one atomic operation.
    """

    def __init__(
        self,
        client_account_id: str,
        engagement_id: str,
        collection_flow_id: str,
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.collection_flow_id = collection_flow_id

    async def analyze_and_generate_questionnaire(
        self,
        selected_asset_ids: List[str],
        db: AsyncSession,
        automation_tier: str = "tier_2",
    ) -> Dict[str, Any]:
        """
        Single atomic operation: Load assets, detect gaps, generate questionnaire.

        Args:
            selected_asset_ids: UUIDs of assets selected for gap analysis
            db: AsyncSession
            automation_tier: Automation tier for agent configuration

        Returns:
            {
                "gaps": {
                    "critical": [...],
                    "high": [...],
                    "medium": [...],
                    "low": [...]
                },
                "questionnaire": {
                    "sections": [...]
                },
                "summary": {
                    "total_gaps": int,
                    "assets_analyzed": int
                }
            }
        """
        logger.info(
            f"🚀 Starting gap analysis - Flow: {self.collection_flow_id}, "
            f"Assets: {len(selected_asset_ids)}, Tier: {automation_tier}"
        )

        try:
            # Resolve actual collection flow ID from master flow if needed
            actual_collection_flow_id = await resolve_collection_flow_id(
                self.collection_flow_id, db
            )
            logger.info(
                f"📋 Resolved collection flow ID: {actual_collection_flow_id} "
                f"(input was: {self.collection_flow_id})"
            )

            # Load REAL assets from database
            logger.debug(f"📥 Loading assets: {selected_asset_ids}")
            assets = await load_assets(
                selected_asset_ids,
                self.client_account_id,
                self.engagement_id,
                db,
            )

            if not assets:
                logger.error(
                    f"❌ No assets found - IDs: {selected_asset_ids}, "
                    f"Client: {self.client_account_id}, Engagement: {self.engagement_id}"
                )
                return self._empty_result()

            logger.info(
                f"📦 Loaded {len(assets)} real assets: "
                f"{[f'{a.name} ({a.asset_type})' for a in assets[:5]]}"
            )

            # Get single persistent agent
            from app.services.persistent_agents.tenant_scoped_agent_pool import (
                TenantScopedAgentPool,
            )

            logger.debug("🔧 Creating persistent agent - Type: gap_analysis_specialist")
            agent = await TenantScopedAgentPool.get_or_create_agent(
                client_id=self.client_account_id,
                engagement_id=self.engagement_id,
                agent_type="gap_analysis_specialist",
            )
            logger.info(
                f"✅ Agent created: {agent.role if hasattr(agent, 'role') else 'gap_analysis_specialist'}"
            )

            # Create and execute task
            task_description = build_task_description(assets)
            logger.debug(f"📝 Task description length: {len(task_description)} chars")

            task_output = await self._execute_agent_task(agent, task_description)
            logger.debug(f"📤 Task output received: {str(task_output)[:200]}...")

            # Parse result
            result_dict = parse_task_output(task_output)
            total_gaps = sum(
                len(v) if isinstance(v, list) else 0
                for v in result_dict.get("gaps", {}).values()
            )
            questionnaire_sections = len(
                result_dict.get("questionnaire", {}).get("sections", [])
            )
            logger.info(
                f"📊 Parsed result - Gaps: {total_gaps}, "
                f"Questionnaire sections: {questionnaire_sections}"
            )

            # Persist gaps to database
            logger.debug("💾 Persisting gaps to database...")
            gaps_count = await persist_gaps(
                result_dict, assets, db, actual_collection_flow_id
            )
            result_dict["summary"]["gaps_persisted"] = gaps_count

            logger.info(
                f"✅ Gap analysis complete: {gaps_count} gaps persisted, "
                f"{len(assets)} assets analyzed, Flow: {self.collection_flow_id}"
            )

            return result_dict

        except Exception as e:
            logger.error(
                f"❌ Gap analysis failed - Flow: {self.collection_flow_id}, "
                f"Error: {e}, Type: {type(e).__name__}",
                exc_info=True,
            )
            return self._error_result(str(e))

    async def _execute_agent_task(self, agent, task_description: str) -> Any:
        """Execute agent task with proper unwrapping and future handling.

        Args:
            agent: AgentWrapper or raw CrewAI agent
            task_description: Task description string

        Returns:
            Task output
        """
        from crewai import Task

        # Unwrap AgentWrapper to get raw CrewAI Agent for Task
        raw_agent = agent._agent if hasattr(agent, "_agent") else agent

        task = Task(
            description=task_description,
            agent=raw_agent,
            expected_output="JSON with gaps and questionnaire structure",
        )

        logger.info("🤖 Executing single-agent gap analysis task")

        # execute_async returns Future, need to wrap for await
        future = task.execute_async()
        task_output = await asyncio.wrap_future(future)

        return task_output

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
