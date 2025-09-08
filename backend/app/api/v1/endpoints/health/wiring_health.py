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
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.asset import Asset
from app.models.data_import.core import RawImportRecord

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

    # Cache key based on tenant + detail mode
    cache_key = hashlib.md5(
        f"{context.client_account_id}:{context.engagement_id}:{detail}".encode()
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

        raw_filter = [
            RawImportRecord.client_account_id == context.client_account_id,
            RawImportRecord.engagement_id == context.engagement_id,
        ]

        issues = {}
        samples = {}
        all_healthy = True

        # 1. Assets with orphaned raw_import_records_id references
        assets_with_orphan_raw_ref = await db.execute(
            select(func.count(Asset.id)).where(
                *base_filter,
                Asset.raw_import_records_id.isnot(None),
                ~exists(
                    select(1).where(
                        RawImportRecord.id == Asset.raw_import_records_id,
                        RawImportRecord.client_account_id == Asset.client_account_id,
                        RawImportRecord.engagement_id == Asset.engagement_id,
                    )
                ),
            )
        )
        orphan_asset_count = assets_with_orphan_raw_ref.scalar()

        if orphan_asset_count > 0:
            all_healthy = False
            issues["assets_with_orphan_raw_references"] = {
                "count": orphan_asset_count,
                "severity": "high",
                "description": "Assets referencing non-existent raw import records",
            }

            if detail:
                # Get sample assets with orphan references
                sample_assets = await db.execute(
                    select(Asset.id, Asset.name, Asset.raw_import_records_id)
                    .where(
                        *base_filter,
                        Asset.raw_import_records_id.isnot(None),
                        ~exists(
                            select(1).where(
                                RawImportRecord.id == Asset.raw_import_records_id,
                                RawImportRecord.client_account_id
                                == context.client_account_id,
                                RawImportRecord.engagement_id == context.engagement_id,
                            )
                        ),
                    )
                    .limit(5)
                )
                samples["assets_with_orphan_raw_references"] = [
                    {
                        "asset_id": str(row.id),
                        "asset_name": row.name,
                        "orphan_raw_id": str(row.raw_import_records_id),
                    }
                    for row in sample_assets
                ]

        # 2. Raw import records with orphaned asset_id references
        raw_with_orphan_asset_ref = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                *raw_filter,
                RawImportRecord.asset_id.isnot(None),
                ~exists(
                    select(1).where(
                        Asset.id == RawImportRecord.asset_id,
                        Asset.client_account_id == context.client_account_id,
                        Asset.engagement_id == context.engagement_id,
                    )
                ),
            )
        )
        orphan_raw_count = raw_with_orphan_asset_ref.scalar()

        if orphan_raw_count > 0:
            all_healthy = False
            issues["raw_records_with_orphan_asset_references"] = {
                "count": orphan_raw_count,
                "severity": "medium",
                "description": "Raw import records referencing non-existent assets",
            }

            if detail:
                sample_raws = await db.execute(
                    select(
                        RawImportRecord.id,
                        RawImportRecord.row_number,
                        RawImportRecord.asset_id,
                    )
                    .where(
                        *raw_filter,
                        RawImportRecord.asset_id.isnot(None),
                        ~exists(
                            select(1).where(
                                Asset.id == RawImportRecord.asset_id,
                                Asset.client_account_id == context.client_account_id,
                                Asset.engagement_id == context.engagement_id,
                            )
                        ),
                    )
                    .limit(5)
                )
                samples["raw_records_with_orphan_asset_references"] = [
                    {
                        "raw_record_id": str(row.id),
                        "row_number": row.row_number,
                        "orphan_asset_id": str(row.asset_id),
                    }
                    for row in sample_raws
                ]

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

        # 4. Raw records not processed into assets
        unprocessed_raw_records = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                *raw_filter,
                RawImportRecord.is_processed.is_(False),
                RawImportRecord.asset_id.is_(None),
            )
        )
        unprocessed_count = unprocessed_raw_records.scalar()

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

    try:
        recommendations = []

        # Check for specific issues and provide targeted recommendations
        base_filter = [
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
        ]

        # Check for orphaned asset references
        assets_with_orphan_raw_ref = await db.execute(
            select(func.count(Asset.id)).where(
                *base_filter,
                Asset.raw_import_records_id.isnot(None),
                ~exists(
                    select(1).where(
                        RawImportRecord.id == Asset.raw_import_records_id,
                        RawImportRecord.client_account_id == context.client_account_id,
                        RawImportRecord.engagement_id == context.engagement_id,
                    )
                ),
            )
        )

        if assets_with_orphan_raw_ref.scalar() > 0:
            recommendations.append(
                {
                    "issue": "assets_with_orphan_raw_references",
                    "severity": "high",
                    "action": "NULL out orphaned raw_import_records_id references",
                    "sql_hint": (
                        "UPDATE assets SET raw_import_records_id = NULL "
                        "WHERE raw_import_records_id NOT IN (SELECT id FROM raw_import_records)"
                    ),
                    "automation": "Use asset cleanup scripts or run discovery flow repair",
                }
            )

        # Check for unprocessed raw records
        raw_filter = [
            RawImportRecord.client_account_id == context.client_account_id,
            RawImportRecord.engagement_id == context.engagement_id,
        ]

        unprocessed_raw = await db.execute(
            select(func.count(RawImportRecord.id)).where(
                *raw_filter,
                RawImportRecord.is_processed.is_(False),
                RawImportRecord.asset_id.is_(None),
            )
        )

        if unprocessed_raw.scalar() > 0:
            recommendations.append(
                {
                    "issue": "unprocessed_raw_records",
                    "severity": "medium",
                    "action": "Reprocess raw import records through asset creation pipeline",
                    "automation": "Trigger asset inventory phase or manual asset creation from raw data",
                }
            )

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
