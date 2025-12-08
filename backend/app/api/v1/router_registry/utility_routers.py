"""
Utility router registration for the v1 API.
Contains system, health, monitoring, and observability routers.
"""

import logging
import os
from fastapi import APIRouter

logger = logging.getLogger(__name__)


def register_utility_routers(api_router: APIRouter):
    """Register utility and system routers."""
    from app.api.v1.router_imports import (
        routers_with_flags,
        API_HEALTH_AVAILABLE,
        api_health_router,
    )

    logger.info("--- Registering Utility Routers ---")

    # API Health endpoints
    if API_HEALTH_AVAILABLE:
        api_router.include_router(api_health_router, prefix="/api-health")
        logger.info("✅ API Health router included")

    # Test Diagnostics endpoints (for E2E testing only)
    if os.getenv("E2E_TEST_MODE", "false").lower() == "true":
        try:
            from app.api.v1.endpoints.test_diagnostics import (
                router as test_diagnostics_router,
            )

            api_router.include_router(test_diagnostics_router, prefix="/test")
            logger.info(
                "✅ Test Diagnostics router included at /test (E2E testing only)"
            )
        except ImportError as e:
            logger.warning(f"Test Diagnostics router import failed: {e}")
    else:
        logger.debug("Test Diagnostics router not enabled (E2E_TEST_MODE not set)")

    # Health endpoints
    if routers_with_flags.get("HEALTH", (False, None))[0]:
        health_router = routers_with_flags["HEALTH"][1]
        api_router.include_router(health_router, prefix="/health")
        logger.info("✅ Health router included")

    if routers_with_flags.get("LLM_HEALTH", (False, None))[0]:
        llm_health_router = routers_with_flags["LLM_HEALTH"][1]
        api_router.include_router(llm_health_router, prefix="/llm")
        logger.info("✅ LLM Health router included")

    # Data Cleansing endpoints
    if routers_with_flags.get("DATA_CLEANSING", (False, None))[0]:
        data_cleansing_router = routers_with_flags["DATA_CLEANSING"][1]
        api_router.include_router(data_cleansing_router)
        logger.info("✅ Data Cleansing router included (prefix removed)")

        # Backward compatibility
        api_router.include_router(data_cleansing_router, prefix="/data-cleansing")
        logger.info("✅ Data Cleansing legacy compatibility router included")
    else:
        logger.warning("⚠️ Data Cleansing router not available")

    # Observability
    if routers_with_flags.get("OBSERVABILITY", (False, None))[0]:
        observability_router = routers_with_flags["OBSERVABILITY"][1]
        api_router.include_router(observability_router, prefix="/observability")
        logger.info("✅ Observability router included")
    else:
        logger.warning("⚠️ Observability router not available")

    # Audit logging endpoint
    try:
        from app.api.v1.endpoints.audit import router as audit_router

        api_router.include_router(audit_router)
        logger.info("✅ Audit router included")
    except ImportError as e:
        logger.warning(f"Audit router import failed: {e}")
