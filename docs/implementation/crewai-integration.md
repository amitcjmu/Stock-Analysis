# CrewAI Integration Implementation Guide

**Last Updated: August 18, 2025**

## Overview

The AI Modernize Migration Platform integrates 17 CrewAI agents across all migration phases. This guide documents the persistent agent architecture, memory systems, tool integration, and tenant-scoped agent management patterns used throughout the platform.

## Architecture Overview

### Persistent Multi-Tenant Agent Architecture

The platform implements **ADR-015: Persistent Multi-Tenant Agent Architecture** with the following key components:

1. **TenantScopedAgentPool** - Manages agent lifecycles per tenant
2. **ThreeTierMemoryManager** - Handles agent memory with tenant isolation
3. **ServiceRegistry** - Provides centralized tool and service access
4. **Flow Orchestration** - Coordinates multi-agent workflows

## Core Components

### 1. TenantScopedAgentPool

The main component for managing persistent agents across tenants:

```python
class TenantScopedAgentPool:
    """
    Manages CrewAI agents per (client_account_id, engagement_id) tuple.
    Implements persistent agent architecture with learning capabilities.
    """
    
    # Class-level storage for agent pools
    _pools: Dict[str, Dict[str, Agent]] = {}
    _pool_health: Dict[str, AgentHealth] = {}
    _pool_lock = threading.Lock()
    
    @classmethod
    def get_agent_pool(
        cls,
        client_account_id: str,
        engagement_id: str,
        force_refresh: bool = False
    ) -> Dict[str, Agent]:
        """
        Get or create agent pool for tenant.
        
        Args:
            client_account_id: Tenant client account UUID
            engagement_id: Engagement UUID within the client account
            force_refresh: Force recreation of agent pool
            
        Returns:
            Dictionary of agent_name -> Agent instances
        """
        pool_key = f"{client_account_id}:{engagement_id}"
        
        with cls._pool_lock:
            if pool_key not in cls._pools or force_refresh:
                logger.info(f"Creating agent pool for tenant: {pool_key}")
                cls._pools[pool_key] = cls._create_agent_pool(
                    client_account_id, engagement_id
                )
                cls._pool_health[pool_key] = AgentHealth(
                    is_healthy=True,
                    last_used=datetime.now()
                )
            
            # Update last used timestamp
            cls._pool_health[pool_key].last_used = datetime.now()
            return cls._pools[pool_key]
    
    @classmethod
    def _create_agent_pool(
        cls,
        client_account_id: str,
        engagement_id: str
    ) -> Dict[str, Agent]:
        """Create tenant-specific agent pool with memory and tools."""
        
        # Initialize memory manager for this tenant
        memory_manager = ThreeTierMemoryManager(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        # Create agents with tenant-scoped configuration
        agents = {}
        
        # Discovery Phase Agents (4 agents)
        agents.update(cls._create_discovery_agents(
            client_account_id, engagement_id, memory_manager
        ))
        
        # Assessment Phase Agents (2 agents)
        agents.update(cls._create_assessment_agents(
            client_account_id, engagement_id, memory_manager
        ))
        
        # Planning Phase Agents (1 agent)
        agents.update(cls._create_planning_agents(
            client_account_id, engagement_id, memory_manager
        ))
        
        # Learning Agents (3 agents)
        agents.update(cls._create_learning_agents(
            client_account_id, engagement_id, memory_manager
        ))
        
        # Observability Agents (3 agents)
        agents.update(cls._create_observability_agents(
            client_account_id, engagement_id, memory_manager
        ))
        
        return agents
```

### 2. Agent Creation Patterns

**Discovery Phase Agents:**
```python
@classmethod
def _create_discovery_agents(
    cls,
    client_account_id: str,
    engagement_id: str,
    memory_manager: ThreeTierMemoryManager
) -> Dict[str, Agent]:
    """Create discovery phase agents."""
    
    # Get tenant-scoped tools
    asset_tools = create_asset_creation_tools(client_account_id, engagement_id)
    validation_tools = create_data_validation_tools(client_account_id, engagement_id)
    dependency_tools = create_dependency_analysis_tools(client_account_id, engagement_id)
    
    agents = {
        "asset_discovery_agent": Agent(
            role="Asset Discovery Specialist",
            goal="Discover and catalog cloud infrastructure assets with high accuracy",
            backstory="""You are an expert in cloud infrastructure discovery with deep 
            knowledge of AWS, Azure, and GCP services. You excel at identifying 
            dependencies and relationships between resources.""",
            memory=memory_manager.get_agent_memory("asset_discovery"),
            tools=asset_tools + validation_tools,
            verbose=True,
            allow_delegation=False,
            llm=get_tenant_llm(client_account_id, engagement_id)
        ),
        
        "dependency_analysis_agent": Agent(
            role="Dependency Analysis Expert",
            goal="Map complex dependencies between discovered assets",
            backstory="""You specialize in understanding intricate relationships 
            between cloud resources, identifying critical paths and potential 
            migration blockers.""",
            memory=memory_manager.get_agent_memory("dependency_analysis"),
            tools=dependency_tools + asset_tools,
            verbose=True,
            allow_delegation=False,
            llm=get_tenant_llm(client_account_id, engagement_id)
        ),
        
        "data_validation_agent": Agent(
            role="Data Quality Assurance Specialist",
            goal="Ensure data accuracy and completeness throughout discovery",
            backstory="""You are meticulous about data quality, with expertise in 
            validating cloud resource data and identifying inconsistencies.""",
            memory=memory_manager.get_agent_memory("data_validation"),
            tools=validation_tools + asset_tools,
            verbose=True,
            allow_delegation=False,
            llm=get_tenant_llm(client_account_id, engagement_id)
        ),
        
        "field_mapping_agent": Agent(
            role="Field Mapping Intelligence Specialist",
            goal="Intelligently map data fields with high confidence",
            backstory="""You excel at understanding data schemas and creating 
            accurate field mappings between different data sources.""",
            memory=memory_manager.get_agent_memory("field_mapping"),
            tools=[MappingConfidenceTool(client_account_id, engagement_id)],
            verbose=True,
            allow_delegation=False,
            llm=get_tenant_llm(client_account_id, engagement_id)
        )
    }
    
    return agents
```

**Assessment Phase Agents:**
```python
@classmethod
def _create_assessment_agents(
    cls,
    client_account_id: str,
    engagement_id: str,
    memory_manager: ThreeTierMemoryManager
) -> Dict[str, Agent]:
    """Create assessment phase agents."""
    
    # Get assessment-specific tools
    intelligence_tools = get_asset_intelligence_tools(client_account_id, engagement_id)
    
    agents = {
        "modernization_agent": Agent(
            role="Cloud Modernization Strategist",
            goal="Analyze applications for cloud modernization opportunities",
            backstory="""You are an expert in cloud-native architectures and 
            modernization strategies, capable of identifying the best approach 
            for migrating legacy applications.""",
            memory=memory_manager.get_agent_memory("modernization"),
            tools=intelligence_tools,
            verbose=True,
            allow_delegation=True,
            llm=get_tenant_llm(client_account_id, engagement_id)
        ),
        
        "business_value_agent": Agent(
            role="Business Value Assessment Expert",
            goal="Calculate business value and ROI for migration scenarios",
            backstory="""You specialize in business case development for cloud 
            migrations, with expertise in cost modeling and value realization.""",
            memory=memory_manager.get_agent_memory("business_value"),
            tools=intelligence_tools,
            verbose=True,
            allow_delegation=True,
            llm=get_tenant_llm(client_account_id, engagement_id)
        )
    }
    
    return agents
```

### 3. Memory Management System

**Three-Tier Memory Architecture:**
```python
class ThreeTierMemoryManager:
    """
    Implements three-tier memory architecture for agent learning:
    L1: In-memory cache (fast access)
    L2: Redis distributed cache (shared across instances)
    L3: PostgreSQL persistent storage (long-term learning)
    """
    
    def __init__(self, client_account_id: str, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.memory_namespace = f"{client_account_id}:{engagement_id}"
        
        # Initialize memory layers
        self.l1_cache = {}  # In-memory
        self.l2_cache = get_redis_client()  # Redis
        self.l3_storage = get_memory_repository()  # PostgreSQL
    
    def get_agent_memory(self, agent_name: str) -> TenantScopedMemory:
        """Get tenant-scoped memory instance for agent."""
        return TenantScopedMemory(
            namespace=f"{self.memory_namespace}:{agent_name}",
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            l1_cache=self.l1_cache,
            l2_cache=self.l2_cache,
            l3_storage=self.l3_storage
        )
```

**Tenant-Scoped Memory Implementation:**
```python
class TenantScopedMemory:
    """Memory implementation with tenant isolation."""
    
    def __init__(
        self,
        namespace: str,
        client_account_id: str,
        engagement_id: str,
        l1_cache: Dict,
        l2_cache,
        l3_storage
    ):
        self.namespace = namespace
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.l3_storage = l3_storage
    
    async def store(self, key: str, value: Any, tier: str = "all"):
        """Store memory with tenant isolation."""
        tenant_key = f"{self.namespace}:{key}"
        
        if tier in ["all", "l1"]:
            self.l1_cache[tenant_key] = value
        
        if tier in ["all", "l2"]:
            await self.l2_cache.set(tenant_key, json.dumps(value), ex=3600)
        
        if tier in ["all", "l3"]:
            await self.l3_storage.store_memory(
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
                agent_name=self.namespace.split(":")[-1],
                key=key,
                value=value
            )
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve memory with tier fallback."""
        tenant_key = f"{self.namespace}:{key}"
        
        # Try L1 cache first
        if tenant_key in self.l1_cache:
            return self.l1_cache[tenant_key]
        
        # Try L2 cache
        l2_value = await self.l2_cache.get(tenant_key)
        if l2_value:
            value = json.loads(l2_value)
            self.l1_cache[tenant_key] = value  # Promote to L1
            return value
        
        # Try L3 storage
        l3_value = await self.l3_storage.retrieve_memory(
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            agent_name=self.namespace.split(":")[-1],
            key=key
        )
        
        if l3_value:
            # Promote to higher tiers
            await self.store(key, l3_value, tier="l1")
            await self.store(key, l3_value, tier="l2")
            return l3_value
        
        return None
```

## Tool Integration

### 1. Tool Creation Patterns

**Asset Creation Tools:**
```python
def create_asset_creation_tools(
    client_account_id: str,
    engagement_id: str
) -> List[Tool]:
    """Create tenant-scoped asset creation tools."""
    
    @tool("create_asset")
    async def create_asset_tool(
        asset_data: str
    ) -> str:
        """Create a new asset with tenant isolation."""
        try:
            # Parse asset data
            asset_info = json.loads(asset_data)
            
            # Add tenant context
            asset_info["client_account_id"] = client_account_id
            asset_info["engagement_id"] = engagement_id
            
            # Create asset through service layer
            asset_service = AssetService()
            result = await asset_service.create_asset(asset_info)
            
            return json.dumps({
                "success": True,
                "asset_id": str(result.id),
                "message": f"Asset '{result.name}' created successfully"
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    @tool("update_asset")
    async def update_asset_tool(
        asset_id: str,
        updates: str
    ) -> str:
        """Update asset with tenant validation."""
        try:
            update_data = json.loads(updates)
            
            # Validate asset belongs to tenant
            asset_service = AssetService()
            asset = await asset_service.get_asset(
                asset_id=asset_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            
            if not asset:
                return json.dumps({
                    "success": False,
                    "error": "Asset not found or access denied"
                })
            
            result = await asset_service.update_asset(asset_id, update_data)
            
            return json.dumps({
                "success": True,
                "message": f"Asset updated successfully"
            })
            
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    return [create_asset_tool, update_asset_tool]
```

**Data Validation Tools:**
```python
def create_data_validation_tools(
    client_account_id: str,
    engagement_id: str
) -> List[Tool]:
    """Create data validation tools with tenant scope."""
    
    @tool("validate_asset_data")
    async def validate_asset_data_tool(asset_data: str) -> str:
        """Validate asset data for quality and completeness."""
        try:
            data = json.loads(asset_data)
            
            validation_service = DataValidationService(
                client_account_id=client_account_id,
                engagement_id=engagement_id
            )
            
            result = await validation_service.validate_asset(data)
            
            return json.dumps({
                "is_valid": result.is_valid,
                "score": result.quality_score,
                "issues": result.validation_issues,
                "suggestions": result.improvement_suggestions
            })
            
        except Exception as e:
            return json.dumps({
                "is_valid": False,
                "error": str(e)
            })
    
    return [validate_asset_data_tool]
```

### 2. Service Registry Integration

**Centralized Tool Access:**
```python
class ServiceRegistry:
    """Centralized registry for tools and services."""
    
    def __init__(self):
        self._tools = {}
        self._services = {}
    
    def register_tool(
        self,
        name: str,
        tool_factory: Callable[[str, str], List[Tool]]
    ):
        """Register a tool factory."""
        self._tools[name] = tool_factory
    
    def get_tools_for_tenant(
        self,
        tool_names: List[str],
        client_account_id: str,
        engagement_id: str
    ) -> List[Tool]:
        """Get tools configured for specific tenant."""
        tools = []
        
        for tool_name in tool_names:
            if tool_name in self._tools:
                tenant_tools = self._tools[tool_name](
                    client_account_id, engagement_id
                )
                tools.extend(tenant_tools)
        
        return tools

# Usage in agent creation
service_registry = ServiceRegistry()
service_registry.register_tool("asset_creation", create_asset_creation_tools)
service_registry.register_tool("data_validation", create_data_validation_tools)

# Get tools for agent
discovery_tools = service_registry.get_tools_for_tenant(
    ["asset_creation", "data_validation"],
    client_account_id,
    engagement_id
)
```

## Flow Orchestration

### 1. Crew Creation and Execution

**Discovery Flow Crew:**
```python
class UnifiedDiscoveryFlow:
    """Orchestrates discovery phase using CrewAI agents."""
    
    def __init__(
        self,
        client_account_id: str,
        engagement_id: str,
        flow_id: str
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_id = flow_id
        
        # Get persistent agent pool
        self.agents = TenantScopedAgentPool.get_agent_pool(
            client_account_id, engagement_id
        )
    
    async def execute_discovery(self, data_import_id: str) -> Dict[str, Any]:
        """Execute discovery flow with agent crew."""
        
        # Create tasks for discovery
        tasks = self._create_discovery_tasks(data_import_id)
        
        # Create crew with persistent agents
        crew = Crew(
            agents=[
                self.agents["asset_discovery_agent"],
                self.agents["dependency_analysis_agent"],
                self.agents["data_validation_agent"],
                self.agents["field_mapping_agent"]
            ],
            tasks=tasks,
            verbose=True,
            process=Process.sequential,
            memory=True,
            embedder={
                "provider": "deepinfra",
                "config": {
                    "model": "BAAI/bge-base-en-v1.5",
                    "api_key": os.getenv("DEEPINFRA_API_KEY")
                }
            }
        )
        
        # Execute crew with error handling
        try:
            result = await crew.kickoff_async()
            
            # Store execution results
            await self._store_execution_results(result)
            
            return {
                "success": True,
                "flow_id": self.flow_id,
                "results": result.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Discovery flow execution failed: {e}")
            await self._handle_execution_error(e)
            raise
    
    def _create_discovery_tasks(self, data_import_id: str) -> List[Task]:
        """Create discovery tasks with tenant context."""
        
        tasks = [
            Task(
                description=f"""
                Discover and catalog assets from data import {data_import_id}.
                Focus on accuracy and completeness of asset attributes.
                """,
                agent=self.agents["asset_discovery_agent"],
                expected_output="Comprehensive list of discovered assets with metadata"
            ),
            
            Task(
                description="""
                Analyze dependencies between discovered assets.
                Identify critical paths and potential migration blockers.
                """,
                agent=self.agents["dependency_analysis_agent"],
                expected_output="Dependency graph with risk assessment"
            ),
            
            Task(
                description="""
                Validate data quality and completeness.
                Identify data quality issues and suggest improvements.
                """,
                agent=self.agents["data_validation_agent"],
                expected_output="Data quality report with recommendations"
            ),
            
            Task(
                description="""
                Create intelligent field mappings with confidence scores.
                Learn from previous mappings to improve accuracy.
                """,
                agent=self.agents["field_mapping_agent"],
                expected_output="Field mapping configuration with confidence scores"
            )
        ]
        
        return tasks
```

### 2. State Management Integration

**Flow State Persistence:**
```python
class CrewAIFlowExecutor:
    """Manages CrewAI flow execution with state persistence."""
    
    async def execute_with_state_management(
        self,
        flow_id: str,
        client_account_id: str,
        engagement_id: str,
        flow_type: str
    ) -> Dict[str, Any]:
        """Execute flow with comprehensive state management."""
        
        # Initialize state manager
        state_manager = PostgresFlowStateStore(
            client_account_id=client_account_id,
            engagement_id=engagement_id
        )
        
        try:
            # Update state to running
            await state_manager.update_flow_state(
                flow_id=flow_id,
                status="running",
                metadata={"start_time": datetime.now().isoformat()}
            )
            
            # Get flow executor based on type
            if flow_type == "discovery":
                executor = UnifiedDiscoveryFlow(
                    client_account_id, engagement_id, flow_id
                )
                result = await executor.execute_discovery(data_import_id)
            elif flow_type == "assessment":
                executor = UnifiedAssessmentFlow(
                    client_account_id, engagement_id, flow_id
                )
                result = await executor.execute_assessment()
            else:
                raise ValueError(f"Unknown flow type: {flow_type}")
            
            # Update state to completed
            await state_manager.update_flow_state(
                flow_id=flow_id,
                status="completed",
                result=result,
                metadata={
                    "end_time": datetime.now().isoformat(),
                    "execution_duration": (datetime.now() - start_time).total_seconds()
                }
            )
            
            return result
            
        except Exception as e:
            # Update state to failed
            await state_manager.update_flow_state(
                flow_id=flow_id,
                status="failed",
                error=str(e),
                metadata={"error_time": datetime.now().isoformat()}
            )
            raise
```

## Performance Optimization

### 1. Agent Pool Management

**Health Monitoring:**
```python
@dataclass
class AgentHealth:
    """Health status tracking for agent pools."""
    is_healthy: bool
    memory_status: bool = True
    last_used: Optional[datetime] = None
    memory_usage_mb: float = 0.0
    error_count: int = 0
    
    def update_memory_usage(self):
        """Update memory usage if psutil available."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            self.memory_usage_mb = process.memory_info().rss / 1024 / 1024

class TenantScopedAgentPool:
    @classmethod
    def cleanup_stale_pools(cls, max_idle_hours: int = 24):
        """Clean up pools that haven't been used recently."""
        cutoff_time = datetime.now() - timedelta(hours=max_idle_hours)
        
        with cls._pool_lock:
            stale_keys = []
            for pool_key, health in cls._pool_health.items():
                if health.last_used and health.last_used < cutoff_time:
                    stale_keys.append(pool_key)
            
            for key in stale_keys:
                logger.info(f"Cleaning up stale agent pool: {key}")
                del cls._pools[key]
                del cls._pool_health[key]
    
    @classmethod
    def get_pool_statistics(cls) -> Dict[str, Any]:
        """Get statistics about agent pools."""
        with cls._pool_lock:
            stats = {
                "total_pools": len(cls._pools),
                "healthy_pools": sum(1 for h in cls._pool_health.values() if h.is_healthy),
                "average_memory_mb": sum(h.memory_usage_mb for h in cls._pool_health.values()) / len(cls._pool_health) if cls._pool_health else 0,
                "pools": {}
            }
            
            for pool_key, health in cls._pool_health.items():
                health.update_memory_usage()
                stats["pools"][pool_key] = {
                    "is_healthy": health.is_healthy,
                    "last_used": health.last_used.isoformat() if health.last_used else None,
                    "memory_mb": health.memory_usage_mb,
                    "error_count": health.error_count
                }
            
            return stats
```

### 2. Memory Optimization

**Lazy Loading and Caching:**
```python
class OptimizedMemoryManager:
    """Memory manager with performance optimizations."""
    
    def __init__(self, client_account_id: str, engagement_id: str):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self._memory_cache = {}
        self._cache_lock = asyncio.Lock()
    
    async def get_agent_memory(self, agent_name: str) -> TenantScopedMemory:
        """Get memory with caching and lazy loading."""
        cache_key = f"{self.client_account_id}:{self.engagement_id}:{agent_name}"
        
        async with self._cache_lock:
            if cache_key not in self._memory_cache:
                self._memory_cache[cache_key] = TenantScopedMemory(
                    namespace=cache_key,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                    l1_cache=self._get_l1_cache(),
                    l2_cache=self._get_l2_cache(),
                    l3_storage=self._get_l3_storage()
                )
            
            return self._memory_cache[cache_key]
```

## Error Handling and Resilience

### 1. Graceful Degradation

**Fallback Patterns:**
```python
class ResilientAgentPool:
    """Agent pool with fallback capabilities."""
    
    @classmethod
    async def get_agent_with_fallback(
        cls,
        agent_name: str,
        client_account_id: str,
        engagement_id: str
    ) -> Agent:
        """Get agent with fallback to basic configuration."""
        
        try:
            # Try to get from persistent pool
            pool = cls.get_agent_pool(client_account_id, engagement_id)
            return pool[agent_name]
            
        except Exception as e:
            logger.warning(f"Failed to get persistent agent, using fallback: {e}")
            
            # Fallback to basic agent configuration
            return Agent(
                role=f"Fallback {agent_name}",
                goal="Perform basic tasks with limited functionality",
                backstory="Basic agent configuration without persistent memory",
                memory=None,  # No memory in fallback mode
                tools=[],     # Basic tool set
                verbose=False,
                llm=get_default_llm()
            )
```

### 2. Circuit Breaker Pattern

**Agent Health Monitoring:**
```python
class AgentCircuitBreaker:
    """Circuit breaker for agent operations."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
    
    async def call_agent(self, agent: Agent, task_input: str) -> str:
        """Execute agent task with circuit breaker protection."""
        
        if self.state == "open":
            if (datetime.now() - self.last_failure_time).total_seconds() > self.timeout_seconds:
                self.state = "half-open"
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await agent.execute_task(task_input)
            
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            raise
```

## Testing CrewAI Integration

### 1. Agent Testing Patterns

**Unit Tests for Agents:**
```python
@pytest.mark.asyncio
async def test_agent_creation():
    """Test agent creation with tenant isolation."""
    client_id = "11111111-1111-1111-1111-111111111111"
    engagement_id = "22222222-2222-2222-2222-222222222222"
    
    # Get agent pool
    pool = TenantScopedAgentPool.get_agent_pool(client_id, engagement_id)
    
    # Verify agents are created
    assert "asset_discovery_agent" in pool
    assert "dependency_analysis_agent" in pool
    
    # Verify tenant isolation
    agent = pool["asset_discovery_agent"]
    assert hasattr(agent.memory, "client_account_id")
    assert agent.memory.client_account_id == client_id

@pytest.mark.asyncio
async def test_agent_memory_isolation():
    """Test that agent memory is isolated between tenants."""
    tenant1_id = "11111111-1111-1111-1111-111111111111"
    tenant2_id = "33333333-3333-3333-3333-333333333333"
    
    # Get pools for different tenants
    pool1 = TenantScopedAgentPool.get_agent_pool(tenant1_id, "engagement1")
    pool2 = TenantScopedAgentPool.get_agent_pool(tenant2_id, "engagement2")
    
    # Store memory in each agent
    await pool1["asset_discovery_agent"].memory.store("test_key", "tenant1_value")
    await pool2["asset_discovery_agent"].memory.store("test_key", "tenant2_value")
    
    # Verify isolation
    value1 = await pool1["asset_discovery_agent"].memory.retrieve("test_key")
    value2 = await pool2["asset_discovery_agent"].memory.retrieve("test_key")
    
    assert value1 == "tenant1_value"
    assert value2 == "tenant2_value"
```

### 2. Integration Testing

**Flow Execution Tests:**
```python
@pytest.mark.asyncio
async def test_discovery_flow_execution():
    """Test complete discovery flow execution."""
    
    # Setup test data
    test_context = {
        "client_account_id": "11111111-1111-1111-1111-111111111111",
        "engagement_id": "22222222-2222-2222-2222-222222222222",
        "flow_id": str(uuid.uuid4())
    }
    
    # Create discovery flow
    flow = UnifiedDiscoveryFlow(**test_context)
    
    # Mock data import
    data_import_id = str(uuid.uuid4())
    
    # Execute flow
    result = await flow.execute_discovery(data_import_id)
    
    # Verify results
    assert result["success"] is True
    assert "flow_id" in result
    assert "results" in result
```

## Monitoring and Observability

### 1. Agent Performance Metrics

**Metrics Collection:**
```python
class AgentMetricsCollector:
    """Collect performance metrics for agents."""
    
    @staticmethod
    async def collect_agent_metrics(
        agent_name: str,
        client_account_id: str,
        engagement_id: str,
        execution_time: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Collect and store agent execution metrics."""
        
        metrics = {
            "agent_name": agent_name,
            "client_account_id": client_account_id,
            "engagement_id": engagement_id,
            "execution_time_seconds": execution_time,
            "success": success,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in metrics database
        await store_agent_metrics(metrics)
        
        # Send to monitoring system
        await send_to_monitoring(metrics)
```

### 2. Health Checks

**Agent Health Endpoints:**
```python
@router.get("/agents/health")
async def get_agent_health():
    """Get health status of all agent pools."""
    
    stats = TenantScopedAgentPool.get_pool_statistics()
    
    return {
        "status": "healthy" if stats["healthy_pools"] == stats["total_pools"] else "degraded",
        "statistics": stats,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/agents/cleanup")
async def cleanup_stale_pools():
    """Clean up stale agent pools."""
    
    TenantScopedAgentPool.cleanup_stale_pools()
    
    return {
        "message": "Stale agent pools cleaned up",
        "timestamp": datetime.now().isoformat()
    }
```

This CrewAI integration provides a robust, scalable, and tenant-isolated agent architecture that supports the platform's 17 operational AI agents across all migration phases while maintaining performance, reliability, and learning capabilities.