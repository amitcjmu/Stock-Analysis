# ADR-018: Service Registry for CrewAI Tools

## Status
Proposed (2025-01-13)

## Context

The AI Modernize Migration Platform's CrewAI tools currently create their own database sessions using `AsyncSessionLocal()`, which violates our orchestrator-first architectural pattern and creates significant risks for multi-tenant isolation and data integrity.

### Current Problem: Direct Database Access Pattern

#### Root Cause Analysis

The current tool implementation pattern directly violates core architectural principles:

```python
# backend/app/services/crewai_flows/tools/asset_creation_tool.py - PROBLEMATIC PATTERN
async def _arun(self, asset_data: Dict[str, Any]) -> str:
    async with AsyncSessionLocal() as db:  # ❌ Tool creates own session
        try:
            # Direct database operations in tool layer
            asset_service = AssetService(db)
            asset = await asset_service.create_asset(asset_data)
            await db.commit()  # ❌ Tool manages transactions
```

#### Architectural Violations

1. **Orchestrator-First Violation**: Tools bypass the master flow orchestrator's session management
2. **Multi-Tenant Risk**: Tools don't inherit tenant context from orchestrator session
3. **Transaction Boundary Issues**: Each tool creates isolated transactions, breaking atomicity
4. **No Centralized Audit**: Tool operations occur outside the main audit trail
5. **Testing Complexity**: Tools are tightly coupled to database infrastructure

#### Specific Issues Identified

- **Session Ownership Confusion**: Multiple sessions per execution break transactional consistency
- **Context Propagation Failure**: Tenant context (`client_account_id`, `engagement_id`) not reliably passed to tools
- **Audit Trail Gaps**: Tool operations not captured in the flow orchestration audit system
- **Error Handling Inconsistency**: Each tool implements its own error recovery patterns
- **Idempotency Violations**: No guarantee against duplicate operations during retries

### Evidence of Current Issues

```python
# From execution_engine_crew.py - Session Management Anti-Pattern
async def execute_crew(self, crew_config: Dict, context: RequestContext) -> Dict:
    async with AsyncSessionLocal() as db:  # Orchestrator session
        # ... orchestrator operations ...
        
        # Tools create ADDITIONAL sessions, breaking isolation
        tools = self._create_tools(crew_config)  # Each tool creates AsyncSessionLocal()
        
        # Result: Multiple concurrent sessions per execution
```

### Impact on ADR-015 Compliance

This pattern directly conflicts with **ADR-015: Persistent Multi-Tenant Agent Architecture**:

- **Agent Persistence**: Tools recreate database connections, preventing efficient agent reuse
- **Memory Integration**: Session fragmentation breaks agent memory system continuity
- **Multi-Tenant Isolation**: Tool sessions may not inherit proper tenant scoping
- **Intelligence Accumulation**: Audit gaps prevent learning from tool operation patterns

## Decision

Implement a **Service Registry Pattern** that enforces orchestrator-first session management and provides tools with injected services instead of direct database access.

### Core Architectural Principles

1. **Orchestrator Session Ownership**: Single database session per execution owned by the flow orchestrator
2. **Service Layer Abstraction**: Tools interact with business logic through service interfaces
3. **Dependency Injection**: Services injected into tools via registry pattern at execution time
4. **Centralized Audit Trail**: All tool operations flow through the orchestrator's audit system
5. **Multi-Tenant Context Propagation**: Tenant context flows from orchestrator through services to tools

### Key Implementation Components

#### 1. Service Registry Architecture

```python
# backend/app/services/service_registry.py
from typing import Dict, Type, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext

class ServiceRegistry:
    """Per-execution registry that manages service lifecycle and dependency injection"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db  # Borrowed from orchestrator, never commit/close
        self.context = context  # Multi-tenant context propagation
        self._services: Dict[Type, Any] = {}
        self._audit_logger: Optional[ToolAuditLogger] = None
    
    async def get_service(self, service_class: Type) -> Any:
        """Lazy instantiation with context injection"""
        if service_class not in self._services:
            # All services get orchestrator session and tenant context
            service = service_class(self.db, self.context)
            self._services[service_class] = service
        return self._services[service_class]
    
    async def with_audit(self, audit_logger: 'ToolAuditLogger') -> 'ServiceRegistry':
        """Enable tool operation auditing"""
        self._audit_logger = audit_logger
        return self
    
    async def record_tool_operation(self, tool_name: str, operation: str, 
                                   input_data: dict, output_data: dict,
                                   duration_ms: float, success: bool):
        """Record tool operations in orchestrator audit trail"""
        if self._audit_logger:
            await self._audit_logger.log_tool_operation(
                tool_name, operation, input_data, output_data, 
                duration_ms, success
            )
```

#### 2. Service Base Class with Context Awareness

```python
# backend/app/services/base_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext
from app.services.integration.failure_journal import log_failure

class ServiceBase:
    """Base class for all services with multi-tenant context awareness"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db  # Orchestrator-owned session - NEVER commit or close
        self.context = context  # Tenant context for isolation
        
    @property
    def client_account_id(self) -> str:
        """Multi-tenant context propagation"""
        return str(self.context.client_account_id)
    
    @property
    def engagement_id(self) -> str:
        """Engagement-scoped context"""
        return str(self.context.engagement_id)
    
    async def record_failure(self, operation: str, error: Exception, details: dict):
        """Integrate with existing failure journal system"""
        await log_failure(
            self.db,
            source="service_layer",
            operation=f"{self.__class__.__name__}.{operation}",
            error_message=str(error),
            details={
                **details,
                "client_account_id": self.client_account_id,
                "engagement_id": self.engagement_id
            }
        )
```

#### 3. Tool Refactoring Pattern

```python
# backend/app/services/crewai_flows/tools/asset_creation_tool.py - REFACTORED
from app.services.service_registry import ServiceRegistry
from app.services.asset_service import AssetService

class AssetCreationToolWithService(BaseTool):
    """Asset creation tool using service registry - NO direct DB access"""
    
    name: str = "asset_creator"
    description: str = "Create assets through service layer with full audit trail"
    
    def __init__(self, registry: ServiceRegistry):
        super().__init__()
        self.registry = registry
    
    async def _arun(self, asset_data: Dict[str, Any]) -> str:
        """Execute through service layer with audit logging"""
        start_time = time.time()
        
        try:
            # Get service from registry (inherits orchestrator session + context)
            asset_service = await self.registry.get_service(AssetService)
            
            # Service handles business logic, orchestrator manages transaction
            asset = await asset_service.create_asset(asset_data)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Audit trail flows through orchestrator
            await self.registry.record_tool_operation(
                tool_name=self.name,
                operation="create_asset",
                input_data=asset_data,
                output_data={"asset_id": str(asset.id), "asset_name": asset.name},
                duration_ms=duration_ms,
                success=True
            )
            
            return json.dumps({
                "success": True,
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "tenant_context": {
                    "client_account_id": asset_service.client_account_id,
                    "engagement_id": asset_service.engagement_id
                }
            })
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Error handling through service layer
            asset_service = await self.registry.get_service(AssetService)
            await asset_service.record_failure("create_asset", e, asset_data)
            
            # Audit error
            await self.registry.record_tool_operation(
                tool_name=self.name,
                operation="create_asset",
                input_data=asset_data,
                output_data={"error": str(e)},
                duration_ms=duration_ms,
                success=False
            )
            
            return json.dumps({
                "success": False,
                "error": str(e),
                "error_type": e.__class__.__name__
            })
```

#### 4. Orchestrator Integration

```python
# backend/app/services/flow_orchestration/execution_engine_crew.py - ENHANCED
async def execute_crew_with_service_registry(
    self, 
    crew_config: Dict, 
    context: RequestContext
) -> Dict:
    """Execute crew with service registry pattern"""
    
    # Orchestrator owns the session throughout execution
    async with self.db as session:  # Single session for entire execution
        
        # Create service registry with orchestrator session
        async with ServiceRegistry(session, context) as registry:
            
            # Enable audit logging
            audit_logger = ToolAuditLogger(self.flow_audit_logger)
            registry = await registry.with_audit(audit_logger)
            
            # Create tools with service registry injection
            tools = await self._create_tools_with_registry(crew_config, registry)
            
            # Execute crew - all tool operations flow through services
            crew = Crew(
                agents=crew_config["agents"],
                tasks=crew_config["tasks"],
                tools=tools
            )
            
            result = await crew.kickoff()
            
            # Orchestrator handles transaction commit
            await session.commit()
            
            return result
```

#### 5. Feature Flag Implementation

```python
# backend/app/services/crewai_flows/tools/__init__.py
import os
from typing import List, Dict, Any, Optional
from app.services.service_registry import ServiceRegistry

def create_asset_tools(
    context_info: Dict[str, Any], 
    registry: Optional[ServiceRegistry] = None
) -> List:
    """Create asset tools with backward compatibility"""
    
    use_service_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
    
    if use_service_registry and registry:
        logger.info("🔧 Creating asset tools with service registry")
        return [
            AssetCreationToolWithService(registry),
            BulkAssetCreationToolWithService(registry)
        ]
    else:
        logger.warning("⚠️ Using legacy tool implementation (deprecated)")
        return [
            AssetCreationTool(context_info),  # Legacy implementation
            BulkAssetCreationTool(context_info)
        ]
```

#### 6. Integration with ADR-015 Agent Pool

```python
# backend/app/services/persistent_agents/tenant_scoped_agent_pool.py - ENHANCED
@classmethod
async def create_agent_with_service_registry(
    cls,
    agent_type: str,
    memory_manager: ThreeTierMemoryManager,
    registry: Optional[ServiceRegistry] = None
) -> CrewAIAgent:
    """Create persistent agent with service registry tools"""
    
    context_info = {
        "client_account_id": str(memory_manager.client_account_id),
        "engagement_id": str(memory_manager.engagement_id),
        "agent_type": agent_type
    }
    
    # Get tools with service registry if available
    tools = []
    if registry:
        # Service-based tools (preferred)
        tools.extend(create_asset_tools(context_info, registry=registry))
        tools.extend(create_field_mapping_tools(context_info, registry=registry))
        tools.extend(create_data_validation_tools(context_info, registry=registry))
    else:
        # Legacy tools (fallback)
        tools.extend(create_asset_tools(context_info))
        tools.extend(create_field_mapping_tools(context_info))
        tools.extend(create_data_validation_tools(context_info))
    
    # Create agent with memory and tools
    agent = CrewAIAgent(
        role=AGENT_ROLES[agent_type],
        goal=AGENT_GOALS[agent_type],
        backstory=AGENT_BACKSTORIES[agent_type],
        memory=True,
        memory_manager=memory_manager,
        tools=tools
    )
    
    return agent
```

## Consequences

### Positive Consequences

#### 1. **Architectural Compliance**
- **Orchestrator-First**: Single session per execution owned by orchestrator
- **Multi-Tenant Safety**: Tenant context flows from orchestrator to all tool operations
- **Transaction Integrity**: All operations within single transaction boundary
- **ADR-015 Alignment**: Service registry supports persistent agent architecture

#### 2. **Operational Benefits**
- **Complete Audit Trail**: All tool operations captured in orchestrator audit log
- **Centralized Error Handling**: Consistent error patterns and recovery mechanisms
- **Idempotency Support**: Service layer can implement operation deduplication
- **Performance Monitoring**: Tool operation metrics integrated with flow monitoring

#### 3. **Development Advantages**
- **Testability**: Tools become thin adapters, services easily mockable
- **Maintainability**: Business logic centralized in service layer
- **Reusability**: Services can be used by multiple tools and API endpoints
- **Type Safety**: Dependency injection provides compile-time safety

#### 4. **Security Improvements**
- **Context Isolation**: Multi-tenant context enforced at service layer
- **Permission Propagation**: User permissions flow through service registry
- **Audit Compliance**: Complete operation trail for security reviews
- **Data Access Control**: Services enforce data access policies consistently

### Negative Consequences

#### 1. **Complexity Increase**
- **Additional Abstraction**: Service registry adds architectural layer
- **Migration Effort**: Existing tools require refactoring
- **Learning Curve**: Developers need to understand dependency injection pattern
- **Testing Complexity**: Need to test both service and tool layers

#### 2. **Performance Considerations**
- **Memory Overhead**: Service registry caches services per execution
- **Indirect Access**: Tool→Registry→Service adds method call overhead
- **Session Lifecycle**: Longer-lived sessions may impact connection pooling
- **Audit Logging**: Additional audit operations add latency

#### 3. **Migration Risks**
- **Backward Compatibility**: Need to maintain legacy tools during transition
- **Feature Flag Complexity**: Dual implementation paths increase testing burden
- **Database Session Management**: Changes to session ownership patterns
- **Agent Integration**: Updates required to persistent agent pool

### Risks and Mitigations

#### Risk 1: Service Registry Performance Impact
**Mitigation**: 
- Lazy service instantiation reduces memory usage
- Service caching eliminates repeated initialization overhead
- Benchmark performance against legacy implementation
- Performance monitoring with rollback capability

#### Risk 2: Session Management Issues
**Mitigation**:
- Clear documentation of session ownership rules
- Service base class prevents accidental session operations
- Comprehensive testing of session lifecycle
- Existing session handling patterns in orchestrator

#### Risk 3: Agent Integration Failures
**Mitigation**:
- Feature flag allows gradual rollout
- Maintain backward compatibility during transition
- Test service registry with persistent agent pool
- Fallback to legacy tools if registry fails

#### Risk 4: Multi-Tenant Context Leakage
**Mitigation**:
- Service base class enforces context propagation
- Unit tests verify tenant isolation
- Audit logs enable security reviews
- Existing multi-tenant patterns proven in codebase

## Implementation Plan

### Phase 1: Foundation Infrastructure (Week 1)

#### Days 1-2: Core Components
1. **Service Registry Implementation**
   - Create `ServiceRegistry` class with dependency injection
   - Implement audit logging integration
   - Add feature flag support

2. **Service Base Class**
   - Create `ServiceBase` with context awareness
   - Integrate with existing failure journal
   - Add multi-tenant property helpers

#### Days 3-4: Asset Tool Migration
1. **Refactor Asset Creation Tools**
   - Create service-based implementations
   - Add comprehensive error handling
   - Implement backward compatibility

2. **Testing Framework**
   - Unit tests for service registry
   - Integration tests for tool operations
   - Performance benchmarks

#### Day 5: Integration Testing
1. **End-to-End Validation**
   - Test service registry with real crews
   - Validate audit trail completeness
   - Verify multi-tenant isolation

### Phase 2: Service Layer Expansion (Week 2)

#### Days 6-7: Service Extraction
1. **Field Mapping Service**
   - Extract from API layer to service layer
   - Add service registry compatibility
   - Update API endpoints to use service

2. **Idempotency Infrastructure**
   - Implement operation deduplication
   - Add to critical services
   - Test retry scenarios

#### Days 8-10: Tool Migration
1. **Additional Tools**
   - Migrate data validation tools
   - Migrate field mapping tools  
   - Migrate dependency analysis tools

### Phase 3: Orchestrator Integration (Week 3)

#### Days 11-13: Execution Engine Updates
1. **Orchestrator Enhancement**
   - Update `execution_engine_crew.py`
   - Integrate service registry creation
   - Add audit logger configuration

2. **Agent Pool Integration**
   - Update persistent agent pool
   - Add service registry tool creation
   - Test with ADR-015 implementation

#### Days 14-15: Production Readiness
1. **Monitoring and Observability**
   - Add service operation metrics
   - Create performance dashboards
   - Implement alerting

### Phase 4: Full Deployment (Week 4)

#### Days 16-18: Rollout
1. **Feature Flag Activation**
   - Gradual rollout to test environments
   - Performance validation
   - Error rate monitoring

2. **Legacy Deprecation**
   - Plan legacy tool removal
   - Update documentation
   - Train development team

#### Days 19-20: Validation
1. **Success Metrics Verification**
   - Audit trail completeness
   - Performance impact assessment
   - Multi-tenant isolation validation

## Success Metrics

### Technical Metrics
- **Session Management**: 100% of tool operations use orchestrator session
- **Audit Coverage**: 100% of tool operations captured in audit trail
- **Performance Impact**: <10% latency increase from service layer
- **Error Rate**: <1% increase in tool operation failures

### Architectural Metrics
- **Code Quality**: Eliminate direct `AsyncSessionLocal()` usage in tools
- **Test Coverage**: >90% coverage for service registry and refactored tools
- **Multi-Tenant Safety**: 100% of operations include tenant context
- **ADR-015 Compatibility**: Service registry works with persistent agents

### Operational Metrics
- **Deployment Success**: Zero-downtime rollout with feature flags
- **Rollback Capability**: <2 minute rollback to legacy implementation
- **Developer Experience**: Positive feedback on service registry pattern
- **Monitoring Effectiveness**: Complete visibility into tool operations

## Alternatives Considered

### Alternative 1: Enhanced Session Passing
**Description**: Pass orchestrator session directly to each tool  
**Rejected Because**: Breaks encapsulation, still requires tools to manage transactions, no service layer benefits

### Alternative 2: Tool-Level Orchestrator Injection
**Description**: Inject orchestrator directly into tools for session access  
**Rejected Because**: Creates tight coupling, violates separation of concerns, testing difficulties

### Alternative 3: Global Session Context
**Description**: Use thread-local or context variables for session access  
**Rejected Because**: Hidden dependencies, testing complexity, potential memory leaks

### Alternative 4: Event-Driven Tool Communication
**Description**: Tools publish events, services listen and execute operations  
**Rejected Because**: Adds complexity, asynchronous challenges, harder to debug

## Validation Criteria

### Must-Have Requirements
- ✅ Tools no longer create database sessions directly
- ✅ All tool operations flow through service layer
- ✅ Multi-tenant context propagated from orchestrator to tools
- ✅ Complete audit trail for all tool operations
- ✅ Backward compatibility maintained during migration

### Should-Have Requirements
- ✅ Service registry performance impact <10%
- ✅ Feature flag allows gradual rollout
- ✅ Integration with persistent agent pool (ADR-015)
- ✅ Comprehensive test coverage for new patterns

### Could-Have Enhancements
- Service-to-service communication patterns
- Advanced caching strategies for services
- Cross-tenant pattern sharing through services
- Performance analytics per service operation

## Related ADRs

- [ADR-015](015-persistent-multi-tenant-agent-architecture.md) - Service registry enables proper agent tool integration
- [ADR-008](008-agentic-intelligence-system-architecture.md) - Service layer supports agent intelligence operations
- [ADR-006](006-master-flow-orchestrator.md) - Orchestrator owns session management
- [ADR-009](009-multi-tenant-architecture.md) - Multi-tenant context flows through service registry
- [ADR-003](003-postgresql-only-state-management.md) - PostgreSQL sessions managed by orchestrator

## References

- Implementation Plan: `/docs/planning/agent-tool-service-registry/implementation-plan.md`
- Service Registry Pattern: https://martinfowler.com/articles/injection.html
- CrewAI Tool Integration: `/backend/app/services/crewai_flows/tools/`
- Flow Orchestration: `/backend/app/services/flow_orchestration/`
- Multi-Tenant Context: `/backend/app/core/context.py`

---

**Decision Made By**: Platform Architecture Team  
**Date**: 2025-01-13  
**Implementation Target**: v1.9.0 - v2.0.0  
**Review Cycle**: Weekly during implementation, Monthly after deployment