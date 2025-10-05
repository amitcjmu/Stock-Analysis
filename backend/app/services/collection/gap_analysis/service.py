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

            # Choose analysis method based on automation tier
            if automation_tier == "tier_1":
                logger.info("🔧 Using tier_1 programmatic gap scanner (fast, no AI)")
                result_dict = await self._run_tier_1_programmatic_scan(
                    selected_asset_ids, actual_collection_flow_id, db
                )
            else:
                logger.info("🤖 Using tier_2 AI agent analysis (slower, intelligent)")
                result_dict = await self._run_tier_2_ai_analysis(
                    assets, actual_collection_flow_id, db
                )

            logger.info(
                f"✅ Gap analysis complete: {result_dict['summary'].get('gaps_persisted', 0)} gaps persisted, "
                f"{len(assets)} assets analyzed, Flow: {self.collection_flow_id}"
            )

            return result_dict

            # LEGACY CODE BELOW - kept for reference, now split into tier_1/tier_2 methods
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

    async def _run_tier_1_programmatic_scan(
        self, selected_asset_ids: List[str], collection_flow_id: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """Run tier_1 programmatic gap scanner (fast, no AI)."""
        from app.services.collection.programmatic_gap_scanner import (
            ProgrammaticGapScanner,
        )

        scanner = ProgrammaticGapScanner()
        result = await scanner.scan_assets_for_gaps(
            selected_asset_ids=selected_asset_ids,
            collection_flow_id=collection_flow_id,
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            db=db,
        )

        # Programmatic scanner returns different format, need to adapt
        # Scanner persists gaps internally and returns gaps list
        gaps_list = result.get("gaps", [])

        # Group gaps by priority for compatibility with existing format
        gaps_by_priority = {"critical": [], "high": [], "medium": [], "low": []}
        for gap in gaps_list:
            priority = gap.get("priority", 3)
            if priority == 1:
                gaps_by_priority["critical"].append(gap)
            elif priority == 2:
                gaps_by_priority["high"].append(gap)
            elif priority == 3:
                gaps_by_priority["medium"].append(gap)
            else:
                gaps_by_priority["low"].append(gap)

        return {
            "gaps": gaps_by_priority,
            "questionnaire": {
                "sections": []
            },  # Programmatic scanner doesn't generate questionnaires
            "summary": result.get("summary", {}),
        }

    async def _run_tier_2_ai_analysis(
        self, assets: List, collection_flow_id: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """Run tier_2 AI agent analysis (slower, intelligent)."""
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
        gaps_count = await persist_gaps(result_dict, assets, db, collection_flow_id)
        result_dict["summary"]["gaps_persisted"] = gaps_count

        return result_dict

    async def _run_tier_2_ai_analysis_no_persist(
        self, assets: List, collection_flow_id: str, gaps: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run tier_2 AI agent analysis WITHOUT persisting (for enhancement only).

        This method is used by the analyze-gaps endpoint which enhances existing gaps
        with AI suggestions and confidence scores. It does NOT persist to avoid
        duplicate key violations on the unique constraint (collection_flow_id, field_name, gap_type, asset_id).

        Args:
            assets: List of Asset objects loaded from database
            collection_flow_id: Collection flow UUID
            gaps: Optional list of programmatic gaps to enhance (if None, AI does detection)

        Returns:
            Dict with AI-enhanced gaps (no persistence)
        """
        from app.services.persistent_agents.tenant_scoped_agent_pool import (
            TenantScopedAgentPool,
        )
        from .task_builder import build_enhancement_task_description

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
        if gaps:
            # Enhancement mode: AI enhances existing programmatic gaps
            task_description = build_enhancement_task_description(gaps, assets)
            logger.info(f"🔄 Enhancement mode: Enhancing {len(gaps)} programmatic gaps")
        else:
            # Detection mode: AI does its own gap detection (legacy)
            task_description = build_task_description(assets)
            logger.info("🔍 Detection mode: AI performing gap detection")

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

        # DO NOT PERSIST - this method is for enhancement only
        logger.debug("⏩ Skipping persistence (enhancement mode)")
        result_dict["summary"]["gaps_persisted"] = 0

        return result_dict

    async def _execute_agent_task(self, agent, task_description: str) -> Any:
        """Execute agent task with proper unwrapping and future handling.

        NOTE: For enhancement tasks, bypassing CrewAI agent to avoid max_iterations cutoff.
        Using direct LLM call for guaranteed complete JSON output.

        Args:
            agent: AgentWrapper or raw CrewAI agent
            task_description: Task description string

        Returns:
            Task output (str containing JSON)
        """
        # BYPASS AGENT: Use direct LLM call to avoid max_iterations cutoff
        # CrewAI agents hit iteration limits before completing 60 gaps
        logger.info(
            "🔧 Using direct LLM call (bypassing agent) for guaranteed completion"
        )

        import litellm

        response = await asyncio.to_thread(
            litellm.completion,
            model="deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a gap analysis specialist. "
                        "Return ONLY valid JSON with no markdown formatting, "
                        "no explanations, just pure JSON."
                    ),
                },
                {"role": "user", "content": task_description},
            ],
            max_tokens=8000,  # Enough for 60 gaps
            temperature=0.1,
        )

        # Extract content from response
        content = response.choices[0].message.content
        logger.info(f"📤 Direct LLM response received: {len(content)} chars")

        # Return mock task output with raw content
        class MockTaskOutput:
            def __init__(self, raw_content):
                self.raw = raw_content

        return MockTaskOutput(content)

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
