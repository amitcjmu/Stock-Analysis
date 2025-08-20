"""
Service utilities for discovery agent status handlers.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.security.secure_logging import safe_log_format
from app.core.database import get_db
from app.services.discovery_flow_service import DiscoveryFlowService

logger = logging.getLogger(__name__)


class MockDiscoveryFlowService:
    """Mock service for graceful degradation when Discovery Flow service is unavailable."""

    async def get_active_flows(self):
        return []

    async def get_flow_statistics(self):
        return {
            "total_flows": 0,
            "completed_flows": 0,
            "in_progress_flows": 0,
        }


# Dependency injection for CrewAI Flow Service
async def get_crewai_flow_service(
    db: AsyncSession = Depends(get_db),
) -> DiscoveryFlowService:
    """Provide a Discovery Flow Service per request to avoid memory leaks."""
    try:
        # Create new instance per request to prevent caching issues
        # This avoids memory leaks from caching by session ID
        return DiscoveryFlowService(db=db)
    except Exception as e:
        logger.warning(safe_log_format("Discovery Flow service unavailable: {e}", e=e))
        return MockDiscoveryFlowService()
