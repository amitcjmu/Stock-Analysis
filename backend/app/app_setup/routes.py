import logging
from fastapi import APIRouter


def include_api_routes(app):
    logger = logging.getLogger(__name__)
    try:
        from app.api.v1.api import api_router

        app.include_router(api_router, prefix="/api/v1")
        logger.info("✅ API v1 routes loaded successfully")
    except Exception as e:  # pragma: no cover
        logger.warning("API v1 routes error: %s", e)
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
