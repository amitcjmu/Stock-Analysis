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
    logger.info(
        f"Auth router flag status: {routers_with_flags.get('AUTH_RBAC', (False, None))}"
    )

    auth_flag = routers_with_flags.get("AUTH_RBAC", (False, None))
    if auth_flag[0] and auth_flag[1] is not None:
        auth_router = auth_flag[1]
        logger.info(
            f"Including auth router: {auth_router}, routes: {[r.path for r in auth_router.routes]}"
        )
        api_router.include_router(auth_router, prefix="/auth")
        logger.info("✅ Auth RBAC router included at /auth")
    else:
        logger.warning(
            f"⚠️ Auth RBAC router not available from router_imports. Flag: {auth_flag}"
        )
        # Fallback: Try direct import
        try:
            from app.api.v1.auth import auth_router as direct_auth_router

            logger.info("✅ Direct auth router import successful, registering...")
            api_router.include_router(direct_auth_router, prefix="/auth")
            logger.info("✅ Auth RBAC router registered via direct import at /auth")
        except Exception as e:
            logger.error(
                f"❌ Failed to register auth router via direct import: {e}",
                exc_info=True,
            )
