import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.asset.models import Asset
from app.models.assessment_flow import AssessmentFlow

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Response Models (snake_case per CLAUDE.md)
# =============================================================================


class ApplicationResponse(BaseModel):
    """Response model for application data (uses snake_case)"""

    id: str = Field(..., description="Asset UUID as string")
    application_name: Optional[str] = Field(None, description="Application name")
    asset_name: Optional[str] = Field(None, description="Asset display name")
    six_r_strategy: Optional[str] = Field(None, description="6R migration strategy")
    tech_stack: Optional[str] = Field(None, description="Technology stack")
    complexity_score: Optional[float] = Field(
        None, description="Assessment readiness score (0-100)"
    )
    asset_type: Optional[str] = Field(None, description="Asset type")

    class Config:
        from_attributes = True


class ApplicationsListResponse(BaseModel):
    """Paginated response for applications list"""

    applications: List[ApplicationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/applications", response_model=ApplicationsListResponse)
async def get_applications(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by application/asset name"),
    assessed_only: bool = Query(
        False, description="Filter to only applications with 6R strategies assigned"
    ),
):
    """
    Fetch applications from Asset table with database-level pagination and search.

    Returns assets that have application_name populated, suitable for
    Planning Flow initialization wizard.

    When assessed_only=True, returns applications with 6R strategies from either:
    - Asset.six_r_strategy column (if user accepted recommendation), OR
    - assessment_flows.phase_results['recommendation_generation']['applications']
      (from Assessment Flow analysis - even if not explicitly "accepted")

    Performance: Uses database-level COUNT and OFFSET/LIMIT to avoid loading
    all records into memory. Only fetches the requested page.

    Multi-tenant scoped by client_account_id and engagement_id per CLAUDE.md.
    """
    # Step 1: Get 6R decisions from assessment_flows.phase_results
    # Maps asset_id -> six_r_strategy using application_asset_groups mapping
    assessment_sixr_lookup = await _get_assessment_sixr_decisions(
        db, context.client_account_id, context.engagement_id
    )
    assessed_asset_ids = list(assessment_sixr_lookup.keys())

    # Step 2: Build base query with all filters applied at database level
    base_query = _build_applications_query(
        context.client_account_id,
        context.engagement_id,
        assessed_asset_ids,
        search,
        assessed_only,
    )

    # Step 3: Get total count at database level (efficient COUNT query)
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Step 4: Apply database-level pagination with OFFSET/LIMIT
    offset = (page - 1) * page_size
    paginated_query = base_query.offset(offset).limit(page_size)

    # Step 5: Execute paginated query - only fetches the requested page
    result = await db.execute(paginated_query)
    assets = result.scalars().all()

    # Step 6: Enrich only the paginated results with 6R strategies
    applications = _enrich_assets_with_sixr(assets, assessment_sixr_lookup)

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    logger.debug(
        f"Applications query: page={page}, total={total}, "
        f"returned={len(applications)}, assessed_only={assessed_only}"
    )

    return ApplicationsListResponse(
        applications=applications,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def _build_applications_query(
    client_account_id: str,
    engagement_id: str,
    assessed_asset_ids: List[str],
    search: Optional[str],
    assessed_only: bool,
):
    """
    Build the base query with all filters applied at database level.

    This enables efficient COUNT and paginated SELECT operations.
    """
    # Base tenant-scoped query
    query = select(Asset).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )

    if assessed_only:
        # Filter to only assets with 6R strategy (from Asset OR from assessment flow)
        query = query.where(
            or_(
                # Asset has six_r_strategy set directly
                and_(
                    Asset.six_r_strategy.isnot(None),
                    Asset.six_r_strategy != "",
                ),
                # Asset is in assessed_asset_ids (has 6R from assessment flow)
                (
                    Asset.id.cast(String).in_(assessed_asset_ids)
                    if assessed_asset_ids
                    else False
                ),
            )
        )
    else:
        # Include assets with application_name OR with assessment 6R strategies
        query = query.where(
            or_(
                and_(
                    Asset.application_name.isnot(None),
                    Asset.application_name != "",
                ),
                (
                    Asset.id.cast(String).in_(assessed_asset_ids)
                    if assessed_asset_ids
                    else False
                ),
            ),
        )

    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Asset.application_name.ilike(search_term),
                Asset.asset_name.ilike(search_term),
            )
        )

    # Order by application name (with asset_name fallback) for consistent results
    query = query.order_by(func.coalesce(Asset.application_name, Asset.asset_name))

    return query


def _enrich_assets_with_sixr(
    assets: List[Asset],
    assessment_sixr_lookup: Dict[str, str],
) -> List[ApplicationResponse]:
    """
    Enrich assets with 6R strategies from assessment flows.

    Priority: Asset.six_r_strategy (accepted) > assessment flow phase_results
    """
    enriched_applications = []
    for asset in assets:
        asset_id = str(asset.id)
        # Use asset's own six_r_strategy if set, otherwise check assessment flow results
        six_r_strategy = (
            asset.six_r_strategy
            if asset.six_r_strategy
            else assessment_sixr_lookup.get(asset_id)
        )

        # Use application_name if set, otherwise fallback to asset_name
        display_name = asset.application_name or asset.asset_name

        enriched_applications.append(
            ApplicationResponse(
                id=asset_id,
                application_name=display_name,
                asset_name=asset.asset_name,
                six_r_strategy=six_r_strategy,
                tech_stack=asset.technology_stack,
                complexity_score=asset.assessment_readiness_score,
                asset_type=asset.asset_type,
            )
        )

    return enriched_applications


async def _get_assessment_sixr_decisions(
    db: AsyncSession,
    client_account_id: str,
    engagement_id: str,
) -> dict:
    """
    Extract 6R decisions from assessment_flows and map to asset IDs.

    Assessment flow stores decisions with canonical_application_id in:
    phase_results['recommendation_generation']['results']['recommendation_generation']['applications']

    The mapping from canonical_application_id -> asset_ids is stored in:
    assessment_flows.application_asset_groups

    Returns:
        Dict mapping asset_id -> six_r_strategy
    """
    try:
        # Query assessment flows for this tenant/engagement
        result = await db.execute(
            select(AssessmentFlow).where(
                and_(
                    AssessmentFlow.client_account_id == client_account_id,
                    AssessmentFlow.engagement_id == engagement_id,
                    # Only flows with phase_results data
                    AssessmentFlow.phase_results.isnot(None),
                )
            )
        )
        flows = result.scalars().all()

        # Build lookup dict: asset_id -> six_r_strategy
        sixr_lookup = {}

        for flow in flows:
            phase_results = flow.phase_results or {}
            recommendation_gen = phase_results.get("recommendation_generation", {})

            # Navigate to nested structure where applications data lives:
            # recommendation_generation -> results -> recommendation_generation -> applications
            results = recommendation_gen.get("results", {})
            inner_rec_gen = results.get("recommendation_generation", {})
            applications = inner_rec_gen.get("applications", [])

            # Build canonical_app_id -> strategy lookup from phase_results
            canonical_to_strategy = {}
            for app_data in applications:
                canonical_app_id = str(app_data.get("application_id", ""))
                strategy = app_data.get("six_r_strategy")
                if canonical_app_id and strategy:
                    canonical_to_strategy[canonical_app_id] = strategy

            # Map canonical_application_id -> asset_ids using application_asset_groups
            app_asset_groups = flow.application_asset_groups or []
            for group in app_asset_groups:
                canonical_app_id = str(group.get("canonical_application_id", ""))
                asset_ids = group.get("asset_ids", [])

                # Get strategy for this canonical app
                strategy = canonical_to_strategy.get(canonical_app_id)
                if strategy:
                    # Map strategy to all associated asset IDs
                    for asset_id in asset_ids:
                        # Later flows override earlier ones (most recent wins)
                        sixr_lookup[str(asset_id)] = strategy

        return sixr_lookup

    except Exception as e:
        # Log error but don't fail the endpoint - return empty lookup
        logger.warning(f"Error fetching assessment 6R decisions: {e}")
        return {}
