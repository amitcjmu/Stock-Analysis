# Agent Tool Service Registry Implementation Plan v3

## Executive Summary

This document outlines the implementation plan for refactoring CrewAI tools to use a service layer architecture instead of direct database access. This addresses critical architectural issues identified in PR#82 code review, specifically tools bypassing the orchestrator's session management and violating multi-tenant isolation patterns.

**Version 3 Updates**: Final corrections for audit logger injection, stable hashing, SQL syntax, and import completeness based on final architectural review.

## Problem Statement

Current issues with direct database access in CrewAI tools:
- Tools create their own `AsyncSessionLocal()` instances, breaking orchestrator session ownership
- No centralized audit trail for tool operations
- Missing idempotency guarantees for critical operations
- Potential multi-tenant data leakage risks
- Difficult to test and maintain

### Critical Anti-Patterns and Rules
```python
# ❌ FORBIDDEN: Tools must NEVER:
from app.core.database import AsyncSessionLocal  # VIOLATION - no DB imports
from app.models.asset import Asset               # VIOLATION - no model imports
await db.commit()                                # VIOLATION - no commits
await db.close()                                 # VIOLATION - no session management

# ✅ REQUIRED: Tools must ONLY:
# 1. Call services through registry
# 2. Return JSON responses
# 3. Handle errors gracefully
# 4. Never access database or models directly
```

## Solution Overview

Implement a service registry pattern where:
1. Orchestrator owns the database session and transaction boundaries
2. Services are injected into tools via registry
3. Tools become thin adapters between agents and services
4. All database operations go through service layer
5. Centralized audit and error handling via injected logger
6. Services may `flush()` but NEVER `commit()`

## Implementation Phases

### Phase 1: Foundation (Week 1)

#### Day 1-2: Core Infrastructure

**File: `backend/app/services/base_service.py`**
```python
import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import DatabaseError, IntegrityError
from app.core.context import RequestContext
from app.services.integration.failure_journal import log_failure

logger = logging.getLogger(__name__)

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
        # Always record to failure journal
        await log_failure(
            self.db,
            source="tool_service",
            operation=f"{self.__class__.__name__}.{operation}",
            error_message=str(error),
            details=details
        )
        
        # For severe failures only, enqueue to DLQ (non-blocking)
        if self._is_severe_failure(error):
            asyncio.create_task(self._enqueue_to_dlq(operation, error, details))
    
    def _is_severe_failure(self, error: Exception) -> bool:
        """
        Determine if failure requires DLQ retry
        Allowlist approach to avoid over-enqueueing
        """
        severe_types = (DatabaseError, IntegrityError)
        return isinstance(error, severe_types)
    
    async def _enqueue_to_dlq(self, operation: str, error: Exception, details: dict):
        """Non-blocking DLQ enqueue for severe failures"""
        try:
            # Lazy import to avoid circular dependencies
            from app.services.recovery.error_recovery_system import ErrorRecoverySystem
            
            # Initialize with proper context if needed
            recovery_system = ErrorRecoverySystem(
                db=self.db,
                context=self.context
            )
            
            await recovery_system.enqueue_for_retry(
                operation=operation,
                context=self.context,
                error=error,
                details=details
            )
        except Exception as e:
            # Never fail the main operation for DLQ issues
            logger.error(f"Failed to enqueue to DLQ: {e}")
```

**File: `backend/app/services/service_registry.py`**
```python
import logging
from typing import Dict, Type, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.context import RequestContext
from app.services.flow_orchestration.tool_audit_logger import ToolAuditLogger

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """
    Per-execution service registry - manages service lifecycle
    
    CRITICAL: Registry NEVER owns or closes the database session
    Cleanup only clears service cache and non-DB resources
    """
    
    def __init__(self, db: AsyncSession, context: RequestContext, audit_logger: Optional[ToolAuditLogger] = None):
        self.db = db  # Borrowed from orchestrator, not owned
        self.context = context  # Multi-tenant context from orchestrator
        self._services: Dict[Type, Any] = {}
        self._audit_logger = audit_logger  # Injected, not created
        self._metrics_buffer = []  # Bounded buffer
        self._max_buffer_size = 100
    
    async def get_service(self, service_class: Type) -> Any:
        """Lazily instantiate and cache services with context injection"""
        if service_class not in self._services:
            # All services receive orchestrator session and tenant context
            self._services[service_class] = service_class(self.db, self.context)
        return self._services[service_class]
    
    async def get_audit_logger(self) -> Optional[ToolAuditLogger]:
        """Get injected audit logger for tools"""
        return self._audit_logger
    
    async def record_metric(self, metric: dict):
        """Record metric with bounded buffer"""
        self._metrics_buffer.append(metric)
        
        # Flush if buffer is full
        if len(self._metrics_buffer) >= self._max_buffer_size:
            await self._flush_metrics()
    
    async def _flush_metrics(self):
        """Flush metrics buffer (non-blocking)"""
        if self._metrics_buffer:
            # Copy and clear buffer
            metrics = self._metrics_buffer.copy()
            self._metrics_buffer.clear()
            
            # Non-blocking write
            asyncio.create_task(self._write_metrics_async(metrics))
    
    async def _write_metrics_async(self, metrics: list):
        """Background metrics write"""
        # Implementation depends on metrics backend
        pass
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Cleanup - only clear cache and flush metrics
        Session lifecycle is managed by orchestrator
        """
        await self._flush_metrics()
        self._services.clear()
```

#### Day 3-4: Asset Tool Refactor

**File: `backend/app/services/flow_orchestration/tool_audit_logger.py`**
```python
import logging
from typing import Optional
from app.services.flow_orchestration.audit_logger import FlowAuditLogger
from app.core.context import RequestContext

logger = logging.getLogger(__name__)

# Use text constants instead of DB enums (avoid ALTER TYPE issues)
AUDIT_CATEGORY_TOOL_OPERATION = "TOOL_OPERATION"

class ToolAuditLogger:
    """
    Wraps FlowAuditLogger for tool operations
    Injected by orchestrator, not created by tools
    """
    
    def __init__(self, flow_audit_logger: FlowAuditLogger, context: RequestContext):
        self.base_logger = flow_audit_logger
        self.context = context
    
    async def log_tool_operation(
        self,
        tool_name: str,
        operation: str,
        agent_name: Optional[str] = None,
        input_data: dict = None,
        output_data: dict = None,
        duration_ms: float = 0,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log tool operations using correct audit API"""
        # Use agent_name from context or default
        if not agent_name:
            agent_name = getattr(self.context, 'agent_name', 'unknown')
        
        await self.base_logger.log_audit_event(
            flow_id=self.context.flow_id,
            operation=f"tool_{tool_name}_{operation}",
            category=AUDIT_CATEGORY_TOOL_OPERATION,  # Text, not enum
            level="INFO" if success else "ERROR",    # Text, not enum
            context={
                "tool_name": tool_name,
                "agent_name": agent_name,
                "input_summary": str(input_data)[:200] if input_data else "",
                "output_summary": str(output_data)[:200] if output_data else "",
                "duration_ms": duration_ms,
                "success": success,
                "error": error,
                "client_account_id": str(self.context.client_account_id),
                "engagement_id": str(self.context.engagement_id)
            }
        )
```

**Modifications to `backend/app/services/crewai_flows/tools/asset_creation_tool.py`**

```python
import os
import json
import time
import logging
from typing import Dict, Any, List, Optional
from app.services.service_registry import ServiceRegistry
from app.services.asset_service import AssetService

logger = logging.getLogger(__name__)

def create_asset_creation_tools(context_info: Dict[str, Any], registry: Optional[ServiceRegistry] = None) -> List:
    """
    Create tools with optional service registry support
    Tools must NEVER import AsyncSessionLocal or models
    """
    
    use_registry = os.getenv("USE_SERVICE_REGISTRY", "false").lower() == "true"
    
    if use_registry and registry:
        logger.info("🔧 Creating asset tools with service registry (no direct DB access)")
        return [
            AssetCreationToolWithService(registry),
            BulkAssetCreationToolWithService(registry)
        ]
    else:
        logger.warning("⚠️ Using legacy tool implementation (deprecated, removal target: 2025-02-01)")
        return [
            AssetCreationTool(context_info),
            BulkAssetCreationTool(context_info)
        ]

class AssetCreationToolWithService(BaseTool):
    """
    Asset creation tool using service layer
    NO direct DB access, NO model imports, NO commits
    """
    
    name: str = "asset_creator"
    description: str = "Create an asset using service layer with full audit trail"
    
    def __init__(self, registry: ServiceRegistry):
        super().__init__()
        self.registry = registry
    
    async def _arun(self, asset_data: Dict[str, Any]) -> str:
        """
        Execute via service - no database or model imports allowed
        Uses injected audit logger from registry
        """
        start_time = time.time()
        
        try:
            # Get service from registry
            asset_service = await self.registry.get_service(AssetService)
            
            # Service handles business logic, may flush, never commits
            asset = await asset_service.create_asset(asset_data)
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Use injected audit logger (not creating FlowAuditLogger)
            audit_logger = await self.registry.get_audit_logger()
            if audit_logger:
                await audit_logger.log_tool_operation(
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
                "asset_name": asset.name
            })
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record failure in service
            asset_service = await self.registry.get_service(AssetService)
            await asset_service.record_failure("create_asset", e, asset_data)
            
            # Audit the error
            audit_logger = await self.registry.get_audit_logger()
            if audit_logger:
                await audit_logger.log_tool_operation(
                    tool_name=self.name,
                    operation="create_asset",
                    input_data=asset_data,
                    output_data={"error": str(e)},
                    duration_ms=duration_ms,
                    success=False,
                    error=str(e)
                )
            
            return json.dumps({
                "success": False,
                "error": str(e)
            })
    
    def _run(self, asset_data: Dict[str, Any]) -> str:
        """Sync wrapper for compatibility"""
        import asyncio
        return asyncio.run(self._arun(asset_data))
```

### Phase 2: Expand Coverage (Week 2)

#### Day 6-7: Field Mapping Service Migration

**File: `backend/app/services/field_mapping_service.py`**
```python
from dataclasses import dataclass
from typing import List, Optional
from app.services.base_service import ServiceBase

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
    
    Transitional exception: This service may still contain commit() 
    from legacy code. Target removal: 2025-02-01
    """
    
    async def create_mapping(self, mapping_data: dict) -> FieldMappingDTO:
        """Create mapping with PostgreSQL upsert example"""
        from app.models.field_mapping import FieldMapping
        from sqlalchemy.dialects.postgresql import insert
        
        # Upsert pattern for idempotency (PostgreSQL ON CONFLICT)
        stmt = insert(FieldMapping).values(**mapping_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['source_field', 'target_field'],
            set_=dict(
                transformation=stmt.excluded.transformation,
                confidence_score=stmt.excluded.confidence_score
            )
        )
        
        result = await self.db.execute(stmt)
        
        # Flush to get ID (no commit!)
        await self.flush_for_id()
        
        # Return domain DTO
        return FieldMappingDTO(
            source_field=mapping_data['source_field'],
            target_field=mapping_data['target_field'],
            transformation=mapping_data.get('transformation'),
            confidence_score=mapping_data.get('confidence_score', 1.0)
        )
```

#### Day 8-9: Idempotency Helper

**File: `backend/app/services/helpers/idempotency_manager.py`**
```python
import hashlib
import json
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

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
        PostgreSQL upsert example with ON CONFLICT
        """
        stmt = insert(table).values(**data)
        
        # Build ON CONFLICT clause
        stmt = stmt.on_conflict_do_update(
            index_elements=unique_fields,  # Requires unique index on these fields
            set_={k: v for k, v in data.items() if k not in unique_fields}
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()  # Make ID available, no commit
        
        return result.returned_defaults
    
    def generate_stable_key(self, operation: str, data: dict) -> str:
        """Generate deterministic key for operation"""
        content = f"{operation}:{json.dumps(data, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()
```

### Phase 3: Full Rollout (Weeks 3-4)

#### Week 3: Orchestrator Integration with Persistent Agents

**CRITICAL: Integration with ADR-015 Persistent Agent Architecture**

```python
# backend/app/services/flow_orchestration/execution_engine_crew.py
import logging
from typing import Dict
from app.core.context import RequestContext
from app.services.service_registry import ServiceRegistry
from app.services.flow_orchestration.tool_audit_logger import ToolAuditLogger
from app.services.persistent_agents.tenant_scoped_agent_pool import TenantScopedAgentPool

logger = logging.getLogger(__name__)

class FlowCrewExecutor:
    """Executor that uses persistent agents, not direct Crew instantiation"""
    
    async def execute_with_persistent_agents(self, crew_config: Dict, context: RequestContext) -> Dict:
        """
        Execute using persistent agent pool - NO direct Crew instantiation
        Aligns with ADR-015: Persistent Multi-Tenant Agent Architecture
        """
        
        # Transaction boundary only (NOT closing session)
        async with self.db.begin():
            
            # Create audit logger wrapper
            tool_audit_logger = ToolAuditLogger(self.flow_audit_logger, context)
            
            # Create service registry with injected audit logger
            async with ServiceRegistry(self.db, context, tool_audit_logger) as registry:
                
                # Get persistent agent pool for this tenant
                agent_pool = TenantScopedAgentPool()
                
                # Inject service registry into persistent agents
                agents_with_services = []
                for agent_type in crew_config["required_agents"]:
                    # Pass agent_name to context for audit logging
                    context_with_agent = context.copy()
                    context_with_agent.agent_name = agent_type
                    
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
    
    async def _execute_with_pool(self, agents: list, tasks: list, context: RequestContext) -> Dict:
        """Execute tasks using persistent agent pool"""
        # Implementation uses persistent agents, not Crew
        pass
```

### Transitional Exceptions and Timeline

**Legacy Services with Commit() - Removal Timeline:**

| Service | Current State | Target Fix Date | Notes |
|---------|--------------|-----------------|-------|
| UserService | Has commit() | 2025-01-20 | High priority |
| DataImportService | Has commit() | 2025-01-25 | Complex refactor |
| MigrationService | Has commit() | 2025-02-01 | Low usage |

**CI Configuration for Transition:**
```yaml
# .github/workflows/service-commit-check.yml
name: Service Commit Check

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check for commit() in services
        run: |
          # Transitional exceptions (remove after 2025-02-01)
          EXCEPTIONS="UserService|DataImportService|MigrationService"
          
          # Find violations excluding exceptions
          if grep -r "\.commit(" backend/app/services/ \
             --exclude-dir=migrations \
             --exclude-dir=tests \
             | grep -v -E "$EXCEPTIONS"; then
            echo "ERROR: New commit() found in services!"
            exit 1
          fi
          
          # Warn about exceptions (becomes error after 2025-02-01)
          if [ "$(date +%Y%m%d)" -gt "20250201" ]; then
            echo "ERROR: Transitional period ended - remove all commits!"
            exit 1
          fi
```

## Progressive Rollout with Stable Hashing

```python
# backend/app/core/feature_flags.py
import hashlib
from datetime import datetime
from app.core.context import RequestContext

def is_service_registry_enabled(context: RequestContext) -> bool:
    """
    Progressive rollout with stable hashing
    Same tenant always gets same result
    """
    
    # Override for specific environments
    if os.getenv("FORCE_SERVICE_REGISTRY") == "true":
        return True
    
    # Rollout percentage (increase gradually)
    rollout_percentage = int(os.getenv("SERVICE_REGISTRY_ROLLOUT_PCT", "0"))
    
    # Stable hash - not Python's hash() which is randomized
    tenant_id = str(context.client_account_id)
    stable_hash = hashlib.sha256(tenant_id.encode()).hexdigest()
    tenant_bucket = int(stable_hash, 16) % 100
    
    return tenant_bucket < rollout_percentage
```

## Database Migrations

```sql
-- Avoid native PostgreSQL ENUMs per platform guidelines
-- Use TEXT with CHECK constraint instead

-- V1: Add audit category as TEXT (not ENUM)
ALTER TABLE audit_logs 
  ALTER COLUMN category TYPE TEXT;

ALTER TABLE audit_logs 
  ADD CONSTRAINT audit_category_check 
  CHECK (category IN ('FLOW_OPERATION', 'USER_ACTION', 'SYSTEM_EVENT', 'TOOL_OPERATION'));

-- V2: Service operations metrics table with proper index syntax
CREATE TABLE IF NOT EXISTS service_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    duration_ms FLOAT NOT NULL,
    success BOOLEAN NOT NULL,
    error_type VARCHAR(100),
    error_message TEXT,
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    flow_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Separate index creation statements (PostgreSQL syntax)
CREATE INDEX idx_service_ops_created ON service_operations (created_at DESC);
CREATE INDEX idx_service_ops_tenant ON service_operations (client_account_id, engagement_id);
CREATE INDEX idx_service_ops_service ON service_operations (service_name, operation);

-- V3: Idempotency keys table
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key_hash VARCHAR(64) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours'
);

CREATE INDEX idx_idempotency_expires ON idempotency_keys (expires_at);
```

## Connection Pooling for Async

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

def get_async_engine():
    """
    Async engine with proper pooling
    Use default AsyncAdaptedQueuePool for async
    """
    return create_async_engine(
        DATABASE_URL,
        # Let SQLAlchemy choose the right async pool
        # Don't force synchronous pool classes
        pool_pre_ping=True,  # Verify connections
        pool_size=20,         # Connection pool size
        max_overflow=40,      # Maximum overflow
        echo_pool=False       # Set True for debugging
    )
```

## Testing Strategy

### Required Test Coverage

```python
# tests/test_service_registry.py
import pytest
from app.services.service_registry import ServiceRegistry
from app.services.asset_service import AssetService

async def test_registry_never_closes_session():
    """Registry must not close the orchestrator's session"""
    mock_session = Mock(spec=AsyncSession)
    context = Mock()
    
    async with ServiceRegistry(mock_session, context) as registry:
        service = await registry.get_service(AssetService)
        assert service.db is mock_session
    
    # Session should never be closed by registry
    mock_session.close.assert_not_called()

async def test_tool_no_db_imports():
    """Tools must not import database or models"""
    import ast
    import inspect
    from app.services.crewai_flows.tools.asset_creation_tool import AssetCreationToolWithService
    
    source = inspect.getsource(AssetCreationToolWithService)
    tree = ast.parse(source)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "AsyncSessionLocal" not in alias.name
                assert "models" not in alias.name
        elif isinstance(node, ast.ImportFrom):
            assert node.module != "app.core.database"
            assert not node.module.startswith("app.models")

async def test_service_flush_not_commit():
    """Services may flush but never commit"""
    from app.services.asset_service import AssetService
    
    mock_session = Mock(spec=AsyncSession)
    context = Mock()
    service = AssetService(mock_session, context)
    
    # Service may flush
    await service.flush_for_id()
    mock_session.flush.assert_called()
    
    # Service must never commit
    mock_session.commit.assert_not_called()
```

## Summary

### Critical Rules Enforced

1. **Tools must NEVER:**
   - Import `AsyncSessionLocal` or any database modules
   - Import models directly
   - Call commit() or manage sessions
   - Create their own audit loggers

2. **Services must:**
   - Only flush(), never commit()
   - Return domain DTOs, not Pydantic models
   - Handle errors gracefully
   - Record failures to journal

3. **Orchestrator must:**
   - Own the database session
   - Manage transaction boundaries with `begin()`
   - Inject audit logger into registry
   - Use persistent agent pool (no direct Crew)

4. **Registry must:**
   - Never close the session
   - Provide injected audit logger to tools
   - Cache services per execution
   - Clear only cache on cleanup

---

*Last Updated: 2025-01-13*
*Version: 3.0*
*Status: Final - Ready for Implementation*
*Target Completion: 2025-02-01*