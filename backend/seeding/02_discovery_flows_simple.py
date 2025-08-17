"""
Seed discovery flows in various states - Simplified version that works with actual schema.
Agent 2 Task 2.3 - Discovery flows seeding
"""

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal  # noqa: E402
from app.models.discovery_flow import DiscoveryFlow  # noqa: E402
from seeding.constants import (  # noqa: E402
    BASE_TIMESTAMP,
    DEMO_CLIENT_ID,
    DEMO_ENGAGEMENT_ID,
    FLOW_IDS,
    FLOWS,
)


async def create_discovery_flows(db: AsyncSession) -> list[DiscoveryFlow]:
    """Create discovery flows in various states."""
    print("Creating discovery flows...")

    created_flows = []

    for i, flow_data in enumerate(FLOWS):
        # Calculate timestamps based on flow state
        created_at = BASE_TIMESTAMP + timedelta(days=i * 7)
        updated_at = created_at + timedelta(hours=flow_data["progress"])

        # Create DiscoveryFlow with actual database fields
        flow = DiscoveryFlow(
            id=flow_data["id"],
            flow_id=flow_data["id"],  # Using same ID for both
            # Multi-tenant isolation
            client_account_id=DEMO_CLIENT_ID,
            engagement_id=DEMO_ENGAGEMENT_ID,
            user_id=str(flow_data["created_by"]),
            # Flow metadata
            flow_name=flow_data["name"],
            status=flow_data["state"],
            progress_percentage=flow_data["progress"] / 100.0,
            # Phase completion tracking
            data_import_completed=flow_data["progress"] >= 20,
            field_mapping_completed=flow_data["progress"] >= 45,
            data_cleansing_completed=flow_data["progress"] >= 60,
            asset_inventory_completed=flow_data["progress"] >= 75,
            dependency_analysis_completed=flow_data["progress"] >= 90,
            tech_debt_assessment_completed=flow_data["progress"] >= 100,
            # Set current phase based on progress
            current_phase=flow_data["current_phase"],
            # Assessment ready only for completed flows
            assessment_ready=flow_data["state"] == "complete",
            # Flow state as simple JSON
            flow_state={
                "initialized": True,
                "current_phase": flow_data["current_phase"],
                "progress": flow_data["progress"],
                "state": flow_data["state"],
            },
            # Error handling for failed flow
            error_message=flow_data.get("error_message"),
            # Timestamps
            created_at=created_at,
            updated_at=updated_at,
        )

        # Set completion time for completed flow
        if flow_data["state"] == "complete":
            flow.completed_at = updated_at

        db.add(flow)
        created_flows.append(flow)

        print(
            f"✓ Created flow: {flow_data['name']} (state: {flow_data['state']}, progress: {flow_data['progress']}%)"
        )

    await db.commit()
    return created_flows


async def main():
    """Main seeding function."""
    print("\n=== Seeding Discovery Flows ===\n")

    async with AsyncSessionLocal() as db:
        try:
            # Check if already seeded
            existing_flow = await db.get(DiscoveryFlow, FLOW_IDS["complete"])
            if existing_flow:
                print("⚠️  Discovery flows already seeded. Skipping...")
                return

            # Create flows
            flows = await create_discovery_flows(db)

            print(f"\n✅ Successfully seeded {len(flows)} discovery flows:")
            for flow in flows:
                print(
                    f"   - {flow.flow_name} ({flow.status}, {flow.progress_percentage * 100:.0f}%)"
                )

        except Exception as e:
            print(f"\n❌ Error seeding discovery flows: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
