"""
Modernization Agent - Utility Functions Module
Contains standalone utility functions for asset enrichment and batch processing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def analyze_modernization_potential_agentic(
    asset_data: Dict[str, Any],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    db: AsyncSession,
    flow_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    Main function to analyze modernization potential using agentic intelligence.

    This function creates a ModernizationAgent and executes comprehensive cloud readiness
    and modernization strategy analysis with TenantMemoryManager integration.

    Args:
        asset_data: Asset data to analyze
        crewai_service: CrewAI service instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        db: Database session for TenantMemoryManager
        flow_id: Optional flow ID

    Returns:
        Modernization assessment with scores and recommendations
    """
    from app.services.agentic_intelligence.modernization_agent import (
        ModernizationAgent,
    )

    agent = ModernizationAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    return await agent.analyze_modernization_potential(asset_data, db)


async def enrich_assets_with_modernization_intelligence(
    assets: List[Dict[str, Any]],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    db: AsyncSession,
    flow_id: Optional[uuid.UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Enrich multiple assets with comprehensive modernization intelligence.

    This function processes assets in batches and enriches them with:
    - Cloud readiness scores (0-100)
    - Modernization potential and recommended strategies
    - Architecture assessment and containerization readiness
    - Migration effort estimation and timeline planning
    - Immediate modernization steps and long-term roadmaps

    Args:
        assets: List of assets to analyze
        crewai_service: CrewAI service instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        db: Database session for TenantMemoryManager
        flow_id: Optional flow ID

    Returns:
        List of enriched assets with modernization assessments
    """
    from app.services.agentic_intelligence.modernization_agent import (
        ModernizationAgent,
    )

    enriched_assets = []

    # Initialize the modernization agent once for batch processing
    agent = ModernizationAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    for i, asset in enumerate(assets):
        try:
            logger.info(
                f"☁️ Analyzing modernization potential for asset {i+1}/{len(assets)}: {asset.get('name')}"
            )

            # Perform agentic modernization analysis with TenantMemoryManager
            analysis_result = await agent.analyze_modernization_potential(asset, db)

            # Merge analysis results with asset data
            enriched_asset = {**asset}
            enriched_asset.update(
                {
                    "cloud_readiness_score": analysis_result.get(
                        "cloud_readiness_score"
                    ),
                    "modernization_potential": analysis_result.get(
                        "modernization_potential"
                    ),
                    "recommended_migration_strategy": analysis_result.get(
                        "recommended_strategy"
                    ),
                    "migration_effort_estimate": analysis_result.get(
                        "migration_effort"
                    ),
                    "enrichment_status": "agent_enriched",
                    "last_enriched_at": datetime.utcnow(),
                    "last_enriched_by_agent": "Modernization Agent",
                }
            )

            enriched_assets.append(enriched_asset)

            logger.info(
                f"✅ Modernization analysis completed - Readiness: {analysis_result.get('cloud_readiness_score')}/100"
            )

        except Exception as e:
            logger.error(
                f"❌ Failed to analyze modernization for asset {asset.get('name')}: {e}"
            )

            # Add asset with basic modernization assessment
            enriched_asset = {**asset}
            enriched_asset.update(
                {
                    "cloud_readiness_score": 50,
                    "modernization_potential": "medium",
                    "recommended_migration_strategy": "lift-and-shift",
                    "enrichment_status": "basic",
                    "last_enriched_at": datetime.utcnow(),
                }
            )
            enriched_assets.append(enriched_asset)

    logger.info(
        f"✅ Completed modernization analysis for {len(enriched_assets)} assets"
    )
    return enriched_assets
