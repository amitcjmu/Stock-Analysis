"""
API v3 Main Router
Integrates all v3 endpoints into a single router.
"""

import logging
from fastapi import APIRouter, Request, Response
from datetime import datetime

from app.api.v3 import discovery_flow, field_mapping, data_import
from app.api.v3.schemas.responses import HealthCheckResponse, MetricsResponse

logger = logging.getLogger(__name__)

# Create the main v3 router
api_router = APIRouter(prefix="/api/v3", tags=["api-v3"])

# Include all v3 sub-routers
api_router.include_router(
    discovery_flow.router,
    tags=["discovery-flow-v3"]
)

api_router.include_router(
    field_mapping.router, 
    tags=["field-mapping-v3"]
)

api_router.include_router(
    data_import.router,
    tags=["data-import-v3"]
)


# === Main v3 API Endpoints ===

@api_router.get("/", response_model=dict)
async def api_v3_root():
    """API v3 root endpoint with information"""
    return {
        "api_version": "3.0.0",
        "title": "AI Force Migration Platform API v3",
        "description": "Unified API for discovery flows, field mapping, and data import operations",
        "status": "stable",
        "documentation": "/docs",
        "endpoints": {
            "discovery_flows": "/api/v3/discovery-flow",
            "field_mapping": "/api/v3/field-mapping", 
            "data_import": "/api/v3/data-import"
        },
        "features": [
            "Unified discovery flow management",
            "Advanced field mapping with auto-suggestions",
            "Comprehensive data import and validation",
            "Real-time flow status and control",
            "Asset promotion and lifecycle management",
            "Comprehensive error handling and validation"
        ],
        "migration_guide": "https://docs.aiforce.com/api/v3/migration-guide",
        "timestamp": datetime.utcnow().isoformat()
    }


@api_router.get("/health", response_model=HealthCheckResponse)
async def api_v3_health():
    """API v3 comprehensive health check"""
    
    # Check component availability
    components = {}
    
    try:
        from app.api.v1.discovery_handlers.flow_management import FlowManagementHandler
        components["flow_management"] = True
    except ImportError:
        components["flow_management"] = False
    
    try:
        from app.api.v1.discovery_handlers.crewai_execution import CrewAIExecutionHandler
        components["crewai_execution"] = True
    except ImportError:
        components["crewai_execution"] = False
    
    try:
        from app.api.v1.discovery_handlers.asset_management import AssetManagementHandler
        components["asset_management"] = True
    except ImportError:
        components["asset_management"] = False
    
    try:
        from app.api.v1.endpoints.data_import.core_import import DataImportService
        components["data_import_service"] = True
    except ImportError:
        components["data_import_service"] = False
    
    # Determine overall health status
    critical_components = ["flow_management"]  # Components required for basic functionality
    health_status = "healthy"
    
    if not all(components.get(comp, False) for comp in critical_components):
        health_status = "degraded"
    
    if not any(components.values()):
        health_status = "unhealthy"
    
    return HealthCheckResponse(
        status=health_status,
        service="api-v3",
        version="3.0.0",
        timestamp=datetime.utcnow(),
        components=components
    )


@api_router.get("/metrics", response_model=MetricsResponse)
async def api_v3_metrics():
    """API v3 performance metrics"""
    
    # In a production environment, these would come from actual metrics collection
    # For now, we'll return placeholder values
    
    return MetricsResponse(
        active_flows=0,  # Would be retrieved from flow management
        total_flows=0,   # Would be retrieved from database
        completed_flows=0,
        failed_flows=0,
        avg_completion_time_seconds=None,
        avg_response_time_ms=None,
        success_rate_percentage=None,
        timestamp=datetime.utcnow()
    )


@api_router.get("/status", response_model=dict)
async def api_v3_status():
    """API v3 detailed status information"""
    
    # Get health information
    health = await api_v3_health()
    
    # Get metrics information
    metrics = await api_v3_metrics()
    
    return {
        "api_version": "3.0.0",
        "status": health.status,
        "timestamp": datetime.utcnow().isoformat(),
        "health": {
            "overall_status": health.status,
            "components": health.components,
            "uptime_seconds": health.uptime_seconds
        },
        "metrics": {
            "active_flows": metrics.active_flows,
            "total_flows": metrics.total_flows,
            "success_rate": metrics.success_rate_percentage
        },
        "api_info": {
            "endpoints_available": len([
                route for route in api_router.routes 
                if hasattr(route, 'path') and route.path.startswith('/api/v3')
            ]),
            "supported_operations": [
                "create_flow",
                "get_flow", 
                "list_flows",
                "execute_phase",
                "pause_flow",
                "resume_flow",
                "delete_flow",
                "create_field_mapping",
                "update_field_mapping",
                "validate_field_mapping",
                "create_data_import",
                "upload_data_file",
                "validate_data_import",
                "preview_data_import"
            ]
        }
    }


@api_router.get("/openapi-spec", response_model=dict)
async def api_v3_openapi_spec(request: Request):
    """Get OpenAPI specification for v3 API"""
    
    from fastapi.openapi.utils import get_openapi
    from fastapi import FastAPI
    
    # Create a temporary FastAPI app with just v3 routes for spec generation
    temp_app = FastAPI(
        title="AI Force Migration Platform API v3",
        description="Unified API for discovery flows, field mapping, and data import operations",
        version="3.0.0"
    )
    
    # Include the v3 router
    temp_app.include_router(api_router)
    
    # Generate OpenAPI spec
    openapi_schema = get_openapi(
        title="AI Force Migration Platform API v3",
        version="3.0.0",
        description="Unified API for discovery flows, field mapping, and data import operations",
        routes=temp_app.routes,
        servers=[
            {
                "url": str(request.base_url).rstrip('/'),
                "description": "Current server"
            }
        ]
    )
    
    # Add custom OpenAPI extensions
    openapi_schema["info"]["x-api-version"] = "3.0.0"
    openapi_schema["info"]["x-api-status"] = "stable"
    openapi_schema["info"]["x-migration-guide"] = "https://docs.aiforce.com/api/v3/migration-guide"
    openapi_schema["info"]["contact"] = {
        "name": "AI Force Migration Platform",
        "url": "https://docs.aiforce.com/api/v3",
        "email": "api-support@aiforce.com"
    }
    
    return openapi_schema


# === Middleware Integration Helper ===

def setup_v3_middleware(app):
    """Set up v3-specific middleware"""
    
    try:
        from app.api.v3.middleware.deprecation import DeprecationMiddleware
        
        # Add deprecation middleware
        app.add_middleware(
            DeprecationMiddleware,
            track_usage=True,
            log_deprecated_calls=True
        )
        
        logger.info("✅ V3 deprecation middleware added")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to add v3 middleware: {e}")


# === Route Information Helper ===

def get_v3_route_info():
    """Get information about all v3 routes"""
    
    route_info = []
    
    for route in api_router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            route_info.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unnamed'),
                "tags": getattr(route, 'tags', [])
            })
    
    return {
        "total_routes": len(route_info),
        "routes": route_info,
        "route_summary": {
            "discovery_flow_routes": len([r for r in route_info if 'discovery-flow' in r['path']]),
            "field_mapping_routes": len([r for r in route_info if 'field-mapping' in r['path']]),
            "data_import_routes": len([r for r in route_info if 'data-import' in r['path']]),
            "utility_routes": len([r for r in route_info if r['path'] in ['/api/v3/', '/api/v3/health', '/api/v3/metrics', '/api/v3/status']])
        }
    }


# Export the main router
__all__ = ["api_router", "setup_v3_middleware", "get_v3_route_info"]