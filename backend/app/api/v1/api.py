"""
Main API router for the AI Modernize Migration Platform.
Includes all endpoint routers and API versioning.
"""

import logging

from fastapi import APIRouter, Depends

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints import (
    agent_learning_router,
    agents_router,
    analysis_router,
    assessment_events_router,
    assessment_flow_router,
    asset_inventory_router,
    chat_router,
    context_router,
    data_import_router,
    monitoring_router,
    sixr_router,
    test_discovery_router,
)

# Analysis endpoints (including queues)
try:
    from app.api.v1.endpoints.analysis import router as analysis_queues_router

    ANALYSIS_QUEUES_AVAILABLE = True
except ImportError:
    ANALYSIS_QUEUES_AVAILABLE = False
from app.api.v1.endpoints.context import get_user_context
from app.api.v1.endpoints.context_establishment import (
    router as context_establishment_router,
)
from app.api.v1.endpoints.flow_sync_debug import router as flow_sync_debug_router
from app.core.database import get_db
from app.schemas.context import UserContext

logger = logging.getLogger(__name__)

# Decommission endpoints
try:
    from app.api.v1.endpoints.decommission import router as decommission_router

    DECOMMISSION_AVAILABLE = True
except ImportError:
    DECOMMISSION_AVAILABLE = False

# Admin endpoints
try:
    from app.api.v1.admin.platform_admin_handlers import router as platform_admin_router
    from app.api.v1.admin.security_monitoring_handlers.security_audit_handler import (
        router as security_audit_router,
    )

    # user_approval_router removed - not used in this file

    ADMIN_ENDPOINTS_AVAILABLE = True
except ImportError as e:
    ADMIN_ENDPOINTS_AVAILABLE = False
    logging.warning(f"Admin endpoints not available: {e}")

# Legacy Discovery Flow Management - DISABLED (replaced by V2 Discovery Flow API)
# from app.api.v1.endpoints.discovery_flow_management import router as discovery_flow_management_router
# from app.api.v1.endpoints.discovery_flow_management_enhanced import \
#     router as discovery_flow_management_enhanced_router

# V2 Discovery Flow API - MOVED TO /api/v2/ for proper versioning
# try:
#     from app.api.v1.discovery_flow_v2 import router as discovery_flow_v2_router
#     DISCOVERY_FLOW_V2_AVAILABLE = True
# except ImportError:
#     DISCOVERY_FLOW_V2_AVAILABLE = False

# Import only existing endpoint files
# context_establishment_router already imported at top

# Unified Discovery Flow API - Master Flow Orchestrator Integration
try:
    from app.api.v1.endpoints.unified_discovery import (
        router as unified_discovery_router,
    )

    UNIFIED_DISCOVERY_AVAILABLE = True
except ImportError as e:
    UNIFIED_DISCOVERY_AVAILABLE = False
    logger.warning(f"Unified Discovery API not available: {e}")

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
# These imports are already at the top of the file

# Collection Flow endpoints
try:
    from app.api.v1.endpoints.collection import router as collection_router

    COLLECTION_AVAILABLE = True
except ImportError:
    COLLECTION_AVAILABLE = False
    # logger not available yet - will log later

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
    from app.api.v1.endpoints.data_cleansing import router as data_cleansing_router

    DATA_CLEANSING_AVAILABLE = True
except ImportError:
    DATA_CLEANSING_AVAILABLE = False
try:
    from app.api.v1.endpoints.observability import router as observability_router

    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

# Agent Events endpoints for real-time SSE communication
try:
    from app.api.v1.endpoints.agent_events import router as agent_events_router

    AGENT_EVENTS_AVAILABLE = True
except ImportError as e:
    AGENT_EVENTS_AVAILABLE = False
    logger.warning(f"Agent Events router not available: {e}")

# Observability router already imported above at line 146
# Removed duplicate import

# Admin Routers
try:
    from app.api.v1.admin.client_management import router as client_management_router

    CLIENT_MANAGEMENT_AVAILABLE = True
except ImportError:
    CLIENT_MANAGEMENT_AVAILABLE = False

try:
    from app.api.v1.admin.engagement_management import (
        export_router as engagement_management_router,
    )

    ENGAGEMENT_MANAGEMENT_AVAILABLE = True
except ImportError:
    ENGAGEMENT_MANAGEMENT_AVAILABLE = False

# platform_admin_router already imported above at line 37
# Check if it was successfully imported
PLATFORM_ADMIN_AVAILABLE = ADMIN_ENDPOINTS_AVAILABLE

try:
    from app.api.v1.admin.session_comparison import router as flow_comparison_router

    FLOW_COMPARISON_AVAILABLE = True
except ImportError:
    FLOW_COMPARISON_AVAILABLE = False

try:
    from app.api.v1.auth.handlers.user_management_handlers import (
        user_management_router as user_approvals_router,
    )

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

# admin_router import removed - see comment at line 555
# No need to include admin_router separately - it would create duplicate routes
ADMIN_HANDLERS_AVAILABLE = True

try:
    from app.api.v1.endpoints.flow_health import router as flow_health_router

    FLOW_HEALTH_AVAILABLE = True
except ImportError:
    FLOW_HEALTH_AVAILABLE = False


# Setup logger
logger = logging.getLogger(__name__)

# --- API Router Setup ---
api_router = APIRouter()


# Add direct /me endpoint at root level (required for frontend authentication flow)
@api_router.get(
    "/me",
    response_model=UserContext,
    summary="Get current user context",
    description="Get complete context for the current user including client, engagement, session, and active flows.",
)
async def get_me_endpoint(
    db=Depends(get_db), current_user=Depends(get_current_user)
) -> UserContext:
    """Direct /me endpoint at root level for frontend authentication."""
    return await get_user_context(db=db, current_user=current_user)


# --- Include All Routers ---
logger.info("--- Starting API Router Inclusion Process ---")

# Core Discovery and Analysis
api_router.include_router(sixr_router, prefix="/6r", tags=["6R Analysis"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])

# Analysis Queues (for batch 6R analysis)
if ANALYSIS_QUEUES_AVAILABLE:
    api_router.include_router(
        analysis_queues_router, prefix="/analysis", tags=["Analysis"]
    )
    logger.info("✅ Analysis Queues router included at /analysis/queues")
else:
    logger.warning("⚠️ Analysis Queues router not available")

# Discovery API - Implemented via Unified Discovery Flow + Master Flow Orchestrator
# Real CrewAI implementation available at /unified-discovery endpoint
logger.info("✅ Discovery API implemented via Unified Discovery Flow (real CrewAI)")

# Collection Flow API - ADCS with CrewAI agents
if COLLECTION_AVAILABLE:
    api_router.include_router(
        collection_router, prefix="/collection", tags=["Collection Flow"]
    )
    logger.info("✅ Collection Flow API router included at /collection")
else:
    logger.warning("⚠️ Collection Flow API router not available")

# Unified Discovery Flow API - Master Flow Orchestrator Integration
if UNIFIED_DISCOVERY_AVAILABLE:
    api_router.include_router(
        unified_discovery_router,
        prefix="/unified-discovery",
        tags=["Unified Discovery Flow"],
    )
    logger.info("✅ Unified Discovery Flow API router included at /unified-discovery")
else:
    logger.warning("⚠️ Unified Discovery Flow API router not available")

# V2 Discovery Flow Management - MOVED TO /api/v2/ for proper versioning
# if DISCOVERY_FLOW_V2_AVAILABLE:
#     api_router.include_router(discovery_flow_v2_router, prefix="/discovery-flows-v2", tags=["Discovery Flow v2"])
#     logger.info("✅ Discovery Flow V2 router included at /discovery-flows-v2")
# else:
#     logger.warning("⚠️ Discovery Flow V2 router not available")

# Migrations if available
if MIGRATIONS_AVAILABLE:
    api_router.include_router(
        migrations_router, prefix="/migration", tags=["Migration"]
    )
    logger.info("✅ Migrations router included")

# Health endpoints
if HEALTH_AVAILABLE:
    api_router.include_router(health_router, prefix="/health", tags=["Health"])
    logger.info("✅ Health router included")

if LLM_HEALTH_AVAILABLE:
    api_router.include_router(llm_health_router, prefix="/llm", tags=["LLM Health"])
    logger.info("✅ LLM Health router included")

# Data Cleansing endpoints
if DATA_CLEANSING_AVAILABLE:
    api_router.include_router(
        data_cleansing_router, prefix="/data-cleansing", tags=["Data Cleansing"]
    )
    logger.info("✅ Data Cleansing router included")
else:
    logger.warning("⚠️ Data Cleansing router not available")
# Observability and System Control
if OBSERVABILITY_AVAILABLE:
    api_router.include_router(
        observability_router, prefix="/observability", tags=["Observability"]
    )
    logger.info("✅ Observability router included")
else:
    logger.warning(
        "⚠️ Observability router not available - polling control endpoints disabled"
    )


# Observability and System Control
if OBSERVABILITY_AVAILABLE:
    api_router.include_router(
        observability_router, prefix="/observability", tags=["Observability"]
    )
    logger.info("✅ Observability router included")
else:
    logger.warning(
        "⚠️ Observability router not available - polling control endpoints disabled"
    )


# Authentication and Context
if AUTH_RBAC_AVAILABLE:
    api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    logger.info("✅ Auth RBAC router included")

# Master Flow Coordination
if MASTER_FLOWS_AVAILABLE:
    api_router.include_router(
        master_flows_router, prefix="/master-flows", tags=["Master Flow Coordination"]
    )
    logger.info("✅ Master Flows router included")
else:
    logger.warning("⚠️ Master Flows router not available")

# Unified Flow API - Master Flow Orchestrator endpoints
try:
    from app.api.v1.flows import router as unified_flows_router

    api_router.include_router(
        unified_flows_router, prefix="/flows", tags=["Unified Flow Management"]
    )
    logger.info("✅ Unified Flow API router included")
except ImportError as e:
    logger.warning(f"⚠️ Unified Flow API router not available: {e}")

# Flow Status Sync Debug endpoints (ADR-012)
api_router.include_router(
    flow_sync_debug_router, prefix="/debug/flow-sync", tags=["Flow Sync Debug"]
)
logger.info("✅ Flow Sync Debug router included")

api_router.include_router(
    context_router, prefix="/context", tags=["Context Management"]
)

# Discovery Flows API - Minimal implementation for frontend compatibility
try:
    from app.api.v1.endpoints.discovery_flows import router as discovery_flows_router

    api_router.include_router(
        discovery_flows_router, prefix="/discovery", tags=["Discovery Flows"]
    )
    logger.info("✅ Discovery Flows router included (minimal implementation)")
except ImportError as e:
    logger.warning(f"⚠️ Discovery Flows router not available: {e}")

# Discovery Flow Implementation Status
logger.info(
    "✅ Discovery flows implemented with real CrewAI via Master Flow Orchestrator"
)

# Include dependency endpoints under discovery prefix
try:
    from app.api.v1.discovery.dependency_endpoints import router as dependency_router

    api_router.include_router(
        dependency_router, prefix="/discovery", tags=["Discovery Dependencies"]
    )
    logger.info("✅ Dependency endpoints included under /discovery")
except ImportError as e:
    logger.warning(f"⚠️ Dependency endpoints not available: {e}")
logger.info("✅ Pseudo-agents archived and replaced with real CrewAI implementations")

# Performance Monitoring API (Task 4.3) - DISABLED (psutil dependency issues)
# try:
#     from app.api.v1.endpoints.performance.monitoring import router as performance_monitoring_router
#     api_router.include_router(performance_monitoring_router, prefix="/performance", tags=["Performance Monitoring"])
#     logger.info("✅ Performance Monitoring router included")
# except ImportError as e:
#     logger.warning(f"⚠️ Performance Monitoring router not available: {e}")
logger.info("⚠️ Performance Monitoring router disabled (psutil dependency conflicts)")
api_router.include_router(
    context_establishment_router,
    prefix="/context-establishment",
    tags=["Context Establishment"],
)

# Assessment Management
if ASSESS_AVAILABLE:
    api_router.include_router(assess_router, prefix="/assess", tags=["Assessment"])
    logger.info("✅ Assessment router included")
else:
    logger.warning("⚠️ Assessment router not available")

if WAVE_PLANNING_AVAILABLE:
    api_router.include_router(
        wave_planning_router, prefix="/ave-planning", tags=["Wave Planning"]
    )
    logger.info("✅ Wave Planning router included")
else:
    logger.warning("⚠️ Wave Planning router not available")

# Decommission Management
if DECOMMISSION_AVAILABLE:
    api_router.include_router(
        decommission_router, prefix="/decommission", tags=["Decommission"]
    )
    logger.info("✅ Decommission router included")
else:
    logger.warning("⚠️ Decommission router not available")

# Data Management
api_router.include_router(
    data_import_router, prefix="/data-import", tags=["Data Import"]
)
api_router.include_router(
    asset_inventory_router, prefix="/assets", tags=["Asset Inventory"]
)

# Top-level Field Mapping API (frontend compatibility)
try:
    from app.api.v1.endpoints.field_mapping import router as field_mapping_router

    api_router.include_router(field_mapping_router, tags=["Field Mapping"])
    logger.info("✅ Top-level Field Mapping router included for frontend compatibility")
except ImportError as e:
    logger.warning(f"⚠️ Top-level Field Mapping router not available: {e}")

# System Management
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring"])

# Agent Performance API (Phase 3 - Agent Observability Enhancement)
try:
    from app.api.v1.endpoints.agent_performance import (
        router as agent_performance_router,
    )

    api_router.include_router(
        agent_performance_router, prefix="/monitoring", tags=["Agent Performance"]
    )
    logger.info("✅ Agent Performance API router included at /monitoring")
except ImportError as e:
    logger.warning(f"⚠️ Agent Performance API router not available: {e}")

# Agent and AI Services
api_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_router.include_router(
    agent_learning_router, prefix="/agent-learning", tags=["Agent Learning"]
)
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])

# Assessment Flow Services
api_router.include_router(assessment_flow_router, tags=["Assessment Flow"])
api_router.include_router(assessment_events_router, tags=["Assessment Flow Events"])

# Agent Events endpoints for real-time SSE communication (all flow types)
if AGENT_EVENTS_AVAILABLE:
    api_router.include_router(agent_events_router, tags=["Flow Events"])
    logger.info("✅ Agent Events (SSE) router included at /flows/{flow_id}/events")
else:
    logger.warning("⚠️ Agent Events router not available")

# Flow Processing Agent (Central routing for all flow continuations)
try:
    from app.api.v1.endpoints.flow_processing import router as flow_processing_router

    api_router.include_router(
        flow_processing_router,
        prefix="/flow-processing",
        tags=["Flow Processing Agent"],
    )
    logger.info("✅ Flow Processing Agent router included")
except ImportError as e:
    logger.warning(f"⚠️ Flow Processing Agent router not available: {e}")

# Flow Health Monitoring
if FLOW_HEALTH_AVAILABLE:
    api_router.include_router(
        flow_health_router, prefix="/flow-health", tags=["Flow Health"]
    )
    logger.info("✅ Flow Health router included")
else:
    logger.warning("⚠️ Flow Health router not available")

# Session Management - REMOVED (use flow_id instead)

# Admin Management (conditional)
if CLIENT_MANAGEMENT_AVAILABLE:
    api_router.include_router(
        client_management_router,
        prefix="/admin/clients",
        tags=["Admin - Client Management"],
    )
    logger.info("✅ Client management router included")

if ENGAGEMENT_MANAGEMENT_AVAILABLE:
    api_router.include_router(
        engagement_management_router,
        prefix="/admin/engagements",
        tags=["Admin - Engagement Management"],
    )
    logger.info("✅ Engagement management router included")

if PLATFORM_ADMIN_AVAILABLE:
    api_router.include_router(
        platform_admin_router,
        prefix="/admin/platform",
        tags=["Admin - Platform Management"],
    )
    logger.info("✅ Platform admin router included")

if FLOW_COMPARISON_AVAILABLE:
    api_router.include_router(flow_comparison_router, tags=["Admin - Flow Comparison"])
    logger.info("✅ Flow comparison router included")
else:
    logger.warning("⚠️ Flow comparison router not available")

if USER_APPROVALS_AVAILABLE:
    api_router.include_router(
        user_approvals_router,
        prefix="/admin/approvals",
        tags=["Admin - User Approvals"],
    )
    logger.info("✅ User approvals router included")

# Security monitoring endpoints
if ADMIN_ENDPOINTS_AVAILABLE:
    api_router.include_router(
        security_audit_router, prefix="/admin", tags=["Admin - Security Monitoring"]
    )
    logger.info("✅ Security audit router included")

# Admin handlers are already included through the auth router (rbac.py)
# No need to include admin_router separately - it would create duplicate routes

# Rate Limit Admin endpoints
try:
    from app.api.v1.endpoints.admin_rate_limit import router as admin_rate_limit_router

    api_router.include_router(
        admin_rate_limit_router, prefix="/admin", tags=["Admin - Rate Limiting"]
    )
    logger.info("✅ Admin rate limit router included")
except ImportError as e:
    logger.warning(f"⚠️ Admin rate limit router not available: {e}")

if SIMPLE_ADMIN_AVAILABLE:
    api_router.include_router(
        simple_admin_router, prefix="/api/v1", tags=["Simple Admin"]
    )
    logger.info("✅ Simple admin router included")
else:
    logger.warning("⚠️ Simple admin router not available")

# Testing and Debug
api_router.include_router(
    test_discovery_router, prefix="/test-discovery", tags=["Test Discovery"]
)

# Emergency system controls
try:
    from app.api.v1.endpoints.system.emergency import router as emergency_router

    api_router.include_router(
        emergency_router, prefix="/system", tags=["System", "Emergency"]
    )
    logger.info("✅ Emergency controls router included")
except ImportError:
    logger.warning("⚠️ Emergency controls router not available")

# Legacy Discovery Flow Management - DISABLED (replaced by V2 Discovery Flow API at /api/v2/discovery-flows/)
# api_router.include_router(discovery_flow_management_router, prefix="/discovery", tags=["Discovery Flow Management"])
# api_router.include_router(
#     discovery_flow_management_enhanced_router,
#     prefix="/discovery/enhanced",
#     tags=["Enhanced Flow Management"]
# )


# Debug endpoint to list all routes
@api_router.get("/debug/routes", include_in_schema=False)
async def debug_routes():
    """Debug endpoint to list all registered routes."""
    routes = []
    for route in api_router.routes:
        routes.append(
            {
                "path": route.path,
                "name": getattr(route, "name", ""),
                "methods": getattr(route, "methods", []),
            }
        )
    return {"routes": routes}


logger.info("--- Finished API Router Inclusion Process ---")
