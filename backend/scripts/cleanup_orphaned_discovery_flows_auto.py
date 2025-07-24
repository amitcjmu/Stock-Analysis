#!/usr/bin/env python3
"""
Automatic Cleanup of Orphaned Discovery Flows

This script identifies and deletes discovery flows that have invalid master_flow_id references
(pointing to non-existent master flows in crewai_flow_state_extensions table).
"""

import asyncio
from datetime import datetime

from app.core.database import AsyncSessionLocal
from app.models.discovery_flow import DiscoveryFlow
from sqlalchemy import delete, text


async def cleanup_orphaned_discovery_flows():
    """
    Identify and delete discovery flows with invalid master_flow_id references.
    """
    async with AsyncSessionLocal() as db:
        print("🔍 Identifying orphaned discovery flows...")

        # Find discovery flows with master_flow_id that don't exist in crewai_flow_state_extensions
        orphaned_flows_query = text(
            """
            SELECT 
                df.id,
                df.flow_id,
                df.master_flow_id,
                df.flow_name,
                df.created_at,
                df.client_account_id,
                df.engagement_id
            FROM discovery_flows df
            LEFT JOIN crewai_flow_state_extensions cfe ON df.master_flow_id = cfe.flow_id
            WHERE df.master_flow_id IS NOT NULL 
            AND cfe.flow_id IS NULL
            ORDER BY df.created_at DESC;
        """
        )

        result = await db.execute(orphaned_flows_query)
        orphaned_flows = result.fetchall()

        print(f"📊 Found {len(orphaned_flows)} orphaned discovery flows")

        if not orphaned_flows:
            print("✅ No orphaned discovery flows found!")
            return

        # Display orphaned flows for review
        print("\n🚨 Orphaned Discovery Flows to be deleted:")
        print("-" * 80)
        for flow in orphaned_flows:
            print(f"ID: {flow.id}")
            print(f"Flow ID: {flow.flow_id}")
            print(f"Name: {flow.flow_name}")
            print(f"Invalid Master Flow ID: {flow.master_flow_id}")
            print(f"Created: {flow.created_at}")
            print(f"Client Account: {flow.client_account_id}")
            print(f"Engagement: {flow.engagement_id}")
            print("-" * 80)

        # Create backup before deletion
        print(f"\n💾 Creating backup of {len(orphaned_flows)} orphaned flows...")
        backup_data = []
        for flow in orphaned_flows:
            backup_data.append(
                {
                    "id": str(flow.id),
                    "flow_id": flow.flow_id,
                    "master_flow_id": str(flow.master_flow_id),
                    "flow_name": flow.flow_name,
                    "created_at": flow.created_at.isoformat(),
                    "client_account_id": str(flow.client_account_id),
                    "engagement_id": str(flow.engagement_id),
                    "deleted_at": datetime.utcnow().isoformat(),
                }
            )

        # Save backup
        import json

        backup_filename = f"orphaned_discovery_flows_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"backend/scripts/{backup_filename}", "w") as f:
            json.dump(backup_data, f, indent=2)

        print(f"✅ Backup saved to: backend/scripts/{backup_filename}")

        # Delete orphaned discovery flows
        print(f"\n🗑️  Deleting {len(orphaned_flows)} orphaned discovery flows...")
        deletion_count = 0

        for flow in orphaned_flows:
            try:
                # Delete the orphaned discovery flow
                await db.execute(
                    delete(DiscoveryFlow).where(DiscoveryFlow.id == flow.id)
                )
                deletion_count += 1
                print(f"✅ Deleted flow: {flow.flow_name} (ID: {flow.id})")

            except Exception as e:
                print(f"❌ Error deleting flow {flow.id}: {e}")

        # Commit all deletions
        await db.commit()

        print(f"\n🎉 Successfully deleted {deletion_count} orphaned discovery flows!")
        print(f"💾 Backup preserved at: backend/scripts/{backup_filename}")

        # Verify cleanup
        print("\n🔍 Verifying cleanup...")
        verification_result = await db.execute(orphaned_flows_query)
        remaining_orphaned = verification_result.fetchall()

        if remaining_orphaned:
            print(f"⚠️  {len(remaining_orphaned)} orphaned flows still remain!")
            for flow in remaining_orphaned:
                print(f"   - {flow.flow_name} (ID: {flow.id})")
        else:
            print("✅ All orphaned discovery flows have been successfully deleted!")

        # Show final discovery flows status
        print("\n📊 Final Discovery Flows Status:")
        flows_count_query = text(
            """
            SELECT 
                COUNT(*) as total_flows,
                COUNT(CASE WHEN master_flow_id IS NOT NULL THEN 1 END) as flows_with_master_id,
                COUNT(CASE WHEN master_flow_id IS NULL THEN 1 END) as flows_without_master_id
            FROM discovery_flows;
        """
        )

        final_result = await db.execute(flows_count_query)
        final_stats = final_result.fetchone()

        print(f"Total Discovery Flows: {final_stats.total_flows}")
        print(f"Flows with Master ID: {final_stats.flows_with_master_id}")
        print(f"Flows without Master ID: {final_stats.flows_without_master_id}")

        if final_stats.total_flows > 0:
            coverage = (
                final_stats.flows_with_master_id / final_stats.total_flows
            ) * 100
            print(f"Master Flow Coverage: {coverage:.1f}%")


if __name__ == "__main__":
    asyncio.run(cleanup_orphaned_discovery_flows())
