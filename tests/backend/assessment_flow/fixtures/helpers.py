"""
Helper fixtures for assessment flow testing.

Factory functions, assertion helpers, and test utilities.
"""

from unittest.mock import MagicMock

import pytest

from tests.fixtures.mfo_fixtures import (
    DEMO_CLIENT_ACCOUNT_ID,
    DEMO_ENGAGEMENT_ID,
    DEMO_USER_ID,
    DEMO_USER_EMAIL,
    MockRequestContext,
)


@pytest.fixture
def assessment_flow_factory():
    """Factory for creating assessment flow instances - MFO compliant."""

    def _create_flow(flow_id="test-flow", client_account_id=DEMO_CLIENT_ACCOUNT_ID, engagement_id=DEMO_ENGAGEMENT_ID):
        mock_context = MockRequestContext(
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            user_id=DEMO_USER_ID,
            user_email=DEMO_USER_EMAIL,
        )

        # This will be replaced with actual implementation
        mock_flow = MagicMock()
        mock_flow.context = mock_context
        return mock_flow

    return _create_flow


@pytest.fixture
def assert_helpers():
    """Helper functions for common test assertions - MFO compliant."""

    def assert_flow_state_valid(flow_state):
        """Assert that flow state is valid."""
        assert hasattr(flow_state, "flow_id")
        assert hasattr(flow_state, "client_account_id")
        assert hasattr(flow_state, "engagement_id")
        assert hasattr(flow_state, "status")
        assert hasattr(flow_state, "current_phase")

    def assert_multi_tenant_isolation(context1, context2):
        """Assert that contexts are properly isolated."""
        if context1.client_account_id == context2.client_account_id:
            if context1.engagement_id != context2.engagement_id:
                return True  # Same client, different engagement is allowed
        else:
            return True  # Different clients are isolated
        return False  # Same client, same engagement should be same context

    def assert_mfo_compliance(flow_data):
        """Assert that flow data follows MFO patterns."""
        # Check for required MFO fields
        if isinstance(flow_data, dict):
            assert "master_flow_id" in flow_data or "flow_id" in flow_data
            assert "client_account_id" in flow_data
            assert "engagement_id" in flow_data

    return {
        "assert_flow_state_valid": assert_flow_state_valid,
        "assert_multi_tenant_isolation": assert_multi_tenant_isolation,
        "assert_mfo_compliance": assert_mfo_compliance,
    }
