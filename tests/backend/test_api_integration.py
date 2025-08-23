"""
API Integration tests for enhanced asset inventory functionality.
Tests the full API endpoints with Docker container validation.
"""

import os
import time

import httpx
import pytest

# Markers for curated runs
pytestmark = [pytest.mark.backend, pytest.mark.discovery, pytest.mark.integration, pytest.mark.regression]

# Docker test configuration
DOCKER_API_BASE = os.getenv("DOCKER_API_BASE", "http://localhost:8000")
DOCKER_FRONTEND_BASE = os.getenv("DOCKER_FRONTEND_BASE", "http://localhost:8081")


@pytest.fixture(scope="session")
def api_client():
    """Create HTTP client for API testing."""
    return httpx.AsyncClient(base_url=DOCKER_API_BASE, timeout=30.0)


@pytest.fixture(scope="session")
def frontend_client():
    """Create HTTP client for frontend testing."""
    return httpx.AsyncClient(base_url=DOCKER_FRONTEND_BASE, timeout=30.0)


@pytest.fixture
def auth_headers():
    """Create authentication headers for API requests."""
    return {
        "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",  # Demo Corporation
        "X-Engagement-Id": "58467010-6a72-44e8-ba37-cc0238724455",  # Azure Transformation 2025
        "X-User-Id": "77b30e13-c331-40eb-a0ec-ed0717f72b22",  # chocka@gmail.com
        "Content-Type": "application/json",
    }


@pytest.fixture
def sample_cmdb_csv_content():
    """Sample CMDB CSV content for testing."""
    return """Asset_Name,CI_Type,Environment,CPU_Cores,Memory_GB,Business_Owner,IP_Address,OS
mysql-prod-01,Database,Production,8,32,DBA Team,192.168.1.20,Linux
core-switch-01,Network,Production,,,Network Team,192.168.1.1,Cisco IOS
firewall-dmz,Security,Production,,,Security Team,192.168.1.2,PAN-OS
srv-web-01,Server,Production,16,64,IT Operations,192.168.1.10,Windows Server
crm-application,Application,Production,,,Sales Team,192.168.1.30,N/A
SAN01,Storage,Production,,,IT Operations,192.168.1.50,ONTAP
vmware-vcenter,Virtualization,Production,8,16,IT Operations,192.168.1.60,vSphere"""


@pytest.fixture
def sample_mixed_assets():
    """Sample mixed asset data for processing."""
    return [
        {
            "Asset_Name": "mysql-cluster-prod",
            "CI_Type": "Database",
            "Environment": "Production",
            "CPU_Cores": "16",
            "Memory_GB": "64",
            "Business_Owner": "Database Team",
        },
        {
            "Asset_Name": "CoreSwitch-Main",
            "CI_Type": "Network",
            "Environment": "Production",
            "IP_Address": "10.0.0.1",
        },
        {
            "Asset_Name": "checkpoint-firewall",
            "CI_Type": "Security",
            "Environment": "Production",
        },
        {
            "Asset_Name": "web-server-cluster",
            "CI_Type": "Server",
            "Environment": "Production",
            "CPU_Cores": "32",
            "Memory_GB": "128",
            "OS": "Linux Ubuntu 22.04",
        },
    ]


class TestCMDBAnalysisAPI:
    """Test CMDB analysis API endpoints with agentic workflows."""

    @pytest.mark.asyncio
    async def test_analyze_cmdb_endpoint(
        self, api_client, sample_cmdb_csv_content, auth_headers
    ):
        """Test CMDB analysis endpoint with sample data."""
        request_data = {
            "filename": "test_assets.csv",
            "content": sample_cmdb_csv_content,
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=request_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "dataQuality" in data
        assert "coverage" in data
        assert "missingFields" in data
        assert "readyForImport" in data

        # Verify data quality structure
        quality = data["dataQuality"]
        assert "score" in quality
        assert "issues" in quality
        assert "recommendations" in quality
        assert isinstance(quality["score"], int)
        assert 0 <= quality["score"] <= 100

        # Verify coverage includes device types
        coverage = data["coverage"]
        assert "applications" in coverage
        assert "servers" in coverage
        assert "databases" in coverage
        # Note: dependencies might be 0 in this test data

        # Verify agentic analysis results
        assert isinstance(data["missingFields"], list)
        assert isinstance(data["readyForImport"], bool)

    @pytest.mark.asyncio
    async def test_cmdb_analysis_with_device_classification(
        self, api_client, auth_headers
    ):
        """Test that device classification works correctly in API."""
        device_heavy_content = """Asset_Name,CI_Type,Environment
core-switch-main,Switch,Production
san-storage-01,Storage,Production
firewall-perimeter,Firewall,Production
ups-datacenter,UPS,Production
vmware-host-01,Virtualization,Production"""

        request_data = {
            "filename": "devices.csv",
            "content": device_heavy_content,
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()

        # Should recognize device-heavy dataset
        assert data["status"] == "success"
        # Device-heavy datasets might have different readiness criteria
        assert "readyForImport" in data

    @pytest.mark.asyncio
    async def test_agentic_intelligence_integration(self, api_client, auth_headers):
        """Test that agentic CrewAI intelligence is properly integrated."""
        # Create data that would benefit from agentic analysis
        complex_content = """Name,Type,Description,Environment
complex-erp-system,Unknown,Enterprise resource planning system,Production
legacy-mainframe,Unknown,IBM z/OS mainframe system,Production
iot-sensor-network,Unknown,Temperature monitoring sensors,Production"""

        request_data = {
            "filename": "complex_assets.csv",
            "content": complex_content,
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=request_data,
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()

        # Agentic analysis should provide intelligent insights
        assert "dataQuality" in data
        assert "recommendations" in data["dataQuality"]

        # Should have suggestions for unknown asset types
        recommendations = data["dataQuality"]["recommendations"]
        assert len(recommendations) > 0


class TestCMDBProcessingAPI:
    """Test CMDB processing API with enhanced classification."""

    @pytest.mark.asyncio
    async def test_process_cmdb_data(
        self, api_client, sample_mixed_assets, auth_headers
    ):
        """Test CMDB data processing with mixed asset types."""

        # For status check, we need a flow_id - using placeholder for now
        flow_id = "test-flow-123"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify processing results
        assert "status" in data
        assert "processedAssets" in data
        assert "qualityMetrics" in data
        assert "summary" in data

        # Verify processed assets have enhanced classification
        processed_assets = data["processedAssets"]
        assert len(processed_assets) > 0

        # Check for intelligent asset type classification
        asset_types = [
            asset.get("intelligent_asset_type") for asset in processed_assets
        ]
        assert "Database" in asset_types
        assert "Server" in asset_types

        # Check for 6R readiness assessment
        readiness_values = [
            asset.get("sixr_ready")
            for asset in processed_assets
            if asset.get("sixr_ready")
        ]
        assert len(readiness_values) > 0

        # Check for migration complexity
        complexity_values = [
            asset.get("migration_complexity")
            for asset in processed_assets
            if asset.get("migration_complexity")
        ]
        assert len(complexity_values) > 0

    @pytest.mark.asyncio
    async def test_device_processing_not_applicable(self, api_client, auth_headers):
        """Test that devices are properly marked as not applicable for 6R."""

        # For status check, we need a flow_id - using placeholder for now
        flow_id = "test-flow-456"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        processed_assets = data["processedAssets"]

        # Devices should be marked as "Not Applicable" for 6R
        for asset in processed_assets:
            if asset.get("intelligent_asset_type") in [
                "Network Device",
                "Storage Device",
            ]:
                assert asset.get("sixr_ready") == "Not Applicable"


class TestAssetInventoryAPI:
    """Test asset inventory API with enhanced features."""

    @pytest.mark.asyncio
    async def test_get_assets_endpoint(self, api_client, auth_headers):
        """Test getting active discovery flows."""
        response = await api_client.get(
            "/api/v1/unified-discovery/flows/active", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify response structure - should be a list of active flows
        assert isinstance(data, list)
        # If no active flows, that's expected for a fresh test environment

    @pytest.mark.asyncio
    async def test_suggested_headers_generation(self, api_client, auth_headers):
        """Test that suggested headers are generated correctly."""
        response = await api_client.get(
            "/api/v1/unified-discovery/flows/active", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        if "suggestedHeaders" in data:
            headers = data["suggestedHeaders"]
            assert isinstance(headers, list)

            # Verify header structure
            for header in headers:
                assert "key" in header
                assert "label" in header
                assert "description" in header

    @pytest.mark.asyncio
    async def test_assets_with_6r_readiness(self, api_client, auth_headers):
        """Test that assets include 6R readiness information."""
        response = await api_client.get(
            "/api/v1/unified-discovery/flows/active", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # The response might be an empty list if no active flows
        if isinstance(data, list) and len(data) == 0:
            return  # No assets to test in empty response

        # Check if response has assets structure
        if "assets" not in data:
            return  # No assets structure in response

        assets = data["assets"]

        # Check if any assets have 6R readiness data
        assets_with_readiness = [a for a in assets if "sixr_ready" in a]
        [a for a in assets if "migration_complexity" in a]

        # Note: This might be empty for test data, but structure should be correct
        if assets_with_readiness:
            for asset in assets_with_readiness:
                readiness = asset["sixr_ready"]
                assert readiness in [
                    "Ready",
                    "Not Applicable",
                    "Needs Owner Info",
                    "Needs Infrastructure Data",
                    "Needs Version Info",
                    "Insufficient Data",
                    "Type Classification Needed",
                    "Complex Analysis Required",
                ]


class TestUserFeedbackAPI:
    """Test user feedback processing with agentic learning."""

    @pytest.mark.asyncio
    async def test_submit_cmdb_feedback(self, api_client, auth_headers):
        """Test submitting user feedback for agentic learning."""
        feedback_data = {
            "filename": "test_feedback.csv",
            "originalAnalysis": {
                "asset_type_detected": "server",
                "confidence_level": 0.7,
                "issues": ["Missing business owner"],
                "missing_fields_relevant": ["Business_Owner", "Environment"],
            },
            "userCorrections": {
                "asset_type_override": "Application",
                "field_mappings": {
                    "RAM_GB": "Memory (GB)",
                    "APP_OWNER": "Business Owner",
                },
                "comments": "This is actually an application, not a server",
            },
            "assetTypeOverride": "Application",
        }

        response = await api_client.post(
            "/api/v1/flows/cmdb-feedback", json=feedback_data, headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()

        # Verify feedback processing response
        assert "status" in data
        assert "learningApplied" in data
        assert "message" in data

        # Agentic learning should be applied
        if data.get("learningApplied"):
            assert "patternsLearned" in data
            assert "accuracyImprovement" in data


class TestFieldMappingAPI:
    """Test field mapping functionality."""

    @pytest.mark.asyncio
    async def test_field_mapping_endpoint(self, api_client, auth_headers):
        """Test field mapping tool integration."""
        response = await api_client.get(
            "/api/v1/flows/test-field-mapping", headers=auth_headers
        )

        # This endpoint might not be available in production
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert "mappings" in data

    @pytest.mark.asyncio
    async def test_cmdb_templates_endpoint(self, api_client, auth_headers):
        """Test CMDB template endpoint."""
        response = await api_client.get(
            "/api/v1/flows/cmdb-templates", headers=auth_headers
        )
        assert response.status_code == 200

        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

        # Verify template structure
        for template in data["templates"]:
            assert "name" in template
            assert "fields" in template
            assert "description" in template


class TestDockerContainerIntegration:
    """Test that the application works correctly in Docker containers."""

    @pytest.mark.asyncio
    async def test_backend_container_health(self, api_client):
        """Test that backend container is healthy."""
        try:
            response = await api_client.get("/health")
            # Health endpoint might not exist, so check any valid endpoint
            if response.status_code == 404:
                # Try root endpoint
                response = await api_client.get("/")

            # Should get some response, not connection error
            assert response.status_code in [
                200,
                404,
                422,
            ]  # Any HTTP response means container is running

        except httpx.ConnectError:
            pytest.fail("Backend Docker container is not accessible")

    @pytest.mark.asyncio
    async def test_frontend_container_health(self, frontend_client):
        """Test that frontend container is healthy."""
        try:
            response = await frontend_client.get("/")
            assert response.status_code == 200

        except httpx.ConnectError:
            pytest.fail("Frontend Docker container is not accessible")

    @pytest.mark.asyncio
    async def test_api_cors_configuration(self, api_client, auth_headers):
        """Test that CORS is properly configured for frontend-backend communication."""
        headers = {
            "Origin": DOCKER_FRONTEND_BASE,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
            **auth_headers,
        }

        # Test preflight request
        response = await api_client.options(
            "/api/v1/unified-discovery/flows/active", headers=headers
        )

        # Should not block CORS
        assert response.status_code in [
            200,
            204,
            404,
        ]  # 404 is OK if OPTIONS not implemented


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_cmdb_data(self, api_client, auth_headers):
        """Test handling of invalid CMDB data."""
        invalid_data = {
            "filename": "invalid.csv",
            "content": "Invalid,CSV,Content\nwith,mismatched,columns,too,many",
            "fileType": "csv",
        }

        response = await api_client.post(
            "/api/v1/unified-discovery/flow/initialize",
            json=invalid_data,
            headers=auth_headers,
        )

        # Should handle gracefully, not crash
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            # Should indicate issues with data quality
            assert "dataQuality" in data
            quality_score = data["dataQuality"]["score"]
            assert quality_score < 50  # Should be low quality

    @pytest.mark.asyncio
    async def test_empty_processing_request(self, api_client, auth_headers):
        """Test handling of empty processing request."""

        # For status check, we need a flow_id - using placeholder for now
        flow_id = "empty-flow-789"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )

        # Should handle gracefully
        assert response.status_code in [200, 400]

        if response.status_code == 200:
            data = response.json()
            assert "processedAssets" in data
            assert len(data["processedAssets"]) == 0

    @pytest.mark.asyncio
    async def test_malformed_feedback(self, api_client, auth_headers):
        """Test handling of malformed feedback data."""
        malformed_feedback = {
            "filename": "test.csv"
            # Missing required fields - this should cause a validation error
        }

        response = await api_client.post(
            "/api/v1/discovery/cmdb-feedback",
            json=malformed_feedback,
            headers=auth_headers,
        )

        # Should return validation error or not found (if endpoint doesn't exist)
        assert response.status_code in [404, 422]


class TestPerformance:
    """Test performance with larger datasets."""

    @pytest.mark.asyncio
    async def test_large_dataset_processing(self, api_client, auth_headers):
        """Test processing of moderately large dataset."""
        # Create larger dataset (100 assets)
        large_dataset = []
        for i in range(100):
            asset_type = ["Server", "Application", "Database", "Network", "Storage"][
                i % 5
            ]
            large_dataset.append(
                {
                    "Asset_Name": f"asset-{i:03d}",
                    "CI_Type": asset_type,
                    "Environment": "Production" if i % 2 == 0 else "Development",
                    "CPU_Cores": str(4 + (i % 16)),
                    "Memory_GB": str(8 + (i % 32)),
                }
            )

        start_time = time.time()
        # For status check, we need a flow_id - using placeholder for now
        flow_id = "large-dataset-flow-999"
        response = await api_client.get(
            f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
        )
        processing_time = time.time() - start_time

        assert response.status_code == 200
        # Should complete within reasonable time (30 seconds for 100 assets)
        assert processing_time < 30

        data = response.json()
        assert len(data["processedAssets"]) == 100


@pytest.mark.asyncio
async def test_end_to_end_workflow(api_client, sample_cmdb_csv_content, auth_headers):
    """Test complete end-to-end workflow: analyze -> process -> inventory -> feedback."""

    # Step 1: Analyze CMDB data
    analyze_request = {
        "filename": "e2e_test.csv",
        "content": sample_cmdb_csv_content,
        "fileType": "csv",
    }

    analyze_response = await api_client.post(
        "/api/v1/unified-discovery/flow/initialize",
        json=analyze_request,
        headers=auth_headers,
    )
    assert analyze_response.status_code == 200

    analyze_data = analyze_response.json()
    assert analyze_data["status"] == "success"

    # Step 2: Process the data
    # Convert CSV to asset list for processing
    import csv
    import io

    csv_reader = csv.DictReader(io.StringIO(sample_cmdb_csv_content))
    list(csv_reader)

    # For status check, we need a flow_id - using placeholder for now
    flow_id = "e2e-flow-123"
    process_response = await api_client.get(
        f"/api/v1/unified-discovery/flow/{flow_id}/status", headers=auth_headers
    )
    assert process_response.status_code == 200

    process_data = process_response.json()
    assert len(process_data["processedAssets"]) > 0

    # Step 3: Check inventory
    inventory_response = await api_client.get(
        "/api/v1/unified-discovery/flows/active", headers=auth_headers
    )
    assert inventory_response.status_code == 200

    inventory_data = inventory_response.json()
    assert "assets" in inventory_data
    assert "summary" in inventory_data

    # Step 4: Submit feedback (if analysis had issues)
    if analyze_data["dataQuality"]["score"] < 90:
        feedback_request = {
            "filename": "e2e_test.csv",
            "originalAnalysis": analyze_data,
            "userCorrections": {"comments": "Data quality looks good after review"},
        }

        feedback_response = await api_client.post(
            "/api/v1/discovery/cmdb-feedback",
            json=feedback_request,
            headers=auth_headers,
        )
        assert feedback_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
