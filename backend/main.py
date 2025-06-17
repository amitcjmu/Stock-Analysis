"""
AI Force Migration Platform - FastAPI Backend
Main application entry point with CORS, routing, and WebSocket support.
"""

import sys
import traceback
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from contextlib import asynccontextmanager
from pathlib import Path

# Load environment variables
load_dotenv()

# Initialize basic app first to ensure health check is always available
app = FastAPI(
    title="AI Force Migration Platform API",
    description="AI-powered cloud migration management platform",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    print("✅ API routes loaded successfully")
    
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

# Try to import WebSocket manager
try:
    from app.websocket.manager import ConnectionManager
    manager = ConnectionManager()
    WEBSOCKET_ENABLED = True
    print("✅ WebSocket manager loaded")
except Exception as e:
    print(f"⚠️  WebSocket manager not available: {e}")
    WEBSOCKET_ENABLED = False
    class DummyConnectionManager:
        def __init__(self):
            pass
    manager = DummyConnectionManager()

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
        require_engagement=False,
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
            "/api/v1/clients/default"  # Allow default client endpoint
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

@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    Initializes services and creates database tables.
    """
    print("🚀 Application starting up...")
    
    # Initialize services here if needed
    
    print("✅ Startup logic completed.")

    # Create database tables
    if DATABASE_ENABLED:
        try:
            print("🔧 Initializing database schema...")
            # Create a synchronous engine for migrations or sync operations
            sync_engine_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg")
            sync_engine = create_engine(sync_engine_url)

            # Log registered tables
            if hasattr(Base, 'metadata'):
                table_names = list(Base.metadata.tables.keys())
                print(f"SQLAlchemy metadata has {len(table_names)} tables registered.")
                print(f"Registered tables: {table_names}")

            # Use a synchronous connection to create tables
            # The async version was causing issues during initial setup
            Base.metadata.create_all(bind=sync_engine)
            
            print("✅✅✅ Database schema initialization command executed successfully.")
            
        except Exception as e:
            print(f"❌❌❌ Database schema initialization failed: {e}")
            import traceback
            traceback.print_exc()

if WEBSOCKET_ENABLED:
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket endpoint for real-time updates."""
        try:
            await manager.connect(websocket, client_id)
            while True:
                data = await websocket.receive_text()
                await manager.send_personal_message(f"Echo: {data}", client_id)
        except WebSocketDisconnect:
            manager.disconnect(client_id)
            await manager.broadcast(f"Client {client_id} disconnected")
        except Exception as e:
            print(f"WebSocket error: {e}")

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