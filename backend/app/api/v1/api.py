"""
Main API router for the AI Force Migration Platform.
Includes all endpoint routers and API versioning.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import migrations, assets, assessments, websocket, monitoring, chat

# Use modular discovery router with robust error handling and clean architecture
try:
    from app.api.v1.endpoints import discovery
    DISCOVERY_AVAILABLE = True
    print("✅ Using modular discovery router")
except ImportError as e:
    print(f"⚠️ Modular discovery not available: {e}")
    try:
        from app.api.v1.endpoints import discovery_robust as discovery
        DISCOVERY_AVAILABLE = True
        print("✅ Falling back to robust discovery router")
    except ImportError as e2:
        print(f"⚠️ Robust discovery not available: {e2}")
        try:
            from app.api.v1.endpoints import discovery_simple as discovery
            DISCOVERY_AVAILABLE = True
            print("✅ Falling back to simple discovery router")
        except ImportError as e3:
            print(f"⚠️ No discovery router available: {e3}")
            DISCOVERY_AVAILABLE = False

# Import 6R analysis endpoints
try:
    from app.api.v1.endpoints import sixr_analysis
    SIXR_AVAILABLE = True
except ImportError:
    SIXR_AVAILABLE = False

# Import demo endpoints
try:
    from app.api.v1.endpoints import demo
    DEMO_AVAILABLE = True
    print("✅ Demo endpoints available")
except ImportError as e:
    print(f"⚠️ Demo endpoints not available: {e}")
    DEMO_AVAILABLE = False

# Import data import endpoints
try:
    from app.api.v1.endpoints import data_import
    DATA_IMPORT_AVAILABLE = True
    print("✅ Data import endpoints available")
except ImportError as e:
    print(f"⚠️ Data import endpoints not available: {e}")
    DATA_IMPORT_AVAILABLE = False

# Import enhanced asset inventory endpoints
try:
    from app.api.v1.endpoints import asset_inventory
    ASSET_INVENTORY_AVAILABLE = True
    print("✅ Enhanced asset inventory endpoints available")
except ImportError as e:
    print(f"⚠️ Enhanced asset inventory endpoints not available: {e}")
    ASSET_INVENTORY_AVAILABLE = False

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    migrations.router,
    prefix="/migrations",
    tags=["migrations"]
)

api_router.include_router(
    assets.router,
    prefix="/assets",
    tags=["assets"]
)

api_router.include_router(
    assessments.router,
    prefix="/assessments",
    tags=["assessments"]
)

# Include discovery router if available
if DISCOVERY_AVAILABLE:
    api_router.include_router(
        discovery.router,
        prefix="/discovery",
        tags=["discovery"]
    )

# Include demo router if available
if DEMO_AVAILABLE:
    api_router.include_router(
        demo.router,
        prefix="/demo",
        tags=["demo"]
    )

api_router.include_router(
    monitoring.router,
    prefix="/monitoring",
    tags=["monitoring"]
)

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["websocket"]
)

# Include chat endpoints for user interactions
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

# Include 6R analysis endpoints if available
if SIXR_AVAILABLE:
    api_router.include_router(
        sixr_analysis.router,
        prefix="/sixr",
        tags=["6r-analysis"]
    )

# Include enhanced asset inventory endpoints if available (additional intelligent features)
if ASSET_INVENTORY_AVAILABLE:
    api_router.include_router(
        asset_inventory.router,
        prefix="/inventory",  # Use /inventory prefix to avoid conflicts
        tags=["enhanced-asset-inventory"]
    )

# Include auth/RBAC endpoints
try:
    from app.api.v1.auth import rbac
    api_router.include_router(
        rbac.router,
        prefix="/auth",
        tags=["authentication", "rbac"]
    )
    print("✅ Authentication & RBAC endpoints available")
except ImportError as e:
    print(f"⚠️ Authentication & RBAC endpoints not available: {e}")

# Include LLM usage tracking admin endpoints
try:
    from app.api.v1.admin import llm_usage
    api_router.include_router(
        llm_usage.router,
        prefix="/admin/llm-usage",
        tags=["llm-usage-tracking"]
    )
    print("✅ LLM usage tracking endpoints available")
except ImportError as e:
    print(f"⚠️ LLM usage tracking endpoints not available: {e}")

# Include platform admin endpoints for enhanced RBAC
try:
    from app.api.v1.admin import platform_admin_handlers
    api_router.include_router(
        platform_admin_handlers.router,
        prefix="/platform-admin",
        tags=["platform-administration"]
    )
    print("✅ Platform admin endpoints available")
except ImportError as e:
    print(f"⚠️ Platform admin endpoints not available: {e}")

# Include workflow integration endpoints
try:
    from app.api.v1.endpoints import workflow_integration
    api_router.include_router(
        workflow_integration.router,
        prefix="/workflow",
        tags=["workflow-integration"]
    )
    print("✅ Workflow integration endpoints available")
except ImportError as e:
    print(f"⚠️ Workflow integration endpoints not available: {e}")

# Include data import endpoints if available
if DATA_IMPORT_AVAILABLE:
    api_router.include_router(
        data_import.router,
        prefix="/data-import",
        tags=["data-import"]
    )

# Include data cleanup endpoints
try:
    from app.api.v1.endpoints import data_cleanup
    api_router.include_router(
        data_cleanup.router,
        prefix="/data-cleanup",
        tags=["data-cleanup"]
    )
    print("✅ Data cleanup endpoints available")
except ImportError as e:
    print(f"⚠️ Data cleanup endpoints not available: {e}")

# Import workflow endpoints
try:
    from app.api.v1.endpoints import asset_workflow
    WORKFLOW_AVAILABLE = True
    print("✅ Asset workflow endpoints available")
except ImportError as e:
    print(f"⚠️ Asset workflow endpoints not available: {e}")
    WORKFLOW_AVAILABLE = False

# Include workflow endpoints if available
if WORKFLOW_AVAILABLE:
    api_router.include_router(
        asset_workflow.router,
        prefix="/workflow",
        tags=["asset-workflow"]
    )

# Include agentic discovery endpoints
try:
    from app.api.v1.endpoints import agent_discovery
    api_router.include_router(
        agent_discovery.router,
        prefix="/discovery/agents",
        tags=["agentic-discovery"]
    )
    print("✅ Agentic discovery endpoints available")
except ImportError as e:
    print(f"⚠️ Agentic discovery endpoints not available: {e}")

# Include agent learning endpoints (Tasks C.1 and C.2)
try:
    from app.api.v1.endpoints import agent_learning_endpoints
    api_router.include_router(
        agent_learning_endpoints.router,
        prefix="/agent-learning",
        tags=["agent-learning"]
    )
    print("✅ Agent learning endpoints available (Tasks C.1 and C.2)")
except ImportError as e:
    print(f"⚠️ Agent learning endpoints not available: {e}")

# Include RBAC authentication endpoints (Task 3.1)
try:
    from app.api.v1.auth import rbac
    api_router.include_router(
        rbac.router,
        prefix="",  # No prefix since router already has /auth
        tags=["rbac-authentication"]
    )
    print("✅ RBAC authentication endpoints available (Task 3.1)")
except ImportError as e:
    print(f"⚠️ RBAC authentication endpoints not available: {e}")

# Include Admin Management endpoints (Task 3.2)
try:
    from app.api.v1.admin import client_management, engagement_management, session_comparison
    api_router.include_router(
        client_management.router,
        prefix="",  # No prefix since router already has /admin/clients
        tags=["client-management"]
    )
    api_router.include_router(
        engagement_management.router,
        prefix="",  # No prefix since router already has /admin/engagements
        tags=["engagement-management"]
    )
    api_router.include_router(
        session_comparison.router,
        prefix="/admin",  # Prefix for session comparison endpoints
        tags=["session-comparison"]
    )
    print("✅ Admin management endpoints available (Task 3.2)")
    print("✅ Session comparison endpoints available (Task 6.1)")
except ImportError as e:
    print(f"⚠️ Admin management endpoints not available: {e}") 