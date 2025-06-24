"""
AI Force Migration Platform - FastAPI Backend
Main application entry point with CORS, routing, and WebSocket support.
"""

# Disable OpenTelemetry before any other imports to prevent connection errors
import os
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")
os.environ.setdefault("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", "all")

import sys
import traceback
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from contextlib import asynccontextmanager
from pathlib import Path
from app.core.context import get_current_context, RequestContext

# Load environment variables
load_dotenv()

# Configure logging to suppress verbose LLM logs
def configure_logging():
    """Configure logging levels to suppress verbose LLM library logs."""
    # Set up basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Suppress verbose LLM-related logs - set to ERROR to only show critical issues
    logging.getLogger("httpx").setLevel(logging.ERROR)
    # LiteLLM references removed - using custom DeepInfra implementation
    logging.getLogger("openai").setLevel(logging.ERROR)
    #logging.getLogger("crewai").setLevel(logging.ERROR)
    #logging.getLogger("CrewAI").setLevel(logging.ERROR)
    logging.getLogger("deepinfra").setLevel(logging.ERROR)
    
    # Additional LLM-related loggers
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("requests").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("h11").setLevel(logging.ERROR)
    
    # Suppress SQL query logs unless they're errors
    logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
    
    # Keep application logs visible at INFO level
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Reduce access logs
    
    # Root logger
    logging.getLogger().setLevel(logging.INFO)
    
    print("✅ Logging configured - LLM library logs suppressed to ERROR level")

# Configure logging before any other imports
configure_logging()

# Lifespan event handler (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🚀 Application starting up...")
    
    # Initialize RBAC system
    try:
        from app.api.v1.auth.rbac import initialize_rbac_system
        await initialize_rbac_system()
    except Exception as e:
        print(f"⚠️  RBAC initialization warning: {e}")
    
    print("✅ Startup logic completed.")

    # Test database connection
    if DATABASE_ENABLED:
        try:
            print("🔧 Testing database connection...")
            from app.core.database import db_manager
            health_check_result = await db_manager.health_check()
            if health_check_result:
                print("✅✅✅ Database connection test successful.")
            else:
                print("⚠️⚠️⚠️ Database connection test failed, but continuing...")
            
        except Exception as e:
            print(f"⚠️⚠️⚠️ Database connection test failed: {e}")
            # Don't fail startup on database connection issues
            import traceback
            traceback.print_exc()
    
    # Yield control to the application
    yield
    
    # Shutdown logic (if needed)
    print("🔄 Application shutting down...")
    print("✅ Shutdown logic completed.")

# Initialize basic app first to ensure health check is always available
app = FastAPI(
    title="AI Force Migration Platform API",
    description="AI-powered cloud migration management platform",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Basic health check that's always available
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "ai-force-migration-api",
        "version": "0.2.0",
        "timestamp": "2025-01-27"
    }

# Basic root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Force Migration Platform API",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# Initialize components with error handling
DATABASE_ENABLED = False
WEBSOCKET_ENABLED = False
API_ROUTES_ENABLED = False
API_ROUTES_ERROR = None

try:
    from app.core.config import settings, get_database_url
    print("✅ Configuration loaded successfully")
    CONFIG_LOADED = True
except Exception as e:
    print(f"⚠️  Configuration error: {e}")
    # Create minimal settings
    class MinimalSettings:
        FRONTEND_URL = "http://localhost:8081"
        ENVIRONMENT = "production"
        DEBUG = False
        ALLOWED_ORIGINS = ["http://localhost:8081"]
        DATABASE_URL = "postgresql://localhost:5432/migration_db"
        
        @property
        def allowed_origins_list(self):
            return self.ALLOWED_ORIGINS.split(",") if isinstance(self.ALLOWED_ORIGINS, str) else self.ALLOWED_ORIGINS
    
    settings = MinimalSettings()
    def get_database_url():
        return settings.DATABASE_URL

try:
    from version import __version__, API_TITLE, API_DESCRIPTION, BUILD_INFO
    # Update app metadata
    app.title = API_TITLE
    app.description = API_DESCRIPTION
    app.version = __version__
    print("✅ Version information loaded")
except Exception as e:
    print(f"⚠️  Version info error: {e}")

# Try to import database components
try:
    from app.core.database import engine, Base, SQLALCHEMY_AVAILABLE
    from app.models.client_account import ClientAccount
    from app.models.data_import import *
    DATABASE_ENABLED = SQLALCHEMY_AVAILABLE
    print("✅ Database components loaded")
except Exception as e:
    print(f"⚠️  Database components not available: {e}")
    DATABASE_ENABLED = False
    engine = None
    Base = None

# Try to import API routes
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix="/api/v1")
    API_ROUTES_ENABLED = True
    print("✅ API v1 routes loaded successfully")
except Exception as e:
    print(f"⚠️  API v1 routes error: {e}")
    API_ROUTES_ERROR = str(e)

# Try to import API v2 routes
try:
    from app.api.v2.api import api_v2_router
    app.include_router(api_v2_router, prefix="/api/v2")
    print("✅ API v2 routes loaded successfully")
    
    # Include v2 router directly to avoid /api/v1 prefix
    try:
        from app.api.v1.discovery_flow_v2 import router as discovery_flow_v2_router
        app.include_router(discovery_flow_v2_router, prefix="/api/v2/discovery-flows", tags=["Discovery Flow v2 - Multi-Flow Architecture"])
        print("✅ V2 Discovery Flow router loaded successfully")
    except Exception as e:
        print(f"⚠️  V2 Discovery Flow router could not be loaded: {e}")
    
    # Test if discovery routes are available
    try:
        routes_list = [route.path for route in api_router.routes]
        discovery_routes = [route for route in routes_list if 'discovery' in route]
        print(f"📋 Discovery routes available: {discovery_routes}")
    except Exception as e:
        print(f"⚠️  Could not enumerate routes: {e}")
        
except Exception as e:
    print(f"⚠️  API routes could not be loaded: {e}")
    with open("api_routes_error.log", "w") as f:
        traceback.print_exc(file=f)
    print(f"📋 Traceback: {traceback.format_exc()}")
    API_ROUTES_ENABLED = False
    API_ROUTES_ERROR = str(e)

# WebSocket support removed for Vercel+Railway compatibility
WEBSOCKET_ENABLED = False
print("ℹ️  WebSocket support disabled - using HTTP polling for Vercel+Railway compatibility")

# CORS middleware configuration
# Build origins list from multiple sources
cors_origins = [
    "http://localhost:8081",  # Fixed frontend port
    "http://localhost:3000",  # React dev server (fallback)
    "http://localhost:5173",  # Vite dev server (fallback)
    getattr(settings, 'FRONTEND_URL', "http://localhost:8081")
]

# Add origins from environment variable
if hasattr(settings, 'allowed_origins_list'):
    cors_origins.extend(settings.allowed_origins_list)

# Add specific Vercel domains (wildcard patterns don't work with FastAPI CORS)
cors_origins.extend([
    "https://aiforce-assess.vercel.app",  # Specific Vercel domain
    "https://aiforce-assess-git-main-chockas-projects.vercel.app",  # Git branch deployments
    "https://aiforce-assess-chockas-projects.vercel.app",  # Project-specific domain
])

# Add Railway deployment patterns
cors_origins.extend([
    "https://migrate-ui-orchestrator-production.up.railway.app",  # Specific Railway domain
])

# Remove duplicates and filter out empty strings
cors_origins = list(set(filter(None, cors_origins)))

print(f"🌐 CORS Origins configured: {cors_origins}")

# CORS middleware configuration first (CRITICAL: Middleware runs in reverse order)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add context middleware (Task 1.2.3)
try:
    from app.core.middleware import ContextMiddleware, RequestLoggingMiddleware
    
    # CRITICAL: Middleware is executed in REVERSE order of addition.
    # Order: RequestLogging -> Context -> CORS
    
    # Add context middleware with updated exempt paths
    app.add_middleware(
        ContextMiddleware,
        require_client=True,
        require_engagement=True,  # SECURITY: Require engagement context for multi-tenancy
        exempt_paths=[
            "/health",
            "/",
            "/docs", 
            "/redoc",
            "/openapi.json",
            "/debug/routes",
            "/static",
            "/api/v1/assets/list/paginated",  # allow unauthenticated inventory preview
            "/api/v1/me",  # Allow user context endpoint
            "/api/v1/clients/default",  # Allow default client endpoint
            "/api/v1/clients/public",  # Allow public clients list endpoint for context establishment
            "/api/v1/clients",  # Allow clients list endpoint for context establishment
            "/api/v1/clients/",  # Allow clients list endpoint with trailing slash
            # Context establishment endpoints - these are needed to establish context
            "/api/v1/context/clients",  # New dedicated context establishment endpoint
            "/api/v1/context/engagements",  # New dedicated context establishment endpoint
            # Data import endpoints that need to work before context is established
            "/api/v1/data-import/latest-import",  # Allow checking for existing data
            "/api/v1/data-import/status",  # Allow checking import status
            # Discovery flow status endpoints that may be called before context
            # Removed /api/v1/discovery/flow/active - now requires context for RBAC
            "/api/v1/discovery/flow/status",  # Allow checking flow status
            "/api/v1/unified-discovery/flow/health",  # Allow health checks
            "/api/v1/unified-discovery/flow/status",  # Allow flow status checks
            "/api/v2/discovery-flows/health",  # Allow v2 discovery flows health check
            # Authentication endpoints - should not require context
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/registration-status",
            "/api/v1/auth/health",
            "/api/v1/auth/demo/create-admin-user",
            "/api/v1/auth/demo/status",
            "/api/v1/auth/demo/reset",
            "/api/v1/auth/demo/health",
            "/api/v1/auth/system/info",
            # Admin dashboard endpoints - should be global, not client-scoped
            "/api/v1/auth/admin/dashboard-stats",
            "/api/v1/admin/clients/dashboard/stats",
            "/api/v1/admin/engagements/dashboard/stats",
            "/api/v1/admin/clients/health",
            "/api/v1/admin/engagements/health",
            # Admin CRUD endpoints - should be global for admin management
            "/api/v1/admin/clients",
            "/api/v1/admin/clients/",
            "/api/v1/admin/engagements",
            "/api/v1/admin/engagements/",
            "/api/v1/admin/users",
            "/api/v1/admin/users/",
            "/api/v1/admin/user-profiles",
            "/api/v1/admin/user-profiles/",
            "/api/v1/auth/admin/create-user",
            "/api/v1/auth/pending-approvals",
            "/api/v1/auth/approve-user",
            "/api/v1/auth/reject-user",
            "/api/v1/auth/active-users",
            "/api/v1/auth/admin/access-logs",
            # User profile endpoint requires authentication but allows admin access without client context via role-based exemption
            "/api/v1/me",
            "/api/v1/context/me"  # Actual location of the /me endpoint
        ]
    )
    
    # Add request logging middleware last
    app.add_middleware(
        RequestLoggingMiddleware,
        excluded_paths=["/health"]
    )

    print("✅ Middleware loaded successfully in correct order: CORS -> Context -> Logging")
except Exception as e:
    print(f"⚠️  Middleware could not be loaded: {e}")
    print(f"📋 Traceback: {traceback.format_exc()}")

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to see what routes are loaded."""
    routes_info = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes_info.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": getattr(route, 'name', 'unnamed')
            })
    
    return {
        "total_routes": len(routes_info),
        "api_routes_enabled": API_ROUTES_ENABLED,
        "api_routes_error": API_ROUTES_ERROR,
        "routes": routes_info[:20],  # First 20 routes
        "discovery_routes": [r for r in routes_info if 'discovery' in r['path']]
    }

@app.get("/debug/test-dependency")
async def debug_test_dependency(
    request: Request,
    context: RequestContext = Depends(get_current_context)
):
    """Test endpoint to debug the context dependency injection."""
    try:
        return {
            "path": request.url.path,
            "headers": dict(request.headers),
            "dependency_context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_id": context.user_id,
                "session_id": context.session_id
            },
            "validation_status": "dependency_success"
        }
    except Exception as e:
        return {
            "path": request.url.path,
            "headers": dict(request.headers),
            "error": str(e),
            "validation_status": "dependency_failed"
        }

@app.get("/debug/context-middleware")
async def debug_context_middleware(request: Request):
    """Debug endpoint to test context middleware behavior for data-import paths."""
    try:
        from app.core.context import get_current_context
        context = get_current_context()
        
        return {
            "path": request.url.path,
            "headers": dict(request.headers),
            "middleware_context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_id": context.user_id,
                "session_id": context.session_id
            },
            "validation_status": "middleware_success"
        }
    except Exception as e:
        return {
            "path": request.url.path,
            "headers": dict(request.headers),
            "error": str(e),
            "validation_status": "middleware_failed"
        }

@app.get("/debug/context")
async def debug_context(request: Request):
    """Debug endpoint to test context extraction."""
    try:
        from app.core.context import extract_context_from_request
        context = extract_context_from_request(request)
        
        return {
            "headers": dict(request.headers),
            "extracted_context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id,
                "user_id": context.user_id,
                "session_id": context.session_id
            },
            "validation_status": "success"
        }
    except Exception as e:
        return {
            "headers": dict(request.headers),
            "error": str(e),
            "validation_status": "failed"
        }

# Update health check with component status
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "ai-force-migration-api",
        "version": getattr(app, 'version', '0.2.0'),
        "components": {
            "database": DATABASE_ENABLED,
            "websocket": WEBSOCKET_ENABLED,
            "api_routes": API_ROUTES_ENABLED
        },
        "environment": getattr(settings, 'ENVIRONMENT', 'production'),
        "error": API_ROUTES_ERROR
    }

# WebSocket endpoint removed - using HTTP polling for Vercel+Railway compatibility

if __name__ == "__main__":
    # Port assignment - Use Railway PORT or default to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    ) 