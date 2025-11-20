"""Tier processing methods for gap analysis.

Contains tier_1 programmatic scan and tier_2 AI analysis implementations.
Split from service.py for file length compliance (<400 lines per file).
"""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

from .comprehensive_task_builder import build_comprehensive_gap_analysis_task
from .gap_persistence import persist_gaps
from .output_parser import parse_task_output

logger = logging.getLogger(__name__)


class TierProcessorMixin:
    """Mixin providing tier processing methods for GapAnalysisService."""

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
        logger.debug("🔧 Creating persistent agent - Type: gap_analysis_specialist")
        agent = await TenantScopedAgentPool.get_or_create_agent(
            client_id=self.client_account_id,
            engagement_id=self.engagement_id,
            agent_type="gap_analysis_specialist",
        )
        logger.info(
            f"✅ Agent created: {agent.role if hasattr(agent, 'role') else 'gap_analysis_specialist'}"
        )

        # Create and execute task (Per PR #1043: comprehensive gap analysis only, no questionnaires)
        task_description = build_comprehensive_gap_analysis_task(assets)
        logger.debug(
            f"📝 Task description length: {len(task_description)} chars (comprehensive gap analysis - no questionnaires)"
        )

        task_output = await self._execute_agent_task(agent, task_description)
        logger.debug(f"📤 Task output received: {str(task_output)[:200]}...")

        # Parse result
        result_dict = parse_task_output(task_output)
        total_gaps = sum(
            len(v) if isinstance(v, list) else 0
            for v in result_dict.get("gaps", {}).values()
        )
        logger.info(
            f"📊 Parsed result - Gaps: {total_gaps} (confidence scores expected)"
        )

        # Persist gaps to database
        logger.debug("💾 Persisting gaps to database...")
        gaps_count = await persist_gaps(result_dict, assets, db, collection_flow_id)
        result_dict["summary"]["gaps_persisted"] = gaps_count

        # Per PR #1043: Questionnaire generation happens separately
        # This auto-trigger phase only analyzes gaps and assigns confidence scores
        logger.debug(
            "ℹ️ Questionnaire generation skipped - happens when user clicks 'Continue to Questionnaire'"
        )
        result_dict["summary"]["questionnaires_persisted"] = 0

        return result_dict
