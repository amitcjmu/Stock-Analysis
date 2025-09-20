"""
Flow-related pytest fixtures for MFO testing.

Provides fixtures for master flows, child flows, and flow state data.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from .base import DEMO_CLIENT_ACCOUNT_ID, DEMO_ENGAGEMENT_ID, DEMO_USER_ID, DISCOVERY_PHASES


@pytest.fixture
def sample_master_flow_data() -> Dict[str, Any]:
    """Sample master flow data for testing MFO operations."""
    return {
        "flow_id": str(uuid.uuid4()),
        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
        "engagement_id": DEMO_ENGAGEMENT_ID,
        "user_id": DEMO_USER_ID,
        "flow_type": "discovery",
        "flow_status": "initialized",
        "flow_configuration": {"auto_advance": True, "notification_email": "demo@demo-corp.com"},
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_discovery_flow_data() -> Dict[str, Any]:
    """Sample discovery flow data linked to master flow."""
    return {
        "id": str(uuid.uuid4()),
        "flow_id": str(uuid.uuid4()),
        "master_flow_id": str(uuid.uuid4()),  # Would be linked to actual master flow
        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
        "engagement_id": DEMO_ENGAGEMENT_ID,
        "user_id": DEMO_USER_ID,
        "status": "active",
        "current_phase": "data_import",
        "progress_percentage": 0.0,
        "phases_completed": [],
        "data_import_completed": False,
        "field_mapping_completed": False,
        "data_cleansing_completed": False,
        "asset_inventory_completed": False,
        "dependency_analysis_completed": False,
        "assessment_ready": False,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def mfo_flow_states() -> Dict[str, Dict[str, Any]]:
    """Predefined flow states for different testing scenarios."""
    base_time = datetime.now(timezone.utc)

    return {
        "initialized": {
            "master_flow": {
                "flow_id": str(uuid.uuid4()),
                "flow_status": "initialized",
                "flow_type": "discovery",
                "created_at": base_time,
            },
            "child_flow": {
                "flow_id": str(uuid.uuid4()),
                "status": "active",
                "current_phase": None,
                "progress_percentage": 0.0,
                "phases_completed": [],
            },
        },
        "running_data_import": {
            "master_flow": {
                "flow_id": str(uuid.uuid4()),
                "flow_status": "running",
                "flow_type": "discovery",
                "created_at": base_time,
            },
            "child_flow": {
                "flow_id": str(uuid.uuid4()),
                "status": "active",
                "current_phase": "data_import",
                "progress_percentage": 25.0,
                "phases_completed": [],
                "data_import_completed": False,
            },
        },
        "running_field_mapping": {
            "master_flow": {
                "flow_id": str(uuid.uuid4()),
                "flow_status": "running",
                "flow_type": "discovery",
                "created_at": base_time,
            },
            "child_flow": {
                "flow_id": str(uuid.uuid4()),
                "status": "active",
                "current_phase": "field_mapping",
                "progress_percentage": 50.0,
                "phases_completed": ["data_import"],
                "data_import_completed": True,
                "field_mapping_completed": False,
            },
        },
        "completed": {
            "master_flow": {
                "flow_id": str(uuid.uuid4()),
                "flow_status": "completed",
                "flow_type": "discovery",
                "created_at": base_time,
                "updated_at": base_time,
            },
            "child_flow": {
                "flow_id": str(uuid.uuid4()),
                "status": "completed",
                "current_phase": None,
                "progress_percentage": 100.0,
                "phases_completed": DISCOVERY_PHASES,
                "data_import_completed": True,
                "field_mapping_completed": True,
                "data_cleansing_completed": True,
                "asset_inventory_completed": True,
                "dependency_analysis_completed": True,
                "assessment_ready": True,
            },
        },
        "paused": {
            "master_flow": {
                "flow_id": str(uuid.uuid4()),
                "flow_status": "paused",
                "flow_type": "discovery",
                "created_at": base_time,
            },
            "child_flow": {
                "flow_id": str(uuid.uuid4()),
                "status": "paused",
                "current_phase": "field_mapping",
                "progress_percentage": 40.0,
                "phases_completed": ["data_import"],
                "data_import_completed": True,
                "field_mapping_completed": False,
            },
        },
        "failed": {
            "master_flow": {
                "flow_id": str(uuid.uuid4()),
                "flow_status": "failed",
                "flow_type": "discovery",
                "created_at": base_time,
                "error_details": {"code": "AGENT_TIMEOUT", "message": "Agent execution timeout"},
            },
            "child_flow": {
                "flow_id": str(uuid.uuid4()),
                "status": "failed",
                "current_phase": "data_import",
                "progress_percentage": 10.0,
                "phases_completed": [],
                "error_details": {"phase": "data_import", "attempt": 3},
            },
        },
    }
