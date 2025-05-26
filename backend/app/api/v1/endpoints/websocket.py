"""
WebSocket API endpoints.
Handles WebSocket connections and real-time communication.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    from app.websocket.manager import ConnectionManager
    manager = ConnectionManager()
    return manager.get_connection_stats()


@router.post("/broadcast")
async def broadcast_message():
    """Broadcast message to all connected clients - placeholder endpoint."""
    return {"message": "WebSocket broadcast endpoint - available now"}


@router.get("/health")
async def websocket_health():
    """WebSocket service health check."""
    return {"status": "healthy", "service": "websocket"} 