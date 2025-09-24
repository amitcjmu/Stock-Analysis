"""
Main API router for the AI Modernize Migration Platform.
Simplified version with modularized components.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends

from app.api.v1.auth.auth_utils import get_current_user
from app.api.v1.endpoints.context import get_user_context
from app.core.database import get_db
from app.schemas.context import UserContext
from app.api.v1.router_registry import register_all_routers

logger = logging.getLogger(__name__)

# --- API Router Setup ---
api_router = APIRouter()


# Simple health endpoint for monitoring (CC generated)
@api_router.get(
    "/health", summary="Health Check", description="Basic health check for API v1"
)
async def health_check():
    """
    Simple health check endpoint for API v1.

    Provides basic health status information without complex dependencies.
    Used by frontend and monitoring systems to verify service availability.
    """
    # Basic database connectivity check
    database_status = False
    try:
        # Try to get a database connection - get_db() is an async generator
        db_gen = get_db()
        session = await db_gen.__anext__()  # Get the database session asynchronously
        database_status = True
        # Properly close the database session
        try:
            await db_gen.__anext__()
        except StopAsyncIteration:
            pass  # Async generator exhausted, session closed
        finally:
            await session.close()
    except Exception as e:
        # Database not available or connection failed
        logging.warning(f"Database health check failed: {e}")
        database_status = False

    # API routes are available if this endpoint is reachable
    api_routes_status = True

    return {
        "status": "healthy",
        "service": "ai-force-migration-api",
        "version": "0.2.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {"database": database_status, "api_routes": api_routes_status},
        "environment": "production",
    }


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


# Register all routers using the modularized registry
logger.info("--- Starting API Router Inclusion Process ---")
register_all_routers(api_router)
logger.info("--- API Router Setup Complete ---")
