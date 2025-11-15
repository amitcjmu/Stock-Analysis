#!/usr/bin/env python3
"""
Test script for PhaseExecutionLockManager integration

Verifies that the lock manager can be imported and used correctly
in the Docker environment.
"""

import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_lock_manager():
    """Test basic lock manager functionality."""
    from app.services.flow_orchestration.phase_execution_lock_manager import (
        phase_lock_manager,
    )

    print("✅ Successfully imported phase_lock_manager")
    print(f"   Type: {type(phase_lock_manager)}")
    print(f"   Instance: {phase_lock_manager}")

    # Test lock acquisition
    flow_id = "test-flow-123"
    phase = "readiness"

    print(f"\n🔒 Testing lock acquisition for {flow_id}:{phase}")

    # First acquisition should succeed
    result1 = await phase_lock_manager.try_acquire_lock(flow_id, phase)
    print(f"   First acquisition: {result1} (expected: True)")
    assert result1 is True, "First acquisition should succeed"

    # Second acquisition should fail (duplicate)
    result2 = await phase_lock_manager.try_acquire_lock(flow_id, phase)
    print(f"   Second acquisition: {result2} (expected: False)")
    assert result2 is False, "Second acquisition should fail (duplicate)"

    # Release lock
    print(f"\n🔓 Releasing lock for {flow_id}:{phase}")
    phase_lock_manager.release_lock(flow_id, phase)
    print("   Lock released")

    # Third acquisition should succeed (lock released)
    result3 = await phase_lock_manager.try_acquire_lock(flow_id, phase)
    print(f"   Third acquisition: {result3} (expected: True)")
    assert result3 is True, "Third acquisition should succeed after release"

    # Clean up
    phase_lock_manager.release_lock(flow_id, phase)

    print("\n✅ All tests passed!")
    print("   Lock manager is working correctly in Docker environment")


if __name__ == "__main__":
    asyncio.run(test_lock_manager())
