"""
Gap Persistence - Database operations for gaps.

Handles deduplication, upserts, clearing existing gaps, and gap inheritance.
Gap inheritance ensures already-resolved gaps (from ANY flow) are not re-created.
"""

import logging
import math
from typing import Any, Dict, List, Set, Tuple
from uuid import UUID

from sqlalchemy import and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection_data_gap import CollectionDataGap

logger = logging.getLogger(__name__)


async def _get_resolved_fields_for_assets(
    asset_ids: List[UUID], db: AsyncSession
) -> Set[Tuple[str, str]]:
    """
    Get set of (asset_id, field_name) already resolved in ANY flow.

    GAP INHERITANCE: This enables skipping gaps that have already been
    resolved, regardless of which collection flow resolved them.

    Args:
        asset_ids: List of asset UUIDs to check
        db: Database session

    Returns:
        Set of (asset_id_str, field_name) tuples that are already resolved
    """
    if not asset_ids:
        return set()

    # Query for already-resolved gaps for these assets (from ANY flow)
    resolved_stmt = select(
        CollectionDataGap.asset_id, CollectionDataGap.field_name
    ).where(
        and_(
            CollectionDataGap.asset_id.in_(asset_ids),
            CollectionDataGap.resolution_status == "resolved",
        )
    )
    resolved_result = await db.execute(resolved_stmt)

    resolved_fields: Set[Tuple[str, str]] = set()
    for row in resolved_result:
        resolved_fields.add((str(row.asset_id), row.field_name))

    if resolved_fields:
        logger.info(
            f"🔄 Gap Inheritance: Found {len(resolved_fields)} already-resolved fields - "
            f"will skip creating duplicate gaps"
        )

    return resolved_fields


async def clear_existing_gaps(collection_flow_id: UUID, db: AsyncSession):
    """
    CRITICAL: Delete existing gaps for THIS flow only
    (tenant-scoped, never global). Allows re-running scan without duplicates.

    NOTE: This is called within scan_assets_for_gaps()
    which commits the transaction.
    """
    stmt = delete(CollectionDataGap).where(
        CollectionDataGap.collection_flow_id == collection_flow_id
    )
    await db.execute(stmt)
    logger.debug(f"🧹 Cleared existing gaps for flow {collection_flow_id}")


async def persist_gaps_with_dedup(
    gaps: List[Dict[str, Any]], collection_flow_id: UUID, db: AsyncSession
) -> int:
    """
    Persist gaps with deduplication using composite unique constraint.
    Upsert pattern: (collection_flow_id, field_name, gap_type, asset_id) uniqueness.

    GAP INHERITANCE: Skips creating gaps for fields that are already resolved
    for the same asset (from ANY previous collection flow).

    CRITICAL:
    - asset_id is NOT NULL (enforced by schema)
    - Uses func.now() for updated_at (not string "NOW()")
    - Updates ALL fields on conflict (including AI enhancements)
    - No explicit commit - handled by parent transaction
    """
    gaps_persisted = 0
    gaps_skipped = 0

    # GAP INHERITANCE: Get already-resolved fields to skip
    asset_ids = []
    for gap in gaps:
        if gap.get("asset_id"):
            try:
                asset_ids.append(UUID(gap["asset_id"]))
            except (ValueError, TypeError):
                pass
    resolved_fields = await _get_resolved_fields_for_assets(list(set(asset_ids)), db)

    for gap in gaps:
        # Sanitize numeric fields (no NaN/Inf)
        confidence_score = gap.get("confidence_score")
        if confidence_score is not None and (
            math.isnan(confidence_score) or math.isinf(confidence_score)
        ):
            confidence_score = None

        # CRITICAL: asset_id is required (NOT NULL)
        if not gap.get("asset_id"):
            logger.warning(f"Skipping gap without asset_id: {gap.get('field_name')}")
            continue

        # Defensive UUID conversion with error handling
        try:
            asset_uuid = UUID(gap["asset_id"])
        except (ValueError, TypeError, KeyError) as uuid_error:
            logger.warning(
                f"⚠️ Skipping gap with invalid asset_id: {gap.get('field_name')} - "
                f"asset_id={gap.get('asset_id')} - Error: {uuid_error}"
            )
            continue

        # GAP INHERITANCE: Skip if this field is already resolved for this asset
        field_name = gap.get("field_name", "unknown")
        if (str(asset_uuid), field_name) in resolved_fields:
            logger.debug(
                f"🔄 Skipping already-resolved gap: {field_name} for asset {str(asset_uuid)[:8]}..."
            )
            gaps_skipped += 1
            continue

        gap_record = {
            "collection_flow_id": collection_flow_id,
            "asset_id": asset_uuid,  # NOT NULL - required
            "field_name": gap["field_name"],
            "gap_type": gap["gap_type"],
            "gap_category": gap.get("gap_category", "unknown"),
            "priority": gap.get("priority", 3),
            "description": gap.get("description", gap.get("field_name", "")),
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

    # Log gap inheritance statistics
    if gaps_skipped > 0:
        logger.info(
            f"💾 Persisted {gaps_persisted} gaps (skipped {gaps_skipped} already-resolved)"
        )

    return gaps_persisted
