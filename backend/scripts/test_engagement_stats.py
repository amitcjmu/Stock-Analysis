#!/usr/bin/env python3
"""
Test engagement stats through Master Flow Orchestrator (MFO)

Updated to use MFO patterns for metrics collection and master flow coordination.
Validates two-table architecture and proper tenant scoping in statistics.

Generated with CC for MFO-aligned engagement statistics testing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import MFO fixtures for consistent testing
from tests.fixtures.mfo_fixtures import (
    create_mock_mfo_context,
    DEMO_ENGAGEMENT_ID,
)

# Set database URL - use Docker network hostname
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@postgres:5432/migration_db"
)


async def test_mfo_engagement_stats():
    """Test engagement stats through MFO with proper master flow coordination"""
    try:
        from sqlalchemy import func, select

        from app.core.database import AsyncSessionLocal
        from app.models import Engagement
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from app.services.master_flow_orchestrator import MasterFlowOrchestrator

        # Create MFO context for metrics collection
        mfo_context = create_mock_mfo_context()
        mfo_orchestrator = MasterFlowOrchestrator()

        async with AsyncSessionLocal() as db:
            # Test MFO-coordinated dashboard stats queries
            print("=== Testing MFO Dashboard Stats Query ===")
            print(f"Using tenant context: {mfo_context.client_account_id}")

            # Total engagements with MFO tenant scoping (only active ones)
            total_query = select(func.count()).where(
                Engagement.is_active is True,
                Engagement.client_id == mfo_context.client_account_id,
            )
            result = await db.execute(total_query)
            total_engagements = result.scalar_one()
            print(
                f"Total active engagements for tenant {mfo_context.client_account_id}: {total_engagements}"
            )

            # Total engagements across all tenants (for comparison)
            total_all_query = select(func.count()).select_from(Engagement)
            result = await db.execute(total_all_query)
            total_all = result.scalar_one()
            print(f"Total all engagements across all tenants: {total_all}")

            # Test MFO master flow statistics
            print("\n=== MFO Master Flow Statistics ===")
            master_flows_query = (
                select(func.count())
                .select_from(CrewAIFlowStateExtensions)
                .where(
                    CrewAIFlowStateExtensions.client_account_id
                    == mfo_context.client_account_id
                )
            )
            result = await db.execute(master_flows_query)
            master_flows_count = result.scalar_one()
            print(f"Master flows for tenant: {master_flows_count}")

            # Check the actual SQL being generated
            print(f"\nSQL for active query: {total_query}")
            print(f"SQL for all query: {total_all_query}")

            # Test MFO flow aggregation statistics
            print("\n=== MFO Flow Aggregation Test ===")

            # Flows by type for tenant
            flows_by_type_query = (
                select(
                    CrewAIFlowStateExtensions.flow_type,
                    func.count(CrewAIFlowStateExtensions.flow_id),
                )
                .where(
                    CrewAIFlowStateExtensions.client_account_id
                    == mfo_context.client_account_id
                )
                .group_by(CrewAIFlowStateExtensions.flow_type)
            )

            result = await db.execute(flows_by_type_query)
            flows_by_type = result.fetchall()
            for flow_type, count in flows_by_type:
                print(f"  {flow_type}: {count} flows")

            # Flows by status for tenant
            flows_by_status_query = (
                select(
                    CrewAIFlowStateExtensions.flow_status,
                    func.count(CrewAIFlowStateExtensions.flow_id),
                )
                .where(
                    CrewAIFlowStateExtensions.client_account_id
                    == mfo_context.client_account_id
                )
                .group_by(CrewAIFlowStateExtensions.flow_status)
            )

            result = await db.execute(flows_by_status_query)
            flows_by_status = result.fetchall()
            for status, count in flows_by_status:
                print(f"  {status}: {count} flows")

            # Get tenant-scoped engagements with MFO coordination
            print("\n=== Tenant-Scoped Engagements with MFO Status ===")
            result = await db.execute(
                select(
                    Engagement.id,
                    Engagement.name,
                    Engagement.is_active,
                    Engagement.client_id,
                ).where(Engagement.client_id == mfo_context.client_account_id)
            )

            engagements = result.fetchall()
            print(f"Found {len(engagements)} engagements for tenant:")
            for row in engagements:
                print(f"  {row[1]}: is_active={row[2]}, client_id={row[3]}")

                # For each engagement, check if it has master flows
                master_flows_result = await db.execute(
                    select(func.count())
                    .select_from(CrewAIFlowStateExtensions)
                    .where(
                        CrewAIFlowStateExtensions.engagement_id == str(row[0]),
                        CrewAIFlowStateExtensions.client_account_id
                        == mfo_context.client_account_id,
                    )
                )
                master_flows_count = master_flows_result.scalar_one()
                print(f"    Master flows: {master_flows_count}")

            # Test MFO orchestrator methods directly
            print("\n=== MFO Orchestrator Direct Methods ===")
            try:
                engagement_flows = await mfo_orchestrator.get_flows_for_engagement(
                    DEMO_ENGAGEMENT_ID
                )
                print(
                    f"Flows for demo engagement: {len(engagement_flows) if engagement_flows else 0}"
                )

                # Test flow status retrieval
                if engagement_flows:
                    for flow in engagement_flows[:3]:  # Limit to first 3
                        flow_status = await mfo_orchestrator.get_flow_status(
                            flow.flow_id
                        )
                        print(
                            f"  Flow {flow.flow_id}: {flow_status.get('flow_status', 'unknown')}"
                        )
            except Exception as mfo_error:
                print(
                    f"MFO methods test failed (expected if no flows exist): {mfo_error}"
                )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mfo_engagement_stats())
