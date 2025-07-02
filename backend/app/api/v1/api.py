"""
Main API router for the AI Force Migration Platform.
Includes all endpoint routers and API versioning.
"""

from fastapi import APIRouter, Depends
import logging

from app.api.v1.endpoints import (
    sixr_router,
    discovery_router,
    asset_inventory_router,
    monitoring_router,
    chat_router,
    agent_learning_router,
    data_import_router,
    context_router,
    test_discovery_router,
    agents_router,
)

# Admin endpoints
try:
    from app.api.v1.admin.security_monitoring_handlers.security_audit_handler import router as security_audit_router
    from app.api.v1.admin.platform_admin_handlers import router as platform_admin_router
    from app.api.v1.admin.user_management_handlers.user_approval_handler import router as user_approval_router
    ADMIN_ENDPOINTS_AVAILABLE = True
except ImportError as e:
    ADMIN_ENDPOINTS_AVAILABLE = False
    logging.warning(f"Admin endpoints not available: {e}")

# Legacy Discovery Flow Management - DISABLED (replaced by V2 Discovery Flow API)
# from app.api.v1.endpoints.discovery_flow_management import router as discovery_flow_management_router
# from app.api.v1.endpoints.discovery_flow_management_enhanced import router as discovery_flow_management_enhanced_router

# V2 Discovery Flow API - MOVED TO /api/v2/ for proper versioning
# try:
#     from app.api.v1.discovery_flow_v2 import router as discovery_flow_v2_router
#     DISCOVERY_FLOW_V2_AVAILABLE = True
# except ImportError:
#     DISCOVERY_FLOW_V2_AVAILABLE = False

# Import only existing endpoint files
from app.api.v1.endpoints.context_establishment import router as context_establishment_router

# Legacy Unified Discovery Flow API (REMOVED - consolidated into /discovery)
# from app.api.v1.unified_discovery import router as unified_discovery_router
UNIFIED_DISCOVERY_AVAILABLE = False  # Disabled - use /discovery instead

# Assessment endpoints
try:
    from app.api.v1.endpoints.assess import router as assess_router
    ASSESS_AVAILABLE = True
except ImportError:
    ASSESS_AVAILABLE = False

# Wave Planning endpoints
try:
    from app.api.v1.endpoints.wave_planning import router as wave_planning_router
    WAVE_PLANNING_AVAILABLE = True
except ImportError:
    WAVE_PLANNING_AVAILABLE = False

# Import the /me endpoint function for root-level access
from app.api.v1.endpoints.context import get_user_context
from app.core.database import get_db
from app.api.v1.auth.auth_utils import get_current_user
from app.schemas.context import UserContext

# Missing endpoint files - functionality may be available through other routers:
# - assessment (functionality may be in sixr_analysis)
# - migration (functionality may be in migrations.py)
# - admin (functionality may be in admin directory)
# - observability (functionality may be in monitoring)
# - agent_ui_bridge (may be separate service)
# - rbac_endpoints (may be in auth directory)
# - rbac_admin (may be in auth directory)

# Check for additional routers in subdirectories
try:
    from app.api.v1.endpoints.migrations import router as migrations_router
    MIGRATIONS_AVAILABLE = True
except ImportError:
    MIGRATIONS_AVAILABLE = False

try:
    from app.api.v1.endpoints.health import router as health_router
    HEALTH_AVAILABLE = True
except ImportError:
    HEALTH_AVAILABLE = False

try:
    from app.api.v1.endpoints.llm_health import router as llm_health_router
    LLM_HEALTH_AVAILABLE = True
except ImportError:
    LLM_HEALTH_AVAILABLE = False
try:
    from app.api.v1.endpoints.observability import router as observability_router
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False


try:
    from app.api.v1.endpoints.observability import router as observability_router
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# Admin Routers
try:
    from app.api.v1.admin.client_management import router as client_management_router
    CLIENT_MANAGEMENT_AVAILABLE = True
except ImportError:
    CLIENT_MANAGEMENT_AVAILABLE = False

try:
    from app.api.v1.admin.engagement_management import export_router as engagement_management_router
    ENGAGEMENT_MANAGEMENT_AVAILABLE = True
except ImportError:
    ENGAGEMENT_MANAGEMENT_AVAILABLE = False

try:
    from app.api.v1.admin.platform_admin_handlers import router as platform_admin_router
    PLATFORM_ADMIN_AVAILABLE = True
except ImportError:
    PLATFORM_ADMIN_AVAILABLE = False

try:
    from app.api.v1.auth.handlers.user_management_handlers import user_management_router as user_approvals_router
    USER_APPROVALS_AVAILABLE = True
except ImportError:
    USER_APPROVALS_AVAILABLE = False

try:
    from app.api.v1.auth.rbac import router as auth_router
    AUTH_RBAC_AVAILABLE = True
except ImportError:
    AUTH_RBAC_AVAILABLE = False

try:
    from app.api.v1.master_flows import router as master_flows_router
    MASTER_FLOWS_AVAILABLE = True
except ImportError:
    MASTER_FLOWS_AVAILABLE = False

try:
    from app.api.v1.endpoints.simple_admin import simple_admin_router
    SIMPLE_ADMIN_AVAILABLE = True
except ImportError:
    SIMPLE_ADMIN_AVAILABLE = False

try:
    from app.api.v1.auth.handlers.admin_handlers import admin_router
    ADMIN_HANDLERS_AVAILABLE = True
except ImportError:
    ADMIN_HANDLERS_AVAILABLE = False



# Setup logger
logger = logging.getLogger(__name__)

# --- API Router Setup ---
api_router = APIRouter()

# Add direct /me endpoint at root level (required for frontend authentication flow)
@api_router.get(
    "/me",
    response_model=UserContext,
    summary="Get current user context",
    description="Get complete context for the current user including client, engagement, and session."
)
async def get_me_endpoint(
    db = Depends(get_db),
    current_user = Depends(get_current_user)
) -> UserContext:
    """Direct /me endpoint at root level for frontend authentication."""
    return await get_user_context(db=db, current_user=current_user)

# --- Include All Routers ---
logger.info("--- Starting API Router Inclusion Process ---")

# Core Discovery and Analysis
api_router.include_router(sixr_router, prefix="/6r", tags=["6R Analysis"])

# Unified Discovery API (Single Source of Truth)
try:
    from app.api.v1.unified_discovery_api import router as unified_discovery_api_router
    api_router.include_router(unified_discovery_api_router, prefix="/discovery", tags=["Discovery - Unified API"])
    logger.info("✅ Unified Discovery API router included at /discovery")
    UNIFIED_DISCOVERY_API_AVAILABLE = True
except ImportError as e:
    # Fallback to legacy discovery router
    api_router.include_router(discovery_router, prefix="/discovery", tags=["Discovery - Legacy"])
    logger.warning(f"⚠️ Unified Discovery API not available ({e}), using legacy discovery router")
    UNIFIED_DISCOVERY_API_AVAILABLE = False

# Legacy Unified Discovery Flow endpoints (REMOVED - redirects to /discovery)
# Old /unified-discovery endpoints have been consolidated into /discovery
logger.info("✅ Legacy /unified-discovery endpoints consolidated into /discovery")

# V2 Discovery Flow Management - MOVED TO /api/v2/ for proper versioning
# if DISCOVERY_FLOW_V2_AVAILABLE:
#     api_router.include_router(discovery_flow_v2_router, prefix="/discovery-flows-v2", tags=["Discovery Flow v2"])
#     logger.info("✅ Discovery Flow V2 router included at /discovery-flows-v2")
# else:
#     logger.warning("⚠️ Discovery Flow V2 router not available")

# Migrations if available
if MIGRATIONS_AVAILABLE:
    api_router.include_router(migrations_router, prefix="/migration", tags=["Migration"])
    logger.info("✅ Migrations router included")

# Health endpoints
if HEALTH_AVAILABLE:
    api_router.include_router(health_router, prefix="/health", tags=["Health"])
    logger.info("✅ Health router included")

if LLM_HEALTH_AVAILABLE:
    api_router.include_router(llm_health_router, prefix="/llm", tags=["LLM Health"])
    logger.info("✅ LLM Health router included")
# Observability and System Control
if OBSERVABILITY_AVAILABLE:
    api_router.include_router(observability_router, prefix="/observability", tags=["Observability"])
    logger.info("✅ Observability router included")
else:
    logger.warning("⚠️ Observability router not available - polling control endpoints disabled")


# Observability and System Control
if OBSERVABILITY_AVAILABLE:
    api_router.include_router(observability_router, prefix="/observability", tags=["Observability"])
    logger.info("✅ Observability router included")
else:
    logger.warning("⚠️ Observability router not available - polling control endpoints disabled")


# Authentication and Context
if AUTH_RBAC_AVAILABLE:
    api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    logger.info("✅ Auth RBAC router included")

# Master Flow Coordination
if MASTER_FLOWS_AVAILABLE:
    api_router.include_router(master_flows_router, prefix="/master-flows", tags=["Master Flow Coordination"])
    logger.info("✅ Master Flows router included")
else:
    logger.warning("⚠️ Master Flows router not available")

api_router.include_router(context_router, prefix="/context", tags=["Context Management"])

# Discovery Crew Escalation API (Task 2.3)
try:
    from app.api.v1.endpoints.discovery_escalation import router as escalation_router
    api_router.include_router(escalation_router, prefix="/discovery", tags=["Discovery Crew Escalation"])
    logger.info("✅ Discovery Crew Escalation router included")
except ImportError as e:
    logger.warning(f"⚠️ Discovery Crew Escalation router not available: {e}")

# Performance Monitoring API (Task 4.3)
try:
    from app.api.v1.endpoints.performance.monitoring import router as performance_monitoring_router
    api_router.include_router(performance_monitoring_router, prefix="/performance", tags=["Performance Monitoring"])
    logger.info("✅ Performance Monitoring router included")
except ImportError as e:
    logger.warning(f"⚠️ Performance Monitoring router not available: {e}")
api_router.include_router(context_establishment_router, prefix="/context-establishment", tags=["Context Establishment"])

# Assessment Management
if ASSESS_AVAILABLE:
    api_router.include_router(assess_router, prefix="/assess", tags=["Assessment"])
    logger.info("✅ Assessment router included")
else:
    logger.warning("⚠️ Assessment router not available")

if WAVE_PLANNING_AVAILABLE:
    api_router.include_router(wave_planning_router, prefix="/ave-planning", tags=["Wave Planning"])
    logger.info("✅ Wave Planning router included")
else:
    logger.warning("⚠️ Wave Planning router not available")

# Data Management
api_router.include_router(data_import_router, prefix="/data-import", tags=["Data Import"])
api_router.include_router(asset_inventory_router, prefix="/assets", tags=["Asset Inventory"])

# System Management
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring"])

# Agent and AI Services
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_router.include_router(agent_learning_router, prefix="/agent-learning", tags=["Agent Learning"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])

# Flow Processing Agent (Central routing for all flow continuations)
try:
    from app.api.v1.endpoints.flow_processing import router as flow_processing_router
    api_router.include_router(flow_processing_router, prefix="/flow-processing", tags=["Flow Processing Agent"])
    logger.info("✅ Flow Processing Agent router included")
except ImportError as e:
    logger.warning(f"⚠️ Flow Processing Agent router not available: {e}")

# Session Management - REMOVED (use flow_id instead)

# Admin Management (conditional)
if CLIENT_MANAGEMENT_AVAILABLE:
    api_router.include_router(client_management_router, prefix="/admin/clients", tags=["Admin - Client Management"])
    logger.info("✅ Client management router included")

if ENGAGEMENT_MANAGEMENT_AVAILABLE:
    api_router.include_router(engagement_management_router, prefix="/admin/engagements", tags=["Admin - Engagement Management"])
    logger.info("✅ Engagement management router included")

if PLATFORM_ADMIN_AVAILABLE:
    api_router.include_router(platform_admin_router, prefix="/admin/platform", tags=["Admin - Platform Management"])
    logger.info("✅ Platform admin router included")

if USER_APPROVALS_AVAILABLE:
    api_router.include_router(user_approvals_router, prefix="/admin/approvals", tags=["Admin - User Approvals"])
    logger.info("✅ User approvals router included")

# Security monitoring endpoints
if ADMIN_ENDPOINTS_AVAILABLE:
    api_router.include_router(security_audit_router, prefix="/admin", tags=["Admin - Security Monitoring"])
    logger.info("✅ Security audit router included")

# Admin handlers are already included through the auth router (rbac.py)
# No need to include admin_router separately - it would create duplicate routes

if SIMPLE_ADMIN_AVAILABLE:
    api_router.include_router(simple_admin_router, prefix="/api/v1", tags=["Simple Admin"])
    logger.info("✅ Simple admin router included")
else:
    logger.warning("⚠️ Simple admin router not available")

# Testing and Debug
api_router.include_router(test_discovery_router, prefix="/test-discovery", tags=["Test Discovery"])

# Legacy Discovery Flow Management - DISABLED (replaced by V2 Discovery Flow API at /api/v2/discovery-flows/)
# api_router.include_router(discovery_flow_management_router, prefix="/discovery", tags=["Discovery Flow Management"])
# api_router.include_router(discovery_flow_management_enhanced_router, prefix="/discovery/enhanced", tags=["Enhanced Flow Management"])

# Debug endpoint to list all routes
@api_router.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    """Debug endpoint to list all registered routes."""
    routes = []
    for route in api_router.routes:
        routes.append({
            "path": route.path,
            "name": getattr(route, "name", ""),
            "methods": getattr(route, "methods", [])
        })
    return {"routes": routes}

logger.info("--- Finished API Router Inclusion Process ---")