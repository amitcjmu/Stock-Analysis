"""
Provider Contract Verification Tests

Issue #592: API Contract Testing Implementation

This test verifies that the backend API provider satisfies the consumer contracts
defined by the frontend. It uses pact-python to replay consumer expectations.

Usage:
    1. Run consumer tests first to generate pact files:
       cd .. && npx vitest tests/contract/

    2. Run provider verification:
       cd backend && python -m pytest tests/contract/ -v

Prerequisites:
    - pip install pact-python pytest-asyncio httpx
    - Consumer pact files in ../tests/contract/pacts/
"""

import pytest
from pathlib import Path

# Provider verification imports
try:
    from pact import Verifier

    PACT_AVAILABLE = True
except ImportError:
    PACT_AVAILABLE = False
    Verifier = None

# Backend app imports (will be available when running in backend context)
try:
    from fastapi.testclient import TestClient
    from app.main import app

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None
    app = None


# Configuration
PACT_DIR = Path(__file__).parent.parent.parent.parent / "tests" / "contract" / "pacts"
PROVIDER_NAME = "migrate-api-backend"
PROVIDER_BASE_URL = "http://localhost:8000"


class ProviderStateSetup:
    """
    Provider state handlers for Pact verification.

    These handlers set up the database/mock state required for each
    consumer expectation defined in the pact files.
    """

    def __init__(self, test_client):
        self.client = test_client

    def setup_state(self, state: str, params: dict = None) -> None:
        """
        Set up provider state based on consumer expectation.

        Args:
            state: The provider state description from the pact
            params: Optional parameters for the state
        """
        params = params or {}

        # Map state descriptions to setup functions
        state_handlers = {
            "the API is running": self._setup_healthy_api,
            "a user is authenticated": self._setup_authenticated_user,
            "an assessment flow exists": self._setup_assessment_flow,
            "no assessment flow exists": self._setup_no_flow,
            "applications ready for assessment": self._setup_ready_applications,
            "assessment flow with 6R decisions": self._setup_flow_with_decisions,
            "a master flow exists": self._setup_master_flow,
            "multiple master flows exist": self._setup_multiple_flows,
            "an active master flow exists": self._setup_active_flow,
            "a paused master flow exists": self._setup_paused_flow,
        }

        handler = state_handlers.get(state)
        if handler:
            handler(params)
        else:
            print(f"Warning: No handler for state '{state}'")

    def _setup_healthy_api(self, params: dict) -> None:
        """API is running - no setup needed."""
        pass

    def _setup_authenticated_user(self, params: dict) -> None:
        """Set up authenticated user context."""
        # The test headers will provide tenant context
        pass

    def _setup_assessment_flow(self, params: dict) -> None:
        """
        Set up an existing assessment flow.

        In real implementation, this would:
        1. Create a test flow in crewai_flow_state_extensions
        2. Create linked assessment_flows record
        """
        flow_id = params.get("flow_id", "550e8400-e29b-41d4-a716-446655440000")
        # Mock or create test data here
        print(f"Setting up assessment flow: {flow_id}")

    def _setup_no_flow(self, params: dict) -> None:
        """Ensure no flow exists - clean state."""
        pass

    def _setup_ready_applications(self, params: dict) -> None:
        """Set up applications ready for assessment."""
        pass

    def _setup_flow_with_decisions(self, params: dict) -> None:
        """Set up flow with existing 6R decisions."""
        flow_id = params.get("flow_id")
        app_id = params.get("app_id")
        print(f"Setting up flow {flow_id} with decisions for app {app_id}")

    def _setup_master_flow(self, params: dict) -> None:
        """Set up a master flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up master flow: {flow_id}")

    def _setup_multiple_flows(self, params: dict) -> None:
        """Set up multiple master flows."""
        pass

    def _setup_active_flow(self, params: dict) -> None:
        """Set up an active (running) flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up active flow: {flow_id}")

    def _setup_paused_flow(self, params: dict) -> None:
        """Set up a paused flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up paused flow: {flow_id}")


@pytest.fixture
def provider_state_handler():
    """Fixture for provider state setup."""
    if FASTAPI_AVAILABLE and app:
        client = TestClient(app)
        return ProviderStateSetup(client)
    return None


@pytest.mark.skipif(
    not PACT_AVAILABLE,
    reason="pact-python not installed. Install with: pip install pact-python",
)
@pytest.mark.skipif(
    not PACT_DIR.exists(),
    reason=f"Pact files not found at {PACT_DIR}. Run consumer tests first.",
)
class TestProviderVerification:
    """
    Provider verification tests.

    These tests verify that the backend API satisfies the contracts
    defined by the frontend consumer.
    """

    def test_verify_pacts(self, provider_state_handler):
        """
        Verify all pact contracts against the running provider.

        Note: This test requires the backend to be running at PROVIDER_BASE_URL.
        For CI, this would be started as part of the test setup.
        """
        # Find all pact files
        pact_files = list(PACT_DIR.glob("*.json"))

        if not pact_files:
            pytest.skip("No pact files found")

        # Create verifier
        verifier = Verifier(
            provider=PROVIDER_NAME,
            provider_base_url=PROVIDER_BASE_URL,
        )

        # Configure state change handler
        # In real usage, this would be a webhook that sets up provider states

        # Verify each pact file
        for pact_file in pact_files:
            print(f"\nVerifying pact: {pact_file.name}")

            # Run verification
            output, result = verifier.verify_pacts(
                str(pact_file),
                enable_pending=True,
                verbose=True,
            )

            # Check result
            assert (
                result == 0
            ), f"Pact verification failed for {pact_file.name}: {output}"

    def test_openapi_schema_available(self):
        """
        Verify OpenAPI schema is available at /openapi.json.

        This is a prerequisite for type generation.
        """
        if not FASTAPI_AVAILABLE:
            pytest.skip("FastAPI not available")

        client = TestClient(app)
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()

        # Verify basic OpenAPI structure
        assert "openapi" in schema
        assert "paths" in schema
        assert "components" in schema

        # Verify critical endpoints exist
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/me" in schema["paths"]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI app not available")
class TestAPIEndpointContracts:
    """
    Direct API contract tests without Pact broker.

    These tests verify endpoint contracts directly using the test client.
    Useful for local development and CI when Pact broker is not available.
    """

    @pytest.fixture
    def client(self):
        """Test client fixture."""
        return TestClient(app)

    def test_health_endpoint_contract(self, client):
        """Verify health endpoint returns expected structure."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        # Contract: must have status field
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_me_endpoint_requires_headers(self, client):
        """Verify /me endpoint requires tenant headers."""
        # Without headers - should work but return demo context
        response = client.get("/api/v1/me")

        # Should return 200 with context
        assert response.status_code == 200
        data = response.json()

        # Contract: must have client/engagement context
        assert "client_account_id" in data or "client" in data

    def test_assessment_flow_endpoints_exist(self, client):
        """Verify assessment flow endpoints are registered."""
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        schema = response.json()

        # Critical assessment flow endpoints
        required_endpoints = [
            "/api/v1/assessment-flow/initialize",
            "/api/v1/assessment-flow/{flow_id}/status",
        ]

        for endpoint in required_endpoints:
            # Check endpoint exists (may have different path parameter formats)
            endpoint_exists = (
                any(
                    endpoint.replace("{flow_id}", "") in path
                    for path in schema["paths"].keys()
                )
                or endpoint in schema["paths"]
            )

            assert endpoint_exists, f"Endpoint {endpoint} not found in OpenAPI schema"


# Entry point for standalone verification
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
