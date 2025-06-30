"""
Event bus for flow coordination
"""

from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class FlowEvent:
    """Flow event structure"""
    flow_id: str
    event_type: str
    phase: str
    data: Dict[str, Any]
    timestamp: datetime
    context: Dict[str, Any]


class FlowEventBus:
    """
    Event bus for flow events.
    Enables:
    - Real-time monitoring
    - WebSocket updates
    - External integrations
    - Audit logging
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[FlowEvent] = []
        self.max_history = 1000
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to specific event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        logger.info(f"Subscribed to {event_type} events")
    
    async def publish(self, event: FlowEvent) -> None:
        """Publish event to subscribers"""
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
        
        # Notify subscribers
        callbacks = self.subscribers.get(event.event_type, [])
        callbacks.extend(self.subscribers.get("*", []))  # Wildcard subscribers
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")
    
    def get_flow_events(self, flow_id: str) -> List[FlowEvent]:
        """Get all events for a specific flow"""
        return [e for e in self.event_history if e.flow_id == flow_id]
    
    def get_recent_events(self, limit: int = 100) -> List[FlowEvent]:
        """Get recent events across all flows"""
        return self.event_history[-limit:]
    
    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[FlowEvent]:
        """Get recent events of specific type"""
        events = [e for e in self.event_history if e.event_type == event_type]
        return events[-limit:]
    
    def get_phase_events(self, phase: str, limit: int = 100) -> List[FlowEvent]:
        """Get recent events for specific phase"""
        events = [e for e in self.event_history if e.phase == phase]
        return events[-limit:]
    
    def clear_history(self) -> int:
        """Clear event history and return count of cleared events"""
        count = len(self.event_history)
        self.event_history.clear()
        logger.info(f"Cleared {count} events from history")
        return count
    
    def get_flow_timeline(self, flow_id: str) -> List[Dict[str, Any]]:
        """Get chronological timeline of events for a flow"""
        flow_events = self.get_flow_events(flow_id)
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "phase": event.phase,
                "data": event.data
            }
            for event in sorted(flow_events, key=lambda e: e.timestamp)
        ]


# Global event bus instance
flow_event_bus = FlowEventBus()


# Built-in event handlers
async def websocket_event_handler(event: FlowEvent):
    """Send flow events to WebSocket clients"""
    try:
        # TODO: Integrate with actual WebSocket manager
        logger.info(f"WebSocket event: {event.event_type} for flow {event.flow_id}")
        
        # For now, just log the event data
        event_data = {
            "type": "flow_event",
            "flow_id": event.flow_id,
            "event_type": event.event_type,
            "phase": event.phase,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        }
        
        # This would normally send to WebSocket clients
        logger.debug(f"Would send to WebSocket: {event_data}")
        
    except Exception as e:
        logger.error(f"WebSocket event handler error: {e}")


async def audit_log_handler(event: FlowEvent):
    """Log flow events for audit purposes"""
    try:
        audit_entry = {
            "timestamp": event.timestamp.isoformat(),
            "flow_id": event.flow_id,
            "event_type": event.event_type,
            "phase": event.phase,
            "context": event.context,
            "data_summary": {
                "keys": list(event.data.keys()),
                "data_size": len(str(event.data))
            }
        }
        
        # Log to audit system
        logger.info(f"AUDIT: {audit_entry}")
        
    except Exception as e:
        logger.error(f"Audit log handler error: {e}")


async def metrics_handler(event: FlowEvent):
    """Handle flow metrics collection"""
    try:
        # Collect metrics based on event type
        if event.event_type == "flow_started":
            logger.info(f"METRIC: Flow started - {event.flow_id}")
        elif event.event_type == "phase_completed":
            phase = event.phase
            duration = event.data.get("duration", "unknown")
            logger.info(f"METRIC: Phase {phase} completed in {duration}")
        elif event.event_type == "flow_completed":
            total_phases = event.data.get("total_phases", 0)
            assets_discovered = event.data.get("assets_discovered", 0)
            logger.info(f"METRIC: Flow completed - {total_phases} phases, {assets_discovered} assets")
        elif event.event_type == "error":
            error_type = event.data.get("type", "unknown")
            phase = event.phase
            logger.error(f"METRIC: Error in {phase} - {error_type}")
            
    except Exception as e:
        logger.error(f"Metrics handler error: {e}")


# Subscribe built-in handlers
flow_event_bus.subscribe("*", websocket_event_handler)
flow_event_bus.subscribe("*", audit_log_handler)
flow_event_bus.subscribe("*", metrics_handler)


# Utility functions for event publishing
async def publish_flow_event(
    flow_id: str,
    event_type: str,
    phase: str,
    data: Dict[str, Any],
    context: Dict[str, Any]
):
    """Utility function to publish a flow event"""
    event = FlowEvent(
        flow_id=flow_id,
        event_type=event_type,
        phase=phase,
        data=data,
        timestamp=datetime.utcnow(),
        context=context
    )
    await flow_event_bus.publish(event)


async def publish_phase_event(
    flow_id: str,
    phase: str,
    status: str,
    data: Dict[str, Any] = None,
    context: Dict[str, Any] = None
):
    """Utility function to publish phase-related events"""
    event_data = data or {}
    event_data["status"] = status
    
    await publish_flow_event(
        flow_id=flow_id,
        event_type="phase_update",
        phase=phase,
        data=event_data,
        context=context or {}
    )


async def publish_error_event(
    flow_id: str,
    phase: str,
    error: Exception,
    context: Dict[str, Any] = None
):
    """Utility function to publish error events"""
    await publish_flow_event(
        flow_id=flow_id,
        event_type="error",
        phase=phase,
        data={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_details": getattr(error, 'args', [])
        },
        context=context or {}
    )