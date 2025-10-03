"""
Business Value Agent - Utility Functions Module
Contains standalone utility functions for asset enrichment and batch processing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def analyze_asset_business_value_agentic(
    asset_data: Dict[str, Any],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    db: AsyncSession,
    flow_id: Optional[uuid.UUID] = None,
) -> Dict[str, Any]:
    """
    Main function to analyze asset business value using agentic intelligence.

    This function creates a BusinessValueAgent and executes the full agentic analysis
    including pattern search, evidence gathering, and memory-based learning with
    TenantMemoryManager integration.

    Args:
        asset_data: Asset data to analyze
        crewai_service: CrewAI service instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        db: Database session for TenantMemoryManager
        flow_id: Optional flow ID

    Returns:
        Business value assessment with score and reasoning
    """
    from app.services.agentic_intelligence.business_value_agent import (
        BusinessValueAgent,
    )

    agent = BusinessValueAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    return await agent.analyze_asset_business_value(asset_data, db)


async def enrich_assets_with_business_value_intelligence(
    assets: List[Dict[str, Any]],
    crewai_service,
    client_account_id: uuid.UUID,
    engagement_id: uuid.UUID,
    db: AsyncSession,
    flow_id: Optional[uuid.UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Enrich multiple assets with business value intelligence.

    This function processes assets in batches and enriches them with:
    - Business value scores (1-10)
    - Confidence levels
    - Detailed reasoning
    - Pattern-based insights
    - Recommendations

    Args:
        assets: List of assets to analyze
        crewai_service: CrewAI service instance
        client_account_id: Client account ID
        engagement_id: Engagement ID
        db: Database session for TenantMemoryManager
        flow_id: Optional flow ID

    Returns:
        List of enriched assets with business value assessments
    """
    from app.services.agentic_intelligence.business_value_agent import (
        BusinessValueAgent,
    )

    enriched_assets = []

    # Initialize the business value agent once for batch processing
    agent = BusinessValueAgent(
        crewai_service=crewai_service,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        flow_id=flow_id,
    )

    for i, asset in enumerate(assets):
        try:
            logger.info(f"🧠 Analyzing asset {i+1}/{len(assets)}: {asset.get('name')}")

            # Perform agentic business value analysis with TenantMemoryManager
            analysis_result = await agent.analyze_asset_business_value(asset, db)

            # Merge analysis results with asset data
            enriched_asset = {**asset}
            enriched_asset.update(
                {
                    "business_value_score": analysis_result.get("business_value_score"),
                    "business_value_reasoning": analysis_result.get("reasoning"),
                    "business_value_confidence": analysis_result.get(
                        "confidence_level"
                    ),
                    "business_value_recommendations": analysis_result.get(
                        "recommendations"
                    ),
                    "enrichment_status": "agent_enriched",
                    "last_enriched_at": datetime.utcnow(),
                    "last_enriched_by_agent": "Business Value Agent",
                }
            )

            enriched_assets.append(enriched_asset)

            logger.info(
                f"✅ Asset enriched - Business Value: {analysis_result.get('business_value_score')}/10"
            )

        except Exception as e:
            logger.error(f"❌ Failed to analyze asset {asset.get('name')}: {e}")

            # Add asset with basic enrichment
            enriched_asset = {**asset}
            enriched_asset.update(
                {
                    "business_value_score": 5,  # Default medium value
                    "business_value_reasoning": "Analysis failed - using default value",
                    "business_value_confidence": "low",
                    "enrichment_status": "basic",
                    "last_enriched_at": datetime.utcnow(),
                }
            )
            enriched_assets.append(enriched_asset)

    logger.info(
        f"✅ Completed business value analysis for {len(enriched_assets)} assets"
    )
    return enriched_assets
