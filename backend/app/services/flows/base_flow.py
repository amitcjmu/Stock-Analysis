"""
Base CrewAI Flow implementation with proper patterns
"""

import json
import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# CrewAI Flow imports with graceful fallback
CREWAI_FLOW_AVAILABLE = False
try:
    from crewai.flow.flow import Flow, listen, start
    CREWAI_FLOW_AVAILABLE = True
    logger.info("✅ CrewAI Flow imports successful")
except ImportError as e:
    logger.warning(f"CrewAI Flow not available: {e}")
    
    # Fallback implementations
    class Flow:
        def __init__(self): 
            self.state = None
        def __class_getitem__(cls, item):
            return cls
        def kickoff(self):
            return {}
    
    def listen(condition):
        def decorator(func):
            return func
        return decorator
    
    def start():
        def decorator(func):
            return func
        return decorator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore


class BaseFlowState(BaseModel):
    """Base state for all discovery flows"""
    flow_id: str
    client_account_id: str
    engagement_id: str
    user_id: str
    current_phase: str = "initialization"
    phases_completed: List[str] = []
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class BaseDiscoveryFlow(Flow):
    """
    Base class for all discovery flows.
    Provides:
    - Proper CrewAI Flow inheritance
    - PostgreSQL state persistence
    - Multi-tenant context management
    - Standard error handling
    - Event emission patterns
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize with database and context"""
        super().__init__()
        self.db = db
        self.context = context
        self.state_store = PostgresFlowStateStore(db, context)
        
    async def save_state(self, state: BaseFlowState) -> None:
        """Persist state to PostgreSQL"""
        try:
            state_dict = state.model_dump()
            await self.state_store.save_state(
                flow_id=state.flow_id,
                state=state_dict,
                phase=state.current_phase
            )
            logger.info(f"Saved state for flow {state.flow_id} in phase {state.current_phase}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            raise
    
    async def load_state(self, flow_id: str) -> Optional[BaseFlowState]:
        """Load state from PostgreSQL"""
        try:
            state_dict = await self.state_store.load_state(flow_id)
            if state_dict:
                return self.state_class(**state_dict)
            return None
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return None
    
    @property
    @abstractmethod
    def state_class(self):
        """Return the state class for this flow"""
        pass
    
    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit flow events for monitoring"""
        try:
            import asyncio

            from app.services.flows.events import publish_flow_event
            
            # Create event context
            context = {
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id,
                "user_id": getattr(self.context, 'user_id', None)
            }
            
            # Get flow and phase info
            flow_id = self.state.flow_id if hasattr(self, 'state') and self.state else "unknown"
            phase = self.state.current_phase if hasattr(self, 'state') and self.state else "unknown"
            
            # Publish event asynchronously
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(publish_flow_event(flow_id, event_type, phase, data, context))
            except RuntimeError:
                # If no event loop is running, just log
                logger.info(f"Flow event: {event_type} for {flow_id} in phase {phase}")
                
        except Exception as e:
            # Fallback to logging if event bus fails
            logger.warning(f"Event bus unavailable, logging event: {event_type} - {e}")
            event = {
                "flow_id": self.state.flow_id if hasattr(self, 'state') else None,
                "event_type": event_type,
                "phase": self.state.current_phase if hasattr(self, 'state') else None,
                "data": data,
                "context": {
                    "client_account_id": self.context.client_account_id,
                    "engagement_id": self.context.engagement_id
                }
            }
            logger.info(f"Flow event: {json.dumps(event)}")
    
    def handle_error(self, error: Exception, phase: str) -> None:
        """Standard error handling"""
        logger.error(f"Error in phase {phase}: {error}")
        if hasattr(self, 'state'):
            self.state.error = str(error)
        self.emit_event("error", {
            "phase": phase,
            "error": str(error),
            "type": type(error).__name__
        })