"""
Programmatic Gap Scanner Service

Fast database scan for data gaps without AI involvement.
Compares assets against 22 critical attributes using SQLAlchemy 2.0 async Core.
"""

import logging
import math
import time
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.collection_data_gap import CollectionDataGap
from app.models.collection_flow import CollectionFlow
from app.services.collection.critical_attributes import CriticalAttributesDefinition

logger = logging.getLogger(__name__)


class ProgrammaticGapScanner:
    """
    Fast database scan for data gaps.

    Compares assets against 22 critical attributes using SQLAlchemy 2.0 async Core.
    Enforces tenant scoping (client_account_id, engagement_id).
    No AI/agent involvement - pure attribute comparison with deduplication.
    """

    BATCH_SIZE = 50  # Process assets in batches to avoid memory issues

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
            collection_flow_id: Child collection flow UUID (resolved from master if needed)
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
            # Convert UUIDs with validation
            asset_uuids = [UUID(aid) for aid in selected_asset_ids]
            flow_uuid = UUID(collection_flow_id)
            client_uuid = UUID(client_account_id)
            engagement_uuid = UUID(engagement_id)

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
            flow_selected_assets = set(flow.flow_metadata.get("selected_asset_ids", []))
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
            await self._clear_existing_gaps(flow_uuid, db)

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

            # Compare against critical attributes
            attribute_mapping = CriticalAttributesDefinition.get_attribute_mapping()
            all_gaps = []

            for asset in assets:
                asset_gaps = self._identify_gaps_for_asset(asset, attribute_mapping)
                all_gaps.extend(asset_gaps)

            logger.info(f"📊 Identified {len(all_gaps)} total gaps")

            # Persist gaps to database with deduplication (upsert)
            gaps_persisted = await self._persist_gaps_with_dedup(
                all_gaps, flow_uuid, db
            )

            logger.info(f"💾 Persisted {gaps_persisted} gaps to database")

            # Commit the transaction (FastAPI manages the session)
            await db.commit()

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Emit telemetry (tenant-scoped metrics)
            await self._emit_telemetry(
                {
                    "event": "gap_scan_complete",
                    "client_account_id": str(client_uuid),
                    "engagement_id": str(engagement_uuid),
                    "flow_id": str(flow_uuid),
                    "gaps_total": len(all_gaps),
                    "gaps_persisted": gaps_persisted,
                    "assets_analyzed": len(assets),
                    "execution_time_ms": execution_time_ms,
                }
            )

            logger.info(
                f"✅ Gap scan complete: {gaps_persisted} gaps persisted in {execution_time_ms}ms"
            )

            return {
                "gaps": all_gaps,
                "summary": {
                    "total_gaps": len(all_gaps),
                    "assets_analyzed": len(assets),
                    "critical_gaps": sum(1 for g in all_gaps if g["priority"] == 1),
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

    async def _clear_existing_gaps(self, collection_flow_id: UUID, db: AsyncSession):
        """
        CRITICAL: Delete existing gaps for THIS flow only (tenant-scoped, never global).
        Allows re-running scan without duplicates.

        NOTE: This is called within scan_assets_for_gaps() which commits the transaction.
        """
        stmt = delete(CollectionDataGap).where(
            CollectionDataGap.collection_flow_id == collection_flow_id
        )
        await db.execute(stmt)
        logger.debug(f"🧹 Cleared existing gaps for flow {collection_flow_id}")

    def _identify_gaps_for_asset(
        self, asset: Any, attribute_mapping: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify missing critical attributes for a single asset."""
        gaps = []

        for attr_name, attr_config in attribute_mapping.items():
            asset_fields = attr_config.get("asset_fields", [])

            # Check if asset has any of these fields populated
            has_value = False
            current_value = None

            for field in asset_fields:
                if "." in field:  # custom_attributes.field_name
                    parts = field.split(".", 1)
                    if hasattr(asset, parts[0]):
                        custom_attrs = getattr(asset, parts[0])
                        if custom_attrs and parts[1] in custom_attrs:
                            has_value = True
                            current_value = custom_attrs[parts[1]]
                            break
                else:
                    if hasattr(asset, field) and getattr(asset, field) is not None:
                        has_value = True
                        current_value = getattr(asset, field)
                        break

            if not has_value:
                gaps.append(
                    {
                        "asset_id": str(asset.id),
                        "asset_name": asset.name,
                        "field_name": attr_name,
                        "gap_type": "missing_field",
                        "gap_category": attr_config.get("category", "unknown"),
                        "priority": attr_config.get("priority", 3),
                        "current_value": current_value,
                        "suggested_resolution": "Manual collection required",
                        "confidence_score": None,  # No AI yet
                    }
                )

        return gaps

    async def _persist_gaps_with_dedup(
        self, gaps: List[Dict[str, Any]], collection_flow_id: UUID, db: AsyncSession
    ) -> int:
        """
        Persist gaps with deduplication using composite unique constraint.
        Upsert pattern: (collection_flow_id, field_name, gap_type, asset_id) uniqueness.

        CRITICAL:
        - asset_id is NOT NULL (enforced by schema)
        - Uses func.now() for updated_at (not string "NOW()")
        - Updates ALL fields on conflict (including AI enhancements)
        - No explicit commit - handled by parent transaction
        """
        gaps_persisted = 0

        for gap in gaps:
            # Sanitize numeric fields (no NaN/Inf)
            confidence_score = gap.get("confidence_score")
            if confidence_score is not None and (
                math.isnan(confidence_score) or math.isinf(confidence_score)
            ):
                confidence_score = None

            # CRITICAL: asset_id is required (NOT NULL)
            if not gap.get("asset_id"):
                logger.warning(
                    f"Skipping gap without asset_id: {gap.get('field_name')}"
                )
                continue

            gap_record = {
                "collection_flow_id": collection_flow_id,
                "asset_id": UUID(gap["asset_id"]),  # NOT NULL - required
                "field_name": gap["field_name"],
                "gap_type": gap["gap_type"],
                "gap_category": gap.get("gap_category", "unknown"),
                "priority": gap.get("priority", 3),
                "description": gap.get("suggested_resolution", ""),
                "impact_on_sixr": "medium",  # Default, can be enhanced by AI
                "suggested_resolution": gap.get(
                    "suggested_resolution", "Manual collection required"
                ),
                "resolution_status": "pending",
                "confidence_score": confidence_score,
                "ai_suggestions": gap.get("ai_suggestions"),  # May be None initially
                "resolution_method": None,  # Will be set on resolution
            }

            # Upsert using PostgreSQL INSERT ... ON CONFLICT DO UPDATE
            stmt = insert(CollectionDataGap).values(**gap_record)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_gaps_dedup",
                set_={
                    "priority": gap_record["priority"],
                    "suggested_resolution": gap_record["suggested_resolution"],
                    "description": gap_record["description"],
                    "confidence_score": gap_record["confidence_score"],
                    "ai_suggestions": gap_record["ai_suggestions"],
                    "updated_at": func.now(),
                },
            )
            await db.execute(stmt)
            gaps_persisted += 1

        return gaps_persisted

    async def _emit_telemetry(self, event_data: Dict[str, Any]):
        """Emit tenant-scoped metrics for observability."""
        logger.info(f"[TELEMETRY] {event_data}")
