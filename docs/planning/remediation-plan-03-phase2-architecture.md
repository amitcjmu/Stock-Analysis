# Remediation Plan: Phase 2 - Architecture Standardization (Weeks 3-4)

## Overview

Phase 2 focuses on aligning the current implementation with CrewAI best practices and clean architectural patterns. This phase transforms the existing pseudo-agent system into true CrewAI agents while maintaining all existing functionality.

## Week 3: CrewAI Agent and Flow Refactoring

### Day 11-12: Convert to True CrewAI Agents

#### Current Issues
```python
# Current: Pseudo-agents that don't use CrewAI patterns
class BaseDiscoveryAgent(ABC):
    def __init__(self, agent_name: str, agent_id: str = None):
        self.agent_name = agent_name
        self.agent_id = agent_id or f"{agent_name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        # Manual initialization, no CrewAI integration
        
    async def execute(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> AgentResult:
        # Direct execution, not leveraging CrewAI framework
```

#### Remediation Steps

**Step 1: Create Agent Registry System**
```python
# backend/app/agents/__init__.py - Auto-discovery agent registry
from typing import Dict, Type, List
import importlib
import pkgutil
from crewai import Agent

class AgentRegistry:
    """Centralized registry for all agents"""
    
    def __init__(self):
        self._agents: Dict[str, Type[Agent]] = {}
        self._discover_agents()
    
    def _discover_agents(self):
        """Auto-discover all agent classes"""
        # Import all modules in agents package
        for importer, modname, ispkg in pkgutil.iter_modules(__path__):
            module = importlib.import_module(f"{__name__}.{modname}")
            
            # Find Agent classes
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, Agent) and 
                    obj is not Agent):
                    # Register agent by name
                    agent_name = getattr(obj, 'agent_name', name.lower().replace('agent', ''))
                    self._agents[agent_name] = obj
    
    def get_agent(self, name: str) -> Type[Agent]:
        """Get agent class by name"""
        if name not in self._agents:
            raise ValueError(f"Agent '{name}' not found. Available: {list(self._agents.keys())}")
        return self._agents[name]
    
    def list_agents(self) -> List[str]:
        """List all available agent names"""
        return list(self._agents.keys())

# Global registry instance
agent_registry = AgentRegistry()
```

**Step 2: Refactor Data Import Validation Agent**
```python
# backend/app/agents/data_validation.py - True CrewAI agent
from crewai import Agent, Task, LLM
from app.tools.data_validation import PiiScannerTool, FormatValidatorTool, SecurityScannerTool
from app.core.config import settings

class DataImportValidationAgent(Agent):
    """Agent specialized in data import validation and security scanning"""
    
    agent_name = "data_validation"
    
    def __init__(self, **kwargs):
        super().__init__(
            role="Data Quality and Security Specialist",
            goal="Ensure imported data meets quality and security standards",
            backstory="""You are an expert data analyst with 10+ years of experience in 
            enterprise data migration. You specialize in identifying data quality issues, 
            PII detection, and security vulnerabilities in imported datasets.""",
            
            tools=[
                PiiScannerTool(),
                FormatValidatorTool(), 
                SecurityScannerTool()
            ],
            
            llm=LLM(
                model=settings.CREWAI_MODEL,
                api_key=settings.DEEPINFRA_API_KEY
            ),
            
            verbose=True,
            memory=True,
            
            **kwargs
        )
    
    def create_validation_task(self, data_context: dict) -> Task:
        """Create specific validation task for this agent"""
        return Task(
            description=f"""
            Analyze the imported data and perform comprehensive validation:
            
            1. Data Quality Assessment:
               - Check for missing required fields
               - Validate data formats and types
               - Identify inconsistencies and anomalies
               
            2. Security Scanning:
               - Scan for PII and sensitive information
               - Check for potential security vulnerabilities
               - Validate against compliance requirements
               
            3. Recommendations:
               - Provide specific remediation steps
               - Suggest data cleansing actions
               - Recommend security measures
            
            Data Context: {data_context}
            
            Provide results in structured JSON format with:
            - validation_status: "passed" | "failed" | "warning"
            - issues_found: list of issues with severity levels
            - recommendations: actionable remediation steps
            - security_score: 0-100 security assessment score
            """,
            
            agent=self,
            expected_output="Structured JSON validation report"
        )

# Remove old BaseDiscoveryAgent and DataImportValidationAgent classes
```

**Step 3: Refactor Application Discovery Agent**
```python
# backend/app/agents/application_discovery.py
from crewai import Agent, Task, LLM
from app.tools.application_analysis import AppDependencyTool, TechStackTool, ConfigAnalysisTool

class ApplicationDiscoveryAgent(Agent):
    """Agent specialized in application discovery and dependency mapping"""
    
    agent_name = "application_discovery"
    
    def __init__(self, **kwargs):
        super().__init__(
            role="Application Architecture Analyst",
            goal="Discover and map application architectures, dependencies, and technical stacks",
            backstory="""You are a senior application architect with expertise in 
            enterprise application discovery. You excel at identifying application 
            dependencies, technology stacks, and architectural patterns.""",
            
            tools=[
                AppDependencyTool(),
                TechStackTool(),
                ConfigAnalysisTool()
            ],
            
            llm=LLM(
                model=settings.CREWAI_MODEL,
                api_key=settings.DEEPINFRA_API_KEY
            ),
            
            verbose=True,
            memory=True,
            
            **kwargs
        )
    
    def create_discovery_task(self, asset_data: dict) -> Task:
        """Create application discovery task"""
        return Task(
            description=f"""
            Analyze the application data and perform comprehensive discovery:
            
            1. Application Mapping:
               - Identify application components and services
               - Map inter-application dependencies
               - Discover communication patterns
               
            2. Technology Stack Analysis:
               - Identify programming languages and frameworks
               - Discover databases and middleware
               - Map infrastructure dependencies
               
            3. Architecture Assessment:
               - Analyze architectural patterns
               - Identify potential migration challenges
               - Assess cloud readiness
            
            Asset Data: {asset_data}
            
            Provide structured analysis with dependency graphs and migration recommendations.
            """,
            
            agent=self,
            expected_output="Comprehensive application discovery report with dependency mapping"
        )
```

**Step 4: Create Tool Framework**
```python
# backend/app/tools/base.py - Base tool framework
from crewai_tools import BaseTool
from typing import Any, Dict, Optional
from app.core.context import get_current_context

class ContextAwareTool(BaseTool):
    """Base tool that automatically includes tenant context"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._context_cache = None
    
    def get_context(self):
        """Get current request context"""
        if not self._context_cache:
            self._context_cache = get_current_context()
        return self._context_cache
    
    def _run(self, *args, **kwargs):
        """Run tool with automatic context injection"""
        context = self.get_context()
        if context:
            kwargs['client_account_id'] = context.client_account_id
            kwargs['engagement_id'] = context.engagement_id
        
        return self._execute(*args, **kwargs)
    
    def _execute(self, *args, **kwargs):
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement _execute method")
```

**Step 5: Implement Specific Tools**
```python
# backend/app/tools/data_validation.py - Validation tools
from app.tools.base import ContextAwareTool
from typing import Dict, List, Any
import re

class PiiScannerTool(ContextAwareTool):
    name: str = "pii_scanner"
    description: str = "Scans data for personally identifiable information (PII)"
    
    def _execute(self, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Scan data for PII patterns"""
        pii_patterns = {
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
        
        found_pii = []
        
        # Recursively scan data structure
        def scan_value(value, path=""):
            if isinstance(value, str):
                for pii_type, pattern in pii_patterns.items():
                    matches = re.findall(pattern, value)
                    if matches:
                        found_pii.append({
                            'type': pii_type,
                            'path': path,
                            'matches_count': len(matches),
                            'sample': matches[0][:4] + "****" if matches else None
                        })
            elif isinstance(value, dict):
                for k, v in value.items():
                    scan_value(v, f"{path}.{k}" if path else k)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    scan_value(item, f"{path}[{i}]" if path else f"[{i}]")
        
        scan_value(data)
        
        return {
            'pii_found': len(found_pii) > 0,
            'pii_count': len(found_pii),
            'pii_details': found_pii,
            'risk_level': 'high' if len(found_pii) > 10 else 'medium' if len(found_pii) > 0 else 'low'
        }

class FormatValidatorTool(ContextAwareTool):
    name: str = "format_validator"
    description: str = "Validates data formats and types"
    
    def _execute(self, data: Dict[str, Any], schema: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """Validate data against expected formats"""
        validation_errors = []
        
        def validate_field(value, field_name, expected_type=None):
            if expected_type:
                if expected_type == 'email' and not re.match(r'^[^@]+@[^@]+\.[^@]+$', str(value)):
                    validation_errors.append(f"Invalid email format in {field_name}: {value}")
                elif expected_type == 'date' and not self._is_valid_date(str(value)):
                    validation_errors.append(f"Invalid date format in {field_name}: {value}")
                elif expected_type == 'number' and not str(value).replace('.', '').isdigit():
                    validation_errors.append(f"Invalid number format in {field_name}: {value}")
        
        # Generic validation if no schema provided
        if not schema:
            schema = self._infer_schema(data)
        
        # Validate against schema
        self._validate_recursive(data, schema, "", validation_errors)
        
        return {
            'valid': len(validation_errors) == 0,
            'error_count': len(validation_errors),
            'errors': validation_errors,
            'schema_used': schema
        }
    
    def _infer_schema(self, data):
        """Infer basic schema from data"""
        # Implementation for schema inference
        return {}
    
    def _validate_recursive(self, data, schema, path, errors):
        """Recursively validate data structure"""
        # Implementation for recursive validation
        pass
```

### Day 13-14: Implement Proper CrewAI Flows

#### Current Issues
```python
# Current: Manual agent orchestration in monolithic flow
# No @start/@listen decorators
# Complex phase management without CrewAI flow control
```

#### Remediation Steps

**Step 1: Refactor to CrewAI Flow Pattern**
```python
# backend/app/flows/discovery_flow.py - True CrewAI flow
from crewai import Flow, Crew, Process
from crewai.flow.flow import listen, start
from app.agents import agent_registry
from app.models.flow_state import DiscoveryFlowState
from app.services.state_manager import StateManager

class DiscoveryFlow(Flow[DiscoveryFlowState]):
    """Main discovery flow using proper CrewAI patterns"""
    
    def __init__(self, context, **kwargs):
        super().__init__()
        self.context = context
        self.state_manager = StateManager()
        self.flow_id = kwargs.get('flow_id', str(uuid.uuid4()))
        
        # Initialize state
        if not hasattr(self, 'state') or self.state is None:
            # Try to load existing state
            existing_state = self.state_manager.load_state(self.flow_id)
            if existing_state:
                self.state = DiscoveryFlowState(**existing_state)
            else:
                self.state = DiscoveryFlowState(
                    flow_id=self.flow_id,
                    client_account_id=context.client_account_id,
                    status="initialized"
                )
    
    @start()
    def initialize_discovery(self):
        """Initialize the discovery process"""
        logger.info(f"🚀 Starting discovery flow {self.state.flow_id}")
        
        self.state.status = "running"
        self.state.current_phase = "initialization"
        self.state.started_at = datetime.utcnow()
        
        # Persist state change
        asyncio.create_task(self._persist_state())
        
        return "initialized"
    
    @listen(initialize_discovery)
    def validate_data(self, result):
        """Validate imported data"""
        logger.info(f"📊 Starting data validation for flow {self.state.flow_id}")
        
        # Create validation crew
        validation_agent = agent_registry.get_agent("data_validation")()
        
        crew = Crew(
            agents=[validation_agent],
            tasks=[validation_agent.create_validation_task(self.state.import_data)],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute validation
        result = crew.kickoff()
        
        # Update state with validation results
        self.state.current_phase = "data_validation"
        self.state.validation_results = result
        
        # Check if validation passed
        if result.get('validation_status') == 'failed':
            self.state.status = "failed"
            self.state.error_message = "Data validation failed"
            asyncio.create_task(self._persist_state())
            return "validation_failed"
        
        asyncio.create_task(self._persist_state())
        return "validated"
    
    @listen(validate_data)
    def discover_applications(self, result):
        """Discover applications and dependencies"""
        if result == "validation_failed":
            return "flow_failed"
        
        logger.info(f"🔍 Starting application discovery for flow {self.state.flow_id}")
        
        # Create discovery crew
        discovery_agent = agent_registry.get_agent("application_discovery")()
        
        crew = Crew(
            agents=[discovery_agent],
            tasks=[discovery_agent.create_discovery_task(self.state.import_data)],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute discovery
        result = crew.kickoff()
        
        # Update state
        self.state.current_phase = "application_discovery"
        self.state.discovery_results = result
        self.state.progress = 60
        
        asyncio.create_task(self._persist_state())
        return "discovered"
    
    @listen(discover_applications)
    def generate_insights(self, result):
        """Generate migration insights and recommendations"""
        if result == "flow_failed":
            return "flow_failed"
        
        logger.info(f"💡 Generating insights for flow {self.state.flow_id}")
        
        # Create insight generation crew with multiple agents
        strategy_agent = agent_registry.get_agent("migration_strategy")()
        risk_agent = agent_registry.get_agent("risk_assessment")()
        
        crew = Crew(
            agents=[strategy_agent, risk_agent],
            tasks=[
                strategy_agent.create_strategy_task(self.state.discovery_results),
                risk_agent.create_risk_assessment_task(self.state.discovery_results)
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute insight generation
        result = crew.kickoff()
        
        # Finalize state
        self.state.current_phase = "completed"
        self.state.status = "completed"
        self.state.insights = result
        self.state.progress = 100
        self.state.completed_at = datetime.utcnow()
        
        asyncio.create_task(self._persist_state())
        return "completed"
    
    async def _persist_state(self):
        """Persist current state"""
        await self.state_manager.save_state(
            self.state.flow_id,
            self.state.dict()
        )
        
        # Emit state change event for real-time updates
        from app.services.websocket_manager import websocket_manager
        await websocket_manager.broadcast_flow_update(
            self.state.flow_id,
            {
                "type": "state_update",
                "flow_id": self.state.flow_id,
                "status": self.state.status,
                "phase": self.state.current_phase,
                "progress": self.state.progress
            }
        )
```

**Step 2: Update Flow Service**
```python
# backend/app/services/discovery_flow_service.py - Updated service
from app.flows.discovery_flow import DiscoveryFlow
from app.core.context import get_current_context

class DiscoveryFlowService:
    """Service for managing discovery flows"""
    
    def __init__(self, context=None):
        self.context = context or get_current_context()
        self.state_manager = StateManager()
    
    async def create_flow(self, flow_data: dict) -> DiscoveryFlow:
        """Create new discovery flow"""
        # Create flow instance
        flow = DiscoveryFlow(
            context=self.context,
            flow_id=str(uuid.uuid4())
        )
        
        # Set initial data
        flow.state.name = flow_data.get('name', 'Unnamed Flow')
        flow.state.description = flow_data.get('description', '')
        flow.state.import_data = flow_data.get('data', {})
        
        # Persist initial state
        await flow._persist_state()
        
        return flow
    
    async def get_flow(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get existing flow by ID"""
        # Load state
        state_data = await self.state_manager.load_state(flow_id)
        if not state_data:
            return None
        
        # Create flow instance with existing state
        flow = DiscoveryFlow(
            context=self.context,
            flow_id=flow_id
        )
        
        return flow
    
    async def continue_flow(self, flow_id: str, continuation_data: dict = None):
        """Continue flow execution"""
        flow = await self.get_flow(flow_id)
        if not flow:
            raise ValueError(f"Flow {flow_id} not found")
        
        # Update flow with any new data
        if continuation_data:
            flow.state.import_data.update(continuation_data)
        
        # Continue execution based on current phase
        if flow.state.current_phase == "initialization":
            return flow.validate_data("initialized")
        elif flow.state.current_phase == "data_validation":
            return flow.discover_applications("validated")
        elif flow.state.current_phase == "application_discovery":
            return flow.generate_insights("discovered")
        else:
            raise ValueError(f"Cannot continue flow in phase: {flow.state.current_phase}")
```

## Week 4: Context Management and Tool Framework

### Day 15-16: Standardize Multi-Tenant Context Management

#### Current Issues
```python
# Manual context propagation through constructors
class DiscoveryFlowService:
    def __init__(self, db: Session, context: RequestContext):
        self.context = context  # Manual propagation
```

#### Remediation Steps

**Step 1: Context Injection Framework**
```python
# backend/app/core/context.py - Enhanced context management
from contextvars import ContextVar
from typing import Optional, Callable, Any
from functools import wraps
from app.models.context import RequestContext

# Context variables
_current_context: ContextVar[Optional[RequestContext]] = ContextVar('current_context', default=None)

def get_current_context() -> Optional[RequestContext]:
    """Get current request context"""
    return _current_context.get()

def set_current_context(context: RequestContext):
    """Set current request context"""
    _current_context.set(context)

def inject_context(func: Callable) -> Callable:
    """Decorator to automatically inject context into service methods"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # If first arg is a class instance, inject context
        if args and hasattr(args[0], '__class__'):
            instance = args[0]
            if not hasattr(instance, 'context') or instance.context is None:
                instance.context = get_current_context()
        return func(*args, **kwargs)
    return wrapper

def require_context(func: Callable) -> Callable:
    """Decorator to ensure context is available"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        context = get_current_context()
        if not context:
            raise ValueError("No request context available")
        return func(*args, **kwargs)
    return wrapper

class ContextAwareService:
    """Base class for services that need context"""
    
    def __init__(self, context: RequestContext = None):
        self.context = context or get_current_context()
        if not self.context:
            raise ValueError("Context required for service initialization")
```

**Step 2: Update Services with Context Injection**
```python
# backend/app/services/discovery_flow_service.py - Context-aware service
from app.core.context import ContextAwareService, inject_context, require_context

class DiscoveryFlowService(ContextAwareService):
    """Discovery flow service with automatic context injection"""
    
    @inject_context
    @require_context
    async def create_flow(self, flow_data: dict) -> DiscoveryFlow:
        """Create flow with automatic context injection"""
        flow = DiscoveryFlow(
            context=self.context,  # Context automatically available
            flow_id=str(uuid.uuid4())
        )
        
        # Context is automatically used for tenant isolation
        flow.state.client_account_id = self.context.client_account_id
        flow.state.engagement_id = self.context.engagement_id
        
        await flow._persist_state()
        return flow
    
    @inject_context
    @require_context 
    async def get_flow(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """Get flow with tenant isolation"""
        # Context automatically ensures tenant isolation
        state_data = await self.state_manager.load_state(flow_id)
        
        # Verify tenant access
        if state_data and state_data.get('client_account_id') != self.context.client_account_id:
            logger.warning(f"Attempted cross-tenant access: flow {flow_id}")
            return None
        
        if not state_data:
            return None
        
        flow = DiscoveryFlow(context=self.context, flow_id=flow_id)
        return flow
```

**Step 3: Database-Level Tenant Isolation**
```sql
-- Add row-level security policies
-- backend/sql/tenant_isolation.sql

-- Enable RLS on all tenant-scoped tables
ALTER TABLE workflow_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE learned_patterns ENABLE ROW LEVEL SECURITY;

-- Create policies for tenant isolation
CREATE POLICY tenant_workflow_isolation ON workflow_states
    USING (client_account_id = current_setting('app.client_account_id')::uuid);

CREATE POLICY tenant_insights_isolation ON agent_insights
    USING (client_account_id = current_setting('app.client_account_id')::uuid);

CREATE POLICY tenant_patterns_isolation ON learned_patterns
    USING (client_account_id = current_setting('app.client_account_id')::uuid);

-- Function to set tenant context for session
CREATE OR REPLACE FUNCTION set_tenant_context(tenant_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.client_account_id', tenant_id::text, true);
END;
$$ LANGUAGE plpgsql;
```

**Step 4: Context Middleware Enhancement**
```python
# backend/app/middleware/tenant.py - Enhanced tenant middleware
from app.core.context import set_current_context, RequestContext
from app.core.database import AsyncSessionLocal

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant information
        client_account_id = request.headers.get("X-Client-Account-ID")
        engagement_id = request.headers.get("X-Engagement-ID")
        user_id = request.headers.get("X-User-ID")
        
        if client_account_id:
            try:
                # Validate and create context
                context = RequestContext(
                    client_account_id=UUID(client_account_id),
                    engagement_id=UUID(engagement_id) if engagement_id else None,
                    user_id=UUID(user_id) if user_id else None
                )
                
                # Set context for this request
                set_current_context(context)
                
                # Set database session context for RLS
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        text("SELECT set_tenant_context(:tenant_id)"),
                        {"tenant_id": context.client_account_id}
                    )
                
                response = await call_next(request)
                return response
                
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid tenant context: {e}")
        else:
            # Allow requests without tenant context for health checks, etc.
            return await call_next(request)
```

### Day 17-18: Unified Tool Framework

#### Current Issues
```python
# Tools defined but not properly integrated with CrewAI
# Manual tool execution instead of agent-driven
```

#### Remediation Steps

**Step 1: Tool Registry System**
```python
# backend/app/tools/__init__.py - Tool auto-discovery
from typing import Dict, Type, List
import importlib
import pkgutil
from crewai_tools import BaseTool

class ToolRegistry:
    """Centralized registry for all tools"""
    
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._tool_instances: Dict[str, BaseTool] = {}
        self._discover_tools()
    
    def _discover_tools(self):
        """Auto-discover all tool classes"""
        # Import all modules in tools package
        for importer, modname, ispkg in pkgutil.iter_modules(__path__):
            if modname.startswith('_'):  # Skip private modules
                continue
                
            module = importlib.import_module(f"{__name__}.{modname}")
            
            # Find Tool classes
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and 
                    issubclass(obj, BaseTool) and 
                    obj is not BaseTool and
                    hasattr(obj, 'name')):
                    
                    # Register tool by name
                    tool_name = obj.name
                    self._tools[tool_name] = obj
                    # Create instance for immediate use
                    self._tool_instances[tool_name] = obj()
    
    def get_tool(self, name: str) -> BaseTool:
        """Get tool instance by name"""
        if name not in self._tool_instances:
            raise ValueError(f"Tool '{name}' not found. Available: {list(self._tool_instances.keys())}")
        return self._tool_instances[name]
    
    def get_tools_for_agent(self, agent_type: str) -> List[BaseTool]:
        """Get appropriate tools for specific agent type"""
        tool_mapping = {
            'data_validation': ['pii_scanner', 'format_validator', 'security_scanner'],
            'application_discovery': ['app_dependency', 'tech_stack', 'config_analysis'],
            'field_mapping': ['schema_analyzer', 'field_matcher', 'mapping_validator'],
            'migration_strategy': ['cost_calculator', 'timeline_estimator', 'risk_assessor']
        }
        
        tool_names = tool_mapping.get(agent_type, [])
        return [self.get_tool(name) for name in tool_names if name in self._tool_instances]
    
    def list_tools(self) -> List[str]:
        """List all available tool names"""
        return list(self._tool_instances.keys())

# Global registry instance
tool_registry = ToolRegistry()
```

**Step 2: Enhanced Base Tool Classes**
```python
# backend/app/tools/base.py - Enhanced base tools
from crewai_tools import BaseTool
from typing import Any, Dict, Optional, Union
from app.core.context import get_current_context, require_context
from app.core.logging import get_logger

class ContextAwareTool(BaseTool):
    """Base tool with automatic context and logging"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(f"tools.{self.name}")
    
    @require_context
    def _run(self, *args, **kwargs) -> Union[str, Dict[str, Any]]:
        """Run tool with context injection and error handling"""
        context = get_current_context()
        
        # Add context to kwargs for tenant isolation
        kwargs.update({
            'client_account_id': context.client_account_id,
            'engagement_id': context.engagement_id,
            'user_id': context.user_id
        })
        
        try:
            self.logger.info(f"Executing tool {self.name} with args: {args}")
            result = self._execute(*args, **kwargs)
            self.logger.info(f"Tool {self.name} completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Tool {self.name} failed: {e}")
            return {
                'error': True,
                'message': str(e),
                'tool': self.name
            }
    
    def _execute(self, *args, **kwargs) -> Union[str, Dict[str, Any]]:
        """Override this method in subclasses"""
        raise NotImplementedError("Subclasses must implement _execute method")

class DatabaseTool(ContextAwareTool):
    """Base tool for database operations with tenant isolation"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from app.core.database import AsyncSessionLocal
        self.session_factory = AsyncSessionLocal
    
    async def get_tenant_session(self):
        """Get database session with tenant context set"""
        context = get_current_context()
        session = self.session_factory()
        
        # Set tenant context for RLS
        await session.execute(
            text("SELECT set_tenant_context(:tenant_id)"),
            {"tenant_id": context.client_account_id}
        )
        
        return session
```

**Step 3: Implement Specific Tool Categories**
```python
# backend/app/tools/database_tools.py - Database analysis tools
from app.tools.base import DatabaseTool
from sqlalchemy import text
from typing import Dict, Any, List

class SchemaAnalyzerTool(DatabaseTool):
    name: str = "schema_analyzer"
    description: str = "Analyzes database schemas and table structures"
    
    def _execute(self, table_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Analyze database schema from imported data"""
        
        schema_analysis = {
            'tables': [],
            'relationships': [],
            'data_types': {},
            'constraints': [],
            'recommendations': []
        }
        
        # Analyze table structure
        for table_name, records in table_data.items():
            if not records:
                continue
                
            # Analyze first few records to infer schema
            sample_record = records[0] if records else {}
            
            table_info = {
                'name': table_name,
                'record_count': len(records),
                'columns': []
            }
            
            # Analyze each column
            for column_name, value in sample_record.items():
                column_info = {
                    'name': column_name,
                    'inferred_type': self._infer_type(value),
                    'nullable': self._check_nullable(records, column_name),
                    'unique_values': self._count_unique_values(records, column_name)
                }
                table_info['columns'].append(column_info)
            
            schema_analysis['tables'].append(table_info)
        
        # Generate recommendations
        schema_analysis['recommendations'] = self._generate_schema_recommendations(schema_analysis)
        
        return schema_analysis
    
    def _infer_type(self, value) -> str:
        """Infer data type from sample value"""
        if isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'decimal'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, str):
            if '@' in value:
                return 'email'
            elif len(value) == 36 and '-' in value:
                return 'uuid'
            else:
                return 'text'
        else:
            return 'unknown'

class FieldMatcherTool(DatabaseTool):
    name: str = "field_matcher"
    description: str = "Matches fields between source and target schemas"
    
    def _execute(self, source_schema: Dict, target_schema: Dict, **kwargs) -> Dict[str, Any]:
        """Match fields between schemas using similarity algorithms"""
        
        matches = []
        confidence_threshold = 0.7
        
        for source_table in source_schema.get('tables', []):
            for source_column in source_table.get('columns', []):
                
                best_match = None
                best_score = 0
                
                # Find best match in target schema
                for target_table in target_schema.get('tables', []):
                    for target_column in target_table.get('columns', []):
                        
                        # Calculate similarity score
                        score = self._calculate_similarity(
                            source_column, target_column
                        )
                        
                        if score > best_score and score >= confidence_threshold:
                            best_score = score
                            best_match = {
                                'target_table': target_table['name'],
                                'target_column': target_column['name'],
                                'confidence': score
                            }
                
                if best_match:
                    matches.append({
                        'source_table': source_table['name'],
                        'source_column': source_column['name'],
                        'target_table': best_match['target_table'],
                        'target_column': best_match['target_column'],
                        'confidence': best_match['confidence'],
                        'transformation_needed': self._needs_transformation(
                            source_column, best_match
                        )
                    })
        
        return {
            'field_matches': matches,
            'match_rate': len(matches) / max(1, self._count_total_fields(source_schema)),
            'high_confidence_matches': [m for m in matches if m['confidence'] > 0.9],
            'recommendations': self._generate_mapping_recommendations(matches)
        }
    
    def _calculate_similarity(self, source_col: Dict, target_col: Dict) -> float:
        """Calculate similarity between two columns"""
        # Implement fuzzy string matching, type compatibility, etc.
        name_similarity = self._string_similarity(
            source_col['name'], target_col['name']
        )
        type_compatibility = self._type_compatibility(
            source_col.get('inferred_type'), target_col.get('inferred_type')
        )
        
        # Weighted average
        return (name_similarity * 0.6) + (type_compatibility * 0.4)
```

### Day 19-20: Agent Integration and Testing

#### Remediation Steps

**Step 1: Update Agent Creation with Tools**
```python
# backend/app/agents/data_validation.py - Updated with tool integration
from app.tools import tool_registry

class DataImportValidationAgent(Agent):
    def __init__(self, **kwargs):
        # Get appropriate tools for this agent
        agent_tools = tool_registry.get_tools_for_agent('data_validation')
        
        super().__init__(
            role="Data Quality and Security Specialist",
            goal="Ensure imported data meets quality and security standards",
            backstory="""You are an expert data analyst...""",
            
            tools=agent_tools,  # Tools automatically assigned
            
            llm=LLM(
                model=settings.CREWAI_MODEL,
                api_key=settings.DEEPINFRA_API_KEY
            ),
            
            verbose=True,
            memory=True,
            **kwargs
        )
    
    def create_validation_task(self, data_context: dict) -> Task:
        return Task(
            description=f"""
            Use your tools to analyze the imported data:
            
            1. Use the pii_scanner tool to identify sensitive information
            2. Use the format_validator tool to check data formats
            3. Use the security_scanner tool to assess security risks
            
            Data to analyze: {data_context}
            
            Provide comprehensive validation report with specific findings and recommendations.
            """,
            
            agent=self,
            expected_output="Detailed validation report with tool findings"
        )
```

**Step 2: Integration Testing**
```python
# backend/tests/test_agent_integration.py - Test agent-tool integration
import pytest
from app.agents import agent_registry
from app.tools import tool_registry

@pytest.mark.asyncio
class TestAgentToolIntegration:
    
    async def test_agent_tool_assignment(self):
        """Test that agents receive appropriate tools"""
        validation_agent = agent_registry.get_agent("data_validation")()
        
        # Check that agent has expected tools
        tool_names = [tool.name for tool in validation_agent.tools]
        expected_tools = ['pii_scanner', 'format_validator', 'security_scanner']
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Missing tool: {expected_tool}"
    
    async def test_tool_execution_with_context(self, test_context):
        """Test tool execution with proper context"""
        pii_scanner = tool_registry.get_tool('pii_scanner')
        
        test_data = {
            'users': [
                {'name': 'John Doe', 'email': 'john@example.com', 'ssn': '123-45-6789'},
                {'name': 'Jane Smith', 'email': 'jane@example.com', 'ssn': '987-65-4321'}
            ]
        }
        
        result = pii_scanner._run(test_data)
        
        assert result['pii_found'] is True
        assert result['pii_count'] > 0
        assert any(pii['type'] == 'ssn' for pii in result['pii_details'])
        assert any(pii['type'] == 'email' for pii in result['pii_details'])
    
    async def test_flow_with_agent_tools(self, test_context):
        """Test complete flow execution with agent tools"""
        from app.flows.discovery_flow import DiscoveryFlow
        
        flow = DiscoveryFlow(context=test_context)
        flow.state.import_data = {
            'applications': [
                {'name': 'WebApp1', 'type': 'web', 'language': 'Java'},
                {'name': 'Database1', 'type': 'database', 'engine': 'PostgreSQL'}
            ]
        }
        
        # Execute validation phase
        result = flow.validate_data("initialized")
        
        assert result == "validated"
        assert flow.state.validation_results is not None
        assert 'validation_status' in flow.state.validation_results
```

## Phase 2 Deliverables

### Code Changes
1. **True CrewAI Agents**: All agents converted to proper CrewAI Agent classes with tools
2. **Proper Flow Implementation**: CrewAI Flow with @start/@listen decorators
3. **Context Injection**: Automatic tenant context injection throughout the system
4. **Tool Framework**: Unified tool registry with automatic discovery and assignment
5. **Database RLS**: Row-level security for multi-tenant isolation

### Testing
1. **Agent Tests**: Unit tests for all agent implementations
2. **Flow Tests**: Integration tests for CrewAI flow execution
3. **Tool Tests**: Tests for tool functionality and context injection
4. **Context Tests**: Tests for multi-tenant isolation

### Quality Gates
- [ ] All agents inherit from CrewAI Agent class and use proper tools
- [ ] Flows use @start/@listen decorators and execute properly
- [ ] Context injection works automatically across all services
- [ ] Tool registry discovers and assigns tools correctly
- [ ] Database RLS enforces tenant isolation
- [ ] All tests pass with >85% coverage

## Risk Mitigation

### Backwards Compatibility
- Keep old agent classes temporarily with deprecation warnings
- Maintain API compatibility during transition
- Feature flags to switch between old/new implementations

### Performance Monitoring
- Monitor CrewAI agent execution times
- Track tool execution performance
- Watch for any database performance impacts from RLS

This completes Phase 2 architecture standardization, bringing the codebase in line with CrewAI best practices while maintaining all existing functionality.