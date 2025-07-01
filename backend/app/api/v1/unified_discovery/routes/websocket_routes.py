"""
Discovery WebSocket route handlers.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["discovery-websocket"])


@router.websocket("/flow-status/{flow_id}")
async def websocket_flow_status(websocket: WebSocket, flow_id: str):
    """WebSocket endpoint for real-time flow status updates."""
    await websocket.accept()
    
    try:
        while True:
            # Placeholder for real-time status updates
            await websocket.send_json({
                "flow_id": flow_id,
                "status": "running",
                "progress": 50.0,
                "timestamp": "2024-01-15T10:00:00Z"
            })
            
            # Wait for client message or timeout
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for flow {flow_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()