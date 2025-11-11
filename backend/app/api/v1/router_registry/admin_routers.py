"""
Admin router registration for the v1 API.
Contains admin, security, and management routers.
"""

import logging
from fastapi import APIRouter

from app.api.v1.api_tags import APITags

logger = logging.getLogger(__name__)


def register_admin_routers(api_router: APIRouter):
    """Register admin and security routers."""
    from app.api.v1.router_imports import (
        ADMIN_ENDPOINTS_AVAILABLE,
        platform_admin_router,
        security_audit_router,
        llm_usage_router,
        memory_management_router,
        routers_with_flags,
    )
    from app.api.v1.endpoints.admin_flows import router as admin_flows_router

    logger.info("--- Registering Admin Routers ---")

    # Platform Admin
    if ADMIN_ENDPOINTS_AVAILABLE:
        api_router.include_router(platform_admin_router, prefix="/admin/platform")
        logger.info("✅ Platform Admin router included")

        api_router.include_router(security_audit_router, prefix="/admin/security/audit")
        logger.info("✅ Security Audit router included")

        api_router.include_router(
            llm_usage_router, prefix="/admin/llm-usage", tags=[APITags.ADMIN_LLM_USAGE]
        )
        logger.info("✅ LLM Usage router included")

        api_router.include_router(memory_management_router, tags=[APITags.ADMIN])
        logger.info("✅ Memory Management router included")
    else:
        logger.warning("⚠️ Platform Admin routers not available")

    # Admin Flow Management (Bug #651 fix - cleanup stale flows)
    api_router.include_router(admin_flows_router, prefix="/admin", tags=[APITags.ADMIN])
    logger.info("✅ Admin Flow Management router included")

    # RBAC Admin
    if routers_with_flags.get("RBAC_ADMIN", (False, None))[0]:
        rbac_admin_router = routers_with_flags["RBAC_ADMIN"][1]
        api_router.include_router(rbac_admin_router, prefix="/admin/rbac")
        logger.info("✅ RBAC Admin router included")
    else:
        logger.warning("⚠️ RBAC Admin router not available")

    # Client Management Admin
    if routers_with_flags.get("CLIENT_MANAGEMENT", (False, None))[0]:
        client_management_router = routers_with_flags["CLIENT_MANAGEMENT"][1]
        api_router.include_router(client_management_router, prefix="/admin/clients")
        logger.info("✅ Client Management router included")
    else:
        logger.warning("⚠️ Client Management router not available")

    # Engagement Management Admin
    if routers_with_flags.get("ENGAGEMENT_MANAGEMENT", (False, None))[0]:
        engagement_management_router = routers_with_flags["ENGAGEMENT_MANAGEMENT"][1]
        api_router.include_router(
            engagement_management_router, prefix="/admin/engagements"
        )
        logger.info("✅ Engagement Management router included")
    else:
        logger.warning("⚠️ Engagement Management router not available")

    # Flow Comparison Admin
    if routers_with_flags.get("FLOW_COMPARISON", (False, None))[0]:
        flow_comparison_router = routers_with_flags["FLOW_COMPARISON"][1]
        api_router.include_router(
            flow_comparison_router, prefix="/admin/flow-comparison"
        )
        logger.info("✅ Flow Comparison router included")
    else:
        logger.warning("⚠️ Flow Comparison router not available")

    # User Approvals
    if routers_with_flags.get("USER_APPROVALS", (False, None))[0]:
        user_approvals_router = routers_with_flags["USER_APPROVALS"][1]
        api_router.include_router(user_approvals_router, prefix="/admin/user-approvals")
        logger.info("✅ User Approvals router included")
    else:
        logger.warning("⚠️ User Approvals router not available")

    # Simple Admin
    if routers_with_flags.get("SIMPLE_ADMIN", (False, None))[0]:
        simple_admin_router = routers_with_flags["SIMPLE_ADMIN"][1]
        api_router.include_router(simple_admin_router)
        logger.info("✅ Simple Admin router included")
    else:
        logger.warning("⚠️ Simple Admin router not available")

    # Rate Limiting Admin
    if routers_with_flags.get("RATE_LIMITING", (False, None))[0]:
        rate_limiting_router = routers_with_flags["RATE_LIMITING"][1]
        api_router.include_router(rate_limiting_router, prefix="/admin/rate-limiting")
        logger.info("✅ Rate Limiting router included")
    else:
        logger.warning("⚠️ Rate Limiting router not available")

    # User Access Management Admin
    if routers_with_flags.get("ADMIN_USER_ACCESS", (False, None))[0]:
        admin_user_access_router = routers_with_flags["ADMIN_USER_ACCESS"][1]
        api_router.include_router(admin_user_access_router, prefix="/admin/user-access")
        logger.info("✅ Admin User Access router included")
    else:
        logger.warning("⚠️ Admin User Access router not available")
