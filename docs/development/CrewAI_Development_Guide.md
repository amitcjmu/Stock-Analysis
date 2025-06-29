# CrewAI Development Guide for AI Force Migration Platform

This comprehensive guide explains how to work with CrewAI agents, tasks, crews, and flows within the AI Force Migration Platform, including our custom PostgreSQL persistence layer.

## Table of Contents

1. [CrewAI Core Concepts](#crewai-core-concepts)
2. [Platform-Specific Customizations](#platform-specific-customizations)
3. [Development Patterns](#development-patterns)
4. [Best Practices](#best-practices)
5. [Common Pitfalls](#common-pitfalls)

## CrewAI Core Concepts

### 1. Agents

**Definition**: Autonomous units that perform specific tasks, make independent decisions, and collaborate with other agents.

#### Core Agent Attributes
- **Role**: Defines the agent's function and expertise (e.g., "Senior Data Scientist")
- **Goal**: Guides the agent's decision-making (e.g., "Analyze complex datasets")
- **Backstory**: Provides context and personality (e.g., "Expert at finding patterns in data")

#### Agent Configuration
```python
from crewai import Agent

agent = Agent(
    role="CMDB Data Analyst",
    goal="Analyze and validate CMDB data for migration readiness",
    backstory="Expert in enterprise CMDB systems with 10+ years experience in data quality assessment",
    tools=[SerperDevTool(), CustomMappingTool()],
    verbose=True,
    allow_delegation=False,  # Prevent delegation in our controlled environment
    max_iter=3,  # Limit iterations for performance
    memory=True  # Enable learning from interactions
)
```

#### Key Features
- **Memory Management**: Agents maintain interaction history for learning
- **Tool Integration**: Agents can use specialized tools to accomplish objectives
- **Context Window Management**: Careful management to prevent token overflow
- **Multimodal Capabilities**: Can process text, images, and structured data

### 2. Tasks

**Definition**: Specific assignments completed by agents, designed to facilitate complex workflows.

#### Core Task Attributes
- **Description**: Clear objective specification
- **Expected Output**: Detailed output format requirements
- **Agent Assignment**: Optional specific agent assignment
- **Tools and Context**: Task-specific resources

#### Task Configuration Methods

**YAML Configuration (Recommended)**:
```yaml
data_validation_task:
  description: >
    Validate the imported CMDB data for completeness, accuracy, and migration readiness.
    Focus on identifying missing critical fields, data quality issues, and potential blockers.
  expected_output: >
    A comprehensive validation report containing:
    - Data quality score (0-100)
    - List of critical missing fields
    - Data completeness percentage
    - Recommendations for data cleansing
  agent: cmdb_data_analyst
  tools:
    - data_validation_tool
    - schema_analysis_tool
```

**Direct Code Definition**:
```python
from crewai import Task

task = Task(
    description="Validate CMDB data for migration readiness",
    expected_output="Structured validation report with quality metrics",
    agent=data_analyst_agent,
    tools=[ValidationTool()],
    async_execution=True  # Enable async for better performance
)
```

#### Advanced Task Features
- **Asynchronous Execution**: Use `async_execution=True` for non-blocking operations
- **Structured Output**: Use Pydantic models for type-safe outputs
- **Task Dependencies**: Chain tasks with context sharing
- **Guardrails**: Output validation to ensure quality

### 3. Crews

**Definition**: Collaborative groups of AI agents working together to accomplish complex tasks.

#### Core Crew Attributes
- **Agents**: List of participating agents
- **Tasks**: List of assigned tasks
- **Process**: Execution strategy (sequential/hierarchical)
- **Memory**: Shared memory across agents

#### Crew Configuration
```python
from crewai import Crew, Process

discovery_crew = Crew(
    agents=[
        data_source_agent,
        cmdb_analyst_agent,
        application_discovery_agent
    ],
    tasks=[
        data_validation_task,
        field_mapping_task,
        asset_discovery_task
    ],
    process=Process.sequential,  # Execute tasks in order
    verbose=True,
    memory=True,  # Enable shared crew memory
    max_rpm=100  # Rate limiting for API calls
)
```

#### Execution Modes
- **Sequential**: Tasks executed in defined order (default)
- **Hierarchical**: Manager agent coordinates and validates work

#### Crew Execution
```python
# Synchronous execution
result = crew.kickoff(inputs={"data_source": "cmdb_export.csv"})

# Asynchronous execution
result = await crew.kickoff_async(inputs={"data_source": "cmdb_export.csv"})
```

### 4. Flows

**Definition**: Event-driven workflow orchestrators that combine and coordinate crews and tasks.

#### Core Flow Decorators

**@start() Decorator**:
- Marks method as flow's starting point
- Can have multiple start methods executed in parallel
- Entry point for flow execution

**@listen() Decorator**:
- Marks method as listener for another method's output
- Enables event-driven workflow progression
- Can listen by method name or direct method reference

#### Flow State Management

**Unstructured State (Quick Prototyping)**:
```python
from crewai import Flow

class DiscoveryFlow(Flow[dict]):
    
    @start()
    def initialize_discovery(self):
        self.state = {
            "session_id": str(uuid.uuid4()),
            "status": "initializing",
            "data_sources": []
        }
        return self.state
    
    @listen(initialize_discovery)
    def validate_data_sources(self):
        # Access and modify state
        self.state["status"] = "validating"
        return {"validation_complete": True}
```

**Structured State (Production Recommended)**:
```python
from pydantic import BaseModel
from crewai import Flow

class DiscoveryFlowState(BaseModel):
    session_id: str
    flow_id: str
    client_account_id: str
    engagement_id: str
    current_phase: str
    status: str
    progress_percentage: float
    raw_data: List[Dict[str, Any]]
    field_mappings: Dict[str, Any]
    agent_insights: List[Dict[str, Any]]

class UnifiedDiscoveryFlow(Flow[DiscoveryFlowState]):
    
    @start()
    def initialize_flow(self) -> DiscoveryFlowState:
        self.state = DiscoveryFlowState(
            session_id=str(uuid.uuid4()),
            flow_id=str(uuid.uuid4()),
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            current_phase="initialization",
            status="running",
            progress_percentage=0.0,
            raw_data=[],
            field_mappings={},
            agent_insights=[]
        )
        return self.state
```

#### Flow Control Mechanisms
```python
from crewai.flow.flow import or_, and_, router

class AdvancedDiscoveryFlow(Flow[DiscoveryFlowState]):
    
    @listen(data_validation)
    def conditional_routing(self):
        if self.state.validation_score > 0.8:
            return self.proceed_to_mapping()
        else:
            return self.data_cleansing_required()
    
    @router(conditional_routing)
    def route_based_on_quality(self):
        if self.state.data_quality == "high":
            return self.fast_track_processing
        else:
            return self.detailed_analysis
```

## Platform-Specific Customizations

### PostgreSQL Persistence Layer

Our platform uses a custom PostgreSQL persistence layer instead of CrewAI's default SQLite persistence due to multi-tenancy requirements.

#### Key Components

**PostgreSQLFlowPersistence Class**:
```python
from app.services.crewai_flows.postgresql_flow_persistence import PostgreSQLFlowPersistence

# Initialize with tenant context
persistence = PostgreSQLFlowPersistence(
    client_account_id="client-uuid",
    engagement_id="engagement-uuid",
    user_id="user-uuid"
)

# Persist flow initialization
await persistence.persist_flow_initialization(state)

# Update workflow state
await persistence.update_workflow_state(state)

# Persist phase completion
await persistence.persist_phase_completion(state, "field_mapping", crew_results)
```

#### V2 Architecture Integration

The platform is migrating to V2 DiscoveryFlow architecture:

```python
from app.services.discovery_flow_service import DiscoveryFlowService

# V2 Service Usage
flow_service = DiscoveryFlowService(db_session, context)

# Create new discovery flow
flow = await flow_service.create_discovery_flow(
    flow_id=state.flow_id,
    raw_data=state.raw_data,
    metadata={"source": "crewai_flow"},
    user_id=user_id
)

# Update phase completion
flow = await flow_service.update_phase_completion(
    flow_id=flow.flow_id,
    phase="field_mapping",
    phase_data=crew_results,
    crew_status=state.crew_status,
    agent_insights=state.agent_insights
)
```

#### Multi-Tenant Repository Pattern

All database operations must be client account scoped:

```python
from app.repositories.base import ContextAwareRepository

class CustomRepository(ContextAwareRepository):
    def __init__(self, db: Session, client_account_id: int):
        super().__init__(db, client_account_id)
    
    async def get_tenant_data(self):
        # Automatically scoped to client_account_id
        return await self.db.execute(
            select(Model).where(Model.client_account_id == self.client_account_id)
        )
```

## Development Patterns

### 1. Agent-First Development

**NEVER implement hard-coded rules**:
```python
# ❌ WRONG - Hard-coded logic
def classify_server(server_data):
    if server_data.get('cpu_cores') > 8:
        return 'high_performance'
    return 'standard'

# ✅ CORRECT - Agent-driven intelligence
class ServerClassificationAgent(Agent):
    def classify_server(self, server_data):
        # Let AI analyze patterns and learn
        return self.analyze_with_tools(server_data)
```

### 2. Flow-Based Architecture

Structure workflows using CrewAI Flows:

```python
class MigrationDiscoveryFlow(Flow[DiscoveryFlowState]):
    
    @start()
    def data_ingestion(self):
        """Initialize and ingest data sources"""
        crew = DataIngestionCrew()
        result = crew.kickoff(inputs=self.state.raw_data)
        self.state.current_phase = "data_validation"
        return result
    
    @listen(data_ingestion)
    def data_validation(self):
        """Validate data quality and completeness"""
        crew = DataValidationCrew()
        result = crew.kickoff(inputs=self.state.dict())
        self.state.current_phase = "field_mapping"
        return result
    
    @listen(data_validation)
    def field_mapping(self):
        """Generate intelligent field mappings"""
        crew = FieldMappingCrew()
        result = crew.kickoff(inputs=self.state.dict())
        self.state.current_phase = "asset_inventory"
        return result
```

### 3. Docker-First Development

**ALWAYS use Docker containers**:
```bash
# ✅ CORRECT - Container-based development
docker exec -it migration_backend python -c "
from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
flow = UnifiedDiscoveryFlow()
result = flow.kickoff()
"

# ❌ WRONG - Local development
python -c "from app.services..."  # Don't run locally
```

### 4. Async Database Sessions

Always use async sessions in CrewAI context:

```python
from app.core.database import AsyncSessionLocal

async def crew_database_operation():
    async with AsyncSessionLocal() as session:
        result = await session.execute(query)
        await session.commit()
        return result
```

## Best Practices

### Agent Design (80/20 Rule)

Focus 80% effort on task design, 20% on agent definition:

```python
# ✅ Well-designed task
migration_analysis_task = Task(
    description="""
    Analyze the provided server inventory for migration readiness.
    Consider dependencies, technical debt, and migration complexity.
    
    Specific analysis requirements:
    1. Categorize servers by migration strategy (6 R's)
    2. Identify dependency relationships
    3. Assess technical debt and modernization opportunities
    4. Estimate migration effort and timeline
    """,
    expected_output="""
    Structured migration analysis report containing:
    - Migration strategy recommendations per server
    - Dependency mapping with criticality scores
    - Technical debt assessment with modernization suggestions
    - Migration wave planning with effort estimates
    """,
    agent=migration_strategy_expert
)
```

### State Management

Use structured state for complex flows:

```python
# ✅ Structured state with validation
class FlowState(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    progress: float = Field(ge=0, le=100, description="Progress percentage")
    status: Literal["running", "paused", "completed", "failed"]
    
    class Config:
        validate_assignment = True  # Validate on assignment
```

### Error Handling

Implement comprehensive error handling:

```python
@listen(previous_method)
def robust_crew_execution(self):
    try:
        crew = FieldMappingCrew()
        result = crew.kickoff(inputs=self.state.dict())
        
        # Validate crew results
        if not result or result.get('status') == 'failed':
            self.state.errors.append(f"Crew execution failed: {result}")
            return self.handle_crew_failure()
        
        return result
        
    except Exception as e:
        logger.error(f"Crew execution error: {e}")
        self.state.status = "failed"
        self.state.errors.append(str(e))
        return self.initiate_recovery()
```

### Tool Integration

Create specialized tools for domain tasks:

```python
from crewai_tools import BaseTool

class ServerClassificationTool(BaseTool):
    name: str = "Server Classification Tool"
    description: str = "Classify servers based on characteristics and usage patterns"
    
    def _run(self, server_data: dict) -> dict:
        # AI-driven classification logic
        return {
            "classification": "web_server",
            "confidence": 0.95,
            "reasoning": "High network I/O, web service patterns detected"
        }
```

## Common Pitfalls

### 1. State Management Issues

**❌ WRONG - Mutating state incorrectly**:
```python
def update_progress(self):
    self.state["progress"] = 50  # May not trigger validation
```

**✅ CORRECT - Proper state updates**:
```python
def update_progress(self):
    new_state = self.state.copy(update={"progress": 50})
    self.state = new_state
```

### 2. Agent Over-Engineering

**❌ WRONG - Generic "god" agents**:
```python
universal_agent = Agent(
    role="Universal Migration Expert",
    goal="Handle all migration tasks",
    # Too broad, poor performance
)
```

**✅ CORRECT - Specialized agents**:
```python
dependency_agent = Agent(
    role="Dependency Analysis Specialist",
    goal="Map and analyze application dependencies",
    backstory="Expert in dependency mapping with deep knowledge of enterprise architectures"
)
```

### 3. Persistence Anti-Patterns

**❌ WRONG - Direct SQLite usage**:
```python
# Don't use CrewAI's default SQLite in production
@persist()  # Uses SQLite, not multi-tenant
def flow_method(self):
    pass
```

**✅ CORRECT - PostgreSQL persistence**:
```python
async def flow_method(self):
    # Use our custom PostgreSQL persistence
    await self.persistence_layer.persist_flow_state(self.state)
```

### 4. Task Design Issues

**❌ WRONG - Vague task descriptions**:
```python
Task(
    description="Analyze the data",  # Too vague
    expected_output="Some analysis"  # Not specific
)
```

**✅ CORRECT - Specific, actionable tasks**:
```python
Task(
    description="Analyze server CPU and memory utilization patterns to identify right-sizing opportunities",
    expected_output="JSON report with recommended instance types and cost savings estimates"
)
```

## Integration with Platform Architecture

### WebSocket Updates

Integrate flow progress with real-time updates:

```python
from app.websocket_manager import websocket_manager

@listen(crew_completion)
async def broadcast_progress(self):
    await websocket_manager.broadcast_to_client(
        self.state.client_account_id,
        {
            "type": "flow_progress",
            "flow_id": self.state.flow_id,
            "progress": self.state.progress_percentage,
            "current_phase": self.state.current_phase
        }
    )
```

### Agent Learning Integration

Connect with platform learning system:

```python
@listen(task_completion)
async def capture_learning(self):
    learning_data = {
        "agent_type": "field_mapping",
        "accuracy": self.state.mapping_accuracy,
        "user_feedback": self.state.user_corrections,
        "context": self.state.client_context
    }
    
    await self.learning_service.record_agent_performance(learning_data)
```

This guide provides the foundation for developing with CrewAI in the AI Force Migration Platform. Remember to always follow the agentic-first approach, use Docker containers, and leverage our custom PostgreSQL persistence layer for enterprise-grade multi-tenancy.