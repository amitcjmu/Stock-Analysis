"""
API Fixtures for Integration Tests

Provides HTTP clients, auth headers, and sample data fixtures.
"""

import os
from typing import Any, Dict, List

import httpx
import pytest
import pytest_asyncio

# Docker test configuration for API tests
DOCKER_API_BASE = os.getenv("DOCKER_API_BASE", "http://localhost:8000")
DOCKER_FRONTEND_BASE = os.getenv("DOCKER_FRONTEND_BASE", "http://localhost:8081")


@pytest_asyncio.fixture(scope="function")
async def api_client():
    """Create HTTP client for API testing.

    Note: Using function scope to avoid event loop lifecycle issues.
    Each test gets its own client instance and event loop.
    """
    client = httpx.AsyncClient(base_url=DOCKER_API_BASE, timeout=30.0)
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(scope="function")
async def frontend_client():
    """Create HTTP client for frontend testing.

    Note: Using function scope to avoid event loop lifecycle issues.
    Each test gets its own client instance and event loop.
    """
    client = httpx.AsyncClient(base_url=DOCKER_FRONTEND_BASE, timeout=30.0)
    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture
def auth_headers():
    """Create authentication headers for API requests."""
    return {
        "X-Client-Account-Id": "11111111-1111-1111-1111-111111111111",  # Demo Corp
        "X-Engagement-Id": "58467010-6a72-44e8-ba37-cc0238724455",  # Azure 2025
        "X-User-Id": "77b30e13-c331-40eb-a0ec-ed0717f72b22",  # chocka@gmail.com
        "Content-Type": "application/json",
    }


@pytest.fixture
def integration_test_config() -> Dict[str, Any]:
    """Integration test configuration."""
    return {
        "test_timeouts": {
            "workflow_execution": 30,  # seconds
            "validation": 10,
            "synchronization": 5,
            "error_recovery": 15,
        },
        "test_data_sizes": {"small": 5, "medium": 25, "large": 100},
        "performance_thresholds": {
            "workflow_execution": 30.0,  # seconds
            "validation_speed": 5.0,
            "sync_speed": 2.0,
            "memory_usage": 100 * 1024 * 1024,  # 100MB
        },
        "quality_thresholds": {
            "min_confidence": 0.7,
            "min_completeness": 0.8,
            "max_critical_issues": 0,
        },
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
def sample_mixed_assets() -> List[Dict[str, Any]]:
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
