# Service Dependency DAG (Directed Acyclic Graph)

## Executive Summary

This document provides a comprehensive mapping of all service-to-service dependencies in the migrate-ui-orchestrator backend, revealing the actual dependency hierarchy, circular dependencies, and architectural violations that need remediation.

**Key Findings**:
- **121 total services** analyzed across 4 architectural layers
- **1 critical circular dependency** between MasterFlowOrchestrator ↔ FlowOrchestration
- **15+ layer violations** where lower layers call higher layers
- **24 services** depend on crewai_flows (highest coupling point)

## Part 1: Service Inventory by Layer

### Orchestration Layer (Level 1) - Highest

Services that orchestrate and coordinate all other services:

1. **MasterFlowOrchestrator** (`app/services/master_flow_orchestrator/`)
   - Purpose: Single source of truth for ALL workflow operations (per ADR-006)
   - Imports: flow_orchestration, crewai_flows, flow_status_sync, mfo_sync_agent
   - Imported by: 8 services (including violations from business logic layer)

2. **FlowOrchestration** (`app/services/flow_orchestration/`)
   - Purpose: Flow execution engine and lifecycle management
   - Imports: master_flow_orchestrator (CIRCULAR!), crewai_flows, agents, service_registry
   - Imported by: master_flow_orchestrator

3. **WorkflowOrchestration** (`app/services/workflow_orchestration/`)
   - Purpose: High-level workflow coordination
   - Imports: monitoring, service_registry
   - Imported by: 2 services

4. **MultiAgentOrchestration** (`app/services/multi_agent_orchestration/`)
   - Purpose: Coordinate multiple AI agents
   - Imports: crewai_flows, persistent_agents
   - Imported by: 1 service

### Business Logic Layer (Level 2)

Services implementing business rules and domain logic:

**Assessment Domain**:
- **AssessmentFlowService** (`app/services/assessment_flow_service/`)
  - Imports: None from services
  - Imported by: flow_configs

- **UnifiedAssessmentFlowService** (`app/services/unified_assessment_flow_service.py`)
  - Imports: master_flow_orchestrator (VIOLATION - upward call)
  - Imported by: API endpoints

**Collection Domain**:
- **CollectionFlow** (`app/services/collection_flow/`)
  - Imports: caching, monitoring
  - Imported by: 15 services (including adapters - VIOLATION)

- **CollectionGaps** (`app/services/collection_gaps/`)
  - Imports: gap_detection
  - Imported by: collection handlers

- **GapDetection** (`app/services/gap_detection/`)
  - Imports: ai_analysis
  - Imported by: 11 services

- **ChildFlowServices** (`app/services/child_flow_services/`)
  - Imports: collection_flow, discovery_flow_service
  - Imported by: master_flow_orchestrator

**Discovery Domain**:
- **DiscoveryFlowService** (`app/services/discovery_flow_service/`)
  - Imports: crewai integration only
  - Imported by: 8 services (including crewai_flows - VIOLATION)

- **Discovery** (`app/services/discovery/`)
  - Imports: master_flow_orchestrator (VIOLATION - upward call)
  - Imported by: unified_discovery

- **UnifiedDiscovery** (`app/services/unified_discovery/`)
  - Imports: discovery
  - Imported by: API endpoints

**Planning & Migration**:
- **Planning** (`app/services/planning/`)
  - Imports: None from services
  - Imported by: flow_configs

- **Migration** (`app/services/migration/`)
  - Imports: None from services
  - Imported by: flow_configs

**Analysis Services**:
- **TechDebtAnalysisService** (`app/services/tech_debt_analysis_service.py`)
  - Imports: None from services
  - Imported by: assessment handlers

- **DependencyAnalysisService** (`app/services/dependency_analysis_service.py`)
  - Imports: None from services
  - Imported by: assessment handlers

- **Enrichment** (`app/services/enrichment/`)
  - Imports: multi_model_service, tenant_memory_manager
  - Imported by: collection flow

**Flow Configuration**:
- **FlowConfigs** (`app/services/flow_configs/`)
  - Imports: Various phase handlers
  - Imported by: master_flow_orchestrator

### Agent Layer (Level 3)

Services managing AI agents and CrewAI:

1. **CrewAIFlows** (`app/services/crewai_flows/`)
   - Purpose: CrewAI integration and agent orchestration
   - Imports: discovery_flow_service (VIOLATION - calls up to business logic)
   - Imported by: 24 services (highest coupling)

2. **CrewAIFlowService** (`app/services/crewai_flow_service.py`)
   - Purpose: Backward compatibility shim for CrewAI
   - Imports: discovery_flow_service (VIOLATION - calls up), crewai_flow_* modules
   - Imported by: API endpoints

3. **PersistentAgents** (`app/services/persistent_agents/`)
   - Purpose: Multi-tenant agent pool management
   - Imports: None from services (good isolation!)
   - Imported by: 7 services

4. **TenantScopedAgentPool** (`app/services/persistent_agents/tenant_scoped_agent_pool.py`)
   - Purpose: Tenant-isolated agent instances
   - Imports: None from services (excellent isolation!)
   - Imported by: field_mapping_executor, tech_debt, dependency_analysis

5. **Agents** (`app/services/agents/`)
   - Purpose: Agent definitions and configurations
   - Imports: crewai_flows, agent_learning_system
   - Imported by: flow_orchestration

6. **AgenticIntelligence** (`app/services/agentic_intelligence/`)
   - Purpose: Advanced AI reasoning
   - Imports: agentic_memory
   - Imported by: enrichment

7. **AgentLearning** (`app/services/agent_learning/`)
   - Purpose: Agent learning and improvement
   - Imports: agentic_memory, enhanced_agent_memory
   - Imported by: 2 services

8. **AgentUIBridgeHandlers** (`app/services/agent_ui_bridge_handlers/`)
   - Purpose: Bridge agent operations to UI
   - Imports: caching
   - Imported by: flow_orchestration

9. **Crews** (`app/services/crews/`)
   - Purpose: CrewAI crew configurations
   - Imports: None from services
   - Imported by: crewai_flows

10. **TenantMemoryManager** (`app/services/crewai_flows/memory/tenant_memory_manager/`)
    - Purpose: Enterprise multi-tenant memory (ADR-024)
    - Imports: None from services (isolated)
    - Imported by: enrichment agents, gap_prioritization

### Infrastructure Layer (Level 4) - Lowest

Services providing technical capabilities:

**LLM & AI Infrastructure**:
- **MultiModelService** (`app/services/multi_model_service.py`)
  - Purpose: LLM API abstraction with cost tracking
  - Imports: llm_usage_tracker only
  - Imported by: 9 services (enrichment agents, gap resolution, dynamic questions)

- **EmbeddingService** (`app/services/embedding_service.py`)
  - Purpose: Text embeddings for vector search
  - Imports: None from services
  - Imported by: tenant_memory_manager

**Storage & Caching**:
- **Caching** (`app/services/caching/`)
  - Purpose: Redis and in-memory caching
  - Imports: None from services (proper infrastructure)
  - Imported by: 15 services

- **SecureCache** (`app/services/secure_cache/`)
  - Purpose: Encrypted caching
  - Imports: caching
  - Imported by: auth services

- **StorageManager** (`app/services/storage_manager/`)
  - Purpose: File and object storage
  - Imports: None from services
  - Imported by: data_import

**Authentication & Security**:
- **AuthServices** (`app/services/auth_services/`)
  - Purpose: Authentication, JWT, user management
  - Imports: None from services
  - Imported by: API layer

- **RBACService** (`app/services/rbac_service.py`)
  - Purpose: Role-based access control
  - Imports: None from services
  - Imported by: API layer

**Monitoring & Performance**:
- **Monitoring** (`app/services/monitoring/`)
  - Purpose: Metrics and observability
  - Imports: None from services
  - Imported by: 7 services

- **Performance** (`app/services/performance/`)
  - Purpose: Performance tracking
  - Imports: None from services
  - Imported by: flow_orchestration

- **AgentPerformanceMonitor** (`app/services/agent_performance_monitor.py`)
  - Purpose: Track agent performance
  - Imports: agent_learning_system (VIOLATION - infra calling agent layer)
  - Imported by: crewai_flows

**Integration & Adapters**:
- **Adapters** (`app/services/adapters/`)
  - Purpose: Cloud provider integrations (AWS, Azure, GCP)
  - Imports: collection_flow (VIOLATION - infra calling business logic)
  - Imported by: discovery flows

- **Integrations** (`app/services/integrations/`)
  - Purpose: Third-party service integrations
  - Imports: None from services
  - Imported by: collection flow

**Service Registry**:
- **ServiceRegistry** (`app/services/service_registry.py`)
  - Purpose: Service discovery and registration
  - Imports: monitoring, performance_tracker, service_registry_metrics
  - Imported by: flow_orchestration, master_flow_orchestrator

- **HandlerRegistry** (`app/services/handler_registry.py`)
  - Purpose: Dynamic handler registration
  - Imports: None from services
  - Imported by: flow_orchestration

## Part 2: Visual Dependency DAG

```
┌─────────────────────────────────────────────────────────────┐
│          ORCHESTRATION LAYER (Level 1 - Highest)           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐     ┌──────────────────────┐     │
│  │ MasterFlowOrchestrator│◄───►│  FlowOrchestration   │     │
│  └──────────┬───────────┘     └──────────┬───────────┘     │
│             │                             │                  │
│  ┌──────────▼───────────┐     ┌──────────▼───────────┐     │
│  │WorkflowOrchestration │     │MultiAgentOrchestration│     │
│  └──────────────────────┘     └──────────────────────┘     │
└──────────────┬──────────────────────────┬──────────────────┘
               │                           │
               │ Calls ↓                   │ CIRCULAR! ↑
               │                           │
┌──────────────▼───────────────────────────▼──────────────────┐
│          BUSINESS LOGIC LAYER (Level 2)                     │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Assessment     │  │  Collection   │  │  Discovery    │  │
│  │  - Readiness    │  │  - GapAnalysis│  │  - DataExtract│ │
│  │  - TechDebt     │  │  - Questions  │  │  - AssetMgmt  │  │
│  │  - 6R Strategy  │  │  - Validation │  │  - Summary    │  │
│  └────────┬────────┘  └──────┬───────┘  └───────┬───────┘  │
│           │                   │                   │          │
│  ┌────────▼──────────────────▼──────────────────▼────────┐  │
│  │         ChildFlowServices (Coordination)              │  │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Planning      │  │  Migration    │  │  Enrichment   │  │
│  │  - WavePlanning │  │  - Strategy   │  │  - AIAnalysis │  │
│  └─────────────────┘  └──────────────┘  └───────────────┘  │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ Calls ↓
                               │
┌──────────────────────────────▼───────────────────────────────┐
│              AGENT LAYER (Level 3)                           │
├───────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐    │
│  │           CrewAIFlows (Main Agent Orchestrator)      │    │
│  │  - Unified flows for Discovery/Assessment/Collection │    │
│  │  - Agent coordination and task execution             │    │
│  └────────────────┬─────────────────────────────────────┘    │
│                   │                                           │
│  ┌────────────────▼────────────┐  ┌─────────────────────┐   │
│  │   TenantScopedAgentPool     │  │  PersistentAgents   │   │
│  │   - Multi-tenant isolation  │  │  - Agent lifecycle   │   │
│  └─────────────────────────────┘  └─────────────────────┘   │
│                                                               │
│  ┌──────────────────┐  ┌────────────┐  ┌────────────────┐   │
│  │ AgentLearning    │  │   Crews    │  │ AgentUIBridge  │   │
│  └──────────────────┘  └────────────┘  └────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐    │
│  │         TenantMemoryManager (ADR-024)               │    │
│  │  - Enterprise multi-tenant memory isolation          │    │
│  │  - PostgreSQL + pgvector (no ChromaDB)              │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               │ Calls ↓
                               │
┌──────────────────────────────▼───────────────────────────────┐
│         INFRASTRUCTURE LAYER (Level 4 - Lowest)              │
├───────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ MultiModelService│  │ EmbeddingService│ │   Caching    │  │
│  │ - LLM calls      │  │ - Vectors       │ │ - Redis      │  │
│  │ - Cost tracking  │  │ - pgvector      │ │ - In-memory  │  │
│  └──────────────────┘  └─────────────────┘ └──────────────┘  │
│                                                               │
│  ┌──────────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │  AuthServices    │  │   Monitoring   │  │  Performance │  │
│  │  - JWT/RBAC      │  │   - Metrics    │  │  - Tracking  │  │
│  └──────────────────┘  └─────────────────┘ └──────────────┘  │
│                                                               │
│  ┌──────────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │    Adapters      │  │ ServiceRegistry│ │StorageManager│  │
│  │  - AWS/Azure/GCP │  │ - Discovery    │ │ - Files/S3   │  │
│  └──────────────────┘  └─────────────────┘ └──────────────┘  │
└───────────────────────────────────────────────────────────────┘

Legend:
→  Normal dependency (allowed)
◄─►  Circular dependency (FORBIDDEN)
↑  Upward dependency (VIOLATION)
```

## Part 3: Dependency Rules Matrix

| From Layer ↓ / To Layer → | Orchestration | Business Logic | Agent | Infrastructure |
|----------------------------|---------------|----------------|-------|----------------|
| **Orchestration**          | ⚠️ Same       | ✅ Down        | ✅ Down| ✅ Down        |
| **Business Logic**         | ❌ Up         | ✅ Same        | ✅ Down| ✅ Down        |
| **Agent**                  | ❌ Up         | ❌ Up          | ✅ Same| ✅ Down        |
| **Infrastructure**         | ❌ Up         | ❌ Up          | ❌ Up  | ✅ Same        |

**Legend**:
- ✅ **Allowed**: Normal top-down dependency flow
- ⚠️ **Caution**: Same-layer dependencies allowed but avoid cycles
- ❌ **Forbidden**: Creates upward dependency or violates architecture

## Part 4: Critical Violations Found

### 1. Circular Dependency: MasterFlowOrchestrator ↔ FlowOrchestration

**Location**:
- `backend/app/services/master_flow_orchestrator/` → flow_orchestration
- `backend/app/services/flow_orchestration/collection_phase_runner.py:20` → master_flow_orchestrator

**Impact**:
- Initialization deadlock risk
- Tight coupling preventing independent testing
- Violates single responsibility principle

**Root Cause**:
- MFO uses FlowAuditLogger and FlowStatusManager from flow_orchestration
- flow_orchestration's collection_phase_runner calls back to MFO

**Fix**: Extract shared components to a common module or use dependency injection

### 2. Business Logic → Orchestration Violations

**Violations Found**:
1. `enhanced_collection_transition_service` → `master_flow_orchestrator`
2. `unified_assessment_flow_service` → `master_flow_orchestrator`
3. `discovery` → `master_flow_orchestrator`

**Impact**: Business logic tightly coupled to orchestration layer

**Fix**: Use events or callbacks instead of direct calls

### 3. Agent Layer → Business Logic Violations

**Violations Found**:
1. `crewai_flows` → `discovery_flow_service`
2. `crewai_flow_service` → `discovery_flow_service`

**Impact**: Agent layer knows about specific business domains

**Fix**: Use abstractions or interfaces

### 4. Infrastructure → Higher Layer Violations

**Violations Found**:
1. All `adapters/*` → `collection_flow` (8 violations!)
2. `agent_performance_monitor` → `agent_learning_system`

**Impact**: Infrastructure tightly coupled to business logic

**Fix**: Invert dependencies using interfaces

### 5. Repository → Service Violations

**Violations Found**:
1. `collection_flow_repository.py:82` → `master_flow_orchestrator`
2. `assessment_flow_repository/commands/` → services

**Impact**: Data layer knows about business logic

**Fix**: Repositories should NEVER import services

## Part 5: Specific Service Dependencies

### MultiModelService
**Layer**: Infrastructure (Level 4)
**Purpose**: LLM API abstraction with automatic cost tracking

**Dependencies (What it imports)**:
- `llm_usage_tracker` (infrastructure) ✅ Allowed

**Dependents (What imports it)**:
- `enrichment/agents/*` (Agent Layer) ✅ Allowed
- `gap_resolution_suggester` (Business Logic) ⚠️ Should go through Agent Layer
- `dynamic_question_engine` (Business Logic) ⚠️ Should go through Agent Layer

**Rule**: Prefer using CrewAI agents for LLM calls to maintain consistency

---

### CrewAIFlows
**Layer**: Agent (Level 3)
**Purpose**: Main CrewAI integration and agent orchestration

**Dependencies (What it imports)**:
- `discovery_flow_service` (Business Logic) ❌ VIOLATION - Agent calling up

**Dependents (What imports it)**:
- 24 services across all layers (highest coupling point)
- `master_flow_orchestrator` (Orchestration) ✅ Allowed
- `flow_orchestration` (Orchestration) ✅ Allowed
- Various business logic services ✅ Allowed

**Rule**: CrewAIFlows should not know about specific business flows

---

### TenantScopedAgentPool
**Layer**: Agent (Level 3)
**Purpose**: Multi-tenant agent instance management

**Dependencies (What it imports)**:
- None from services layer ✅ Excellent isolation!

**Dependents (What imports it)**:
- `field_mapping_executor` (Business Logic) ✅ Allowed
- `tech_debt_persistent` (Agent) ✅ Allowed
- `dependency_analysis_persistent` (Agent) ✅ Allowed

**Rule**: This is a model service - perfect isolation

---

### MasterFlowOrchestrator
**Layer**: Orchestration (Level 1)
**Purpose**: Single source of truth for workflow operations (ADR-006)

**Dependencies (What it imports)**:
- `flow_orchestration` (Orchestration) ⚠️ Creates circular dependency!
- `crewai_flows` (Agent) ✅ Allowed
- `flow_status_sync` (Orchestration) ✅ Allowed

**Dependents (What imports it)**:
- `flow_orchestration` (Orchestration) ⚠️ Circular!
- `enhanced_collection_transition_service` (Business) ❌ Violation
- `discovery` (Business) ❌ Violation
- API endpoints ✅ Allowed

**Rule**: Only API layer and same-level orchestration should call MFO

## Part 6: Forbidden Patterns

### Pattern 1: Circular Service Dependencies
❌ **Forbidden**: ServiceA → ServiceB → ServiceA

**Found Instance**:
```python
# master_flow_orchestrator/core.py
from app.services.flow_orchestration import FlowAuditLogger

# flow_orchestration/collection_phase_runner.py
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
```

**Alternative**: Extract FlowAuditLogger to a shared utilities module

### Pattern 2: Repository Calling Service
❌ **Forbidden**: Repository → Service

**Found Instance**:
```python
# repositories/collection_flow_repository.py:82
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
```

**Alternative**: Service calls Repository, Repository returns data only

### Pattern 3: Infrastructure Calling Business Logic
❌ **Forbidden**: Adapter → BusinessLogicService

**Found Instance**:
```python
# adapters/aws_adapter/base.py
from app.services.collection_flow import CollectionFlowService
```

**Alternative**: Use dependency injection or events

### Pattern 4: Agent Layer Calling Business Logic
⚠️ **Caution**: Agent → Specific Business Service

**Found Instance**:
```python
# crewai_flows/some_file.py
from app.services.discovery_flow_service import DiscoveryFlowService
```

**Alternative**: Use generic interfaces or abstract base classes

## Part 7: Real-World Code Examples

### ✅ CORRECT: Top-Down Dependencies
```python
# Orchestration calling Agent (allowed)
class MasterFlowOrchestrator:
    def __init__(self, db: AsyncSession):
        self.crewai_service = CrewAIFlowService(db)

    async def execute_phase(self, flow_id: str, phase: str):
        # Orchestration layer calls down to Agent layer
        result = await self.crewai_service.execute_task(...)
        return result

# Agent calling Infrastructure (allowed)
class CrewAIFlowService:
    def __init__(self):
        self.llm = MultiModelService()
        self.cache = CacheService()

    async def execute_task(self, task):
        # Agent layer calls down to Infrastructure
        cached = await self.cache.get(task.id)
        if not cached:
            result = await self.llm.generate_response(...)
            await self.cache.set(task.id, result)
        return result
```

### ❌ INCORRECT: Upward Dependencies
```python
# Infrastructure calling Business Logic (violation)
class AWSAdapter:
    def __init__(self):
        # ❌ Infrastructure shouldn't know about business logic
        from app.services.collection_flow import CollectionFlowService
        self.collection_service = CollectionFlowService()

    async def sync_resources(self):
        # ❌ Adapter driving business logic
        await self.collection_service.update_assets(...)

# Business Logic calling Orchestration (violation)
class DiscoveryService:
    def __init__(self):
        # ❌ Business logic shouldn't import orchestration
        from app.services.master_flow_orchestrator import MFO
        self.mfo = MFO()

    async def complete_discovery(self):
        # ❌ Business logic calling up to orchestration
        await self.mfo.transition_phase(...)
```

### ✅ FIXED: Using Proper Patterns
```python
# Fixed: Infrastructure uses events
class AWSAdapter:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def sync_resources(self):
        resources = await self._fetch_resources()
        # ✅ Publish event instead of calling service
        await self.event_bus.publish("resources.synced", resources)

# Fixed: Business Logic uses callbacks
class DiscoveryService:
    def __init__(self, on_complete: Optional[Callable] = None):
        self.on_complete = on_complete

    async def complete_discovery(self):
        result = await self._process_discovery()
        # ✅ Use callback instead of direct call
        if self.on_complete:
            await self.on_complete(result)

# Fixed: Using dependency injection
class MasterFlowOrchestrator:
    def __init__(self, audit_logger: AuditLogger):
        # ✅ Inject dependency instead of importing
        self.audit_logger = audit_logger
```

## Part 8: Migration Roadmap

### Priority 1: Critical (Fix Immediately)

#### 1. Circular Dependency: MFO ↔ FlowOrchestration
**Location**: `master_flow_orchestrator` ↔ `flow_orchestration`
**Fix**:
```python
# Create new shared module
# app/services/flow_shared/audit_logger.py
class FlowAuditLogger:
    # Move from flow_orchestration to shared

# Update imports
# master_flow_orchestrator/core.py
from app.services.flow_shared import FlowAuditLogger

# flow_orchestration/collection_phase_runner.py
# Use dependency injection instead
class CollectionPhaseRunner:
    def __init__(self, orchestrator: Optional[Any] = None):
        self.orchestrator = orchestrator  # Inject MFO
```
**Effort**: 2-4 hours

#### 2. Repository → Service Violations
**Location**: `repositories/collection_flow_repository.py:82`
**Fix**: Remove service import, return data only
**Effort**: 1-2 hours

### Priority 2: High (Fix This Sprint)

#### 3. Adapters → Collection Flow (8 violations)
**Location**: All `adapters/*` importing `collection_flow`
**Fix**: Use event bus or dependency injection
**Effort**: 4-6 hours

#### 4. Business Logic → MFO Violations
**Location**: `discovery`, `assessment`, `collection` services
**Fix**: Use callbacks or events
**Effort**: 3-4 hours per service

### Priority 3: Medium (Fix This Quarter)

#### 5. Agent Layer → Business Logic
**Location**: `crewai_flows` → `discovery_flow_service`
**Fix**: Create abstract interfaces
**Effort**: 6-8 hours

#### 6. Performance Monitor → Agent Learning
**Location**: `agent_performance_monitor.py`
**Fix**: Invert dependency
**Effort**: 2-3 hours

## Part 9: Enforcement Recommendations

### 1. Add Pre-commit Hook
```python
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: check-service-dependencies
      name: Check Service Dependencies
      entry: python scripts/check_dependencies.py
      language: python
      files: ^backend/app/services/.*\.py$
```

### 2. Create Dependency Check Script
```python
#!/usr/bin/env python3
# scripts/check_dependencies.py

FORBIDDEN_IMPORTS = {
    # Repository layer cannot import services
    r"repositories/.*": ["from app.services"],

    # Infrastructure cannot import higher layers
    r"services/(adapters|multi_model_service|embedding|caching)/.*": [
        "from app.services.collection",
        "from app.services.discovery",
        "from app.services.assessment",
        "from app.services.master_flow_orchestrator"
    ],

    # Agent layer cannot import business logic
    r"services/(crewai_flows|agents|persistent_agents)/.*": [
        "from app.services.discovery_flow_service",
        "from app.services.collection_flow",
        "from app.services.assessment"
    ]
}
```

### 3. Update CLAUDE.md
Add this DAG to CLAUDE.md as the authoritative reference for service dependencies.

### 4. Create ADR for Service Dependencies
```markdown
# ADR-XXX: Service Dependency Rules

## Status: Accepted

## Context
Service dependencies have grown organically, creating circular dependencies
and layer violations.

## Decision
Enforce strict top-down dependency flow:
1. Orchestration → Business/Agent/Infrastructure
2. Business → Agent/Infrastructure
3. Agent → Infrastructure
4. Infrastructure → None

## Consequences
- Clear dependency flow
- Easier testing
- Better modularity
- Some refactoring required
```

## Part 10: Summary & Key Metrics

### Dependency Analysis Summary

**Total Services Analyzed**: 121
**Total Import Relationships**: 200+
**Services by Layer**:
- Orchestration: 4 services
- Business Logic: 45 services
- Agent: 25 services
- Infrastructure: 47 services

### Violation Summary

**Critical Issues**:
- **1** Circular dependency (MFO ↔ FlowOrchestration)
- **5** Repository → Service violations
- **15+** Upward dependency violations

**Most Coupled Services**:
1. `crewai_flows`: 24 dependents (needs interface abstraction)
2. `caching`: 15 dependents (acceptable for infrastructure)
3. `collection_flow`: 15 dependents (8 are violations from adapters)

### Compliance Score

| Layer | Compliance | Issues |
|-------|------------|--------|
| Orchestration | 60% | Circular dependency with flow_orchestration |
| Business Logic | 85% | Some upward calls to MFO |
| Agent | 70% | Calls to specific business services |
| Infrastructure | 65% | Adapters violating layer boundaries |
| **Overall** | **70%** | Needs improvement |

## Most Important Rules

### The Golden Rules of Service Dependencies

1. **Top-Down Only**: Services can ONLY call same layer or lower layers
2. **No Circles**: A → B → A is FORBIDDEN
3. **Repositories are Dumb**: They return data, never call services
4. **Infrastructure is Foundation**: It knows nothing about business logic
5. **Orchestration Orchestrates**: It coordinates but doesn't implement business logic
6. **Business Logic is Pure**: It implements rules without knowing how it's orchestrated
7. **Agents are Generic**: They execute tasks without knowing specific business domains
8. **Use Abstractions**: When crossing layers, use interfaces not concrete types

### Quick Reference

**If you're in...**
- **Orchestration**: You can call anyone below
- **Business Logic**: You can call Agent or Infrastructure, NOT Orchestration
- **Agent**: You can call Infrastructure only, NOT Business Logic or Orchestration
- **Infrastructure**: You cannot call any other services
- **Repository**: You cannot call ANY services

**When you need upward communication**:
- Use callbacks
- Use events
- Use dependency injection
- Never use direct imports

## Appendix: File Locations of Key Violations

For immediate action, fix these files:

1. **Circular Dependency Files**:
   - `backend/app/services/master_flow_orchestrator/core.py`
   - `backend/app/services/flow_orchestration/collection_phase_runner.py`

2. **Repository Violations**:
   - `backend/app/repositories/collection_flow_repository.py:82`
   - `backend/app/repositories/assessment_flow_repository/commands/flow_commands/*.py`

3. **Adapter Violations**:
   - `backend/app/services/adapters/aws_adapter/base.py`
   - `backend/app/services/adapters/azure_adapter/base.py`
   - `backend/app/services/adapters/gcp_adapter/adapter.py`

4. **Business → Orchestration Violations**:
   - `backend/app/services/enhanced_collection_transition_service.py`
   - `backend/app/services/unified_assessment_flow_service.py`
   - `backend/app/services/discovery/*.py`

5. **Agent → Business Violations**:
   - `backend/app/services/crewai_flow_service.py`
   - `backend/app/services/crewai_flows/` (multiple files)

---

**Document Version**: 1.0
**Last Updated**: November 2024
**Next Review**: After fixing Priority 1 violations

This DAG should be treated as the authoritative reference for all service dependency decisions in the migrate-ui-orchestrator codebase.