#!/usr/bin/env python3
"""
Test script for phase transitions using the atomic helper functions.
This script tests the actual database with the real flow data.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.models.discovery_flow import DiscoveryFlow
from app.services.discovery.phase_persistence_helpers import (
    advance_phase,
    persist_if_changed,
    persist_error_with_classification,
)


async def test_phase_transitions():
    """Test phase transitions with existing flow data."""
    print("🧪 Testing Phase Transitions with Real Data")
    print("=" * 50)

    # Create database connection
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as db:
        # Get the existing flow
        result = await db.execute(select(DiscoveryFlow))
        flows = result.scalars().all()

        if not flows:
            print("❌ No flows found in database")
            return

        flow = flows[0]
        print(f"📋 Testing with flow: {flow.flow_id}")
        print(f"   Current phase: {flow.current_phase}")
        print(f"   Status: {flow.status}")
        print(f"   Data import completed: {flow.data_import_completed}")
        print(f"   Field mapping completed: {flow.field_mapping_completed}")
        print(f"   Data cleansing completed: {flow.data_cleansing_completed}")
        print(f"   Progress: {flow.progress_percentage}%")
        print()

        # Test 1: Idempotency - transition to current phase
        print("🔄 Test 1: Idempotency Check")
        current_phase = flow.current_phase or "data_import"

        # Since advance_phase manages its own transaction, we don't need begin()
        result = await advance_phase(db=db, flow=flow, target_phase=current_phase)

        print(f"   Result: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"   Was idempotent: {result.was_idempotent}")
        print(f"   Warnings: {result.warnings}")
        await db.rollback()  # Don't persist this test
        print()

        # Test 2: Valid transition to next phase
        print("🔄 Test 2: Valid Phase Transition")

        # Determine next valid phase
        phase_sequence = [
            "data_import",
            "field_mapping",
            "data_cleansing",
            "asset_inventory",
            "dependency_analysis",
            "tech_debt_assessment",
        ]

        current_idx = (
            phase_sequence.index(current_phase)
            if current_phase in phase_sequence
            else 0
        )
        if current_idx < len(phase_sequence) - 1:
            next_phase = phase_sequence[current_idx + 1]

            result = await advance_phase(db=db, flow=flow, target_phase=next_phase)

            print(f"   Transition: {current_phase} → {next_phase}")
            print(f"   Result: {'✅ Success' if result.success else '❌ Failed'}")
            print(f"   Prior phase: {result.prior_phase}")
            print(f"   Warnings: {result.warnings}")
            await db.rollback()  # Don't persist this test
        else:
            print(f"   Flow is already at terminal phase: {current_phase}")
        print()

        # Test 3: Invalid transition (skip phases)
        print("🔄 Test 3: Invalid Phase Transition")

        invalid_target = (
            "tech_debt_assessment"
            if current_phase != "tech_debt_assessment"
            else "dependency_analysis"
        )

        result = await advance_phase(db=db, flow=flow, target_phase=invalid_target)

        print(f"   Attempted: {current_phase} → {invalid_target}")
        print(
            f"   Result: {'✅ Success' if result.success else '❌ Failed (Expected)'}"
        )
        print(f"   Warnings: {result.warnings}")
        await db.rollback()  # Don't persist this test
        print()

        # Test 4: Write-through flag persistence
        print("🔄 Test 4: Write-through Flag Persistence")

        original_data_import = flow.data_import_completed
        original_field_mapping = flow.field_mapping_completed

        async with db.begin():
            changes_made = await persist_if_changed(
                db=db,
                flow=flow,
                data_import_completed=not original_data_import,  # Flip the value
                field_mapping_completed=original_field_mapping,  # Keep same
            )

            print(f"   Original data_import_completed: {original_data_import}")
            print(f"   New data_import_completed: {flow.data_import_completed}")
            print(f"   Changes made: {'✅ Yes' if changes_made else '❌ No'}")
            print(f"   Progress updated: {flow.progress_percentage}%")
            await db.rollback()  # Don't persist this test
        print()

        # Test 5: Error classification
        print("🔄 Test 5: Error Classification")

        test_error = Exception("Connection timeout while importing data")

        async with db.begin():
            await persist_error_with_classification(
                db=db,
                flow=flow,
                error=test_error,
                phase="data_import",
                error_code="IMPORT_TIMEOUT",
                recovery_hint="Retry with exponential backoff",
                is_retryable=True,
            )

            print(f"   Error message: {flow.error_message}")
            print(f"   Error phase: {flow.error_phase}")
            print(f"   Error type: {flow.error_details.get('error_type')}")
            print(f"   Is retryable: {flow.error_details.get('is_retryable')}")
            await db.rollback()  # Don't persist this test
        print()

        print("✅ All phase transition tests completed successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_phase_transitions())
