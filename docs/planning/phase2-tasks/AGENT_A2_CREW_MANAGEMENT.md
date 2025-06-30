# Phase 2 - Agent A2: Crew Factory and Management

## Context
You are part of Phase 2 remediation effort to transform the AI Force Migration Platform to proper CrewAI architecture. This is Track A (Crews) focusing on implementing proper CrewAI Crew patterns, task orchestration, and crew coordination.

### Required Reading Before Starting
- `docs/planning/PHASE-2-REMEDIATION-PLAN.md` - Phase 2 objectives
- `AGENT_A1_AGENT_SYSTEM_CORE.md` - Understanding agent infrastructure
- CrewAI documentation on Crews and Tasks
- Current crew implementations in `backend/app/services/crewai_flows/crews/`

### Prerequisites
- Agent A1 has created the agent registry and base classes
- Core agents are converted to CrewAI pattern
- Agent factory is available

### Phase 2 Goal
Implement proper CrewAI Crew patterns with dynamic crew composition, task orchestration, and process management. Transform individual agent executions into coordinated crew operations.

## Your Specific Tasks

### 1. Create Base Crew Implementation
**File to create**: `backend/app/services/crews/base_crew.py`

```python
"""
Base Crew implementation with context awareness and standard patterns
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from crewai import Crew, Task, Process
from app.core.context import get_current_context
from app.services.agents.factory import agent_factory
from app.services.llm_config import get_crewai_llm
import logging

logger = logging.getLogger(__name__)

class BaseDiscoveryCrew(ABC):
    """
    Base class for all discovery crews.
    Provides:
    - Standard crew initialization
    - Context-aware execution
    - Task creation patterns
    - Result handling
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        process: Process = Process.sequential,
        verbose: bool = True,
        memory: bool = True,
        cache: bool = True,
        max_rpm: int = 100,
        share_crew: bool = False
    ):
        """Initialize base crew with configuration"""
        self.name = name
        self.description = description
        self.context = get_current_context()
        self.llm = get_crewai_llm()
        
        # Crew configuration
        self.process = process
        self.verbose = verbose
        self.memory = memory
        self.cache = cache
        self.max_rpm = max_rpm
        self.share_crew = share_crew
        
        # Will be populated by subclasses
        self.agents: List[Any] = []
        self.tasks: List[Task] = []
        self.crew: Optional[Crew] = None
    
    @abstractmethod
    def create_agents(self) -> List[Any]:
        """Create and return agents for this crew"""
        pass
    
    @abstractmethod
    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create and return tasks for this crew"""
        pass
    
    def initialize_crew(self, inputs: Dict[str, Any]) -> Crew:
        """Initialize the crew with agents and tasks"""
        # Create agents
        self.agents = self.create_agents()
        if not self.agents:
            raise ValueError(f"No agents created for crew {self.name}")
        
        # Create tasks
        self.tasks = self.create_tasks(inputs)
        if not self.tasks:
            raise ValueError(f"No tasks created for crew {self.name}")
        
        # Create crew
        self.crew = Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=self.process,
            verbose=self.verbose,
            memory=self.memory,
            cache=self.cache,
            max_rpm=self.max_rpm,
            share_crew=self.share_crew
        )
        
        logger.info(f"Initialized crew: {self.name} with {len(self.agents)} agents and {len(self.tasks)} tasks")
        return self.crew
    
    def execute(self, inputs: Dict[str, Any]) -> Any:
        """Execute the crew with given inputs"""
        try:
            # Ensure context is set
            if not self.context:
                raise ValueError("No context available for multi-tenant execution")
            
            logger.info(f"Executing crew {self.name} for client {self.context.client_account_id}")
            
            # Initialize crew if not already done
            if not self.crew:
                self.initialize_crew(inputs)
            
            # Execute crew
            result = self.crew.kickoff(inputs=inputs)
            
            logger.info(f"Crew {self.name} completed successfully")
            return self.process_results(result)
            
        except Exception as e:
            logger.error(f"Crew {self.name} execution failed: {e}")
            raise
    
    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process crew results into standard format"""
        return {
            "crew_name": self.name,
            "status": "completed",
            "results": raw_results,
            "context": {
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            }
        }
```

### 2. Implement Field Mapping Crew
**File to update**: `backend/app/services/crewai_flows/crews/field_mapping_crew.py`

```python
"""
Field Mapping Crew - Proper CrewAI implementation
"""

from typing import List, Dict, Any
from crewai import Task, Process
from app.services.crews.base_crew import BaseDiscoveryCrew
from app.services.agents.factory import agent_factory
import json

class FieldMappingCrew(BaseDiscoveryCrew):
    """
    Crew for intelligent field mapping using multiple specialized agents.
    
    Process:
    1. Schema analysis
    2. Semantic matching
    3. Confidence scoring
    4. Validation
    """
    
    def __init__(self):
        """Initialize field mapping crew"""
        super().__init__(
            name="field_mapping_crew",
            description="Intelligent field mapping with semantic understanding",
            process=Process.sequential,
            verbose=True,
            memory=True,
            cache=True
        )
    
    def create_agents(self) -> List[Any]:
        """Create specialized agents for field mapping"""
        return [
            agent_factory.create_agent("schema_analyzer_agent"),
            agent_factory.create_agent("field_mapping_agent"),
            agent_factory.create_agent("semantic_matcher_agent"),
            agent_factory.create_agent("validation_agent")
        ]
    
    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        """Create field mapping tasks"""
        source_schema = inputs.get("source_schema", {})
        target_fields = inputs.get("target_fields", [])
        sample_data = inputs.get("sample_data", [])
        
        tasks = []
        
        # Task 1: Analyze source schema
        schema_analysis_task = Task(
            description=f"""
            Analyze the source data schema and extract field characteristics:
            
            Source Schema: {json.dumps(source_schema, indent=2)}
            Sample Data: {json.dumps(sample_data[:5], indent=2)}
            
            For each field, identify:
            1. Data type and format
            2. Value patterns and ranges
            3. Null percentage
            4. Unique value count
            5. Potential field purpose
            
            Output a detailed analysis of each source field.
            """,
            agent=self.agents[0],  # schema_analyzer_agent
            expected_output="Detailed schema analysis with field characteristics"
        )
        tasks.append(schema_analysis_task)
        
        # Task 2: Create initial mappings
        initial_mapping_task = Task(
            description=f"""
            Create initial field mappings based on schema analysis:
            
            Target Fields Available: {json.dumps(target_fields, indent=2)}
            
            For each source field:
            1. Find the best matching target field
            2. Consider field names, types, and purposes
            3. Assign initial confidence score (0-1)
            4. Provide reasoning for the mapping
            
            Output mappings as JSON:
            {{
                "mappings": [
                    {{
                        "source_field": "field_name",
                        "target_field": "target_name",
                        "confidence": 0.85,
                        "reasoning": "explanation"
                    }}
                ]
            }}
            """,
            agent=self.agents[1],  # field_mapping_agent
            expected_output="JSON list of field mappings with confidence scores",
            context=[schema_analysis_task]
        )
        tasks.append(initial_mapping_task)
        
        # Task 3: Semantic enhancement
        semantic_enhancement_task = Task(
            description="""
            Enhance field mappings using semantic analysis:
            
            1. Analyze semantic similarity between field names
            2. Consider business context and domain knowledge
            3. Identify potential many-to-one or one-to-many mappings
            4. Adjust confidence scores based on semantic matching
            5. Flag ambiguous mappings for review
            
            Improve the mappings with deeper semantic understanding.
            """,
            agent=self.agents[2],  # semantic_matcher_agent
            expected_output="Enhanced mappings with semantic analysis",
            context=[initial_mapping_task]
        )
        tasks.append(semantic_enhancement_task)
        
        # Task 4: Validation and finalization
        validation_task = Task(
            description="""
            Validate and finalize the field mappings:
            
            1. Check for mapping conflicts or duplicates
            2. Ensure all critical fields are mapped
            3. Validate data type compatibility
            4. Set final confidence scores
            5. Create summary report
            
            Output final validated mappings ready for use.
            """,
            agent=self.agents[3],  # validation_agent
            expected_output="Final validated field mappings with summary",
            context=[semantic_enhancement_task]
        )
        tasks.append(validation_task)
        
        return tasks
    
    def process_results(self, raw_results: Any) -> Dict[str, Any]:
        """Process field mapping results"""
        # Extract mappings from the final task result
        final_result = raw_results
        
        # Parse mappings if they're in string format
        if isinstance(final_result, str):
            try:
                import re
                # Extract JSON from the result
                json_match = re.search(r'\{.*\}', final_result, re.DOTALL)
                if json_match:
                    final_result = json.loads(json_match.group())
            except:
                logger.warning("Could not parse JSON from results")
        
        return {
            "crew_name": self.name,
            "status": "completed",
            "mappings": final_result.get("mappings", []) if isinstance(final_result, dict) else [],
            "summary": {
                "total_fields": len(final_result.get("mappings", [])) if isinstance(final_result, dict) else 0,
                "high_confidence": sum(1 for m in final_result.get("mappings", []) if m.get("confidence", 0) > 0.8) if isinstance(final_result, dict) else 0,
                "requires_review": sum(1 for m in final_result.get("mappings", []) if m.get("confidence", 0) < 0.6) if isinstance(final_result, dict) else 0
            },
            "context": {
                "client_account_id": self.context.client_account_id,
                "engagement_id": self.context.engagement_id
            }
        }
```

### 3. Create Crew Factory
**File to create**: `backend/app/services/crews/factory.py`

```python
"""
Crew Factory for dynamic crew composition
"""

from typing import Dict, Any, Optional, Type
from app.services.crews.base_crew import BaseDiscoveryCrew
from app.services.crewai_flows.crews.field_mapping_crew import FieldMappingCrew
from app.services.crewai_flows.crews.data_cleansing_crew import DataCleansingCrew
from app.services.crewai_flows.crews.asset_inventory_crew import AssetInventoryCrew
from app.services.crewai_flows.crews.dependency_analysis_crew import DependencyAnalysisCrew
import logging

logger = logging.getLogger(__name__)

class CrewFactory:
    """
    Factory for creating and managing CrewAI crews.
    Provides:
    - Dynamic crew instantiation
    - Crew registry
    - Execution management
    """
    
    # Registry of available crews
    _crew_registry: Dict[str, Type[BaseDiscoveryCrew]] = {
        "field_mapping": FieldMappingCrew,
        "data_cleansing": DataCleansingCrew,
        "asset_inventory": AssetInventoryCrew,
        "dependency_analysis": DependencyAnalysisCrew
    }
    
    @classmethod
    def register_crew(cls, name: str, crew_class: Type[BaseDiscoveryCrew]) -> None:
        """Register a new crew type"""
        cls._crew_registry[name] = crew_class
        logger.info(f"Registered crew: {name}")
    
    @classmethod
    def create_crew(cls, crew_type: str) -> Optional[BaseDiscoveryCrew]:
        """Create a crew instance by type"""
        crew_class = cls._crew_registry.get(crew_type)
        if not crew_class:
            logger.error(f"Unknown crew type: {crew_type}")
            return None
        
        try:
            crew = crew_class()
            logger.info(f"Created crew: {crew_type}")
            return crew
        except Exception as e:
            logger.error(f"Failed to create crew {crew_type}: {e}")
            return None
    
    @classmethod
    def execute_crew(
        cls, 
        crew_type: str, 
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create and execute a crew in one call"""
        crew = cls.create_crew(crew_type)
        if not crew:
            return {
                "status": "error",
                "error": f"Failed to create crew: {crew_type}"
            }
        
        try:
            return crew.execute(inputs)
        except Exception as e:
            logger.error(f"Crew execution failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "crew_type": crew_type
            }
    
    @classmethod
    def list_crews(cls) -> List[str]:
        """List all available crew types"""
        return list(cls._crew_registry.keys())
```

### 4. Create Task Templates
**File to create**: `backend/app/services/crews/task_templates.py`

```python
"""
Reusable task templates for common operations
"""

from crewai import Task
from typing import Any, List, Dict

class TaskTemplates:
    """
    Library of reusable task templates.
    Provides standard task patterns for common operations.
    """
    
    @staticmethod
    def create_analysis_task(
        description: str,
        agent: Any,
        data: Dict[str, Any],
        expected_output: str,
        context: List[Task] = None
    ) -> Task:
        """Create a standard analysis task"""
        return Task(
            description=f"""
            {description}
            
            Data to analyze:
            {data}
            
            Provide comprehensive analysis including:
            - Key findings
            - Patterns identified
            - Potential issues
            - Recommendations
            """,
            agent=agent,
            expected_output=expected_output,
            context=context or []
        )
    
    @staticmethod
    def create_validation_task(
        items_to_validate: List[Any],
        validation_rules: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a validation task"""
        return Task(
            description=f"""
            Validate the following items against specified rules:
            
            Items: {items_to_validate}
            
            Validation Rules:
            {validation_rules}
            
            For each item:
            1. Check against all applicable rules
            2. Identify any violations
            3. Assign validation status
            4. Provide correction suggestions
            
            Output validation report with pass/fail status.
            """,
            agent=agent,
            expected_output="Validation report with detailed findings",
            context=context or []
        )
    
    @staticmethod
    def create_transformation_task(
        source_format: str,
        target_format: str,
        transformation_rules: Dict[str, Any],
        agent: Any,
        context: List[Task] = None
    ) -> Task:
        """Create a data transformation task"""
        return Task(
            description=f"""
            Transform data from {source_format} to {target_format}:
            
            Transformation Rules:
            {transformation_rules}
            
            Steps:
            1. Parse source format
            2. Apply transformation rules
            3. Validate transformed data
            4. Format according to target specification
            
            Ensure no data loss during transformation.
            """,
            agent=agent,
            expected_output=f"Data successfully transformed to {target_format}",
            context=context or []
        )
```

### 5. Update Other Crews
Convert these crews to use the new base class:
- `data_cleansing_crew.py`
- `asset_inventory_crew.py`
- `dependency_analysis_crew.py`

Each should:
1. Inherit from `BaseDiscoveryCrew`
2. Implement `create_agents()` and `create_tasks()`
3. Use proper task chaining with context
4. Process results appropriately

## Success Criteria
- [ ] Base crew class provides standard patterns
- [ ] Field mapping crew fully implemented
- [ ] Crew factory creates crews dynamically
- [ ] Task templates reduce duplication
- [ ] All crews converted to new pattern
- [ ] Proper task chaining with context
- [ ] Results processed consistently

## Interfaces with Other Agents
- **Agent A1** provides the agents you'll use
- **Agent B1** will integrate crews into flows
- **Agent D1** uses crews for tool coordination
- Share crew types in registry

## Implementation Guidelines

### 1. Crew Structure Pattern
```python
class MyCrew(BaseDiscoveryCrew):
    def create_agents(self) -> List[Any]:
        # Use agent_factory to create agents
        
    def create_tasks(self, inputs: Dict[str, Any]) -> List[Task]:
        # Create tasks with proper context chaining
```

### 2. Task Context Chaining
```python
task2 = Task(
    description="...",
    agent=agent2,
    context=[task1]  # Results from task1 available
)
```

### 3. Process Selection
- Use `Process.sequential` for dependent tasks
- Use `Process.hierarchical` for complex coordination
- Consider parallel execution where possible

## Commands to Run
```bash
# Test crew creation
docker exec -it migration_backend python -c "from app.services.crews.factory import CrewFactory; print(CrewFactory.list_crews())"

# Test field mapping crew
docker exec -it migration_backend python -m pytest tests/crews/test_field_mapping_crew.py -v

# Test crew execution
docker exec -it migration_backend python -m tests.crews.test_crew_execution
```

## Definition of Done
- [ ] Base crew class implemented
- [ ] Field mapping crew working end-to-end
- [ ] Crew factory creates all crew types
- [ ] Task templates in use
- [ ] All crews converted to new pattern
- [ ] Context propagation verified
- [ ] Unit tests >85% coverage
- [ ] Integration tests passing
- [ ] PR created with title: "feat: [Phase2-A2] Crew factory and management"

## Notes
- Start with base crew class
- Focus on field mapping crew first
- Test task chaining thoroughly
- Ensure context flows through all operations
- Keep crews focused on single responsibility