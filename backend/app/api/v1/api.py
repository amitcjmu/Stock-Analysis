"""
Main API router for the AI Force Migration Platform.
Includes all endpoint routers and API versioning.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import migrations, assets, assessments, websocket, monitoring, chat

# Use simplified discovery for now to resolve 404 issues
try:
    from app.api.v1.endpoints import discovery_simple as discovery
    DISCOVERY_AVAILABLE = True
except ImportError:
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