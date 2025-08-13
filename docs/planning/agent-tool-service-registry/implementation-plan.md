# Agent Tool Service Registry Implementation Plan

## Executive Summary

This document outlines the implementation plan for refactoring CrewAI tools to use a service layer architecture instead of direct database access. This addresses critical architectural issues identified in PR#82 code review, specifically tools bypassing the orchestrator's session management and violating multi-tenant isolation patterns.

## Problem Statement

Current issues with direct database access in CrewAI tools:
- Tools create their own `AsyncSessionLocal()` instances, breaking orchestrator session ownership
- No centralized audit trail for tool operations
- Missing idempotency guarantees for critical operations
- Potential multi-tenant data leakage risks
- Difficult to test and maintain

## Solution Overview

Implement a service registry pattern where:
1. Orchestrator owns the database session
2. Services are injected into tools via registry
3. Tools become thin adapters between agents and services
4. All database operations go through service layer
5. Centralized audit and error handling

## Implementation Phases

### Phase 1: Foundation (Week 1)

#### Day 1-2: Core Infrastructure

**File: `backend/app/services/base_service.py`**
```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext
from app.services.integration.failure_journal import log_failure

class ServiceBase:
    """Base class for all services - minimal, no business logic"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db  # Orchestrator-owned, never commit/close
        self.context = context
    
    async def record_failure(self, operation: str, error: Exception, details: dict):
        """Record failures using existing failure journal"""
        await log_failure(
            self.db,
            source="tool_service",
            operation=operation,
            error_message=str(error),
            details=details
        )
```

**File: `backend/app/services/service_registry.py`**
```python
from typing import Dict, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext

class ServiceRegistry:
    """Per-execution service registry - manages service lifecycle"""
    
    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db  # Borrowed, not owned
        self.context = context
        self._services: Dict[Type, Any] = {}
        self._metrics = []
    
    async def get_service(self, service_class: Type) -> Any:
        """Lazily instantiate and cache services"""
        if service_class not in self._services:
            self._services[service_class] = service_class(self.db, self.context)
        return self._services[service_class]
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup - only clear cache, don't touch DB session"""
        self._services.clear()
        # Could log metrics here if needed
```

#### Day 3-4: Asset Tool Refactor

**Modifications to `backend/app/services/crewai_flows/tools/asset_creation_tool.py`**

1. Add feature flag support:
```python
import os
from app.services.service_registry import ServiceRegistry
from app.services.asset_service import AssetService

def create_asset_creation_tools(context_info: Dict[str, Any], registry: ServiceRegistry = None) -> List:
    """Create tools with optional service registry support"""
    
    use_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
    
    if use_registry and registry:
        logger.info("🔧 Creating asset tools with service registry")
        return [
            AssetCreationToolWithService(registry),
            BulkAssetCreationToolWithService(registry)
        ]
    else:
        logger.warning("⚠️ Using legacy tool implementation (deprecated)")
        return [
            AssetCreationTool(context_info),
            BulkAssetCreationTool(context_info)
        ]
```

2. New service-based implementation:
```python
class AssetCreationToolWithService(BaseTool):
    """Asset creation tool using service layer"""
    
    name: str = "asset_creator"
    description: str = "Create an asset using service layer"
    
    def __init__(self, registry: ServiceRegistry):
        super().__init__()
        self.registry = registry
    
    async def _arun(self, asset_data: Dict[str, Any]) -> str:
        """Execute via service"""
        asset_service = await self.registry.get_service(AssetService)
        try:
            asset = await asset_service.create_asset(asset_data)
            return json.dumps({
                "success": True,
                "asset_id": str(asset.id),
                "asset_name": asset.name
            })
        except Exception as e:
            await asset_service.record_failure("create_asset", e, asset_data)
            return json.dumps({
                "success": False,
                "error": str(e)
            })
```

#### Day 5: Testing & Audit

**File: `backend/app/services/flow_orchestration/tool_audit_logger.py`**
```python
from app.services.flow_orchestration.audit_logger import FlowAuditLogger

class ToolAuditLogger:
    """Extends existing flow audit logger for tool operations"""
    
    def __init__(self, flow_audit_logger: FlowAuditLogger):
        self.base_logger = flow_audit_logger
    
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
        """Log tool operations using existing audit infrastructure"""
        await self.base_logger.log_event(
            event_type="tool_operation",
            details={
                "tool_name": tool_name,
                "operation": operation,
                "agent_name": agent_name,
                "input_summary": str(input_data)[:200],
                "output_summary": str(output_data)[:200],
                "duration_ms": duration_ms,
                "success": success,
                "error": error
            }
        )
```

**Test Coverage Requirements:**
```python
# tests/test_service_registry.py
async def test_service_registry_lifecycle():
    """Test registry creates and cleans up services"""
    pass

async def test_service_registry_caching():
    """Test services are cached per execution"""
    pass

# tests/test_asset_tool_with_service.py
async def test_asset_creation_via_service():
    """Test tool uses service, not direct DB"""
    pass

async def test_asset_tool_audit_trail():
    """Test all operations are audited"""
    pass
```

### Phase 2: Expand Coverage (Week 2)

#### Day 6-7: Field Mapping Service Migration

1. Move `MappingService` from `backend/app/api/v1/endpoints/data_import/field_mapping/mapping_service.py` to `backend/app/services/field_mapping_service.py`

2. Keep only HTTP concerns in API layer:
```python
# backend/app/api/v1/endpoints/data_import/field_mapping/router.py
from app.services.field_mapping_service import FieldMappingService

@router.post("/mappings")
async def create_mapping(
    mapping_data: MappingRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """API endpoint - handles HTTP concerns only"""
    service = FieldMappingService(db, context)
    try:
        result = await service.create_mapping(mapping_data.dict())
        return MappingResponse.from_domain(result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### Day 8-9: Idempotency Helper

**File: `backend/app/services/helpers/idempotency_manager.py`**
```python
from typing import Optional
import hashlib
import json

class IdempotencyManager:
    """Lightweight idempotency helper using DB constraints"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def generate_key(self, operation: str, data: dict) -> str:
        """Generate deterministic key for operation"""
        content = f"{operation}:{json.dumps(data, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def check_duplicate(self, key: str, entity_type: str) -> Optional[UUID]:
        """Check if operation was already performed"""
        # Query idempotency table or use unique constraints
        pass
    
    async def record_operation(self, key: str, entity_type: str, result_id: UUID):
        """Record successful operation for future checks"""
        pass
```

#### Day 10: Integration Testing

**End-to-end test script:**
```bash
#!/bin/bash
# tests/e2e/test_service_registry_integration.sh

echo "Testing service registry integration..."

# 1. Enable feature flag
export USE_SERVICE_REGISTRY=true

# 2. Run asset creation flow
python -m pytest tests/e2e/test_asset_creation_with_service.py -v

# 3. Verify audit trail
python -m pytest tests/e2e/test_audit_completeness.py -v

# 4. Test failure recovery
python -m pytest tests/e2e/test_failure_recovery_dlq.py -v

echo "Integration tests complete"
```

### Phase 3: Full Rollout (Weeks 3-4)

#### Week 3: Orchestrator Integration

**Modify `backend/app/services/flow_orchestration/execution_engine_crew.py`:**
```python
async def execute_crew(self, crew_config: Dict, context: RequestContext) -> Dict:
    """Execute crew with service registry"""
    
    # Create registry for this execution
    async with ServiceRegistry(self.db, context) as registry:
        # Pass registry to tool factories
        tools = self._create_tools_with_registry(crew_config, registry)
        
        # Create and execute crew
        crew = Crew(
            agents=crew_config["agents"],
            tasks=crew_config["tasks"],
            tools=tools
        )
        
        result = await crew.kickoff()
        return result
```

**Modify `backend/app/services/persistent_agents/tenant_scoped_agent_pool.py`:**
```python
@classmethod
def _get_agent_tools(
    cls,
    agent_type: str,
    memory_manager: ThreeTierMemoryManager,
    registry: Optional[ServiceRegistry] = None
) -> List:
    """Get tools with optional service registry"""
    
    context_info = {
        "client_account_id": str(memory_manager.client_account_id),
        "engagement_id": str(memory_manager.engagement_id),
        "agent_type": agent_type
    }
    
    # Pass registry to tool creators if available
    tools = []
    if registry and os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true":
        tools.extend(create_asset_creation_tools(context_info, registry=registry))
        tools.extend(create_data_validation_tools(context_info, registry=registry))
    else:
        # Legacy path
        tools.extend(create_asset_creation_tools(context_info))
        tools.extend(create_data_validation_tools(context_info))
    
    return tools
```

#### Week 4: Remaining Tools Migration

**Progressive migration checklist:**
- [ ] `data_validation_tool.py` - Refactor to use `DataValidationService`
- [ ] `critical_attributes_tool.py` - Refactor to use `AttributeService`
- [ ] `dependency_analysis_tool.py` - Refactor to use `DependencyService`
- [ ] `mapping_confidence_tool.py` - Refactor to use `FieldMappingService`

**CI Rule Enforcement:**
```yaml
# .github/workflows/no-direct-db-access.yml
name: Enforce No Direct DB Access in Tools

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Check for AsyncSessionLocal in tools
        run: |
          if grep -r "AsyncSessionLocal" backend/app/services/crewai_flows/tools/; then
            echo "ERROR: Direct DB access found in tools!"
            exit 1
          fi
          echo "✅ No direct DB access in tools"
```

## Monitoring & Rollback

### Feature Flag Configuration

**File: `backend/.env.example`**
```bash
# Service Registry Feature Flag
# Set to "true" to enable service-based tools
# Set to "false" to use legacy direct DB access
USE_SERVICE_REGISTRY=false
```

### Performance Metrics

**File: `backend/app/services/monitoring/metrics_adapter.py`**
```python
from app.models.agent_execution_history import AgentExecutionHistory
import asyncio

class MetricsAdapter:
    """Lightweight, non-blocking metrics collection"""
    
    async def record_service_call(
        self,
        service: str,
        operation: str,
        duration_ms: float,
        success: bool
    ):
        """Fire-and-forget metrics recording"""
        # Non-blocking, uses existing AgentExecutionHistory
        asyncio.create_task(self._record_async(service, operation, duration_ms, success))
    
    async def _record_async(self, service: str, operation: str, duration_ms: float, success: bool):
        """Background recording - doesn't block main flow"""
        try:
            # Record to existing monitoring tables
            pass
        except Exception:
            # Never fail the main flow for metrics
            pass
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

3. Verify rollback:
   ```bash
   curl http://localhost:8000/api/v1/monitoring/agents/metrics
   ```

## Monitoring After Rollback

1. Check error rates:
   ```
   GET /api/v1/admin/audit/logs?event_type=tool_operation&status=failed
   ```

2. Check DLQ status:
   ```
   GET /api/v1/recovery/queue/status
   ```

3. Monitor agent performance:
   ```
   GET /api/v1/monitoring/agents/{agent_name}/performance
   ```

## Rollback Validation

- All flows should continue working with legacy tools
- No data loss or corruption
- Audit trail continues (though less detailed)
```

## Success Criteria

### Phase 1 Success Metrics
- [ ] Asset creation tool refactored and tested
- [ ] Feature flag working (can toggle between implementations)
- [ ] Audit trail captures all tool operations
- [ ] No regression in existing flows
- [ ] Test coverage > 80% for new code

### Phase 2 Success Metrics
- [ ] Field mapping service extracted from API layer
- [ ] Idempotency helper preventing duplicates
- [ ] One additional tool migrated successfully
- [ ] End-to-end tests passing

### Phase 3 Success Metrics
- [ ] All tools migrated to service pattern
- [ ] No `AsyncSessionLocal` in tool modules
- [ ] CI rules preventing regression
- [ ] Performance impact < 10% latency increase
- [ ] Complete audit trail for all operations

## Testing Strategy

### Unit Tests
```python
# Required test coverage per phase

# Phase 1
test_service_base_initialization()
test_service_registry_lifecycle()
test_service_registry_caching()
test_asset_tool_with_service()
test_asset_tool_without_db_access()
test_tool_audit_logging()

# Phase 2
test_field_mapping_service()
test_idempotency_manager()
test_bulk_operations_with_savepoints()
test_partial_failure_handling()

# Phase 3
test_all_tools_use_registry()
test_multi_tenant_isolation()
test_transaction_boundaries()
test_performance_metrics()
```

### Integration Tests
```python
# End-to-end flow tests

test_discovery_flow_with_service_registry()
test_collection_flow_with_service_registry()
test_failure_recovery_through_dlq()
test_audit_trail_completeness()
test_rollback_to_legacy_tools()
```

### Contract Tests
```python
# Ensure stable interfaces

test_tool_interface_compatibility()
test_service_interface_stability()
test_registry_api_contract()
```

## Risk Mitigation

### Identified Risks

1. **Performance Degradation**
   - Mitigation: Metrics from day 1, < 10% threshold
   - Rollback: Feature flag to legacy

2. **Breaking Agent Workflows**
   - Mitigation: Incremental rollout, extensive testing
   - Rollback: Keep legacy implementations

3. **Session Management Issues**
   - Mitigation: Clear ownership model, never close orchestrator session
   - Rollback: Revert to direct DB access

4. **Audit Trail Gaps**
   - Mitigation: Test audit completeness per phase
   - Rollback: Maintain legacy logging

### Contingency Plans

- **Partial Rollout Failure**: Can run mixed mode (some tools legacy, some service-based)
- **Performance Issues**: Can optimize service caching, connection pooling
- **Testing Gaps**: Can extend timeline for more comprehensive testing

## Documentation Updates

### Developer Guide Updates
- How to create new tools with service registry
- Service layer patterns and best practices
- Testing requirements for tools

### Operations Guide Updates
- Monitoring service-based tools
- Performance tuning recommendations
- Troubleshooting guide

### Architecture Documentation
- Updated ADR for service layer architecture
- Sequence diagrams for tool-service-db flow
- Multi-tenant isolation guarantees

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Foundation | Core infrastructure, asset tool refactor, testing framework |
| 2 | Expansion | Field mapping service, idempotency, second tool migration |
| 3 | Integration | Orchestrator integration, registry injection |
| 4 | Completion | Remaining tools, CI rules, documentation |

## Approval and Sign-off

- [ ] Architecture Team Review
- [ ] Security Team Review
- [ ] Operations Team Review
- [ ] QA Team Review
- [ ] Product Owner Approval

---

*Last Updated: 2025-01-13*
*Version: 1.0*
*Status: Draft*