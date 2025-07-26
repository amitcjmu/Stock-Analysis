#!/usr/bin/env python3
"""
Simple cleanup of orphaned discovery flows - no backup needed since we have full database audit
"""

import asyncio

from sqlalchemy import text

from app.core.database import AsyncSessionLocal


async def cleanup_orphaned_discovery_flows():
    """Delete discovery flows with invalid master_flow_id references."""
    async with AsyncSessionLocal() as db:
        print("🔍 Deleting orphaned discovery flows...")

        # Delete discovery flows with master_flow_id that don't exist in crewai_flow_state_extensions
        cleanup_query = text(
            """
            DELETE FROM discovery_flows
            WHERE master_flow_id IS NOT NULL
            AND master_flow_id NOT IN (
                SELECT flow_id FROM crewai_flow_state_extensions
            );
        """
        )

        result = await db.execute(cleanup_query)
        deleted_count = result.rowcount

        await db.commit()

        print(f"✅ Deleted {deleted_count} orphaned discovery flows")

        # Show final status
        status_query = text(
            """
            SELECT
                COUNT(*) as total_flows,
                COUNT(CASE WHEN master_flow_id IS NOT NULL THEN 1 END) as flows_with_master_id,
                COUNT(CASE WHEN master_flow_id IS NULL THEN 1 END) as flows_without_master_id
            FROM discovery_flows;
        """
        )

        result = await db.execute(status_query)
        stats = result.fetchone()

        print("📊 Final Status:")
        print(f"   Total Discovery Flows: {stats.total_flows}")
        print(f"   Flows with Master ID: {stats.flows_with_master_id}")
        print(f"   Flows without Master ID: {stats.flows_without_master_id}")


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_discovery_flows())
