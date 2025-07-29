#!/usr/bin/env python3
"""
Cleanup Demo Flows Script

This script removes any flows with demo UUID patterns that were created
due to the frontend fallback mechanism when proper flow IDs were not available.

Demo UUID pattern: XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX
"""
# flake8: noqa: E402

import asyncio
import os
import sys
from typing import Dict, List, Any
import uuid

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.data_import import DataImport
from app.models.discovery_flow import DiscoveryFlow
from app.models.field_mapping import FieldMapping

logger = get_logger(__name__)

# Demo UUID pattern - middle section is always "def0-def0-def0"
DEMO_UUID_PATTERN = "def0-def0-def0"


async def identify_demo_flows(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Identify flows with demo UUID patterns.

    Returns:
        List of flows with demo patterns including related data counts
    """
    demo_flows = []

    try:
        # Query all flows and check for demo pattern
        stmt = select(CrewAIFlowStateExtensions)
        result = await db.execute(stmt)
        all_flows = result.scalars().all()

        for flow in all_flows:
            flow_id_str = str(flow.flow_id)

            # Check if this flow has the demo pattern
            if DEMO_UUID_PATTERN in flow_id_str:
                logger.info(f"🔍 Found demo flow: {flow_id_str}")

                # Check for related data
                # 1. Discovery flow records
                discovery_stmt = select(DiscoveryFlow).where(
                    DiscoveryFlow.flow_id == flow.flow_id
                )
                discovery_result = await db.execute(discovery_stmt)
                discovery_count = len(discovery_result.scalars().all())

                # 2. Field mappings
                field_mapping_stmt = select(FieldMapping).where(
                    FieldMapping.flow_id == flow.flow_id
                )
                field_mapping_result = await db.execute(field_mapping_stmt)
                field_mapping_count = len(field_mapping_result.scalars().all())

                # 3. Data imports linked to this flow
                data_import_stmt = select(DataImport).where(
                    DataImport.master_flow_id == flow.flow_id
                )
                data_import_result = await db.execute(data_import_stmt)
                data_import_count = len(data_import_result.scalars().all())

                demo_flows.append(
                    {
                        "flow_id": flow_id_str,
                        "flow_type": flow.flow_type,
                        "status": flow.flow_status,
                        "created_at": flow.created_at,
                        "client_account_id": str(flow.client_account_id),
                        "engagement_id": str(flow.engagement_id),
                        "discovery_flows": discovery_count,
                        "field_mappings": field_mapping_count,
                        "data_imports": data_import_count,
                        "total_related_records": discovery_count
                        + field_mapping_count
                        + data_import_count,
                    }
                )

        logger.info(f"✅ Found {len(demo_flows)} demo flows total")
        return demo_flows

    except Exception as e:
        logger.error(f"❌ Error identifying demo flows: {e}")
        return []


async def cleanup_demo_flow(
    db: AsyncSession, flow_id: str, dry_run: bool = True
) -> bool:
    """
    Clean up a single demo flow and all related data.

    Args:
        db: Database session
        flow_id: Flow ID to clean up
        dry_run: If True, only log what would be deleted without actually deleting

    Returns:
        True if cleanup was successful
    """
    try:
        flow_uuid = uuid.UUID(flow_id)

        if dry_run:
            logger.info(f"🔍 DRY RUN - Would delete flow: {flow_id}")
        else:
            logger.info(f"🗑️ Deleting demo flow: {flow_id}")

        # Delete in order of dependencies
        # 1. Field mappings
        field_mapping_stmt = delete(FieldMapping).where(
            FieldMapping.flow_id == flow_uuid
        )
        if not dry_run:
            result = await db.execute(field_mapping_stmt)
            logger.info(f"   Deleted {result.rowcount} field mappings")

        # 2. Discovery flows
        discovery_stmt = delete(DiscoveryFlow).where(DiscoveryFlow.flow_id == flow_uuid)
        if not dry_run:
            result = await db.execute(discovery_stmt)
            logger.info(f"   Deleted {result.rowcount} discovery flows")

        # 3. Update data imports to remove master_flow_id reference
        if not dry_run:
            data_import_update_stmt = select(DataImport).where(
                DataImport.master_flow_id == flow_uuid
            )
            result = await db.execute(data_import_update_stmt)
            data_imports = result.scalars().all()

            for data_import in data_imports:
                data_import.master_flow_id = None
                logger.info(f"   Unlinked data import: {data_import.id}")

        # 4. Delete the master flow
        master_flow_stmt = delete(CrewAIFlowStateExtensions).where(
            CrewAIFlowStateExtensions.flow_id == flow_uuid
        )
        if not dry_run:
            result = await db.execute(master_flow_stmt)
            logger.info("   Deleted master flow record")

            # Commit the transaction
            await db.commit()
            logger.info(f"✅ Successfully deleted demo flow: {flow_id}")

        return True

    except Exception as e:
        logger.error(f"❌ Error cleaning up flow {flow_id}: {e}")
        if not dry_run:
            await db.rollback()
        return False


async def main():
    """Main function to run the cleanup script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up demo flows with invalid UUID patterns"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete the flows (default is dry run)",
    )
    parser.add_argument(
        "--client-id", help="Only clean up flows for specific client ID"
    )
    parser.add_argument(
        "--engagement-id", help="Only clean up flows for specific engagement ID"
    )

    args = parser.parse_args()

    logger.info("🚀 Starting demo flow cleanup script")
    logger.info(f"   Mode: {'EXECUTE' if args.execute else 'DRY RUN'}")
    if args.client_id:
        logger.info(f"   Client filter: {args.client_id}")
    if args.engagement_id:
        logger.info(f"   Engagement filter: {args.engagement_id}")

    async with AsyncSessionLocal() as db:
        # Identify demo flows
        demo_flows = await identify_demo_flows(db)

        # Apply filters if specified
        if args.client_id:
            demo_flows = [
                f for f in demo_flows if f["client_account_id"] == args.client_id
            ]
        if args.engagement_id:
            demo_flows = [
                f for f in demo_flows if f["engagement_id"] == args.engagement_id
            ]

        if not demo_flows:
            logger.info("✅ No demo flows found to clean up")
            return

        # Display summary
        logger.info("\n📊 Demo Flow Summary:")
        logger.info(f"   Total flows found: {len(demo_flows)}")

        total_related = sum(f["total_related_records"] for f in demo_flows)
        logger.info(f"   Total related records: {total_related}")

        # Group by client/engagement
        by_client = {}
        for flow in demo_flows:
            client_id = flow["client_account_id"]
            if client_id not in by_client:
                by_client[client_id] = []
            by_client[client_id].append(flow)

        logger.info("\n📊 By Client:")
        for client_id, flows in by_client.items():
            logger.info(f"   {client_id}: {len(flows)} flows")

        # Show detailed flow information
        logger.info("\n📋 Demo Flows to Clean:")
        for flow in demo_flows:
            logger.info(f"\n   Flow ID: {flow['flow_id']}")
            logger.info(f"   Type: {flow['flow_type']}")
            logger.info(f"   Status: {flow['status']}")
            logger.info(f"   Created: {flow['created_at']}")
            logger.info(f"   Related Records: {flow['total_related_records']}")

        if args.execute:
            # Confirm before proceeding
            logger.info(
                f"\n⚠️  WARNING: This will DELETE {len(demo_flows)} flows and {total_related} related records!"
            )
            response = input("Are you sure you want to proceed? (yes/no): ")

            if response.lower() != "yes":
                logger.info("❌ Cleanup cancelled")
                return

            # Perform cleanup
            logger.info("\n🗑️ Starting cleanup...")
            success_count = 0

            for flow in demo_flows:
                if await cleanup_demo_flow(db, flow["flow_id"], dry_run=False):
                    success_count += 1

            logger.info(
                f"\n✅ Cleanup complete: {success_count}/{len(demo_flows)} flows deleted"
            )
        else:
            logger.info(
                "\n✅ Dry run complete. Use --execute to actually delete the flows."
            )


if __name__ == "__main__":
    asyncio.run(main())
