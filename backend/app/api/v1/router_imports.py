"""
Router imports for the v1 API.
This module centralizes all router imports to reduce complexity in the main api.py file.
"""

import logging
from typing import Optional, Dict, Tuple
from fastapi import APIRouter

# Core endpoint imports
from app.api.v1.endpoints import (
    agent_learning_router,
    agents_router,
    analysis_router,
    assessment_events_router,
    assessment_flow_router,
    asset_workflow_router,
    asset_inventory_router,
    chat_router,
    context_router,
    data_import_router,
    feedback_router,
    field_mapping_router,
    monitoring_router,
    # sixr_router removed - replaced by Assessment Flow with MFO integration (Phase 4, Issue #840)
)

# Asset conflicts and preview routers
from app.api.v1.endpoints.asset_conflicts import router as asset_conflicts_router
from app.api.v1.endpoints.asset_preview import (  # noqa: F401
    router as asset_preview_router,
)

# Asset editing router (Issues #911, #912)
from app.api.v1.endpoints.asset_editing import router as asset_editing_router

from app.api.v1.endpoints.execute import router as execute_router

from app.api.v1.endpoints.context_establishment import (
    router as context_establishment_router,
)
from app.api.v1.endpoints.flow_sync_debug import router as flow_sync_debug_router

# Analysis endpoints (including queues)
analysis_queues_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.analysis import router as analysis_queues_router

    ANALYSIS_QUEUES_AVAILABLE = True
except ImportError:
    ANALYSIS_QUEUES_AVAILABLE = False
    analysis_queues_router = None

# Decommission endpoints (legacy - deprecated)
decommission_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.decommission import router as decommission_router

    DECOMMISSION_AVAILABLE = True
except ImportError:
    DECOMMISSION_AVAILABLE = False
    decommission_router = None

# Decommission Flow endpoints (MFO-integrated per ADR-006)
decommission_flow_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.decommission_flow import (
        router as decommission_flow_router,
    )

    DECOMMISSION_FLOW_AVAILABLE = True
except ImportError:
    DECOMMISSION_FLOW_AVAILABLE = False
    decommission_flow_router = None

# Admin endpoints
platform_admin_router: Optional[APIRouter]
security_audit_router: Optional[APIRouter]
llm_usage_router: Optional[APIRouter]
memory_management_router: Optional[APIRouter]
try:
    from app.api.v1.admin.platform_admin_handlers import router as platform_admin_router
    from app.api.v1.admin.security_monitoring_handlers.security_audit_handler import (
        router as security_audit_router,
    )
    from app.api.v1.admin.llm_usage import router as llm_usage_router
    from app.api.v1.admin.memory_management import router as memory_management_router

    ADMIN_ENDPOINTS_AVAILABLE = True
except ImportError:
    ADMIN_ENDPOINTS_AVAILABLE = False
    platform_admin_router = None
    security_audit_router = None
    llm_usage_router = None
    memory_management_router = None

# Discovery endpoints - REMOVED: Legacy discovery endpoints are deprecated
# All discovery functionality must use MFO (/api/v1/flows/*) or unified-discovery
# DO NOT re-add discovery router imports - they violate MFO-first architecture
DISCOVERY_AVAILABLE = False
discovery_router = None

# Unified Discovery Flow API - Master Flow Orchestrator Integration
unified_discovery_router: Optional[APIRouter]
dependency_analysis_router: Optional[APIRouter]
agent_insights_router: Optional[APIRouter]
clarifications_router: Optional[APIRouter]
flow_management_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.unified_discovery import (
        router as unified_discovery_router,
    )
    from app.api.v1.endpoints.dependency_analysis import (
        router as dependency_analysis_router,
    )
    from app.api.v1.endpoints.agent_insights import (
        router as agent_insights_router,
    )
    from app.api.v1.endpoints.clarifications import (
        router as clarifications_router,
    )

    UNIFIED_DISCOVERY_AVAILABLE = True
except ImportError:
    UNIFIED_DISCOVERY_AVAILABLE = False
    unified_discovery_router = None
    dependency_analysis_router = None
    agent_insights_router = None
    clarifications_router = None

# Assessment endpoints
assess_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.assess import router as assess_router

    ASSESS_AVAILABLE = True
except ImportError:
    ASSESS_AVAILABLE = False
    assess_router = None

# Assessment Flow endpoints (already imported above)
# assessment_flow_router is imported from endpoints package at line 16
ASSESSMENT_FLOW_AVAILABLE = True

# Assessment Flow Readiness endpoints (Issue #980 - Gap Detection Integration)
assessment_flow_readiness_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.assessment_flow_readiness import (
        router as assessment_flow_readiness_router,
    )

    ASSESSMENT_FLOW_READINESS_AVAILABLE = True
except ImportError:
    ASSESSMENT_FLOW_READINESS_AVAILABLE = False
    assessment_flow_readiness_router = None

# Wave Planning endpoints
wave_planning_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.wave_planning import router as wave_planning_router

    WAVE_PLANNING_AVAILABLE = True
except ImportError:
    WAVE_PLANNING_AVAILABLE = False
    wave_planning_router = None

# Plan endpoints
plan_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.plan import router as plan_router

    PLAN_AVAILABLE = True
except ImportError:
    PLAN_AVAILABLE = False
    plan_router = None

# Collection Flow endpoints
collection_flows_router: Optional[APIRouter]
collection_post_completion_router: Optional[APIRouter]
collection_bulk_ops_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.collection_flows import router as collection_flows_router
    from app.api.v1.endpoints.collection_post_completion import (
        router as collection_post_completion_router,
    )
    from app.api.v1.endpoints.collection import router as collection_bulk_ops_router

    COLLECTION_AVAILABLE = True
except ImportError:
    COLLECTION_AVAILABLE = False
    collection_flows_router = None
    collection_post_completion_router = None
    collection_bulk_ops_router = None

# Collection Bulk Operations endpoints (Adaptive Questionnaire Enhancements)
# NOTE: These are now included in collection_bulk_ops_router via collection/__init__.py
# Individual routers no longer imported separately to avoid duplicate registration
COLLECTION_BULK_OPS_AVAILABLE = (
    COLLECTION_AVAILABLE  # Same availability as main collection router
)

# Collection Gaps endpoints
collection_gaps_vendor_products_router: Optional[APIRouter]
collection_gaps_maintenance_windows_router: Optional[APIRouter]
collection_gaps_governance_router: Optional[APIRouter]
collection_gaps_assets_router: Optional[APIRouter]
collection_gaps_collection_flows_router: Optional[APIRouter]
collection_gap_analysis_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.collection_gaps.vendor_products import (
        router as collection_gaps_vendor_products_router,
    )
    from app.api.v1.endpoints.collection_gaps.maintenance_windows import (
        router as collection_gaps_maintenance_windows_router,
    )
    from app.api.v1.endpoints.collection_gaps.governance import (
        router as collection_gaps_governance_router,
    )
    from app.api.v1.endpoints.collection_gaps.assets import (
        router as collection_gaps_assets_router,
    )
    from app.api.v1.endpoints.collection_gaps.collection_flows import (
        router as collection_gaps_collection_flows_router,
    )
    from app.api.v1.endpoints.collection_gap_analysis import (
        router as collection_gap_analysis_router,
    )

    COLLECTION_GAPS_AVAILABLE = True
except ImportError:
    COLLECTION_GAPS_AVAILABLE = False
    collection_gaps_vendor_products_router = None
    collection_gaps_maintenance_windows_router = None
    collection_gaps_governance_router = None
    collection_gaps_assets_router = None
    collection_gaps_collection_flows_router = None
    collection_gap_analysis_router = None

# Flow Processing endpoints
flow_processing_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.flow_processing import router as flow_processing_router

    FLOW_PROCESSING_AVAILABLE = True
except ImportError:
    FLOW_PROCESSING_AVAILABLE = False
    flow_processing_router = None

# Additional routers with availability flags
# API Health router
api_health_router: Optional[APIRouter]
try:
    from app.api.v1.endpoints.api_health import router as api_health_router

    API_HEALTH_AVAILABLE = True
except ImportError:
    api_health_router = None
    API_HEALTH_AVAILABLE = False

routers_with_flags: Dict[str, Tuple[bool, Optional[APIRouter]]] = {}

# Migrations
try:
    from app.api.v1.endpoints.migrations import router as migrations_router

    routers_with_flags["MIGRATIONS"] = (True, migrations_router)
except ImportError:
    routers_with_flags["MIGRATIONS"] = (False, None)

# Health endpoints
try:
    from app.api.v1.endpoints.health import router as health_router

    routers_with_flags["HEALTH"] = (True, health_router)
except ImportError:
    routers_with_flags["HEALTH"] = (False, None)

# LLM Health endpoints
try:
    from app.api.v1.endpoints.llm_health import router as llm_health_router

    routers_with_flags["LLM_HEALTH"] = (True, llm_health_router)
except ImportError:
    routers_with_flags["LLM_HEALTH"] = (False, None)

# Data Cleansing endpoints
try:
    from app.api.v1.endpoints.data_cleansing import router as data_cleansing_router

    routers_with_flags["DATA_CLEANSING"] = (True, data_cleansing_router)
except ImportError:
    routers_with_flags["DATA_CLEANSING"] = (False, None)

# Observability endpoints
try:
    from app.api.v1.endpoints.observability import router as observability_router

    routers_with_flags["OBSERVABILITY"] = (True, observability_router)
except ImportError:
    routers_with_flags["OBSERVABILITY"] = (False, None)

# Authentication and RBAC
try:
    from app.api.v1.auth import auth_router

    routers_with_flags["AUTH_RBAC"] = (True, auth_router)
except ImportError:
    routers_with_flags["AUTH_RBAC"] = (False, None)

# RBAC Admin
try:
    from app.api.v1.admin.rbac_admin_handlers import router as rbac_admin_router

    routers_with_flags["RBAC_ADMIN"] = (True, rbac_admin_router)
except ImportError:
    routers_with_flags["RBAC_ADMIN"] = (False, None)

# Emergency System Control
try:
    from app.api.v1.endpoints.system.emergency import router as emergency_router

    routers_with_flags["EMERGENCY"] = (True, emergency_router)
except ImportError:
    routers_with_flags["EMERGENCY"] = (False, None)

# Websocket Cache
try:
    from app.api.v1.endpoints.websocket_cache import router as websocket_cache_router

    routers_with_flags["WEBSOCKET_CACHE"] = (True, websocket_cache_router)
except ImportError:
    routers_with_flags["WEBSOCKET_CACHE"] = (False, None)

# Cached Context
try:
    from app.api.v1.endpoints.cached_context import router as cached_context_router

    routers_with_flags["CACHED_CONTEXT"] = (True, cached_context_router)
except ImportError:
    routers_with_flags["CACHED_CONTEXT"] = (False, None)

# Flow health
try:
    from app.api.v1.endpoints.flow_health import router as flow_health_router

    routers_with_flags["FLOW_HEALTH"] = (True, flow_health_router)
except ImportError:
    routers_with_flags["FLOW_HEALTH"] = (False, None)

# Blocking flows
try:
    from app.api.v1.endpoints.blocking_flows import router as blocking_flows_router

    routers_with_flags["BLOCKING_FLOWS"] = (True, blocking_flows_router)
except ImportError:
    routers_with_flags["BLOCKING_FLOWS"] = (False, None)

# Additional admin routers
try:
    from app.api.v1.admin.client_management import router as client_management_router

    routers_with_flags["CLIENT_MANAGEMENT"] = (True, client_management_router)
except ImportError:
    routers_with_flags["CLIENT_MANAGEMENT"] = (False, None)

try:
    from app.api.v1.admin.engagement_management import (
        router as engagement_management_router,
    )

    routers_with_flags["ENGAGEMENT_MANAGEMENT"] = (True, engagement_management_router)
except ImportError:
    routers_with_flags["ENGAGEMENT_MANAGEMENT"] = (False, None)

try:
    from app.api.v1.admin.session_comparison import router as flow_comparison_router

    routers_with_flags["FLOW_COMPARISON"] = (True, flow_comparison_router)
except ImportError:
    routers_with_flags["FLOW_COMPARISON"] = (False, None)

try:
    from app.api.v1.auth.handlers.user_management_handlers import (
        user_management_router as user_approvals_router,
    )

    routers_with_flags["USER_APPROVALS"] = (True, user_approvals_router)
except ImportError:
    routers_with_flags["USER_APPROVALS"] = (False, None)

try:
    from app.api.v1.endpoints.admin_user_access import (
        router as admin_user_access_router,
    )

    routers_with_flags["ADMIN_USER_ACCESS"] = (True, admin_user_access_router)
except ImportError:
    routers_with_flags["ADMIN_USER_ACCESS"] = (False, None)

try:
    from app.api.v1.master_flows import router as master_flows_router

    routers_with_flags["MASTER_FLOWS"] = (True, master_flows_router)
except ImportError:
    routers_with_flags["MASTER_FLOWS"] = (False, None)

try:
    from app.api.v1.endpoints.simple_admin import simple_admin_router

    routers_with_flags["SIMPLE_ADMIN"] = (True, simple_admin_router)
except ImportError:
    routers_with_flags["SIMPLE_ADMIN"] = (False, None)

# Agent Events for SSE communication
try:
    from app.api.v1.endpoints.agent_events import router as agent_events_router

    routers_with_flags["AGENT_EVENTS"] = (True, agent_events_router)
except ImportError:
    routers_with_flags["AGENT_EVENTS"] = (False, None)

# Additional missing routers
try:
    from app.api.v1.admin.rate_limiting import router as rate_limiting_router

    routers_with_flags["RATE_LIMITING"] = (True, rate_limiting_router)
except ImportError:
    routers_with_flags["RATE_LIMITING"] = (False, None)

try:
    from app.api.v1.finops.finops_router import router as finops_router

    routers_with_flags["FINOPS"] = (True, finops_router)
except ImportError:
    routers_with_flags["FINOPS"] = (False, None)

# Canonical Applications
try:
    from app.api.v1.canonical_applications import (
        router as canonical_applications_router,
    )

    routers_with_flags["CANONICAL_APPLICATIONS"] = (True, canonical_applications_router)
except ImportError:
    routers_with_flags["CANONICAL_APPLICATIONS"] = (False, None)

# Applications (for Planning Flow wizard)
try:
    from app.api.v1.endpoints.applications import router as applications_router

    routers_with_flags["APPLICATIONS"] = (True, applications_router)
except ImportError:
    routers_with_flags["APPLICATIONS"] = (False, None)

# Wave Planning (for Plan Flow wizard)
if WAVE_PLANNING_AVAILABLE:
    routers_with_flags["WAVE_PLANNING"] = (True, wave_planning_router)
else:
    routers_with_flags["WAVE_PLANNING"] = (False, None)

# RBAC Admin router
try:
    from app.api.v1.admin.rbac import router as rbac_admin_router

    routers_with_flags["RBAC_ADMIN"] = (True, rbac_admin_router)
except ImportError:
    routers_with_flags["RBAC_ADMIN"] = (False, None)

# Initialize logger after all imports
logger = logging.getLogger(__name__)

# Export all available routers and flags for use by router_registry.py
__all__ = [
    # Core routers
    "agent_learning_router",
    "agents_router",
    "analysis_router",
    "assessment_events_router",
    "assessment_flow_router",
    "asset_workflow_router",
    "asset_inventory_router",
    "asset_conflicts_router",
    "asset_editing_router",
    "chat_router",
    "context_router",
    "data_import_router",
    "feedback_router",
    "field_mapping_router",
    "execute_router",
    "monitoring_router",
    # "sixr_router",  # Removed - replaced by Assessment Flow with MFO integration (Phase 4, Issue #840)
    "context_establishment_router",
    "flow_sync_debug_router",
    # Conditional routers with availability flags
    "ANALYSIS_QUEUES_AVAILABLE",
    "analysis_queues_router",
    "DECOMMISSION_AVAILABLE",
    "decommission_router",
    "ADMIN_ENDPOINTS_AVAILABLE",
    "platform_admin_router",
    "security_audit_router",
    "DISCOVERY_AVAILABLE",
    # "discovery_router",  # Removed - legacy endpoints deprecated
    "UNIFIED_DISCOVERY_AVAILABLE",
    "unified_discovery_router",
    "dependency_analysis_router",
    "agent_insights_router",
    "clarifications_router",
    "ASSESS_AVAILABLE",
    "assess_router",
    "ASSESSMENT_FLOW_READINESS_AVAILABLE",
    "assessment_flow_readiness_router",
    "WAVE_PLANNING_AVAILABLE",
    "wave_planning_router",
    "PLAN_AVAILABLE",
    "plan_router",
    "COLLECTION_AVAILABLE",
    "collection_flows_router",
    "collection_post_completion_router",
    "collection_bulk_ops_router",
    "COLLECTION_BULK_OPS_AVAILABLE",
    "COLLECTION_GAPS_AVAILABLE",
    "collection_gaps_vendor_products_router",
    "collection_gaps_maintenance_windows_router",
    "collection_gaps_governance_router",
    "collection_gaps_assets_router",
    "collection_gaps_collection_flows_router",
    "collection_gap_analysis_router",
    "FLOW_PROCESSING_AVAILABLE",
    "flow_processing_router",
    # Dynamic routers with flags
    "routers_with_flags",
]
