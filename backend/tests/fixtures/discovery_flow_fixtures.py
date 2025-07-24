"""
Test fixtures for Discovery Flow testing.

This module provides comprehensive test data for testing the Discovery flow,
including mock CMDB data, field mappings, and expected agent decisions.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict

# Test client and engagement IDs
TEST_CLIENT_ACCOUNT_ID = 99999
TEST_ENGAGEMENT_ID = 99999
TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")

# Mock CMDB data for testing
MOCK_CMDB_DATA = {
    "servers": [
        {
            "server_name": "APP-WEB-01",
            "ip_address": "10.0.1.10",
            "operating_system": "Windows Server 2019",
            "cpu_cores": 8,
            "memory_gb": 32,
            "storage_gb": 500,
            "environment": "Production",
            "location": "DC-East",
            "business_criticality": "High",
            "owner": "Web Team",
            "last_updated": "2024-01-15",
            "tags": ["web", "frontend", "critical"],
        },
        {
            "server_name": "APP-DB-01",
            "ip_address": "10.0.2.20",
            "operating_system": "Red Hat Enterprise Linux 8",
            "cpu_cores": 16,
            "memory_gb": 128,
            "storage_gb": 2048,
            "environment": "Production",
            "location": "DC-East",
            "business_criticality": "Critical",
            "owner": "Database Team",
            "last_updated": "2024-01-10",
            "tags": ["database", "oracle", "critical"],
        },
        {
            "server_name": "APP-API-01",
            "ip_address": "10.0.3.30",
            "operating_system": "Ubuntu 20.04 LTS",
            "cpu_cores": 4,
            "memory_gb": 16,
            "storage_gb": 200,
            "environment": "Production",
            "location": "DC-West",
            "business_criticality": "High",
            "owner": "API Team",
            "last_updated": "2024-01-20",
            "tags": ["api", "microservices", "kubernetes"],
        },
        {
            "server_name": "DEV-TEST-01",
            "ip_address": "10.0.10.100",
            "operating_system": "Windows Server 2016",
            "cpu_cores": 2,
            "memory_gb": 8,
            "storage_gb": 100,
            "environment": "Development",
            "location": "DC-Dev",
            "business_criticality": "Low",
            "owner": "Dev Team",
            "last_updated": "2024-01-05",
            "tags": ["development", "test", "non-critical"],
        },
    ],
    "applications": [
        {
            "app_name": "Customer Portal",
            "app_id": "APP-001",
            "version": "3.2.1",
            "technology_stack": ["Java", "Spring Boot", "React", "PostgreSQL"],
            "server_dependencies": ["APP-WEB-01", "APP-API-01", "APP-DB-01"],
            "business_unit": "Customer Service",
            "criticality": "Critical",
            "users": 50000,
            "data_classification": "Confidential",
        },
        {
            "app_name": "Internal Dashboard",
            "app_id": "APP-002",
            "version": "1.5.0",
            "technology_stack": ["Python", "Django", "Vue.js", "MySQL"],
            "server_dependencies": ["APP-WEB-01", "APP-DB-01"],
            "business_unit": "Operations",
            "criticality": "Medium",
            "users": 500,
            "data_classification": "Internal",
        },
    ],
    "databases": [
        {
            "db_name": "CustomerDB",
            "db_type": "PostgreSQL",
            "version": "14.5",
            "size_gb": 500,
            "server": "APP-DB-01",
            "replication": "Master-Slave",
            "backup_frequency": "Daily",
            "data_classification": "Confidential",
        },
        {
            "db_name": "AnalyticsDB",
            "db_type": "MySQL",
            "version": "8.0",
            "size_gb": 200,
            "server": "APP-DB-01",
            "replication": "None",
            "backup_frequency": "Weekly",
            "data_classification": "Internal",
        },
    ],
}

# Field mapping suggestions for testing
FIELD_MAPPING_SUGGESTIONS = {
    "servers": {
        "server_name": {
            "suggested_mapping": "hostname",
            "confidence": 0.95,
            "alternatives": ["name", "server_id"],
        },
        "ip_address": {
            "suggested_mapping": "private_ip",
            "confidence": 0.90,
            "alternatives": ["ip", "network_address"],
        },
        "operating_system": {
            "suggested_mapping": "os_type",
            "confidence": 0.85,
            "alternatives": ["os", "platform"],
        },
        "cpu_cores": {
            "suggested_mapping": "cpu_count",
            "confidence": 0.88,
            "alternatives": ["cores", "vcpus"],
        },
        "memory_gb": {
            "suggested_mapping": "memory_size",
            "confidence": 0.87,
            "alternatives": ["ram", "memory"],
        },
        "environment": {
            "suggested_mapping": "environment",
            "confidence": 0.99,
            "alternatives": ["env", "stage"],
        },
    },
    "applications": {
        "app_name": {
            "suggested_mapping": "application_name",
            "confidence": 0.93,
            "alternatives": ["name", "app_id"],
        },
        "technology_stack": {
            "suggested_mapping": "tech_stack",
            "confidence": 0.85,
            "alternatives": ["technologies", "stack"],
        },
        "criticality": {
            "suggested_mapping": "business_criticality",
            "confidence": 0.91,
            "alternatives": ["priority", "importance"],
        },
    },
}

# Expected agent decisions for testing
AGENT_DECISIONS = {
    "data_validation": {
        "status": "completed",
        "issues_found": [
            {
                "type": "missing_data",
                "field": "patch_level",
                "affected_records": 4,
                "severity": "medium",
                "recommendation": "Consider adding OS patch information for security assessment",
            },
            {
                "type": "outdated_os",
                "field": "operating_system",
                "affected_records": 1,
                "severity": "high",
                "recommendation": "Windows Server 2016 is approaching end of support",
            },
        ],
        "data_quality_score": 0.85,
    },
    "field_mapping": {
        "status": "completed",
        "mappings_confirmed": 12,
        "mappings_suggested": 3,
        "confidence_average": 0.89,
    },
    "asset_classification": {
        "status": "completed",
        "classifications": {
            "production_critical": 3,
            "production_non_critical": 0,
            "development": 1,
            "total": 4,
        },
        "migration_candidates": {
            "rehost": ["APP-WEB-01", "APP-API-01"],
            "replatform": ["APP-DB-01"],
            "retire": ["DEV-TEST-01"],
        },
    },
    "dependency_analysis": {
        "status": "completed",
        "dependencies_found": 8,
        "critical_paths": [
            ["Customer Portal", "APP-WEB-01", "APP-API-01", "APP-DB-01", "CustomerDB"],
            ["Internal Dashboard", "APP-WEB-01", "APP-DB-01", "AnalyticsDB"],
        ],
        "migration_groups": [
            {
                "group_id": 1,
                "assets": ["APP-DB-01", "CustomerDB", "AnalyticsDB"],
                "reason": "Database tier - must migrate together",
            },
            {
                "group_id": 2,
                "assets": ["APP-WEB-01", "APP-API-01"],
                "reason": "Application tier - can migrate after database",
            },
        ],
    },
}

# SSE event test data
SSE_EVENT_SEQUENCE = [
    {
        "event": "phase_start",
        "data": {
            "phase": "data_import",
            "message": "Starting data import phase",
            "timestamp": datetime.utcnow().isoformat(),
        },
    },
    {
        "event": "agent_thinking",
        "data": {
            "agent": "DataValidationAgent",
            "thought": "Analyzing CMDB data structure and quality...",
            "timestamp": datetime.utcnow().isoformat(),
        },
    },
    {
        "event": "agent_decision",
        "data": {
            "agent": "DataValidationAgent",
            "decision": "Found 4 servers with complete data. Identified 2 data quality issues.",
            "confidence": 0.85,
            "timestamp": datetime.utcnow().isoformat(),
        },
    },
    {
        "event": "phase_complete",
        "data": {
            "phase": "data_import",
            "status": "success",
            "next_phase": "field_mapping",
            "timestamp": datetime.utcnow().isoformat(),
        },
    },
]

# Test flow states
FLOW_STATES = {
    "initialized": {
        "flow_id": str(uuid.uuid4()),
        "status": "initialized",
        "current_phase": None,
        "phases_completed": [],
        "created_at": datetime.utcnow().isoformat(),
    },
    "data_import_in_progress": {
        "flow_id": str(uuid.uuid4()),
        "status": "running",
        "current_phase": "data_import",
        "phases_completed": [],
        "data_import_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
    },
    "field_mapping_in_progress": {
        "flow_id": str(uuid.uuid4()),
        "status": "running",
        "current_phase": "field_mapping",
        "phases_completed": ["data_import"],
        "data_import_id": str(uuid.uuid4()),
        "field_mapping_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
    },
    "completed": {
        "flow_id": str(uuid.uuid4()),
        "status": "completed",
        "current_phase": None,
        "phases_completed": [
            "data_import",
            "field_mapping",
            "asset_inventory",
            "dependency_analysis",
        ],
        "data_import_id": str(uuid.uuid4()),
        "field_mapping_id": str(uuid.uuid4()),
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
    },
}


def get_mock_file_content(file_type: str = "csv") -> bytes:
    """Generate mock file content for testing file uploads."""
    if file_type == "csv":
        csv_content = (
            "server_name,ip_address,operating_system,cpu_cores,memory_gb,environment\n"
        )
        for server in MOCK_CMDB_DATA["servers"]:
            csv_content += f"{server['server_name']},{server['ip_address']},{server['operating_system']},"
            csv_content += (
                f"{server['cpu_cores']},{server['memory_gb']},{server['environment']}\n"
            )
        return csv_content.encode("utf-8")
    elif file_type == "json":
        return json.dumps(MOCK_CMDB_DATA, indent=2).encode("utf-8")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def create_test_discovery_flow() -> Dict[str, Any]:
    """Create a test discovery flow with all required fields."""
    flow_id = str(uuid.uuid4())
    return {
        "flow_id": flow_id,
        "master_flow_id": str(uuid.uuid4()),
        "client_account_id": TEST_CLIENT_ACCOUNT_ID,
        "engagement_id": TEST_ENGAGEMENT_ID,
        "created_by": str(TEST_USER_ID),
        "status": "initialized",
        "current_phase": None,
        "phases_completed": [],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {"source": "test_fixture", "test_run": True},
    }


def create_test_data_import() -> Dict[str, Any]:
    """Create a test data import record."""
    return {
        "import_id": str(uuid.uuid4()),
        "flow_id": str(uuid.uuid4()),
        "client_account_id": TEST_CLIENT_ACCOUNT_ID,
        "engagement_id": TEST_ENGAGEMENT_ID,
        "filename": "test_cmdb_data.csv",
        "file_type": "csv",
        "file_size": 2048,
        "status": "completed",
        "validation_results": AGENT_DECISIONS["data_validation"],
        "created_at": datetime.utcnow(),
        "completed_at": datetime.utcnow(),
    }


def create_test_field_mapping() -> Dict[str, Any]:
    """Create a test field mapping record."""
    return {
        "mapping_id": str(uuid.uuid4()),
        "flow_id": str(uuid.uuid4()),
        "data_import_id": str(uuid.uuid4()),
        "client_account_id": TEST_CLIENT_ACCOUNT_ID,
        "engagement_id": TEST_ENGAGEMENT_ID,
        "source_schema": list(MOCK_CMDB_DATA["servers"][0].keys()),
        "target_schema": [
            "hostname",
            "private_ip",
            "os_type",
            "cpu_count",
            "memory_size",
            "environment",
        ],
        "mappings": FIELD_MAPPING_SUGGESTIONS["servers"],
        "status": "completed",
        "created_at": datetime.utcnow(),
        "completed_at": datetime.utcnow(),
    }


# Error scenarios for testing
ERROR_SCENARIOS = {
    "file_too_large": {
        "error": "File size exceeds maximum allowed size of 10MB",
        "code": "FILE_TOO_LARGE",
        "status_code": 413,
    },
    "invalid_file_format": {
        "error": "Invalid file format. Supported formats: CSV, JSON, XML",
        "code": "INVALID_FORMAT",
        "status_code": 400,
    },
    "parsing_error": {
        "error": "Failed to parse file content. Please check the file structure.",
        "code": "PARSE_ERROR",
        "status_code": 422,
    },
    "unauthorized": {
        "error": "User does not have permission to access this resource",
        "code": "UNAUTHORIZED",
        "status_code": 403,
    },
    "flow_not_found": {
        "error": "Discovery flow not found",
        "code": "NOT_FOUND",
        "status_code": 404,
    },
}

# Performance test data
PERFORMANCE_TEST_DATA = {
    "large_dataset": {
        "servers": [
            {
                "server_name": f"SERVER-{i:04d}",
                "ip_address": f"10.0.{i // 256}.{i % 256}",
                "operating_system": ["Windows Server 2019", "Ubuntu 20.04", "RHEL 8"][
                    i % 3
                ],
                "cpu_cores": [4, 8, 16, 32][i % 4],
                "memory_gb": [16, 32, 64, 128][i % 4],
                "environment": ["Production", "Development", "Testing"][i % 3],
            }
            for i in range(1000)
        ]
    }
}
