"""
Base constants and classes for MFO test fixtures.

Contains core constants, mock classes, and shared data structures.
"""

from typing import Dict
from unittest.mock import AsyncMock, MagicMock

# Demo tenant constants
DEMO_CLIENT_ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_ENGAGEMENT_ID = "22222222-2222-2222-2222-222222222222"
DEMO_USER_ID = "33333333-3333-3333-3333-333333333333"
DEMO_USER_EMAIL = "demo@demo-corp.com"

# Flow type constants
FLOW_TYPES = ["discovery", "assessment", "collection", "planning"]
FLOW_STATUSES = ["initialized", "running", "paused", "completed", "failed", "error"]
DISCOVERY_PHASES = ["data_import", "field_mapping", "data_cleansing", "asset_inventory", "dependency_analysis"]


class MockRequestContext:
    """Mock request context for MFO operations with proper tenant scoping."""

    def __init__(
        self,
        client_account_id: str = DEMO_CLIENT_ACCOUNT_ID,
        engagement_id: str = DEMO_ENGAGEMENT_ID,
        user_id: str = DEMO_USER_ID,
        user_email: str = DEMO_USER_EMAIL,
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id
        self.user_email = user_email
        self.tenant_id = client_account_id  # Alias for convenience

    def to_dict(self) -> Dict[str, str]:
        """Convert context to dictionary for request headers."""
        return {
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            "user_id": self.user_id,
            "user_email": self.user_email,
        }

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for tenant scoping."""
        return {
            "X-Client-Account-ID": self.client_account_id,
            "X-Engagement-ID": self.engagement_id,
            "X-User-ID": self.user_id,
            "X-User-Email": self.user_email,
        }


class MockServiceRegistry:
    """Mock service registry for MFO operations."""

    def __init__(self):
        self.master_flow_orchestrator = MagicMock()
        self.discovery_flow_repository = MagicMock()
        self.assessment_flow_repository = MagicMock()
        self.collection_flow_repository = MagicMock()
        self.tenant_scoped_agent_pool = MagicMock()

        # Setup common async mock behaviors
        self._setup_async_mocks()

    def _setup_async_mocks(self):
        """Setup async mock behaviors for common operations."""
        # Master Flow Orchestrator mocks
        self.master_flow_orchestrator.create_flow = AsyncMock()
        self.master_flow_orchestrator.get_flow = AsyncMock()
        self.master_flow_orchestrator.start_phase = AsyncMock()
        self.master_flow_orchestrator.complete_phase = AsyncMock()
        self.master_flow_orchestrator.pause_flow = AsyncMock()
        self.master_flow_orchestrator.resume_flow = AsyncMock()

        # Repository mocks
        self.discovery_flow_repository.create = AsyncMock()
        self.discovery_flow_repository.get_by_flow_id = AsyncMock()
        self.discovery_flow_repository.update = AsyncMock()

        self.assessment_flow_repository.create = AsyncMock()
        self.assessment_flow_repository.get_by_flow_id = AsyncMock()
        self.assessment_flow_repository.update = AsyncMock()

        self.collection_flow_repository.create = AsyncMock()
        self.collection_flow_repository.get_by_flow_id = AsyncMock()
        self.collection_flow_repository.update = AsyncMock()

        # Agent pool mocks
        self.tenant_scoped_agent_pool.get_agent = AsyncMock()
        self.tenant_scoped_agent_pool.release_agent = AsyncMock()
