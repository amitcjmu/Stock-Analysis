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

# Cache for CrewAI service to avoid repeated initialization
_crewai_service_cache = {}


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


# Dependency injection for CrewAI Flow Service with caching
async def get_crewai_flow_service(
    db: AsyncSession = Depends(get_db),
) -> DiscoveryFlowService:
    """Cached Discovery Flow Service to avoid repeated initialization."""
    try:
        # Use database session ID as cache key
        cache_key = f"discovery_flow_service_{id(db)}"

        if cache_key not in _crewai_service_cache:
            _crewai_service_cache[cache_key] = DiscoveryFlowService(db=db)

        return _crewai_service_cache[cache_key]
    except Exception as e:
        logger.warning(safe_log_format("Discovery Flow service unavailable: {e}", e=e))
        return MockDiscoveryFlowService()


def clear_crewai_service_cache():
    """Clear the CrewAI service cache. Useful for testing or service resets."""
    _crewai_service_cache.clear()
    logger.info("CrewAI service cache cleared")
