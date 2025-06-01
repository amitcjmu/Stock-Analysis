"""
Agent Coordinator - Cross-page agent communication and state management

Manages unified agent state across all discovery pages, coordinates agent collaboration,
and enables real-time communication and learning synchronization between agents.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from collections import defaultdict, deque
import weakref

logger = logging.getLogger(__name__)

class AgentState(Enum):
    """States for agent coordination"""
    IDLE = "idle"
    WORKING = "working"
    COLLABORATING = "collaborating"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    ERROR = "error"

class CoordinationLevel(Enum):
    """Levels of agent coordination"""
    INDIVIDUAL = "individual"  # Agent works independently
    COLLABORATIVE = "collaborative"  # Agents share insights
    COORDINATED = "coordinated"  # Agents coordinate tasks
    UNIFIED = "unified"  # Agents work as unified system

class MessageType(Enum):
    """Types of inter-agent messages"""
    INSIGHT_SHARE = "insight_share"
    QUESTION_CLARIFICATION = "question_clarification"
    DATA_REQUEST = "data_request"
    PATTERN_NOTIFICATION = "pattern_notification"
    STATE_UPDATE = "state_update"
    COLLABORATION_REQUEST = "collaboration_request"
    LEARNING_UPDATE = "learning_update"

@dataclass
class AgentMessage:
    """Message between agents"""
    message_id: str
    sender_agent: str
    recipient_agents: List[str]
    message_type: MessageType
    content: Dict[str, Any]
    priority: int  # 1=high, 2=medium, 3=low
    page_context: str
    client_account_id: int
    engagement_id: str
    timestamp: datetime
    requires_response: bool = False
    response_deadline: Optional[datetime] = None

@dataclass
class AgentCoordinationState:
    """State of an agent in coordination system"""
    agent_name: str
    current_state: AgentState
    current_page: str
    current_task: Optional[str]
    collaboration_group: Optional[str]
    message_queue: deque
    active_conversations: Set[str]
    shared_context: Dict[str, Any]
    last_activity: datetime
    performance_metrics: Dict[str, float]

@dataclass
class CrossPageContext:
    """Context shared across pages"""
    context_id: str
    client_account_id: int
    engagement_id: str
    context_type: str
    context_data: Dict[str, Any]
    participating_agents: Set[str]
    participating_pages: Set[str]
    created_at: datetime
    updated_at: datetime
    expiry_time: Optional[datetime] = None

@dataclass
class CollaborationGroup:
    """Group of agents collaborating on a task"""
    group_id: str
    group_name: str
    participating_agents: Set[str]
    coordination_level: CoordinationLevel
    shared_objective: str
    shared_data: Dict[str, Any]
    group_leader: Optional[str]
    created_at: datetime
    status: str  # active, paused, completed

class AgentCoordinator:
    """
    Coordinates agent communication, state management, and collaboration
    across all pages and discovery phases.
    """
    
    def __init__(self):
        self.agent_states: Dict[str, AgentCoordinationState] = {}
        self.cross_page_contexts: Dict[str, CrossPageContext] = {}
        self.collaboration_groups: Dict[str, CollaborationGroup] = {}
        self.message_bus: deque = deque(maxlen=10000)
        self.subscribers: Dict[str, List[callable]] = defaultdict(list)
        self.coordination_rules: Dict[str, Dict[str, Any]] = {}
        self.learning_synchronizer = None
        self.state_synchronizer_task = None
        
    async def initialize_coordinator(self) -> None:
        """Initialize the agent coordinator"""
        try:
            # Start background tasks
            self.state_synchronizer_task = asyncio.create_task(self._state_synchronizer())
            
            # Initialize coordination rules
            await self._initialize_coordination_rules()
            
            logger.info("Agent Coordinator initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Agent Coordinator: {str(e)}")
            raise
    
    async def register_agent(
        self,
        agent_name: str,
        current_page: str,
        client_account_id: int,
        engagement_id: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Register an agent with the coordinator"""
        try:
            if agent_name not in self.agent_states:
                self.agent_states[agent_name] = AgentCoordinationState(
                    agent_name=agent_name,
                    current_state=AgentState.IDLE,
                    current_page=current_page,
                    current_task=None,
                    collaboration_group=None,
                    message_queue=deque(maxlen=100),
                    active_conversations=set(),
                    shared_context=initial_context or {},
                    last_activity=datetime.now(),
                    performance_metrics={}
                )
            else:
                # Update existing agent state
                agent_state = self.agent_states[agent_name]
                agent_state.current_page = current_page
                agent_state.last_activity = datetime.now()
                if initial_context:
                    agent_state.shared_context.update(initial_context)
            
            # Notify other agents of registration
            await self._broadcast_message(
                sender_agent=agent_name,
                message_type=MessageType.STATE_UPDATE,
                content={
                    "event": "agent_registered",
                    "page": current_page,
                    "client_account_id": client_account_id,
                    "engagement_id": engagement_id
                },
                page_context=current_page,
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            
            logger.info(f"Registered agent {agent_name} on page {current_page}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering agent {agent_name}: {str(e)}")
            return False
    
    async def update_agent_state(
        self,
        agent_name: str,
        new_state: AgentState,
        current_task: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update agent state and notify coordination system"""
        try:
            if agent_name not in self.agent_states:
                logger.warning(f"Agent {agent_name} not registered")
                return False
            
            agent_state = self.agent_states[agent_name]
            old_state = agent_state.current_state
            
            agent_state.current_state = new_state
            agent_state.current_task = current_task
            agent_state.last_activity = datetime.now()
            
            if additional_context:
                agent_state.shared_context.update(additional_context)
            
            # Handle state transitions
            await self._handle_state_transition(agent_name, old_state, new_state)
            
            # Notify other agents
            await self._broadcast_message(
                sender_agent=agent_name,
                message_type=MessageType.STATE_UPDATE,
                content={
                    "event": "state_changed",
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "current_task": current_task,
                    "context": additional_context
                },
                page_context=agent_state.current_page,
                client_account_id=0,  # Will be filled by context
                engagement_id=""
            )
            
            logger.info(f"Updated agent {agent_name} state: {old_state.value} -> {new_state.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent state: {str(e)}")
            return False
    
    async def create_cross_page_context(
        self,
        context_type: str,
        context_data: Dict[str, Any],
        participating_pages: List[str],
        client_account_id: int,
        engagement_id: str,
        expiry_hours: Optional[int] = 24
    ) -> str:
        """Create cross-page context for agent communication"""
        try:
            context_id = self._generate_context_id(context_type, participating_pages)
            
            expiry_time = None
            if expiry_hours:
                expiry_time = datetime.now() + timedelta(hours=expiry_hours)
            
            context = CrossPageContext(
                context_id=context_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                context_type=context_type,
                context_data=context_data,
                participating_agents=set(),
                participating_pages=set(participating_pages),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                expiry_time=expiry_time
            )
            
            self.cross_page_contexts[context_id] = context
            
            # Notify relevant agents
            await self._notify_agents_of_context(context)
            
            logger.info(f"Created cross-page context {context_id} for pages: {participating_pages}")
            return context_id
            
        except Exception as e:
            logger.error(f"Error creating cross-page context: {str(e)}")
            return ""
    
    async def add_agent_to_context(
        self,
        context_id: str,
        agent_name: str
    ) -> bool:
        """Add agent to cross-page context"""
        try:
            if context_id not in self.cross_page_contexts:
                logger.warning(f"Context {context_id} not found")
                return False
            
            context = self.cross_page_contexts[context_id]
            context.participating_agents.add(agent_name)
            context.updated_at = datetime.now()
            
            # Update agent's shared context
            if agent_name in self.agent_states:
                agent_state = self.agent_states[agent_name]
                agent_state.shared_context[f"cross_page_context_{context_id}"] = {
                    "context_type": context.context_type,
                    "context_data": context.context_data,
                    "participating_pages": list(context.participating_pages)
                }
            
            logger.info(f"Added agent {agent_name} to context {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding agent to context: {str(e)}")
            return False
    
    async def send_message(
        self,
        sender_agent: str,
        recipient_agents: List[str],
        message_type: MessageType,
        content: Dict[str, Any],
        priority: int = 2,
        requires_response: bool = False,
        response_deadline_minutes: Optional[int] = None
    ) -> str:
        """Send message between agents"""
        try:
            message_id = self._generate_message_id(sender_agent, recipient_agents, message_type)
            
            # Get sender context
            sender_state = self.agent_states.get(sender_agent)
            if not sender_state:
                logger.warning(f"Sender agent {sender_agent} not registered")
                return ""
            
            response_deadline = None
            if requires_response and response_deadline_minutes:
                response_deadline = datetime.now() + timedelta(minutes=response_deadline_minutes)
            
            message = AgentMessage(
                message_id=message_id,
                sender_agent=sender_agent,
                recipient_agents=recipient_agents,
                message_type=message_type,
                content=content,
                priority=priority,
                page_context=sender_state.current_page,
                client_account_id=0,  # Will be filled from context
                engagement_id="",
                timestamp=datetime.now(),
                requires_response=requires_response,
                response_deadline=response_deadline
            )
            
            # Add to message bus
            self.message_bus.append(message)
            
            # Deliver to recipients
            await self._deliver_message(message)
            
            logger.info(f"Sent message {message_id} from {sender_agent} to {recipient_agents}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return ""
    
    async def create_collaboration_group(
        self,
        group_name: str,
        participating_agents: List[str],
        coordination_level: CoordinationLevel,
        shared_objective: str,
        group_leader: Optional[str] = None
    ) -> str:
        """Create collaboration group for agents"""
        try:
            group_id = self._generate_group_id(group_name, participating_agents)
            
            group = CollaborationGroup(
                group_id=group_id,
                group_name=group_name,
                participating_agents=set(participating_agents),
                coordination_level=coordination_level,
                shared_objective=shared_objective,
                shared_data={},
                group_leader=group_leader,
                created_at=datetime.now(),
                status="active"
            )
            
            self.collaboration_groups[group_id] = group
            
            # Update agent states
            for agent_name in participating_agents:
                if agent_name in self.agent_states:
                    self.agent_states[agent_name].collaboration_group = group_id
            
            # Notify agents of group creation
            await self._notify_group_creation(group)
            
            logger.info(f"Created collaboration group {group_id}: {group_name}")
            return group_id
            
        except Exception as e:
            logger.error(f"Error creating collaboration group: {str(e)}")
            return ""
    
    async def get_agent_messages(
        self,
        agent_name: str,
        message_types: Optional[List[MessageType]] = None,
        limit: int = 50
    ) -> List[AgentMessage]:
        """Get messages for specific agent"""
        try:
            if agent_name not in self.agent_states:
                return []
            
            agent_state = self.agent_states[agent_name]
            messages = list(agent_state.message_queue)
            
            # Filter by message types if specified
            if message_types:
                messages = [m for m in messages if m.message_type in message_types]
            
            # Sort by priority and timestamp
            messages.sort(key=lambda m: (m.priority, m.timestamp), reverse=True)
            
            return messages[:limit]
            
        except Exception as e:
            logger.error(f"Error getting agent messages: {str(e)}")
            return []
    
    async def get_cross_page_contexts(
        self,
        agent_name: str,
        context_type: Optional[str] = None
    ) -> List[CrossPageContext]:
        """Get cross-page contexts for agent"""
        try:
            contexts = []
            
            for context in self.cross_page_contexts.values():
                if agent_name in context.participating_agents:
                    if context_type is None or context.context_type == context_type:
                        # Check if context has expired
                        if context.expiry_time and datetime.now() > context.expiry_time:
                            continue
                        contexts.append(context)
            
            # Sort by creation time
            contexts.sort(key=lambda c: c.created_at, reverse=True)
            
            return contexts
            
        except Exception as e:
            logger.error(f"Error getting cross-page contexts: {str(e)}")
            return []
    
    async def synchronize_learning(
        self,
        agent_name: str,
        learning_data: Dict[str, Any]
    ) -> bool:
        """Synchronize learning across agents"""
        try:
            # Broadcast learning update to relevant agents
            await self._broadcast_message(
                sender_agent=agent_name,
                message_type=MessageType.LEARNING_UPDATE,
                content={
                    "learning_type": learning_data.get("type", "unknown"),
                    "learning_data": learning_data,
                    "confidence": learning_data.get("confidence", 0.5),
                    "domain": learning_data.get("domain", "general")
                },
                page_context="",  # Learning is cross-page
                client_account_id=0,
                engagement_id=""
            )
            
            # Update coordination rules based on learning
            await self._update_coordination_rules(learning_data)
            
            logger.info(f"Synchronized learning from agent {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error synchronizing learning: {str(e)}")
            return False
    
    async def get_coordination_status(
        self,
        client_account_id: Optional[int] = None,
        engagement_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get overall coordination status"""
        try:
            status = {
                "total_agents": len(self.agent_states),
                "active_agents": len([a for a in self.agent_states.values() 
                                   if a.current_state not in [AgentState.IDLE, AgentState.ERROR]]),
                "collaboration_groups": len(self.collaboration_groups),
                "cross_page_contexts": len(self.cross_page_contexts),
                "message_queue_size": len(self.message_bus),
                "agent_distribution": {},
                "recent_activity": [],
                "coordination_health": "healthy"
            }
            
            # Agent distribution by page
            page_distribution = defaultdict(int)
            state_distribution = defaultdict(int)
            
            for agent_state in self.agent_states.values():
                page_distribution[agent_state.current_page] += 1
                state_distribution[agent_state.current_state.value] += 1
            
            status["agent_distribution"] = {
                "by_page": dict(page_distribution),
                "by_state": dict(state_distribution)
            }
            
            # Recent activity
            recent_messages = list(self.message_bus)[-10:]
            status["recent_activity"] = [
                {
                    "message_id": m.message_id,
                    "sender": m.sender_agent,
                    "type": m.message_type.value,
                    "timestamp": m.timestamp.isoformat(),
                    "page_context": m.page_context
                } for m in recent_messages
            ]
            
            # Health assessment
            error_agents = len([a for a in self.agent_states.values() 
                              if a.current_state == AgentState.ERROR])
            if error_agents > 0:
                status["coordination_health"] = "degraded"
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting coordination status: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup_expired_contexts(self) -> int:
        """Clean up expired cross-page contexts"""
        try:
            current_time = datetime.now()
            expired_contexts = []
            
            for context_id, context in self.cross_page_contexts.items():
                if context.expiry_time and current_time > context.expiry_time:
                    expired_contexts.append(context_id)
            
            for context_id in expired_contexts:
                del self.cross_page_contexts[context_id]
                
                # Notify agents of context expiry
                await self._broadcast_message(
                    sender_agent="coordinator",
                    message_type=MessageType.STATE_UPDATE,
                    content={
                        "event": "context_expired",
                        "context_id": context_id
                    },
                    page_context="system",
                    client_account_id=0,
                    engagement_id=""
                )
            
            logger.info(f"Cleaned up {len(expired_contexts)} expired contexts")
            return len(expired_contexts)
            
        except Exception as e:
            logger.error(f"Error cleaning up expired contexts: {str(e)}")
            return 0
    
    # Private helper methods
    
    async def _state_synchronizer(self) -> None:
        """Background task for state synchronization"""
        while True:
            try:
                await asyncio.sleep(30)  # Run every 30 seconds
                
                # Clean up expired contexts
                await self.cleanup_expired_contexts()
                
                # Update agent performance metrics
                await self._update_performance_metrics()
                
                # Process pending coordination tasks
                await self._process_coordination_tasks()
                
            except Exception as e:
                logger.error(f"Error in state synchronizer: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _initialize_coordination_rules(self) -> None:
        """Initialize coordination rules"""
        self.coordination_rules = {
            "field_mapping": {
                "requires_collaboration": True,
                "coordination_level": CoordinationLevel.COLLABORATIVE,
                "participating_agents": ["Data Source Intelligence Agent", "Field Mapping Intelligence Agent"]
            },
            "application_discovery": {
                "requires_collaboration": True,
                "coordination_level": CoordinationLevel.COORDINATED,
                "participating_agents": ["Application Intelligence Agent", "Asset Intelligence Agent", "Dependency Intelligence Agent"]
            },
            "data_quality": {
                "requires_collaboration": False,
                "coordination_level": CoordinationLevel.INDIVIDUAL,
                "participating_agents": ["Data Quality Assessment Agent"]
            }
        }
    
    async def _handle_state_transition(
        self,
        agent_name: str,
        old_state: AgentState,
        new_state: AgentState
    ) -> None:
        """Handle agent state transitions"""
        try:
            # Handle specific transitions
            if new_state == AgentState.WAITING_FOR_INPUT:
                # Notify relevant agents that input is needed
                await self._request_collaboration_input(agent_name)
            
            elif new_state == AgentState.COMPLETED:
                # Share completion results with other agents
                await self._share_completion_results(agent_name)
            
            elif new_state == AgentState.ERROR:
                # Attempt error recovery coordination
                await self._coordinate_error_recovery(agent_name)
        
        except Exception as e:
            logger.error(f"Error handling state transition: {str(e)}")
    
    async def _broadcast_message(
        self,
        sender_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        page_context: str,
        client_account_id: int,
        engagement_id: str,
        exclude_agents: Optional[Set[str]] = None
    ) -> None:
        """Broadcast message to all relevant agents"""
        try:
            exclude_agents = exclude_agents or set()
            exclude_agents.add(sender_agent)  # Don't send to sender
            
            recipient_agents = [
                agent_name for agent_name in self.agent_states.keys()
                if agent_name not in exclude_agents
            ]
            
            if recipient_agents:
                await self.send_message(
                    sender_agent=sender_agent,
                    recipient_agents=recipient_agents,
                    message_type=message_type,
                    content=content,
                    priority=2
                )
        
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
    
    async def _deliver_message(self, message: AgentMessage) -> None:
        """Deliver message to recipient agents"""
        try:
            for recipient in message.recipient_agents:
                if recipient in self.agent_states:
                    agent_state = self.agent_states[recipient]
                    agent_state.message_queue.append(message)
                    
                    # Notify subscribers
                    if recipient in self.subscribers:
                        for callback in self.subscribers[recipient]:
                            try:
                                if callable(callback):
                                    await callback(message)
                            except Exception as e:
                                logger.error(f"Error in subscriber callback: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error delivering message: {str(e)}")
    
    async def _notify_agents_of_context(self, context: CrossPageContext) -> None:
        """Notify agents of new cross-page context"""
        try:
            # Find agents on participating pages
            relevant_agents = [
                agent_name for agent_name, agent_state in self.agent_states.items()
                if agent_state.current_page in context.participating_pages
            ]
            
            if relevant_agents:
                await self.send_message(
                    sender_agent="coordinator",
                    recipient_agents=relevant_agents,
                    message_type=MessageType.STATE_UPDATE,
                    content={
                        "event": "cross_page_context_created",
                        "context_id": context.context_id,
                        "context_type": context.context_type,
                        "participating_pages": list(context.participating_pages)
                    },
                    priority=1
                )
        
        except Exception as e:
            logger.error(f"Error notifying agents of context: {str(e)}")
    
    async def _notify_group_creation(self, group: CollaborationGroup) -> None:
        """Notify agents of collaboration group creation"""
        try:
            await self.send_message(
                sender_agent="coordinator",
                recipient_agents=list(group.participating_agents),
                message_type=MessageType.COLLABORATION_REQUEST,
                content={
                    "event": "group_created",
                    "group_id": group.group_id,
                    "group_name": group.group_name,
                    "coordination_level": group.coordination_level.value,
                    "shared_objective": group.shared_objective,
                    "group_leader": group.group_leader
                },
                priority=1
            )
        
        except Exception as e:
            logger.error(f"Error notifying group creation: {str(e)}")
    
    async def _request_collaboration_input(self, agent_name: str) -> None:
        """Request collaboration input when agent needs help"""
        # Implementation for requesting collaboration
        pass
    
    async def _share_completion_results(self, agent_name: str) -> None:
        """Share agent completion results with others"""
        # Implementation for sharing results
        pass
    
    async def _coordinate_error_recovery(self, agent_name: str) -> None:
        """Coordinate error recovery for failed agent"""
        # Implementation for error recovery coordination
        pass
    
    async def _update_coordination_rules(self, learning_data: Dict[str, Any]) -> None:
        """Update coordination rules based on learning"""
        # Implementation for updating coordination rules
        pass
    
    async def _update_performance_metrics(self) -> None:
        """Update agent performance metrics"""
        # Implementation for updating performance metrics
        pass
    
    async def _process_coordination_tasks(self) -> None:
        """Process pending coordination tasks"""
        # Implementation for processing coordination tasks
        pass
    
    def _generate_context_id(self, context_type: str, participating_pages: List[str]) -> str:
        """Generate unique context ID"""
        content = f"{context_type}_{sorted(participating_pages)}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_message_id(
        self,
        sender_agent: str,
        recipient_agents: List[str],
        message_type: MessageType
    ) -> str:
        """Generate unique message ID"""
        content = f"{sender_agent}_{sorted(recipient_agents)}_{message_type.value}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _generate_group_id(self, group_name: str, participating_agents: List[str]) -> str:
        """Generate unique group ID"""
        content = f"{group_name}_{sorted(participating_agents)}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

# Global instance for agent coordination
agent_coordinator = AgentCoordinator() 