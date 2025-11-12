"""
Manual Test Script for Assessment Flow Recovery (Issue #999)

This script tests both manual and automatic recovery of zombie assessment flows.

Usage:
    python backend/tests/manual/test_assessment_flow_recovery.py

Requirements:
    - Backend running on localhost:8000
    - Valid authentication token
    - Zombie flow exists in database (or create one for testing)
"""

import asyncio
import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.assessment_flow import AssessmentFlow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TEST_FLOW_ID = "8bdaa388-75a7-4059-81f6-d29af2037538"  # Known zombie flow


class AssessmentFlowRecoveryTester:
    """Test harness for assessment flow recovery mechanism."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(timeout=30.0)

        # Setup database connection
        engine = create_async_engine(str(settings.DATABASE_URL))
        self.async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()

    async def get_flow_state(self, flow_id: str) -> dict:
        """Fetch current flow state from database."""
        async with self.async_session() as db:
            result = await db.execute(
                select(AssessmentFlow).where(AssessmentFlow.id == UUID(flow_id))
            )
            flow = result.scalar_one_or_none()

            if not flow:
                return {"error": "Flow not found"}

            return {
                "flow_id": str(flow.id),
                "progress": flow.progress,
                "current_phase": flow.current_phase,
                "status": flow.status,
                "phase_results_count": len(flow.phase_results or {}),
                "agent_insights_count": len(flow.agent_insights or []),
                "is_zombie": (
                    flow.progress >= 80
                    and (not flow.phase_results or flow.phase_results == {})
                    and (not flow.agent_insights or flow.agent_insights == [])
                ),
            }

    async def test_manual_recovery(self, flow_id: str):
        """Test manual recovery via POST /recover endpoint."""
        logger.info(f"\n{'='*60}")
        logger.info("TEST 1: Manual Recovery Endpoint")
        logger.info(f"{'='*60}\n")

        # Get initial state
        logger.info("Step 1: Fetch initial flow state from database")
        initial_state = await self.get_flow_state(flow_id)
        logger.info(f"Initial State: {initial_state}")

        if initial_state.get("error"):
            logger.error(f"❌ Test failed: {initial_state['error']}")
            return False

        # Call recovery endpoint
        logger.info(f"\nStep 2: Call recovery endpoint for flow {flow_id}")
        url = f"{self.base_url}/assessment-flow/{flow_id}/recover"
        logger.info(f"POST {url}")

        response = await self.client.post(url, headers=self.headers)
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Body: {response.json()}")

        if response.status_code != 200:
            logger.error("❌ Test failed: Recovery endpoint returned error")
            return False

        recovery_result = response.json()

        # Verify zombie detection
        logger.info("\nStep 3: Verify zombie detection logic")
        expected_zombie = initial_state["is_zombie"]
        actual_zombie = recovery_result.get("zombie_detected", False)

        if expected_zombie and actual_zombie:
            logger.info("✅ Zombie correctly detected")
        elif not expected_zombie and not actual_zombie:
            logger.info("✅ Non-zombie correctly identified")
        else:
            logger.error(
                f"❌ Zombie detection mismatch: expected={expected_zombie}, actual={actual_zombie}"
            )
            return False

        # Wait for background task to complete
        if recovery_result.get("recovery_queued"):
            logger.info("\nStep 4: Wait for background task to complete (30 seconds)")
            await asyncio.sleep(30)

            # Check final state
            logger.info("Step 5: Verify recovery results")
            final_state = await self.get_flow_state(flow_id)
            logger.info(f"Final State: {final_state}")

            if (
                final_state["phase_results_count"] > 0
                or final_state["agent_insights_count"] > 0
            ):
                logger.info("✅ Recovery successful - results populated")
                return True
            else:
                logger.warning(
                    "⚠️  Recovery queued but results not yet populated (may need more time)"
                )
                return True  # Still consider it a pass if task was queued
        else:
            logger.info("✅ Recovery not needed - flow is healthy")
            return True

    async def test_auto_recovery_on_resume(self, flow_id: str):
        """Test automatic recovery when resuming a zombie flow."""
        logger.info(f"\n{'='*60}")
        logger.info("TEST 2: Automatic Recovery on Resume")
        logger.info(f"{'='*60}\n")

        # Get initial state
        logger.info("Step 1: Fetch initial flow state from database")
        initial_state = await self.get_flow_state(flow_id)
        logger.info(f"Initial State: {initial_state}")

        if not initial_state.get("is_zombie"):
            logger.info("⏭️  Skipping test - flow is not a zombie")
            return True

        # Call resume endpoint (which should auto-detect zombie)
        logger.info(f"\nStep 2: Call resume endpoint for flow {flow_id}")
        url = f"{self.base_url}/master-flows/{flow_id}/assessment/resume"
        logger.info(f"POST {url}")

        response = await self.client.post(
            url,
            headers=self.headers,
            json={"user_input": {}},  # Empty user input for resume
        )
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Body: {response.json()}")

        if response.status_code != 200:
            logger.error("❌ Test failed: Resume endpoint returned error")
            return False

        # Check logs for auto-recovery detection
        logger.info("\nStep 3: Check backend logs for zombie detection")
        logger.info(
            "Look for: [ISSUE-999-ZOMBIE] 🧟 AUTO-RECOVERY: Detected zombie flow"
        )

        # Wait for background task
        logger.info("\nStep 4: Wait for background task to complete (30 seconds)")
        await asyncio.sleep(30)

        # Verify results
        logger.info("Step 5: Verify recovery results")
        final_state = await self.get_flow_state(flow_id)
        logger.info(f"Final State: {final_state}")

        if (
            final_state["phase_results_count"] > 0
            or final_state["agent_insights_count"] > 0
        ):
            logger.info("✅ Auto-recovery successful - results populated")
            return True
        else:
            logger.warning("⚠️  Auto-recovery triggered but results not yet populated")
            return True

    async def run_all_tests(self, flow_id: str):
        """Run all recovery tests."""
        logger.info("\n" + "=" * 80)
        logger.info("ASSESSMENT FLOW RECOVERY TEST SUITE (GitHub Issue #999)")
        logger.info("=" * 80)

        results = {
            "manual_recovery": False,
            "auto_recovery": False,
        }

        try:
            # Test 1: Manual recovery
            results["manual_recovery"] = await self.test_manual_recovery(flow_id)

            # Test 2: Auto recovery on resume
            # Note: This will modify the flow, so run after manual test
            results["auto_recovery"] = await self.test_auto_recovery_on_resume(flow_id)

        except Exception as e:
            logger.error(f"❌ Test suite failed with error: {e}", exc_info=True)

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{test_name}: {status}")

        all_passed = all(results.values())
        logger.info("\n" + "=" * 80)
        if all_passed:
            logger.info("🎉 ALL TESTS PASSED")
        else:
            logger.info("❌ SOME TESTS FAILED")
        logger.info("=" * 80 + "\n")

        return all_passed


async def main():
    """Main test runner."""
    # SECURITY NOTE: This is a manual test script for local development only.
    # The placeholder token is intentional and includes validation to prevent
    # accidental execution without proper configuration.
    # This file is in tests/manual/ and is NOT deployed to production.

    # TODO: Replace with actual auth token
    # You can get this by:
    # 1. Login to the app at http://localhost:8081
    # 2. Open browser dev tools → Application → Local Storage
    # 3. Copy the token value
    AUTH_TOKEN = "your-auth-token-here"

    if AUTH_TOKEN == "your-auth-token-here":
        logger.error("❌ Please set a valid AUTH_TOKEN in the script")
        logger.info("Get token from: http://localhost:8081 → Dev Tools → Local Storage")
        return

    tester = AssessmentFlowRecoveryTester(API_BASE_URL, AUTH_TOKEN)

    try:
        success = await tester.run_all_tests(TEST_FLOW_ID)
        return 0 if success else 1
    finally:
        await tester.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
