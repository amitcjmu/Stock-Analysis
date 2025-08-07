"""
AI Modernize Migration Platform - FastAPI Backend
Main application entry point with CORS, routing, and WebSocket support.
"""

# Standard library imports
import logging
import os
import uuid
from contextlib import asynccontextmanager

# Third-party imports
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Disable OpenTelemetry before any other app imports to prevent connection errors
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")
os.environ.setdefault("OTEL_PYTHON_DISABLED_INSTRUMENTATIONS", "all")

# Configure Rich console early to prevent display conflicts
from app.core.rich_config import configure_rich_for_backend  # noqa: E402

configure_rich_for_backend()

# Import error handlers
try:
    from app.api.error_handlers import register_error_handlers

    ERROR_HANDLERS_AVAILABLE = True
except ImportError:
    ERROR_HANDLERS_AVAILABLE = False
    print("Warning: Error handlers not available")

# Load environment variables
load_dotenv()

# Import DeepInfra response fix for early startup application
# Note: patch_litellm_response_parsing is applied automatically on import
try:
    from app.services.deepinfra_response_fixer import (
        patch_litellm_response_parsing,  # noqa: F401
    )

    logger = logging.getLogger(__name__)
    logger.info("✅ DeepInfra response fixer module loaded")
except ImportError as e:
    print(f"Warning: Could not load DeepInfra response fixer: {e}")

# Database migrations will be handled by entrypoint.sh in Railway deployment

# Import context dependencies
try:
    from app.core.context import RequestContext, get_current_context_dependency

    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False
    print("Warning: Context dependencies not available")

# Import our structured logging module
try:
    from app.core.logging import configure_logging, get_logger, set_trace_id

    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError:
    STRUCTURED_LOGGING_AVAILABLE = False

    # Fallback to basic logging
    def configure_logging():
        """Fallback logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        print("⚠️  Using fallback logging configuration")


# Configure logging before any other imports
if STRUCTURED_LOGGING_AVAILABLE:
    # Use structured JSON logging in production
    env = os.getenv("ENVIRONMENT", "production")
    log_format = "json" if env == "production" else "text"
    configure_logging(level="INFO", format=log_format, enable_security_filter=True)
    logger = get_logger(__name__)
    logger.info("✅ Structured logging configured", extra={"environment": env})
else:
    configure_logging()
    logger = logging.getLogger(__name__)


# Lifespan event handler (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # Startup logic
    logger.info("🚀 Application starting up...")

    # Initialize RBAC system
    try:
        from app.api.v1.auth.rbac import initialize_rbac_system

        await initialize_rbac_system()
    except Exception as e:
        logger.warning(f"RBAC initialization warning: {e}")

    # Initialize Master Flow Orchestrator configurations
    try:
        from app.core.flow_initialization import initialize_flows_on_startup

        logger.info("🔄 Initializing Master Flow Orchestrator configurations...")
        flow_init_results = initialize_flows_on_startup()
        if flow_init_results.get("success", False):
            logger.info("✅ Master Flow Orchestrator initialized successfully")
        else:
            errors = flow_init_results.get("initialization", {}).get("errors", [])
            logger.warning(f"Flow initialization completed with issues: {errors}")
    except Exception as e:
        logger.warning(f"Flow initialization warning: {e}", exc_info=True)
        # Don't fail startup on flow initialization issues

    # Initialize LLM rate limiting to prevent 429 errors
    try:
        logger.info("🔄 Initializing LLM rate limiting...")
        # Enable rate limiting by default
        os.environ["ENABLE_LLM_RATE_LIMITING"] = "true"

        # Enable full CrewAI functionality - no bypasses for testing
        # os.environ["BYPASS_CREWAI_FOR_FIELD_MAPPING"] = "true"
        logger.info("✅ Full CrewAI functionality enabled - no bypasses")

        # Log rate limiting configuration
        from app.services.simple_rate_limiter import simple_rate_limiter

        logger.info(
            f"✅ LLM rate limiting enabled: {simple_rate_limiter.max_tokens} requests/minute"
        )
    except Exception as e:
        logger.warning(f"LLM rate limiting initialization warning: {e}")

    logger.info("✅ Startup logic completed.")

    # Test database connection
    if DATABASE_ENABLED:
        try:
            logger.info("🔧 Testing database connection...")
            from app.core.database import db_manager

            health_check_result = await db_manager.health_check()
            if health_check_result:
                logger.info("✅✅✅ Database connection test successful.")

                # Migrations are handled by deployment scripts

                # Initialize database with required data (platform admin, test users in development)
                if os.getenv("SKIP_DB_INIT", "false").lower() != "true":
                    try:
                        from app.core.database import AsyncSessionLocal
                        from app.core.database_initialization import initialize_database

                        logger.info("📦 Initializing database with required data...")
                        async with AsyncSessionLocal() as db:
                            await initialize_database(db)
                        logger.info("✅ Database initialization completed")
                    except Exception as e:
                        logger.warning(f"Database initialization warning: {e}")
                        # Don't fail startup on initialization issues
            else:
                logger.warning("⚠️⚠️⚠️ Database connection test failed, but continuing...")

        except Exception as e:
            logger.warning(f"⚠️⚠️⚠️ Database connection test failed: {e}", exc_info=True)
            # Don't fail startup on database connection issues

    # Start flow health monitor
    try:
        logger.info("🔄 Starting flow health monitor...")
        from app.services.flow_health_monitor import flow_health_monitor

        await flow_health_monitor.start()
        logger.info("✅ Flow health monitor started successfully")
    except Exception as e:
        logger.warning(f"Flow health monitor initialization warning: {e}")

    # Yield control to the application
    yield

    # Shutdown logic (if needed)
    logger.info("🔄 Application shutting down...")

    # Stop flow health monitor
    try:
        from app.services.flow_health_monitor import flow_health_monitor

        await flow_health_monitor.stop()
        logger.info("✅ Flow health monitor stopped")
    except Exception as e:
        logger.warning(f"Error stopping flow health monitor: {e}")

    logger.info("✅ Shutdown logic completed.")


# Initialize basic app first to ensure health check is always available
fastapi_app = FastAPI(
    title="AI Modernize Migration Platform API",
    description="AI-powered cloud migration management platform",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Health check is defined later with more comprehensive component status


@fastapi_app.get("/cors-test")
async def cors_test():
    """Simple endpoint to test CORS configuration."""
    return {
        "message": "CORS is working!",
        "timestamp": "2025-07-08",
        "status": "success",
    }


# Basic root endpoint
@fastapi_app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Modernize Migration Platform API",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


# Initialize components with error handling
DATABASE_ENABLED = False
WEBSOCKET_ENABLED = False
API_ROUTES_ENABLED = False
API_ROUTES_ERROR = None

try:
    from app.core.config import get_database_url, settings

    logger.info("✅ Configuration loaded successfully")
    CONFIG_LOADED = True
except Exception as e:
    logger.warning(f"Configuration error: {e}")

    # Create minimal settings
    class MinimalSettings:
        FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8081")
        ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
        DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8081")
        DATABASE_URL = os.getenv(
            "DATABASE_URL", "postgresql://localhost:5432/migration_db"
        )

        @property
        def allowed_origins_list(self):
            return (
                self.ALLOWED_ORIGINS.split(",")
                if isinstance(self.ALLOWED_ORIGINS, str)
                else self.ALLOWED_ORIGINS
            )

    settings = MinimalSettings()

    def get_database_url():
        return settings.DATABASE_URL


try:
    from version import API_DESCRIPTION, API_TITLE, __version__

    # Update app metadata
    fastapi_app.title = API_TITLE
    fastapi_app.description = API_DESCRIPTION
    fastapi_app.version = __version__
    logger.info("✅ Version information loaded")
except Exception as e:
    logger.warning(f"Version info error: {e}")

# Try to import database components
try:
    import app.models.data_import  # noqa: F401,F811
    from app.core.database import SQLALCHEMY_AVAILABLE, Base, engine

    DATABASE_ENABLED = SQLALCHEMY_AVAILABLE
    logger.info("✅ Database components loaded")
except Exception as e:
    logger.warning(f"Database components not available: {e}")
    DATABASE_ENABLED = False
    engine = None
    Base = None

# Try to import API routes
try:
    from app.api.v1.api import api_router

    fastapi_app.include_router(api_router, prefix="/api/v1")
    API_ROUTES_ENABLED = True
    logger.info("✅ API v1 routes loaded successfully")
except Exception as e:
    logger.warning(f"API v1 routes error: {e}")
    API_ROUTES_ERROR = str(e)

# V3 API routes removed - replaced by unified API
API_V3_ROUTES_ENABLED = False
API_V3_ROUTES_ERROR = "V3 API archived - was legacy database abstraction layer"
logger.info("✅ V3 API routes archived - legacy database abstraction removed")

# WebSocket support removed for Vercel+Railway compatibility
WEBSOCKET_ENABLED = False
logger.info(
    "ℹ️  WebSocket support disabled - using HTTP polling for Vercel+Railway compatibility"
)


# CORS middleware configuration - Secure setup based on environment
def get_cors_origins():
    """Get CORS origins based on environment."""
    cors_origins = []

    # Get environment - check multiple possible values
    env = getattr(settings, "ENVIRONMENT", "development").lower()
    is_dev = env in ["development", "dev", "local", "localhost"]

    logger.info(f"Environment detected: {env}, is_development: {is_dev}")

    # Development environment (default to development for safety)
    if is_dev or env not in ["production", "prod"]:
        cors_origins.extend(
            [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",
                "http://localhost:8081",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8081",
            ]
        )
        logger.info("Using development CORS origins")

    # Production environment - only specific domains
    else:
        cors_origins.extend(
            [
                "https://aiforce-assess.vercel.app",
                "https://migrate-ui-orchestrator-production.up.railway.app",
            ]
        )
        logger.info("Using production CORS origins")

    # Railway/Vercel detection - if we detect Railway deployment, force production origins
    if (
        os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("RAILWAY_PROJECT_NAME")
        or os.getenv("PORT")
        or "railway.app" in os.getenv("DATABASE_URL", "")
    ):
        cors_origins.extend(
            [
                "https://aiforce-assess.vercel.app",
                "https://migrate-ui-orchestrator-production.up.railway.app",
            ]
        )
        logger.info("Railway deployment detected - adding production CORS origins")

    # Add frontend URL from settings if specified
    if hasattr(settings, "FRONTEND_URL") and settings.FRONTEND_URL:
        cors_origins.append(settings.FRONTEND_URL)

    # Add explicit allowed origins from environment
    if hasattr(settings, "allowed_origins_list"):
        cors_origins.extend(settings.allowed_origins_list)

    # Ensure Vercel domain is always included if we're on Railway or in production
    if (
        (os.getenv("DATABASE_URL") and "railway.app" in os.getenv("DATABASE_URL", ""))
        or os.getenv("PORT")
        or os.getenv("RAILWAY_ENVIRONMENT")
        or env == "production"
    ):
        vercel_domain = "https://aiforce-assess.vercel.app"
        if vercel_domain not in cors_origins:
            cors_origins.append(vercel_domain)
            logger.info(f"Force-added Vercel domain to CORS origins: {vercel_domain}")

    # Remove duplicates and filter out empty strings
    return list(set(filter(None, cors_origins)))


cors_origins = get_cors_origins()

logger.info(f"🌐 CORS Origins configured: {cors_origins}")
logger.info(f"🌐 Total CORS origins: {len(cors_origins)}")

# Debug: Print each origin
for i, origin in enumerate(cors_origins):
    logger.info(f"🌐 CORS Origin {i+1}: {origin}")

# Add context middleware (Task 1.2.3)
ENABLE_MIDDLEWARE = True  # Production setting

if ENABLE_MIDDLEWARE:
    try:
        # Import request tracking middleware
        from starlette.middleware.base import BaseHTTPMiddleware

        from app.core.middleware import ContextMiddleware, RequestLoggingMiddleware
        from app.middleware.adaptive_rate_limit_middleware import (
            AdaptiveRateLimitMiddleware,
        )
        from app.middleware.security_headers import (
            SecurityAuditMiddleware,
            SecurityHeadersMiddleware,
        )

        class TraceIDMiddleware(BaseHTTPMiddleware):
            """Middleware to add trace ID to all requests"""

            async def dispatch(self, request: Request, call_next):
                # Generate or extract trace ID
                trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())

                # Set trace ID in context
                if STRUCTURED_LOGGING_AVAILABLE:
                    set_trace_id(trace_id)

                # Process request
                response = await call_next(request)

                # Add trace ID to response headers
                response.headers["X-Trace-ID"] = trace_id

                return response

        # Add trace ID middleware first (executes last)
        fastapi_app.add_middleware(TraceIDMiddleware)
        logger.info("✅ Trace ID middleware added")

        # CRITICAL: Middleware is executed in REVERSE order of addition.
        # Actual execution order will be: CORS -> Context -> RequestLogging
        # This ensures CORS headers are added to ALL responses, including errors

        # Import tenant context middleware for RLS
        from app.middleware.tenant_context import TenantContextMiddleware

        # Add tenant context middleware (for Row-Level Security)
        fastapi_app.add_middleware(TenantContextMiddleware)
        logger.info("✅ Tenant context middleware added for RLS")

        # Add context middleware with app-specific additional exempt paths
        # Core paths (health, auth, docs) are handled by middleware defaults
        app_specific_exempt_paths = [
            # User registration - creates inactive users pending approval (security testing)
            "/auth/register",
            "/api/v1/auth/register",  # Full API path for registration
            # Context establishment endpoints - these are needed to establish context
            "/api/v1/context/me",  # User context endpoint - needed before client context
            "/api/v1/clients/default",  # Allow default client endpoint
            "/api/v1/clients",  # Allow clients list endpoint for context establishment
            "/api/v1/clients/",  # Allow clients list endpoint with trailing slash
            "/api/v1/context/clients",  # New dedicated context establishment endpoint
            "/api/v1/context/clients/",  # With trailing slash
            "/api/v1/context/engagements",  # New dedicated context establishment endpoint
            "/api/v1/context/engagements/",  # With trailing slash
            "/api/v1/context-establishment/clients",  # Correct context establishment endpoint
            "/api/v1/context-establishment/engagements",  # Correct context establishment endpoint
            # Admin endpoints - these handle their own authentication via RBAC
            "/api/v1/admin/clients/dashboard/stats",  # Admin dashboard stats
            "/api/v1/admin/engagements/dashboard/stats",  # Admin engagement stats
            "/api/v1/auth/admin/dashboard-stats",  # Admin user stats
            # Platform admin endpoints should bypass client/engagement requirements
            "/api/v1/admin/",  # All admin endpoints
            "/api/v1/auth/admin/",  # All auth admin endpoints
            # NO DEMO FALLBACK - All users must be authenticated
            # Data import endpoints that need to work before context is established
            "/api/v1/data-import/latest-import",  # Allow checking for existing data
            "/api/v1/data-import/status",  # Allow checking import status
            # Discovery flow status endpoints that may be called before context
            "/api/v1/discovery/flow/status",  # Allow checking flow status
            "/api/v1/unified-discovery/flow/health",  # Allow health checks
            "/api/v1/unified-discovery/flow/status",  # Allow flow status checks
            # Note: Auth and health endpoints are handled by middleware defaults
        ]

        fastapi_app.add_middleware(
            ContextMiddleware,
            require_client=True,
            require_engagement=True,  # SECURITY: Require engagement context for multi-tenancy
            additional_exempt_paths=app_specific_exempt_paths,  # Extend defaults, don't replace
        )

        # Add request logging middleware first (will execute last)
        fastapi_app.add_middleware(RequestLoggingMiddleware, excluded_paths=["/health"])

        # Add adaptive rate limiting middleware
        fastapi_app.add_middleware(AdaptiveRateLimitMiddleware)

        # Add security audit middleware
        fastapi_app.add_middleware(SecurityAuditMiddleware)

        # Add security headers middleware last (will execute first after CORS)
        fastapi_app.add_middleware(SecurityHeadersMiddleware)

        # Add Redis cache middleware (only for GET requests)
        if settings.REDIS_ENABLED:
            try:
                from app.middleware.cache_middleware import (
                    CacheInstrumentationMiddleware,
                    CacheMiddleware,
                )

                fastapi_app.add_middleware(CacheMiddleware)
                fastapi_app.add_middleware(CacheInstrumentationMiddleware)
                logger.info("✅ Redis cache middleware added")
            except ImportError as e:
                logger.warning(f"Could not import cache middleware: {e}")

        logger.info("✅ Middleware loaded successfully")
    except Exception as e:
        logger.warning(f"Middleware could not be loaded: {e}", exc_info=True)
else:
    logger.info("🚫 Middleware disabled for CORS debugging")

# Add CORS middleware LAST so it executes FIRST (middleware runs in reverse order)
# This ensures CORS headers are added to ALL responses, including error responses
logger.info("🌐 Adding CORS middleware with the following configuration:")
logger.info(f"🌐 allow_origins: {cors_origins}")
logger.info("🌐 allow_credentials: True")
logger.info("🌐 allow_methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH']")

# Production-safe CORS configuration
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Client-Account-ID",
        "X-Client-ID",
        "X-Engagement-ID",
        "X-Trace-ID",
        "X-Request-ID",
        "X-User-ID",
        "X-User-Role",
        "X-Flow-ID",
        "Cache-Control",
        "Pragma",
        "Accept",
        "Accept-Language",
        "Accept-Encoding",
        "Content-Language",
    ],
    expose_headers=["X-Trace-ID", "X-RateLimit-Limit", "X-RateLimit-Reset"],
    max_age=3600,
)
logger.info("✅ CORS middleware added - will process all responses including errors")

# Register error handlers if available
if ERROR_HANDLERS_AVAILABLE:
    register_error_handlers(fastapi_app)
    logger.info("✅ Error handlers registered")
else:
    logger.warning("⚠️  Error handlers not available")


@fastapi_app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to see what routes are loaded."""
    routes_info = []
    for route in fastapi_app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes_info.append(
                {
                    "path": route.path,
                    "methods": list(route.methods) if route.methods else [],
                    "name": getattr(route, "name", "unnamed"),
                }
            )

    return {
        "total_routes": len(routes_info),
        "api_v1_enabled": API_ROUTES_ENABLED,
        "api_v3_enabled": API_V3_ROUTES_ENABLED,
        "errors": {"api_v1": API_ROUTES_ERROR, "api_v3": API_V3_ROUTES_ERROR},
        "routes": routes_info[:20],  # First 20 routes
        "discovery_routes": [r for r in routes_info if "discovery" in r["path"]],
        "v3_routes": [r for r in routes_info if "/api/v3/" in r["path"]],
    }


@fastapi_app.get("/debug/test-dependency")
async def debug_test_dependency(
    request: Request, context: RequestContext = Depends(get_current_context_dependency)
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
                "flow_id": getattr(context, "flow_id", None),
            },
            "validation_status": "dependency_success",
        }
    except Exception as e:
        return {
            "path": request.url.path,
            "headers": dict(request.headers),
            "error": str(e),
            "validation_status": "dependency_failed",
        }


@fastapi_app.get("/debug/context-middleware")
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
                "flow_id": getattr(context, "flow_id", None),
            },
            "validation_status": "middleware_success",
        }
    except Exception as e:
        return {
            "path": request.url.path,
            "headers": dict(request.headers),
            "error": str(e),
            "validation_status": "middleware_failed",
        }


@fastapi_app.get("/debug/context")
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
                "flow_id": getattr(context, "flow_id", None),
            },
            "validation_status": "success",
        }
    except Exception as e:
        return {
            "headers": dict(request.headers),
            "error": str(e),
            "validation_status": "failed",
        }


# Update health check with component status
@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "ai-force-migration-api",
        "version": getattr(fastapi_app, "version", "0.2.0"),
        "components": {
            "database": DATABASE_ENABLED,
            "websocket": WEBSOCKET_ENABLED,
            "api_routes": API_ROUTES_ENABLED,
            "api_v3_routes": API_V3_ROUTES_ENABLED,
        },
        "environment": getattr(settings, "ENVIRONMENT", "production"),
        "errors": {"api_v1": API_ROUTES_ERROR, "api_v3": API_V3_ROUTES_ERROR},
    }


# WebSocket endpoint removed - using HTTP polling for Vercel+Railway compatibility

# Create aliases for backward compatibility and deployment
# Alias for ASGI compatibility
application = fastapi_app


# For docker-compose compatibility (avoid conflict with app module import)
# This allows docker-compose files to use main:app
def create_app():
    return fastapi_app


# Direct alias for deployment (replacing previous definition at line 281)
app = fastapi_app  # Final app definition for deployment compatibility  # noqa: F811

if __name__ == "__main__":
    # Port assignment - Use Railway PORT or default to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run(
        "main:fastapi_app",
        host="0.0.0.0",  # nosec B104 - bind to all interfaces for container deployment
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False,
    )
