# Phase 2 - Agent B1: CrewAI Flow Framework Implementation

## Context
You are part of Phase 2 remediation effort to transform the AI Force Migration Platform to proper CrewAI architecture. This is Track B (Flows) focusing on implementing proper CrewAI Flow patterns with `@start` and `@listen` decorators, replacing manual orchestration.

### Required Reading Before Starting
- `docs/planning/PHASE-2-REMEDIATION-PLAN.md` - Phase 2 objectives
- `backend/app/services/crewai_flows/unified_discovery_flow.py` - Current implementation
- CrewAI documentation on Flows and decorators
- `AGENT_A1_AGENT_SYSTEM_CORE.md` and `AGENT_A2_CREW_MANAGEMENT.md`

### Prerequisites
- API v3 consolidation complete from Phase 1
- Agent registry and crews available from Track A
- PostgreSQL-only state management ready

### Phase 2 Goal
Transform the manual orchestration patterns into proper CrewAI Flows using `@start` and `@listen` decorators. Create a clean, event-driven flow architecture that leverages CrewAI's built-in flow control.

## Your Specific Tasks

### 1. Create Base Flow Framework
**File to create**: `backend/app/services/flows/base_flow.py`

```python
"""
Base CrewAI Flow implementation with proper patterns
"""

from abc import abstractmethod
from typing import Dict, Any, Optional, List
from crewai.flow.flow import Flow, start, listen
from pydantic import BaseModel
from app.core.context import get_current_context, RequestContext
from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json

logger = logging.getLogger(__name__)

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
        # TODO: Integrate with event bus
    
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
```

### 2. Implement Discovery Flow with Decorators
**File to update**: `backend/app/services/crewai_flows/unified_discovery_flow.py`

```python
"""
Unified Discovery Flow with proper CrewAI patterns
"""

from typing import Dict, Any, List, Optional
from crewai.flow.flow import Flow, start, listen
from pydantic import BaseModel, Field
from app.services.flows.base_flow import BaseDiscoveryFlow, BaseFlowState
from app.services.crews.factory import CrewFactory
from app.core.context import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

class DiscoveryFlowState(BaseFlowState):
    """Complete state for discovery flow"""
    # Data import info
    data_import_id: str = ""
    import_filename: str = ""
    total_records: int = 0
    
    # Phase-specific results
    field_mappings: Dict[str, Any] = {}
    cleansed_data: Dict[str, Any] = {}
    discovered_assets: List[Dict[str, Any]] = []
    dependencies: Dict[str, Any] = {}
    tech_debt_analysis: Dict[str, Any] = {}
    
    # Progress tracking
    progress_percentage: float = 0.0
    phase_timings: Dict[str, float] = {}

class UnifiedDiscoveryFlow(BaseDiscoveryFlow):
    """
    Discovery flow with proper CrewAI patterns.
    Uses @start and @listen decorators for flow control.
    """
    
    @property
    def state_class(self):
        return DiscoveryFlowState
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        """Initialize discovery flow"""
        super().__init__(db, context)
        self.crew_factory = CrewFactory()
    
    @start()
    async def initialize_discovery(self, import_data: Dict[str, Any]) -> DiscoveryFlowState:
        """
        Start the discovery flow with data import.
        This is the entry point triggered by external call.
        """
        logger.info("Starting discovery flow initialization")
        
        # Create initial state
        self.state = DiscoveryFlowState(
            flow_id=import_data["flow_id"],
            client_account_id=self.context.client_account_id,
            engagement_id=self.context.engagement_id,
            user_id=self.context.user_id,
            data_import_id=import_data["import_id"],
            import_filename=import_data["filename"],
            total_records=import_data["record_count"],
            current_phase="initialization"
        )
        
        # Save initial state
        await self.save_state(self.state)
        
        # Emit start event
        self.emit_event("flow_started", {
            "import_id": self.state.data_import_id,
            "filename": self.state.import_filename,
            "records": self.state.total_records
        })
        
        return self.state
    
    @listen(initialize_discovery)
    async def validate_and_analyze_data(self, initial_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Validate imported data and perform initial analysis.
        Triggered automatically after initialization.
        """
        logger.info(f"Starting data validation for flow {initial_state.flow_id}")
        
        self.state = initial_state
        self.state.current_phase = "data_validation"
        
        try:
            # Execute validation crew
            validation_result = await self.crew_factory.execute_crew(
                crew_type="data_validation",
                inputs={
                    "import_id": self.state.data_import_id,
                    "flow_id": self.state.flow_id
                }
            )
            
            # Update state with results
            self.state.metadata["validation_results"] = validation_result
            self.state.phases_completed.append("data_validation")
            self.state.progress_percentage = 10.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "data_validation",
                "status": validation_result.get("status", "unknown")
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "data_validation")
            raise
    
    @listen(validate_and_analyze_data)
    async def perform_field_mapping(self, validated_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Perform intelligent field mapping.
        Triggered after successful validation.
        """
        logger.info(f"Starting field mapping for flow {validated_state.flow_id}")
        
        self.state = validated_state
        self.state.current_phase = "field_mapping"
        
        try:
            # Get source schema from validation results
            validation_results = self.state.metadata.get("validation_results", {})
            source_schema = validation_results.get("schema", {})
            
            # Execute field mapping crew
            mapping_result = await self.crew_factory.execute_crew(
                crew_type="field_mapping",
                inputs={
                    "import_id": self.state.data_import_id,
                    "source_schema": source_schema,
                    "target_fields": await self._get_target_fields()
                }
            )
            
            # Update state with mappings
            self.state.field_mappings = mapping_result.get("mappings", {})
            self.state.phases_completed.append("field_mapping")
            self.state.progress_percentage = 30.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "field_mapping",
                "mappings_created": len(self.state.field_mappings)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "field_mapping")
            raise
    
    @listen(perform_field_mapping)
    async def cleanse_data(self, mapped_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Cleanse data based on field mappings.
        Triggered after field mapping completion.
        """
        logger.info(f"Starting data cleansing for flow {mapped_state.flow_id}")
        
        self.state = mapped_state
        self.state.current_phase = "data_cleansing"
        
        try:
            # Execute data cleansing crew
            cleansing_result = await self.crew_factory.execute_crew(
                crew_type="data_cleansing",
                inputs={
                    "import_id": self.state.data_import_id,
                    "field_mappings": self.state.field_mappings
                }
            )
            
            # Update state
            self.state.cleansed_data = cleansing_result.get("cleansed_data", {})
            self.state.phases_completed.append("data_cleansing")
            self.state.progress_percentage = 50.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "data_cleansing",
                "records_cleansed": cleansing_result.get("records_processed", 0)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "data_cleansing")
            raise
    
    @listen(cleanse_data)
    async def build_asset_inventory(self, cleansed_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Build asset inventory from cleansed data.
        Triggered after data cleansing.
        """
        logger.info(f"Starting asset inventory for flow {cleansed_state.flow_id}")
        
        self.state = cleansed_state
        self.state.current_phase = "asset_inventory"
        
        try:
            # Execute asset inventory crew
            inventory_result = await self.crew_factory.execute_crew(
                crew_type="asset_inventory",
                inputs={
                    "import_id": self.state.data_import_id,
                    "cleansed_data": self.state.cleansed_data
                }
            )
            
            # Update state
            self.state.discovered_assets = inventory_result.get("assets", [])
            self.state.phases_completed.append("asset_inventory")
            self.state.progress_percentage = 70.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "asset_inventory",
                "assets_discovered": len(self.state.discovered_assets)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "asset_inventory")
            raise
    
    @listen(build_asset_inventory)
    async def analyze_dependencies(self, inventory_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Analyze dependencies between discovered assets.
        Triggered after asset inventory.
        """
        logger.info(f"Starting dependency analysis for flow {inventory_state.flow_id}")
        
        self.state = inventory_state
        self.state.current_phase = "dependency_analysis"
        
        try:
            # Execute dependency analysis crew
            dependency_result = await self.crew_factory.execute_crew(
                crew_type="dependency_analysis",
                inputs={
                    "assets": self.state.discovered_assets
                }
            )
            
            # Update state
            self.state.dependencies = dependency_result.get("dependencies", {})
            self.state.phases_completed.append("dependency_analysis")
            self.state.progress_percentage = 90.0
            
            # Save state
            await self.save_state(self.state)
            
            # Emit completion event
            self.emit_event("phase_completed", {
                "phase": "dependency_analysis",
                "dependencies_found": dependency_result.get("total_dependencies", 0)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "dependency_analysis")
            raise
    
    @listen(analyze_dependencies)
    async def assess_technical_debt(self, analyzed_state: DiscoveryFlowState) -> DiscoveryFlowState:
        """
        Final phase: Assess technical debt and provide recommendations.
        Triggered after dependency analysis.
        """
        logger.info(f"Starting technical debt assessment for flow {analyzed_state.flow_id}")
        
        self.state = analyzed_state
        self.state.current_phase = "technical_debt"
        
        try:
            # Execute tech debt analysis crew
            tech_debt_result = await self.crew_factory.execute_crew(
                crew_type="tech_debt_analysis",
                inputs={
                    "assets": self.state.discovered_assets,
                    "dependencies": self.state.dependencies
                }
            )
            
            # Update state
            self.state.tech_debt_analysis = tech_debt_result
            self.state.phases_completed.append("technical_debt")
            self.state.progress_percentage = 100.0
            self.state.current_phase = "completed"
            
            # Save final state
            await self.save_state(self.state)
            
            # Emit completion events
            self.emit_event("phase_completed", {
                "phase": "technical_debt",
                "recommendations": len(tech_debt_result.get("recommendations", []))
            })
            
            self.emit_event("flow_completed", {
                "flow_id": self.state.flow_id,
                "total_phases": len(self.state.phases_completed),
                "assets_discovered": len(self.state.discovered_assets)
            })
            
            return self.state
            
        except Exception as e:
            self.handle_error(e, "technical_debt")
            raise
    
    async def _get_target_fields(self) -> List[Dict[str, Any]]:
        """Get available target fields for mapping"""
        # TODO: Implement fetching from database
        return []
```

### 3. Create Flow Manager
**File to create**: `backend/app/services/flows/manager.py`

```python
"""
Flow Manager for lifecycle management
"""

from typing import Dict, Any, Optional, List
from app.services.flows.base_flow import BaseDiscoveryFlow
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
from app.core.context import RequestContext
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import logging

logger = logging.getLogger(__name__)

class FlowManager:
    """
    Manages flow lifecycle and execution.
    Features:
    - Flow creation and initialization
    - Execution management
    - Status tracking
    - Flow resumption
    """
    
    def __init__(self):
        self.active_flows: Dict[str, BaseDiscoveryFlow] = {}
        self.flow_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_discovery_flow(
        self,
        db: AsyncSession,
        context: RequestContext,
        import_data: Dict[str, Any]
    ) -> str:
        """Create and start a new discovery flow"""
        flow = UnifiedDiscoveryFlow(db, context)
        flow_id = import_data["flow_id"]
        
        # Store flow instance
        self.active_flows[flow_id] = flow
        
        # Start flow execution in background
        task = asyncio.create_task(
            flow.kickoff(inputs={"import_data": import_data})
        )
        self.flow_tasks[flow_id] = task
        
        logger.info(f"Created and started discovery flow: {flow_id}")
        return flow_id
    
    async def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a flow"""
        flow = self.active_flows.get(flow_id)
        if not flow:
            return None
        
        # Load current state
        state = await flow.load_state(flow_id)
        if not state:
            return None
        
        return {
            "flow_id": flow_id,
            "current_phase": state.current_phase,
            "phases_completed": state.phases_completed,
            "progress_percentage": state.progress_percentage,
            "error": state.error,
            "is_active": flow_id in self.flow_tasks and not self.flow_tasks[flow_id].done()
        }
    
    async def pause_flow(self, flow_id: str) -> bool:
        """Pause a running flow"""
        task = self.flow_tasks.get(flow_id)
        if task and not task.done():
            task.cancel()
            logger.info(f"Paused flow: {flow_id}")
            return True
        return False
    
    async def resume_flow(
        self,
        flow_id: str,
        db: AsyncSession,
        context: RequestContext
    ) -> bool:
        """Resume a paused flow from last checkpoint"""
        # Create new flow instance
        flow = UnifiedDiscoveryFlow(db, context)
        
        # Load existing state
        state = await flow.load_state(flow_id)
        if not state:
            logger.error(f"No state found for flow: {flow_id}")
            return False
        
        # Determine resume point based on completed phases
        resume_method = self._get_resume_method(state.phases_completed)
        if not resume_method:
            logger.error(f"Cannot determine resume point for flow: {flow_id}")
            return False
        
        # Store flow instance
        self.active_flows[flow_id] = flow
        
        # Resume execution
        task = asyncio.create_task(
            resume_method(flow, state)
        )
        self.flow_tasks[flow_id] = task
        
        logger.info(f"Resumed flow: {flow_id} from phase {state.current_phase}")
        return True
    
    def _get_resume_method(self, phases_completed: List[str]):
        """Determine which method to call for resumption"""
        phase_methods = {
            "initialization": "validate_and_analyze_data",
            "data_validation": "perform_field_mapping",
            "field_mapping": "cleanse_data",
            "data_cleansing": "build_asset_inventory",
            "asset_inventory": "analyze_dependencies",
            "dependency_analysis": "assess_technical_debt"
        }
        
        # Find next phase
        for phase, method in phase_methods.items():
            if phase not in phases_completed:
                return lambda flow, state: getattr(flow, method)(state)
        
        return None
    
    async def cleanup_completed_flows(self) -> int:
        """Clean up completed flow instances"""
        cleaned = 0
        
        for flow_id in list(self.flow_tasks.keys()):
            task = self.flow_tasks[flow_id]
            if task.done():
                del self.flow_tasks[flow_id]
                if flow_id in self.active_flows:
                    del self.active_flows[flow_id]
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} completed flows")
        return cleaned

# Global flow manager instance
flow_manager = FlowManager()
```

### 4. Create Event Bus Integration
**File to create**: `backend/app/services/flows/events.py`

```python
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

# Global event bus instance
flow_event_bus = FlowEventBus()

# WebSocket handler integration
async def websocket_event_handler(event: FlowEvent):
    """Send flow events to WebSocket clients"""
    # TODO: Integrate with actual WebSocket manager
    logger.info(f"WebSocket event: {event.event_type} for flow {event.flow_id}")

# Subscribe WebSocket handler
flow_event_bus.subscribe("*", websocket_event_handler)
```

### 5. Update Flow Endpoints
**File to update**: `backend/app/api/v3/discovery_flow.py`

Add endpoints for flow management:
- Start flow with CrewAI kickoff
- Get flow status
- Pause/resume flows
- Subscribe to flow events

## Success Criteria
- [ ] Base flow framework with proper CrewAI patterns
- [ ] Discovery flow uses @start/@listen decorators
- [ ] Flow manager handles lifecycle
- [ ] Event bus publishes flow events
- [ ] State persistence works correctly
- [ ] Flow can be paused and resumed
- [ ] All phases execute in sequence

## Interfaces with Other Agents
- **Agent A1/A2** provide agents and crews you orchestrate
- **Agent C1** shares context management patterns
- **Agent D1** uses your flow patterns for tools
- Coordinate on state schema

## Implementation Guidelines

### 1. Decorator Usage
```python
@start()  # Entry point - external trigger
async def begin_flow(self, inputs):
    # Initialize state
    return state

@listen(begin_flow)  # Chained execution
async def next_phase(self, previous_state):
    # Process and return updated state
```

### 2. State Management
- Always save state after updates
- Handle errors gracefully
- Enable resumption from any phase

### 3. Event Patterns
- Emit events at phase boundaries
- Include relevant metrics
- Enable real-time monitoring

## Commands to Run
```bash
# Test flow creation
docker exec -it migration_backend python -m app.services.flows.test_flow_creation

# Test flow execution
docker exec -it migration_backend python -m pytest tests/flows/test_discovery_flow.py -v

# Monitor flow events
docker exec -it migration_backend python -m app.services.flows.monitor_events
```

## Definition of Done
- [ ] Base flow framework implemented
- [ ] Discovery flow fully converted to decorators
- [ ] Flow manager handles lifecycle properly
- [ ] Event bus integrated and working
- [ ] State persistence verified
- [ ] Flow resumption tested
- [ ] Unit tests >85% coverage
- [ ] Integration tests passing
- [ ] PR created with title: "feat: [Phase2-B1] CrewAI Flow framework implementation"

## Notes
- Start with base flow class
- Focus on proper decorator usage
- Test state persistence thoroughly
- Ensure events flow to WebSocket
- Keep flows idempotent for resumption