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