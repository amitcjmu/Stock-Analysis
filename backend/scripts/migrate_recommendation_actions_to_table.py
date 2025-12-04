#!/usr/bin/env python3
"""
Migration script to consolidate recommendation actions from JSONB storage to database table.

Per ADR-012, child flows store operational decisions. This script migrates recommendation
actions from discovery_flows.crewai_state_data.data_cleansing_results.recommendation_actions
to the data_cleansing_recommendations table.

This consolidates dual storage into a single source of truth (the table).
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.data_cleansing import (  # noqa: E402
    DataCleansingRecommendation,
)
from app.models.discovery_flow import DiscoveryFlow  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def find_flows_with_jsonb_actions(db) -> List[DiscoveryFlow]:
    """Find all discovery flows that have recommendation_actions in JSONB."""
    flows_with_actions = []

    result = await db.execute(select(DiscoveryFlow))
    all_flows = result.scalars().all()

    for flow in all_flows:
        crewai_data = flow.crewai_state_data or {}
        data_cleansing_results = crewai_data.get("data_cleansing_results", {})
        recommendation_actions = data_cleansing_results.get(
            "recommendation_actions", {}
        )

        if recommendation_actions:
            flows_with_actions.append(flow)

    return flows_with_actions


async def migrate_actions_for_flow(  # noqa: C901 - one-time migration script
    flow: DiscoveryFlow,
    db,
    dry_run: bool = False,
    cleanup_jsonb: bool = False,
) -> Dict[str, int]:
    """
    Migrate recommendation actions from JSONB to database table for a single flow.

    Returns:
        Dict with counts: migrated, not_found, errors
    """
    stats = {"migrated": 0, "not_found": 0, "errors": 0}

    crewai_data = flow.crewai_state_data or {}
    data_cleansing_results = crewai_data.get("data_cleansing_results", {})
    recommendation_actions = data_cleansing_results.get("recommendation_actions", {})

    if not recommendation_actions:
        return stats

    logger.info(
        f"Processing flow {flow.flow_id}: {len(recommendation_actions)} actions found"
    )

    for recommendation_id_str, action_data in recommendation_actions.items():
        try:
            # Try to parse recommendation_id as UUID
            try:
                recommendation_uuid = UUID(recommendation_id_str)
            except ValueError:
                logger.warning(
                    f"Flow {flow.flow_id}: Recommendation ID '{recommendation_id_str}' "
                    f"is not a valid UUID. Skipping."
                )
                stats["errors"] += 1
                continue

            # Find the recommendation in the database table
            # Try matching by legacy_id first (for deterministic UUID5 IDs from JSONB)
            # Then try matching by id (for new random UUIDs)
            rec_query = select(DataCleansingRecommendation).where(
                (
                    (DataCleansingRecommendation.legacy_id == recommendation_uuid)
                    | (DataCleansingRecommendation.id == recommendation_uuid)
                ),
                DataCleansingRecommendation.flow_id == flow.flow_id,
            )
            rec_result = await db.execute(rec_query)
            db_rec = rec_result.scalar_one_or_none()

            if not db_rec:
                logger.warning(
                    f"Flow {flow.flow_id}: Recommendation {recommendation_id_str} "
                    f"not found in database table (checked both id and legacy_id). "
                    f"This may be a legacy recommendation that was never migrated to the table."
                )
                stats["not_found"] += 1
                continue

            # Extract action data from JSONB
            action_status = action_data.get("status", "pending")
            action_notes = action_data.get("notes")
            applied_by_user_id = action_data.get("applied_by_user_id")
            applied_at_str = action_data.get("applied_at")

            # Parse applied_at timestamp
            applied_at = None
            if applied_at_str:
                try:
                    # Handle ISO format strings
                    if isinstance(applied_at_str, str):
                        # Remove timezone info if present and parse
                        applied_at = datetime.fromisoformat(
                            applied_at_str.replace("Z", "+00:00")
                        )
                    else:
                        applied_at = applied_at_str
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Flow {flow.flow_id}: Could not parse applied_at "
                        f"'{applied_at_str}': {e}"
                    )

            if dry_run:
                logger.info(
                    f"  [DRY RUN] Would migrate action for recommendation {recommendation_id_str}: "
                    f"status={action_status}, applied_by={applied_by_user_id}"
                )
                stats["migrated"] += 1
            else:
                # Update the database record
                db_rec.status = action_status
                if action_notes:
                    db_rec.action_notes = action_notes
                if applied_by_user_id:
                    db_rec.applied_by_user_id = applied_by_user_id
                if applied_at:
                    db_rec.applied_at = applied_at

                db.add(db_rec)
                logger.info(
                    f"  Migrated action for recommendation {recommendation_id_str}: "
                    f"status={action_status}"
                )
                stats["migrated"] += 1

        except Exception:
            logger.exception(
                f"Flow {flow.flow_id}: Error migrating action for "
                f"recommendation {recommendation_id_str}"
            )
            stats["errors"] += 1

    # Clean up JSONB data after migration (if requested and not dry run)
    if cleanup_jsonb and not dry_run and stats["migrated"] > 0:
        logger.info(f"Cleaning up JSONB recommendation_actions for flow {flow.flow_id}")
        data_cleansing_results.pop("recommendation_actions", None)
        flow.crewai_state_data = crewai_data
        flag_modified(flow, "crewai_state_data")
        db.add(flow)

    return stats


async def migrate_all_actions(
    dry_run: bool = False, cleanup_jsonb: bool = False
) -> None:
    """Migrate all recommendation actions from JSONB to database table."""

    async with AsyncSessionLocal() as db:
        try:
            # Find all flows with JSONB actions
            flows_with_actions = await find_flows_with_jsonb_actions(db)
            total_flows = len(flows_with_actions)

            if total_flows == 0:
                logger.info("No flows found with recommendation_actions in JSONB.")
                logger.info("Migration complete - nothing to migrate.")
                return

            logger.info(
                f"Found {total_flows} flows with recommendation_actions in JSONB"
            )

            if dry_run:
                logger.info("=" * 80)
                logger.info("DRY RUN MODE - No changes will be made")
                logger.info("=" * 80)

            total_stats = {"migrated": 0, "not_found": 0, "errors": 0}

            for flow in flows_with_actions:
                flow_stats = await migrate_actions_for_flow(
                    flow, db, dry_run=dry_run, cleanup_jsonb=cleanup_jsonb
                )

                # Accumulate stats
                for key in total_stats:
                    total_stats[key] += flow_stats[key]

            # Commit changes if not dry run
            if not dry_run:
                await db.commit()
                logger.info("=" * 80)
                logger.info("Migration completed successfully!")
                logger.info("=" * 80)
            else:
                logger.info("=" * 80)
                logger.info("DRY RUN completed - No changes were made")
                logger.info("=" * 80)

            # Print summary
            logger.info("=" * 80)
            logger.info("MIGRATION SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Total flows processed: {total_flows}")
            logger.info(f"Actions migrated: {total_stats['migrated']}")
            logger.info(
                f"Recommendations not found in table: {total_stats['not_found']}"
            )
            logger.info(f"Errors: {total_stats['errors']}")
            logger.info("=" * 80)

            if total_stats["not_found"] > 0:
                logger.warning(
                    f"\n⚠️  {total_stats['not_found']} actions could not be migrated because "
                    f"the corresponding recommendations don't exist in the database table.\n"
                    f"This is expected for legacy flows that used deterministic IDs.\n"
                    f"These actions will remain in JSONB storage until the recommendations "
                    f"are recreated in the table."
                )

        except Exception:
            logger.exception("Migration failed")
            await db.rollback()
            raise


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate recommendation actions from JSONB to database table"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )
    parser.add_argument(
        "--cleanup-jsonb",
        action="store_true",
        help="Remove recommendation_actions from JSONB after successful migration",
    )

    args = parser.parse_args()

    if args.cleanup_jsonb and args.dry_run:
        logger.warning(
            "⚠️  --cleanup-jsonb has no effect in --dry-run mode. "
            "Run without --dry-run to clean up JSONB data."
        )

    asyncio.run(
        migrate_all_actions(dry_run=args.dry_run, cleanup_jsonb=args.cleanup_jsonb)
    )


if __name__ == "__main__":
    main()
