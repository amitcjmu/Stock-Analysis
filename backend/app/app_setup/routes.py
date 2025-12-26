import logging
from fastapi import APIRouter


def include_api_routes(app):
    logger = logging.getLogger(__name__)
    try:
        from app.api.v1.api import api_router

        app.include_router(api_router, prefix="/api/v1")
        logger.info("✅ API v1 routes loaded successfully")

        # Debug: Log registered routes
        auth_routes = [
            r for r in api_router.routes if hasattr(r, "path") and "/auth" in r.path
        ]
        if auth_routes:
            logger.info(f"✅ Found {len(auth_routes)} auth routes registered")
            for route in auth_routes[:5]:  # Log first 5 auth routes
                logger.info(f"  - {getattr(route, 'methods', [])} {route.path}")
        else:
            logger.warning("⚠️ No auth routes found in api_router")

    except Exception as e:  # pragma: no cover
        logger.error(f"❌ API v1 routes error: {e}", exc_info=True)
        fallback_router = APIRouter()

        @fallback_router.get("/health", summary="Fallback Health Check")
        async def fallback_health_check():
            from datetime import datetime

            return {
                "status": "degraded",
                "service": "ai-force-migration-api",
                "timestamp": datetime.utcnow().isoformat(),
            }

        app.include_router(fallback_router, prefix="/api/v1")
        logger.info("✅ Fallback API v1 health endpoint added")


def add_debug_routes(app):
    @app.get("/debug/routes")
    async def debug_routes():
        routes_info = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                routes_info.append(
                    {
                        "path": route.path,
                        "methods": list(route.methods) if route.methods else [],
                        "name": getattr(route, "name", "unnamed"),
                    }
                )
        return {"total_routes": len(routes_info), "routes": routes_info[:50]}

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "ai-force-migration-api"}
