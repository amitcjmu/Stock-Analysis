"""
Discovery Flow Event Listener for CrewAI Integration

This implements the CrewAI Event Listener pattern for proper flow tracking,
as recommended in https://docs.crewai.com/concepts/event-listener

The listener captures Flow, Crew, Agent, and Task events to provide:
- Real-time flow progress tracking for frontend
- Event-based status updates using flow IDs (not fingerprints)
- Cross-crew collaboration monitoring
- Task completion and failure tracking
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import console manager to prevent Rich display conflicts
from .console_manager import console_manager

try:
    from crewai.utilities.events import (
        AgentExecutionCompletedEvent,
        AgentExecutionErrorEvent,
        # Agent and Task Events - For detailed progress
        AgentExecutionStartedEvent,
        CrewKickoffCompletedEvent,
        CrewKickoffFailedEvent,
        # Crew Events - For crew-level progress
        CrewKickoffStartedEvent,
        # Flow Events - These are what we need for flow tracking
        FlowCreatedEvent,
        FlowFinishedEvent,
        FlowStartedEvent,
        LLMCallCompletedEvent,
        LLMCallStartedEvent,
        MethodExecutionFailedEvent,
        MethodExecutionFinishedEvent,
        MethodExecutionStartedEvent,
        TaskCompletedEvent,
        TaskFailedEvent,
        TaskStartedEvent,
        ToolUsageFinishedEvent,
        # Tool and LLM Events - For operational insights
        ToolUsageStartedEvent,
    )
    from crewai.utilities.events.base_event_listener import BaseEventListener
    CREWAI_EVENTS_AVAILABLE = True
except ImportError:
    # Fallback for development without CrewAI events
    CREWAI_EVENTS_AVAILABLE = False
    
    class BaseEventListener:
        def __init__(self):
            pass
        def setup_listeners(self, crewai_event_bus):
            pass

logger = logging.getLogger(__name__)

@dataclass
class FlowEvent:
    """Structured event for frontend consumption"""
    event_id: str
    event_type: str
    flow_id: str
    timestamp: datetime
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    crew_name: Optional[str] = None
    agent_name: Optional[str] = None
    task_name: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    error_message: Optional[str] = None

class DiscoveryFlowEventListener(BaseEventListener):
    """
    CrewAI Event Listener for Discovery Flow tracking.
    
    Implements the pattern from CrewAI documentation:
    https://docs.crewai.com/concepts/event-listener
    
    This listener captures events from Discovery Flow execution and:
    - Tracks flow progress using flow IDs (not fingerprints)
    - Provides real-time status updates for frontend
    - Monitors crew and agent collaboration
    - Handles error scenarios and recovery
    """
    
    def __init__(self):
        super().__init__()
        
        # Event storage for frontend queries
        self.flow_events: Dict[str, List[FlowEvent]] = {}
        self.active_flows: Dict[str, Dict[str, Any]] = {}
        self.flow_status: Dict[str, str] = {}
        
        # Discovery Flow specific tracking
        self.discovery_phases = [
            "field_mapping", "data_cleansing", "inventory_building",
            "app_server_dependencies", "app_app_dependencies", "technical_debt"
        ]
        
        # Disable Rich output globally for event processing to prevent conflicts
        console_manager.disable_rich_output()
        
        logger.info("🎯 Discovery Flow Event Listener initialized")
        if not CREWAI_EVENTS_AVAILABLE:
            logger.warning("⚠️ CrewAI Events not available - using fallback mode")
    
    def setup_listeners(self, crewai_event_bus):
        """Setup event listeners as per CrewAI documentation pattern"""
        
        if not CREWAI_EVENTS_AVAILABLE:
            logger.warning("CrewAI events not available - listeners not registered")
            return
        
        # Flow-level events - Primary tracking mechanism
        @crewai_event_bus.on(FlowStartedEvent)
        def on_flow_started(source, event: FlowStartedEvent):
            """Track when Discovery Flow starts execution"""
            flow_id = self._extract_flow_id(source, event)
            
            if not flow_id:
                logger.warning("⚠️ FlowStartedEvent received but could not extract flow_id, skipping tracking")
                return
            
            self._add_flow_event(
                flow_id=flow_id,
                event_type="flow_started",
                source="discovery_flow",
                data={
                    "flow_type": "discovery",
                    "total_phases": len(self.discovery_phases),
                    "expected_duration_minutes": 15
                },
                status="running",
                progress=0.0
            )
            
            # Initialize flow tracking
            self.active_flows[flow_id] = {
                "start_time": datetime.utcnow(),
                "current_phase": "initialization",
                "completed_phases": [],
                "total_crews": 6,
                "progress": 0.0
            }
            self.flow_status[flow_id] = "running"
            
            # DELTA TEAM FIX: DISABLED event-based database updates to eliminate competing state management
            # Database updates should go through Master Flow Orchestrator only
            logger.info(f"🔄 Event-based database updates DISABLED for state consolidation - flow: {flow_id}")
            logger.info("📋 State updates now handled exclusively by Master Flow Orchestrator")
            
            logger.info(f"🚀 Discovery Flow started: {flow_id}")
        
        @crewai_event_bus.on(FlowFinishedEvent) 
        def on_flow_finished(source, event: FlowFinishedEvent):
            """Track when Discovery Flow completes - with conditional logic for user approval"""
            flow_id = self._extract_flow_id(source, event)
            
            if not flow_id:
                logger.warning("⚠️ FlowFinishedEvent received but could not extract flow_id, skipping tracking")
                return
            
            # ✅ CONDITIONAL LOGIC: Check if flow is waiting for user approval
            # Try multiple possible attributes to get the flow result
            final_result = getattr(event, 'output', '')
            if not final_result:
                final_result = getattr(event, 'result', '')
            if not final_result:
                final_result = getattr(event, 'final_result', '')
            if not final_result and hasattr(event, 'data'):
                final_result = event.data.get('result', '')
            
            # Debug logging to see what we're getting
            logger.info(f"🔍 Flow finished event attributes: output={getattr(event, 'output', 'None')}, result={getattr(event, 'result', 'None')}, final_result={getattr(event, 'final_result', 'None')}")
            logger.info(f"🔍 Checking final_result: '{final_result}' for pause conditions")
            
            # Check for various pause conditions
            pause_conditions = [
                "awaiting_user_approval_in_attribute_mapping",
                "awaiting_user_approval", 
                "paused_for_user_approval",
                "waiting_for_user_approval",
                "user_approval_required"
            ]
            
            is_paused_for_approval = any(condition in str(final_result).lower() for condition in pause_conditions)
            
            if is_paused_for_approval:
                # Flow paused for user approval - don't mark as completed
                logger.info(f"⏸️ Discovery Flow paused for user approval: {flow_id}")
                
                self._add_flow_event(
                    flow_id=flow_id,
                    event_type="flow_paused_for_approval",
                    source="discovery_flow",
                    data={
                        "pause_time": datetime.utcnow().isoformat(),
                        "reason": "waiting_for_user_approval",
                        "phase": "attribute_mapping",
                        "total_duration": self._calculate_duration(flow_id),
                        "next_action": "user_approval_required",
                        "approval_context": "attribute_mapping_validation"
                    },
                    status="waiting_for_user",
                    progress=90.0  # High progress but not complete
                )
                
                # Update flow tracking to waiting state
                if flow_id in self.active_flows:
                    self.active_flows[flow_id]["current_phase"] = "attribute_mapping"
                    self.active_flows[flow_id]["progress"] = 90.0
                    self.active_flows[flow_id]["status"] = "waiting_for_user"
                    # Don't set end_time - flow is paused, not finished
                self.flow_status[flow_id] = "waiting_for_user"
                
                logger.info(f"⏸️ Flow {flow_id} paused in attribute_mapping - awaiting user approval")
                
            else:
                # Flow actually completed
                logger.info(f"🏁 Discovery Flow completed: {flow_id}")
                
                self._add_flow_event(
                    flow_id=flow_id,
                    event_type="flow_completed",
                    source="discovery_flow",
                    data={
                        "completion_time": datetime.utcnow().isoformat(),
                        "total_duration": self._calculate_duration(flow_id),
                        "final_result": final_result,
                        "completion_status": "success"
                    },
                    status="completed",
                    progress=100.0
                )
                
                # Update flow tracking to completed state
                if flow_id in self.active_flows:
                    self.active_flows[flow_id]["end_time"] = datetime.utcnow()
                    self.active_flows[flow_id]["progress"] = 100.0
                    self.active_flows[flow_id]["status"] = "completed"
                self.flow_status[flow_id] = "completed"
        
        # Method execution events - Crew phase tracking
        @crewai_event_bus.on(MethodExecutionStartedEvent)
        def on_method_started(source, event: MethodExecutionStartedEvent):
            """Track when crew execution methods start"""
            flow_id = self._extract_flow_id(source, event)
            
            if not flow_id:
                logger.warning("⚠️ MethodExecutionStartedEvent received but could not extract flow_id, skipping tracking")
                return
                
            method_name = getattr(event, 'method_name', 'unknown_method')
            
            # Extract crew name from method name
            crew_name = self._extract_crew_name_from_method(method_name)
            
            if crew_name:
                self._add_flow_event(
                    flow_id=flow_id,
                    event_type="crew_started",
                    source="discovery_flow",
                    crew_name=crew_name,
                    data={
                        "method_name": method_name,
                        "crew_type": crew_name,
                        "estimated_duration_minutes": 2
                    },
                    status="running",
                    progress=self._calculate_crew_progress(flow_id, crew_name, "started")
                )
                
                # Update active flow tracking
                if flow_id in self.active_flows:
                    self.active_flows[flow_id]["current_phase"] = crew_name
                
                logger.info(f"🔄 Crew started - {crew_name} in flow {flow_id}")
        
        @crewai_event_bus.on(MethodExecutionFinishedEvent)
        def on_method_finished(source, event: MethodExecutionFinishedEvent):
            """Track when crew execution methods complete"""
            flow_id = self._extract_flow_id(source, event)
            
            if not flow_id:
                logger.warning("⚠️ MethodExecutionFinishedEvent received but could not extract flow_id, skipping tracking")
                return
                
            method_name = getattr(event, 'method_name', 'unknown_method')
            
            crew_name = self._extract_crew_name_from_method(method_name)
            
            if crew_name:
                self._add_flow_event(
                    flow_id=flow_id,
                    event_type="crew_completed",
                    source="discovery_flow", 
                    crew_name=crew_name,
                    data={
                        "method_name": method_name,
                        "crew_type": crew_name,
                        "execution_result": getattr(event, 'result', {}),
                        "duration_seconds": getattr(event, 'duration', 0)
                    },
                    status="completed",
                    progress=self._calculate_crew_progress(flow_id, crew_name, "completed")
                )
                
                # Update active flow tracking
                if flow_id in self.active_flows:
                    if crew_name not in self.active_flows[flow_id]["completed_phases"]:
                        self.active_flows[flow_id]["completed_phases"].append(crew_name)
                    
                    # Calculate overall progress
                    completed_count = len(self.active_flows[flow_id]["completed_phases"])
                    total_count = self.active_flows[flow_id]["total_crews"]
                    self.active_flows[flow_id]["progress"] = (completed_count / total_count) * 100
                
                logger.info(f"✅ Crew completed - {crew_name} in flow {flow_id}")
        
        @crewai_event_bus.on(MethodExecutionFailedEvent)
        def on_method_failed(source, event: MethodExecutionFailedEvent):
            """Track when crew execution methods fail"""
            flow_id = self._extract_flow_id(source, event)
            
            if not flow_id:
                logger.warning("⚠️ MethodExecutionFailedEvent received but could not extract flow_id, skipping tracking")
                return
                
            method_name = getattr(event, 'method_name', 'unknown_method')
            error = getattr(event, 'error', 'Unknown error')
            
            crew_name = self._extract_crew_name_from_method(method_name)
            
            self._add_flow_event(
                flow_id=flow_id,
                event_type="crew_failed",
                source="discovery_flow",
                crew_name=crew_name,
                data={
                    "method_name": method_name,
                    "crew_type": crew_name,
                    "error_details": str(error)
                },
                status="failed",
                error_message=str(error)
            )
            
            # Update flow status to handle error
            if flow_id in self.flow_status:
                self.flow_status[flow_id] = "error"
            
            logger.error(f"❌ Crew failed - {crew_name} in flow {flow_id}: {error}")
        
        # Agent-level events for detailed progress
        @crewai_event_bus.on(AgentExecutionStartedEvent)
        def on_agent_started(source, event: AgentExecutionStartedEvent):
            """Track agent execution start"""
            flow_id = self._extract_flow_id(source, event)
            
            if not flow_id:
                logger.warning("⚠️ AgentExecutionStartedEvent received but could not extract flow_id, skipping tracking")
                return
            
            # Safely extract agent name from agent object
            agent = getattr(event, 'agent', None)
            if agent:
                agent_name = getattr(agent, 'role', 'unknown_agent')
            else:
                agent_name = 'unknown_agent'
            
            # Safely extract task description
            task = getattr(event, 'task', None)
            if task:
                task_description = getattr(task, 'description', '')
            else:
                task_description = ''
            
            self._add_flow_event(
                flow_id=flow_id,
                event_type="agent_started",
                source="discovery_flow",
                agent_name=agent_name,
                data={
                    "agent_role": agent_name,
                    "task_description": task_description
                },
                status="running"
            )
        
        @crewai_event_bus.on(AgentExecutionCompletedEvent) 
        def on_agent_completed(source, event: AgentExecutionCompletedEvent):
            """Track agent execution completion"""
            flow_id = self._extract_flow_id(source, event)
            
            if not flow_id:
                logger.warning("⚠️ AgentExecutionCompletedEvent received but could not extract flow_id, skipping tracking")
                return
            
            # Safely extract agent name from agent object
            agent = getattr(event, 'agent', None)
            if agent:
                agent_name = getattr(agent, 'role', 'unknown_agent')
            else:
                agent_name = 'unknown_agent'
            
            self._add_flow_event(
                flow_id=flow_id,
                event_type="agent_completed",
                source="discovery_flow",
                agent_name=agent_name,
                data={
                    "agent_role": agent_name,
                    "output": getattr(event, 'output', ''),
                    "execution_time": getattr(event, 'execution_time', 0)
                },
                status="completed"
            )
        
        # Task-level events for granular tracking
        @crewai_event_bus.on(TaskCompletedEvent)
        def on_task_completed(source, event: TaskCompletedEvent):
            """Track task completion for progress updates"""
            # Disable Rich output to prevent display conflicts
            console_manager.disable_rich_output()
            
            try:
                flow_id = self._extract_flow_id(source, event)
                
                if not flow_id:
                    logger.warning("⚠️ TaskCompletedEvent received but could not extract flow_id, skipping tracking")
                    return
                
                # Safely extract task description
                task = getattr(event, 'task', None)
                if task:
                    task_description = getattr(task, 'description', 'unknown_task')
                else:
                    task_description = 'unknown_task'
                
                # Safely extract agent name
                agent = getattr(event, 'agent', None)
                if agent:
                    agent_name = getattr(agent, 'role', 'unknown')
                else:
                    agent_name = 'unknown'
                
                self._add_flow_event(
                    flow_id=flow_id,
                    event_type="task_completed",
                    source="discovery_flow",
                    task_name=task_description[:50] + "..." if len(task_description) > 50 else task_description,
                    data={
                        "task_description": task_description,
                        "output": getattr(event, 'output', ''),
                        "agent": agent_name
                    },
                    status="completed"
                )
            finally:
                # Re-enable Rich output after processing
                console_manager.enable_rich_output()
        
        logger.info("✅ Discovery Flow Event Listeners registered successfully")
    
    def _extract_flow_id(self, source, event) -> str:
        """Extract flow ID from event source - PRIORITIZE flow_id over session_id"""
        try:
            # Import CrewAI Flow Service for proper flow ID resolution
            from app.services.crewai_flow_service import CrewAIFlowService
            
            # Method 1: From source flow ID directly (HIGHEST PRIORITY)
            if hasattr(source, 'flow_id'):
                flow_id = source.flow_id
                if flow_id:
                    logger.info(f"🎯 Flow ID extracted from source.flow_id: {flow_id}")
                    return str(flow_id)
            
            # Method 2: From source ID (CrewAI Flow UUID)
            if hasattr(source, 'id'):
                source_id = source.id
                if source_id:
                    logger.info(f"🎯 Flow ID extracted from source.id: {source_id}")
                    return str(source_id)
            
            # Method 3: From event data
            if hasattr(event, 'flow_id'):
                flow_id = event.flow_id
                if flow_id:
                    logger.info(f"🎯 Flow ID extracted from event.flow_id: {flow_id}")
                    return str(flow_id)
            
            # Method 4: From source object state flow_id (if available)
            if hasattr(source, 'state') and hasattr(source.state, 'flow_id'):
                flow_id = source.state.flow_id
                if flow_id:
                    logger.info(f"🎯 Flow ID extracted from source.state.flow_id: {flow_id}")
                    return str(flow_id)
            
            # Method 5: FALLBACK to session_id (DEPRECATED - only for backward compatibility)
            if hasattr(source, 'state') and hasattr(source.state, 'session_id'):
                session_id = source.state.session_id
                if session_id:
                    logger.warning(f"⚠️ Using DEPRECATED session_id as flow_id: {session_id}")
                    return str(session_id)
            
            # Method 6: From source session (DEPRECATED)
            if hasattr(source, 'session_id'):
                session_id = source.session_id
                if session_id:
                    logger.warning(f"⚠️ Using DEPRECATED source.session_id as flow_id: {session_id}")
                    return str(session_id)
            
            # Method 6: Query CrewAI Flow Service for active flows
            # Get the current active flow from the flow service
            try:
                # Create a temporary service instance to query active flows
                service = CrewAIFlowService()
                active_flows = service.get_all_active_flows()
                
                if active_flows:
                    # Return the most recent active flow ID
                    flow_ids = list(active_flows.keys()) if isinstance(active_flows, dict) else active_flows
                    if flow_ids:
                        most_recent_flow = flow_ids[-1]  # Get the last/most recent flow
                        logger.info(f"🔍 Using most recent active flow from service: {most_recent_flow}")
                        return most_recent_flow
                        
            except Exception as service_error:
                logger.warning(f"Could not query CrewAI Flow Service: {service_error}")
            
            # Method 7: Last resort - log comprehensive error and return None
            logger.error("❌ Could not extract flow ID from any source:")
            logger.error(f"   Source type: {type(source)}")
            logger.error(f"   Source attributes: {[attr for attr in dir(source) if not attr.startswith('_')]}")
            logger.error(f"   Event type: {type(event)}")
            logger.error(f"   Event attributes: {[attr for attr in dir(event) if not attr.startswith('_')]}")
            
            # Return None instead of fallback ID to prevent ghost flows
            return None
            
        except Exception as e:
            logger.error(f"Error in _extract_flow_id: {e}")
            return None
    
    def _extract_crew_name_from_method(self, method_name: str) -> Optional[str]:
        """Extract crew name from method name like 'execute_field_mapping_crew'"""
        if not method_name or not method_name.startswith('execute_'):
            return None
        
        # Remove 'execute_' prefix and '_crew' suffix
        crew_name = method_name.replace('execute_', '').replace('_crew', '')
        
        # Validate against known crews
        if crew_name in self.discovery_phases:
            return crew_name
        
        return None
    
    def _calculate_crew_progress(self, flow_id: str, crew_name: str, status: str) -> float:
        """Calculate overall flow progress based on crew completion"""
        if flow_id not in self.active_flows:
            return 0.0
        
        # Get current position of crew in sequence
        try:
            crew_position = self.discovery_phases.index(crew_name)
        except ValueError:
            return self.active_flows[flow_id].get("progress", 0.0)
        
        total_phases = len(self.discovery_phases)
        
        if status == "started":
            # Progress at start of crew (previous crews completed)
            return (crew_position / total_phases) * 100
        elif status == "completed":
            # Progress at completion of crew
            return ((crew_position + 1) / total_phases) * 100
        
        return self.active_flows[flow_id].get("progress", 0.0)
    
    def _calculate_duration(self, flow_id: str) -> float:
        """Calculate flow duration in seconds"""
        if flow_id not in self.active_flows:
            return 0.0
        
        flow_data = self.active_flows[flow_id]
        start_time = flow_data.get("start_time")
        end_time = flow_data.get("end_time", datetime.utcnow())
        
        if start_time:
            return (end_time - start_time).total_seconds()
        
        return 0.0
    
    def _add_flow_event(self, flow_id: str, event_type: str, source: str, **kwargs):
        """Add event to flow tracking"""
        if not flow_id:
            logger.warning(f"⚠️ Attempted to add event {event_type} with None flow_id, skipping")
            return
            
        if flow_id not in self.flow_events:
            self.flow_events[flow_id] = []
        
        event = FlowEvent(
            event_id=f"{flow_id}_{len(self.flow_events[flow_id])}",
            event_type=event_type,
            flow_id=flow_id,
            timestamp=datetime.utcnow(),
            source=source,
            **kwargs
        )
        
        self.flow_events[flow_id].append(event)
        
        # Keep only last 100 events per flow to manage memory
        if len(self.flow_events[flow_id]) > 100:
            self.flow_events[flow_id] = self.flow_events[flow_id][-100:]
    
    # Public API methods for frontend consumption
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get current status of a flow by flow ID"""
        if flow_id not in self.active_flows:
            return {
                "status": "not_found",
                "error": f"Flow {flow_id} not found"
            }
        
        flow_data = self.active_flows[flow_id]
        recent_events = self.flow_events.get(flow_id, [])[-10:]  # Last 10 events
        
        return {
            "flow_id": flow_id,
            "status": self.flow_status.get(flow_id, "unknown"),
            "current_phase": flow_data.get("current_phase", "unknown"),
            "progress": flow_data.get("progress", 0.0),
            "completed_phases": flow_data.get("completed_phases", []),
            "total_phases": len(self.discovery_phases),
            "start_time": flow_data.get("start_time").isoformat() if flow_data.get("start_time") else None,
            "duration_seconds": self._calculate_duration(flow_id),
            "recent_events": [
                {
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "crew_name": event.crew_name,
                    "agent_name": event.agent_name,
                    "status": event.status,
                    "data": event.data
                }
                for event in recent_events
            ]
        }
    
    def get_flow_events(self, flow_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get events for a specific flow"""
        if flow_id not in self.flow_events:
            return []
        
        events = self.flow_events[flow_id][-limit:]
        
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "crew_name": event.crew_name,
                "agent_name": event.agent_name,
                "task_name": event.task_name,
                "status": event.status,
                "progress": event.progress,
                "data": event.data,
                "error_message": event.error_message
            }
            for event in events
        ]
    
    def get_active_flows(self) -> List[str]:
        """Get list of currently active flow IDs"""
        active_flows = []
        for flow_id, status in self.flow_status.items():
            if status in ["running", "error"]:
                active_flows.append(flow_id)
        return active_flows
    
    def cleanup_completed_flows(self, hours_old: int = 24):
        """Clean up old completed flows to manage memory"""
        cutoff_time = datetime.utcnow().timestamp() - (hours_old * 3600)
        
        flows_to_remove = []
        for flow_id, flow_data in self.active_flows.items():
            end_time = flow_data.get("end_time")
            if end_time and end_time.timestamp() < cutoff_time:
                flows_to_remove.append(flow_id)
        
        for flow_id in flows_to_remove:
            self.active_flows.pop(flow_id, None)
            self.flow_events.pop(flow_id, None)
            self.flow_status.pop(flow_id, None)
        
        if flows_to_remove:
            logger.info(f"🧹 Cleaned up {len(flows_to_remove)} old flows")

# Create singleton instance for import
discovery_flow_listener = DiscoveryFlowEventListener() 