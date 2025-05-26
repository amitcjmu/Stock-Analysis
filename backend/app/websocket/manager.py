"""
WebSocket connection manager for real-time updates.
Handles client connections, message broadcasting, and real-time notifications.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        # Store active connections by client_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store client metadata
        self.client_metadata: Dict[str, Dict[str, Any]] = {}
        # Message history for reconnection
        self.message_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_metadata[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "message_count": 0
        }
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket connection established successfully"
        }, client_id)
        
        # Send recent message history
        await self._send_message_history(client_id)
        
        # Notify other clients about new connection
        await self.broadcast({
            "type": "client_connected",
            "client_id": client_id,
            "total_connections": len(self.active_connections),
            "timestamp": datetime.utcnow().isoformat()
        }, exclude_client=client_id)
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if client_id in self.client_metadata:
            del self.client_metadata[client_id]
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Any, client_id: str):
        """Send a message to a specific client."""
        if client_id not in self.active_connections:
            logger.warning(f"Attempted to send message to disconnected client: {client_id}")
            return False
        
        try:
            websocket = self.active_connections[client_id]
            
            # Ensure message is properly formatted
            if isinstance(message, str):
                formatted_message = {
                    "type": "text_message",
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "client_id": client_id
                }
            elif isinstance(message, dict):
                formatted_message = {
                    **message,
                    "timestamp": message.get("timestamp", datetime.utcnow().isoformat()),
                    "client_id": client_id
                }
            else:
                formatted_message = {
                    "type": "data_message",
                    "content": str(message),
                    "timestamp": datetime.utcnow().isoformat(),
                    "client_id": client_id
                }
            
            await websocket.send_text(json.dumps(formatted_message))
            
            # Update client metadata
            if client_id in self.client_metadata:
                self.client_metadata[client_id]["last_seen"] = datetime.utcnow().isoformat()
                self.client_metadata[client_id]["message_count"] += 1
            
            return True
            
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected during message send")
            self.disconnect(client_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to client {client_id}: {e}")
            return False
    
    async def broadcast(self, message: Any, exclude_client: Optional[str] = None):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            logger.debug("No active connections for broadcast")
            return
        
        # Format message for broadcast
        if isinstance(message, str):
            formatted_message = {
                "type": "broadcast",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        elif isinstance(message, dict):
            formatted_message = {
                **message,
                "timestamp": message.get("timestamp", datetime.utcnow().isoformat())
            }
        else:
            formatted_message = {
                "type": "broadcast",
                "content": str(message),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Add to message history
        self._add_to_history(formatted_message)
        
        # Send to all clients except excluded one
        disconnected_clients = []
        for client_id, websocket in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue
            
            try:
                await websocket.send_text(json.dumps(formatted_message))
                
                # Update client metadata
                if client_id in self.client_metadata:
                    self.client_metadata[client_id]["last_seen"] = datetime.utcnow().isoformat()
                    self.client_metadata[client_id]["message_count"] += 1
                    
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected during broadcast")
                disconnected_clients.append(client_id)
            except Exception as e:
                logger.error(f"Error broadcasting to client {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
        
        logger.debug(f"Broadcast sent to {len(self.active_connections) - len(disconnected_clients)} clients")
    
    async def send_migration_update(self, migration_id: int, update_data: Dict[str, Any]):
        """Send migration-specific update to all clients."""
        message = {
            "type": "migration_update",
            "migration_id": migration_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    async def send_asset_update(self, asset_id: int, update_data: Dict[str, Any]):
        """Send asset-specific update to all clients."""
        message = {
            "type": "asset_update",
            "asset_id": asset_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    async def send_assessment_update(self, assessment_id: int, update_data: Dict[str, Any]):
        """Send assessment-specific update to all clients."""
        message = {
            "type": "assessment_update",
            "assessment_id": assessment_id,
            "data": update_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(message)
    
    async def send_ai_insight(self, insight_data: Dict[str, Any], target_client: Optional[str] = None):
        """Send AI-generated insight to clients."""
        message = {
            "type": "ai_insight",
            "data": insight_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if target_client:
            await self.send_personal_message(message, target_client)
        else:
            await self.broadcast(message)
    
    async def send_error_notification(self, error_data: Dict[str, Any], target_client: Optional[str] = None):
        """Send error notification to clients."""
        message = {
            "type": "error_notification",
            "data": error_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if target_client:
            await self.send_personal_message(message, target_client)
        else:
            await self.broadcast(message)
    
    async def _send_message_history(self, client_id: str):
        """Send recent message history to a newly connected client."""
        if not self.message_history:
            return
        
        history_message = {
            "type": "message_history",
            "messages": self.message_history[-10:],  # Send last 10 messages
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(history_message, client_id)
    
    def _add_to_history(self, message: Dict[str, Any]):
        """Add message to history with size limit."""
        self.message_history.append(message)
        
        # Maintain history size limit
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get current connection statistics."""
        return {
            "total_connections": len(self.active_connections),
            "connected_clients": list(self.active_connections.keys()),
            "client_metadata": self.client_metadata,
            "message_history_size": len(self.message_history),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def ping_all_clients(self):
        """Send ping to all clients to check connection health."""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast(ping_message)
    
    def is_client_connected(self, client_id: str) -> bool:
        """Check if a specific client is connected."""
        return client_id in self.active_connections 