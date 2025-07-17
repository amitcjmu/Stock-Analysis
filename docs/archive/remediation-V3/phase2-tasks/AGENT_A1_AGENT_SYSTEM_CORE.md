# Phase 2 - Agent A1: Agent System Core Infrastructure

## Context
You are part of Phase 2 remediation effort to transform the AI Modernize Migration Platform to proper CrewAI architecture. This is Track A (Core) focusing on building the foundational agent system infrastructure that all other agents will depend on.

### Required Reading Before Starting
- `docs/planning/PHASE-2-REMEDIATION-PLAN.md` - Phase 2 objectives
- `docs/planning/phase1-tasks/` - Understand Phase 1 completions
- `docs/development/CrewAI_Development_Guide.md` - CrewAI patterns
- Current agent implementations in `backend/app/services/agents/`

### Prerequisites from Phase 1
- Flow ID migration complete (no more session_id)
- API v3 consolidated and working
- PostgreSQL-only state management

### Phase 2 Goal
Transform pseudo-agents into proper CrewAI agents with dynamic tool usage, proper inheritance, and auto-discovery capabilities. Your work is **critical** as other agents depend on this infrastructure.

## Your Specific Tasks

### 1. Create Agent Registry System
**File to create**: `backend/app/services/agents/registry.py`

```python
"""
Central Agent Registry with auto-discovery
Manages all CrewAI agents and their capabilities
"""

import os
import importlib
import inspect
from typing import Dict, List, Type, Optional, Any
from dataclasses import dataclass
from crewai import Agent
import logging

logger = logging.getLogger(__name__)

@dataclass
class AgentMetadata:
    """Metadata for registered agents"""
    name: str
    description: str
    agent_class: Type[Agent]
    required_tools: List[str]
    capabilities: List[str]
    max_iter: int = 15
    memory: bool = True
    verbose: bool = True
    allow_delegation: bool = False

class AgentRegistry:
    """
    Central registry for all CrewAI agents with auto-discovery.
    Features:
    - Automatic agent discovery on startup
    - Dynamic agent instantiation
    - Tool assignment based on requirements
    - Capability-based agent selection
    """
    
    _instance = None
    _agents: Dict[str, AgentMetadata] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.discover_agents()
    
    def discover_agents(self) -> None:
        """Auto-discover all agents in the agents directory"""
        agents_dir = os.path.dirname(__file__)
        
        for filename in os.listdir(agents_dir):
            if filename.endswith('_agent.py') and not filename.startswith('_'):
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'.{module_name}', package='app.services.agents')
                    
                    # Find all Agent subclasses in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, Agent) and 
                            obj != Agent and
                            hasattr(obj, 'agent_metadata')):
                            
                            metadata = obj.agent_metadata()
                            self.register_agent(metadata)
                            logger.info(f"Discovered agent: {metadata.name}")
                            
                except Exception as e:
                    logger.error(f"Failed to load agent module {module_name}: {e}")
    
    def register_agent(self, metadata: AgentMetadata) -> None:
        """Register an agent with the registry"""
        self._agents[metadata.name] = metadata
    
    def get_agent(
        self, 
        name: str, 
        tools: List[Any], 
        llm: Any,
        **kwargs
    ) -> Optional[Agent]:
        """Get an instantiated agent by name"""
        if name not in self._agents:
            logger.error(f"Agent {name} not found in registry")
            return None
        
        metadata = self._agents[name]
        
        # Filter tools based on agent requirements
        agent_tools = [
            tool for tool in tools 
            if tool.__class__.__name__ in metadata.required_tools
        ]
        
        try:
            agent = metadata.agent_class(
                tools=agent_tools,
                llm=llm,
                max_iter=metadata.max_iter,
                memory=metadata.memory,
                verbose=metadata.verbose,
                allow_delegation=metadata.allow_delegation,
                **kwargs
            )
            return agent
        except Exception as e:
            logger.error(f"Failed to instantiate agent {name}: {e}")
            return None
    
    def get_agents_by_capability(self, capability: str) -> List[AgentMetadata]:
        """Get all agents with a specific capability"""
        return [
            metadata for metadata in self._agents.values()
            if capability in metadata.capabilities
        ]
    
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return list(self._agents.keys())

# Global registry instance
agent_registry = AgentRegistry()
```

### 2. Implement Base Agent Class
**File to create**: `backend/app/services/agents/base_agent.py`

```python
"""
Base CrewAI Agent implementation
All discovery agents must inherit from this class
"""

from abc import abstractmethod
from typing import List, Dict, Any, Optional
from crewai import Agent
from app.core.context import get_current_context
from app.services.agents.registry import AgentMetadata
import logging

logger = logging.getLogger(__name__)

class BaseDiscoveryAgent(Agent):
    """
    Base class for all discovery agents.
    Provides:
    - Proper CrewAI Agent inheritance
    - Context awareness for multi-tenancy
    - Standard logging and error handling
    - Metadata registration
    """
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: List[Any],
        llm: Any,
        **kwargs
    ):
        """Initialize base agent with CrewAI patterns"""
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            llm=llm,
            **kwargs
        )
        
        # Multi-tenant context
        self.context = get_current_context()
        
        # Ensure all tools are context-aware
        self._inject_context_into_tools()
    
    def _inject_context_into_tools(self) -> None:
        """Inject tenant context into all tools"""
        for tool in self.tools:
            if hasattr(tool, 'set_context'):
                tool.set_context(self.context)
    
    @classmethod
    @abstractmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Return metadata for agent registration"""
        raise NotImplementedError("Each agent must define its metadata")
    
    def execute_with_context(self, inputs: Dict[str, Any]) -> Any:
        """Execute agent task with proper context"""
        # Ensure context is available
        if not self.context:
            raise ValueError("No context available for multi-tenant execution")
        
        # Log execution start
        logger.info(
            f"Agent {self.role} executing for client {self.context.client_account_id}"
        )
        
        try:
            # Execute through CrewAI's execution method
            result = self.execute(inputs)
            logger.info(f"Agent {self.role} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Agent {self.role} failed: {e}")
            raise
```

### 3. Convert Data Validation Agent
**File to update**: `backend/app/services/agents/data_import_validation_agent.py`

```python
"""
Data Import Validation Agent - Converted to proper CrewAI pattern
"""

from typing import List, Dict, Any
from crewai import Agent
from app.services.agents.base_agent import BaseDiscoveryAgent
from app.services.agents.registry import AgentMetadata
from app.services.llm_config import get_crewai_llm

class DataImportValidationAgent(BaseDiscoveryAgent):
    """
    Validates imported data quality and structure using CrewAI patterns.
    
    Capabilities:
    - Schema validation
    - Data quality assessment
    - Missing value detection
    - Format consistency checking
    - PII detection
    """
    
    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize with proper CrewAI configuration"""
        if llm is None:
            llm = get_crewai_llm()
        
        super().__init__(
            role="Data Import Validation Specialist",
            goal="Ensure imported data meets quality standards and is ready for processing",
            backstory="""You are an expert data validator with years of experience 
            in enterprise data migration. You excel at:
            - Identifying data quality issues before they cause problems
            - Detecting patterns and anomalies in large datasets
            - Ensuring data meets schema requirements
            - Protecting sensitive information through PII detection
            
            Your validation prevents downstream failures and ensures smooth migrations.""",
            tools=tools,
            llm=llm,
            **kwargs
        )
    
    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="data_validation_agent",
            description="Validates data quality and structure for migration readiness",
            agent_class=cls,
            required_tools=[
                "SchemaValidatorTool",
                "DataQualityAnalyzerTool",
                "PIIScannerTool",
                "FormatValidatorTool"
            ],
            capabilities=[
                "data_validation",
                "schema_validation",
                "quality_assessment",
                "pii_detection"
            ],
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False
        )
```

### 4. Create Agent Factory
**File to create**: `backend/app/services/agents/factory.py`

```python
"""
Agent Factory for dynamic agent creation
"""

from typing import List, Dict, Any, Optional
from app.services.agents.registry import agent_registry
from app.services.tools.registry import tool_registry
from app.services.llm_config import get_crewai_llm
import logging

logger = logging.getLogger(__name__)

class AgentFactory:
    """
    Factory for creating CrewAI agents with proper configuration.
    Handles:
    - Dynamic agent instantiation
    - Tool assignment based on requirements
    - LLM configuration
    - Context injection
    """
    
    def __init__(self):
        self.llm = get_crewai_llm()
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry
    
    def create_agent(
        self, 
        agent_name: str,
        additional_tools: Optional[List[Any]] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        Create an agent instance with required tools.
        
        Args:
            agent_name: Name of the agent to create
            additional_tools: Extra tools beyond required ones
            **kwargs: Additional agent configuration
        
        Returns:
            Instantiated agent or None if creation fails
        """
        # Get agent metadata
        agent_metadata = self.agent_registry._agents.get(agent_name)
        if not agent_metadata:
            logger.error(f"Agent {agent_name} not found in registry")
            return None
        
        # Gather required tools
        tools = []
        for tool_name in agent_metadata.required_tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                tools.append(tool)
            else:
                logger.warning(f"Required tool {tool_name} not found for agent {agent_name}")
        
        # Add any additional tools
        if additional_tools:
            tools.extend(additional_tools)
        
        # Create agent instance
        try:
            agent = self.agent_registry.get_agent(
                name=agent_name,
                tools=tools,
                llm=self.llm,
                **kwargs
            )
            
            logger.info(f"Successfully created agent: {agent_name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_name}: {e}")
            return None
    
    def create_validation_crew(self) -> List[Any]:
        """Create all agents needed for data validation"""
        return [
            self.create_agent("data_validation_agent"),
            self.create_agent("schema_analyzer_agent")
        ]
    
    def create_mapping_crew(self) -> List[Any]:
        """Create all agents needed for field mapping"""
        return [
            self.create_agent("field_mapping_agent"),
            self.create_agent("semantic_matcher_agent")
        ]
    
    def create_discovery_crew(self) -> List[Any]:
        """Create all agents needed for full discovery"""
        agents = []
        
        # Create agents in dependency order
        agent_names = [
            "data_validation_agent",
            "field_mapping_agent",
            "data_cleansing_agent",
            "asset_inventory_agent",
            "dependency_analysis_agent",
            "tech_debt_agent"
        ]
        
        for agent_name in agent_names:
            agent = self.create_agent(agent_name)
            if agent:
                agents.append(agent)
            else:
                logger.error(f"Failed to create required agent: {agent_name}")
        
        return agents

# Global factory instance
agent_factory = AgentFactory()
```

### 5. Update Other Core Agents
Convert these agents to proper CrewAI pattern:
- `field_mapping_agent.py`
- `data_cleansing_agent.py` 
- `asset_inventory_agent.py`

Each should:
1. Inherit from `BaseDiscoveryAgent`
2. Define proper `agent_metadata()`
3. Use CrewAI initialization pattern
4. Specify required tools

## Success Criteria
- [ ] Agent registry auto-discovers all agents on startup
- [ ] Base agent class provides proper CrewAI inheritance
- [ ] All core agents converted to new pattern
- [ ] Agent factory creates agents with correct tools
- [ ] Context injection works for multi-tenancy
- [ ] No regressions in agent functionality
- [ ] Tests pass for all agent operations

## Interfaces with Other Agents
- **Agent A2** will use your registry to implement crews
- **Agent B1** will integrate agents into flows
- **Agent C1** uses your base classes for context
- **Agent D1** depends on your tool integration

## Implementation Guidelines

### 1. Agent Conversion Pattern
```python
# Old pattern
class OldAgent:
    async def execute(self, data):
        # Manual execution

# New pattern  
class NewAgent(BaseDiscoveryAgent):
    def __init__(self, tools, llm=None, **kwargs):
        super().__init__(
            role="...",
            goal="...",
            backstory="...",
            tools=tools,
            llm=llm or get_crewai_llm(),
            **kwargs
        )
```

### 2. Metadata Definition
Every agent must define:
- Unique name
- Required tools list
- Capabilities list
- Execution parameters

### 3. Testing Approach
- Unit test each agent independently
- Test registry auto-discovery
- Test factory creation
- Integration test with tools

## Commands to Run
```bash
# Test agent discovery
docker exec -it migration_backend python -c "from app.services.agents.registry import agent_registry; print(agent_registry.list_agents())"

# Test agent creation
docker exec -it migration_backend python -m pytest tests/agents/test_agent_factory.py -v

# Verify no import errors
docker exec -it migration_backend python -m py_compile app/services/agents/*.py
```

## Definition of Done
- [ ] Agent registry implemented with auto-discovery
- [ ] Base agent class with CrewAI inheritance
- [ ] All core agents converted to new pattern
- [ ] Agent factory creates crews successfully
- [ ] Context injection verified for all agents
- [ ] Unit tests >90% coverage
- [ ] Integration tests passing
- [ ] PR created with title: "feat: [Phase2-A1] Agent system core infrastructure"
- [ ] No regressions in existing functionality

## Notes
- Start with registry and base class
- Convert one agent at a time
- Test thoroughly after each conversion
- Maintain backward compatibility temporarily
- Focus on core agents first