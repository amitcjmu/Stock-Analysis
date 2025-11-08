"""
Programmatic Gap Scanner Service - Main orchestration.

Fast database scan for data gaps using shared inspectors from gap_detection module.
Refactored (Day 13 - Issue #980) to eliminate duplicate gap detection logic.
Uses GapAnalyzer orchestrator from app.services.gap_detection for consistency.
"""

import logging
import time
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import CollectionFlow
from app.models.canonical_applications import CanonicalApplication
from app.services.gap_detection import GapAnalyzer

from .persistence import clear_existing_gaps, persist_gaps_with_dedup
from .report_transformer import ReportTransformer

logger = logging.getLogger(__name__)


class ProgrammaticGapScanner:
    """
    Fast database scan for data gaps using shared inspectors.

    Refactored (Day 13 - Issue #980) to use GapAnalyzer instead of duplicate gap detection logic.
    Benefits:
    - Code deduplication: Eliminates ~200 lines of duplicate logic
    - Performance: 10-40x faster gap detection via shared inspectors
    - Consistency: Single source of truth for gap analysis across assessment & collection flows
    - Maintainability: Updates to inspectors benefit both flows automatically

    Enforces tenant scoping (client_account_id, engagement_id).
    No AI/agent involvement - pure attribute comparison with deduplication.
    """

    BATCH_SIZE = 50  # Process assets in batches to avoid memory issues

    def __init__(self):
        """Initialize with shared GapAnalyzer orchestrator and ReportTransformer."""
        self.gap_analyzer = GapAnalyzer()
        self.transformer = ReportTransformer()

    async def scan_assets_for_gaps(
        self,
        selected_asset_ids: List[str],
        collection_flow_id: str,
        client_account_id: str,
        engagement_id: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Scan assets and return data gaps with tenant scoping and deduplication.

        Args:
            selected_asset_ids: UUIDs of assets to scan
            collection_flow_id: Child collection flow UUID
                               (resolved from master if needed)
            client_account_id: Tenant client account UUID
            engagement_id: Engagement UUID
            db: AsyncSession

        Returns:
            {
                "gaps": [
                    {
                        "asset_id": "uuid",
                        "asset_name": "App-001",
                        "field_name": "technology_stack",
                        "gap_type": "missing_field",
                        "gap_category": "application",
                        "priority": 1,
                        "current_value": null,
                        "suggested_resolution": "Manual collection required",
                        "confidence_score": null  # No AI = no confidence
                    }
                ],
                "summary": {
                    "total_gaps": 16,
                    "assets_analyzed": 2,
                    "critical_gaps": 5,
                    "execution_time_ms": 234
                },
                "status": "SCAN_COMPLETE"
            }
        """
        start_time = time.time()

        try:
            # Convert UUIDs with validation (handle both string and UUID objects)
            asset_uuids = [
                UUID(aid) if isinstance(aid, str) else aid for aid in selected_asset_ids
            ]
            flow_uuid = (
                UUID(collection_flow_id)
                if isinstance(collection_flow_id, str)
                else collection_flow_id
            )
            client_uuid = (
                UUID(client_account_id)
                if isinstance(client_account_id, str)
                else client_account_id
            )
            engagement_uuid = (
                UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id
            )

            logger.info(
                f"🚀 Starting gap scan - Flow: {flow_uuid}, Assets: {len(asset_uuids)}"
            )

            # CRITICAL: Asset ownership validation
            stmt = select(CollectionFlow).where(
                CollectionFlow.id == flow_uuid,
                CollectionFlow.client_account_id == client_uuid,
                CollectionFlow.engagement_id == engagement_uuid,
            )
            result = await db.execute(stmt)
            flow = result.scalar_one_or_none()

            if not flow:
                logger.error(f"❌ Flow {flow_uuid} not found or not accessible")
                return {
                    "gaps": [],
                    "summary": {
                        "total_gaps": 0,
                        "assets_analyzed": 0,
                        "critical_gaps": 0,
                        "execution_time_ms": 0,
                        "gaps_persisted": 0,
                    },
                    "status": "SCAN_FAILED",
                    "error": f"Flow {flow_uuid} not found or not accessible",
                }

            # Validate assets are subset of flow's selected assets
            flow_selected_assets = set(
                (flow.flow_metadata or {}).get("selected_asset_ids", [])
            )
            requested_assets = set(str(aid) for aid in asset_uuids)

            if not requested_assets.issubset(flow_selected_assets):
                invalid_assets = requested_assets - flow_selected_assets
                logger.error(
                    f"❌ Assets {invalid_assets} not selected for flow {flow_uuid}"
                )
                return {
                    "gaps": [],
                    "summary": {
                        "total_gaps": 0,
                        "assets_analyzed": 0,
                        "critical_gaps": 0,
                        "execution_time_ms": 0,
                        "gaps_persisted": 0,
                    },
                    "status": "SCAN_FAILED",
                    "error": f"Assets {invalid_assets} not selected for this flow",
                }

            # CRITICAL: Wipe existing gaps for THIS flow (tenant-scoped, never global)
            await clear_existing_gaps(flow_uuid, db)

            # Load assets with tenant scoping
            stmt = select(Asset).where(
                Asset.id.in_(asset_uuids),
                Asset.client_account_id == client_uuid,
                Asset.engagement_id == engagement_uuid,
            )
            result = await db.execute(stmt)
            assets = list(result.scalars().all())

            if not assets:
                logger.warning("⚠️ No assets found for scan")
                return {
                    "gaps": [],
                    "summary": {
                        "total_gaps": 0,
                        "assets_analyzed": 0,
                        "critical_gaps": 0,
                        "execution_time_ms": 0,
                        "gaps_persisted": 0,
                    },
                    "status": "SCAN_COMPLETE_NO_ASSETS",
                }

            logger.info(f"📦 Loaded {len(assets)} assets: {[a.name for a in assets]}")

            # Use GapAnalyzer orchestrator instead of duplicate gap detection logic
            # (Day 13 - Issue #980 refactoring)
            all_gaps = []

            for asset in assets:
                # Get application if asset is an application type
                application = None
                asset_type = getattr(asset, "asset_type", "other")
                if asset_type.lower() == "application":
                    app_stmt = select(CanonicalApplication).where(
                        CanonicalApplication.id == asset.id
                    )
                    app_result = await db.execute(app_stmt)
                    application = app_result.scalar_one_or_none()

                logger.debug(
                    f"🔍 Asset '{asset.name}' (type: {asset_type}) - "
                    f"Using GapAnalyzer with 5 shared inspectors"
                )

                # Use GapAnalyzer to produce comprehensive report
                try:
                    comprehensive_report = await self.gap_analyzer.analyze_asset(
                        asset=asset,
                        application=application,
                        client_account_id=str(client_uuid),
                        engagement_id=str(engagement_uuid),
                        db=db,
                    )

                    # Transform ComprehensiveGapReport to legacy gap dict format
                    asset_gaps = self.transformer.transform_to_legacy_format(
                        comprehensive_report, asset
                    )
                    all_gaps.extend(asset_gaps)

                    logger.debug(
                        f"✅ Asset '{asset.name}': {len(asset_gaps)} gaps identified "
                        f"(completeness: {comprehensive_report.overall_completeness:.2f})"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Failed to analyze asset '{asset.name}': {e}",
                        exc_info=True,
                    )
                    # Continue with other assets even if one fails
                    continue

            logger.info(f"📊 Identified {len(all_gaps)} total gaps via GapAnalyzer")

            # Persist gaps to database with deduplication (upsert)
            gaps_persisted = await persist_gaps_with_dedup(all_gaps, flow_uuid, db)

            logger.info(f"💾 Persisted {gaps_persisted} gaps to database")

            # Commit the transaction (FastAPI manages the session)
            await db.commit()

            # CRITICAL FIX: Query gaps back from database with their UUIDs
            # This eliminates need for synthetic keys in frontend
            stmt = (
                select(CollectionDataGap, Asset.name)
                .join(Asset, CollectionDataGap.asset_id == Asset.id, isouter=True)
                .where(CollectionDataGap.collection_flow_id == flow_uuid)
            )
            result = await db.execute(stmt)
            rows = result.all()

            # Convert to dict format with database IDs
            gaps_with_ids = []
            for gap, asset_name in rows:
                gaps_with_ids.append(
                    {
                        "id": str(gap.id),  # ✅ Database UUID
                        "asset_id": str(gap.asset_id),
                        "asset_name": asset_name or "Unknown Asset",
                        "field_name": gap.field_name,
                        "gap_type": gap.gap_type,
                        "gap_category": gap.gap_category,
                        "priority": gap.priority,
                        "current_value": gap.resolved_value,
                        "suggested_resolution": gap.suggested_resolution,
                        "confidence_score": gap.confidence_score,
                    }
                )

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Emit telemetry (tenant-scoped metrics)
            await self._emit_telemetry(
                {
                    "event": "gap_scan_complete",
                    "client_account_id": str(client_uuid),
                    "engagement_id": str(engagement_uuid),
                    "flow_id": str(flow_uuid),
                    "gaps_total": len(gaps_with_ids),
                    "gaps_persisted": gaps_persisted,
                    "assets_analyzed": len(assets),
                    "execution_time_ms": execution_time_ms,
                }
            )

            logger.info(
                f"✅ Gap scan complete: {gaps_persisted} gaps persisted "
                f"in {execution_time_ms}ms"
            )

            return {
                "gaps": gaps_with_ids,  # ✅ Now includes database IDs
                "summary": {
                    "total_gaps": len(
                        gaps_with_ids
                    ),  # Use gaps_with_ids for consistency
                    "assets_analyzed": len(assets),
                    "critical_gaps": sum(
                        1 for g in gaps_with_ids if g["priority"] == 1
                    ),
                    "execution_time_ms": execution_time_ms,
                    "gaps_persisted": gaps_persisted,
                },
                "status": "SCAN_COMPLETE",
            }

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Gap scan failed: {e}", exc_info=True)
            await self._emit_telemetry(
                {
                    "event": "gap_scan_failed",
                    "error": str(e),
                    "execution_time_ms": execution_time_ms,
                }
            )
            return {
                "gaps": [],
                "summary": {
                    "total_gaps": 0,
                    "assets_analyzed": 0,
                    "critical_gaps": 0,
                    "execution_time_ms": execution_time_ms,
                    "gaps_persisted": 0,
                },
                "status": "SCAN_FAILED",
                "error": str(e),
            }

    async def _emit_telemetry(self, event_data: Dict[str, Any]):
        """Emit tenant-scoped metrics for observability."""
        logger.info(f"[TELEMETRY] {event_data}")
