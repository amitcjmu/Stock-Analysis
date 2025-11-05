"""
Router registration utilities for the v1 API.
This module handles the registration of all routers to reduce complexity
in the main api.py file.

This package is modularized to maintain file length under 400 lines per module.
"""

import logging
from fastapi import APIRouter

from .core_routers import register_core_routers
from .conditional_routers import register_conditional_routers
from .utility_routers import register_utility_routers
from .admin_routers import register_admin_routers
from .auth_routers import register_auth_routers
from .special_routers import register_special_routers

logger = logging.getLogger(__name__)


def register_all_routers(api_router: APIRouter):
    """Register all routers in organized groups."""
    # Validate endpoint migration mappings on startup
    try:
        from app.utils.endpoint_migration_logger import validate_endpoint_migration

        validate_endpoint_migration()
    except ImportError as e:
        logger.warning(f"Endpoint migration validation skipped: {e}")

    register_core_routers(api_router)
    register_conditional_routers(api_router)
    register_utility_routers(api_router)
    register_admin_routers(api_router)
    register_auth_routers(api_router)
    register_special_routers(api_router)
    logger.info("--- Router Registration Complete ---")


# Export individual registration functions for backward compatibility
__all__ = [
    "register_all_routers",
    "register_core_routers",
    "register_conditional_routers",
    "register_utility_routers",
    "register_admin_routers",
    "register_auth_routers",
    "register_special_routers",
]
