# Backend Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [FastAPI Application Structure](#fastapi-application-structure)
3. [Core Services](#core-services)
4. [AI Agent System](#ai-agent-system)
5. [Database Layer](#database-layer)
6. [API Endpoints](#api-endpoints)
7. [Real-time Communication](#real-time-communication)
8. [Configuration Management](#configuration-management)
9. [Error Handling](#error-handling)
10. [Testing](#testing)

## Overview

The backend is built with FastAPI, a modern Python web framework that provides automatic API documentation, type validation, and async support. The architecture follows a layered approach with clear separation of concerns.

### Key Components
- **FastAPI Application**: Main web server and API framework
- **CrewAI Agents**: AI-powered analysis and learning agents
- **SQLAlchemy ORM**: Database abstraction layer
- **Pydantic V2 Schemas**: Data validation and serialization with improved performance and features
- **Polling Service**: HTTP polling for real-time updates (Railway compatible)
- **Service Layer**: Business logic and AI integration

## FastAPI Application Structure

### Application Factory Pattern

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    return app

app = create_application()
```

### Directory Structure

```
backend/app/
├── api/                    # API layer
│   └── v1/
│       ├── api.py         # Main API router
│       └── endpoints/     # Individual endpoint modules
│           ├── discovery.py    # CMDB analysis endpoints
│           ├── migrations.py   # Migration management
│           ├── feedback.py     # User feedback processing
│           └── monitoring_main.py   # Agent monitoring (main router)
├── core/                  # Core configuration
│   ├── config.py         # Settings and configuration
│   ├── database.py       # Database connection
│   └── security.py       # Authentication/authorization
├── models/               # SQLAlchemy models
│   ├── migration.py      # Migration project models
│   ├── asset.py          # Asset models
│   └── feedback.py       # Feedback models
├── schemas/              # Pydantic V2 schemas
│   ├── base.py           # Base schemas and common types
│   ├── migration.py      # Migration request/response schemas
│   ├── asset.py          # Asset schemas
│   ├── feedback.py       # Feedback schemas
│   └── session.py        # Session management schemas
├── services/             # Business logic layer
│   ├── crewai_service.py # Main AI service orchestrator
│   ├── agents.py         # AI agent management
│   ├── field_mapper.py   # Field mapping intelligence
│   ├── analysis.py       # Data analysis services
│   ├── feedback.py       # Feedback processing
│   ├── memory.py         # Agent memory management
│   ├── agent_monitor.py  # Real-time agent monitoring
│   └── tools/            # AI agent tools
│       └── field_mapping_tool.py  # Field mapping tool
└── polling/             # HTTP polling handlers
    └── service.py       # Polling service for real-time updates
```

## Core Services

### Updated Dependencies

```bash
# Updated requirements.txt
fastapi>=0.100.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
# ... other dependencies ...
```

### Database Connection

```python
# Updated database.py with async support
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://user:password@localhost/dbname"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## Core Services

### 1. Master Flow Orchestrator (`master_flow_orchestrator/core.py`)

The central orchestrator for all CrewAI flows with modular architecture.

```python
class MasterFlowOrchestrator:
    """THE SINGLE ORCHESTRATOR - Refactored with modular components
    
    This orchestrator provides:
    - Unified flow lifecycle management (via FlowLifecycleManager)
    - Flow execution and monitoring
    - State synchronization across flow types
    - Error handling and recovery
    """
    
    def __init__(self):
        # Core orchestration components
        self.flow_operations = FlowOperations()
        self.status_operations = StatusOperations()
        self.monitoring_operations = MonitoringOperations()
        self.status_sync_operations = StatusSyncOperations()
        
        # Flow management services
        self.lifecycle_manager = FlowLifecycleManager()
        self.execution_engine = FlowExecutionEngine()
        self.status_manager = FlowStatusManager()
        self.error_handler = FlowErrorHandler()
        self.audit_logger = FlowAuditLogger()
        
        # Specialized services
        self.repair_service = FlowRepairService()
        self.smart_discovery = SmartDiscoveryService()
        self.performance_monitor = MockFlowPerformanceMonitor()
    
    async def create_flow(self, flow_type: str, config: dict, context: RequestContext) -> str:
        """Create a new flow instance with full lifecycle management."""
        return await self.flow_operations.create_flow(flow_type, config, context)
    
    async def execute_flow(self, flow_id: str, phase_input: dict, context: RequestContext) -> dict:
        """Execute flow phase with comprehensive monitoring."""
        return await self.flow_operations.execute_flow(flow_id, phase_input, context)
```

**Key Features:**
- **LLM Integration**: Uses DeepInfra's Llama 4 Maverick model
- **Agent Management**: Creates and manages specialized AI agents
- **Memory System**: Persistent learning across sessions
- **Fallback Logic**: Graceful degradation when AI is unavailable

### 2. CrewAI Flow Service (`crewai_flow_service.py`)

Bridges CrewAI flows with the Discovery Flow architecture.

```python
class CrewAIFlowService:
    """V2 CrewAI Flow Service - Bridges CrewAI flows with Discovery Flow architecture.
    
    Key Features:
    - Uses flow_id as single source of truth instead of session_id
    - Modular components for maintainability
    - Backward compatibility with existing systems
    """
    
    def __init__(self):
        # Modular components
        self.executor = CrewAIFlowExecutor()
        self.lifecycle_manager = CrewAIFlowLifecycleManager()
        self.monitoring = CrewAIFlowMonitoring()
        self.state_manager = CrewAIFlowStateManager()
        self.utils = CrewAIFlowUtils()
        
        # Integration services
        self.discovery_flow_service = DiscoveryFlowService()
        
        # CrewAI Flow integration (conditional)
        if CREWAI_FLOWS_AVAILABLE:
            self.unified_discovery_flow = UnifiedDiscoveryFlow
    
    async def create_flow(self, flow_config: dict, context: RequestContext) -> str:
        """Create a new CrewAI flow instance."""
        return await self.lifecycle_manager.create_flow(flow_config, context)
    
    async def execute_phase(self, flow_id: str, phase_input: dict) -> dict:
        """Execute a flow phase with CrewAI agents."""
        return await self.executor.execute_phase(flow_id, phase_input)
```

**Service Types:**
- **Flow Orchestration**: Central coordination of all workflow types
- **Discovery Flow Service**: Specialized discovery workflow management
- **Assessment Flow Service**: Assessment and analysis workflows
- **Collection Flow Service**: Adaptive data collection workflows
- **Agent Pool Management**: Tenant-scoped agent instance management
- **Performance Monitoring**: Real-time agent and flow performance tracking

### 3. Persistent Agent System (`persistent_agents/`)

Tenant-scoped agent pools with memory and learning capabilities.

```python
class TenantScopedAgentPool:
    """Manages isolated agent instances for each client account.
    Provides persistent agents with tenant-specific memory and configuration."""
    
    def __init__(self, client_account_id: str, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.agent_instances = {}
        self.memory_manager = TenantMemoryManager(client_account_id)
        self.performance_tracker = AgentPerformanceTracker()
    
    async def get_agent(self, agent_type: str, context: dict = None) -> Agent:
        """Get or create a persistent agent for this tenant."""
        agent_key = f"{agent_type}_{self.client_account_id}"
        
        if agent_key not in self.agent_instances:
            agent = await self._create_agent(agent_type, context)
            self.agent_instances[agent_key] = agent
            
        return self.agent_instances[agent_key]
    
    async def _create_agent(self, agent_type: str, context: dict) -> Agent:
        """Create a new agent instance with tenant-specific configuration."""
        config = await self._get_agent_config(agent_type)
        memory = await self.memory_manager.get_agent_memory(agent_type)
        
        return AgentFactory.create_agent(
            agent_type=agent_type,
            config=config,
            memory=memory,
            context=context,
            client_id=self.client_account_id
        )
```

**Key Features:**
- **Dynamic Learning**: Learns from user feedback and AI analysis
- **Fuzzy Matching**: Handles variations in field names
- **Persistent Storage**: Saves learned mappings to JSON file
- **Pattern Recognition**: Identifies common field naming patterns

### 4. Flow Orchestration Services (`flow_orchestration/`)

Modular services for comprehensive flow management.

```python
class FlowExecutionEngine:
    """Core engine for executing flow phases with agent coordination."""
    
    async def execute_phase(self, flow_id: str, phase_name: str, 
                           phase_input: dict, context: RequestContext) -> dict:
        """Execute a specific phase with appropriate agents and monitoring."""
        
        # Get flow configuration
        flow_config = await self.get_flow_config(flow_id)
        
        # Initialize agent pool for tenant
        agent_pool = await self.get_agent_pool(
            context.client_account_id, 
            context.engagement_id
        )
        
        # Execute phase with monitoring
        with self.performance_monitor.track_execution(flow_id, phase_name):
            result = await self._execute_phase_with_agents(
                flow_id, phase_name, phase_input, agent_pool
            )
        
        return result

class FlowStatusManager:
    """Manages flow status and state transitions."""
    
    async def update_flow_status(self, flow_id: str, new_status: str, 
                               context: dict = None) -> bool:
        """Update flow status with validation and audit logging."""
        
        # Validate status transition
        if not await self._validate_status_transition(flow_id, new_status):
            raise InvalidStatusTransitionError(f"Cannot transition to {new_status}")
        
        # Update master flow state
        await self.master_flow_repository.update_status(flow_id, new_status)
        
        # Update child flow state
        await self.child_flow_repository.update_status(flow_id, new_status)
        
        # Log status change
        await self.audit_logger.log_status_change(
            flow_id, new_status, context
        )
        
        return True
```

**Features:**
- **Real-time Tracking**: Monitor agent activities as they happen
- **WebSocket Integration**: Push updates to frontend
- **Task History**: Maintain history of all agent activities
- **Performance Metrics**: Track task duration and success rates

## AI Agent System

### Agent Architecture

The AI agent system is built on CrewAI, providing specialized agents for different aspects of migration analysis.

```python
# Agent Creation Example
def _create_cmdb_analyst_agent(self):
    return Agent(
        role='Senior CMDB Data Analyst',
        goal='Analyze CMDB data with expert precision using field mapping tools',
        backstory="""You are a Senior CMDB Data Analyst with over 15 years 
        of experience in enterprise asset management and cloud migration projects.
        
        IMPORTANT: You have access to a field_mapping_tool that helps you:
        - Query existing field mappings
        - Learn new field mappings from data analysis
        - Analyze data columns to identify missing fields
        
        Always use this tool when analyzing CMDB data.""",
        verbose=False,
        allow_delegation=False,
        llm=self.llm,
        memory=True   # Memory enabled via DeepInfra patch (ADR-019)
    )
```

### Agent Tools

Agents have access to specialized tools for enhanced capabilities:

```python
# Field Mapping Tool
class FieldMappingTool:
    """External tool for AI agents to query and learn field mappings."""
    
    def query_field_mapping(self, source_field: str) -> Dict[str, Any]:
        """Query existing field mappings."""
        
    def learn_field_mapping(self, source_field: str, target_field: str, 
                          source: str) -> Dict[str, Any]:
        """Learn new field mapping."""
        
    def analyze_data_columns(self, columns: List[str], 
                           asset_type: str = "server") -> Dict[str, Any]:
        """Analyze columns and suggest mappings."""
```

### Task Execution

Tasks are executed asynchronously with proper monitoring:

```python
async def _execute_task_async(self, task: Any) -> str:
    """Execute a CrewAI task asynchronously with enhanced monitoring."""
    task_id = str(uuid.uuid4())
    
    try:
        # Start task monitoring
        agent_monitor.start_task(task_id, task.agent.role, task.description)
        
        # Create temporary crew
        temp_crew = Crew(
            agents=[task.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
            memory=True   # Memory enabled via DeepInfra patch
        )
        
        # Execute with timeout
        result = await asyncio.wait_for(
            loop.run_in_executor(executor, temp_crew.kickoff),
            timeout=45.0
        )
        
        # Complete task monitoring
        agent_monitor.complete_task(task_id, str(result))
        return str(result)
        
    except Exception as e:
        agent_monitor.fail_task(task_id, str(e))
        raise
```

## Database Layer

### SQLAlchemy Models

```python
# models/migration.py
class Migration(Base):
    __tablename__ = "migrations"
    __table_args__ = {'schema': 'migration'}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(MigrationStatus), default=MigrationStatus.PLANNING)
    phase = Column(Enum(MigrationPhase), default=MigrationPhase.DISCOVERY)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assets = relationship("Asset", back_populates="migration")
```

### Database Configuration

```python
# core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# High-performance async configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=20,
    max_overflow=30,
    pool_timeout=30,
    pool_recycle=3600,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## API Endpoints

### Discovery Endpoints (`endpoints/discovery.py`)

```python
@router.post("/analyze", response_model=CMDBAnalysisResponse)
async def analyze_cmdb_data(request: CMDBAnalysisRequest):
    """Analyze CMDB data using AI agents."""
    
    try:
        # Parse CSV data
        df = pd.read_csv(io.StringIO(request.content))
        
        # Prepare data for analysis
        analysis_data = {
            'filename': request.filename,
            'headers': df.columns.tolist(),
            'sample_data': df.head(5).values.tolist(),
            'total_rows': len(df)
        }
        
        # Analyze using CrewAI service
        result = await crewai_service.analyze_cmdb_data(analysis_data)
        
        return CMDBAnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in CMDB analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Feedback Endpoints (`endpoints/feedback.py`)

```python
@router.post("/process", response_model=FeedbackResponse)
async def process_feedback(request: FeedbackRequest):
    """Process user feedback for AI learning."""
    
    try:
        # Process feedback through AI learning system
        result = await crewai_service.process_user_feedback(request.dict())
        
        return FeedbackResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

## Real-time Communication

### HTTP Polling Strategy (Railway Deployment)

**IMPORTANT**: The platform uses HTTP polling instead of WebSockets for Railway compatibility.

```python
# services/polling_service.py
class PollingService:
    """Manages HTTP polling for real-time updates without WebSockets."""

    def __init__(self):
        self.active_intervals = {
            'running': 5000,      # 5 seconds for active flows
            'waiting': 15000,     # 15 seconds for waiting states
            'completed': 30000    # 30 seconds for completed flows
        }

    async def get_flow_status(self, flow_id: str, client_context: dict) -> dict:
        """Get current flow status for polling clients."""

        # Get comprehensive flow status
        flow_status = await self.master_flow_service.get_flow_status(flow_id)

        # Determine appropriate polling interval
        polling_interval = self._get_polling_interval(flow_status['status'])

        return {
            'flow_status': flow_status,
            'polling_interval': polling_interval,
            'timestamp': datetime.utcnow().isoformat(),
            'next_poll_in': polling_interval
        }

    def _get_polling_interval(self, status: str) -> int:
        """Return appropriate polling interval based on flow status."""
        if status in ['running', 'in_progress']:
            return self.active_intervals['running']
        elif status in ['waiting', 'paused']:
            return self.active_intervals['waiting']
        else:
            return self.active_intervals['completed']
```

### Polling Endpoints

```python
@router.get("/polling/flow-status/{flow_id}")
async def poll_flow_status(flow_id: str, context: RequestContext = Depends(get_request_context)):
    """Polling endpoint for real-time flow status updates."""

    try:
        polling_service = PollingService()
        status_data = await polling_service.get_flow_status(flow_id, context.dict())

        return {
            'success': True,
            'data': status_data,
            'polling_strategy': 'http_polling',
            'railway_compatible': True
        }

    except Exception as e:
        logger.error(f"Polling error for flow {flow_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'polling_interval': 30000  # Fallback to 30s on error
        }

@router.get("/polling/agent-monitor/{flow_id}")
async def poll_agent_status(flow_id: str):
    """Polling endpoint for agent monitoring updates."""

    status = agent_monitor.get_current_status(flow_id)

    return {
        'agent_status': status,
        'polling_interval': 5000 if status.get('active_tasks') else 15000,
        'timestamp': datetime.utcnow().isoformat()
    }
```

## Pydantic V2 Implementation

### Model Configuration

Pydantic V2 introduces several improvements and changes from V1. Here's how we're using it:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

class FlowBase(BaseModel):
    """Base model for flow data using snake_case fields."""
    flow_id: str = Field(..., description="Unique identifier for the flow")
    flow_display_name: Optional[str] = Field(
        None,
        description="User-friendly display name for the flow"
    )
    client_account_id: str = Field(..., description="Client account identifier")
    engagement_id: str = Field(..., description="Engagement identifier")
    # ... other fields ...

    model_config = {
        "from_attributes": True,  # Replaces orm_mode in Pydantic V1
        "json_schema_extra": {
            "example": {
                "flow_id": "XXXXXXXX-def0-def0-def0-XXXXXXXXXXXX",
                "flow_display_name": "my-discovery-flow",
                "client_account_id": "client_123",
                "engagement_id": "eng_456"
                # ... other example fields ...
            }
        }
    }
```

### Key Changes from V1 to V2

1. **Model Configuration**:
   - Old (V1): `class Config` with `orm_mode = True`
   - New (V2): `model_config` class variable with `from_attributes = True`

2. **Field Configuration**:
   - More powerful Field configuration with better type hints
   - Built-in support for JSON Schema examples
   - Improved validation performance

3. **Serialization**:
   - Use `model_dump()` instead of `dict()`
   - Use `model_dump_json()` instead of `json()`

4. **Field Naming**:
   - **CRITICAL**: All fields use snake_case (e.g., `flow_id`, `client_account_id`)
   - No camelCase transformation - use fields exactly as returned from API

## Configuration Management

### Settings (`core/config.py`)

```python
class Settings(BaseSettings):
    # API Configuration
    PROJECT_NAME: str = "AI Modernize Migration Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost/db"
    DATABASE_ECHO: bool = False
    
    # AI Configuration
    DEEPINFRA_API_KEY: str = ""
    DEEPINFRA_MODEL: str = "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
    CREWAI_ENABLED: bool = True
    CREWAI_TEMPERATURE: float = 0.1
    CREWAI_MAX_TOKENS: int = 1000
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:8081"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Error Handling

### Global Exception Handler

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

## Testing

### Test Structure

```
tests/backend/
├── test_ai_learning.py      # AI learning system tests
├── test_crewai.py          # CrewAI integration tests
├── test_field_mapper.py    # Field mapping tests
├── test_api_endpoints.py   # API endpoint tests
└── conftest.py             # Test configuration
```

### Example Test

```python
# tests/backend/test_ai_learning.py
async def test_ai_learning_scenario():
    """Test AI learning from user feedback."""
    
    # Reset field mappings
    field_mapper.learned_mappings = {}
    
    # Test columns
    test_columns = ['RAM_GB', 'APPLICATION_OWNER', 'DR_TIER']
    
    # Check missing fields before learning
    missing_before = field_mapper.identify_missing_fields(test_columns, 'server')
    
    # Simulate user feedback
    user_feedback = {
        "user_corrections": {
            "analysis_issues": "RAM_GB should map to Memory (GB)"
        }
    }
    
    # Process feedback
    result = await crewai_service.process_user_feedback(user_feedback)
    
    # Check missing fields after learning
    missing_after = field_mapper.identify_missing_fields(test_columns, 'server')
    
    # Verify improvement
    assert len(missing_after) < len(missing_before)
```

## Service Registry and Dynamic Configuration

### Service Registry (`service_registry.py`)

```python
class ServiceRegistry:
    """Dynamic service discovery and configuration management."""
    
    def __init__(self):
        self.services = {}
        self.configurations = {}
        self.health_monitors = {}
    
    def register_service(self, service_name: str, service_instance: Any, 
                        config: dict = None):
        """Register a service with optional configuration."""
        self.services[service_name] = service_instance
        if config:
            self.configurations[service_name] = config
        
        # Setup health monitoring
        self.health_monitors[service_name] = ServiceHealthMonitor(service_instance)
    
    async def get_service(self, service_name: str) -> Any:
        """Get a registered service instance."""
        if service_name not in self.services:
            raise ServiceNotFoundError(f"Service {service_name} not registered")
        
        # Check service health
        if not await self.health_monitors[service_name].is_healthy():
            raise ServiceUnavailableError(f"Service {service_name} is unhealthy")
        
        return self.services[service_name]
```

## Multi-Model Architecture

The platform supports multiple LLM providers and models:

```python
class MultiModelService:
    """Manages multiple LLM providers and models."""
    
    def __init__(self):
        self.providers = {
            "deepinfra": DeepInfraProvider(),
            "openai": OpenAIProvider(),  # Optional
            "anthropic": AnthropicProvider()  # Optional
        }
        self.default_provider = "deepinfra"
    
    async def get_completion(self, prompt: str, model_config: dict = None):
        """Get completion from appropriate model provider."""
        provider_name = model_config.get("provider", self.default_provider)
        provider = self.providers[provider_name]
        
        return await provider.complete(prompt, model_config)
```

This backend architecture provides a robust, scalable foundation for the AI Modernize Migration Platform with:

- **Modular Design**: Clear separation of concerns with composable services
- **Multi-Tenant Architecture**: Complete isolation between client accounts
- **Flow Orchestration**: Centralized coordination of complex workflows
- **Persistent Agent System**: Tenant-scoped agents with memory and learning
- **Comprehensive Monitoring**: Real-time performance tracking and health monitoring
- **Error Handling**: Graceful degradation and recovery mechanisms
- **Security**: RBAC and audit logging throughout the system

Last Updated: 2025-01-22

**IMPORTANT**: This platform uses HTTP polling instead of WebSockets for Railway deployment compatibility. All database tables are in the 'migration' schema, and all fields use snake_case naming convention. 