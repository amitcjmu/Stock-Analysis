# Discovery Flow Development Guide

## 📋 **Overview**

This guide provides comprehensive instructions for developers to understand, extend, and optimize the Discovery Flow CrewAI architecture. The system is built on CrewAI best practices with hierarchical crew management, shared memory, cross-crew collaboration, and adaptive planning.

## 🏗️ **Architecture Deep Dive**

### **Core Design Principles**

#### **1. Agentic-First Architecture**
- **All intelligence comes from CrewAI agents** - no hard-coded heuristics
- **Hierarchical Process**: Manager agents coordinate specialist agents
- **Learning System**: Agents improve through memory and feedback
- **Collaboration**: Cross-crew and intra-crew agent communication

#### **2. Modular Crew Design**
```python
# Each crew follows this pattern:
class DiscoveryCrew:
    def __init__(self, crewai_service):
        self.llm = crewai_service.llm
        self.knowledge_base = self._setup_knowledge_base()
        self.shared_memory = crewai_service.shared_memory
    
    def create_agents(self) -> List[Agent]:
        # Manager + Specialist agents
        pass
    
    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        # Hierarchical task structure
        pass
    
    def create_crew(self) -> Crew:
        # Process.hierarchical with memory and planning
        pass
```

#### **3. Flow State Management**
```python
class DiscoveryFlowState(BaseModel):
    # Session management
    session_id: str
    client_account_id: str
    engagement_id: str
    
    # Planning and coordination
    overall_plan: Dict[str, Any]
    crew_coordination: Dict[str, Any]
    
    # Shared resources
    shared_memory_id: str
    knowledge_base_refs: List[str]
    
    # Phase results
    field_mappings: Dict[str, Any]
    cleaned_data: List[Dict[str, Any]]
    asset_inventory: Dict[str, List[Dict[str, Any]]]
    # ... additional phase results
```

---

## 🧠 **Understanding the Crew Architecture**

### **Hierarchical Agent Structure**

#### **Manager Agents**
- **Purpose**: Coordinate crew activities, delegate tasks, make decisions
- **Configuration**: `manager=True`, `planning=True`, `delegation=True`
- **Responsibilities**: Planning, task delegation, quality assurance, coordination

```python
manager_agent = Agent(
    role="Crew Manager",
    goal="Coordinate crew activities and ensure quality results",
    backstory="Expert manager with deep domain knowledge",
    manager=True,
    planning=True,
    delegation=True,
    max_delegation=3,
    memory=shared_memory,
    knowledge=knowledge_base,
    verbose=True
)
```

#### **Specialist Agents**
- **Purpose**: Execute domain-specific tasks with expertise
- **Configuration**: `collaboration=True`, domain-specific tools
- **Responsibilities**: Task execution, insight generation, peer collaboration

```python
specialist_agent = Agent(
    role="Domain Specialist",
    goal="Execute specialized tasks with high accuracy",
    backstory="Expert in specific domain with deep knowledge",
    collaboration=True,
    delegation=False,
    memory=shared_memory,
    knowledge=knowledge_base,
    tools=[domain_specific_tools],
    verbose=True
)
```

### **Memory Integration Patterns**

#### **Shared Memory Configuration**
```python
from crewai.memory import LongTermMemory

shared_memory = LongTermMemory(
    storage_type="vector",
    embedder_config={
        "provider": "openai",
        "model": "text-embedding-3-small"
    }
)
```

#### **Memory Usage Patterns**
```python
# Storing insights for cross-crew sharing
def store_insights(self, insights: Dict[str, Any]):
    self.shared_memory.add(
        key=f"{self.crew_name}_insights",
        value=insights,
        metadata={
            "crew": self.crew_name,
            "phase": self.current_phase,
            "timestamp": datetime.now().isoformat()
        }
    )

# Retrieving insights from previous crews
def get_previous_insights(self, source_crew: str):
    return self.shared_memory.get(f"{source_crew}_insights")
```

### **Knowledge Base Integration**

#### **Domain-Specific Knowledge Bases**
```python
from crewai.knowledge import KnowledgeBase

field_mapping_kb = KnowledgeBase(
    sources=[
        "docs/field_mapping_patterns.json",
        "docs/industry_standards.yaml",
        "docs/semantic_patterns.csv"
    ],
    embedder_config={
        "provider": "openai",
        "model": "text-embedding-3-small"
    }
)
```

#### **Knowledge Application Patterns**
```python
# In agent tools
class SemanticAnalysisTool(BaseTool):
    def _run(self, field_data: str) -> str:
        # Query knowledge base for patterns
        patterns = self.knowledge_base.search(
            query=field_data,
            top_k=5
        )
        
        # Apply AI analysis with knowledge context
        return self.llm.analyze_with_context(field_data, patterns)
```

---

## 🛠️ **Adding New Crews**

### **Step 1: Define Crew Purpose and Architecture**

#### **Crew Specification Template**
```python
# File: backend/app/services/crewai_flows/crews/new_crew.py

from crewai import Agent, Task, Crew, Process
from crewai.memory import LongTermMemory
from crewai.knowledge import KnowledgeBase
from typing import List, Dict, Any

class NewAnalysisCrew:
    """
    Purpose: [Describe what this crew analyzes]
    Input: [What data this crew expects]
    Output: [What insights this crew produces]
    Dependencies: [Which crews must run before this one]
    """
    
    def __init__(self, crewai_service):
        self.llm = crewai_service.llm
        self.shared_memory = crewai_service.shared_memory
        self.knowledge_base = self._setup_knowledge_base()
        self.crew_name = "NewAnalysisCrew"
    
    def _setup_knowledge_base(self) -> KnowledgeBase:
        return KnowledgeBase(
            sources=["docs/new_analysis_patterns.json"],
            embedder_config={
                "provider": "openai",
                "model": "text-embedding-3-small"
            }
        )
```

### **Step 2: Create Manager Agent**

```python
def create_manager_agent(self) -> Agent:
    return Agent(
        role="New Analysis Manager",
        goal="Coordinate new analysis activities and ensure comprehensive coverage",
        backstory="Expert manager with 10+ years in [domain] analysis",
        manager=True,
        planning=True,
        delegation=True,
        max_delegation=2,  # Number of specialist agents
        memory=self.shared_memory,
        knowledge=self.knowledge_base,
        verbose=True,
        step_callback=self._manager_step_callback
    )

def _manager_step_callback(self, step: str):
    # Log manager activities
    logger.info(f"Manager step: {step}")
    # Store coordination insights
    self.shared_memory.add(f"manager_decisions_{step}", {
        "crew": self.crew_name,
        "decision": step,
        "timestamp": datetime.now().isoformat()
    })
```

### **Step 3: Create Specialist Agents**

```python
def create_specialist_agents(self) -> List[Agent]:
    specialist_1 = Agent(
        role="Domain Expert 1",
        goal="Analyze [specific aspect] with high accuracy",
        backstory="Specialist with deep knowledge of [domain area]",
        collaboration=True,
        delegation=False,
        memory=self.shared_memory,
        knowledge=self.knowledge_base,
        tools=[
            self._create_analysis_tool_1(),
            self._create_validation_tool_1()
        ],
        verbose=True
    )
    
    specialist_2 = Agent(
        role="Domain Expert 2", 
        goal="Analyze [different aspect] and coordinate with Expert 1",
        backstory="Specialist with expertise in [complementary domain]",
        collaboration=True,
        delegation=False,
        memory=self.shared_memory,
        knowledge=self.knowledge_base,
        tools=[
            self._create_analysis_tool_2(),
            self._create_collaboration_tool()
        ],
        verbose=True
    )
    
    return [specialist_1, specialist_2]
```

### **Step 4: Define Tasks with Dependencies**

```python
def create_tasks(self, agents: List[Agent]) -> List[Task]:
    manager, specialist_1, specialist_2 = agents
    
    # Planning task (manager)
    planning_task = Task(
        description="Plan comprehensive analysis strategy for new domain",
        expected_output="Analysis execution plan with specialist assignments",
        agent=manager,
        tools=[],
        async_execution=False
    )
    
    # Specialist task 1
    analysis_task_1 = Task(
        description="""
        Analyze [specific domain aspect] using shared memory insights.
        
        Requirements:
        1. Review previous crew insights from shared memory
        2. Apply domain-specific analysis patterns
        3. Generate high-confidence insights
        4. Store insights for collaboration with specialist 2
        """,
        expected_output="Domain analysis report with confidence scores",
        agent=specialist_1,
        context=[planning_task],
        tools=[
            self._create_analysis_tool_1(),
            self._create_validation_tool_1()
        ],
        async_execution=False,
        callback=self._specialist_1_callback
    )
    
    # Specialist task 2 with collaboration
    analysis_task_2 = Task(
        description="""
        Analyze [complementary aspect] collaborating with specialist 1.
        
        Requirements:
        1. Access specialist 1 insights from shared memory
        2. Cross-validate findings with specialist 1
        3. Generate collaborative insights
        4. Produce integrated analysis results
        """,
        expected_output="Integrated analysis with cross-validation",
        agent=specialist_2,
        context=[analysis_task_1],
        tools=[
            self._create_analysis_tool_2(),
            self._create_collaboration_tool()
        ],
        async_execution=False,
        callback=self._specialist_2_callback
    )
    
    return [planning_task, analysis_task_1, analysis_task_2]
```

### **Step 5: Create Crew with Collaboration**

```python
def create_crew(self) -> Crew:
    agents = [self.create_manager_agent()] + self.create_specialist_agents()
    tasks = self.create_tasks(agents)
    
    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_llm=self.llm,
        planning=True,
        memory=True,
        knowledge=self.knowledge_base,
        verbose=True,
        share_crew=True,  # Enable cross-crew collaboration
        step_callback=self._crew_step_callback,
        task_callback=self._task_completion_callback
    )
```

### **Step 6: Integrate with Discovery Flow**

```python
# File: backend/app/services/crewai_flows/discovery_flow_redesigned.py

@listen(execute_previous_crew)  # Listen to appropriate predecessor
def execute_new_analysis_crew(self, previous_result):
    """Execute new analysis crew using previous insights"""
    try:
        # Create crew instance
        new_crew = NewAnalysisCrew(self.crewai_service)
        crew = new_crew.create_crew()
        
        # Prepare input with previous insights
        crew_input = {
            "previous_insights": previous_result,
            "session_context": {
                "session_id": self.state.session_id,
                "client_account_id": self.state.client_account_id,
                "engagement_id": self.state.engagement_id
            }
        }
        
        # Execute crew
        result = crew.kickoff(inputs=crew_input)
        
        # Update state with results
        self.state.new_analysis_results = result
        
        # Store insights in shared memory
        self._store_crew_insights("new_analysis", result)
        
        return result
        
    except Exception as e:
        logger.error(f"New analysis crew execution failed: {e}")
        return self._handle_crew_failure("new_analysis", e)
```

---

## 🔧 **Creating Custom Agent Tools**

### **Tool Development Pattern**

```python
from crewai_tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Optional

class CustomAnalysisTool(BaseTool):
    name: str = "custom_analysis_tool"
    description: str = "Performs custom analysis using AI and domain knowledge"
    
    # Tool-specific configuration
    confidence_threshold: float = Field(default=0.8)
    analysis_depth: str = Field(default="comprehensive")
    
    def __init__(self, knowledge_base: Optional[Any] = None, **kwargs):
        super().__init__(**kwargs)
        self.knowledge_base = knowledge_base
    
    def _run(self, analysis_input: str) -> str:
        """Execute the custom analysis"""
        try:
            # 1. Query knowledge base for relevant patterns
            if self.knowledge_base:
                patterns = self.knowledge_base.search(
                    query=analysis_input,
                    top_k=5
                )
            else:
                patterns = []
            
            # 2. Apply AI analysis with context
            analysis_prompt = self._build_analysis_prompt(
                analysis_input, 
                patterns
            )
            
            # 3. Execute analysis
            result = self._execute_analysis(analysis_prompt)
            
            # 4. Validate and score confidence
            validated_result = self._validate_result(result)
            
            return validated_result
            
        except Exception as e:
            return f"Analysis failed: {str(e)}"
    
    def _build_analysis_prompt(self, input_data: str, patterns: List[Dict]) -> str:
        """Build analysis prompt with context"""
        prompt = f"""
        Analyze the following data using domain expertise and patterns:
        
        Data to analyze:
        {input_data}
        
        Relevant patterns from knowledge base:
        {self._format_patterns(patterns)}
        
        Requirements:
        - Provide high-confidence analysis
        - Include confidence scores
        - Identify key insights and patterns
        - Suggest actionable recommendations
        
        Analysis depth: {self.analysis_depth}
        Minimum confidence threshold: {self.confidence_threshold}
        """
        return prompt
    
    def _execute_analysis(self, prompt: str) -> Dict[str, Any]:
        """Execute the AI analysis"""
        # Use the crew's LLM for analysis
        response = self.llm.invoke(prompt)
        
        # Parse and structure the response
        structured_result = self._parse_llm_response(response)
        
        return structured_result
    
    def _validate_result(self, result: Dict[str, Any]) -> str:
        """Validate analysis result and format output"""
        confidence = result.get("confidence", 0.0)
        
        if confidence < self.confidence_threshold:
            result["warning"] = f"Low confidence ({confidence:.2f}) below threshold ({self.confidence_threshold})"
        
        # Format as structured output
        return json.dumps(result, indent=2)
```

### **Specialized Tool Examples**

#### **Pattern Recognition Tool**
```python
class PatternRecognitionTool(BaseTool):
    name: str = "pattern_recognition_tool"
    description: str = "Identifies patterns in data using AI and historical knowledge"
    
    def _run(self, data: str) -> str:
        # Implement pattern recognition logic
        patterns = self._identify_patterns(data)
        confidence_scores = self._calculate_confidence(patterns)
        
        return json.dumps({
            "patterns_found": patterns,
            "confidence_scores": confidence_scores,
            "recommendations": self._generate_recommendations(patterns)
        })
```

#### **Cross-Domain Collaboration Tool**
```python
class CollaborationTool(BaseTool):
    name: str = "collaboration_tool"
    description: str = "Facilitates collaboration with other agents and crews"
    
    def __init__(self, shared_memory: LongTermMemory, **kwargs):
        super().__init__(**kwargs)
        self.shared_memory = shared_memory
    
    def _run(self, collaboration_request: str) -> str:
        # Parse collaboration request
        request_data = json.loads(collaboration_request)
        target_agent = request_data.get("target_agent")
        message_type = request_data.get("message_type")
        payload = request_data.get("payload")
        
        # Store collaboration message in shared memory
        collaboration_key = f"collaboration_{target_agent}_{int(time.time())}"
        self.shared_memory.add(collaboration_key, {
            "from_agent": request_data.get("from_agent"),
            "to_agent": target_agent,
            "message_type": message_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        })
        
        # Return collaboration confirmation
        return json.dumps({
            "collaboration_initiated": True,
            "target_agent": target_agent,
            "message_key": collaboration_key
        })
```

---

## 📊 **Memory and Learning Systems**

### **Advanced Memory Patterns**

#### **Hierarchical Memory Organization**
```python
class HierarchicalMemoryManager:
    def __init__(self, shared_memory: LongTermMemory):
        self.shared_memory = shared_memory
        self.memory_hierarchy = {
            "session": {},      # Session-specific insights
            "engagement": {},   # Engagement-level patterns
            "client": {},       # Client-specific learning
            "global": {}        # Global industry patterns
        }
    
    def store_insight(self, insight: Dict[str, Any], level: str = "session"):
        """Store insight at appropriate hierarchy level"""
        insight_key = f"{level}_{insight['type']}_{int(time.time())}"
        
        # Add hierarchy metadata
        insight["hierarchy_level"] = level
        insight["storage_key"] = insight_key
        
        # Store in shared memory with hierarchy tags
        self.shared_memory.add(insight_key, insight, metadata={
            "hierarchy_level": level,
            "insight_type": insight["type"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Update local hierarchy tracking
        if level not in self.memory_hierarchy:
            self.memory_hierarchy[level] = {}
        self.memory_hierarchy[level][insight_key] = insight
    
    def retrieve_insights(self, query: str, levels: List[str] = None) -> List[Dict]:
        """Retrieve insights from specified hierarchy levels"""
        if levels is None:
            levels = ["session", "engagement", "client", "global"]
        
        all_insights = []
        for level in levels:
            level_insights = self.shared_memory.search(
                query=query,
                filter={"hierarchy_level": level},
                top_k=10
            )
            all_insights.extend(level_insights)
        
        # Sort by relevance and hierarchy priority
        return self._prioritize_insights(all_insights, levels)
```

#### **Learning Pattern Implementation**
```python
class AgentLearningSystem:
    def __init__(self, agent_name: str, shared_memory: LongTermMemory):
        self.agent_name = agent_name
        self.shared_memory = shared_memory
        self.learning_patterns = {}
    
    def record_success_pattern(self, task_context: Dict, result: Dict, feedback: Dict = None):
        """Record successful patterns for future learning"""
        pattern = {
            "agent": self.agent_name,
            "task_type": task_context.get("task_type"),
            "input_characteristics": self._extract_input_characteristics(task_context),
            "successful_approach": self._extract_approach(result),
            "outcome_quality": result.get("confidence", 0.0),
            "user_feedback": feedback,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory for future reference
        pattern_key = f"success_pattern_{self.agent_name}_{int(time.time())}"
        self.shared_memory.add(pattern_key, pattern, metadata={
            "pattern_type": "success",
            "agent": self.agent_name
        })
    
    def get_similar_patterns(self, current_context: Dict) -> List[Dict]:
        """Retrieve similar successful patterns for current context"""
        context_query = self._build_context_query(current_context)
        
        similar_patterns = self.shared_memory.search(
            query=context_query,
            filter={"pattern_type": "success", "agent": self.agent_name},
            top_k=5
        )
        
        return similar_patterns
    
    def apply_learned_patterns(self, current_task: Dict) -> Dict[str, Any]:
        """Apply learned patterns to current task"""
        similar_patterns = self.get_similar_patterns(current_task)
        
        if not similar_patterns:
            return {"strategy": "default", "confidence": 0.5}
        
        # Analyze patterns and generate strategy
        strategy = self._synthesize_strategy(similar_patterns, current_task)
        
        return {
            "strategy": strategy,
            "confidence": self._calculate_strategy_confidence(similar_patterns),
            "learned_patterns_applied": len(similar_patterns)
        }
```

---

## 🔍 **Testing and Validation**

### **Crew Testing Framework**

#### **Unit Testing for Crews**
```python
# File: tests/backend/crews/test_new_crew.py

import pytest
from unittest.mock import AsyncMock, Mock, patch
from backend.app.services.crewai_flows.crews.new_crew import NewAnalysisCrew

class TestNewAnalysisCrew:
    @pytest.fixture
    def mock_crewai_service(self):
        service = Mock()
        service.llm = Mock()
        service.shared_memory = Mock()
        return service
    
    @pytest.fixture  
    def new_crew(self, mock_crewai_service):
        return NewAnalysisCrew(mock_crewai_service)
    
    def test_crew_initialization(self, new_crew):
        """Test crew initializes correctly"""
        assert new_crew.crew_name == "NewAnalysisCrew"
        assert new_crew.llm is not None
        assert new_crew.shared_memory is not None
        assert new_crew.knowledge_base is not None
    
    def test_manager_agent_creation(self, new_crew):
        """Test manager agent is created with correct configuration"""
        manager = new_crew.create_manager_agent()
        
        assert manager.role == "New Analysis Manager"
        assert manager.manager is True
        assert manager.planning is True
        assert manager.delegation is True
        assert manager.max_delegation == 2
    
    def test_specialist_agents_creation(self, new_crew):
        """Test specialist agents are created correctly"""
        specialists = new_crew.create_specialist_agents()
        
        assert len(specialists) == 2
        assert all(agent.collaboration is True for agent in specialists)
        assert all(agent.delegation is False for agent in specialists)
    
    @pytest.mark.asyncio
    async def test_crew_execution(self, new_crew):
        """Test crew execution with mock data"""
        crew = new_crew.create_crew()
        
        # Mock crew execution
        mock_result = {
            "analysis_results": {"insight": "test_insight"},
            "confidence": 0.95,
            "execution_time": "30 seconds"
        }
        
        with patch.object(crew, 'kickoff', return_value=mock_result):
            result = crew.kickoff({
                "test_input": "sample_data",
                "session_context": {"session_id": "test_123"}
            })
            
            assert result["confidence"] >= 0.8
            assert "analysis_results" in result
    
    def test_memory_integration(self, new_crew):
        """Test shared memory integration"""
        # Test storing insights
        test_insights = {"pattern": "test_pattern", "confidence": 0.9}
        new_crew._store_insights(test_insights)
        
        # Verify memory interaction
        new_crew.shared_memory.add.assert_called_once()
        
        # Test retrieving insights
        new_crew.shared_memory.get.return_value = test_insights
        retrieved = new_crew._get_previous_insights("previous_crew")
        
        assert retrieved == test_insights
    
    def test_knowledge_base_usage(self, new_crew):
        """Test knowledge base integration"""
        # Mock knowledge base search
        new_crew.knowledge_base.search.return_value = [
            {"pattern": "known_pattern", "relevance": 0.9}
        ]
        
        # Test knowledge application
        patterns = new_crew.knowledge_base.search("test_query")
        assert len(patterns) > 0
        assert patterns[0]["relevance"] >= 0.9
```

#### **Integration Testing**
```python
# File: tests/backend/integration/test_new_crew_integration.py

class TestNewCrewIntegration:
    @pytest.mark.asyncio
    async def test_flow_integration(self, discovery_flow_service):
        """Test new crew integrates correctly with discovery flow"""
        # Initialize flow with new crew
        flow_state = await discovery_flow_service.initialize_with_new_crew()
        
        # Execute flow through new crew
        result = await discovery_flow_service.execute_new_analysis_crew(
            previous_result={"test": "data"}
        )
        
        # Verify integration
        assert result is not None
        assert flow_state.new_analysis_results is not None
    
    @pytest.mark.asyncio
    async def test_cross_crew_collaboration(self, discovery_flow_service):
        """Test collaboration with other crews"""
        # Execute previous crew
        previous_result = await discovery_flow_service.execute_previous_crew()
        
        # Execute new crew with previous insights
        new_result = await discovery_flow_service.execute_new_analysis_crew(
            previous_result=previous_result
        )
        
        # Verify collaboration
        assert "previous_insights" in new_result
        assert new_result["collaboration_effectiveness"] > 0.8
```

### **Performance Testing**

```python
# File: tests/backend/performance/test_new_crew_performance.py

class TestNewCrewPerformance:
    @pytest.mark.asyncio
    async def test_execution_performance(self, new_crew):
        """Test crew execution performance"""
        start_time = time.time()
        
        # Execute with test data
        result = await new_crew.execute_with_test_data(asset_count=1000)
        
        execution_time = time.time() - start_time
        
        # Performance assertions
        assert execution_time < 300  # 5 minutes max
        assert result["throughput"] > 3.0  # Assets per second
        assert result["memory_usage"] < 500  # MB
    
    @pytest.mark.asyncio
    async def test_scalability(self, new_crew):
        """Test crew scalability with different data sizes"""
        test_sizes = [100, 500, 1000, 2000]
        performance_results = {}
        
        for size in test_sizes:
            start_time = time.time()
            result = await new_crew.execute_with_test_data(asset_count=size)
            execution_time = time.time() - start_time
            
            performance_results[size] = {
                "execution_time": execution_time,
                "throughput": size / execution_time,
                "memory_usage": result.get("memory_usage", 0)
            }
        
        # Verify scalability characteristics
        for size in test_sizes:
            perf = performance_results[size]
            assert perf["throughput"] > 1.0  # Minimum throughput
            assert perf["memory_usage"] < size * 0.5  # Memory efficiency
```

---

## 🚀 **Deployment and Operations**

### **Environment Configuration**

#### **Development Environment Setup**
```python
# File: backend/app/core/config.py

class DiscoveryFlowSettings(BaseSettings):
    # CrewAI Configuration
    crewai_enabled: bool = True
    deepinfra_api_key: str = ""
    openai_api_key: str = ""
    
    # Memory Configuration
    memory_storage_type: str = "vector"
    memory_embedder_provider: str = "openai"
    memory_embedder_model: str = "text-embedding-3-small"
    
    # Knowledge Base Configuration
    knowledge_base_path: str = "backend/app/knowledge_bases"
    knowledge_base_refresh_interval: int = 3600  # 1 hour
    
    # Performance Configuration
    max_concurrent_crews: int = 10
    crew_timeout_seconds: int = 1800  # 30 minutes
    memory_max_size_mb: int = 1000
    
    # Monitoring Configuration
    enable_agent_monitoring: bool = True
    enable_performance_metrics: bool = True
    metrics_collection_interval: int = 30  # seconds
    
    class Config:
        env_prefix = "DISCOVERY_FLOW_"
```

#### **Production Configuration**
```yaml
# File: deployment/production.yaml

discovery_flow:
  crewai:
    enabled: true
    max_concurrent_crews: 50
    crew_timeout_seconds: 3600
    
  memory:
    storage_type: "vector"
    max_size_mb: 5000
    cleanup_interval: 7200  # 2 hours
    
  knowledge_bases:
    auto_refresh: true
    refresh_interval: 1800  # 30 minutes
    validation_enabled: true
    
  performance:
    monitoring_enabled: true
    alerting_enabled: true
    performance_thresholds:
      execution_time_max: 1800  # 30 minutes
      memory_usage_max: 2000   # MB
      error_rate_max: 0.05     # 5%
```

### **Monitoring and Observability**

#### **Agent Performance Monitoring**
```python
# File: backend/app/services/observability/agent_monitor.py

class AgentPerformanceMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
    
    def monitor_crew_execution(self, crew_name: str, execution_context: Dict):
        """Monitor crew execution performance"""
        start_time = time.time()
        
        try:
            # Execute with monitoring
            with self.metrics_collector.time_execution(crew_name):
                result = yield  # Actual execution happens here
                
            # Record success metrics
            self._record_success_metrics(crew_name, result, start_time)
            
        except Exception as e:
            # Record failure metrics
            self._record_failure_metrics(crew_name, e, start_time)
            raise
    
    def _record_success_metrics(self, crew_name: str, result: Dict, start_time: float):
        execution_time = time.time() - start_time
        
        metrics = {
            "crew_execution_time": execution_time,
            "crew_success_rate": 1.0,
            "result_confidence": result.get("confidence", 0.0),
            "memory_usage": result.get("memory_usage", 0),
            "collaboration_count": result.get("collaboration_events", 0)
        }
        
        self.metrics_collector.record_metrics(f"crew.{crew_name}", metrics)
        
        # Check performance thresholds
        if execution_time > 1800:  # 30 minutes
            self.alert_manager.send_alert(
                f"Crew {crew_name} execution time exceeded threshold",
                severity="warning"
            )
```

#### **Memory System Monitoring**
```python
class MemorySystemMonitor:
    def monitor_memory_usage(self, shared_memory: LongTermMemory):
        """Monitor shared memory system performance"""
        stats = {
            "total_insights": shared_memory.count(),
            "memory_size_mb": shared_memory.size_mb(),
            "retrieval_performance": self._measure_retrieval_performance(shared_memory),
            "storage_efficiency": self._calculate_storage_efficiency(shared_memory)
        }
        
        # Record metrics
        self.metrics_collector.record_metrics("memory_system", stats)
        
        # Optimize if needed
        if stats["memory_size_mb"] > 1000:
            self._trigger_memory_optimization(shared_memory)
    
    def _trigger_memory_optimization(self, shared_memory: LongTermMemory):
        """Optimize memory system performance"""
        # Compress old insights
        shared_memory.compress_old_insights(age_days=7)
        
        # Archive less relevant insights
        shared_memory.archive_low_relevance_insights(threshold=0.3)
        
        # Defragment vector storage
        shared_memory.defragment_storage()
```

---

## 📚 **Best Practices and Guidelines**

### **Code Quality Standards**

#### **Agent Development Guidelines**
1. **Single Responsibility**: Each agent should have one clear domain of expertise
2. **Collaboration Design**: Agents should actively collaborate and share insights
3. **Memory Integration**: Always use shared memory for cross-crew communication
4. **Error Handling**: Implement graceful fallback mechanisms
5. **Performance Awareness**: Monitor and optimize agent performance

#### **Tool Development Standards**
```python
# Best practice tool template
class WellDesignedTool(BaseTool):
    name: str = "descriptive_tool_name"
    description: str = "Clear description of what this tool does and when to use it"
    
    # Type hints for all parameters
    def _run(self, input_data: str) -> str:
        """
        Well-documented tool execution method.
        
        Args:
            input_data: Description of expected input format
            
        Returns:
            Structured JSON string with results and metadata
        """
        try:
            # 1. Validate input
            validated_input = self._validate_input(input_data)
            
            # 2. Execute core logic
            result = self._execute_core_logic(validated_input)
            
            # 3. Validate output
            validated_result = self._validate_output(result)
            
            # 4. Return structured output
            return json.dumps(validated_result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "tool": self.name,
                "timestamp": datetime.now().isoformat()
            })
```

### **Performance Optimization**

#### **Memory Optimization Strategies**
1. **Efficient Storage**: Use appropriate data structures for different insight types
2. **Memory Cleanup**: Implement regular cleanup of old or irrelevant insights
3. **Lazy Loading**: Load knowledge bases and memory content on demand
4. **Compression**: Compress large insights while maintaining accessibility

#### **Execution Optimization**
1. **Parallel Processing**: Enable parallel execution where possible
2. **Caching**: Cache frequently accessed patterns and insights
3. **Resource Management**: Monitor and optimize resource utilization
4. **Timeout Management**: Implement appropriate timeouts for agent tasks

### **Security and Privacy**

#### **Multi-Tenant Data Isolation**
```python
class SecureMemoryManager:
    def store_insight(self, insight: Dict, client_account_id: str):
        """Store insight with proper tenant isolation"""
        # Add client isolation metadata
        insight["client_account_id"] = client_account_id
        insight["access_level"] = "client_restricted"
        
        # Use tenant-specific storage key
        storage_key = f"client_{client_account_id}_{insight['type']}_{uuid.uuid4()}"
        
        # Store with access controls
        self.shared_memory.add(storage_key, insight, metadata={
            "client_account_id": client_account_id,
            "access_restrictions": ["client_scoped"]
        })
    
    def retrieve_insights(self, query: str, client_account_id: str):
        """Retrieve insights with tenant filtering"""
        return self.shared_memory.search(
            query=query,
            filter={"client_account_id": client_account_id},
            top_k=10
        )
```

---

This comprehensive development guide provides all the tools and patterns needed to extend the Discovery Flow with new crews, agents, and capabilities while maintaining the high-quality, agentic-first architecture. 