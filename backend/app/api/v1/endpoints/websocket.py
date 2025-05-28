"""
WebSocket API endpoints.
Handles WebSocket connections and real-time communication.
"""

from fastapi import APIRouter, WebSocket, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

# Import 6R WebSocket functionality
try:
    from app.api.v1.endpoints.sixr_websocket import websocket_endpoint, get_websocket_stats
    from app.core.database import get_db
    SIXR_WS_AVAILABLE = True
except ImportError:
    SIXR_WS_AVAILABLE = False

router = APIRouter()


@router.get("/stats")
async def get_websocket_stats_endpoint():
    """Get WebSocket connection statistics."""
    from app.websocket.manager import ConnectionManager
    manager = ConnectionManager()
    stats = manager.get_connection_stats()
    
    # Add 6R WebSocket stats if available
    if SIXR_WS_AVAILABLE:
        sixr_stats = get_websocket_stats()
        stats["sixr_analysis"] = sixr_stats
    
    return stats


@router.post("/broadcast")
async def broadcast_message():
    """Broadcast message to all connected clients - placeholder endpoint."""
    return {"message": "WebSocket broadcast endpoint - available now"}


@router.get("/health")
async def websocket_health():
    """WebSocket service health check."""
    return {"status": "healthy", "service": "websocket"}


# 6R Analysis WebSocket endpoint
if SIXR_WS_AVAILABLE:
    @router.websocket("/sixr/{analysis_id}")
    async def sixr_analysis_websocket(
        websocket: WebSocket,
        analysis_id: int,
        user_id: Optional[str] = Query(None),
        db: Session = Depends(get_db)
    ):
        """
        WebSocket endpoint for 6R analysis real-time updates.
        
        Connect to receive real-time updates for:
        - Analysis progress
        - Parameter changes  
        - Recommendation updates
        - Agent activity
        - Error notifications
        """
        await websocket_endpoint(websocket, analysis_id, user_id, db) 