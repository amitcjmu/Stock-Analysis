# Backend Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [FastAPI Application Structure](#fastapi-application-structure)
3. [Core Services](#core-services)
4. [AI Agent System](#ai-agent-system)
5. [Database Layer](#database-layer)
6. [API Endpoints](#api-endpoints)
7. [WebSocket Implementation](#websocket-implementation)
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
- **WebSocket Manager**: Real-time communication
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
│           └── monitoring.py   # Agent monitoring
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
└── websocket/            # WebSocket handlers
    └── manager.py        # WebSocket connection management
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

### 1. CrewAI Service (`crewai_service.py`)

The main orchestrator for AI-powered analysis and learning.

```python
class CrewAIService:
    """Service for managing truly agentic CrewAI agents with memory and learning."""
    
    def __init__(self):
        self.llm = None
        self.memory = AgentMemory()
        self.agent_manager = None
        self.analyzer = IntelligentAnalyzer(self.memory)
        self.feedback_processor = FeedbackProcessor(self.memory)
        
        # Initialize LLM and agents if available
        if CREWAI_AVAILABLE and settings.DEEPINFRA_API_KEY:
            self._initialize_llm()
            self.agent_manager = AgentManager(self.llm)
    
    async def analyze_cmdb_data(self, cmdb_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze CMDB data using AI agents."""
        # Implementation details...
    
    async def process_user_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process user feedback for continuous learning."""
        # Implementation details...
```

**Key Features:**
- **LLM Integration**: Uses DeepInfra's Llama 4 Maverick model
- **Agent Management**: Creates and manages specialized AI agents
- **Memory System**: Persistent learning across sessions
- **Fallback Logic**: Graceful degradation when AI is unavailable

### 2. Agent Manager (`agents.py`)

Manages the creation and lifecycle of specialized AI agents.

```python
class AgentManager:
    """Manages creation and lifecycle of AI agents and crews."""
    
    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
        self.agents = {}
        self.crews = {}
        
        if CREWAI_AVAILABLE and self.llm:
            self._create_agents()
            self._create_crews()
    
    def _create_agents(self):
        """Create all specialized agents."""
        
        # CMDB Data Analyst Agent
        self.agents['cmdb_analyst'] = Agent(
            role='Senior CMDB Data Analyst',
            goal='Analyze CMDB data with expert precision',
            backstory="""Expert in enterprise asset management...""",
            llm=self.llm,
            memory=False  # Disable to avoid OpenAI API calls
        )
        
        # Additional agents: learning_agent, pattern_agent, etc.
```

**Agent Types:**
- **CMDB Analyst**: Analyzes infrastructure data
- **Learning Specialist**: Processes feedback for improvement
- **Pattern Recognition Expert**: Identifies data patterns
- **Migration Strategist**: Recommends 6R strategies
- **Risk Assessor**: Evaluates migration risks
- **Wave Planner**: Optimizes migration sequencing

### 3. Field Mapping System (`field_mapper.py`)

Intelligent field mapping with AI learning capabilities.

```python
class FieldMapper:
    """Intelligent field mapping with AI learning capabilities."""
    
    def __init__(self):
        self.mappings_file = Path("data/field_mappings.json")
        self.learned_mappings = self._load_learned_mappings()
        self.base_mappings = self._get_base_mappings()
    
    def find_matching_fields(self, available_columns: List[str], 
                           target_field: str) -> List[str]:
        """Find columns that match a target field."""
        # Implementation with fuzzy matching and learned patterns
    
    def learn_field_mapping(self, source_field: str, target_field: str, 
                          source: str) -> Dict[str, Any]:
        """Learn a new field mapping from user feedback or analysis."""
        # Implementation for persistent learning
```

**Key Features:**
- **Dynamic Learning**: Learns from user feedback and AI analysis
- **Fuzzy Matching**: Handles variations in field names
- **Persistent Storage**: Saves learned mappings to JSON file
- **Pattern Recognition**: Identifies common field naming patterns

### 4. Agent Monitor (`agent_monitor.py`)

Real-time monitoring of AI agent activities.

```python
class AgentMonitor:
    """Real-time monitoring of AI agent activities."""
    
    def __init__(self):
        self.active_tasks = {}
        self.task_history = []
        self.monitoring_active = False
    
    def start_task(self, task_id: str, agent_name: str, 
                   description: str) -> None:
        """Start monitoring a new task."""
        # Implementation for task tracking
    
    def complete_task(self, task_id: str, result: str) -> None:
        """Mark a task as completed."""
        # Implementation for task completion
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
        memory=False  # Disable memory to avoid OpenAI API calls
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
            memory=False  # Disable memory to avoid OpenAI API calls
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

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
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

## WebSocket Implementation

### Connection Manager

```python
# websocket/manager.py
## Pydantic V2 Implementation

### Model Configuration

Pydantic V2 introduces several improvements and changes from V1. Here's how we're using it:

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

class SessionBase(BaseModel):
    """Base model for session data."""
    session_name: str = Field(..., description="Unique identifier for the session")
    session_display_name: Optional[str] = Field(
        None, 
        description="User-friendly display name for the session"
    )
    # ... other fields ...

    model_config = {
        "from_attributes": True,  # Replaces orm_mode in Pydantic V1
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "session_name": "my-session",
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

## WebSocket Implementation

```python
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except ConnectionClosedOK:
                self.active_connections.remove(connection)
```

### WebSocket Endpoints

```python
@router.websocket("/agent-monitor")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send agent status updates
            status = agent_monitor.get_current_status()
            await websocket.send_json(status)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

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
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
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

This backend architecture provides a robust, scalable foundation for the AI Modernize Migration Platform with clear separation of concerns, comprehensive error handling, and extensive AI integration capabilities. 