"""
AI Force Migration Platform - FastAPI Backend
Main application entry point with CORS, routing, and WebSocket support.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.config import settings
from version import __version__, API_TITLE, API_DESCRIPTION, BUILD_INFO

# Try to import database components
try:
    from app.core.database import engine, Base, SQLALCHEMY_AVAILABLE
    from app.api.v1.api import api_router
    DATABASE_ENABLED = SQLALCHEMY_AVAILABLE
except ImportError as e:
    print(f"Database components not available: {e}")
    DATABASE_ENABLED = False
    engine = None
    Base = None

# Try to import WebSocket manager
try:
    from app.websocket.manager import ConnectionManager
    WEBSOCKET_ENABLED = True
except ImportError as e:
    print(f"WebSocket manager not available: {e}")
    WEBSOCKET_ENABLED = False
    class ConnectionManager:
        def __init__(self):
            pass

# Create FastAPI application
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",  # Fixed frontend port
        "http://localhost:3000",  # React dev server (fallback)
        "http://localhost:5173",  # Vite dev server (fallback)
        "https://*.railway.app",  # Railway deployment
        settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') and settings.FRONTEND_URL else "http://localhost:8081"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
if WEBSOCKET_ENABLED:
    manager = ConnectionManager()

# Include API routes if database is available
if DATABASE_ENABLED:
    try:
        app.include_router(api_router, prefix="/api/v1")
        print("✅ API routes loaded successfully")
    except Exception as e:
        print(f"⚠️  API routes could not be loaded: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup."""
    print("🚀 AI Force Migration Platform API starting...")
    
    if DATABASE_ENABLED and engine:
        try:
            # Create database tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
        except Exception as e:
            print(f"⚠️  Database initialization failed: {e}")
    else:
        print("⚠️  Database not available - running in limited mode")
    
    print(f"📊 Database: {'Enabled' if DATABASE_ENABLED else 'Disabled'}")
    print(f"🌐 Frontend URL: {getattr(settings, 'FRONTEND_URL', 'Not configured')}")
    print(f"📝 API Documentation: http://localhost:8000/docs")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": API_TITLE,
        "version": __version__,
        "status": "running",
        "database_enabled": DATABASE_ENABLED,
        "websocket_enabled": WEBSOCKET_ENABLED,
        "docs": "/docs",
        "build_info": BUILD_INFO
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "ai-force-migration-api",
        "version": __version__,
        "database_enabled": DATABASE_ENABLED,
        "websocket_enabled": WEBSOCKET_ENABLED
    }

if WEBSOCKET_ENABLED:
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """WebSocket endpoint for real-time updates."""
        await manager.connect(websocket, client_id)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.send_personal_message(f"Echo: {data}", client_id)
        except WebSocketDisconnect:
            manager.disconnect(client_id)
            await manager.broadcast(f"Client {client_id} disconnected")

if __name__ == "__main__":
    # Port assignment - Use Railway PORT or default to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    ) 