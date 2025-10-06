"""Main gap analysis service using single persistent agent."""

import logging
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from .agent_helpers import AgentHelperMixin
from .data_loader import load_assets, resolve_collection_flow_id
from .enhancement_processor import EnhancementProcessorMixin
from .tier_processors import TierProcessorMixin

logger = logging.getLogger(__name__)


class GapAnalysisService(
    TierProcessorMixin, EnhancementProcessorMixin, AgentHelperMixin
):
    """
    Lean gap analysis using single persistent agent.

    Loads REAL assets from database, compares against 22 critical attributes,
    identifies gaps, and generates questionnaires - all in one atomic operation.

    Inherits from:
        - TierProcessorMixin: Provides tier_1/tier_2 processing methods
        - EnhancementProcessorMixin: Provides AI enhancement processing
        - AgentHelperMixin: Provides agent execution and helper methods
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

        except Exception as e:
            logger.error(
                f"❌ Gap analysis failed - Flow: {self.collection_flow_id}, "
                f"Error: {e}, Type: {type(e).__name__}",
                exc_info=True,
            )
            return self._error_result(str(e))
