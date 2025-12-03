"""
Asset Readiness Helper Functions.

Extracted from asset_readiness_service.py for modularization.
Contains:
- _build_ready_report: Build a ready ComprehensiveGapReport for assets marked ready in DB
- filter_assets_by_readiness: Filter assets by readiness status
"""

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.assessment_flow import AssessmentFlow
from app.services.gap_detection.schemas import (
    ApplicationGapReport,
    ColumnGapReport,
    ComprehensiveGapReport,
    EnrichmentGapReport,
    JSONBGapReport,
    StandardsGapReport,
)

logger = logging.getLogger(__name__)


def build_ready_report(asset: Asset) -> ComprehensiveGapReport:
    """
    Build a ready ComprehensiveGapReport for an asset already marked ready in DB.

    This is used when the asset's assessment_readiness field is 'ready',
    typically set after questionnaire completion. We don't need to re-run
    GapAnalyzer for these assets.

    Args:
        asset: Asset model instance

    Returns:
        ComprehensiveGapReport with all gaps empty and completeness=1.0
    """
    # Create proper gap report objects with "no gaps" state (completeness=1.0)
    column_gaps = ColumnGapReport(
        missing_attributes=[],
        empty_attributes=[],
        null_attributes=[],
        completeness_score=1.0,
    )
    enrichment_gaps = EnrichmentGapReport(
        missing_tables=[],
        incomplete_tables={},
        completeness_score=1.0,
    )
    jsonb_gaps = JSONBGapReport(
        missing_keys={},
        empty_values={},
        completeness_score=1.0,
    )
    application_gaps = ApplicationGapReport(
        missing_metadata=[],
        incomplete_tech_stack=[],
        missing_business_context=[],
        missing_critical_attributes={},
        completeness_score=1.0,
    )
    standards_gaps = StandardsGapReport(
        violated_standards=[],
        missing_mandatory_data=[],
        override_required=False,
        completeness_score=1.0,
    )

    # Get readiness score, explicitly check for None to handle 0.0 correctly
    score = getattr(asset, "assessment_readiness_score", None)
    overall_completeness = float(score if score is not None else 0.85)

    return ComprehensiveGapReport(
        asset_id=str(asset.id),
        asset_name=getattr(asset, "asset_name", None)
        or getattr(asset, "name", "Unknown"),
        asset_type=getattr(asset, "asset_type", "unknown"),
        overall_completeness=overall_completeness,
        is_ready_for_assessment=True,
        readiness_blockers=[],
        critical_gaps=[],
        high_priority_gaps=[],
        medium_priority_gaps=[],
        column_gaps=column_gaps,
        enrichment_gaps=enrichment_gaps,
        jsonb_gaps=jsonb_gaps,
        application_gaps=application_gaps,
        standards_gaps=standards_gaps,
        weighted_scores={
            "columns": 1.0,
            "enrichments": 1.0,
            "jsonb": 1.0,
            "application": 1.0,
            "standards": 1.0,
        },
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )


async def filter_assets_by_readiness(
    flow_id: UUID,
    ready_only: bool,
    client_account_id: str,
    engagement_id: str,
    db: AsyncSession,
    analyze_asset_func,
) -> List[UUID]:
    """
    Get list of asset IDs filtered by readiness status.

    Args:
        flow_id: AssessmentFlow UUID
        ready_only: If True, return only ready assets; if False, return not ready
        client_account_id: Tenant client account UUID
        engagement_id: Engagement UUID
        db: AsyncSession for database queries
        analyze_asset_func: Function to analyze asset readiness (injected dependency)

    Returns:
        List of asset UUIDs matching readiness filter

    Raises:
        ValueError: If flow not found or not in tenant scope
    """
    # Query assessment flow with tenant scoping
    stmt = select(AssessmentFlow).where(
        AssessmentFlow.id == flow_id,
        AssessmentFlow.client_account_id == UUID(client_account_id),
        AssessmentFlow.engagement_id == UUID(engagement_id),
    )
    result = await db.execute(stmt)
    flow = result.scalar_one_or_none()

    if not flow:
        raise ValueError(
            f"Assessment flow {flow_id} not found or not in tenant scope "
            f"(client_account_id={client_account_id}, "
            f"engagement_id={engagement_id})"
        )

    # Get selected asset IDs from flow
    # Note: selected_application_ids is deprecated and actually stores asset UUIDs
    # Use selected_asset_ids if available, fallback for backward compatibility
    selected_asset_ids = flow.selected_asset_ids or flow.selected_application_ids or []

    if not selected_asset_ids:
        return []

    # Query all selected assets directly by their IDs
    # Convert asset IDs to UUIDs, filtering out invalid ones
    asset_uuids = []
    for asset_id in selected_asset_ids:
        try:
            if isinstance(asset_id, str):
                if asset_id.strip():  # Skip empty strings
                    asset_uuids.append(UUID(asset_id))
            elif asset_id is not None:
                asset_uuids.append(
                    asset_id if isinstance(asset_id, UUID) else UUID(str(asset_id))
                )
        except (ValueError, AttributeError) as e:
            logger.warning(
                f"Invalid asset ID in selected_asset_ids: {asset_id} (error: {e})",
                extra={"flow_id": str(flow_id), "asset_id": str(asset_id)},
            )
            continue

    if not asset_uuids:
        logger.warning(
            f"No valid asset IDs found in selected_asset_ids for flow {flow_id}",
            extra={
                "flow_id": str(flow_id),
                "selected_asset_ids": selected_asset_ids,
            },
        )
        return []

    stmt = select(Asset).where(
        Asset.id.in_(asset_uuids),
        Asset.client_account_id == UUID(client_account_id),
        Asset.engagement_id == UUID(engagement_id),
    )
    result = await db.execute(stmt)
    assets = result.scalars().all()

    # Filter by readiness status
    filtered_asset_ids = []

    for asset in assets:
        try:
            report = await analyze_asset_func(
                asset_id=asset.id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                db=db,
            )

            # Apply readiness filter
            if ready_only and report.is_ready_for_assessment:
                filtered_asset_ids.append(asset.id)
            elif not ready_only and not report.is_ready_for_assessment:
                filtered_asset_ids.append(asset.id)

        except Exception as e:
            logger.error(
                f"Failed to analyze asset {asset.id} for filtering: {e}",
                extra={"asset_id": str(asset.id), "flow_id": str(flow_id)},
                exc_info=True,
            )

    logger.info(
        f"Filtered {len(filtered_asset_ids)} assets by readiness "
        f"(ready_only={ready_only}) for flow {flow_id}",
        extra={
            "flow_id": str(flow_id),
            "total_assets": len(assets),
            "filtered_count": len(filtered_asset_ids),
            "ready_only": ready_only,
        },
    )

    return filtered_asset_ids
