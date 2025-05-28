"""
6R Analysis WebSocket endpoints for real-time updates.
Provides WebSocket connections for live analysis progress, parameter updates, and notifications.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.models.sixr_analysis import SixRAnalysis
    from app.schemas.sixr_analysis import AnalysisStatus
except ImportError as e:
    logging.warning(f"Import failed: {e}")
    # Fallback for testing
    def get_db():
        return None

logger = logging.getLogger(__name__)


class SixRWebSocketManager:
    """WebSocket connection manager for 6R analysis updates."""
    
    def __init__(self):
        # Store active connections by analysis_id
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, analysis_id: int, user_id: Optional[str] = None):
        """Accept WebSocket connection and register for analysis updates."""
        await websocket.accept()
        
        # Add to active connections
        if analysis_id not in self.active_connections:
            self.active_connections[analysis_id] = []
        
        self.active_connections[analysis_id].append(websocket)
        
        # Store metadata
        self.connection_metadata[websocket] = {
            "analysis_id": analysis_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }
        
        logger.info(f"WebSocket connected for analysis {analysis_id}, user {user_id}")
        
        # Send initial connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "analysis_id": analysis_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to 6R analysis updates"
        }, websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.connection_metadata:
            metadata = self.connection_metadata[websocket]
            analysis_id = metadata["analysis_id"]
            user_id = metadata.get("user_id")
            
            # Remove from active connections
            if analysis_id in self.active_connections:
                if websocket in self.active_connections[analysis_id]:
                    self.active_connections[analysis_id].remove(websocket)
                
                # Clean up empty analysis connection lists
                if not self.active_connections[analysis_id]:
                    del self.active_connections[analysis_id]
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected for analysis {analysis_id}, user {user_id}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send message to specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message))
            
            # Update last activity
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]["last_activity"] = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            # Connection might be closed, remove it
            self.disconnect(websocket)
    
    async def broadcast_to_analysis(self, message: Dict[str, Any], analysis_id: int):
        """Broadcast message to all connections for a specific analysis."""
        if analysis_id in self.active_connections:
            disconnected_connections = []
            
            for websocket in self.active_connections[analysis_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                    
                    # Update last activity
                    if websocket in self.connection_metadata:
                        self.connection_metadata[websocket]["last_activity"] = datetime.utcnow()
                        
                except Exception as e:
                    logger.error(f"Failed to send broadcast message: {e}")
                    disconnected_connections.append(websocket)
            
            # Clean up disconnected connections
            for websocket in disconnected_connections:
                self.disconnect(websocket)
    
    async def send_analysis_update(self, analysis_id: int, update_type: str, data: Dict[str, Any]):
        """Send analysis update to all connected clients."""
        message = {
            "type": "analysis_update",
            "update_type": update_type,
            "analysis_id": analysis_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_analysis(message, analysis_id)
    
    async def send_parameter_update(self, analysis_id: int, parameters: Dict[str, Any], user_id: Optional[str] = None):
        """Send parameter update notification."""
        await self.send_analysis_update(analysis_id, "parameters_updated", {
            "parameters": parameters,
            "updated_by": user_id
        })
    
    async def send_progress_update(self, analysis_id: int, progress: float, status: str, message: Optional[str] = None):
        """Send progress update notification."""
        await self.send_analysis_update(analysis_id, "progress_updated", {
            "progress_percentage": progress,
            "status": status,
            "message": message
        })
    
    async def send_recommendation_update(self, analysis_id: int, recommendation: Dict[str, Any], iteration: int):
        """Send recommendation update notification."""
        await self.send_analysis_update(analysis_id, "recommendation_updated", {
            "recommendation": recommendation,
            "iteration_number": iteration
        })
    
    async def send_question_update(self, analysis_id: int, questions: List[Dict[str, Any]]):
        """Send qualifying questions update."""
        await self.send_analysis_update(analysis_id, "questions_updated", {
            "questions": questions
        })
    
    async def send_error_notification(self, analysis_id: int, error: str, error_type: str = "general"):
        """Send error notification."""
        await self.send_analysis_update(analysis_id, "error_occurred", {
            "error_message": error,
            "error_type": error_type
        })
    
    async def send_agent_activity(self, analysis_id: int, agent_name: str, activity: str, details: Optional[Dict[str, Any]] = None):
        """Send agent activity notification."""
        await self.send_analysis_update(analysis_id, "agent_activity", {
            "agent_name": agent_name,
            "activity": activity,
            "details": details or {}
        })
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics."""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            "total_connections": total_connections,
            "active_analyses": len(self.active_connections),
            "connections_by_analysis": {
                analysis_id: len(connections) 
                for analysis_id, connections in self.active_connections.items()
            }
        }


# Global WebSocket manager instance
websocket_manager = SixRWebSocketManager()


async def websocket_endpoint(
    websocket: WebSocket,
    analysis_id: int,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for 6R analysis real-time updates.
    
    Provides real-time updates for:
    - Analysis progress
    - Parameter changes
    - Recommendation updates
    - Agent activity
    - Error notifications
    """
    try:
        # Verify analysis exists
        if db:
            analysis = db.query(SixRAnalysis).filter(SixRAnalysis.id == analysis_id).first()
            if not analysis:
                await websocket.close(code=4004, reason="Analysis not found")
                return
        
        # Connect WebSocket
        await websocket_manager.connect(websocket, analysis_id, user_id)
        
        try:
            # Send initial analysis state
            if db and analysis:
                initial_state = {
                    "type": "initial_state",
                    "analysis_id": analysis_id,
                    "status": analysis.status,
                    "progress_percentage": analysis.progress_percentage,
                    "current_iteration": analysis.current_iteration,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket_manager.send_personal_message(initial_state, websocket)
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for messages from client
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    await handle_websocket_message(websocket, analysis_id, message, db)
                    
                except json.JSONDecodeError:
                    await websocket_manager.send_personal_message({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }, websocket)
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for analysis {analysis_id}")
        
    except Exception as e:
        logger.error(f"WebSocket error for analysis {analysis_id}: {e}")
        await websocket.close(code=1011, reason="Internal server error")
    
    finally:
        # Clean up connection
        websocket_manager.disconnect(websocket)


async def handle_websocket_message(
    websocket: WebSocket, 
    analysis_id: int, 
    message: Dict[str, Any], 
    db: Optional[Session]
):
    """Handle incoming WebSocket messages from client."""
    try:
        message_type = message.get("type")
        
        if message_type == "ping":
            # Respond to ping with pong
            await websocket_manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)
        
        elif message_type == "subscribe_agent_activity":
            # Client wants to subscribe to agent activity updates
            await websocket_manager.send_personal_message({
                "type": "subscription_confirmed",
                "subscription": "agent_activity",
                "analysis_id": analysis_id
            }, websocket)
        
        elif message_type == "request_status":
            # Client requesting current analysis status
            if db:
                analysis = db.query(SixRAnalysis).filter(SixRAnalysis.id == analysis_id).first()
                if analysis:
                    status_update = {
                        "type": "status_response",
                        "analysis_id": analysis_id,
                        "status": analysis.status,
                        "progress_percentage": analysis.progress_percentage,
                        "current_iteration": analysis.current_iteration,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await websocket_manager.send_personal_message(status_update, websocket)
        
        elif message_type == "parameter_change_notification":
            # Client notifying of parameter changes (for real-time collaboration)
            parameters = message.get("parameters", {})
            user_id = message.get("user_id")
            
            # Broadcast to other connected clients
            await websocket_manager.send_parameter_update(analysis_id, parameters, user_id)
        
        else:
            # Unknown message type
            await websocket_manager.send_personal_message({
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }, websocket)
    
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await websocket_manager.send_personal_message({
            "type": "error",
            "message": "Failed to process message"
        }, websocket)


# Utility functions for triggering WebSocket updates from other parts of the application

async def notify_analysis_progress(analysis_id: int, progress: float, status: str, message: Optional[str] = None):
    """Notify connected clients of analysis progress update."""
    await websocket_manager.send_progress_update(analysis_id, progress, status, message)


async def notify_parameter_change(analysis_id: int, parameters: Dict[str, Any], user_id: Optional[str] = None):
    """Notify connected clients of parameter changes."""
    await websocket_manager.send_parameter_update(analysis_id, parameters, user_id)


async def notify_recommendation_update(analysis_id: int, recommendation: Dict[str, Any], iteration: int):
    """Notify connected clients of recommendation updates."""
    await websocket_manager.send_recommendation_update(analysis_id, recommendation, iteration)


async def notify_questions_generated(analysis_id: int, questions: List[Dict[str, Any]]):
    """Notify connected clients of new qualifying questions."""
    await websocket_manager.send_question_update(analysis_id, questions)


async def notify_agent_activity(analysis_id: int, agent_name: str, activity: str, details: Optional[Dict[str, Any]] = None):
    """Notify connected clients of agent activity."""
    await websocket_manager.send_agent_activity(analysis_id, agent_name, activity, details)


async def notify_analysis_error(analysis_id: int, error: str, error_type: str = "general"):
    """Notify connected clients of analysis errors."""
    await websocket_manager.send_error_notification(analysis_id, error, error_type)


def get_websocket_stats() -> Dict[str, Any]:
    """Get WebSocket connection statistics."""
    return websocket_manager.get_connection_stats() 