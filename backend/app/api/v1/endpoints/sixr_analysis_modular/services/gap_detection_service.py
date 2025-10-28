"""
Gap Detection Service for 6R Assessment Server-Side Gate.

Per Two-Tier Inline Gap-Filling Design (October 2025), this service detects
Tier 1 (blocking) gaps BEFORE starting AI agents to prevent wasted executions.

Tier 1 Fields (Assessment-Blocking):
- criticality: Required for strategy scoring (Rehost vs Refactor)
- business_criticality: Impacts risk assessment
- application_type: Determines COTS vs Custom strategies
- migration_priority: Needed for wave planning

Reference:
- Design Doc: /docs/design/TWO_TIER_INLINE_GAP_FILLING_DESIGN.md
- ADR-029: snake_case JSON, safe serialization
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset.models import Asset

logger = logging.getLogger(__name__)


# Tier 1 Field Configuration (Assessment-Blocking)
TIER1_FIELDS = {
    "criticality": {
        "display_name": "Business Criticality",
        "reason": "Required for 6R strategy scoring",
        "asset_field": "criticality",
        "priority": 1,
    },
    "business_criticality": {
        "display_name": "Business Impact Level",
        "reason": "Impacts risk assessment and strategy selection",
        "asset_field": "business_criticality",
        "priority": 1,
    },
    "application_type": {
        "display_name": "Application Type",
        "reason": "Determines COTS vs Custom migration strategies",
        "asset_field": "asset_type",  # Maps to asset_type field
        "priority": 1,
    },
    "migration_priority": {
        "display_name": "Migration Priority",
        "reason": "Needed for wave planning and resource allocation",
        "asset_field": "migration_priority",
        "priority": 2,
    },
}


class AssessmentGapDetector:
    """
    Detects Tier 1 (blocking) gaps for 6R assessment.

    This service executes the server-side gate BEFORE AI agents start,
    preventing wasted LLM calls on incomplete data.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize gap detector with database session.

        Args:
            db: Async database session for tenant-scoped queries
        """
        self.db = db

    async def detect_tier1_gaps(
        self,
        asset_ids: List[UUID],
        client_account_id: UUID,
        engagement_id: UUID,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect Tier 1 (blocking) gaps for given assets.

        Per design: Gate executes BEFORE AI agents start. Returns structured
        gap payload for frontend modal or empty dict if no gaps.

        Args:
            asset_ids: List of asset UUIDs to check
            client_account_id: Tenant account ID (security scoping)
            engagement_id: Engagement ID (security scoping)

        Returns:
            Dict mapping asset_id (str) to list of gap details:
            {
                "asset-uuid-1": [
                    {
                        "field_name": "criticality",
                        "display_name": "Business Criticality",
                        "reason": "Required for 6R strategy scoring",
                        "tier": 1,
                        "priority": 1
                    }
                ],
                "asset-uuid-2": [...]
            }

            Returns empty dict {} if no Tier 1 gaps found.

        Example:
            >>> detector = AssessmentGapDetector(db)
            >>> gaps = await detector.detect_tier1_gaps(
            ...     asset_ids=[uuid1, uuid2],
            ...     client_account_id=tenant_uuid,
            ...     engagement_id=engagement_uuid
            ... )
            >>> if gaps:
            ...     return {"status": "requires_input", ...}
        """
        tier1_gaps_by_asset: Dict[str, List[Dict[str, Any]]] = {}

        for asset_id in asset_ids:
            # Fetch asset with tenant scoping (SECURITY)
            stmt = select(Asset).where(
                Asset.id == asset_id,
                Asset.client_account_id == client_account_id,
                Asset.engagement_id == engagement_id,
            )
            result = await self.db.execute(stmt)
            asset = result.scalar_one_or_none()

            if not asset:
                logger.warning(
                    f"Asset {asset_id} not found or not in tenant scope "
                    f"(client={client_account_id}, engagement={engagement_id})"
                )
                continue

            # Check each Tier 1 field
            asset_gaps = []
            for field_name, field_config in TIER1_FIELDS.items():
                asset_field = field_config["asset_field"]
                value = getattr(asset, asset_field, None)

                # Check if value is missing or empty
                is_missing = False
                if value is None:
                    is_missing = True
                elif isinstance(value, str) and not value.strip():
                    is_missing = True

                if is_missing:
                    asset_gaps.append(
                        {
                            "field_name": field_name,
                            "display_name": field_config["display_name"],
                            "reason": field_config["reason"],
                            "tier": 1,  # All are Tier 1 (blocking)
                            "priority": field_config["priority"],
                        }
                    )
                    logger.debug(
                        f"Tier 1 gap detected: Asset {asset.name} missing "
                        f"'{field_name}' ({field_config['display_name']})"
                    )

            # Only add to result if gaps exist
            if asset_gaps:
                tier1_gaps_by_asset[str(asset_id)] = asset_gaps
                logger.info(
                    f"Asset {asset.name} ({asset_id}) has {len(asset_gaps)} Tier 1 gaps"
                )

        if tier1_gaps_by_asset:
            total_gaps = sum(len(gaps) for gaps in tier1_gaps_by_asset.values())
            logger.info(
                f"Server-side gate BLOCKED: {len(tier1_gaps_by_asset)} assets "
                f"with {total_gaps} total Tier 1 gaps"
            )
        else:
            logger.info(
                f"Server-side gate PROCEED: All {len(asset_ids)} assets "
                f"have complete Tier 1 data"
            )

        return tier1_gaps_by_asset

    async def check_has_tier1_gaps(
        self,
        asset_ids: List[UUID],
        client_account_id: UUID,
        engagement_id: UUID,
    ) -> bool:
        """
        Quick check if ANY asset has Tier 1 gaps (boolean result).

        Use this for lightweight gate checks that only need yes/no answer.

        Args:
            asset_ids: List of asset UUIDs to check
            client_account_id: Tenant account ID
            engagement_id: Engagement ID

        Returns:
            True if ANY asset has Tier 1 gaps, False otherwise
        """
        gaps = await self.detect_tier1_gaps(
            asset_ids=asset_ids,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )
        return len(gaps) > 0


# Utility function for handler code
async def detect_tier1_gaps_for_analysis(
    asset_ids: List[UUID],
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convenience function for use in analysis handlers.

    Args:
        asset_ids: List of asset UUIDs
        client_account_id: Tenant account ID
        engagement_id: Engagement ID
        db: Database session

    Returns:
        Dict of tier1_gaps_by_asset (same as AssessmentGapDetector.detect_tier1_gaps)
    """
    detector = AssessmentGapDetector(db)
    return await detector.detect_tier1_gaps(
        asset_ids=asset_ids,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
    )


def build_blocked_response(
    analysis_id,
    tier1_gaps_by_asset,
    applications,
    parameters,
    logger_instance=None,
):
    """
    Build SixRAnalysisResponse when analysis is blocked by Tier 1 gaps.

    Encapsulates the response construction logic to reduce handler complexity.

    Args:
        analysis_id: Analysis UUID
        tier1_gaps_by_asset: Dict mapping asset_id to list of gaps
        applications: List of application details
        parameters: SixRParameters instance
        logger_instance: Optional logger for logging blocked status

    Returns:
        SixRAnalysisResponse with status='requires_input' (blocked by Tier 1 gaps)
    """
    # Import here to avoid circular dependency
    from app.schemas.sixr_analysis import SixRAnalysisResponse, AnalysisStatus
    from datetime import datetime

    if logger_instance:
        logger_instance.info(
            f"Analysis {analysis_id} BLOCKED by server-side gate: "
            f"{len(tier1_gaps_by_asset)} assets with Tier 1 gaps"
        )

    return SixRAnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.REQUIRES_INPUT,  # Triggers frontend modal for inline answers
        current_iteration=1,
        applications=applications,
        parameters=parameters,
        qualifying_questions=[],
        recommendation=None,
        progress_percentage=0.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        # Server-side gate fields (per Two-Tier Design)
        tier1_gaps_by_asset=tier1_gaps_by_asset,
        retry_after_inline=True,  # Analysis will resume after answers submitted
    )


def build_proceed_response(
    analysis_id, applications, parameters, created_at, updated_at
):
    """
    Build SixRAnalysisResponse when no Tier 1 gaps and analysis can proceed.

    Args:
        analysis_id: Analysis UUID
        applications: List of application details
        parameters: SixRParameters instance
        created_at: Analysis creation timestamp
        updated_at: Analysis last update timestamp

    Returns:
        SixRAnalysisResponse with status='pending' (AI agents starting)
    """
    # Import here to avoid circular dependency
    from app.schemas.sixr_analysis import SixRAnalysisResponse, AnalysisStatus

    return SixRAnalysisResponse(
        analysis_id=analysis_id,
        status=AnalysisStatus.PENDING,  # AI agents starting
        current_iteration=1,
        applications=applications,
        parameters=parameters,
        qualifying_questions=[],
        recommendation=None,
        progress_percentage=5.0,  # AI agents started
        estimated_completion=None,
        created_at=created_at,
        updated_at=updated_at,
    )


def convert_params_to_schema(params_model):
    """
    Convert SixRParametersModel (DB model) to SixRParameters (Pydantic schema).

    Reduces duplication in get_analysis and list_sixr_analyses handlers.

    Args:
        params_model: SixRParametersModel instance from database

    Returns:
        SixRParameters Pydantic schema instance
    """
    from app.schemas.sixr_analysis import SixRParameters

    return SixRParameters(
        business_value=params_model.business_value,
        technical_complexity=params_model.technical_complexity,
        migration_urgency=params_model.migration_urgency,
        compliance_requirements=params_model.compliance_requirements,
        cost_sensitivity=params_model.cost_sensitivity,
        risk_tolerance=params_model.risk_tolerance,
        innovation_priority=params_model.innovation_priority,
        application_type=params_model.application_type,
        parameter_source=params_model.parameter_source,
        confidence_level=params_model.confidence_level,
        last_updated=params_model.updated_at or params_model.created_at,
        updated_by=params_model.updated_by,
    )


def convert_recommendation_to_schema(rec_model):
    """
    Convert SixRRecommendationModel (DB model) to SixRRecommendation (Pydantic schema).

    Reduces duplication in get_analysis and list_sixr_analyses handlers.

    Args:
        rec_model: SixRRecommendationModel instance from database

    Returns:
        SixRRecommendation Pydantic schema instance or None
    """
    if not rec_model:
        return None

    from app.schemas.sixr_analysis import SixRRecommendation

    return SixRRecommendation(
        recommended_strategy=rec_model.recommended_strategy,
        confidence_score=rec_model.confidence_score,
        strategy_scores=rec_model.strategy_scores or [],
        key_factors=rec_model.key_factors or [],
        assumptions=rec_model.assumptions or [],
        next_steps=rec_model.next_steps or [],
        estimated_effort=rec_model.estimated_effort,
        estimated_timeline=rec_model.estimated_timeline,
        estimated_cost_impact=rec_model.estimated_cost_impact,
    )
