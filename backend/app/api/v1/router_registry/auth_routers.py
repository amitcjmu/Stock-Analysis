"""
Authentication router registration for the v1 API.
Contains authentication and RBAC routers.
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)


def register_auth_routers(api_router: APIRouter):
    """Register authentication routers."""
    from app.api.v1.router_imports import routers_with_flags

    logger.info("--- Registering Auth Routers ---")

    if routers_with_flags.get("AUTH_RBAC", (False, None))[0]:
        auth_router = routers_with_flags["AUTH_RBAC"][1]
        api_router.include_router(auth_router, prefix="/auth")
        logger.info("✅ Auth RBAC router included")
    else:
        logger.warning("⚠️ Auth RBAC router not available")
