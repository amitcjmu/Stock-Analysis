# Implementation Plan: Part 4 - Phase 2: CrewAI Implementation (Weeks 3-4)

## Overview
Phase 2 focuses on implementing the core CrewAI flow architecture, agent framework, and crew management system that forms the heart of the platform's AI-driven automation.

## Week 3: CrewAI Flow Framework

### Day 11-12: Flow Architecture Implementation

#### Base Flow Framework
```python
# backend/app/flows/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from crewai import Flow
from crewai.flow.flow import listen, start
from crewai.flow.persistence import persist
from pydantic import BaseModel
from app.core.context import get_current_tenant
from app.services.state_manager import StateManager
from app.services.event_bus import EventBus
import logging

StateType = TypeVar("StateType", bound=BaseModel)

@persist()
class BaseFlow(Flow[StateType], ABC, Generic[StateType]):
    """Base class for all platform flows with common functionality"""
    
    def __init__(self, state_class: type[StateType]):
        super().__init__()
        self.state_class = state_class
        self.logger = logging.getLogger(f"flows.{self.__class__.__name__}")
        self.state_manager = StateManager()
        self.event_bus = EventBus()
        self.tenant_context = get_current_tenant()
        
        # Initialize state if not exists
        if not hasattr(self, 'state') or self.state is None:
            self.state = state_class()
            if self.tenant_context:
                self.state.tenant_id = self.tenant_context.tenant_id
    
    async def _persist_state(self):
        """Persist state to both CrewAI and our state manager"""
        try:
            await self.state_manager.save_state(self.state)
            await self.event_bus.publish_state_change(self.state)
        except Exception as e:
            self.logger.error(f"Failed to persist state: {e}")
    
    async def _handle_error(self, phase: str, error: Exception):
        """Standard error handling for all flows"""
        self.logger.error(f"Error in phase {phase}: {error}")
        
        if hasattr(self.state, 'errors'):
            self.state.errors.append({
                'phase': phase,
                'error': str(error),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        if hasattr(self.state, 'status'):
            self.state.status = 'error'
        
        await self._persist_state()
        await self.event_bus.publish_error(self.state.flow_id, phase, error)
    
    @abstractmethod
    async def execute_flow(self) -> str:
        """Execute the flow - implemented by subclasses"""
        pass
```

#### Discovery Flow State Model
```python
# backend/app/models/flow_state.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

class FlowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class PhaseStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class DiscoveryFlowState(BaseModel):
    # Core identification
    flow_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    user_id: Optional[UUID] = None
    
    # Flow control
    status: FlowStatus = FlowStatus.PENDING
    current_phase: str = "initialization"
    progress_percentage: float = 0.0
    
    # Phase tracking
    phases: Dict[str, PhaseStatus] = Field(default_factory=lambda: {
        "validation": PhaseStatus.PENDING,
        "mapping": PhaseStatus.PENDING,
        "cleansing": PhaseStatus.PENDING,
        "inventory": PhaseStatus.PENDING,
        "dependencies": PhaseStatus.PENDING,
        "analysis": PhaseStatus.PENDING
    })
    
    # Data storage
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)
    processed_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Results from each phase
    validation_results: Dict[str, Any] = Field(default_factory=dict)
    field_mappings: Dict[str, Any] = Field(default_factory=dict)
    cleaned_data: List[Dict[str, Any]] = Field(default_factory=list)
    asset_inventory: Dict[str, Any] = Field(default_factory=dict)
    dependencies: Dict[str, Any] = Field(default_factory=dict)
    analysis_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent insights and confidence scores
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Error handling
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def mark_phase_complete(self, phase: str, results: Optional[Dict] = None):
        """Mark a phase as completed and store results"""
        self.phases[phase] = PhaseStatus.COMPLETED
        self.updated_at = datetime.utcnow()
        
        if results:
            setattr(self, f"{phase}_results", results)
        
        # Update progress
        completed_phases = sum(1 for status in self.phases.values() 
                              if status == PhaseStatus.COMPLETED)
        self.progress_percentage = (completed_phases / len(self.phases)) * 100
    
    def add_error(self, phase: str, error: str, details: Optional[Dict] = None):
        """Add an error to the flow state"""
        self.errors.append({
            'phase': phase,
            'error': error,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        self.phases[phase] = PhaseStatus.FAILED
        self.updated_at = datetime.utcnow()
    
    def add_insight(self, agent_id: str, insight: str, confidence: float, 
                   metadata: Optional[Dict] = None):
        """Add an agent insight"""
        self.agent_insights.append({
            'agent_id': agent_id,
            'insight': insight,
            'confidence': confidence,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        })
        self.confidence_scores[agent_id] = confidence
        self.updated_at = datetime.utcnow()
```

#### Discovery Flow Implementation
```python
# backend/app/flows/discovery.py
from app.flows.base import BaseFlow
from app.models.flow_state import DiscoveryFlowState, FlowStatus, PhaseStatus
from app.agents.registry import AgentRegistry
from app.crews.factory import CrewFactory
from typing import Any, Dict
import asyncio

class DiscoveryFlow(BaseFlow[DiscoveryFlowState]):
    """Main discovery flow for asset discovery and analysis"""
    
    def __init__(self, raw_data: List[Dict], metadata: Dict[str, Any] = None):
        super().__init__(DiscoveryFlowState)
        
        # Initialize state with input data
        self.state.raw_data = raw_data
        self.state.metadata = metadata or {}
        
        # Initialize agent registry and crew factory
        self.agent_registry = AgentRegistry()
        self.crew_factory = CrewFactory()
    
    @start()
    async def initialize_discovery(self) -> str:
        """Initialize the discovery flow"""
        self.logger.info(f"Initializing discovery flow: {self.state.flow_id}")
        
        try:
            # Set initial state
            self.state.status = FlowStatus.RUNNING
            self.state.started_at = datetime.utcnow()
            
            # Validate input data
            if not self.state.raw_data:
                raise ValueError("No raw data provided for discovery")
            
            self.logger.info(f"Discovery initialized with {len(self.state.raw_data)} records")
            await self._persist_state()
            
            return "initialized"
            
        except Exception as e:
            await self._handle_error("initialization", e)
            return "failed"
    
    @listen(initialize_discovery)
    async def execute_data_validation(self, previous_result: str) -> str:
        """Execute data validation phase"""
        if previous_result == "failed":
            return "validation_skipped"
        
        self.logger.info("Starting data validation phase")
        self.state.current_phase = "validation"
        self.state.phases["validation"] = PhaseStatus.RUNNING
        
        try:
            # Get validation agents
            validation_agents = self.agent_registry.get_agents_by_type("validation")
            
            # Create validation crew
            validation_crew = self.crew_factory.create_validation_crew(
                agents=validation_agents,
                data=self.state.raw_data,
                metadata=self.state.metadata
            )
            
            # Execute crew
            crew_result = await validation_crew.kickoff_async({
                'data': self.state.raw_data,
                'metadata': self.state.metadata
            })
            
            # Process results
            self.state.validation_results = crew_result.raw
            self.state.mark_phase_complete("validation", crew_result.raw)
            
            # Extract insights from agents
            for agent_result in crew_result.tasks_output:
                if hasattr(agent_result, 'agent') and hasattr(agent_result.agent, 'agent_id'):
                    self.state.add_insight(
                        agent_id=agent_result.agent.agent_id,
                        insight=f"Validation completed for {agent_result.agent.role}",
                        confidence=0.9,  # Will be extracted from actual agent output
                        metadata={'task': agent_result.description}
                    )
            
            await self._persist_state()
            self.logger.info("Data validation phase completed successfully")
            return "validation_completed"
            
        except Exception as e:
            await self._handle_error("validation", e)
            return "validation_failed"
    
    @listen(execute_data_validation)
    async def execute_field_mapping(self, previous_result: str) -> str:
        """Execute field mapping phase"""
        if previous_result == "validation_failed":
            self.logger.warning("Proceeding with field mapping despite validation failure")
        
        self.logger.info("Starting field mapping phase")
        self.state.current_phase = "mapping"
        self.state.phases["mapping"] = PhaseStatus.RUNNING
        
        try:
            # Get mapping agents
            mapping_agents = self.agent_registry.get_agents_by_type("mapping")
            
            # Create mapping crew
            mapping_crew = self.crew_factory.create_mapping_crew(
                agents=mapping_agents,
                data=self.state.raw_data,
                validation_results=self.state.validation_results
            )
            
            # Execute crew
            crew_result = await mapping_crew.kickoff_async({
                'raw_data': self.state.raw_data,
                'validation_results': self.state.validation_results,
                'learned_patterns': await self._get_learned_patterns("mapping")
            })
            
            # Process results
            self.state.field_mappings = crew_result.raw
            self.state.mark_phase_complete("mapping", crew_result.raw)
            
            await self._persist_state()
            self.logger.info("Field mapping phase completed successfully")
            return "mapping_completed"
            
        except Exception as e:
            await self._handle_error("mapping", e)
            return "mapping_failed"
    
    @listen(execute_field_mapping)
    async def execute_data_cleansing(self, previous_result: str) -> str:
        """Execute data cleansing phase"""
        if previous_result == "mapping_failed":
            self.logger.warning("Proceeding with data cleansing despite mapping failure")
        
        self.logger.info("Starting data cleansing phase")
        self.state.current_phase = "cleansing"
        self.state.phases["cleansing"] = PhaseStatus.RUNNING
        
        try:
            # Get cleansing agents
            cleansing_agents = self.agent_registry.get_agents_by_type("cleansing")
            
            # Create cleansing crew
            cleansing_crew = self.crew_factory.create_cleansing_crew(
                agents=cleansing_agents,
                data=self.state.raw_data,
                field_mappings=self.state.field_mappings
            )
            
            # Execute crew
            crew_result = await cleansing_crew.kickoff_async({
                'raw_data': self.state.raw_data,
                'field_mappings': self.state.field_mappings,
                'quality_standards': self.state.metadata.get('quality_standards', {})
            })
            
            # Process results
            self.state.cleaned_data = crew_result.raw.get('cleaned_data', [])
            self.state.mark_phase_complete("cleansing", crew_result.raw)
            
            await self._persist_state()
            self.logger.info(f"Data cleansing completed: {len(self.state.cleaned_data)} clean records")
            return "cleansing_completed"
            
        except Exception as e:
            await self._handle_error("cleansing", e)
            return "cleansing_failed"
    
    @listen(execute_data_cleansing)
    async def execute_parallel_analysis(self, previous_result: str) -> str:
        """Execute inventory and dependency analysis in parallel"""
        if previous_result == "cleansing_failed":
            self.logger.warning("Proceeding with analysis despite cleansing failure")
        
        self.logger.info("Starting parallel analysis phases")
        self.state.current_phase = "analysis"
        self.state.phases["inventory"] = PhaseStatus.RUNNING
        self.state.phases["dependencies"] = PhaseStatus.RUNNING
        
        try:
            # Create crews for parallel execution
            inventory_crew = self.crew_factory.create_inventory_crew(
                agents=self.agent_registry.get_agents_by_type("inventory"),
                data=self.state.cleaned_data or self.state.raw_data
            )
            
            dependency_crew = self.crew_factory.create_dependency_crew(
                agents=self.agent_registry.get_agents_by_type("dependency"),
                data=self.state.cleaned_data or self.state.raw_data
            )
            
            # Execute crews in parallel
            inventory_task = inventory_crew.kickoff_async({
                'cleaned_data': self.state.cleaned_data,
                'field_mappings': self.state.field_mappings
            })
            
            dependency_task = dependency_crew.kickoff_async({
                'cleaned_data': self.state.cleaned_data,
                'field_mappings': self.state.field_mappings
            })
            
            # Wait for both to complete
            inventory_result, dependency_result = await asyncio.gather(
                inventory_task, dependency_task, return_exceptions=True
            )
            
            # Process inventory results
            if not isinstance(inventory_result, Exception):
                self.state.asset_inventory = inventory_result.raw
                self.state.mark_phase_complete("inventory", inventory_result.raw)
                self.logger.info("Asset inventory phase completed successfully")
            else:
                await self._handle_error("inventory", inventory_result)
            
            # Process dependency results
            if not isinstance(dependency_result, Exception):
                self.state.dependencies = dependency_result.raw
                self.state.mark_phase_complete("dependencies", dependency_result.raw)
                self.logger.info("Dependency analysis phase completed successfully")
            else:
                await self._handle_error("dependencies", dependency_result)
            
            await self._persist_state()
            return "analysis_completed"
            
        except Exception as e:
            await self._handle_error("analysis", e)
            return "analysis_failed"
    
    @listen(execute_parallel_analysis)
    async def finalize_discovery(self, previous_result: str) -> str:
        """Finalize the discovery flow"""
        self.logger.info("Finalizing discovery flow")
        
        try:
            # Calculate final statistics
            total_assets = len(self.state.asset_inventory.get('assets', []))
            total_dependencies = len(self.state.dependencies.get('relationships', []))
            error_count = len(self.state.errors)
            
            # Create summary
            summary = {
                'flow_id': str(self.state.flow_id),
                'total_assets': total_assets,
                'total_dependencies': total_dependencies,
                'error_count': error_count,
                'success_rate': (total_assets / len(self.state.raw_data)) * 100 if self.state.raw_data else 0,
                'duration_seconds': (datetime.utcnow() - self.state.started_at).total_seconds(),
                'phases_completed': [phase for phase, status in self.state.phases.items() 
                                   if status == PhaseStatus.COMPLETED]
            }
            
            self.state.analysis_results = summary
            self.state.status = FlowStatus.COMPLETED if error_count == 0 else FlowStatus.FAILED
            self.state.completed_at = datetime.utcnow()
            self.state.progress_percentage = 100.0
            
            await self._persist_state()
            await self.event_bus.publish_flow_completed(self.state)
            
            self.logger.info(f"Discovery flow completed: {total_assets} assets, {total_dependencies} dependencies")
            return "discovery_completed"
            
        except Exception as e:
            await self._handle_error("finalization", e)
            return "discovery_failed"
    
    async def _get_learned_patterns(self, pattern_type: str) -> Dict[str, Any]:
        """Retrieve learned patterns for agent use"""
        # This will be implemented when learning system is ready
        return {}
```

### Day 13-14: Agent Registry and Factory

#### Agent Registry System
```python
# backend/app/agents/registry.py
from typing import Dict, List, Type, Optional
from abc import ABC, abstractmethod
from crewai import Agent
from app.agents.base import BaseAgent
import importlib
import os
import logging

logger = logging.getLogger(__name__)

class AgentRegistry:
    """Registry for managing and discovering agents"""
    
    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._agent_instances: Dict[str, BaseAgent] = {}
        self._agents_by_type: Dict[str, List[str]] = {}
        self._auto_discover()
    
    def _auto_discover(self):
        """Automatically discover and register agents"""
        agent_dir = os.path.dirname(__file__)
        
        for file in os.listdir(agent_dir):
            if file.endswith('_agent.py') and not file.startswith('__'):
                module_name = file[:-3]  # Remove .py
                try:
                    module = importlib.import_module(f'app.agents.{module_name}')
                    
                    # Look for agent classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseAgent) and 
                            attr != BaseAgent):
                            self.register_agent(attr)
                            
                except Exception as e:
                    logger.warning(f"Failed to load agent module {module_name}: {e}")
    
    def register_agent(self, agent_class: Type[BaseAgent]):
        """Register an agent class"""
        agent_id = agent_class.get_agent_id()
        agent_type = agent_class.get_agent_type()
        
        self._agents[agent_id] = agent_class
        
        if agent_type not in self._agents_by_type:
            self._agents_by_type[agent_type] = []
        self._agents_by_type[agent_type].append(agent_id)
        
        logger.info(f"Registered agent: {agent_id} (type: {agent_type})")
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent instance by ID"""
        if agent_id in self._agent_instances:
            return self._agent_instances[agent_id]
        
        if agent_id in self._agents:
            agent_class = self._agents[agent_id]
            instance = agent_class()
            self._agent_instances[agent_id] = instance
            return instance
        
        return None
    
    def get_agents_by_type(self, agent_type: str) -> List[BaseAgent]:
        """Get all agents of a specific type"""
        if agent_type not in self._agents_by_type:
            return []
        
        agents = []
        for agent_id in self._agents_by_type[agent_type]:
            agent = self.get_agent(agent_id)
            if agent:
                agents.append(agent)
        
        return agents
    
    def list_agents(self) -> Dict[str, Dict[str, str]]:
        """List all registered agents"""
        result = {}
        for agent_id, agent_class in self._agents.items():
            result[agent_id] = {
                'type': agent_class.get_agent_type(),
                'description': agent_class.get_description(),
                'capabilities': agent_class.get_capabilities()
            }
        return result
```

#### Base Agent Implementation
```python
# backend/app/agents/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from crewai import Agent
from crewai.tools import BaseTool
from app.tools.registry import ToolRegistry
from app.services.llm_service import LLMService
import logging

class BaseAgent(Agent, ABC):
    """Base class for all platform agents"""
    
    def __init__(self):
        # Get agent configuration
        config = self.get_agent_config()
        
        # Initialize tools
        tools = self._initialize_tools()
        
        # Initialize with CrewAI Agent
        super().__init__(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            tools=tools,
            llm=LLMService.get_default_llm(),
            verbose=True,
            memory=True,
            allow_delegation=False  # Control delegation explicitly
        )
        
        self.logger = logging.getLogger(f"agents.{self.get_agent_id()}")
        self.tool_registry = ToolRegistry()
    
    @classmethod
    @abstractmethod
    def get_agent_id(cls) -> str:
        """Return unique agent identifier"""
        pass
    
    @classmethod
    @abstractmethod
    def get_agent_type(cls) -> str:
        """Return agent type for categorization"""
        pass
    
    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """Return agent description"""
        pass
    
    @classmethod
    @abstractmethod
    def get_capabilities(cls) -> List[str]:
        """Return list of agent capabilities"""
        pass
    
    @abstractmethod
    def get_agent_config(self) -> Dict[str, str]:
        """Return agent configuration (role, goal, backstory)"""
        pass
    
    @abstractmethod
    def get_required_tools(self) -> List[str]:
        """Return list of required tool IDs"""
        pass
    
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize agent tools"""
        tool_ids = self.get_required_tools()
        tools = []
        
        for tool_id in tool_ids:
            tool = self.tool_registry.get_tool(tool_id)
            if tool:
                tools.append(tool)
            else:
                self.logger.warning(f"Tool not found: {tool_id}")
        
        return tools
    
    async def analyze(self, data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze data using the agent's capabilities
        This method can be overridden for custom analysis logic
        """
        try:
            # Prepare input for the agent
            input_data = self._prepare_input(data, context)
            
            # Execute the agent (this will use CrewAI's execution)
            result = await self._execute_analysis(input_data)
            
            # Process and return results
            return self._process_results(result)
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_id': self.get_agent_id()
            }
    
    def _prepare_input(self, data: Dict[str, Any], context: Optional[Dict] = None) -> Dict[str, Any]:
        """Prepare input data for analysis"""
        return {
            'data': data,
            'context': context or {},
            'agent_id': self.get_agent_id(),
            'capabilities': self.get_capabilities()
        }
    
    async def _execute_analysis(self, input_data: Dict[str, Any]) -> Any:
        """Execute the actual analysis - can be overridden"""
        # This is where CrewAI agent execution would happen
        # For now, return a placeholder
        return {
            'status': 'completed',
            'results': {},
            'confidence': 0.8
        }
    
    def _process_results(self, raw_result: Any) -> Dict[str, Any]:
        """Process raw results into standard format"""
        return {
            'success': True,
            'agent_id': self.get_agent_id(),
            'results': raw_result,
            'timestamp': datetime.utcnow().isoformat()
        }
```

### Day 15: Crew Factory and Management

#### Crew Factory Implementation
```python
# backend/app/crews/factory.py
from typing import List, Dict, Any, Optional
from crewai import Crew, Task, Process
from app.agents.base import BaseAgent
from app.agents.registry import AgentRegistry
from app.services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)

class CrewFactory:
    """Factory for creating specialized crews"""
    
    def __init__(self):
        self.agent_registry = AgentRegistry()
        self.llm_service = LLMService()
    
    def create_validation_crew(self, agents: List[BaseAgent], 
                             data: List[Dict], metadata: Dict) -> Crew:
        """Create a crew for data validation"""
        
        # Create tasks for validation
        tasks = []
        
        for agent in agents:
            if 'pii_detection' in agent.get_capabilities():
                task = Task(
                    description=f"""
                    Analyze the provided data for PII (Personally Identifiable Information).
                    
                    Data to analyze: {len(data)} records
                    Metadata: {metadata}
                    
                    Requirements:
                    1. Identify any PII fields (SSN, email, phone, etc.)
                    2. Assess data sensitivity levels
                    3. Recommend masking or encryption requirements
                    4. Provide confidence scores for each finding
                    
                    Return results in JSON format with findings and recommendations.
                    """,
                    agent=agent,
                    expected_output="JSON with PII analysis results and recommendations"
                )
                tasks.append(task)
            
            elif 'format_validation' in agent.get_capabilities():
                task = Task(
                    description=f"""
                    Validate the format and structure of the provided data.
                    
                    Data to analyze: {len(data)} records
                    Sample record keys: {list(data[0].keys()) if data else []}
                    
                    Requirements:
                    1. Validate data types and formats
                    2. Check for required fields
                    3. Identify inconsistencies
                    4. Suggest data cleansing needs
                    
                    Return results in JSON format with validation findings.
                    """,
                    agent=agent,
                    expected_output="JSON with format validation results"
                )
                tasks.append(task)
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )
    
    def create_mapping_crew(self, agents: List[BaseAgent], 
                          data: List[Dict], validation_results: Dict) -> Crew:
        """Create a crew for field mapping"""
        
        tasks = []
        
        for agent in agents:
            if 'field_mapping' in agent.get_capabilities():
                task = Task(
                    description=f"""
                    Map source data fields to standard migration schema.
                    
                    Source data sample: {data[0] if data else {}}
                    Available fields: {list(data[0].keys()) if data else []}
                    Validation results: {validation_results}
                    
                    Requirements:
                    1. Map each source field to target schema fields
                    2. Identify unmapped fields and suggest mappings
                    3. Provide confidence scores for each mapping
                    4. Suggest field transformations needed
                    
                    Target schema fields:
                    - hostname, ip_address, operating_system
                    - environment, business_owner, department
                    - criticality, asset_type, location
                    
                    Return mapping results in JSON format.
                    """,
                    agent=agent,
                    expected_output="JSON with field mapping results and confidence scores"
                )
                tasks.append(task)
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )
    
    def create_cleansing_crew(self, agents: List[BaseAgent], 
                            data: List[Dict], field_mappings: Dict) -> Crew:
        """Create a crew for data cleansing"""
        
        tasks = []
        
        for agent in agents:
            if 'data_cleansing' in agent.get_capabilities():
                task = Task(
                    description=f"""
                    Cleanse and standardize the provided data using field mappings.
                    
                    Raw data: {len(data)} records
                    Field mappings: {field_mappings}
                    
                    Requirements:
                    1. Apply field mappings to transform data
                    2. Standardize values (e.g., OS names, environments)
                    3. Fill missing values where possible
                    4. Remove duplicates and invalid records
                    5. Validate data quality after cleansing
                    
                    Return cleansed data and quality metrics.
                    """,
                    agent=agent,
                    expected_output="JSON with cleansed data and quality metrics"
                )
                tasks.append(task)
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )
    
    def create_inventory_crew(self, agents: List[BaseAgent], 
                            data: List[Dict]) -> Crew:
        """Create a crew for asset inventory building"""
        
        tasks = []
        
        for agent in agents:
            if 'asset_classification' in agent.get_capabilities():
                task = Task(
                    description=f"""
                    Build comprehensive asset inventory from cleansed data.
                    
                    Cleansed data: {len(data)} records
                    
                    Requirements:
                    1. Classify assets by type (servers, applications, databases, etc.)
                    2. Group related assets
                    3. Identify critical vs non-critical assets
                    4. Create asset hierarchy and relationships
                    5. Generate asset metadata and tags
                    
                    Return structured inventory with classifications.
                    """,
                    agent=agent,
                    expected_output="JSON with asset inventory and classifications"
                )
                tasks.append(task)
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )
    
    def create_dependency_crew(self, agents: List[BaseAgent], 
                             data: List[Dict]) -> Crew:
        """Create a crew for dependency analysis"""
        
        tasks = []
        
        for agent in agents:
            if 'dependency_analysis' in agent.get_capabilities():
                task = Task(
                    description=f"""
                    Analyze dependencies and relationships between assets.
                    
                    Asset data: {len(data)} records
                    
                    Requirements:
                    1. Identify application-to-server dependencies
                    2. Map database connections and dependencies
                    3. Discover network dependencies
                    4. Create dependency graph
                    5. Assess migration complexity based on dependencies
                    
                    Return dependency analysis with relationship mappings.
                    """,
                    agent=agent,
                    expected_output="JSON with dependency analysis and relationship mappings"
                )
                tasks.append(task)
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=True
        )
```

## Week 4: Agent Implementation

### Day 16-17: Core Agent Implementations

#### Data Validation Agent
```python
# backend/app/agents/validation_agent.py
from app.agents.base import BaseAgent
from typing import List, Dict, Any

class DataValidationAgent(BaseAgent):
    
    @classmethod
    def get_agent_id(cls) -> str:
        return "data_validation_agent"
    
    @classmethod
    def get_agent_type(cls) -> str:
        return "validation"
    
    @classmethod
    def get_description(cls) -> str:
        return "Validates data quality, format, and security for migration readiness"
    
    @classmethod
    def get_capabilities(cls) -> List[str]:
        return ["pii_detection", "format_validation", "data_quality", "security_scan"]
    
    def get_agent_config(self) -> Dict[str, str]:
        return {
            "role": "Senior Data Quality Analyst",
            "goal": "Ensure data integrity and security compliance for migration",
            "backstory": """You are a seasoned data quality expert with 15 years of experience 
                           in enterprise data migration projects. You have a keen eye for detecting 
                           PII, data format issues, and security vulnerabilities. Your expertise 
                           includes GDPR compliance, data classification, and enterprise security 
                           standards."""
        }
    
    def get_required_tools(self) -> List[str]:
        return ["pii_scanner", "format_validator", "data_profiler", "security_scanner"]
```

#### Field Mapping Agent
```python
# backend/app/agents/mapping_agent.py
from app.agents.base import BaseAgent
from typing import List, Dict, Any

class FieldMappingAgent(BaseAgent):
    
    @classmethod
    def get_agent_id(cls) -> str:
        return "field_mapping_agent"
    
    @classmethod
    def get_agent_type(cls) -> str:
        return "mapping"
    
    @classmethod
    def get_description(cls) -> str:
        return "Maps source data fields to standardized migration schema"
    
    @classmethod
    def get_capabilities(cls) -> List[str]:
        return ["field_mapping", "schema_analysis", "semantic_matching", "confidence_scoring"]
    
    def get_agent_config(self) -> Dict[str, str]:
        return {
            "role": "Enterprise Data Architect",
            "goal": "Create accurate field mappings for seamless data transformation",
            "backstory": """You are an expert data architect with deep knowledge of enterprise 
                           systems and data schemas. You excel at understanding data semantics 
                           and creating precise field mappings. Your experience includes working 
                           with CMDB systems, asset inventories, and enterprise data warehouses."""
        }
    
    def get_required_tools(self) -> List[str]:
        return ["schema_analyzer", "semantic_matcher", "confidence_calculator", "mapping_validator"]
```

### Day 18-19: Tool System Implementation

#### Tool Registry
```python
# backend/app/tools/registry.py
from typing import Dict, Optional, List
from crewai.tools import BaseTool
import importlib
import os
import logging

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for managing and discovering tools"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._auto_discover()
    
    def _auto_discover(self):
        """Automatically discover and register tools"""
        tools_dir = os.path.dirname(__file__)
        
        for file in os.listdir(tools_dir):
            if file.endswith('_tool.py') and not file.startswith('__'):
                module_name = file[:-3]
                try:
                    module = importlib.import_module(f'app.tools.{module_name}')
                    
                    # Look for tool classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseTool) and 
                            attr != BaseTool):
                            tool_instance = attr()
                            self.register_tool(tool_instance)
                            
                except Exception as e:
                    logger.warning(f"Failed to load tool module {module_name}: {e}")
    
    def register_tool(self, tool: BaseTool):
        """Register a tool instance"""
        tool_id = getattr(tool, 'tool_id', tool.name)
        self._tools[tool_id] = tool
        logger.info(f"Registered tool: {tool_id}")
    
    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """Get a tool by ID"""
        return self._tools.get(tool_id)
    
    def list_tools(self) -> List[str]:
        """List all registered tool IDs"""
        return list(self._tools.keys())
```

#### Example Tools
```python
# backend/app/tools/pii_scanner_tool.py
from crewai.tools import BaseTool
from typing import Any, Dict
import re

class PiiScannerTool(BaseTool):
    name: str = "pii_scanner"
    description: str = "Scans data for personally identifiable information (PII)"
    tool_id: str = "pii_scanner"
    
    def _run(self, data: str) -> Dict[str, Any]:
        """Scan data for PII patterns"""
        
        pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        }
        
        findings = {}
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, data)
            if matches:
                findings[pii_type] = {
                    'count': len(matches),
                    'samples': matches[:3],  # First 3 matches
                    'risk_level': 'high' if pii_type in ['ssn', 'credit_card'] else 'medium'
                }
        
        return {
            'scan_completed': True,
            'findings': findings,
            'total_pii_items': sum(len(f['samples']) for f in findings.values()),
            'risk_assessment': 'high' if any(f['risk_level'] == 'high' for f in findings.values()) else 'medium'
        }

# backend/app/tools/schema_analyzer_tool.py
from crewai.tools import BaseTool
from typing import Any, Dict, List

class SchemaAnalyzerTool(BaseTool):
    name: str = "schema_analyzer"
    description: str = "Analyzes data schema and field characteristics"
    tool_id: str = "schema_analyzer"
    
    def _run(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze schema of provided data"""
        
        if not data:
            return {'error': 'No data provided'}
        
        schema_analysis = {}
        
        # Analyze each field
        for record in data[:100]:  # Sample first 100 records
            for field, value in record.items():
                if field not in schema_analysis:
                    schema_analysis[field] = {
                        'data_type': type(value).__name__,
                        'sample_values': [],
                        'null_count': 0,
                        'unique_values': set(),
                        'patterns': set()
                    }
                
                field_info = schema_analysis[field]
                
                if value is None:
                    field_info['null_count'] += 1
                else:
                    field_info['sample_values'].append(str(value)[:50])  # Truncate long values
                    field_info['unique_values'].add(str(value))
                    
                    # Detect patterns
                    if isinstance(value, str):
                        if re.match(r'^\d+\.\d+\.\d+\.\d+$', value):
                            field_info['patterns'].add('ip_address')
                        elif re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$', value):
                            field_info['patterns'].add('email')
                        elif re.match(r'^\d{4}-\d{2}-\d{2}', value):
                            field_info['patterns'].add('date')
        
        # Convert sets to lists for JSON serialization
        for field_info in schema_analysis.values():
            field_info['unique_values'] = list(field_info['unique_values'])[:10]  # Limit samples
            field_info['patterns'] = list(field_info['patterns'])
            field_info['sample_values'] = field_info['sample_values'][:5]  # Limit samples
        
        return {
            'schema_analysis': schema_analysis,
            'total_fields': len(schema_analysis),
            'total_records_analyzed': len(data)
        }
```

### Day 20: State Management and Event System

#### State Manager Implementation
```python
# backend/app/services/state_manager.py
from typing import Optional, Dict, Any
from uuid import UUID
from app.models.flow_state import DiscoveryFlowState
from app.core.database import AsyncSessionLocal
from app.repositories.flow_state import FlowStateRepository
import json
import logging

logger = logging.getLogger(__name__)

class StateManager:
    """Manages flow state persistence and retrieval"""
    
    def __init__(self):
        self.repository = None
    
    async def save_state(self, state: DiscoveryFlowState):
        """Save flow state to database"""
        try:
            async with AsyncSessionLocal() as db:
                if not self.repository:
                    self.repository = FlowStateRepository(db)
                
                # Convert state to dict for storage
                state_data = state.model_dump()
                
                # Save or update
                await self.repository.upsert_flow_state(
                    flow_id=state.flow_id,
                    state_data=state_data
                )
                
                logger.info(f"Saved state for flow {state.flow_id}")
                
        except Exception as e:
            logger.error(f"Failed to save state for flow {state.flow_id}: {e}")
            raise
    
    async def load_state(self, flow_id: UUID) -> Optional[DiscoveryFlowState]:
        """Load flow state from database"""
        try:
            async with AsyncSessionLocal() as db:
                if not self.repository:
                    self.repository = FlowStateRepository(db)
                
                state_data = await self.repository.get_flow_state(flow_id)
                
                if state_data:
                    return DiscoveryFlowState(**state_data)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to load state for flow {flow_id}: {e}")
            return None
    
    async def delete_state(self, flow_id: UUID):
        """Delete flow state from database"""
        try:
            async with AsyncSessionLocal() as db:
                if not self.repository:
                    self.repository = FlowStateRepository(db)
                
                await self.repository.delete_flow_state(flow_id)
                logger.info(f"Deleted state for flow {flow_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete state for flow {flow_id}: {e}")
            raise
```

#### Event Bus Implementation
```python
# backend/app/services/event_bus.py
from typing import Any, Dict, List, Callable, Optional
from uuid import UUID
from datetime import datetime
from app.models.flow_state import DiscoveryFlowState
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class FlowEvent:
    def __init__(self, event_type: str, flow_id: UUID, data: Dict[str, Any]):
        self.event_type = event_type
        self.flow_id = flow_id
        self.data = data
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'flow_id': str(self.flow_id),
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }

class EventBus:
    """Event bus for flow events and notifications"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._redis_client = None  # Will be initialized when needed
    
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    async def publish(self, event: FlowEvent):
        """Publish an event to all subscribers"""
        try:
            # Notify local subscribers
            if event.event_type in self._subscribers:
                for callback in self._subscribers[event.event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Event callback failed: {e}")
            
            # Publish to Redis for distributed systems
            if self._redis_client:
                await self._redis_client.publish(
                    f"flow_events:{event.event_type}",
                    json.dumps(event.to_dict())
                )
            
            logger.debug(f"Published event: {event.event_type} for flow {event.flow_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
    
    async def publish_state_change(self, state: DiscoveryFlowState):
        """Publish state change event"""
        event = FlowEvent(
            event_type="state_changed",
            flow_id=state.flow_id,
            data={
                'status': state.status,
                'current_phase': state.current_phase,
                'progress_percentage': state.progress_percentage,
                'phases': dict(state.phases)
            }
        )
        await self.publish(event)
    
    async def publish_phase_started(self, flow_id: UUID, phase: str):
        """Publish phase started event"""
        event = FlowEvent(
            event_type="phase_started",
            flow_id=flow_id,
            data={'phase': phase}
        )
        await self.publish(event)
    
    async def publish_phase_completed(self, flow_id: UUID, phase: str, results: Dict):
        """Publish phase completed event"""
        event = FlowEvent(
            event_type="phase_completed",
            flow_id=flow_id,
            data={'phase': phase, 'results': results}
        )
        await self.publish(event)
    
    async def publish_error(self, flow_id: UUID, phase: str, error: Exception):
        """Publish error event"""
        event = FlowEvent(
            event_type="error_occurred",
            flow_id=flow_id,
            data={
                'phase': phase,
                'error': str(error),
                'error_type': type(error).__name__
            }
        )
        await self.publish(event)
    
    async def publish_flow_completed(self, state: DiscoveryFlowState):
        """Publish flow completed event"""
        event = FlowEvent(
            event_type="flow_completed",
            flow_id=state.flow_id,
            data={
                'status': state.status,
                'duration': (state.completed_at - state.started_at).total_seconds() if state.completed_at and state.started_at else 0,
                'summary': state.analysis_results
            }
        )
        await self.publish(event)
```

## Deliverables for Phase 2

### CrewAI Framework Deliverables
1. **Base Flow Architecture**: Reusable flow framework with proper patterns
2. **Agent Registry System**: Auto-discovery and management of agents
3. **Crew Factory**: Dynamic crew composition for different phases
4. **Tool System**: Extensible tool registry and base tools

### Implementation Deliverables
1. **Discovery Flow**: Complete implementation with all phases
2. **Core Agents**: Data validation, field mapping, cleansing agents
3. **State Management**: Persistent state with event system
4. **Event Bus**: Real-time event publishing and subscription

### Integration Deliverables
1. **Database Models**: Flow state and related models
2. **Repository Layer**: Data access with tenant isolation
3. **Service Layer**: State management and event handling
4. **Configuration**: LLM service integration

### Quality Gates
- [ ] Discovery flow executes end-to-end successfully
- [ ] All agents can be discovered and instantiated
- [ ] Crews can be created and executed
- [ ] State persistence works correctly
- [ ] Events are published and handled
- [ ] Error handling is comprehensive
- [ ] Performance meets targets (<45s for 1000 records)