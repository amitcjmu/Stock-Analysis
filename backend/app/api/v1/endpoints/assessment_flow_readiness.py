"""
Assessment Flow Readiness API Endpoints

Provides REST API endpoints for analyzing asset readiness in assessment flows.
Integrates GapAnalyzer via AssetReadinessService for comprehensive gap detection.

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
Day 11: AssessmentFlowChildService Integration and API Endpoints

API Endpoints:
1. GET /api/v1/assessment-flow/{flow_id}/asset-readiness/{asset_id}
   - Returns ComprehensiveGapReport for single asset
2. GET /api/v1/assessment-flow/{flow_id}/readiness-summary
   - Returns batch readiness analysis for all flow assets
3. GET /api/v1/assessment-flow/{flow_id}/ready-assets
   - Returns list of asset IDs filtered by readiness status
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.api_tags import APITags
from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.database import get_db
from app.services.assessment.asset_readiness_service import AssetReadinessService
from app.services.gap_detection.schemas import ComprehensiveGapReport

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assessment-flow",
)


@router.get(
    "/{flow_id}/asset-readiness/{asset_id}",
    response_model=ComprehensiveGapReport,
    summary="Get asset readiness analysis",
    description=(
        "Get comprehensive gap analysis for a single asset in an assessment flow.\n\n"
        "Returns detailed report with:\n"
        "- Column, enrichment, JSONB, application, standards gaps\n"
        "- Weighted completeness scores\n"
        "- Prioritized gaps (critical/high/medium)\n"
        "- Assessment readiness determination\n"
        "- Specific readiness blockers\n\n"
        "Performance: <50ms per asset (GapAnalyzer target)"
    ),
)
async def get_asset_readiness(
    flow_id: UUID,
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
) -> ComprehensiveGapReport:
    """
    Get comprehensive gap analysis for a single asset.

    Args:
        flow_id: Assessment flow UUID (for context validation)
        asset_id: Asset UUID to analyze
        db: Database session (injected)
        current_user: Authenticated user (injected)
        client_account_id: Tenant client account ID (injected)
        engagement_id: Engagement ID from header

    Returns:
        ComprehensiveGapReport with full gap analysis across all 5 inspectors

    Raises:
        HTTPException 404: If asset not found or not in tenant scope
        HTTPException 500: If analysis fails
    """
    try:

        logger.info(
            f"GET /assessment-flow/{flow_id}/asset-readiness/{asset_id}",
            extra={
                "flow_id": str(flow_id),
                "asset_id": str(asset_id),
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
                "user_id": str(getattr(current_user, "id", None)),
            },
        )

        service = AssetReadinessService()

        report = await service.analyze_asset_readiness(
            asset_id=asset_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            db=db,
        )

        logger.info(
            f"Asset readiness analysis complete: asset_id={asset_id}, "
            f"completeness={report.overall_completeness:.2f}, "
            f"ready={report.is_ready_for_assessment}",
            extra={
                "asset_id": str(asset_id),
                "overall_completeness": report.overall_completeness,
                "is_ready": report.is_ready_for_assessment,
                "critical_gaps_count": len(report.critical_gaps),
            },
        )

        return report

    except ValueError as e:
        # Asset not found or not in tenant scope
        logger.warning(
            f"Asset not found: {e}",
            extra={"asset_id": str(asset_id), "client_account_id": client_account_id},
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error during analysis
        logger.error(
            f"Failed to analyze asset {asset_id}: {e}",
            extra={"asset_id": str(asset_id), "flow_id": str(flow_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze asset: {str(e)}",
        )


@router.get(
    "/{flow_id}/readiness-summary",
    response_model=Dict[str, Any],
    summary="Get readiness summary for flow assets",
    description=(
        "Returns batch readiness analysis for all assets in an assessment flow.\n\n"
        "Query parameters:\n"
        "- `detailed=true|false`: Include detailed reports per asset (default: false)\n\n"
        "Returns:\n"
        "- Total asset count\n"
        "- Ready vs not-ready counts\n"
        "- Overall readiness rate (percentage)\n"
        "- Summary by asset type\n"
        "- Detailed per-asset reports (if detailed=true)\n\n"
        "Use detailed=false for lightweight status checks."
    ),
)
async def get_readiness_summary(
    flow_id: UUID,
    detailed: bool = Query(
        default=False,
        description="Include detailed reports per asset (default: false for performance)",
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
) -> Dict[str, Any]:
    """
    Get batch readiness analysis for all flow assets.

    Args:
        flow_id: Assessment flow UUID
        detailed: If True, include full reports per asset; if False, counts only
        db: Database session (injected)
        current_user: Authenticated user (injected)
        client_account_id: Tenant client account ID (injected)

    Returns:
        Dict with readiness summary:
        {
            "flow_id": str,
            "total_assets": int,
            "ready_count": int,
            "not_ready_count": int,
            "overall_readiness_rate": float (0-100),
            "asset_reports": List[Dict] (if detailed=True),
            "summary_by_type": Dict[str, Dict],
            "analyzed_at": str (ISO timestamp)
        }

    Raises:
        HTTPException 404: If flow not found or not in tenant scope
        HTTPException 500: If analysis fails
    """
    try:
        logger.info(
            f"GET /assessment-flow/{flow_id}/readiness-summary?detailed={detailed}",
            extra={
                "flow_id": str(flow_id),
                "detailed": detailed,
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )

        service = AssetReadinessService()

        summary = await service.analyze_flow_assets_readiness(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            db=db,
            detailed=detailed,
        )

        logger.info(
            f"Readiness summary complete: flow_id={flow_id}, "
            f"total={summary['total_assets']}, "
            f"ready={summary['ready_count']}, "
            f"rate={summary['overall_readiness_rate']:.2f}%",
            extra={
                "flow_id": str(flow_id),
                "total_assets": summary["total_assets"],
                "ready_count": summary["ready_count"],
                "readiness_rate": summary["overall_readiness_rate"],
            },
        )

        return summary

    except ValueError as e:
        # Flow not found or not in tenant scope
        logger.warning(
            f"Assessment flow not found: {e}",
            extra={"flow_id": str(flow_id), "client_account_id": client_account_id},
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error during analysis
        logger.error(
            f"Failed to get readiness summary for flow {flow_id}: {e}",
            extra={"flow_id": str(flow_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get readiness summary: {str(e)}",
        )


@router.get(
    "/{flow_id}/ready-assets",
    response_model=List[str],
    summary="Filter assets by readiness status",
    description=(
        "Returns list of asset IDs filtered by readiness status.\n\n"
        "Query parameters:\n"
        "- `ready_only=true|false`: Filter for ready or not-ready assets "
        "(default: true)\n\n"
        "Use cases:\n"
        "- Get ready assets to proceed with assessment\n"
        "- Identify not-ready assets that need data collection\n"
        "- Validate flow progress before finalization"
    ),
)
async def get_ready_assets(
    flow_id: UUID,
    ready_only: bool = Query(
        default=True,
        description="If True, return only ready assets; if False, return not ready",
    ),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
) -> List[str]:
    """
    Get list of asset IDs filtered by readiness status.

    Args:
        flow_id: Assessment flow UUID
        ready_only: If True, return only ready assets; if False, return not ready
        db: Database session (injected)
        current_user: Authenticated user (injected)
        client_account_id: Tenant client account ID (injected)
        engagement_id: Engagement ID from header

    Returns:
        List of asset UUIDs (as strings) matching readiness filter

    Raises:
        HTTPException 404: If flow not found or not in tenant scope
        HTTPException 500: If filtering fails
    """
    try:

        logger.info(
            f"GET /assessment-flow/{flow_id}/ready-assets?ready_only={ready_only}",
            extra={
                "flow_id": str(flow_id),
                "ready_only": ready_only,
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )

        service = AssetReadinessService()

        asset_ids = await service.filter_assets_by_readiness(
            flow_id=flow_id,
            ready_only=ready_only,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            db=db,
        )

        # Convert UUIDs to strings for JSON serialization
        asset_id_strings = [str(asset_id) for asset_id in asset_ids]

        logger.info(
            f"Asset filtering complete: flow_id={flow_id}, "
            f"ready_only={ready_only}, "
            f"count={len(asset_id_strings)}",
            extra={
                "flow_id": str(flow_id),
                "ready_only": ready_only,
                "filtered_count": len(asset_id_strings),
            },
        )

        return asset_id_strings

    except ValueError as e:
        # Flow not found or not in tenant scope
        logger.warning(
            f"Assessment flow not found: {e}",
            extra={"flow_id": str(flow_id), "client_account_id": client_account_id},
        )
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Unexpected error during filtering
        logger.error(
            f"Failed to filter assets for flow {flow_id}: {e}",
            extra={"flow_id": str(flow_id)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to filter assets: {str(e)}",
        )
