"""
Constants and sample data for seeding discovery flow tables.
"""

import uuid

# Demo constants for multi-tenant testing
DEMO_CLIENT_ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"
DEMO_USER_ID = "demo_user"
DEMO_IMPORT_SESSION_ID = "33333333-3333-3333-3333-333333333333"

# Sample discovery flow data (truncated for space)
SAMPLE_DISCOVERY_FLOWS = [
    {
        "flow_id": uuid.UUID("f1111111-1111-1111-1111-111111111111"),
        "name": "Demo CMDB Discovery",
        "description": "Initial discovery of enterprise CMDB data",
        "current_phase": "completed",
        "progress_percentage": 100.0,
        "status": "completed",
        "raw_data": [
            {
                "hostname": "web-server-01",
                "ip_address": "10.0.1.10",
                "os": "Windows Server 2019",
                "cpu_cores": 4,
                "memory_gb": 16,
                "application": "IIS Web Server",
            }
        ],
        "field_mappings": {
            "hostname": "asset_name",
            "ip_address": "ip_address",
            "os": "operating_system",
        },
        "asset_inventory": {
            "total_assets": 3,
            "by_type": {"server": 3, "database": 1, "application": 2},
        },
    }
]

# Sample asset data
SAMPLE_ASSETS = [
    {
        "id": uuid.UUID("a1111111-1111-1111-1111-111111111111"),
        "name": "Web Server 01",
        "asset_type": "server",
        "asset_subtype": "web_server",
        "description": "Primary web server for customer portal",
        "status": "discovered",
        "criticality": "high",
        "quality_score": 0.85,
        "confidence_score": 0.90,
        "validation_status": "validated",
        "tech_debt_score": 0.3,
        "modernization_priority": "high",
        "six_r_recommendation": "rehost",
        "migration_ready": True,
    }
]
