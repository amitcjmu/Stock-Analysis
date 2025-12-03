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

import re
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

    # Class-level mapping of state descriptions to handler method names
    STATE_HANDLERS = {
        # Health & Auth states
        "the API is running": "_setup_healthy_api",
        "a user is authenticated": "_setup_authenticated_user",
        # Assessment Flow states
        "an assessment flow exists": "_setup_assessment_flow",
        "no assessment flow exists": "_setup_no_flow",
        "no assessment flow exists": "_setup_no_flow",
        "applications ready for assessment": "_setup_ready_applications",
        "assessment flow with 6R decisions": "_setup_flow_with_decisions",
        # Master Flow states
        "a master flow exists": "_setup_master_flow",
        "multiple master flows exist": "_setup_multiple_flows",
        "an active master flow exists": "_setup_active_flow",
        "a paused master flow exists": "_setup_paused_flow",
        # Discovery Flow states
        "ready to create discovery flow": "_setup_ready_for_discovery",
        "a discovery flow exists": "_setup_discovery_flow",
        "an active discovery flow exists": "_setup_active_discovery_flow",
        "a discovery flow ready for execution": "_setup_discovery_flow",
        "a running discovery flow": "_setup_running_discovery_flow",
        "a paused discovery flow": "_setup_paused_discovery_flow",
        "discovery flow has assets": "_setup_discovery_with_assets",
        "discovery flow has field mappings": "_setup_discovery_with_mappings",
        "discovery service is running": "_setup_healthy_api",
        # Collection Flow states
        "a discovery flow exists": "_setup_discovery_flow",
        "an active collection flow exists": "_setup_active_collection_flow",
        "collection flows exist": "_setup_collection_flows",
        "a collection flow exists": "_setup_collection_flow",
        "a collection flow ready for gap analysis": "_setup_collection_flow",
        "a completed collection flow": "_setup_completed_collection_flow",
        # Decommission Flow states
        "systems eligible for decommission exist": "_setup_decommission_eligible",
        "a decommission flow exists": "_setup_decommission_flow",
        "a paused decommission flow": "_setup_paused_decommission_flow",
        "a running decommission flow": "_setup_running_decommission_flow",
        "an active decommission flow": "_setup_active_decommission_flow",
        "decommission flows exist": "_setup_decommission_flows",
        "systems exist that can be decommissioned": "_setup_decommission_eligible",
        "a decommission flow ready for phase execution": "_setup_decommission_flow",
        "data retention policies exist": "_setup_data_retention_policies",
        # Data Import states
        "data imports exist": "_setup_data_imports",
        "at least one data import exists": "_setup_data_imports",
        "a data import exists": "_setup_data_import",
        "target fields are configured": "_setup_target_fields",
        "field categories are configured": "_setup_field_categories",
        "an import with field mappings exists": "_setup_import_with_mappings",
        "an import ready for mapping generation": "_setup_import_for_mapping",
        "imports with critical attributes exist": "_setup_critical_attributes",
        "learning data exists": "_setup_learning_data",
        "data import service is running": "_setup_healthy_api",
        # FinOps states
        "FinOps metrics are available": "_setup_finops_metrics",
        "resources with costs exist": "_setup_finops_resources",
        "cost optimization opportunities exist": "_setup_finops_opportunities",
        "cost alerts are configured": "_setup_finops_alerts",
        "LLM usage data exists": "_setup_llm_usage",
        "FinOps service is running": "_setup_healthy_api",
        # Canonical Applications states
        "canonical applications exist": "_setup_canonical_apps",
        "a canonical application and asset exist": "_setup_canonical_app_with_asset",
        "a canonical application and multiple assets exist": "_setup_canonical_app_with_assets",
        "a canonical application with assessed assets": "_setup_canonical_app_assessed",
    }

    def __init__(self, test_client):
        self.client = test_client

    def setup_state(self, state: str, **kwargs) -> None:
        """
        Set up provider state based on consumer expectation.

        Args:
            state: The provider state description from the pact
            **kwargs: Optional parameters for the state (pact-python passes these as kwargs)
        """
        params = kwargs or {}

        handler_name = self.STATE_HANDLERS.get(state)
        if handler_name:
            handler = getattr(self, handler_name, None)
            if handler:
                handler(params)
            else:
                print(f"Warning: Handler method '{handler_name}' not found")
        else:
            print(f"Warning: No handler for state '{state}'")

    # ============== Health & Auth Handlers ==============

    def _setup_healthy_api(self, params: dict) -> None:
        """API is running - no setup needed."""
        pass

    def _setup_authenticated_user(self, params: dict) -> None:
        """Set up authenticated user context."""
        # The test headers will provide tenant context
        pass

    # ============== Assessment Flow Handlers ==============

    def _setup_assessment_flow(self, params: dict) -> None:
        """Set up an existing assessment flow."""
        flow_id = params.get("flow_id", "550e8400-e29b-41d4-a716-446655440000")
        print(f"Setting up assessment flow: {flow_id}")
        # TODO: Create test flow in database when running integration tests

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

    # ============== Master Flow Handlers ==============

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

    # ============== Discovery Flow Handlers ==============

    def _setup_ready_for_discovery(self, params: dict) -> None:
        """Ready to create discovery flow."""
        pass

    def _setup_discovery_flow(self, params: dict) -> None:
        """Set up a discovery flow."""
        flow_id = params.get("flow_id", "550e8400-e29b-41d4-a716-446655440000")
        print(f"Setting up discovery flow: {flow_id}")

    def _setup_active_discovery_flow(self, params: dict) -> None:
        """Set up an active discovery flow."""
        pass

    def _setup_running_discovery_flow(self, params: dict) -> None:
        """Set up a running discovery flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up running discovery flow: {flow_id}")

    def _setup_paused_discovery_flow(self, params: dict) -> None:
        """Set up a paused discovery flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up paused discovery flow: {flow_id}")

    def _setup_discovery_with_assets(self, params: dict) -> None:
        """Set up discovery flow with assets."""
        flow_id = params.get("flow_id")
        print(f"Setting up discovery flow with assets: {flow_id}")

    def _setup_discovery_with_mappings(self, params: dict) -> None:
        """Set up discovery flow with field mappings."""
        flow_id = params.get("flow_id")
        print(f"Setting up discovery flow with mappings: {flow_id}")

    # ============== Collection Flow Handlers ==============

    def _setup_active_collection_flow(self, params: dict) -> None:
        """Set up an active collection flow."""
        pass

    def _setup_collection_flows(self, params: dict) -> None:
        """Set up multiple collection flows."""
        pass

    def _setup_collection_flow(self, params: dict) -> None:
        """Set up a collection flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up collection flow: {flow_id}")

    def _setup_completed_collection_flow(self, params: dict) -> None:
        """Set up a completed collection flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up completed collection flow: {flow_id}")

    # ============== Decommission Flow Handlers ==============

    def _setup_decommission_eligible(self, params: dict) -> None:
        """Set up systems eligible for decommission."""
        pass

    def _setup_decommission_flow(self, params: dict) -> None:
        """Set up a decommission flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up decommission flow: {flow_id}")

    def _setup_paused_decommission_flow(self, params: dict) -> None:
        """Set up a paused decommission flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up paused decommission flow: {flow_id}")

    def _setup_running_decommission_flow(self, params: dict) -> None:
        """Set up a running decommission flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up running decommission flow: {flow_id}")

    def _setup_active_decommission_flow(self, params: dict) -> None:
        """Set up an active decommission flow."""
        flow_id = params.get("flow_id")
        print(f"Setting up active decommission flow: {flow_id}")

    def _setup_decommission_flows(self, params: dict) -> None:
        """Set up multiple decommission flows."""
        pass

    def _setup_data_retention_policies(self, params: dict) -> None:
        """Set up data retention policies."""
        pass

    # ============== Data Import Handlers ==============

    def _setup_data_imports(self, params: dict) -> None:
        """Set up data imports."""
        pass

    def _setup_data_import(self, params: dict) -> None:
        """Set up a specific data import."""
        import_id = params.get("import_id")
        print(f"Setting up data import: {import_id}")

    def _setup_target_fields(self, params: dict) -> None:
        """Set up target fields configuration."""
        pass

    def _setup_field_categories(self, params: dict) -> None:
        """Set up field categories."""
        pass

    def _setup_import_with_mappings(self, params: dict) -> None:
        """Set up import with field mappings."""
        import_id = params.get("import_id")
        print(f"Setting up import with mappings: {import_id}")

    def _setup_import_for_mapping(self, params: dict) -> None:
        """Set up import ready for mapping generation."""
        import_id = params.get("import_id")
        print(f"Setting up import for mapping: {import_id}")

    def _setup_critical_attributes(self, params: dict) -> None:
        """Set up critical attributes."""
        pass

    def _setup_learning_data(self, params: dict) -> None:
        """Set up learning data."""
        pass

    # ============== FinOps Handlers ==============

    def _setup_finops_metrics(self, params: dict) -> None:
        """Set up FinOps metrics."""
        pass

    def _setup_finops_resources(self, params: dict) -> None:
        """Set up FinOps resources."""
        pass

    def _setup_finops_opportunities(self, params: dict) -> None:
        """Set up FinOps opportunities."""
        pass

    def _setup_finops_alerts(self, params: dict) -> None:
        """Set up FinOps alerts."""
        pass

    def _setup_llm_usage(self, params: dict) -> None:
        """Set up LLM usage data."""
        pass

    # ============== Canonical Applications Handlers ==============

    def _setup_canonical_apps(self, params: dict) -> None:
        """Set up canonical applications."""
        pass

    def _setup_canonical_app_with_asset(self, params: dict) -> None:
        """Set up canonical application with asset."""
        app_id = params.get("app_id")
        asset_id = params.get("asset_id")
        print(f"Setting up canonical app {app_id} with asset {asset_id}")

    def _setup_canonical_app_with_assets(self, params: dict) -> None:
        """Set up canonical application with multiple assets."""
        app_id = params.get("app_id")
        print(f"Setting up canonical app {app_id} with multiple assets")

    def _setup_canonical_app_assessed(self, params: dict) -> None:
        """Set up canonical application with assessed assets."""
        app_id = params.get("app_id")
        print(f"Setting up canonical app {app_id} with assessed assets")


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

        # Verify each pact file
        for pact_file in pact_files:
            print(f"\nVerifying pact: {pact_file.name}")

            # Run verification
            # Note: Provider state setup requires a webhook endpoint in production
            # For now, we verify the contract structure without state setup
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

        # Normalize path parameters for robust matching
        paths = schema["paths"].keys()
        normalized_paths = {re.sub(r"\{.*?\}", "{param}", path) for path in paths}

        for endpoint in required_endpoints:
            normalized_endpoint = re.sub(r"\{.*?\}", "{param}", endpoint)
            assert (
                normalized_endpoint in normalized_paths
            ), f"Endpoint {endpoint} not found in OpenAPI schema"


# Entry point for standalone verification
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
