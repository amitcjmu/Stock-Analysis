"""Gap persistence utilities."""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.collection_data_gap import CollectionDataGap

logger = logging.getLogger(__name__)


async def persist_gaps(
    result_dict: Dict[str, Any],
    assets: List[Asset],
    db: AsyncSession,
    collection_flow_id: str,
) -> int:
    """Persist gaps to collection_data_gaps table.

    Args:
        result_dict: Parsed gap analysis result
        assets: List of analyzed assets (for logging)
        db: Database session
        collection_flow_id: Collection flow ID for FK reference

    Returns:
        Number of gaps persisted
    """
    gaps_by_priority = result_dict.get("gaps", {})
    gaps_persisted = 0
    gaps_failed = 0

    logger.debug(
        f"📥 Persisting gaps - Priority levels: {list(gaps_by_priority.keys())}"
    )

    for priority_level, gaps in gaps_by_priority.items():
        if not isinstance(gaps, list):
            logger.warning(
                f"⚠️ Skipping non-list gaps for priority '{priority_level}': {type(gaps)}"
            )
            continue

        priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        priority_value = priority_map.get(priority_level, 3)

        logger.debug(
            f"📝 Processing {len(gaps)} {priority_level} gaps (priority={priority_value})"
        )

        for gap in gaps:
            try:
                gap_record = CollectionDataGap(
                    collection_flow_id=UUID(collection_flow_id),
                    gap_type=gap.get("gap_type", "missing_field"),
                    gap_category=gap.get("gap_category", "unknown"),
                    field_name=gap.get("field_name", "unknown"),
                    description=gap.get("description", ""),
                    impact_on_sixr=gap.get("impact_on_sixr", "medium"),
                    priority=priority_value,
                    suggested_resolution=gap.get(
                        "suggested_resolution",
                        "Manual collection required",
                    ),
                    resolution_status="pending",
                    gap_metadata={
                        "asset_id": gap.get("asset_id"),
                        "priority_level": priority_level,
                    },
                )

                db.add(gap_record)
                gaps_persisted += 1

            except Exception as e:
                gaps_failed += 1
                logger.error(
                    f"❌ Failed to persist gap - Field: {gap.get('field_name', 'unknown')}, "
                    f"Asset: {gap.get('asset_id', 'unknown')}, Error: {e}"
                )
                continue

    await db.commit()
    logger.info(
        f"💾 Persisted {gaps_persisted} gaps to database "
        f"(failed: {gaps_failed}, flow: {collection_flow_id})"
    )

    return gaps_persisted
