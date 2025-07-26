"""
End-to-End tests for the complete discovery flow
Tests the entire flow from data import to asset creation
"""

import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.main import app

# Configure pytest to use asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def test_client():
    """Create test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_headers(test_client):
    """Create authenticated headers"""
    # In a real test, this would create a test user and get a real token
    return {"Authorization": "Bearer test-token", "Content-Type": "application/json"}


@pytest_asyncio.fixture
async def test_context_headers():
    """Create test context headers"""
    return {
        "X-Client-Account-ID": "550e8400-e29b-41d4-a716-446655440000",
        "X-Engagement-ID": "660e8400-e29b-41d4-a716-446655440000",
        "X-User-ID": "770e8400-e29b-41d4-a716-446655440000",
    }


class TestDiscoveryFlowE2E:
    """End-to-end tests for discovery flow"""

    async def test_complete_discovery_flow_with_file_upload(
        self, test_client, auth_headers, test_context_headers
    ):
        """Test complete flow: upload CSV -> process -> create assets"""
        headers = {**auth_headers, **test_context_headers}

        # Step 1: Upload CSV file
        csv_content = """hostname,ip_address,operating_system,cpu_cores,memory_gb,storage_gb,environment,location
server-01,10.0.1.100,Ubuntu 20.04,8,32,500,production,datacenter-1
server-02,10.0.1.101,Ubuntu 20.04,16,64,1000,production,datacenter-1
server-03,10.0.1.102,Windows Server 2019,8,16,250,development,datacenter-2
app-server-01,10.0.2.100,RHEL 8,4,8,100,production,datacenter-1
db-server-01,10.0.3.100,Ubuntu 20.04,32,128,2000,production,datacenter-1"""

        files = {"file": ("servers.csv", csv_content.encode(), "text/csv")}

        response = await test_client.post(
            "/api/v3/data-import/imports/upload",
            files=files,
            headers=headers,
            params={"name": "Q1 2025 Server Inventory", "auto_create_flow": True},
        )

        assert response.status_code == 201
        import_data = response.json()
        assert import_data["total_records"] == 5
        assert import_data["flow_id"] is not None

        flow_id = import_data["flow_id"]
        import_id = import_data["import_id"]

        # Step 2: Wait for flow initialization
        await asyncio.sleep(2)

        # Step 3: Get flow status
        response = await test_client.get(
            f"/api/v3/discovery-flow/flows/{flow_id}/status", headers=headers
        )

        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] in ["initialized", "in_progress"]
        assert status_data["current_phase"] in ["initialization", "field_mapping"]

        # Step 4: Create field mappings
        response = await test_client.post(
            "/api/v3/field-mapping/mappings",
            json={
                "flow_id": flow_id,
                "source_fields": [
                    "hostname",
                    "ip_address",
                    "operating_system",
                    "cpu_cores",
                    "memory_gb",
                    "storage_gb",
                    "environment",
                    "location",
                ],
                "target_schema": "asset_inventory",
                "auto_map": True,
            },
            headers=headers,
        )

        assert response.status_code == 201
        mapping_data = response.json()
        assert mapping_data["mapping_percentage"] == 100.0
        assert len(mapping_data["mappings"]) == 8

        # Step 5: Execute data validation phase
        response = await test_client.post(
            f"/api/v3/discovery-flow/flows/{flow_id}/execute/data_validation",
            headers=headers,
        )

        assert response.status_code == 200

        # Step 6: Validate the import data
        response = await test_client.post(
            f"/api/v3/data-import/imports/{import_id}/validate",
            json={
                "validation_rules": [
                    {
                        "field": "ip_address",
                        "rule_type": "format",
                        "parameters": {"pattern": "ipv4"},
                        "severity": "error",
                    },
                    {
                        "field": "memory_gb",
                        "rule_type": "range",
                        "parameters": {"min": 1, "max": 1024},
                        "severity": "warning",
                    },
                ]
            },
            headers=headers,
        )

        assert response.status_code == 200
        validation_data = response.json()
        assert validation_data["is_valid"] is True
        assert validation_data["total_records"] == 5
        assert validation_data["valid_records"] == 5

        # Step 7: Execute remaining phases
        phases = ["data_cleansing", "inventory_building"]

        for phase in phases:
            response = await test_client.post(
                f"/api/v3/discovery-flow/flows/{flow_id}/execute/{phase}",
                headers=headers,
            )
            assert response.status_code == 200
            await asyncio.sleep(1)  # Give time for phase execution

        # Step 8: Get final flow status
        response = await test_client.get(
            f"/api/v3/discovery-flow/flows/{flow_id}", headers=headers
        )

        assert response.status_code == 200
        flow_data = response.json()
        assert flow_data["records_total"] == 5
        assert len(flow_data["phases_completed"]) >= 3

        # Step 9: Verify assets were created (would need asset endpoint)
        # This would be implemented when asset endpoints are available

        print("\n✅ E2E Test completed successfully!")
        print(f"   - Imported {import_data['total_records']} records")
        print(f"   - Created flow: {flow_id}")
        print(f"   - Completed phases: {flow_data['phases_completed']}")

    async def test_discovery_flow_with_json_data(
        self, test_client, auth_headers, test_context_headers
    ):
        """Test discovery flow with JSON data input"""
        headers = {**auth_headers, **test_context_headers}

        # Step 1: Create import with JSON data
        json_data = [
            {
                "name": "web-server-01",
                "type": "application_server",
                "specs": {"cpu": 4, "memory_mb": 8192, "storage_mb": 102400},
                "network": {"ip": "10.0.1.50", "dns": "web01.example.com"},
                "software": {"os": "Ubuntu 22.04", "runtime": "Node.js 18"},
            },
            {
                "name": "api-server-01",
                "type": "application_server",
                "specs": {"cpu": 8, "memory_mb": 16384, "storage_mb": 204800},
                "network": {"ip": "10.0.1.51", "dns": "api01.example.com"},
                "software": {"os": "Ubuntu 22.04", "runtime": "Python 3.11"},
            },
        ]

        response = await test_client.post(
            "/api/v3/data-import/imports",
            json={
                "name": "Application Servers Import",
                "description": "Import of application server inventory",
                "source_type": "json",
                "data": json_data,
                "auto_create_flow": True,
            },
            headers=headers,
        )

        assert response.status_code == 201
        import_data = response.json()
        assert import_data["total_records"] == 2

        # Step 2: Create custom field mappings for nested JSON
        flow_id = import_data["flow_id"]

        response = await test_client.post(
            "/api/v3/field-mapping/mappings",
            json={
                "flow_id": flow_id,
                "source_fields": [
                    "name",
                    "type",
                    "specs.cpu",
                    "specs.memory_mb",
                    "network.ip",
                    "software.os",
                ],
                "target_schema": "asset_inventory",
                "mapping_rules": {
                    "name": "asset_name",
                    "type": "asset_type",
                    "specs.cpu": "cpu_cores",
                    "specs.memory_mb": "memory_gb",  # Will need conversion
                    "network.ip": "ip_address",
                    "software.os": "operating_system",
                },
            },
            headers=headers,
        )

        assert response.status_code == 201

        # Step 3: Get preview of imported data
        response = await test_client.get(
            f"/api/v3/data-import/imports/{import_data['import_id']}/preview?sample_size=10",
            headers=headers,
        )

        assert response.status_code == 200
        preview_data = response.json()
        assert len(preview_data["preview_data"]) == 2
        assert "name" in preview_data["field_names"]

    async def test_flow_pause_resume_functionality(
        self, test_client, auth_headers, test_context_headers
    ):
        """Test pausing and resuming a discovery flow"""
        headers = {**auth_headers, **test_context_headers}

        # Create a flow with substantial data
        test_data = [
            {"server": f"server-{i:03d}", "ip": f"10.0.1.{i}"} for i in range(100)
        ]

        response = await test_client.post(
            "/api/v3/discovery-flow/flows",
            json={
                "name": "Pausable Flow Test",
                "raw_data": test_data,
                "execution_mode": "hybrid",
            },
            headers=headers,
        )

        assert response.status_code == 201
        flow_id = response.json()["flow_id"]

        # Wait a moment then pause the flow
        await asyncio.sleep(1)

        response = await test_client.post(
            f"/api/v3/discovery-flow/flows/{flow_id}/pause",
            json={"reason": "Manual review required"},
            headers=headers,
        )

        assert response.status_code == 200
        pause_result = response.json()
        assert pause_result["status"] == "paused"

        # Verify flow is paused
        response = await test_client.get(
            f"/api/v3/discovery-flow/flows/{flow_id}/status", headers=headers
        )

        status = response.json()
        assert status["status"] == "paused"
        assert status["can_resume"] is True

        # Resume the flow
        response = await test_client.post(
            f"/api/v3/discovery-flow/flows/{flow_id}/resume",
            json={"resume_context": {"reviewed": True}},
            headers=headers,
        )

        assert response.status_code == 200
        resume_result = response.json()
        assert resume_result["status"] == "in_progress"

    async def test_flow_error_handling_and_recovery(
        self, test_client, auth_headers, test_context_headers
    ):
        """Test error handling and recovery in discovery flow"""
        headers = {**auth_headers, **test_context_headers}

        # Create flow with invalid data to trigger validation errors
        invalid_data = [
            {
                "hostname": "server-01",
                "ip_address": "invalid-ip",  # Invalid IP
                "memory_gb": -16,  # Invalid negative value
                "cpu_cores": 999999,  # Unrealistic value
            }
        ]

        response = await test_client.post(
            "/api/v3/data-import/imports",
            json={
                "name": "Invalid Data Test",
                "source_type": "json",
                "data": invalid_data,
                "auto_create_flow": True,
            },
            headers=headers,
        )

        assert response.status_code == 201
        import_id = response.json()["import_id"]

        # Validate with strict rules
        response = await test_client.post(
            f"/api/v3/data-import/imports/{import_id}/validate",
            json={
                "validation_rules": [
                    {
                        "field": "ip_address",
                        "rule_type": "format",
                        "parameters": {"pattern": "ipv4"},
                        "severity": "error",
                    },
                    {
                        "field": "memory_gb",
                        "rule_type": "range",
                        "parameters": {"min": 1, "max": 1024},
                        "severity": "error",
                    },
                    {
                        "field": "cpu_cores",
                        "rule_type": "range",
                        "parameters": {"min": 1, "max": 128},
                        "severity": "error",
                    },
                ]
            },
            headers=headers,
        )

        assert response.status_code == 200
        validation = response.json()
        assert validation["is_valid"] is False
        assert len(validation["validation_errors"]) >= 3
        assert (
            "Fix validation errors before proceeding" in validation["recommendations"]
        )

    async def test_bulk_flow_operations(
        self, test_client, auth_headers, test_context_headers
    ):
        """Test bulk operations on multiple flows"""
        headers = {**auth_headers, **test_context_headers}

        # Create multiple flows
        flow_ids = []
        for i in range(3):
            response = await test_client.post(
                "/api/v3/discovery-flow/flows",
                json={
                    "name": f"Bulk Test Flow {i+1}",
                    "raw_data": [{"test": i}],
                    "execution_mode": "database",
                },
                headers=headers,
            )
            assert response.status_code == 201
            flow_ids.append(response.json()["flow_id"])

        # List all flows
        response = await test_client.get(
            "/api/v3/discovery-flow/flows?page_size=10", headers=headers
        )

        assert response.status_code == 200
        list_data = response.json()
        assert list_data["total"] >= 3

        # Delete flows
        for flow_id in flow_ids:
            response = await test_client.delete(
                f"/api/v3/discovery-flow/flows/{flow_id}", headers=headers
            )
            assert response.status_code == 204


@pytest.mark.asyncio
async def test_discovery_flow_performance():
    """Test discovery flow performance with larger datasets"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        headers = {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
            "X-Client-Account-ID": "550e8400-e29b-41d4-a716-446655440000",
            "X-Engagement-ID": "660e8400-e29b-41d4-a716-446655440000",
        }

        # Generate large dataset (1000 servers)
        large_dataset = []
        for i in range(1000):
            large_dataset.append(
                {
                    "hostname": f"server-{i:04d}",
                    "ip_address": f"10.{i // 256}.{(i // 16) % 16}.{i % 256}",
                    "operating_system": [
                        "Ubuntu 20.04",
                        "RHEL 8",
                        "Windows Server 2019",
                    ][i % 3],
                    "cpu_cores": 4 + (i % 28),
                    "memory_gb": 8 + (i % 120),
                    "storage_gb": 100 + (i % 1900),
                    "environment": ["production", "staging", "development"][i % 3],
                    "location": f"datacenter-{(i % 5) + 1}",
                }
            )

        import time

        start_time = time.time()

        # Create import with large dataset
        response = await client.post(
            "/api/v3/data-import/imports",
            json={
                "name": "Large Dataset Performance Test",
                "source_type": "json",
                "data": large_dataset,
                "auto_create_flow": True,
            },
            headers=headers,
        )

        assert response.status_code == 201
        import_time = time.time() - start_time

        import_data = response.json()
        flow_id = import_data["flow_id"]

        # Measure field mapping performance
        start_time = time.time()

        response = await client.post(
            "/api/v3/field-mapping/mappings",
            json={
                "flow_id": flow_id,
                "source_fields": list(large_dataset[0].keys()),
                "target_schema": "asset_inventory",
                "auto_map": True,
            },
            headers=headers,
        )

        assert response.status_code == 201
        mapping_time = time.time() - start_time

        print("\n⚡ Performance Results:")
        print(f"   - Import 1000 records: {import_time:.2f}s")
        print(f"   - Auto-map 8 fields: {mapping_time:.2f}s")

        # Performance assertions
        assert import_time < 10.0, f"Import took {import_time}s, expected < 10s"
        assert mapping_time < 2.0, f"Mapping took {mapping_time}s, expected < 2s"


if __name__ == "__main__":
    asyncio.run(test_discovery_flow_performance())
