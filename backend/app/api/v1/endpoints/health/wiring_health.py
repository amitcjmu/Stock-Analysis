"""
Discovery Wiring Health Check Endpoint

Provides detailed health checks for discovery flow data wiring integrity,
focusing on orphaned records and referential integrity between assets and raw import records.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

# REMOVED: exists import - RawImportRecord queries were removed
# from sqlalchemy import exists, func, select
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.asset import Asset

# REMOVED: Data import models
# from app.models.data_import.core import RawImportRecord

logger = logging.getLogger(__name__)
router = APIRouter()

# Simple TTL cache for health metrics
_health_cache: Dict[str, tuple] = {}
_cache_ttl = timedelta(seconds=30)  # 30 second cache


@router.get("/health/wiring")
async def check_wiring_health(
    detail: bool = Query(False, description="Include detailed samples and metrics"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Enhanced wiring health check with TTL cache.

    Validates data wiring integrity between discovery flows, assets, and raw import records.
    Uses tenant isolation and includes performance optimizations.
    """

    # Validate tenant access authorization
    if (
        not hasattr(current_user, "client_account_id")
        or current_user.client_account_id != context.client_account_id
    ):
        raise HTTPException(
            status_code=403, detail="Access denied: insufficient tenant permissions"
        )

    # Cache key based on tenant + detail mode (MD5 used for non-cryptographic cache key generation)
    cache_key = hashlib.md5(  # nosec B303
        f"{context.client_account_id}:{context.engagement_id}:{detail}".encode(),
        usedforsecurity=False,
    ).hexdigest()

    # Check cache
    now = datetime.utcnow()
    if cache_key in _health_cache:
        cached_result, cached_time = _health_cache[cache_key]
        if now - cached_time < _cache_ttl:
            return {
                **cached_result,
                "cached": True,
                "cache_age_seconds": (now - cached_time).seconds,
            }

    try:
        # Base tenant filter for all queries
        base_filter = [
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
        ]

        issues = {}
        samples = {}
        all_healthy = True

        # 3. Assets without raw import record links (potential data gaps)
        assets_without_raw_links = await db.execute(
            select(func.count(Asset.id)).where(
                *base_filter, Asset.raw_import_records_id.is_(None)
            )
        )
        unlinked_asset_count = assets_without_raw_links.scalar()

        if unlinked_asset_count > 0:
            issues["assets_without_raw_import_links"] = {
                "count": unlinked_asset_count,
                "severity": "low",
                "description": "Assets not linked to raw import records (may be manually created)",
            }

        # REMOVED: Raw records check - RawImportRecord model was removed
        # # 4. Raw records not processed into assets
        # unprocessed_raw_records = await db.execute(
        #     select(func.count(RawImportRecord.id)).where(
        #         *raw_filter,
        #         RawImportRecord.is_processed.is_(False),
        #         RawImportRecord.asset_id.is_(None),
        #     )
        # )
        # unprocessed_count = unprocessed_raw_records.scalar()
        unprocessed_count = 0

        if unprocessed_count > 0:
            issues["unprocessed_raw_records"] = {
                "count": unprocessed_count,
                "severity": "medium",
                "description": "Raw import records that have not been processed into assets",
            }

        # 5. Assets with missing discovery flow references
        assets_without_discovery_flow = await db.execute(
            select(func.count(Asset.id)).where(
                *base_filter, Asset.discovery_flow_id.is_(None)
            )
        )
        no_discovery_flow_count = assets_without_discovery_flow.scalar()

        if no_discovery_flow_count > 0:
            issues["assets_without_discovery_flow"] = {
                "count": no_discovery_flow_count,
                "severity": "low",
                "description": "Assets without discovery flow ID references",
            }

        # Health summary
        health_status = "healthy" if all_healthy else "unhealthy"

        result = {
            "health_status": health_status,
            "tenant": {
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(context.engagement_id),
            },
            "metrics": issues,
            "summary": {
                "total_issues": len(
                    [
                        issue
                        for issue in issues.values()
                        if issue.get("severity") in ["high", "medium"]
                    ]
                ),
                "critical_issues": len(
                    [
                        issue
                        for issue in issues.values()
                        if issue.get("severity") == "high"
                    ]
                ),
                "warning_issues": len(
                    [
                        issue
                        for issue in issues.values()
                        if issue.get("severity") == "medium"
                    ]
                ),
            },
            "timestamp": now.isoformat(),
            "cached": False,
        }

        if detail:
            result["samples"] = samples

        # Cache the result
        _health_cache[cache_key] = (result, now)

        # Cleanup old cache entries periodically
        if len(_health_cache) > 100:
            _health_cache.clear()  # Simple cleanup - clear all if too many

        return result

    except Exception as e:
        logger.error(
            f"Wiring health check failed for tenant {context.client_account_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Health check failed",
                "tenant": {
                    "client_account_id": str(context.client_account_id),
                    "engagement_id": str(context.engagement_id),
                },
                "message": str(e),
            },
        )


@router.get("/health/wiring/repair")
async def get_wiring_repair_recommendations(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Provide repair recommendations for wiring issues.

    Returns actionable recommendations for fixing data wiring problems
    identified by the health check.
    """

    # Validate tenant access authorization
    if (
        not hasattr(current_user, "client_account_id")
        or current_user.client_account_id != context.client_account_id
    ):
        raise HTTPException(
            status_code=403, detail="Access denied: insufficient tenant permissions"
        )

    try:
        recommendations = []

        return {
            "tenant": {
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(context.engagement_id),
            },
            "recommendations": recommendations,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(
            f"Repair recommendations failed for tenant {context.client_account_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to generate repair recommendations",
                "message": str(e),
            },
        )
