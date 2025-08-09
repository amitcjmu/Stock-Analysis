#!/usr/bin/env python3
"""
Diagnostic tool for collection flows
Helps identify and resolve stuck collection flows
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import os

# Add the backend directory to the Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.models.collection_flow import CollectionFlow, CollectionFlowStatus

# Database connection
# Try to get from environment or use standard URL
DATABASE_URL = os.getenv("DATABASE_URL", None)
if not DATABASE_URL:
    # Use synchronous psycopg2 for simplicity
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/migration_db"

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

print(f"Using database URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_all_collection_flows(session: AsyncSession):
    """Get all collection flows"""
    result = await session.execute(
        select(CollectionFlow).order_by(CollectionFlow.created_at.desc())
    )
    return result.scalars().all()


async def get_active_flows(session: AsyncSession):
    """Get active collection flows"""
    result = await session.execute(
        select(CollectionFlow)
        .where(
            CollectionFlow.status.notin_([
                CollectionFlowStatus.COMPLETED.value,
                CollectionFlowStatus.FAILED.value,
                CollectionFlowStatus.CANCELLED.value
            ])
        )
        .order_by(CollectionFlow.created_at.desc())
    )
    return result.scalars().all()


async def get_stuck_flows(session: AsyncSession, hours: int = 24):
    """Get flows that appear to be stuck (active but not updated recently)"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    result = await session.execute(
        select(CollectionFlow)
        .where(
            CollectionFlow.status.notin_([
                CollectionFlowStatus.COMPLETED.value,
                CollectionFlowStatus.FAILED.value,
                CollectionFlowStatus.CANCELLED.value
            ]),
            CollectionFlow.updated_at < cutoff_time
        )
        .order_by(CollectionFlow.created_at.desc())
    )
    return result.scalars().all()


async def cancel_flow(session: AsyncSession, flow_id):
    """Cancel a collection flow"""
    await session.execute(
        update(CollectionFlow)
        .where(CollectionFlow.id == flow_id)
        .values(
            status=CollectionFlowStatus.CANCELLED.value,
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
    )
    await session.commit()


def print_flow_details(flow):
    """Print detailed information about a flow"""
    age = datetime.utcnow() - flow.created_at
    last_update = datetime.utcnow() - flow.updated_at

    print(f"\n{'='*60}")
    print(f"Flow ID: {flow.id}")
    print(f"Engagement ID: {flow.engagement_id}")
    print(f"Status: {flow.status}")
    print(f"Current Phase: {flow.current_phase}")
    print(f"Automation Tier: {flow.automation_tier}")
    print(f"Progress: {flow.progress_percentage or 0}%")
    print(f"Created: {flow.created_at} ({age.total_seconds() / 3600:.1f} hours ago)")
    print(f"Last Updated: {flow.updated_at} ({last_update.total_seconds() / 3600:.1f} hours ago)")
    print(f"Completed: {flow.completed_at or 'Not completed'}")


async def main():
    """Main diagnostic function"""
    print("Collection Flow Diagnostic Tool")
    print("==============================\n")

    async with AsyncSessionLocal() as session:
        # Get all flows
        all_flows = await get_all_collection_flows(session)
        print(f"Total collection flows in database: {len(all_flows)}")

        # Get active flows
        active_flows = await get_active_flows(session)
        print(f"Active (non-terminal) flows: {len(active_flows)}")

        # Get stuck flows
        stuck_flows = await get_stuck_flows(session, hours=24)
        print(f"Potentially stuck flows (not updated in 24h): {len(stuck_flows)}")

        # Show status distribution
        status_counts = {}
        for flow in all_flows:
            status = flow.status
            status_counts[status] = status_counts.get(status, 0) + 1

        print("\nStatus Distribution:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")

        # Group active flows by engagement
        engagement_flows = {}
        for flow in active_flows:
            eng_id = str(flow.engagement_id)
            if eng_id not in engagement_flows:
                engagement_flows[eng_id] = []
            engagement_flows[eng_id].append(flow)

        if engagement_flows:
            print(f"\nActive Flows by Engagement ({len(engagement_flows)} engagements):")
            for eng_id, flows in engagement_flows.items():
                print(f"\n  Engagement {eng_id}: {len(flows)} active flow(s)")
                for flow in flows:
                    last_update = datetime.utcnow() - flow.updated_at
                    print(f"    - Flow {flow.id}: {flow.status} (last update: {last_update.total_seconds() / 3600:.1f}h ago)")

        # Show details of stuck flows
        if stuck_flows:
            print("\n" + "="*60)
            print("STUCK FLOWS DETAILS:")
            for flow in stuck_flows:
                print_flow_details(flow)

            # Offer to cancel stuck flows
            print("\n" + "="*60)
            response = input("\nWould you like to cancel these stuck flows? (yes/no): ").lower().strip()
            if response == 'yes':
                for flow in stuck_flows:
                    await cancel_flow(session, flow.id)
                    print(f"Cancelled flow {flow.id}")
                print(f"\nSuccessfully cancelled {len(stuck_flows)} stuck flow(s)")
            else:
                print("\nNo changes made. You can manually cancel flows using:")
                print("UPDATE collection_flow SET status = 'cancelled', completed_at = NOW() WHERE id = 'FLOW_ID';")
        else:
            print("\nNo stuck flows found!")

        # Summary
        print("\n" + "="*60)
        print("SUMMARY:")
        print(f"- Total flows: {len(all_flows)}")
        print(f"- Active flows: {len(active_flows)}")
        print(f"- Completed flows: {status_counts.get(CollectionFlowStatus.COMPLETED.value, 0)}")
        print(f"- Failed flows: {status_counts.get(CollectionFlowStatus.FAILED.value, 0)}")
        print(f"- Cancelled flows: {status_counts.get(CollectionFlowStatus.CANCELLED.value, 0)}")

        if active_flows:
            print("\nTo create a new collection flow, you need to complete or cancel existing active flows.")
            print("The frontend error 'An active collection flow already exists' occurs when there are")
            print("flows in non-terminal states (not completed, failed, or cancelled).")


if __name__ == "__main__":
    asyncio.run(main())
