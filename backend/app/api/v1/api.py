"""
Main API router for the AI Force Migration Platform.
Includes all endpoint routers and API versioning.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import migrations, assets, assessments, discovery, websocket

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

api_router.include_router(
    discovery.router,
    prefix="/discovery",
    tags=["discovery"]
)

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["websocket"]
) 