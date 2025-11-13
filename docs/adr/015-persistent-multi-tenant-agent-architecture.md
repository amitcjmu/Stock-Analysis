# ADR-015: Persistent Multi-Tenant Agent Architecture

## Status
Proposed (2025-08-07)

**HISTORICAL CONTEXT NOTE (October 2025)**: Code examples in this ADR predate ADR-024 and show `memory=True`. As of October 2025, CrewAI memory is disabled (`memory=False`) and TenantMemoryManager is used for all agent learning. See [ADR-024](024-tenant-memory-manager-architecture.md) for current memory architecture.

## Context

The AI Modernize Migration Platform currently instantiates CrewAI agents **per flow execution** rather than maintaining persistent agent instances per multi-tenant context. This pattern emerged accidentally due to technical issues rather than intentional architectural design, creating significant limitations in agent intelligence and learning capabilities.

### Current Problem: Accidental Architecture

#### Root Cause Analysis
1. **Memory System Disabled**: CrewAI agent memory was globally disabled due to technical bugs:
   ```python
   # backend/app/services/crewai_flows/crews/__init__.py
   def patch_crew_init():
       kwargs['memory'] = False  # Force disable memory
   ```

2. **API Compatibility Issues**: 
   - `APIStatusError.__init__() missing 2 required keyword-only arguments: 'response' and 'body'`
   - Performance degradation (40+ second execution times)
   - Dependency version mismatches between CrewAI and OpenAI libraries

3. **Consequence**: Without memory, agent persistence became irrelevant, leading to "agent per execution" pattern

#### Current Implementation Pattern
```python
# In execution_engine_crew.py (line 117-120) - PROBLEMATIC PATTERN
async with AsyncSessionLocal() as db:
    crewai_service = CrewAIFlowService(db)  # New agent instances every time
```

**Result**: Agents are recreated for every flow execution, losing all accumulated learning and expertise.

### Problems with Current Architecture

#### 1. **No Agent Learning or Memory**
- Agents cannot improve through experience
- Each execution starts from zero knowledge
- Previously discovered patterns are lost
- User corrections and feedback don't accumulate

#### 2. **Performance Overhead**
- Agent initialization overhead for every execution
- Redundant CrewAI service instantiation
- Repeated model loading and setup costs
- No caching of agent-specific optimizations

#### 3. **Inconsistent Agent Personalities**
- Agents have no persistent characteristics or expertise
- No specialization development over time
- Loss of agent-specific reasoning patterns
- Inability to maintain conversational context

#### 4. **Violation of Documented Architecture**
Per **ADR-008: Agentic Intelligence System Architecture**:
- "ALL intelligence comes from CrewAI agents"
- Documents sophisticated 3-tier memory architecture
- Emphasizes learning and pattern discovery capabilities
- **Current implementation prevents all of these benefits**

#### 5. **Multi-Tenant Intelligence Gaps**
- Cannot develop client-specific expertise
- No engagement-specific learning patterns
- Missed opportunities for tenant-scoped optimization
- Inability to share validated patterns within tenant boundary

### Evidence of Existing Multi-Tenant Memory Infrastructure

The platform already has sophisticated multi-tenant memory systems that are **unused** due to current architecture:

```python
# ThreeTierMemoryManager - ALREADY EXISTS BUT UNUSED
class ThreeTierMemoryManager:
    def __init__(self, client_account_id: uuid.UUID, engagement_id: uuid.UUID):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        # Multi-tenant memory scoping already implemented
```

## Decision

Implement **Persistent Multi-Tenant Agent Architecture** where CrewAI agents are maintained as singletons per `(client_account_id, engagement_id)` tuple, enabling true agent learning and intelligence accumulation.

### Core Architectural Principles

1. **Agent Persistence**: Maintain long-lived agent instances per tenant context
2. **Memory-Enabled Learning**: Fix memory bugs and re-enable CrewAI memory systems
3. **Multi-Tenant Isolation**: Agents scoped to specific client/engagement boundaries
4. **Intelligence Accumulation**: Enable agents to build expertise over time
5. **Performance Optimization**: Eliminate redundant agent initialization

### Key Implementation Components

#### 1. **Tenant-Scoped Agent Pool**
```python
class TenantScopedAgentPool:
    """Maintains persistent agents per tenant context"""
    
    _agent_pools: Dict[Tuple[str, str], Dict[str, Any]] = {}  # (client_id, engagement_id) -> agent_pool
    
    @classmethod
    async def get_or_create_agent(
        cls, 
        client_id: str, 
        engagement_id: str, 
        agent_type: str
    ) -> CrewAIAgent:
        """Get existing agent or create new one with full memory integration"""
        tenant_key = (client_id, engagement_id)
        
        if tenant_key not in cls._agent_pools:
            cls._agent_pools[tenant_key] = {}
            
        if agent_type not in cls._agent_pools[tenant_key]:
            # Initialize agent with persistent memory
            memory_manager = ThreeTierMemoryManager(client_id, engagement_id)
            agent = await cls._create_agent_with_memory(agent_type, memory_manager)
            cls._agent_pools[tenant_key][agent_type] = agent
            
        return cls._agent_pools[tenant_key][agent_type]
    
    @classmethod
    async def initialize_tenant_pool(
        cls, 
        client_id: str, 
        engagement_id: str
    ) -> Dict[str, CrewAIAgent]:
        """Pre-initialize common agents for a tenant"""
        required_agents = [
            "data_analyst", 
            "field_mapper", 
            "quality_assessor",
            "business_value_analyst",
            "risk_assessment_agent",
            "pattern_discovery_agent"
        ]
        
        pool = {}
        for agent_type in required_agents:
            pool[agent_type] = await cls.get_or_create_agent(client_id, engagement_id, agent_type)
            await pool[agent_type].warm_up()  # Load memory and prepare for execution
        
        return pool
```

#### 2. **Memory-Enabled Agent Factory**
```python
class MemoryEnabledAgentFactory:
    """Creates agents with full memory integration"""
    
    @staticmethod
    async def create_agent_with_memory(
        agent_type: str, 
        memory_manager: ThreeTierMemoryManager
    ) -> CrewAIAgent:
        """Create agent with memory bugs fixed"""
        
        # Fix 1: Resolve API compatibility issues
        memory_config = {
            'provider': 'DeepInfra',
            'config': {
                'response_format': 'fixed',  # Fix APIStatusError
                'timeout': 30,
                'max_retries': 3
            }
        }
        
        # Fix 2: Enable memory with proper error handling
        # NOTE (October 2025): This code is historical. Current implementation uses memory=False
        # and TenantMemoryManager for agent learning. See ADR-024 for details.
        agent = CrewAI Agent(
            role=AGENT_ROLES[agent_type],
            goal=AGENT_GOALS[agent_type],
            backstory=AGENT_BACKSTORIES[agent_type],
            memory=True,  # HISTORICAL: Changed to False in October 2025 per ADR-024
            memory_config=memory_config,
            tools=get_agent_tools(agent_type)
        )
        
        # Fix 3: Integrate with three-tier memory system
        agent.memory_manager = memory_manager
        await agent.load_persistent_patterns()
        
        return agent
```

#### 3. **Flow Initialization Redesign**
```python
async def initialize_flow_with_persistent_agents(
    flow_id: str, 
    context: RequestContext
) -> bool:
    """Proper initialization with persistent agents"""
    
    try:
        logger.info(f"🔄 Initializing flow {flow_id} with persistent agents")
        
        # 1. Ensure agent pool exists for this tenant
        agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(
            context.client_account_id, 
            context.engagement_id
        )
        
        # 2. Validate agent memory systems are working
        for agent_type, agent in agent_pool.items():
            memory_status = await agent.validate_memory_system()
            if not memory_status.is_healthy:
                logger.error(f"❌ Agent {agent_type} memory system unhealthy: {memory_status.error}")
                return False
        
        # 3. Validate CrewAI flow state consistency
        crewai_state = await validate_crewai_flow_state(flow_id, context)
        if not crewai_state.is_valid:
            logger.error(f"❌ CrewAI flow state validation failed: {crewai_state.errors}")
            return False
            
        # 4. Initialize flow-specific resources and context
        workspace_initialized = await setup_flow_workspace(flow_id, context, agent_pool)
        if not workspace_initialized:
            logger.error(f"❌ Flow workspace initialization failed")
            return False
            
        # 5. Warm up agents with flow context
        for agent in agent_pool.values():
            await agent.set_flow_context(flow_id, context)
            
        logger.info(f"✅ Flow {flow_id} initialized successfully with {len(agent_pool)} persistent agents")
        return True
        
    except Exception as e:
        logger.error(f"❌ Flow initialization failed: {e}")
        return False
```

#### 4. **Enhanced Status Transition Logic**
```python
# In unified_discovery.py execute endpoint - ENHANCED VERSION
async def execute_flow_with_proper_initialization(
    flow_id: str,
    discovery_flow: DiscoveryFlow,
    context: RequestContext,
    db: AsyncSession
):
    """Execute flow with proper initialization and status transitions"""
    
    # Update status based on proper initialization
    if discovery_flow.status == "initializing":
        logger.info(f"🔄 Performing proper initialization for flow {flow_id}")
        
        initialization_success = await initialize_flow_with_persistent_agents(flow_id, context)
        
        if initialization_success:
            logger.info(f"✅ Flow {flow_id} initialization successful - transitioning to running")
            discovery_flow.status = "running"
            await db.commit()
        else:
            logger.error(f"❌ Flow {flow_id} initialization failed - transitioning to failed")
            discovery_flow.status = "failed"
            await db.commit()
            return {
                "success": False,
                "flow_id": flow_id,
                "message": "Flow initialization failed",
                "details": {
                    "error": "Agent pool or memory system initialization failed",
                    "recommended_action": "Check agent memory system health and retry"
                }
            }
```

## Consequences

### Positive Consequences

#### 1. **True Agent Intelligence**
- Agents accumulate expertise and learning over time
- Memory systems enable pattern discovery and application
- Agent personalities and specializations develop naturally
- Evidence-based reasoning improves with experience

#### 2. **Performance Improvements**
- Eliminate agent initialization overhead (estimated 60-80% reduction in startup time)
- Memory caching and optimization at agent level
- Reduced API calls through intelligent caching
- Parallel agent execution with persistent state

#### 3. **Multi-Tenant Learning Benefits**
- Client-specific agent expertise development
- Engagement-scoped pattern discovery
- Validated pattern sharing within tenant boundaries
- Tenant-specific optimization and adaptation

#### 4. **Architectural Alignment**
- Fulfills vision from ADR-008: "ALL intelligence comes from CrewAI agents"
- Enables documented 3-tier memory architecture
- Aligns with sophisticated reasoning and learning goals
- Proper separation between tools and intelligence

#### 5. **Enhanced User Experience**
- Consistent agent personalities across sessions
- Improved suggestion quality through learning
- Reduced repetitive questions through memory
- Contextual awareness spanning multiple interactions

### Negative Consequences

#### 1. **Memory Resource Usage**
- Persistent agents consume more memory than per-execution pattern
- Need memory management and cleanup strategies
- Potential memory leaks if not properly managed
- Higher baseline resource requirements

#### 2. **Complexity Increase**
- More sophisticated agent lifecycle management
- Multi-tenant cleanup and isolation logic
- Memory debugging and monitoring requirements
- Potential threading/concurrency considerations

#### 3. **Migration Complexity**
- Need to fix existing memory system bugs
- Refactor existing agent instantiation patterns
- Update all flow execution paths
- Comprehensive testing of memory-enabled agents

#### 4. **Dependency on Memory System Health**
- Agent functionality depends on memory system reliability
- Need robust error handling and fallback mechanisms
- Memory corruption could affect multiple flows
- Backup and recovery strategies required

### Risks and Mitigations

#### Risk 1: Memory System Bugs
**Mitigation**: 
- Fix root cause API compatibility issues before implementation
- Comprehensive testing in isolated environments
- Graceful fallback to memory-disabled mode if needed
- Monitoring and alerting on memory system health

#### Risk 2: Resource Exhaustion
**Mitigation**:
- Implement agent pool size limits per tenant
- Memory usage monitoring and cleanup routines
- Agent hibernation for inactive tenants
- Configurable resource limits

#### Risk 3: Data Isolation Failures
**Mitigation**:
- Strict tenant boundary validation
- Memory encryption and access controls
- Audit logging for all agent memory access
- Regular security validation of tenant isolation

## Implementation Plan

### Phase 1: Memory System Stabilization (Week 1-2)
1. **Fix Memory Bugs**
   - Resolve APIStatusError compatibility issues
   - Update dependency versions and configurations
   - Implement proper error handling in memory systems

2. **Memory System Testing**
   - Isolated testing of ThreeTierMemoryManager
   - Performance benchmarking of memory operations
   - Tenant isolation validation

### Phase 2: Agent Pool Infrastructure (Week 3-4)
1. **Build TenantScopedAgentPool**
   - Implement singleton pattern with tenant scoping
   - Agent lifecycle management (create, warm-up, cleanup)
   - Memory integration and validation

2. **Agent Factory Enhancement**
   - Memory-enabled agent creation
   - Configuration management for different agent types
   - Error handling and fallback mechanisms

### Phase 3: Flow Integration (Week 5-6)
1. **Update Flow Initialization**
   - Implement proper initialization logic in unified_discovery.py
   - Status transition enhancements
   - Error handling and recovery mechanisms

2. **Refactor Agent Usage**
   - Update all flow execution paths to use persistent agents
   - Remove per-execution agent creation patterns
   - Integration testing across all flow types

### Phase 4: Production Deployment (Week 7-8)
1. **Monitoring and Observability**
   - Agent pool health monitoring
   - Memory usage dashboards
   - Performance metrics and alerting

2. **Migration and Validation**
   - Staged deployment with rollback capability
   - Comprehensive validation of agent behavior
   - User acceptance testing

## Success Metrics

### Technical Metrics
- **Agent Initialization Time**: Reduce from current ~3-5 seconds to <500ms for warm agents
- **Memory System Uptime**: 99.9% availability
- **Flow Execution Performance**: 30-50% improvement in overall flow execution time
- **Memory-Related Errors**: Zero `APIStatusError` incidents

### Intelligence Metrics
- **Agent Learning Effectiveness**: Pattern discovery rate >5 per week per active tenant
- **Suggestion Accuracy**: 15% improvement in agent suggestion acceptance rate
- **Contextual Awareness**: 90% reduction in repetitive agent questions
- **Agent Confidence Scores**: Trending upward over time per agent type

### Business Metrics
- **User Experience**: Improved flow completion times
- **System Reliability**: Reduced error rates in agent-driven processes
- **Operational Efficiency**: Lower support burden due to improved agent intelligence
- **Tenant Satisfaction**: Measurement of client-specific agent effectiveness

## Alternatives Considered

### Alternative 1: Enhanced Per-Execution Pattern
**Description**: Fix memory bugs but keep per-execution agent creation  
**Rejected Because**: Doesn't address learning continuity, performance overhead, or expertise accumulation

### Alternative 2: Global Agent Singletons
**Description**: Single agent pool shared across all tenants  
**Rejected Because**: Violates multi-tenant isolation, security concerns, no client-specific learning

### Alternative 3: Session-Scoped Agents
**Description**: Agents persist for user session duration only  
**Rejected Because**: Sessions are typically short, limited learning benefit, doesn't solve core problems

### Alternative 4: Microservice Agent Pool
**Description**: Separate service managing persistent agents  
**Rejected Because**: Adds complexity, network overhead, doesn't align with current architecture

## Validation Criteria

### Must-Have Requirements
- ✅ Agents persist across multiple flow executions within tenant scope
- ✅ Memory systems functional with zero APIStatusError incidents  
- ✅ Multi-tenant isolation maintained with audit trail
- ✅ Performance improvement demonstrated through benchmarking
- ✅ Learning capability validated through pattern accumulation

### Should-Have Requirements
- ✅ Agent pool size management and resource limits
- ✅ Graceful fallback to memory-disabled mode if needed
- ✅ Monitoring and observability for agent health
- ✅ Migration path from current architecture

### Could-Have Enhancements
- Cross-tenant pattern sharing (with privacy controls)
- Advanced agent specialization strategies
- Integration with external knowledge systems
- Agent performance analytics and optimization

## Related ADRs
- [ADR-008](008-agentic-intelligence-system-architecture.md) - Provides vision for agent-based intelligence
- [ADR-006](006-master-flow-orchestrator.md) - Flow orchestration framework supports agent integration
- [ADR-009](009-multi-tenant-architecture.md) - Multi-tenant isolation patterns apply to agents
- [ADR-003](003-postgresql-only-state-management.md) - PostgreSQL stores agent memory and patterns

## References
- Memory Architecture: `/docs/development/agentic-memory-architecture/01_architecture_overview.md`
- Agent Learning Analysis: `/docs/agents/AGENT_LEARNING_MEMORY_ANALYSIS.md`  
- CrewAI Critical Fixes: `/docs/development/CREWAI_CRITICAL_FIXES_APPLIED.md`
- Current Agent Registry: `/backend/app/services/agent_registry/`
- Memory Systems: `/backend/app/services/agentic_memory/`

---

**Decision Made By**: Platform Architecture Team  
**Date**: 2025-08-07  
**Implementation Target**: v1.8.0 - v1.9.0  
**Review Cycle**: Monthly during implementation, Quarterly after deployment