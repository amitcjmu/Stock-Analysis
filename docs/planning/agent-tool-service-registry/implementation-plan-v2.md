# Agent Tool Service Registry Implementation Plan v2

## Executive Summary

This document outlines the implementation plan for refactoring CrewAI tools to use a service layer architecture instead of direct database access. This addresses critical architectural issues identified in PR#82 code review, specifically tools bypassing the orchestrator's session management and violating multi-tenant isolation patterns.

**Version 2 Updates**: Incorporates critical fixes for session handling, audit API alignment, persistent agent integration, and deployment guidance based on architectural review.

## Problem Statement

Current issues with direct database access in CrewAI tools:
- Tools create their own `AsyncSessionLocal()` instances, breaking orchestrator session ownership
- No centralized audit trail for tool operations
- Missing idempotency guarantees for critical operations
- Potential multi-tenant data leakage risks
- Difficult to test and maintain

### Critical Anti-Pattern
```python
# ❌ FORBIDDEN: Tools must NEVER import or use AsyncSessionLocal
from app.core.database import AsyncSessionLocal  # VIOLATION

async def _arun(self, data: Dict) -> str:
    async with AsyncSessionLocal() as db:  # VIOLATION
        # Tool creates own session, breaking orchestrator ownership
```

## Solution Overview

Implement a service registry pattern where:
1. Orchestrator owns the database session and transaction boundaries
2. Services are injected into tools via registry
3. Tools become thin adapters between agents and services
4. All database operations go through service layer
5. Centralized audit and error handling
6. Services may `flush()` but NEVER `commit()`

## Implementation Phases

### Phase 1: Foundation (Week 1)

#### Day 1-2: Core Infrastructure

**File: `backend/app/services/base_service.py`**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext
from app.services.integration.failure_journal import log_failure
from app.services.recovery.error_recovery_system import ErrorRecoverySystem

class ServiceBase:
    """
    Base class for all services - minimal, no business logic
    
    CRITICAL RULES:
    - Services may call db.flush() for ID generation
    - Services must NEVER call db.commit() or db.close()
    - Orchestrator owns transaction via db.begin()
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db  # Orchestrator-owned, never commit/close
        self.context = context
    
    async def flush_for_id(self):
        """Flush to make IDs available within transaction"""
        await self.db.flush()
    
    async def record_failure(self, operation: str, error: Exception, details: dict):
        """Record failures using existing failure journal"""
        await log_failure(
            self.db,
            source="tool_service",
            operation=operation,
            error_message=str(error),
            details=details
        )
        
        # For severe failures, optionally enqueue to DLQ
        if self._is_severe_failure(error):
            recovery_system = ErrorRecoverySystem()
            await recovery_system.enqueue_for_retry(
                operation=operation,
                context=self.context,
                error=error,
                details=details
            )
    
    def _is_severe_failure(self, error: Exception) -> bool:
        """Determine if failure requires DLQ retry"""
        return isinstance(error, (DatabaseError, IntegrityError))
```

**File: `backend/app/services/service_registry.py`**
```python
from typing import Dict, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext

class ServiceRegistry:
    """
    Per-execution service registry - manages service lifecycle
    
    CRITICAL: Registry NEVER owns or closes the database session
    Cleanup only clears service cache and non-DB resources
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db  # Borrowed from orchestrator, not owned
        self.context = context  # Multi-tenant context from orchestrator
        self._services: Dict[Type, Any] = {}
        self._metrics = []
    
    async def get_service(self, service_class: Type) -> Any:
        """Lazily instantiate and cache services with context injection"""
        if service_class not in self._services:
            # All services receive orchestrator session and tenant context
            self._services[service_class] = service_class(self.db, self.context)
        return self._services[service_class]
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Cleanup - only clear cache, don't touch DB session
        Session lifecycle is managed by orchestrator
        """
        self._services.clear()
        # Log metrics if needed (non-blocking)
```

#### Day 3-4: Asset Tool Refactor

**Modifications to `backend/app/services/crewai_flows/tools/asset_creation_tool.py`**

```python
import os
from app.services.service_registry import ServiceRegistry
from app.services.asset_service import AssetService
from app.services.flow_orchestration.audit_logger import FlowAuditLogger, AuditCategory, AuditLevel

def create_asset_creation_tools(context_info: Dict[str, Any], registry: ServiceRegistry = None) -> List:
    """
    Create tools with optional service registry support
    Tools must NEVER import AsyncSessionLocal
    """
    
    use_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
    
    if use_registry and registry:
        logger.info("🔧 Creating asset tools with service registry (no direct DB access)")
        return [
            AssetCreationToolWithService(registry),
            BulkAssetCreationToolWithService(registry)
        ]
    else:
        logger.warning("⚠️ Using legacy tool implementation (deprecated, will be removed)")
        return [
            AssetCreationTool(context_info),
            BulkAssetCreationTool(context_info)
        ]

class AssetCreationToolWithService(BaseTool):
    """Asset creation tool using service layer - NO direct DB access"""
    
    name: str = "asset_creator"
    description: str = "Create an asset using service layer with full audit trail"
    
    def __init__(self, registry: ServiceRegistry):
        super().__init__()
        self.registry = registry
    
    async def _arun(self, asset_data: Dict[str, Any]) -> str:
        """Execute via service - no database imports allowed"""
        start_time = time.time()
        asset_service = await self.registry.get_service(AssetService)
        
        try:
            # Service handles business logic, may flush, never commits
            asset = await asset_service.create_asset(asset_data)
            duration_ms = (time.time() - start_time) * 1000
            
            # Audit using correct API
            await self._audit_operation(
                success=True,
                operation="create_asset",
                input_data=asset_data,
                output_data={"asset_id": str(asset.id)},
                duration_ms=duration_ms
            )
            
            return json.dumps({
                "success": True,
                "asset_id": str(asset.id),
                "asset_name": asset.name
            })
            
        except Exception as e:
            await asset_service.record_failure("create_asset", e, asset_data)
            await self._audit_operation(
                success=False,
                operation="create_asset",
                input_data=asset_data,
                output_data={"error": str(e)},
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
            return json.dumps({"success": False, "error": str(e)})
    
    async def _audit_operation(self, success: bool, operation: str, input_data: dict, 
                              output_data: dict, duration_ms: float, error: str = None):
        """Audit tool operations using existing FlowAuditLogger API"""
        if hasattr(self.registry, 'context'):
            audit_logger = FlowAuditLogger()
            await audit_logger.log_audit_event(
                flow_id=self.registry.context.flow_id,
                operation=f"tool_{self.name}_{operation}",
                category=AuditCategory.TOOL_OPERATION,
                level=AuditLevel.INFO if success else AuditLevel.ERROR,
                context={
                    "tool_name": self.name,
                    "agent_name": getattr(self.registry.context, 'agent_name', 'unknown'),
                    "input_summary": str(input_data)[:200],
                    "output_summary": str(output_data)[:200],
                    "duration_ms": duration_ms,
                    "success": success,
                    "error": error,
                    "client_account_id": str(self.registry.context.client_account_id),
                    "engagement_id": str(self.registry.context.engagement_id)
                }
            )
```

#### Day 5: Testing & Audit

**File: `backend/app/services/flow_orchestration/tool_audit_logger.py`**
```python
from app.services.flow_orchestration.audit_logger import FlowAuditLogger, AuditCategory, AuditLevel
from app.core.context import RequestContext

class ToolAuditLogger:
    """
    Extends existing flow audit logger for tool operations
    Uses the actual FlowAuditLogger.log_audit_event API
    """
    
    def __init__(self, flow_audit_logger: FlowAuditLogger, context: RequestContext):
        self.base_logger = flow_audit_logger
        self.context = context
    
    async def log_tool_operation(
        self,
        tool_name: str,
        operation: str,
        agent_name: str,
        input_data: dict,
        output_data: dict,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Log tool operations using correct audit API"""
        await self.base_logger.log_audit_event(
            flow_id=self.context.flow_id,
            operation=f"tool_{tool_name}_{operation}",
            category=AuditCategory.TOOL_OPERATION,  # New category
            level=AuditLevel.INFO if success else AuditLevel.ERROR,
            context={
                "tool_name": tool_name,
                "agent_name": agent_name,
                "input_summary": str(input_data)[:200],
                "output_summary": str(output_data)[:200],
                "duration_ms": duration_ms,
                "success": success,
                "error": error,
                "client_account_id": str(self.context.client_account_id),
                "engagement_id": str(self.context.engagement_id)
            }
        )
```

### Phase 2: Expand Coverage (Week 2)

#### Day 6-7: Field Mapping Service Migration

1. Move `MappingService` from correct location:
```bash
# Correct source path includes 'services' subfolder
mv backend/app/api/v1/endpoints/data_import/field_mapping/services/mapping_service.py \
   backend/app/services/field_mapping_service.py
```

2. Service returns domain DTOs, not Pydantic models:
```python
# backend/app/services/field_mapping_service.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FieldMappingDTO:
    """Domain DTO - not a Pydantic model"""
    source_field: str
    target_field: str
    transformation: Optional[str] = None
    confidence_score: float = 1.0

class FieldMappingService(ServiceBase):
    """
    Field mapping service - returns domain DTOs
    May flush() for IDs, never commits
    """
    
    async def create_mapping(self, mapping_data: dict) -> FieldMappingDTO:
        """Create mapping, return domain DTO"""
        # Create entity
        mapping = FieldMapping(**mapping_data)
        self.db.add(mapping)
        
        # Flush to get ID if needed (no commit!)
        await self.flush_for_id()
        
        # Return domain DTO
        return FieldMappingDTO(
            source_field=mapping.source_field,
            target_field=mapping.target_field,
            transformation=mapping.transformation,
            confidence_score=mapping.confidence_score
        )
```

3. API layer adapts DTOs to Pydantic:
```python
# backend/app/api/v1/endpoints/data_import/field_mapping/router.py
from app.services.field_mapping_service import FieldMappingService
from app.api.v1.schemas.field_mapping import FieldMappingResponse

@router.post("/mappings")
async def create_mapping(
    mapping_data: MappingRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """API endpoint - handles HTTP concerns only, adapts DTOs"""
    service = FieldMappingService(db, context)
    
    # Service returns domain DTO
    dto = await service.create_mapping(mapping_data.dict())
    
    # Router adapts to Pydantic response model
    return FieldMappingResponse(
        source_field=dto.source_field,
        target_field=dto.target_field,
        transformation=dto.transformation,
        confidence_score=dto.confidence_score
    )
```

#### Day 8-9: Idempotency Helper

**File: `backend/app/services/helpers/idempotency_manager.py`**
```python
class IdempotencyManager:
    """
    Lightweight idempotency helper
    
    Hierarchy:
    1. First choice: DB unique constraints
    2. Second choice: Upserts (INSERT ... ON CONFLICT)
    3. Last resort: Idempotency key table
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def ensure_idempotent_insert(self, table, data: dict, unique_fields: List[str]):
        """
        Try strategies in order:
        1. Unique constraint (let DB handle it)
        2. Upsert if supported
        3. Key table as fallback
        """
        # Implementation follows hierarchy
        pass
```

### Phase 3: Full Rollout (Weeks 3-4)

#### Week 3: Orchestrator Integration with Persistent Agents

**CRITICAL: Integration with ADR-015 Persistent Agent Architecture**

```python
# backend/app/services/flow_orchestration/execution_engine_crew.py
async def execute_with_persistent_agents(self, crew_config: Dict, context: RequestContext) -> Dict:
    """
    Execute using persistent agent pool - NO direct Crew instantiation
    Aligns with ADR-015: Persistent Multi-Tenant Agent Architecture
    """
    
    # Orchestrator manages transaction boundary (not session closure!)
    async with self.db.begin():  # ✅ Transaction boundary only
        
        # Create service registry with orchestrator's session
        async with ServiceRegistry(self.db, context) as registry:
            
            # Get persistent agent pool for this tenant
            agent_pool = TenantScopedAgentPool()
            
            # Inject service registry into persistent agents
            agents_with_services = []
            for agent_type in crew_config["required_agents"]:
                agent = await agent_pool.get_or_create_agent(
                    client_id=str(context.client_account_id),
                    engagement_id=str(context.engagement_id),
                    agent_type=agent_type,
                    service_registry=registry  # Pass registry to agent
                )
                agents_with_services.append(agent)
            
            # Execute tasks using persistent agents (no new Crew!)
            results = await self._execute_with_pool(
                agents=agents_with_services,
                tasks=crew_config["tasks"],
                context=context
            )
            
            # Transaction commits here automatically
            return results
```

**Update `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`:**
```python
@classmethod
def _get_agent_tools(
    cls,
    agent_type: str,
    memory_manager: ThreeTierMemoryManager,
    registry: Optional[ServiceRegistry] = None
) -> List:
    """
    Get tools with optional service registry
    Tools attached to persistent agents, not new Crews
    """
    
    context_info = {
        "client_account_id": str(memory_manager.client_account_id),
        "engagement_id": str(memory_manager.engagement_id),
        "agent_type": agent_type
    }
    
    # Pass registry to tool creators if available
    tools = []
    use_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
    
    if registry and use_registry:
        # Service-based tools for persistent agents
        tools.extend(create_asset_creation_tools(context_info, registry=registry))
        tools.extend(create_data_validation_tools(context_info, registry=registry))
        # ... other tools
    else:
        # Legacy path (deprecated, with warning logs)
        logger.warning(f"⚠️ Agent {agent_type} using legacy tools (deprecated)")
        tools.extend(create_asset_creation_tools(context_info))
        # ... legacy tools
    
    return tools
```

#### Week 4: Remaining Tools Migration & CI Enforcement

**CI Rule Enforcement - Comprehensive Guards:**
```yaml
# .github/workflows/no-direct-db-access.yml
name: Enforce No Direct DB Access in Tools

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Check for AsyncSessionLocal usage in tools
        run: |
          # Check multiple tool directories
          TOOL_DIRS=(
            "backend/app/services/crewai_flows/tools/"
            "backend/app/services/agents/*/tools/"
            "backend/app/services/crewai_flows/handlers/"
          )
          
          for dir in "${TOOL_DIRS[@]}"; do
            if [ -d "$dir" ]; then
              if grep -r "AsyncSessionLocal" "$dir"; then
                echo "ERROR: Direct DB access found in $dir!"
                exit 1
              fi
            fi
          done
          echo "✅ No AsyncSessionLocal usage in tools"
      
      - name: Check for AsyncSessionLocal imports in tools
        run: |
          # Also forbid imports
          for dir in "${TOOL_DIRS[@]}"; do
            if [ -d "$dir" ]; then
              if grep -r "from app.core.database import AsyncSessionLocal" "$dir"; then
                echo "ERROR: AsyncSessionLocal import found in $dir!"
                exit 1
              fi
            fi
          done
          echo "✅ No AsyncSessionLocal imports in tools"
      
      - name: Check for commit() calls in services
        run: |
          # Services should never commit (excluding migrations/infra)
          if grep -r "\.commit(" backend/app/services/ \
             --exclude-dir=migrations \
             --exclude-dir=infrastructure \
             --exclude-dir=tests; then
            echo "WARNING: commit() found in services - services should only flush!"
            # Make this a hard failure after migration
          fi
          echo "✅ Service commit check complete"
```

## Monitoring & Rollback

### Feature Flag Configuration & Deployment

**Docker Compose Configuration:**
```yaml
# docker-compose.yml
services:
  migration_backend:
    environment:
      - USE_SERVICE_REGISTRY=${USE_SERVICE_REGISTRY:-false}
```

**Railway Configuration:**
```bash
# Railway environment variables
USE_SERVICE_REGISTRY=true  # Enable in production gradually
```

**Vercel Configuration:**
```bash
# Vercel environment variables (for API routes if any)
USE_SERVICE_REGISTRY=true
```

**Backend reads flag:**
```python
# backend/app/core/config.py
class Settings(BaseSettings):
    use_service_registry: bool = Field(
        default=False,
        env="USE_SERVICE_REGISTRY",
        description="Enable service registry for tools"
    )
```

### Performance Metrics - Staged Approach

**Phase 1: Adapter Pattern (No Schema Changes)**
```python
# backend/app/services/monitoring/metrics_adapter.py
class MetricsAdapter:
    """Start with no-op, add table later to avoid schema churn"""
    
    async def record_service_call(self, service: str, operation: str, 
                                 duration_ms: float, success: bool):
        """Non-blocking metrics - never fail main path"""
        if os.getenv("ENABLE_SERVICE_METRICS", "false") == "true":
            # Log for now, add table in Phase 2
            logger.info(f"SERVICE_METRIC: {service}.{operation} {duration_ms}ms")
```

**Phase 2: Dedicated Metrics Table (After Validation)**
```sql
-- After initial rollout succeeds
CREATE TABLE service_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    duration_ms FLOAT NOT NULL,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Rollback Procedure

**File: `docs/operations/service-registry-rollback.md`**
```markdown
# Service Registry Rollback Procedure

## Quick Rollback (< 1 minute)

1. Set environment variable:
   ```bash
   export USE_SERVICE_REGISTRY=false
   ```

2. Restart backend services:
   ```bash
   docker-compose restart migration_backend
   ```

3. Verify rollback (check actual endpoints):
   ```bash
   # If recovery queue endpoint exists:
   curl http://localhost:8000/api/v1/recovery/queue/status
   
   # Alternative: Use existing monitoring
   curl http://localhost:8000/api/v1/monitoring/agents/metrics
   curl http://localhost:8000/api/v1/admin/audit/logs?category=TOOL_OPERATION
   ```

## Mixed-Mode Operation

During rollout, legacy and service-based tools run side-by-side:
- Legacy tools: Deprecation warnings logged
- Service tools: Full audit trail
- Both work with persistent agent pool

## Monitoring After Rollback

1. Check error rates:
   ```
   GET /api/v1/admin/audit/logs?level=ERROR&category=TOOL_OPERATION
   ```

2. Monitor agent performance:
   ```
   GET /api/v1/monitoring/agents/{agent_name}/performance
   ```
```

## Success Criteria

### Phase 1 Success Metrics
- [ ] Asset creation tool refactored and tested
- [ ] Feature flag working (can toggle between implementations)
- [ ] Audit trail captures all tool operations with correct API
- [ ] No regression in existing flows
- [ ] Test coverage > 80% for new code
- [ ] No `AsyncSessionLocal` imports or usage in refactored tools

### Phase 2 Success Metrics
- [ ] Field mapping service extracted from API layer (correct path)
- [ ] Service flush/commit policy documented and enforced
- [ ] Idempotency hierarchy implemented (constraints → upserts → keys)
- [ ] End-to-end tests passing with persistent agents

### Phase 3 Success Metrics
- [ ] All tools migrated to service pattern
- [ ] CI rules prevent regression (usage + imports + commits)
- [ ] Performance impact < 10% latency increase
- [ ] Complete audit trail with flow_id and tenant context
- [ ] Mixed-mode operation stable during transition

## Service Architecture Guidelines

### Service Consolidation Rules
To avoid service sprawl:
1. **One service per domain**: Don't create overlapping services
2. **Clear boundaries**: Each service owns specific entities
3. **Reuse existing**: Prefer extending services over creating new ones

### Initial Service Scope
Focus on high-value services:
- `AssetService` - Already exists, extend as needed
- `FieldMappingService` - Extract from API layer
- `DataImportService` - Already exists, adapt for registry
- `DependencyService` - Reuse existing dependency_analysis_service.py

Defer creating until clear need:
- `AttributeService` - Wait for clear domain boundary
- `ValidationService` - May overlap with existing services

### DTO Guidelines
```python
# Services return simple domain DTOs
@dataclass
class AssetDTO:
    id: UUID
    name: str
    asset_type: str
    # ... domain fields

# Routers adapt to Pydantic models
class AssetResponse(BaseModel):
    id: str
    name: str
    asset_type: AssetTypeEnum
    # ... API-specific fields
```

## Testing Strategy

### Required Test Coverage

```python
# Phase 1 Tests
test_service_registry_lifecycle()
test_service_registry_never_closes_session()
test_service_base_flush_not_commit()
test_asset_tool_no_db_imports()
test_audit_logger_correct_api()
test_persistent_agent_integration()

# Phase 2 Tests
test_field_mapping_service_dto_pattern()
test_idempotency_hierarchy()
test_mixed_mode_operation()

# Phase 3 Tests
test_all_tools_use_registry()
test_ci_guards_comprehensive()
test_performance_metrics_non_blocking()
```

## Risk Mitigation

### Critical Rules
1. **Tools must NEVER import `AsyncSessionLocal`**
2. **Services may `flush()` but NEVER `commit()`**
3. **Orchestrator owns transaction via `begin()`**
4. **Registry never owns or closes sessions**
5. **Persistent agents only, no direct Crew instantiation**

### Monitoring
- Deprecation warnings for legacy tools
- Audit all tool operations
- Track service operation metrics (non-blocking)
- Alert on any `AsyncSessionLocal` usage

---

*Last Updated: 2025-01-13*
*Version: 2.0*
*Status: Ready for Implementation*
*Review: Architecture team approved corrections*