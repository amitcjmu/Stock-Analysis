"""
Shared constants for database seeding across all agents.
This file contains hardcoded IDs and values to ensure consistency.
"""

import os
import uuid
from datetime import datetime, timezone

# Demo Client and Engagement IDs (hardcoded for consistency)
DEMO_CLIENT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

# Demo Company Info
DEMO_COMPANY_NAME = "DemoCorp International"
DEMO_COMPANY_DOMAIN = "democorp.com"

# User IDs (hardcoded for consistency)
USER_IDS = {
    "engagement_manager": uuid.UUID("33333333-3333-3333-3333-333333333333"),
    "analyst": uuid.UUID("44444444-4444-4444-4444-444444444444"),
    "viewer": uuid.UUID("55555555-5555-5555-5555-555555555555"),
    "client_admin": uuid.UUID("66666666-6666-6666-6666-666666666666"),
}

# User Details
USERS = [
    {
        "id": USER_IDS["engagement_manager"],
        "email": "demo@democorp.com",
        "username": "demo_manager",
        "full_name": "Demo Manager",
        "role": "ENGAGEMENT_MANAGER",
        "is_active": True,
        "is_verified": True,
    },
    {
        "id": USER_IDS["analyst"],
        "email": "analyst@democorp.com",
        "username": "demo_analyst",
        "full_name": "Demo Analyst",
        "role": "ANALYST",
        "is_active": True,
        "is_verified": True,
    },
    {
        "id": USER_IDS["viewer"],
        "email": "viewer@democorp.com",
        "username": "demo_viewer",
        "full_name": "Demo Viewer",
        "role": "VIEWER",
        "is_active": True,
        "is_verified": True,
    },
    {
        "id": USER_IDS["client_admin"],
        "email": "client.admin@democorp.com",
        "username": "client_admin",
        "full_name": "Client Administrator",
        "role": "CLIENT_ADMIN",
        "is_active": True,
        "is_verified": True,
    },
]

# Discovery Flow IDs (hardcoded for consistency)
FLOW_IDS = {
    "complete": uuid.UUID("77777777-7777-7777-7777-777777777777"),
    "field_mapping": uuid.UUID("88888888-8888-8888-8888-888888888888"),
    "asset_inventory": uuid.UUID("99999999-9999-9999-9999-999999999999"),
    "failed_import": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
    "just_started": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
}

# Data Import IDs (hardcoded for consistency)
IMPORT_IDS = {
    "csv_servers": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
    "json_applications": uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
    "excel_dependencies": uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
}

# Flow States and Details
FLOWS = [
    {
        "id": FLOW_IDS["complete"],
        "name": "Completed Discovery - Production Environment",
        "flow_type": "full_discovery",
        "state": "complete",
        "current_phase": "completion_phase",
        "progress": 100,
        "assessment_ready": True,
        "created_by": USER_IDS["engagement_manager"],
        "description": "Full discovery completed with all assessments ready",
    },
    {
        "id": FLOW_IDS["field_mapping"],
        "name": "In Progress - Field Mapping Phase",
        "flow_type": "standard_discovery",
        "state": "in_progress",
        "current_phase": "field_mapping_phase",
        "progress": 45,
        "assessment_ready": False,
        "created_by": USER_IDS["analyst"],
        "description": "Currently mapping fields from imported data",
    },
    {
        "id": FLOW_IDS["asset_inventory"],
        "name": "Asset Inventory Building",
        "flow_type": "asset_focused",
        "state": "in_progress",
        "current_phase": "asset_intelligence_phase",
        "progress": 65,
        "assessment_ready": False,
        "created_by": USER_IDS["analyst"],
        "description": "Building comprehensive asset inventory",
    },
    {
        "id": FLOW_IDS["failed_import"],
        "name": "Failed Import - Data Quality Issues",
        "flow_type": "quick_discovery",
        "state": "failed",
        "current_phase": "data_import_phase",
        "progress": 15,
        "assessment_ready": False,
        "created_by": USER_IDS["engagement_manager"],
        "error_message": "Data validation failed: Missing required columns",
        "description": "Import failed due to data quality issues",
    },
    {
        "id": FLOW_IDS["just_started"],
        "name": "New Discovery - Just Initialized",
        "flow_type": "standard_discovery",
        "state": "in_progress",
        "current_phase": "initialization_phase",
        "progress": 5,
        "assessment_ready": False,
        "created_by": USER_IDS["client_admin"],
        "description": "Newly created discovery flow",
    },
]

# Data Import Details
IMPORTS = [
    {
        "id": IMPORT_IDS["csv_servers"],
        "flow_id": FLOW_IDS["complete"],
        "filename": "server_inventory.csv",
        "file_type": "csv",
        "import_type": "ASSET_INVENTORY",
        "status": "completed",
        "total_rows": 150,
        "processed_rows": 150,
        "failed_rows": 0,
        "created_by": USER_IDS["analyst"],
    },
    {
        "id": IMPORT_IDS["json_applications"],
        "flow_id": FLOW_IDS["field_mapping"],
        "filename": "application_catalog.json",
        "file_type": "json",
        "import_type": "BUSINESS_APPS",
        "status": "processing",
        "total_rows": 75,
        "processed_rows": 45,
        "failed_rows": 2,
        "created_by": USER_IDS["analyst"],
    },
    {
        "id": IMPORT_IDS["excel_dependencies"],
        "flow_id": FLOW_IDS["asset_inventory"],
        "filename": "app_dependencies.xlsx",
        "file_type": "excel",
        "import_type": "NETWORK_DATA",
        "status": "completed",
        "total_rows": 200,
        "processed_rows": 198,
        "failed_rows": 2,
        "created_by": USER_IDS["engagement_manager"],
    },
]

# Agent Learning Configuration
AGENT_LEARNING_CONFIG = {
    "learning_enabled": True,
    "learning_scope": "engagement",
    "memory_isolation_level": "client_account",
}

# Timestamps
BASE_TIMESTAMP = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

# Default password for demo users (should be hashed in actual seeding)
DEFAULT_PASSWORD = os.getenv(
    "DEMO_SEED_PASSWORD", "DemoPassword123!"
)  # nosec B105 - Default only for development/seeding

# API Keys and Tokens (for demo purposes)
DEMO_API_KEY = "demo_api_key_" + str(
    DEMO_CLIENT_ID
)  # nosec B105 - Demo/test API key for seeding
DEMO_ACCESS_TOKEN = "demo_token_" + str(
    DEMO_ENGAGEMENT_ID
)  # nosec B105 - Demo/test token for seeding
