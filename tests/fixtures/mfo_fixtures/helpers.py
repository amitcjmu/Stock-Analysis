"""
Helper functions for MFO test setup and utilities.

Provides utility functions for creating test contexts, linked flow data, and test environments.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from .base import DEMO_CLIENT_ACCOUNT_ID, DEMO_ENGAGEMENT_ID, DEMO_USER_ID, MockRequestContext


def create_mock_mfo_context(
    client_account_id: str = DEMO_CLIENT_ACCOUNT_ID,
    engagement_id: str = DEMO_ENGAGEMENT_ID,
    user_id: str = DEMO_USER_ID,
) -> MockRequestContext:
    """Create a mock MFO request context with proper tenant scoping."""
    return MockRequestContext(
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
    )


def create_linked_flow_data(
    flow_type: str = "discovery", flow_status: str = "initialized"
) -> Dict[str, Dict[str, Any]]:
    """Create properly linked master and child flow data."""
    master_flow_id = str(uuid.uuid4())
    child_flow_id = str(uuid.uuid4())

    master_flow = {
        "flow_id": master_flow_id,
        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
        "engagement_id": DEMO_ENGAGEMENT_ID,
        "user_id": DEMO_USER_ID,
        "flow_type": flow_type,
        "flow_status": flow_status,
        "flow_configuration": {},
        "created_at": datetime.now(timezone.utc),
    }

    child_flow = {
        "id": str(uuid.uuid4()),
        "flow_id": child_flow_id,
        "master_flow_id": master_flow_id,  # Proper FK reference
        "client_account_id": DEMO_CLIENT_ACCOUNT_ID,
        "engagement_id": DEMO_ENGAGEMENT_ID,
        "user_id": DEMO_USER_ID,
        "status": "active" if flow_status == "running" else "initialized",
        "created_at": datetime.now(timezone.utc),
    }

    return {
        "master_flow": master_flow,
        "child_flow": child_flow,
        "master_flow_id": master_flow_id,
        "child_flow_id": child_flow_id,
    }


async def setup_mfo_test_environment(
    session: AsyncSession, context: MockRequestContext, flow_type: str = "discovery"
) -> Dict[str, Any]:
    """Setup a complete MFO test environment with linked flows."""
    # This would create actual database records in a real implementation
    # For now, return mock data structure

    flow_data = create_linked_flow_data(flow_type=flow_type)

    # In real implementation:
    # 1. Create master flow record
    # 2. Create child flow record with proper FK
    # 3. Setup agent pool for tenant
    # 4. Initialize flow state

    return {
        "context": context,
        "flows": flow_data,
        "session": session,
        "setup_complete": True,
    }
