#!/usr/bin/env python3
"""
Backfill missing master flow records for collection flows (Bug #646 fix).

This script creates master flow records for any collection flows that exist
without a corresponding master flow record in crewai_flow_state_extensions.

Per ADR-006, every flow MUST have a master flow record as single source of truth.

Usage:
    python scripts/backfill_collection_master_flows.py [--dry-run]
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.collection_flow import CollectionFlow
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def find_orphaned_flows(db: AsyncSession) -> list[CollectionFlow]:
    """Find collection flows without master flow records."""
    # Get all existing master flow IDs in a single query (optimization)
    master_flow_ids_result = await db.execute(
        select(CrewAIFlowStateExtensions.flow_id)
    )
    existing_master_flow_ids = {f_id for f_id, in master_flow_ids_result}

    # Get all collection flows
    result = await db.execute(select(CollectionFlow))
    all_flows = result.scalars().all()

    orphaned = []
    for flow in all_flows:
        # Check for existence in the set (in-memory, no DB query)
        if flow.flow_id not in existing_master_flow_ids:
            orphaned.append(flow)
            logger.warning(
                f"Found orphaned flow: {flow.flow_id} (name: {flow.flow_name}, "
                f"status: {flow.status}, created: {flow.created_at})"
            )

    return orphaned


async def backfill_master_flow(
    db: AsyncSession, collection_flow: CollectionFlow, dry_run: bool = False
) -> None:
    """Create master flow record for an orphaned collection flow."""
    if dry_run:
        logger.info(
            f"[DRY RUN] Would create master flow for: {collection_flow.flow_id}"
        )
        return

    # Create master flow record
    master_flow = CrewAIFlowStateExtensions(
        flow_id=collection_flow.flow_id,
        flow_type="collection",
        flow_status=collection_flow.status or "initialized",
        client_account_id=collection_flow.client_account_id,
        engagement_id=collection_flow.engagement_id,
        user_id=collection_flow.user_id,
        # Initialize phase transitions from current phase
        phase_transitions=[
            {
                "phase": collection_flow.current_phase or "initialization",
                "status": (
                    "active" if collection_flow.status == "running" else "completed"
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "source": "backfill_script",
                    "reason": "Bug #646 fix - create missing master flow",
                    "original_created_at": (
                        collection_flow.created_at.isoformat()
                        if collection_flow.created_at
                        else None
                    ),
                },
            }
        ],
        flow_persistence_data={
            "flow_id": str(collection_flow.flow_id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
            "backfilled": True,
        },
        error_history=[],
        phase_execution_times={},
        agent_state_snapshot={},
        created_at=collection_flow.created_at or datetime.now(timezone.utc),
        updated_at=collection_flow.updated_at or datetime.now(timezone.utc),
    )

    db.add(master_flow)

    # Update collection flow with master_flow_id reference
    collection_flow.master_flow_id = collection_flow.flow_id

    logger.info(
        f"✅ Created master flow for collection flow: {collection_flow.flow_id}"
    )


async def main(dry_run: bool = False):
    """Main backfill script."""
    logger.info("=" * 80)
    logger.info("Collection Flow Master Flow Backfill Script (Bug #646 Fix)")
    logger.info("=" * 80)
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'PRODUCTION'}")
    logger.info("")

    # Validate DATABASE_URL exists (without logging credentials)
    if not settings.DATABASE_URL:
        raise ValueError("DATABASE_URL not configured in settings")

    # Create async engine (echo=False prevents SQL/URL logging for security)
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False,  # Security: Prevents credentials from being logged in SQL statements
    )

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        try:
            # Find orphaned flows
            logger.info("🔍 Searching for collection flows without master flows...")
            orphaned_flows = await find_orphaned_flows(db)

            if not orphaned_flows:
                logger.info(
                    "✅ No orphaned flows found. All collection flows have master flows."
                )
                return

            logger.info(f"⚠️  Found {len(orphaned_flows)} orphaned collection flows")
            logger.info("")

            # Backfill each orphaned flow
            for i, flow in enumerate(orphaned_flows, 1):
                logger.info(f"Processing {i}/{len(orphaned_flows)}: {flow.flow_id}")
                await backfill_master_flow(db, flow, dry_run=dry_run)

            if not dry_run:
                # Commit transaction
                await db.commit()
                logger.info("")
                logger.info(
                    f"✅ Successfully backfilled {len(orphaned_flows)} master flows"
                )
            else:
                logger.info("")
                logger.info(
                    f"[DRY RUN] Would backfill {len(orphaned_flows)} master flows"
                )
                logger.info("Run without --dry-run to apply changes")

        except Exception as e:
            logger.error(f"❌ Error during backfill: {e}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()

    logger.info("")
    logger.info("=" * 80)
    logger.info("Backfill Complete")
    logger.info("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill missing master flows for collection flows"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them",
    )

    args = parser.parse_args()

    asyncio.run(main(dry_run=args.dry_run))
