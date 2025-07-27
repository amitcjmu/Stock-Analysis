"""
Fix flow navigation by ensuring flows redirect to the correct phase based on their actual state
"""

import asyncio

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.models.discovery_flow import DiscoveryFlow


async def analyze_and_fix_flow_navigation():
    async with AsyncSessionLocal() as db:
        # Get all active flows
        flows_result = await db.execute(
            select(DiscoveryFlow, CrewAIFlowStateExtensions)
            .join(
                CrewAIFlowStateExtensions,
                DiscoveryFlow.flow_id == CrewAIFlowStateExtensions.flow_id,
            )
            .where(DiscoveryFlow.status.in_(["active", "paused", "processing"]))
        )

        flows = flows_result.all()
        print(f"Found {len(flows)} active flows to analyze")

        for discovery_flow, crewai_state in flows:
            print(f"\n{'='*60}")
            print(f"Flow ID: {discovery_flow.flow_id}")
            print(f"Current Phase: {discovery_flow.current_phase}")
            print(f"Field Mapping Completed: {discovery_flow.field_mapping_completed}")
            # Check flow persistence data for awaiting_user_approval
            persistence_data = crewai_state.flow_persistence_data or {}
            awaiting_approval = persistence_data.get("awaiting_user_approval", False)
            print(f"Awaiting User Approval: {awaiting_approval}")

            # Check flow metadata for field mappings
            flow_metadata = crewai_state.flow_metadata or {}
            field_mappings = flow_metadata.get("field_mappings", {})
            has_field_mappings = bool(field_mappings.get("mappings"))
            print(f"Has Field Mappings: {has_field_mappings}")

            # Determine correct phase
            correct_phase = None
            needs_correction = False

            # If field mapping is not completed and awaiting approval, should be in field_mapping phase
            if not discovery_flow.field_mapping_completed and awaiting_approval:
                if discovery_flow.current_phase != "field_mapping":
                    correct_phase = "field_mapping"
                    needs_correction = True
                    print(
                        f"⚠️  ISSUE: Flow is awaiting field mapping approval but phase is {discovery_flow.current_phase}"
                    )

            # If in data_cleansing but no field mappings completed
            elif (
                discovery_flow.current_phase == "data_cleansing"
                and not discovery_flow.field_mapping_completed
            ):
                correct_phase = "field_mapping"
                needs_correction = True
                print(
                    "⚠️  ISSUE: Flow is in data_cleansing but field mapping not completed"
                )

            if needs_correction and correct_phase:
                print(
                    f"✅ FIX: Updating phase from {discovery_flow.current_phase} to {correct_phase}"
                )

                # Update the phase
                await db.execute(
                    update(DiscoveryFlow)
                    .where(DiscoveryFlow.flow_id == discovery_flow.flow_id)
                    .values(
                        {
                            "current_phase": correct_phase,
                            "progress_percentage": 25.0,  # Field mapping phase progress
                        }
                    )
                )

                # Also update CrewAI persistence data to ensure consistency
                persistence_data = crewai_state.flow_persistence_data or {}
                persistence_data["current_phase"] = correct_phase

                await db.execute(
                    update(CrewAIFlowStateExtensions)
                    .where(CrewAIFlowStateExtensions.flow_id == discovery_flow.flow_id)
                    .values({"flow_persistence_data": persistence_data})
                )

                await db.commit()
                print(
                    f"✅ Flow {discovery_flow.flow_id} phase corrected to {correct_phase}"
                )
            else:
                print("✅ Flow phase is correct")


if __name__ == "__main__":
    asyncio.run(analyze_and_fix_flow_navigation())
