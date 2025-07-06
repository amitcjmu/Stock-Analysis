# Team Epsilon - CrewAI Implementation Briefing

## Mission Statement
Team Epsilon is responsible for implementing real CrewAI agents to replace the archived pseudo-agents, ensuring the platform leverages true AI-driven decision making and learning capabilities as designed.

## Team Objectives
1. Implement real CrewAI discovery agents to replace pseudo-agents
2. Create proper CrewAI crews with defined roles and goals
3. Implement agent tools for data analysis and validation
4. Set up agent memory and learning systems
5. Integrate with existing UnifiedDiscoveryFlow
6. Implement agent observability and monitoring

## Background Context
The platform previously used "pseudo-agents" (Pydantic-based classes) that have been archived. The UnifiedDiscoveryFlow is ready for real CrewAI implementation with proper @start/@listen decorators.

## Specific Tasks

### Task 1: Create Base CrewAI Agent Structure
**Create foundation for all agents:**

```python
# /backend/app/services/crewai_flows/agents/base_agent.py
from crewai import Agent
from typing import Optional, Dict, Any, List
from app.services.tools.registry import ToolRegistry
from app.core.config import settings

class BaseCrewAIAgent(Agent):
    """Base class for all CrewAI agents in the platform"""
    
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[Any]] = None,
        llm: Optional[Any] = None,
        max_iter: int = 10,
        memory: bool = True,
        verbose: bool = True,
        allow_delegation: bool = False,
        **kwargs
    ):
        # Use configured LLM if not provided
        if llm is None:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                api_key=settings.DEEPINFRA_API_KEY,
                base_url="https://api.deepinfra.com/v1/openai",
                model=settings.LLM_MODEL,
                temperature=0.7
            )
        
        # Get tools from registry if not provided
        if tools is None:
            tools = ToolRegistry.get_tools_for_role(role)
        
        super().__init__(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            llm=llm,
            max_iter=max_iter,
            memory=memory,
            verbose=verbose,
            allow_delegation=allow_delegation,
            **kwargs
        )
        
    def log_execution(self, task: str, result: Any) -> None:
        """Log agent execution for observability"""
        # Implementation for logging
        pass
```

### Task 2: Implement Discovery Agents
**Replace pseudo-agents with real CrewAI agents:**

```python
# /backend/app/services/crewai_flows/agents/discovery/data_validation_agent.py
from app.services.crewai_flows.agents.base_agent import BaseCrewAIAgent
from app.services.tools.data_validation_tool import DataValidationTool
from app.services.tools.schema_analyzer_tool import SchemaAnalyzerTool

class DataValidationAgent(BaseCrewAIAgent):
    """Agent responsible for validating imported data"""
    
    def __init__(self):
        super().__init__(
            role="Data Validation Specialist",
            goal="Validate imported data for completeness, accuracy, and compatibility with target systems",
            backstory="""You are an expert data validation specialist with years of experience 
            in enterprise data migration. You understand various data formats (CSV, JSON, XML) 
            and can identify data quality issues, missing fields, format inconsistencies, and 
            potential migration blockers. You provide detailed validation reports with actionable 
            recommendations.""",
            tools=[
                DataValidationTool(),
                SchemaAnalyzerTool()
            ]
        )

# /backend/app/services/crewai_flows/agents/discovery/attribute_mapping_agent.py
class AttributeMappingAgent(BaseCrewAIAgent):
    """Agent responsible for intelligent attribute mapping"""
    
    def __init__(self):
        super().__init__(
            role="Attribute Mapping Expert",
            goal="Create optimal mappings between source and target system attributes using ML and pattern recognition",
            backstory="""You are an AI-powered attribute mapping expert who excels at understanding 
            data schemas and creating intelligent mappings. You use machine learning to recognize 
            patterns, suggest mappings based on semantic similarity, and learn from user feedback 
            to improve future suggestions. You understand enterprise systems like AWS, Azure, GCP 
            and their resource attributes.""",
            tools=[
                AttributeAnalyzerTool(),
                SemanticMatchingTool(),
                MappingSuggestionTool()
            ]
        )

# /backend/app/services/crewai_flows/agents/discovery/data_cleansing_agent.py  
class DataCleansingAgent(BaseCrewAIAgent):
    """Agent responsible for data cleansing and transformation"""
    
    def __init__(self):
        super().__init__(
            role="Data Cleansing Specialist",
            goal="Clean, transform, and standardize data for optimal migration results",
            backstory="""You are a data cleansing expert who identifies and fixes data quality 
            issues. You excel at standardizing formats, handling missing values, removing duplicates, 
            and transforming data to meet target system requirements. You provide detailed reports 
            on all cleansing actions taken and their impact on data quality.""",
            tools=[
                DataCleansingTool(),
                DataTransformationTool(),
                QualityMetricsTool()
            ]
        )

# /backend/app/services/crewai_flows/agents/discovery/insight_generation_agent.py
class InsightGenerationAgent(BaseCrewAIAgent):
    """Agent responsible for generating migration insights"""
    
    def __init__(self):
        super().__init__(
            role="Migration Insight Analyst",
            goal="Generate actionable insights and recommendations for the migration strategy",
            backstory="""You are a senior migration analyst who synthesizes data from various 
            sources to provide strategic insights. You identify patterns, risks, opportunities, 
            and provide recommendations for migration strategy, timeline, and resource allocation. 
            Your insights help organizations make informed decisions about their cloud migration.""",
            tools=[
                InsightAnalysisTool(),
                RiskAssessmentTool(),
                RecommendationTool()
            ]
        )
```

### Task 3: Create Discovery Crew
**Implement crew coordination:**

```python
# /backend/app/services/crewai_flows/crews/discovery_crew.py
from crewai import Crew, Task
from typing import Dict, Any, List
from app.services.crewai_flows.agents.discovery import (
    DataValidationAgent,
    AttributeMappingAgent,
    DataCleansingAgent,
    InsightGenerationAgent
)

class DiscoveryCrew:
    """Crew for handling discovery flow operations"""
    
    def __init__(self, client_account_id: int, flow_id: str):
        self.client_account_id = client_account_id
        self.flow_id = flow_id
        self._setup_agents()
        self._setup_crew()
    
    def _setup_agents(self):
        """Initialize all agents for the crew"""
        self.data_validation_agent = DataValidationAgent()
        self.attribute_mapping_agent = AttributeMappingAgent()
        self.data_cleansing_agent = DataCleansingAgent()
        self.insight_generation_agent = InsightGenerationAgent()
    
    def _setup_crew(self):
        """Setup the crew with agents"""
        self.crew = Crew(
            agents=[
                self.data_validation_agent,
                self.attribute_mapping_agent,
                self.data_cleansing_agent,
                self.insight_generation_agent
            ],
            verbose=True,
            memory=True,
            embedder={
                "provider": "openai",
                "config": {
                    "api_key": settings.DEEPINFRA_API_KEY,
                    "base_url": "https://api.deepinfra.com/v1/openai"
                }
            }
        )
    
    def validate_data(self, import_data: Dict[str, Any]) -> Task:
        """Create data validation task"""
        return Task(
            description=f"""
            Validate the imported data for flow {self.flow_id}.
            Check for:
            1. Data completeness and required fields
            2. Data type consistency
            3. Format validation
            4. Referential integrity
            5. Business rule compliance
            
            Data to validate:
            {import_data}
            """,
            expected_output="Detailed validation report with issues, warnings, and recommendations",
            agent=self.data_validation_agent
        )
    
    def map_attributes(self, source_schema: Dict, target_schema: Dict) -> Task:
        """Create attribute mapping task"""
        return Task(
            description=f"""
            Create intelligent attribute mappings between source and target schemas.
            Use semantic analysis and ML to suggest optimal mappings.
            
            Source Schema: {source_schema}
            Target Schema: {target_schema}
            
            Consider:
            1. Semantic similarity
            2. Data type compatibility
            3. Business context
            4. Historical mapping patterns
            """,
            expected_output="Attribute mapping suggestions with confidence scores and transformation rules",
            agent=self.attribute_mapping_agent
        )
    
    def cleanse_data(self, data: Dict, validation_results: Dict) -> Task:
        """Create data cleansing task"""
        return Task(
            description=f"""
            Cleanse and transform data based on validation results.
            
            Apply these cleansing operations:
            1. Standardize formats
            2. Handle missing values
            3. Remove duplicates
            4. Fix data quality issues
            5. Apply transformation rules
            
            Validation Results: {validation_results}
            """,
            expected_output="Cleansed data with transformation report",
            agent=self.data_cleansing_agent
        )
    
    def generate_insights(self, all_results: Dict) -> Task:
        """Create insight generation task"""
        return Task(
            description=f"""
            Generate comprehensive migration insights based on all discovery results.
            
            Analyze:
            1. Data quality metrics
            2. Complexity assessment
            3. Risk factors
            4. Migration timeline estimates
            5. Resource requirements
            6. Cost implications
            
            Results to analyze: {all_results}
            """,
            expected_output="Executive summary with insights, risks, and recommendations",
            agent=self.insight_generation_agent
        )
    
    async def run_discovery_flow(self, import_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete discovery flow"""
        # Create tasks
        validation_task = self.validate_data(import_data)
        
        # Execute validation
        validation_results = await self.crew.kickoff(tasks=[validation_task])
        
        # Map attributes based on validation
        mapping_task = self.map_attributes(
            import_data.get('source_schema', {}),
            import_data.get('target_schema', {})
        )
        mapping_results = await self.crew.kickoff(tasks=[mapping_task])
        
        # Cleanse data
        cleansing_task = self.cleanse_data(import_data, validation_results)
        cleansing_results = await self.crew.kickoff(tasks=[cleansing_task])
        
        # Generate insights
        all_results = {
            'validation': validation_results,
            'mapping': mapping_results,
            'cleansing': cleansing_results
        }
        insight_task = self.generate_insights(all_results)
        insights = await self.crew.kickoff(tasks=[insight_task])
        
        return {
            'status': 'completed',
            'results': all_results,
            'insights': insights
        }
```

### Task 4: Implement Agent Tools
**Create specialized tools for agents:**

```python
# /backend/app/services/tools/data_validation_tool.py
from crewai_tools import BaseTool
from typing import Dict, Any, List
import pandas as pd
import json

class DataValidationTool(BaseTool):
    name: str = "Data Validation Tool"
    description: str = "Validates data quality, completeness, and format compliance"
    
    def _run(self, data: str) -> str:
        """Execute data validation"""
        try:
            # Parse input data
            if isinstance(data, str):
                data_dict = json.loads(data)
            else:
                data_dict = data
            
            validation_results = {
                'total_records': 0,
                'valid_records': 0,
                'issues': [],
                'warnings': [],
                'field_analysis': {}
            }
            
            # Validate based on data type
            if 'csv_data' in data_dict:
                results = self._validate_csv(data_dict['csv_data'])
            elif 'json_data' in data_dict:
                results = self._validate_json(data_dict['json_data'])
            else:
                results = self._validate_generic(data_dict)
            
            return json.dumps(results, indent=2)
            
        except Exception as e:
            return f"Validation error: {str(e)}"
    
    def _validate_csv(self, csv_data: str) -> Dict[str, Any]:
        """Validate CSV data"""
        df = pd.read_csv(pd.io.common.StringIO(csv_data))
        
        return {
            'total_records': len(df),
            'columns': list(df.columns),
            'missing_values': df.isnull().sum().to_dict(),
            'duplicate_rows': df.duplicated().sum(),
            'data_types': df.dtypes.astype(str).to_dict(),
            'unique_values': {col: df[col].nunique() for col in df.columns},
            'validation_passed': True
        }

# /backend/app/services/tools/semantic_matching_tool.py
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticMatchingTool(BaseTool):
    name: str = "Semantic Matching Tool"
    description: str = "Uses ML to find semantic similarities between attributes"
    
    def __init__(self):
        super().__init__()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _run(self, params: str) -> str:
        """Find semantic matches between attributes"""
        try:
            params_dict = json.loads(params)
            source_attrs = params_dict.get('source_attributes', [])
            target_attrs = params_dict.get('target_attributes', [])
            
            # Generate embeddings
            source_embeddings = self.model.encode(source_attrs)
            target_embeddings = self.model.encode(target_attrs)
            
            # Calculate similarity matrix
            similarity_matrix = np.inner(source_embeddings, target_embeddings)
            
            # Find best matches
            matches = []
            for i, source_attr in enumerate(source_attrs):
                best_match_idx = np.argmax(similarity_matrix[i])
                confidence = similarity_matrix[i][best_match_idx]
                
                matches.append({
                    'source': source_attr,
                    'target': target_attrs[best_match_idx],
                    'confidence': float(confidence),
                    'match_type': 'semantic'
                })
            
            return json.dumps({
                'matches': matches,
                'average_confidence': np.mean([m['confidence'] for m in matches])
            }, indent=2)
            
        except Exception as e:
            return f"Semantic matching error: {str(e)}"
```

### Task 5: Integrate with UnifiedDiscoveryFlow
**Update flow to use real CrewAI:**

```python
# /backend/app/services/crewai_flows/unified_discovery_flow.py
from crewai.flow.flow import Flow, listen, start
from app.services.crewai_flows.crews.discovery_crew import DiscoveryCrew

class UnifiedDiscoveryFlow(Flow):
    def __init__(self, client_account_id: int, flow_id: str):
        super().__init__()
        self.client_account_id = client_account_id
        self.flow_id = flow_id
        self.discovery_crew = DiscoveryCrew(client_account_id, flow_id)
    
    @start()
    async def initialize_flow(self):
        """Initialize the discovery flow"""
        self.state['status'] = 'initialized'
        self.state['phase'] = 'initialization'
        return {'status': 'initialized', 'flow_id': self.flow_id}
    
    @listen(initialize_flow)
    async def data_import_phase(self):
        """Handle data import with real CrewAI validation"""
        import_data = self.state.get('import_data', {})
        
        # Use CrewAI for validation
        validation_task = self.discovery_crew.validate_data(import_data)
        validation_results = await self.discovery_crew.crew.kickoff(tasks=[validation_task])
        
        self.state['validation_results'] = validation_results
        self.state['phase'] = 'data_import'
        
        return validation_results
    
    @listen(data_import_phase)
    async def attribute_mapping_phase(self):
        """Handle attribute mapping with CrewAI"""
        source_schema = self.state.get('source_schema', {})
        target_schema = self.state.get('target_schema', {})
        
        # Use CrewAI for intelligent mapping
        mapping_task = self.discovery_crew.map_attributes(source_schema, target_schema)
        mapping_results = await self.discovery_crew.crew.kickoff(tasks=[mapping_task])
        
        self.state['mapping_results'] = mapping_results
        self.state['phase'] = 'attribute_mapping'
        
        return mapping_results
    
    @listen(attribute_mapping_phase)
    async def data_cleansing_phase(self):
        """Handle data cleansing with CrewAI"""
        validation_results = self.state.get('validation_results', {})
        import_data = self.state.get('import_data', {})
        
        # Use CrewAI for cleansing
        cleansing_task = self.discovery_crew.cleanse_data(import_data, validation_results)
        cleansing_results = await self.discovery_crew.crew.kickoff(tasks=[cleansing_task])
        
        self.state['cleansing_results'] = cleansing_results
        self.state['phase'] = 'data_cleansing'
        
        return cleansing_results
    
    @listen(data_cleansing_phase)
    async def insight_generation_phase(self):
        """Generate insights using CrewAI"""
        all_results = {
            'validation': self.state.get('validation_results'),
            'mapping': self.state.get('mapping_results'),
            'cleansing': self.state.get('cleansing_results')
        }
        
        # Use CrewAI for insight generation
        insight_task = self.discovery_crew.generate_insights(all_results)
        insights = await self.discovery_crew.crew.kickoff(tasks=[insight_task])
        
        self.state['insights'] = insights
        self.state['phase'] = 'completed'
        self.state['status'] = 'completed'
        
        return insights
```

### Task 6: Implement Agent Memory and Learning
**Set up agent memory system:**

```python
# /backend/app/services/crewai_flows/memory/agent_memory.py
from typing import Dict, Any, List
import json
from datetime import datetime
from app.core.database import AsyncSessionLocal
from app.models.agent_memory import AgentMemory

class AgentMemoryManager:
    """Manages agent memory and learning"""
    
    @staticmethod
    async def store_interaction(
        agent_role: str,
        task: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None
    ):
        """Store agent interaction for learning"""
        async with AsyncSessionLocal() as session:
            memory = AgentMemory(
                agent_role=agent_role,
                task_type=task,
                input_data=json.dumps(input_data),
                output_data=json.dumps(output_data),
                feedback=json.dumps(feedback) if feedback else None,
                timestamp=datetime.utcnow()
            )
            session.add(memory)
            await session.commit()
    
    @staticmethod
    async def get_similar_interactions(
        agent_role: str,
        task: str,
        input_data: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve similar past interactions for learning"""
        # Implementation for semantic similarity search
        pass
    
    @staticmethod
    async def update_feedback(
        interaction_id: str,
        feedback: Dict[str, Any]
    ):
        """Update feedback for learning improvement"""
        async with AsyncSessionLocal() as session:
            memory = await session.get(AgentMemory, interaction_id)
            if memory:
                memory.feedback = json.dumps(feedback)
                memory.feedback_timestamp = datetime.utcnow()
                await session.commit()

# /backend/app/services/crewai_flows/memory/learning_system.py
class AgentLearningSystem:
    """Implements continuous learning for agents"""
    
    def __init__(self):
        self.memory_manager = AgentMemoryManager()
    
    async def learn_from_feedback(
        self,
        agent_role: str,
        task_type: str,
        feedback: Dict[str, Any]
    ):
        """Process feedback to improve agent performance"""
        # Get historical interactions
        similar_tasks = await self.memory_manager.get_similar_interactions(
            agent_role, task_type, {}, limit=20
        )
        
        # Analyze patterns in successful vs unsuccessful outcomes
        positive_patterns = self._extract_patterns(
            [t for t in similar_tasks if t.get('feedback', {}).get('success', False)]
        )
        negative_patterns = self._extract_patterns(
            [t for t in similar_tasks if not t.get('feedback', {}).get('success', True)]
        )
        
        # Update agent prompts/behaviors based on patterns
        return {
            'learned_patterns': positive_patterns,
            'avoid_patterns': negative_patterns,
            'confidence_improvement': self._calculate_improvement(similar_tasks)
        }
```

### Task 7: Implement Agent Observability
**Create monitoring for CrewAI agents:**

```python
# /backend/app/services/observability/agent_monitor.py
from typing import Dict, Any
import time
from prometheus_client import Counter, Histogram, Gauge
from app.core.events import EventBus

# Metrics
agent_tasks_total = Counter(
    'agent_tasks_total',
    'Total number of agent tasks',
    ['agent_role', 'task_type', 'status']
)
agent_task_duration = Histogram(
    'agent_task_duration_seconds',
    'Agent task execution duration',
    ['agent_role', 'task_type']
)
agent_confidence_score = Gauge(
    'agent_confidence_score',
    'Agent confidence in task output',
    ['agent_role', 'task_type']
)

class AgentMonitor:
    """Monitors CrewAI agent performance"""
    
    def __init__(self):
        self.event_bus = EventBus()
    
    async def track_task_execution(
        self,
        agent_role: str,
        task_type: str,
        task_func,
        *args,
        **kwargs
    ):
        """Track agent task execution"""
        start_time = time.time()
        
        try:
            # Execute task
            result = await task_func(*args, **kwargs)
            
            # Track metrics
            duration = time.time() - start_time
            agent_tasks_total.labels(
                agent_role=agent_role,
                task_type=task_type,
                status='success'
            ).inc()
            agent_task_duration.labels(
                agent_role=agent_role,
                task_type=task_type
            ).observe(duration)
            
            # Extract confidence if available
            if isinstance(result, dict) and 'confidence' in result:
                agent_confidence_score.labels(
                    agent_role=agent_role,
                    task_type=task_type
                ).set(result['confidence'])
            
            # Emit event
            await self.event_bus.emit('agent.task.completed', {
                'agent_role': agent_role,
                'task_type': task_type,
                'duration': duration,
                'status': 'success',
                'result_summary': self._summarize_result(result)
            })
            
            return result
            
        except Exception as e:
            # Track failure
            agent_tasks_total.labels(
                agent_role=agent_role,
                task_type=task_type,
                status='failure'
            ).inc()
            
            # Emit error event
            await self.event_bus.emit('agent.task.failed', {
                'agent_role': agent_role,
                'task_type': task_type,
                'error': str(e)
            })
            
            raise
```

## Success Criteria
1. All pseudo-agents replaced with real CrewAI agents
2. Agents using proper tools and LLM integration
3. Memory and learning system implemented
4. Agent decisions are explainable and auditable
5. Performance metrics collected and monitored
6. Agents improve over time with feedback
7. Integration with UnifiedDiscoveryFlow working
8. No hard-coded business logic in agents

## Common Issues and Solutions

### Issue 1: LLM API Errors
**Symptom:** Agents fail with API errors
**Solution:** Implement retry logic and fallback models:
```python
@retry(max_attempts=3, backoff_factor=2)
async def call_llm(self, prompt: str):
    try:
        return await self.primary_llm.invoke(prompt)
    except Exception as e:
        # Fallback to secondary model
        return await self.fallback_llm.invoke(prompt)
```

### Issue 2: Agent Memory Growth
**Symptom:** Database grows too large with memories
**Solution:** Implement memory pruning:
```python
async def prune_old_memories(days: int = 90):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    # Archive or delete old memories
```

### Issue 3: Slow Agent Response
**Symptom:** Agents take too long to respond
**Solution:** 
- Use async/await properly
- Implement caching for common queries
- Use smaller, specialized models for simple tasks

## Rollback Procedures
1. **Feature flag for CrewAI:**
   ```python
   USE_CREWAI = os.getenv('USE_CREWAI', 'true').lower() == 'true'
   
   if USE_CREWAI:
       crew = DiscoveryCrew()
   else:
       # Fallback to simpler implementation
   ```

2. **Gradual rollout:**
   - Start with one agent type
   - Monitor performance
   - Expand to other agents

3. **Emergency disable:**
   ```bash
   # Disable CrewAI
   export USE_CREWAI=false
   docker-compose restart backend
   ```

## Testing Requirements
```python
# Test agent creation
def test_agent_initialization():
    agent = DataValidationAgent()
    assert agent.role == "Data Validation Specialist"
    assert len(agent.tools) > 0

# Test crew execution
async def test_discovery_crew():
    crew = DiscoveryCrew(client_id=1, flow_id="test")
    result = await crew.run_discovery_flow({
        'csv_data': 'col1,col2\nval1,val2'
    })
    assert result['status'] == 'completed'

# Test memory system
async def test_agent_memory():
    await AgentMemoryManager.store_interaction(
        agent_role="validator",
        task="validate_csv",
        input_data={"file": "test.csv"},
        output_data={"valid": True}
    )
```

## Status Report Template
```markdown
# Epsilon Team Status Report - [DATE]

## Completed Tasks
- [ ] Task 1: Create Base CrewAI Agent Structure
- [ ] Task 2: Implement Discovery Agents
- [ ] Task 3: Create Discovery Crew
- [ ] Task 4: Implement Agent Tools
- [ ] Task 5: Integrate with UnifiedDiscoveryFlow
- [ ] Task 6: Implement Agent Memory and Learning
- [ ] Task 7: Implement Agent Observability

## Agent Implementation Status
| Agent | Status | Tools | Memory | Tests |
|-------|--------|-------|--------|-------|
| DataValidationAgent | Complete | 2/2 | ✓ | ✓ |
| AttributeMappingAgent | In Progress | 3/3 | ✓ | ✗ |

## Performance Metrics
- Average agent response time: X seconds
- Task success rate: X%
- Memory usage: X MB
- Learning improvement: X%

## Integration Status
- UnifiedDiscoveryFlow: X/Y phases integrated
- API endpoints: X/Y updated
- Frontend integration: Pending

## Issues Encountered
- Issue description and resolution

## Next Steps
- Additional agents to implement
- Performance optimizations needed
```

## Resources
- CrewAI Documentation: https://docs.crewai.com
- LangChain Integration: https://python.langchain.com
- DeepInfra API: https://deepinfra.com/docs
- Agent Tools Registry: `/backend/app/services/tools/`
- Memory Models: `/backend/app/models/agent_memory.py`

## Contact
- Team Lead: Epsilon Team
- Slack Channel: #epsilon-crewai-implementation
- AI/ML Support: #ml-team
- Backend Support: #backend-team