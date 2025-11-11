# Milestone: Decommission Flow Implementation

**Target Version**: v2.5.0
**Estimated Duration**: 12 weeks
**Priority**: High
**Type**: Feature - New Flow Implementation

## Overview

Implement the complete Decommission Flow for safe retirement of legacy systems, following ADR-027 (FlowTypeConfig), ADR-025 (Child Flow Service), and ADR-006 (MFO Two-Table Pattern). This milestone delivers AI-powered decommission planning, data retention automation, safe execution with rollback, and comprehensive validation.

## Success Criteria

- [ ] All 3 phases (decommission_planning, data_migration, system_shutdown) fully functional
- [ ] Integration with Assessment Flow (6R "Retire" strategy)
- [ ] Integration with Wave Execution (post-migration decommission)
- [ ] TenantScopedAgentPool with 7 decommission agents operational
- [ ] All E2E tests passing (Playwright)
- [ ] Zero pre-commit violations
- [ ] API documentation complete
- [ ] User guide published

## Milestone Statistics

**Total Issues**: 22
**Story Points**: 185
**Backend Issues**: 10
**Frontend Issues**: 8
**Testing Issues**: 3
**Documentation Issues**: 1

---

## Phase 0: Preparation & Mock Preservation (Week 1)

### Issue #1: Rename Existing Decommission Section to "Decom"
**Labels**: `frontend`, `refactoring`, `preparation`
**Story Points**: 3
**Assignee**: TBD
**Priority**: Critical - Blocker for Phase 1

#### Description
Preserve existing mock pages by moving the entire Decommission section below FinOps and above Observability, renaming it to "Decom". This preserves reference wireframes while clearing space for the production implementation.

#### Acceptance Criteria
- [ ] Sidebar link "Decommission" → "Decom" with same icon
- [ ] Decom section moved below FinOps, above Observability
- [ ] All Decom pages accessible at new routes:
  - `/decom/overview` (was `/decommission/overview`)
  - `/decom/planning` (was `/decommission/planning`)
  - `/decom/data-retention` (was `/decommission/data-retention`)
  - `/decom/execution` (was `/decommission/execution`)
  - `/decom/validation` (was `/decommission/validation`)
- [ ] All existing mock data preserved
- [ ] No broken links in sidebar navigation
- [ ] URL redirects from old `/decommission/*` to `/decom/*`

#### Technical Details

**Files to Update**:
```typescript
// 1. Sidebar component
src/components/Sidebar.tsx
  - Change label: "Decommission" → "Decom"
  - Change href: "/decommission/overview" → "/decom/overview"
  - Move section after FinOps, before Observability

// 2. Rename page directory
mv src/pages/decommission/ src/pages/decom/

// 3. Update Next.js routing (if applicable)
// Create redirects in next.config.js or middleware.ts
```

**Implementation Steps**:
1. Update `Sidebar.tsx` navigation order and labels
2. Rename `/pages/decommission/` → `/pages/decom/`
3. Update all internal links within Decom pages
4. Add redirects for backwards compatibility
5. Test all navigation flows
6. Update any route guards/permissions

#### Testing
- [ ] Navigate to all Decom pages via sidebar
- [ ] Verify Decom appears below FinOps
- [ ] Verify old `/decommission/*` URLs redirect
- [ ] Check no console errors
- [ ] Verify mock data displays correctly

#### References
- Solution Document: Section 1.1 (Architecture Overview)
- Similar pattern: Assessment Flow mock → production migration

---

## Phase 1: Database Foundation (Weeks 1-2)

### Issue #2: Create Decommission Database Schema (Alembic Migration)
**Labels**: `backend`, `database`, `migration`
**Story Points**: 13
**Assignee**: TBD
**Priority**: Critical - Blocker for Phase 2

#### Description
Create comprehensive database schema for decommission flow using the two-table MFO pattern. Includes 6 new tables: decommission_flows (child flow), decommission_plans, data_retention_policies, archive_jobs, decommission_execution_logs, decommission_validation_checks.

#### Acceptance Criteria
- [ ] Alembic migration `120_create_decommission_tables.py` created
- [ ] All 6 tables created in `migration` schema
- [ ] Phase columns match FlowTypeConfig exactly:
  - `decommission_planning_status`
  - `data_migration_status`
  - `system_shutdown_status`
- [ ] All foreign keys reference correct tables
- [ ] All indexes created for performance
- [ ] CHECK constraints enforce valid phase/status values
- [ ] Migration is idempotent (can run multiple times)
- [ ] Migration tested locally and on staging
- [ ] Downgrade path documented (no actual downgrade implementation per patterns)

#### Technical Details

**Migration File**: `backend/alembic/versions/120_create_decommission_tables.py`

**Tables to Create** (Per Solution Document Section 3):

1. **decommission_flows** (Child Flow Table)
```sql
CREATE TABLE migration.decommission_flows (
    flow_id UUID PRIMARY KEY,
    master_flow_id UUID NOT NULL REFERENCES migration.crewai_flow_state_extensions(flow_id),
    client_account_id UUID NOT NULL,
    engagement_id UUID NOT NULL,
    flow_name VARCHAR(255),
    created_by VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    current_phase VARCHAR(50) NOT NULL DEFAULT 'decommission_planning',
    selected_system_ids UUID[] NOT NULL,
    system_count INTEGER NOT NULL,

    -- Phase progress (MUST match FlowTypeConfig)
    decommission_planning_status VARCHAR(50) DEFAULT 'pending',
    decommission_planning_completed_at TIMESTAMP WITH TIME ZONE,
    data_migration_status VARCHAR(50) DEFAULT 'pending',
    data_migration_completed_at TIMESTAMP WITH TIME ZONE,
    system_shutdown_status VARCHAR(50) DEFAULT 'pending',
    system_shutdown_started_at TIMESTAMP WITH TIME ZONE,
    system_shutdown_completed_at TIMESTAMP WITH TIME ZONE,

    decommission_strategy JSONB NOT NULL DEFAULT '{}',
    runtime_state JSONB NOT NULL DEFAULT '{}',
    total_systems_decommissioned INTEGER DEFAULT 0,
    estimated_annual_savings DECIMAL(15, 2),
    compliance_score DECIMAL(5, 2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN (
        'initialized', 'decommission_planning', 'data_migration',
        'system_shutdown', 'completed', 'failed'
    )),
    CONSTRAINT valid_phase CHECK (current_phase IN (
        'decommission_planning', 'data_migration', 'system_shutdown', 'completed'
    ))
);
```

2. **decommission_plans** (Per-System Plans)
3. **data_retention_policies** (Compliance Policies)
4. **archive_jobs** (Data Archival Tracking)
5. **decommission_execution_logs** (Audit Trail)
6. **decommission_validation_checks** (Post-Decommission Validation)

**Full schemas in Solution Document Section 3.2-3.3**

#### Implementation Steps
1. Create migration file with 3-digit prefix: `120_create_decommission_tables.py`
2. Define upgrade() with all CREATE TABLE statements
3. Add indexes for multi-tenant queries and status lookups
4. Add CHECK constraints matching FlowTypeConfig phases
5. Define downgrade() with NotImplementedError (per migration patterns)
6. Test migration: `alembic upgrade head`
7. Verify all tables and indexes created
8. Test rollback: `alembic downgrade -1` (should show NotImplementedError message)

#### Testing
```bash
# Run migration
cd backend && alembic upgrade head

# Verify tables exist
docker exec -it migration_postgres psql -U postgres -d migration_db \
  -c "\dt migration.decommission*"

# Verify columns match FlowTypeConfig
docker exec -it migration_postgres psql -U postgres -d migration_db \
  -c "\d migration.decommission_flows"

# Check constraints
docker exec -it migration_postgres psql -U postgres -d migration_db \
  -c "SELECT constraint_name, check_clause
      FROM information_schema.check_constraints
      WHERE table_name = 'decommission_flows';"
```

#### References
- Solution Document: Section 3 (Database Schema Design)
- ADR-027: Phase naming requirements
- Migration Pattern: `backend/alembic/versions/092_add_supported_versions_requirement_details.py`

---

### Issue #3: Create SQLAlchemy Models for Decommission Flow
**Labels**: `backend`, `models`, `database`
**Story Points**: 8
**Assignee**: TBD
**Depends On**: #2

#### Description
Create SQLAlchemy ORM models for all 6 decommission tables with proper relationships, type hints, and validation. Follow existing model patterns from Assessment/Collection flows.

#### Acceptance Criteria
- [ ] `backend/app/models/decommission_flow.py` created with all models
- [ ] All models inherit from `Base`
- [ ] All relationships defined with proper foreign keys
- [ ] Type hints on all attributes
- [ ] `__repr__()` methods for debugging
- [ ] JSON columns have proper serialization
- [ ] Models registered in `backend/app/models/__init__.py`
- [ ] No circular import issues
- [ ] All models pass mypy type checking

#### Technical Details

**File**: `backend/app/models/decommission_flow.py`

**Models to Create**:
```python
from sqlalchemy import Column, UUID, String, Integer, DECIMAL, TIMESTAMP, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class DecommissionFlow(Base):
    """Child flow for decommission operations (ADR-006 two-table pattern)."""
    __tablename__ = "decommission_flows"
    __table_args__ = {"schema": "migration"}

    flow_id = Column(UUID(as_uuid=True), primary_key=True)
    master_flow_id = Column(UUID(as_uuid=True), ForeignKey("migration.crewai_flow_state_extensions.flow_id"))
    client_account_id = Column(UUID(as_uuid=True), nullable=False)
    engagement_id = Column(UUID(as_uuid=True), nullable=False)

    # ... (full model per Solution Document Section 3.2)

class DecommissionPlan(Base):
    """Per-system decommission plan with dependencies and risks."""
    __tablename__ = "decommission_plans"
    __table_args__ = {"schema": "migration"}
    # ... (full model)

# DataRetentionPolicy, ArchiveJob, DecommissionExecutionLog, DecommissionValidationCheck
```

#### Implementation Steps
1. Create `decommission_flow.py` in `models/` directory
2. Define all 6 model classes
3. Add relationships (e.g., `DecommissionFlow.plans`)
4. Add `__repr__()` for each model
5. Register models in `__init__.py`
6. Run mypy: `cd backend && mypy app/models/decommission_flow.py`
7. Test model imports in Python REPL

#### Testing
```python
# Test model imports
from app.models.decommission_flow import DecommissionFlow, DecommissionPlan

# Test model instantiation
flow = DecommissionFlow(
    flow_id=uuid4(),
    client_account_id=uuid4(),
    status="initialized",
    current_phase="decommission_planning"
)

# Verify __repr__
print(flow)  # Should show readable representation
```

#### References
- Solution Document: Section 3.2-3.3
- Pattern: `backend/app/models/assessment_flow.py`
- Pattern: `backend/app/models/collection_flow.py`

---

### Issue #4: Create DecommissionFlowRepository
**Labels**: `backend`, `repository`, `database`
**Story Points**: 8
**Assignee**: TBD
**Depends On**: #3

#### Description
Create repository layer for decommission flow CRUD operations with multi-tenant scoping, async/await patterns, and proper error handling.

#### Acceptance Criteria
- [ ] `backend/app/repositories/decommission_flow_repository.py` created
- [ ] All CRUD operations implemented:
  - `create()`, `get_by_flow_id()`, `get_by_master_flow_id()`
  - `update_status()`, `update_phase_status()`
  - `list_by_tenant()`, `delete()`
- [ ] All queries include `client_account_id` and `engagement_id` scoping
- [ ] Async/await throughout
- [ ] Proper exception handling
- [ ] Type hints on all methods
- [ ] Docstrings for all public methods
- [ ] Unit tests for all methods

#### Technical Details

**File**: `backend/app/repositories/decommission_flow_repository.py`

```python
from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decommission_flow import DecommissionFlow

class DecommissionFlowRepository:
    """Repository for decommission flow operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        flow: DecommissionFlow
    ) -> DecommissionFlow:
        """Create new decommission flow."""
        self.db.add(flow)
        await self.db.flush()
        return flow

    async def get_by_flow_id(
        self,
        flow_id: UUID,
        client_account_id: UUID,
        engagement_id: UUID
    ) -> Optional[DecommissionFlow]:
        """Get flow by ID with tenant scoping."""
        stmt = select(DecommissionFlow).where(
            DecommissionFlow.flow_id == flow_id,
            DecommissionFlow.client_account_id == client_account_id,
            DecommissionFlow.engagement_id == engagement_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ... (remaining methods per Solution Document Section 3.2)
```

#### Implementation Steps
1. Create repository class with `__init__(db: AsyncSession)`
2. Implement all CRUD methods
3. Add multi-tenant scoping to ALL queries
4. Add error handling (try/except for DB errors)
5. Write unit tests: `backend/tests/repositories/test_decommission_flow_repository.py`
6. Run tests: `cd backend && pytest tests/repositories/test_decommission_flow_repository.py -v`

#### Testing
```python
# Unit test example
async def test_create_decommission_flow(db_session):
    repo = DecommissionFlowRepository(db_session)

    flow = DecommissionFlow(
        flow_id=uuid4(),
        master_flow_id=uuid4(),
        client_account_id=uuid4(),
        engagement_id=uuid4(),
        status="initialized"
    )

    result = await repo.create(flow)
    assert result.flow_id == flow.flow_id
    assert result.status == "initialized"
```

#### References
- Solution Document: Section 3.2
- Pattern: `backend/app/repositories/assessment_flow_repository.py`
- Pattern: `backend/app/repositories/collection_flow_repository.py`

---

## Phase 2: Backend API & MFO Integration (Weeks 3-4)

### Issue #5: Implement MFO Integration Layer
**Labels**: `backend`, `mfo`, `api`
**Story Points**: 13
**Assignee**: TBD
**Depends On**: #4

#### Description
Implement MFO integration helpers following ADR-006 two-table pattern. Provides atomic creation/update of master + child flows, status synchronization per ADR-012.

#### Acceptance Criteria
- [ ] `backend/app/api/v1/endpoints/decommission_flow/mfo_integration.py` created
- [ ] `create_decommission_via_mfo()` implemented with atomic transaction
- [ ] `get_decommission_status_via_mfo()` returns child flow status (ADR-012)
- [ ] `update_decommission_phase_via_mfo()` syncs master + child atomically
- [ ] `resume_decommission_flow()` implemented
- [ ] All functions include proper error handling
- [ ] Multi-tenant scoping enforced
- [ ] Integration tests pass

#### Technical Details

**File**: `backend/app/api/v1/endpoints/decommission_flow/mfo_integration.py`

```python
"""
Decommission Flow MFO Integration
Per ADR-006: Two-table pattern for master + child flows
"""

from uuid import UUID, uuid4
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

async def create_decommission_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    system_ids: List[UUID],
    user_id: str,
    flow_name: str | None,
    decommission_strategy: Dict[str, Any],
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Create decommission flow through MFO using two-table pattern.

    Returns:
        {
            "flow_id": "uuid",
            "status": "initialized",
            "current_phase": "decommission_planning",
            "selected_systems": [...],
            "message": "..."
        }
    """
    flow_id = uuid4()

    try:
        async with db.begin():  # Atomic transaction
            # Step 1: Create master flow (lifecycle management)
            master_flow = CrewAIFlowStateExtensions(
                flow_id=flow_id,
                flow_type="decommission",
                flow_status="running",
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                user_id=user_id,
                flow_configuration={"created_via": "decommission_api"},
                flow_persistence_data={}
            )
            db.add(master_flow)
            await db.flush()

            # Step 2: Create child flow (operational state)
            child_flow = DecommissionFlow(
                flow_id=flow_id,
                master_flow_id=master_flow.flow_id,
                client_account_id=client_account_id,
                engagement_id=engagement_id,
                created_by=user_id,
                status="initialized",
                current_phase="decommission_planning",
                selected_system_ids=system_ids,
                system_count=len(system_ids),
                decommission_strategy=decommission_strategy
            )
            db.add(child_flow)

            await db.commit()

        return {
            "flow_id": str(flow_id),
            "status": child_flow.status,
            "current_phase": child_flow.current_phase,
            "selected_systems": [str(sid) for sid in system_ids],
            "message": f"Decommission flow initialized for {len(system_ids)} systems"
        }

    except Exception as e:
        logger.error(f"Failed to create decommission flow: {e}")
        raise
```

**Full implementation in Solution Document Section 3.2**

#### Implementation Steps
1. Create `mfo_integration.py` file
2. Implement `create_decommission_via_mfo()` with atomic transaction
3. Implement `get_decommission_status_via_mfo()` (uses child flow per ADR-012)
4. Implement `update_decommission_phase_via_mfo()` with master/child sync
5. Add error handling and logging
6. Write integration tests
7. Test with Docker: Create flow → Verify in database

#### Testing
```python
# Integration test
async def test_create_decommission_via_mfo(db_session):
    result = await create_decommission_via_mfo(
        client_account_id=TEST_CLIENT_ID,
        engagement_id=TEST_ENGAGEMENT_ID,
        system_ids=[uuid4(), uuid4()],
        user_id="test_user",
        flow_name="Test Decommission",
        decommission_strategy={"priority": "cost_savings"},
        db=db_session
    )

    assert "flow_id" in result
    assert result["status"] == "initialized"
    assert result["current_phase"] == "decommission_planning"

    # Verify both tables created
    master = await get_master_flow(result["flow_id"])
    child = await get_child_flow(result["flow_id"])
    assert master.flow_type == "decommission"
    assert child.system_count == 2
```

#### References
- Solution Document: Section 3.2 (MFO Integration Layer)
- ADR-006: Master Flow Orchestrator
- ADR-012: Status Management Separation
- Pattern: `backend/app/api/v1/endpoints/assessment_flow/mfo_integration.py`

---

### Issue #6: Implement Flow Management Endpoints
**Labels**: `backend`, `api`, `fastapi`
**Story Points**: 13
**Assignee**: TBD
**Depends On**: #5

#### Description
Create FastAPI endpoints for decommission flow management: initialize, get status, resume, pause, cancel. Follows Assessment Flow pattern with MFO integration.

#### Acceptance Criteria
- [ ] `backend/app/api/v1/endpoints/decommission_flow/flow_management.py` created
- [ ] POST `/initialize` - Create new decommission flow
- [ ] GET `/{flow_id}/status` - Get flow status (child flow per ADR-012)
- [ ] POST `/{flow_id}/resume` - Resume paused flow
- [ ] POST `/{flow_id}/pause` - Pause running flow
- [ ] POST `/{flow_id}/cancel` - Cancel flow
- [ ] All endpoints include authentication (`get_current_user`)
- [ ] All endpoints include tenant verification
- [ ] Background tasks start agent execution
- [ ] OpenAPI docs generated correctly
- [ ] Integration tests pass

#### Technical Details

**File**: `backend/app/api/v1/endpoints/decommission_flow/flow_management.py`

```python
"""
Decommission flow management endpoints.
Handles initialization, status, resume, pause, and cancellation.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.v1.auth.auth_utils import get_current_user
from app.core.database import get_db
from app.core.context_helpers import verify_client_access, verify_engagement_access
from app.schemas.decommission_flow import (
    DecommissionFlowCreateRequest,
    DecommissionFlowResponse,
    DecommissionFlowStatusResponse
)

from .mfo_integration import (
    create_decommission_via_mfo,
    get_decommission_status_via_mfo
)

router = APIRouter()

@router.post("/initialize", response_model=DecommissionFlowResponse)
async def initialize_decommission_flow(
    request: DecommissionFlowCreateRequest,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
):
    """
    Initialize decommission flow for selected systems.

    Eligible systems:
    - Pre-migration: 6R strategy = "Retire"
    - Post-migration: Successfully migrated, past grace period
    """
    try:
        await verify_engagement_access(db, engagement_id, client_account_id)

        # Verify systems eligible for decommission
        await verify_systems_eligible(
            db, request.selected_system_ids, client_account_id, engagement_id
        )

        # Create flow via MFO
        result = await create_decommission_via_mfo(
            client_account_id=UUID(client_account_id),
            engagement_id=UUID(engagement_id),
            system_ids=[UUID(sid) for sid in request.selected_system_ids],
            user_id=current_user.id,
            flow_name=request.flow_name,
            decommission_strategy=request.decommission_strategy,
            db=db
        )

        flow_id = result["flow_id"]

        # Start planning phase in background
        background_tasks.add_task(
            execute_decommission_planning_phase,
            flow_id, client_account_id, engagement_id, current_user.id
        )

        return DecommissionFlowResponse(**result)

    except Exception as e:
        logger.error(f"Decommission flow initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{flow_id}/status", response_model=DecommissionFlowStatusResponse)
async def get_decommission_flow_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
):
    """Get current status of decommission flow (child flow per ADR-012)."""
    try:
        status = await get_decommission_status_via_mfo(
            UUID(flow_id), UUID(client_account_id), UUID(engagement_id), db
        )
        return DecommissionFlowStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Resume, pause, cancel endpoints follow same pattern
```

**Full implementation in Solution Document Section 5**

#### Implementation Steps
1. Create `flow_management.py` router
2. Implement initialize endpoint with background task
3. Implement status endpoint (returns child flow status)
4. Implement resume/pause/cancel endpoints
5. Create Pydantic schemas in `backend/app/schemas/decommission_flow.py`
6. Register router in `router_registry.py`
7. Test with Postman/curl
8. Write integration tests

#### Testing
```bash
# Test initialize endpoint
curl -X POST http://localhost:8000/api/v1/decommission-flow/initialize \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_system_ids": ["uuid1", "uuid2"],
    "flow_name": "Q1 2025 Decommission",
    "decommission_strategy": {"priority": "cost_savings"}
  }'

# Test status endpoint
curl -X GET http://localhost:8000/api/v1/decommission-flow/$FLOW_ID/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID"
```

#### References
- Solution Document: Section 5.1-5.2
- Pattern: `backend/app/api/v1/endpoints/assessment_flow/flow_management.py`
- ADR-012: Child flow status for UI decisions

---

### Issue #7: Create Pydantic Schemas for API Contracts
**Labels**: `backend`, `schemas`, `validation`
**Story Points**: 5
**Assignee**: TBD
**Depends On**: #6

#### Description
Create Pydantic schemas for request/response validation following API field naming standards (snake_case per CLAUDE.md).

#### Acceptance Criteria
- [ ] `backend/app/schemas/decommission_flow.py` created
- [ ] All request schemas validated (DecommissionFlowCreateRequest, etc.)
- [ ] All response schemas typed (DecommissionFlowResponse, etc.)
- [ ] snake_case field naming throughout
- [ ] Field validators for enums (status, phase values)
- [ ] Proper inheritance from BaseModel
- [ ] Example values in docstrings
- [ ] OpenAPI docs display correctly

#### Technical Details

**File**: `backend/app/schemas/decommission_flow.py`

```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime

class DecommissionFlowCreateRequest(BaseModel):
    """Request to create new decommission flow."""
    selected_system_ids: List[str] = Field(
        ...,
        description="List of Asset IDs to decommission",
        min_items=1,
        max_items=100
    )
    flow_name: Optional[str] = Field(
        None,
        description="Optional name for decommission flow"
    )
    decommission_strategy: Dict[str, Any] = Field(
        default_factory=dict,
        description="Decommission strategy configuration",
        example={
            "priority": "cost_savings",
            "execution_mode": "phased",
            "rollback_enabled": True
        }
    )

    @validator('decommission_strategy')
    def validate_strategy(cls, v):
        if 'priority' in v and v['priority'] not in ['cost_savings', 'risk_reduction', 'compliance']:
            raise ValueError("Invalid priority value")
        return v

class DecommissionFlowResponse(BaseModel):
    """Response after creating decommission flow."""
    flow_id: str
    status: str
    current_phase: str
    next_phase: str
    selected_systems: List[str]
    message: str

class PhaseProgress(BaseModel):
    """Phase progress status (matches FlowTypeConfig phases)."""
    decommission_planning: str
    data_migration: str
    system_shutdown: str

class DecommissionFlowStatusResponse(BaseModel):
    """Full status response for decommission flow."""
    flow_id: str
    master_flow_id: str
    status: str
    current_phase: str
    system_count: int
    phase_progress: PhaseProgress
    metrics: Dict[str, Any]
    runtime_state: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

#### Implementation Steps
1. Create schemas file with all request/response models
2. Add field validators for enums
3. Add example values for OpenAPI docs
4. Test schema validation with pytest
5. Verify OpenAPI docs render correctly at `/docs`

#### Testing
```python
def test_create_request_validation():
    # Valid request
    req = DecommissionFlowCreateRequest(
        selected_system_ids=["uuid1", "uuid2"],
        decommission_strategy={"priority": "cost_savings"}
    )
    assert len(req.selected_system_ids) == 2

    # Invalid priority
    with pytest.raises(ValueError):
        DecommissionFlowCreateRequest(
            selected_system_ids=["uuid1"],
            decommission_strategy={"priority": "invalid"}
        )
```

#### References
- Solution Document: Section 5.2
- API Field Naming: `/docs/guidelines/API_REQUEST_PATTERNS.md`
- Pattern: `backend/app/schemas/assessment_flow.py`

---

## Phase 3: Child Flow Service & Agent Architecture (Weeks 5-6)

### Issue #8: Implement DecommissionChildFlowService (ADR-025)
**Labels**: `backend`, `service`, `mfo`
**Story Points**: 13
**Assignee**: TBD
**Depends On**: #7

#### Description
Create child flow service implementing ADR-025 pattern for phase execution routing. Single execution path via `execute_phase()` method, integrating with TenantScopedAgentPool.

#### Acceptance Criteria
- [ ] `backend/app/services/child_flows/decommission_child_flow_service.py` created
- [ ] Inherits from `BaseChildFlowService`
- [ ] `execute_phase()` routes to phase-specific handlers
- [ ] Phase handlers for all 3 phases:
  - `_execute_decommission_planning()`
  - `_execute_data_migration()`
  - `_execute_system_shutdown()`
- [ ] Integration with `DecommissionAgentPool`
- [ ] `get_flow_by_master_id()` implemented
- [ ] `update_flow_status()` implemented
- [ ] No `crew_class` usage (deprecated per ADR-025)
- [ ] Unit tests for all methods

#### Technical Details

**File**: `backend/app/services/child_flows/decommission_child_flow_service.py`

```python
"""
Decommission Child Flow Service
Per ADR-025: Single execution path via child_flow_service
"""

from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.child_flows.base_child_flow_service import BaseChildFlowService
from app.repositories.decommission_flow_repository import DecommissionFlowRepository
from app.services.persistent_agents.decommission_agent_pool import DecommissionAgentPool
from app.models.decommission_flow import DecommissionFlow

class DecommissionChildFlowService(BaseChildFlowService):
    """
    Handles all decommission flow child operations.
    Follows Discovery/Collection pattern per ADR-025.
    """

    def __init__(self, db: AsyncSession, context: Dict[str, Any]):
        super().__init__(db, context)
        self.repository = DecommissionFlowRepository(db)
        self.agent_pool = DecommissionAgentPool()

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute phase by routing to appropriate handler.
        Per ADR-027: phase_name matches FlowTypeConfig phase name.
        """
        child_flow = await self.repository.get_by_flow_id(
            UUID(flow_id),
            UUID(self.context["client_account_id"]),
            UUID(self.context["engagement_id"])
        )

        if not child_flow:
            raise ValueError(f"Decommission flow {flow_id} not found")

        # Route to phase-specific handler
        if phase_name == "decommission_planning":
            return await self._execute_decommission_planning(child_flow, phase_input)
        elif phase_name == "data_migration":
            return await self._execute_data_migration(child_flow, phase_input)
        elif phase_name == "system_shutdown":
            return await self._execute_system_shutdown(child_flow, phase_input)
        else:
            raise ValueError(f"Unknown phase: {phase_name}")

    async def _execute_decommission_planning(
        self,
        child_flow: DecommissionFlow,
        phase_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Phase 1: Decommission Planning"""
        # Get agents from pool
        dependency_analyzer = await self.agent_pool.get_agent(
            "dependency_analyzer",
            str(child_flow.client_account_id),
            str(child_flow.engagement_id)
        )
        risk_assessor = await self.agent_pool.get_agent(
            "risk_assessor",
            str(child_flow.client_account_id),
            str(child_flow.engagement_id)
        )
        cost_analyst = await self.agent_pool.get_agent(
            "cost_optimization_analyst",
            str(child_flow.client_account_id),
            str(child_flow.engagement_id)
        )

        # Execute planning crew
        result = await execute_decommission_planning_crew(
            child_flow, dependency_analyzer, risk_assessor, cost_analyst
        )

        # Update phase status
        await self.repository.update_phase_status(
            child_flow.flow_id,
            "decommission_planning",
            "completed",
            child_flow.client_account_id,
            child_flow.engagement_id
        )

        return result

    # _execute_data_migration() and _execute_system_shutdown() follow same pattern
```

**Full implementation in Solution Document Section 4.0**

#### Implementation Steps
1. Create child flow service class inheriting from `BaseChildFlowService`
2. Implement `execute_phase()` with phase routing
3. Implement all 3 phase handler methods
4. Integrate with `DecommissionAgentPool` (Issue #9)
5. Implement `get_flow_by_master_id()` and `update_flow_status()`
6. Write unit tests mocking agent pool
7. Test phase routing logic

#### Testing
```python
async def test_execute_phase_routing():
    service = DecommissionChildFlowService(db, context)

    # Test routing to decommission_planning
    result = await service.execute_phase(
        flow_id=str(test_flow_id),
        phase_name="decommission_planning",
        phase_input={}
    )

    assert result["phase"] == "decommission_planning"
    assert result["status"] == "completed"

    # Test invalid phase
    with pytest.raises(ValueError, match="Unknown phase"):
        await service.execute_phase(
            flow_id=str(test_flow_id),
            phase_name="invalid_phase",
            phase_input={}
        )
```

#### References
- Solution Document: Section 4.0 (Child Flow Service Pattern)
- ADR-025: Child Flow Service Pattern
- Pattern: `backend/app/services/child_flows/collection_child_flow_service.py`

---

### Issue #9: Create DecommissionAgentPool with TenantScopedAgentPool
**Labels**: `backend`, `agents`, `crewai`
**Story Points**: 13
**Assignee**: TBD
**Depends On**: #8

#### Description
Create decommission-specific agent pool configuration with 7 agents (Dependency Analyzer, Risk Assessor, Data Retention Specialist, Archive Orchestrator, Execution Safety Agent, Validation Engineer, Cost Optimization Analyst). Integrates with TenantScopedAgentPool for lifecycle management.

#### Acceptance Criteria
- [ ] `backend/app/services/persistent_agents/decommission_agent_pool.py` created
- [ ] All 7 agent configurations defined with AgentConfig
- [ ] `memory=False` per ADR-024 (TenantMemoryManager instead)
- [ ] Agent tools specified (cmdb_query, compliance_checker, etc.)
- [ ] `DecommissionAgentPool` class wraps `TenantScopedAgentPool`
- [ ] `get_agent()` method with tenant scoping
- [ ] `release_agents()` for cleanup
- [ ] Agent pool registered in agent registry
- [ ] Unit tests for agent retrieval

#### Technical Details

**File**: `backend/app/services/persistent_agents/decommission_agent_pool.py`

```python
"""
Decommission-specific agent pool configuration.
Integrates with TenantScopedAgentPool for lifecycle management.
"""

from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool, AgentConfig
)

# Decommission agent definitions
DECOMMISSION_AGENTS = {
    "dependency_analyzer": AgentConfig(
        name="Dependency Analyzer",
        role="System Dependency Mapping Specialist",
        goal="Identify all system dependencies to prevent downstream failures",
        backstory="""Expert in enterprise architecture with 15+ years analyzing
        system dependencies. Creates comprehensive dependency maps to ensure safe
        decommissioning without impacting dependent systems.""",
        tools=["cmdb_query", "network_discovery", "api_dependency_mapper"],
        memory=False  # Per ADR-024
    ),

    "risk_assessor": AgentConfig(
        name="Decommission Risk Assessor",
        role="Risk Analysis and Mitigation Specialist",
        goal="Assess decommission risks and create mitigation strategies",
        backstory="""20+ years in IT risk management, specialized in system
        retirement risks. Evaluates business impact, technical risks, and
        regulatory compliance to ensure safe decommissioning.""",
        tools=["risk_matrix_calculator", "compliance_checker", "impact_analyzer"],
        memory=False
    ),

    "data_retention_specialist": AgentConfig(
        name="Data Retention Specialist",
        role="Compliance and Data Archival Expert",
        goal="Ensure data retention compliance and secure archival",
        backstory="""Compliance expert with deep knowledge of GDPR, SOX, HIPAA,
        and PCI-DSS. Creates retention policies that balance legal requirements
        with storage optimization.""",
        tools=["compliance_policy_lookup", "data_classifier", "archive_calculator"],
        memory=False
    ),

    "archive_orchestrator": AgentConfig(
        name="Archive Orchestrator",
        role="Data Migration and Archive Automation Specialist",
        goal="Execute data archival with integrity verification",
        backstory="""Data migration expert with 10+ years managing petabyte-scale
        archives. Ensures data integrity, encryption, and accessibility while
        optimizing storage costs.""",
        tools=["data_migrator", "integrity_verifier", "encryption_service"],
        memory=False
    ),

    "execution_safety_agent": AgentConfig(
        name="Execution Safety Guardian",
        role="Safe Decommission Execution Specialist",
        goal="Execute decommissions safely with rollback capabilities",
        backstory="""Infrastructure automation expert with zero-downtime deployment
        expertise. Implements safety checks, gradual shutdowns, and automated
        rollback for risk-free decommissioning.""",
        tools=["service_controller", "health_monitor", "rollback_orchestrator"],
        memory=False
    ),

    "validation_engineer": AgentConfig(
        name="Validation Engineer",
        role="Post-Decommission Verification Specialist",
        goal="Verify successful decommission and complete cleanup",
        backstory="""Quality assurance engineer specialized in infrastructure
        validation. Performs comprehensive checks to ensure complete system
        removal and resource cleanup.""",
        tools=["access_verifier", "resource_scanner", "compliance_auditor"],
        memory=False
    ),

    "cost_optimization_analyst": AgentConfig(
        name="Cost Optimization Analyst",
        role="Decommission ROI and Savings Analyst",
        goal="Calculate and verify cost savings from decommissioning",
        backstory="""FinOps specialist with expertise in TCO analysis. Tracks
        infrastructure costs, calculates savings, and provides ROI metrics for
        decommission initiatives.""",
        tools=["cost_calculator", "roi_analyzer", "savings_tracker"],
        memory=False
    )
}

class DecommissionAgentPool:
    """
    Manages decommission-specific agent pool using TenantScopedAgentPool.
    """

    def __init__(self):
        self.agent_pool = TenantScopedAgentPool(
            agent_configs=DECOMMISSION_AGENTS,
            pool_name="decommission_agents"
        )

    async def get_agent(
        self,
        agent_key: str,
        client_account_id: str,
        engagement_id: str
    ):
        """Get agent instance scoped to tenant."""
        return await self.agent_pool.get_agent(
            agent_key, client_account_id, engagement_id
        )

    async def release_agents(
        self,
        client_account_id: str,
        engagement_id: str
    ):
        """Release all agents for tenant when flow completes."""
        await self.agent_pool.release_tenant_agents(
            client_account_id, engagement_id
        )
```

**Full implementation in Solution Document Section 5.1**

#### Implementation Steps
1. Create agent pool configuration file
2. Define all 7 agent configs with tools
3. Set `memory=False` per ADR-024
4. Create `DecommissionAgentPool` wrapper class
5. Implement `get_agent()` with tenant scoping
6. Implement `release_agents()` for cleanup
7. Write unit tests for agent retrieval
8. Test agent instantiation in Python REPL

#### Testing
```python
async def test_get_dependency_analyzer():
    pool = DecommissionAgentPool()

    agent = await pool.get_agent(
        "dependency_analyzer",
        client_account_id="test-client",
        engagement_id="test-engagement"
    )

    assert agent.name == "Dependency Analyzer"
    assert agent.role == "System Dependency Mapping Specialist"
    assert "cmdb_query" in agent.tools
```

#### References
- Solution Document: Section 5.1 (Decommission Agent Pool)
- ADR-024: TenantMemoryManager (memory=False)
- Pattern: `backend/app/services/persistent_agents/discovery_agent_pool.py`

---

### Issue #10: Implement Phase-Specific Crew Execution Functions
**Labels**: `backend`, `agents`, `crewai`
**Story Points**: 13
**Assignee**: TBD
**Depends On**: #9

#### Description
Create crew execution functions for each of the 3 decommission phases, orchestrating multiple agents per phase with proper task definitions and context passing.

#### Acceptance Criteria
- [ ] `backend/app/services/crewai_flows/decommission/planning_crew.py` created
- [ ] `backend/app/services/crewai_flows/decommission/data_migration_crew.py` created
- [ ] `backend/app/services/crewai_flows/decommission/system_shutdown_crew.py` created
- [ ] Each crew function orchestrates appropriate agents
- [ ] Task definitions include descriptions and expected outputs
- [ ] Context passing between tasks works correctly
- [ ] Crew uses `memory=False` per ADR-024
- [ ] Results stored in flow runtime_state
- [ ] Integration tests for each crew

#### Technical Details

**File**: `backend/app/services/crewai_flows/decommission/planning_crew.py`

```python
"""
Decommission Planning Phase Crew
Orchestrates: Dependency Analyzer, Risk Assessor, Cost Analyst
"""

from crewai import Crew, Task
from app.services.crewai_flows.config.crew_factory import create_crew

async def execute_decommission_planning_crew(
    flow_id: str,
    client_account_id: str,
    engagement_id: str,
    selected_systems: List[Dict]
):
    """
    Decommission Planning Phase Crew (per FlowTypeConfig ADR-027):
    - Dependency Analyzer: Map system dependencies
    - Risk Assessor: Evaluate decommission risks
    - Cost Analyst: Calculate potential savings

    Phase name: "decommission_planning" per FlowTypeConfig
    """
    agent_pool = DecommissionAgentPool()

    # Get agents
    dependency_analyzer = await agent_pool.get_agent(
        "dependency_analyzer", client_account_id, engagement_id
    )
    risk_assessor = await agent_pool.get_agent(
        "risk_assessor", client_account_id, engagement_id
    )
    cost_analyst = await agent_pool.get_agent(
        "cost_optimization_analyst", client_account_id, engagement_id
    )

    # Define tasks
    dependency_task = Task(
        description=f"Analyze dependencies for {len(selected_systems)} systems",
        expected_output="Dependency map with impact analysis",
        agent=dependency_analyzer
    )

    risk_task = Task(
        description="Assess decommission risks and create mitigation plan",
        expected_output="Risk assessment with mitigation strategies",
        agent=risk_assessor,
        context=[dependency_task]  # Depends on dependency analysis
    )

    cost_task = Task(
        description="Calculate estimated cost savings from decommissioning",
        expected_output="Financial impact analysis with ROI projections",
        agent=cost_analyst
    )

    # Create crew
    planning_crew = create_crew(
        agents=[dependency_analyzer, risk_assessor, cost_analyst],
        tasks=[dependency_task, risk_task, cost_task],
        memory=False,  # Per ADR-024
        verbose=False
    )

    # Execute crew
    result = await planning_crew.kickoff_async()

    # Store results in flow runtime_state
    await update_flow_planning_results(flow_id, result)

    return result
```

**Similar implementation for `data_migration_crew.py` and `system_shutdown_crew.py`**

#### Implementation Steps
1. Create `decommission/` directory under `crewai_flows/`
2. Create planning_crew.py with dependency+risk+cost agents
3. Create data_migration_crew.py with retention+archive agents
4. Create system_shutdown_crew.py with execution+validation agents
5. Define tasks with descriptions and expected outputs
6. Use `create_crew()` with `memory=False`
7. Write integration tests for each crew
8. Test crew execution with mock data

#### Testing
```python
async def test_decommission_planning_crew():
    result = await execute_decommission_planning_crew(
        flow_id="test-flow",
        client_account_id="test-client",
        engagement_id="test-engagement",
        selected_systems=[{"id": "sys1", "name": "Test System"}]
    )

    assert "dependencies" in result
    assert "risks" in result
    assert "cost_savings" in result
```

#### References
- Solution Document: Section 5.2 (Phase-Specific Crews)
- ADR-024: memory=False for all crews
- Pattern: `backend/app/services/crewai_flows/assessment/strategy_crew.py`

---

## Phase 4: Frontend Implementation (Weeks 7-8)

### Issue #11: Create Decommission Flow API Service Layer
**Labels**: `frontend`, `api`, `typescript`
**Story Points**: 8
**Assignee**: TBD
**Depends On**: #6

#### Description
Create TypeScript API service layer for decommission flow with snake_case field naming per API conventions. Provides type-safe methods for all decommission flow operations.

#### Acceptance Criteria
- [ ] `src/lib/api/decommissionFlowApi.ts` created
- [ ] All interfaces use snake_case (decommission_planning, data_migration, system_shutdown)
- [ ] `initialize()` method for creating flows
- [ ] `getStatus()` method for flow status
- [ ] `getPhases()` method for FlowTypeConfig phases (ADR-027)
- [ ] `getEligibleSystems()` method
- [ ] `approvePlan()` method
- [ ] `startExecution()` method
- [ ] `exportReport()` method
- [ ] All methods include proper error handling
- [ ] TypeScript types exported

#### Technical Details

**File**: `src/lib/api/decommissionFlowApi.ts`

```typescript
/**
 * Decommission Flow API Service
 * Follows snake_case convention per API field naming standards
 */

import { apiCall } from './apiClient';

export interface DecommissionFlowCreateRequest {
  selected_system_ids: string[];
  flow_name?: string;
  decommission_strategy: {
    priority: 'cost_savings' | 'risk_reduction' | 'compliance';
    execution_mode: 'immediate' | 'scheduled' | 'phased';
    rollback_enabled: boolean;
  };
}

export interface DecommissionFlowResponse {
  flow_id: string;
  status: string;
  current_phase: string;
  next_phase: string;
  selected_systems: string[];
  message: string;
}

export interface PhaseProgress {
  decommission_planning: string;
  data_migration: string;
  system_shutdown: string;
}

export interface DecommissionFlowStatus {
  flow_id: string;
  master_flow_id: string;
  status: string;
  current_phase: string;
  system_count: number;
  phase_progress: PhaseProgress;
  metrics: {
    systems_decommissioned: number;
    estimated_savings: number;
    compliance_score: number;
  };
  runtime_state: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface PhaseDetail {
  name: string;
  display_name: string;
  description: string;
  timeout_seconds: number;
  can_pause: boolean;
}

export const decommissionFlowApi = {
  /**
   * Initialize new decommission flow
   */
  async initialize(
    request: DecommissionFlowCreateRequest
  ): Promise<DecommissionFlowResponse> {
    return apiCall('/api/v1/decommission-flow/initialize', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  /**
   * Get flow status (child flow operational state per ADR-012)
   */
  async getStatus(flow_id: string): Promise<DecommissionFlowStatus> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/status`);
  },

  /**
   * Get phase definitions from FlowTypeConfig (ADR-027)
   * Frontend MUST retrieve phases from API, not hardcode
   */
  async getPhases(): Promise<PhaseDetail[]> {
    return apiCall('/api/v1/flow-metadata/phases/decommission');
  },

  /**
   * Get eligible systems for decommission
   */
  async getEligibleSystems(engagement_id: string): Promise<any[]> {
    return apiCall(`/api/v1/decommission-flow/eligible-systems`, {
      method: 'GET',
      headers: { 'X-Engagement-ID': engagement_id },
    });
  },

  /**
   * Approve decommission plan
   */
  async approvePlan(flow_id: string, plan_id: string): Promise<void> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/planning/approve`, {
      method: 'POST',
      body: JSON.stringify({ plan_id }),
    });
  },

  /**
   * Start execution phase
   */
  async startExecution(flow_id: string): Promise<void> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/execution/start`, {
      method: 'POST',
    });
  },

  /**
   * Export decommission report
   */
  async exportReport(
    flow_id: string,
    format: 'pdf' | 'excel' | 'json'
  ): Promise<Blob> {
    return apiCall(`/api/v1/decommission-flow/${flow_id}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
      responseType: 'blob',
    });
  },
};
```

**Full implementation in Solution Document Section 6.1**

#### Implementation Steps
1. Create `decommissionFlowApi.ts` file
2. Define all TypeScript interfaces with snake_case
3. Implement all API methods using `apiCall()`
4. Add JSDoc comments for each method
5. Export all interfaces and API object
6. Write unit tests with mock fetch
7. Test with actual backend API

#### Testing
```typescript
describe('decommissionFlowApi', () => {
  it('should initialize decommission flow', async () => {
    const response = await decommissionFlowApi.initialize({
      selected_system_ids: ['sys1', 'sys2'],
      decommission_strategy: {
        priority: 'cost_savings',
        execution_mode: 'phased',
        rollback_enabled: true
      }
    });

    expect(response.flow_id).toBeDefined();
    expect(response.status).toBe('initialized');
    expect(response.current_phase).toBe('decommission_planning');
  });
});
```

#### References
- Solution Document: Section 6.1 (Frontend API Service Layer)
- API Naming: `/docs/guidelines/API_REQUEST_PATTERNS.md`
- Pattern: `src/lib/api/assessmentFlowApi.ts`

---

### Issue #12: Create React Query Hooks for Decommission Flow
**Labels**: `frontend`, `react-query`, `hooks`
**Story Points**: 8
**Assignee**: TBD
**Depends On**: #11

#### Description
Create React Query hooks for decommission flow state management with polling, mutations, and cache invalidation following established patterns.

#### Acceptance Criteria
- [ ] `src/hooks/decommission/useDecommissionFlow.ts` created
- [ ] `useDecommissionFlowStatus()` hook with polling (5s running, 15s idle)
- [ ] `useInitializeDecommissionFlow()` mutation hook
- [ ] `useEligibleSystems()` query hook
- [ ] `useApprovePlan()` mutation hook
- [ ] `useStartExecution()` mutation hook
- [ ] `useExportReport()` mutation hook
- [ ] Proper cache invalidation on mutations
- [ ] TypeScript types for all hooks
- [ ] Loading and error states handled

#### Technical Details

**File**: `src/hooks/decommission/useDecommissionFlow.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { decommissionFlowApi } from '@/lib/api/decommissionFlowApi';

/**
 * Hook for decommission flow status with polling
 * Per ADR-012: Uses child flow status for UI decisions
 */
export function useDecommissionFlowStatus(flow_id: string | null) {
  return useQuery({
    queryKey: ['decommission-flow-status', flow_id],
    queryFn: () => decommissionFlowApi.getStatus(flow_id!),
    enabled: !!flow_id,
    refetchInterval: (data) => {
      // Poll every 5s if running, 15s if completed/failed
      const status = data?.status;
      if (status === 'decommission_planning' ||
          status === 'data_migration' ||
          status === 'system_shutdown') {
        return 5000;
      }
      if (status === 'completed' || status === 'failed') {
        return false; // Stop polling
      }
      return 15000;
    },
  });
}

/**
 * Initialize decommission flow mutation
 */
export function useInitializeDecommissionFlow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: decommissionFlowApi.initialize,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['decommission-flows'] });
      queryClient.setQueryData(['decommission-flow-status', data.flow_id], data);
    },
  });
}

/**
 * Get eligible systems for decommission
 */
export function useEligibleSystems(engagement_id: string) {
  return useQuery({
    queryKey: ['eligible-systems', engagement_id],
    queryFn: () => decommissionFlowApi.getEligibleSystems(engagement_id),
    enabled: !!engagement_id,
  });
}

/**
 * Approve decommission plan mutation
 */
export function useApprovePlan(flow_id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (plan_id: string) =>
      decommissionFlowApi.approvePlan(flow_id, plan_id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['decommission-flow-status', flow_id]
      });
    },
  });
}

/**
 * Start execution phase mutation
 */
export function useStartExecution(flow_id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => decommissionFlowApi.startExecution(flow_id),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['decommission-flow-status', flow_id]
      });
    },
  });
}

/**
 * Export report mutation
 */
export function useExportReport(flow_id: string) {
  return useMutation({
    mutationFn: (format: 'pdf' | 'excel' | 'json') =>
      decommissionFlowApi.exportReport(flow_id, format),
    onSuccess: (blob, format) => {
      // Trigger download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `decommission-report-${flow_id}.${format}`;
      a.click();
      window.URL.revokeObjectURL(url);
    },
  });
}
```

**Full implementation in Solution Document Section 6.2**

#### Implementation Steps
1. Create hooks file in `src/hooks/decommission/`
2. Implement query hooks with proper keys
3. Implement mutation hooks with cache invalidation
4. Add polling logic to status hook
5. Add TypeScript return types
6. Write tests with React Testing Library
7. Test hooks in Storybook or dev environment

#### Testing
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClientProvider } from '@tanstack/react-query';

describe('useDecommissionFlowStatus', () => {
  it('should fetch flow status and poll', async () => {
    const { result } = renderHook(
      () => useDecommissionFlowStatus('test-flow-id'),
      { wrapper: QueryClientProvider }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.flow_id).toBe('test-flow-id');
  });
});
```

#### References
- Solution Document: Section 6.2 (React Query Hooks)
- Pattern: `src/hooks/assessment/useAssessmentFlow.ts`
- React Query Docs: https://tanstack.com/query/latest

---

### Issue #13: Implement Decommission Overview Page
**Labels**: `frontend`, `react`, `ui`
**Story Points**: 13
**Assignee**: TBD
**Depends On**: #12

#### Description
Create production Decommission Overview page (replaces mock) with live data from API, flow initialization, metrics dashboard, and phase pipeline visualization.

#### Acceptance Criteria
- [ ] `src/pages/decommission/Index.tsx` updated with live data
- [ ] Flow initialization modal with system selection
- [ ] Real-time metrics from API (systems queued, savings, compliance)
- [ ] Phase pipeline with progress tracking
- [ ] Upcoming decommissions list from database
- [ ] "AI Analysis" button triggers agent analysis
- [ ] "Schedule Decommission" button opens initialization modal
- [ ] All data fetched via React Query hooks
- [ ] Loading states for all data fetches
- [ ] Error handling with user-friendly messages

#### Technical Details

**File**: `src/pages/decommission/Index.tsx`

```typescript
import { useState } from 'react';
import {
  useDecommissionFlows,
  useInitializeDecommissionFlow,
  useEligibleSystems
} from '@/hooks/decommission/useDecommissionFlow';
import Sidebar from '@/components/Sidebar';

export default function DecommissionOverview() {
  const [showInitModal, setShowInitModal] = useState(false);
  const { data: flows, isLoading } = useDecommissionFlows();
  const { data: eligibleSystems } = useEligibleSystems(engagementId);
  const initializeMutation = useInitializeDecommissionFlow();

  // Calculate metrics from real data
  const metrics = {
    systemsQueued: flows?.filter(f => f.status !== 'completed').length || 0,
    annualSavings: flows?.reduce((sum, f) => sum + f.estimated_savings, 0) || 0,
    dataArchived: calculateDataArchived(flows),
    complianceScore: calculateComplianceScore(flows)
  };

  const handleInitialize = async (selectedSystems: string[]) => {
    await initializeMutation.mutateAsync({
      selected_system_ids: selectedSystems,
      decommission_strategy: {
        priority: 'cost_savings',
        execution_mode: 'phased',
        rollback_enabled: true
      }
    });
    setShowInitModal(false);
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar />
      <div className="flex-1 ml-64">
        <main className="p-8">
          <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="mb-8">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    Decommission Overview
                  </h1>
                  <p className="text-lg text-gray-600">
                    Safely retire legacy systems with automated compliance
                  </p>
                </div>
                <div className="flex space-x-3">
                  <button
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg"
                    onClick={() => triggerAIAnalysis()}
                  >
                    AI Analysis
                  </button>
                  <button
                    className="bg-red-600 text-white px-4 py-2 rounded-lg"
                    onClick={() => setShowInitModal(true)}
                  >
                    Schedule Decommission
                  </button>
                </div>
              </div>
            </div>

            {/* Metrics Grid */}
            <MetricsGrid metrics={metrics} />

            {/* Phase Pipeline */}
            <PhasePipeline flows={flows} />

            {/* Upcoming Decommissions */}
            <UpcomingDecommissions flows={flows} />
          </div>
        </main>
      </div>

      {/* Initialization Modal */}
      {showInitModal && (
        <DecommissionInitModal
          eligibleSystems={eligibleSystems}
          onSubmit={handleInitialize}
          onCancel={() => setShowInitModal(false)}
        />
      )}
    </div>
  );
}
```

**Components to create**:
- `MetricsGrid` - Display 4 key metrics
- `PhasePipeline` - Show 3 phases with progress
- `UpcomingDecommissions` - List of scheduled decommissions
- `DecommissionInitModal` - System selection and configuration

#### Implementation Steps
1. Update Index.tsx to use real data hooks
2. Replace mock data with API calls
3. Create initialization modal component
4. Implement metrics calculation from flows
5. Create phase pipeline visualization
6. Add loading/error states
7. Test with real backend data
8. Add E2E test with Playwright

#### Testing
```typescript
// E2E test
test('should display decommission overview with real data', async ({ page }) => {
  await page.goto('/decommission/overview');

  // Wait for data to load
  await page.waitForSelector('[data-testid="metrics-grid"]');

  // Verify metrics displayed
  await expect(page.locator('text=Systems Queued')).toBeVisible();
  await expect(page.locator('text=Annual Savings')).toBeVisible();

  // Click Schedule Decommission
  await page.click('button:has-text("Schedule Decommission")');
  await expect(page.locator('[data-testid="init-modal"]')).toBeVisible();
});
```

#### References
- Solution Document: Mock wireframe at `src/pages/decom/Index.tsx`
- Pattern: `src/pages/assessment/Index.tsx`

---

### Issue #14-17: Implement Phase-Specific Pages
**(Issues #14: Planning, #15: Data Migration, #16: System Shutdown, #17: Export)**

**Similar structure to Issue #13 for each page**

Each issue includes:
- Update page to use live data hooks
- Display phase-specific information from API
- Agent insights and recommendations
- Action buttons (approve, start, export)
- Real-time progress tracking
- E2E tests with Playwright

**Story Points: 8 each (Total: 32)**

---

## Phase 5: Integration & Testing (Weeks 9-10)

### Issue #18: Assessment Flow Integration (6R Retire Strategy)
**Labels**: `backend`, `integration`, `assessment`
**Story Points**: 8
**Assignee**: TBD
**Depends On**: #6

#### Description
Integrate decommission flow with Assessment Flow to auto-recommend decommission for assets with 6R strategy = "Retire".

#### Acceptance Criteria
- [ ] Assessment completion handler triggers decommission recommendation
- [ ] Query assets by `six_r_strategy = "Retire"`
- [ ] Create decommission recommendation in database
- [ ] Notification to user about retirement candidates
- [ ] Link from Assessment results to Decommission flow
- [ ] Integration test covering end-to-end flow
- [ ] Documentation updated

#### Technical Details

**File**: `backend/app/services/integrations/assessment_decommission_integration.py`

```python
"""
Assessment → Decommission Flow Integration
Trigger: Assets with 6R strategy = "Retire"
"""

async def on_assessment_complete(assessment_flow_id: str, db: AsyncSession):
    """Auto-create decommission recommendations for Retire assets."""

    # Get assessment flow
    assessment = await get_assessment_flow(assessment_flow_id, db)

    # Get assets marked for retirement
    retire_assets = await db.execute(
        select(Asset).where(
            Asset.assessment_flow_id == assessment_flow_id,
            Asset.six_r_strategy == "Retire",
            Asset.client_account_id == assessment.client_account_id,
            Asset.engagement_id == assessment.engagement_id
        )
    )
    retire_assets = retire_assets.scalars().all()

    if retire_assets:
        # Calculate estimated savings
        estimated_savings = sum(
            asset.annual_infrastructure_cost or 0
            for asset in retire_assets
        )

        # Create decommission recommendation
        recommendation = DecommissionRecommendation(
            engagement_id=assessment.engagement_id,
            client_account_id=assessment.client_account_id,
            system_ids=[asset.id for asset in retire_assets],
            reason="6R Assessment Recommendation - Retire Strategy",
            estimated_annual_savings=estimated_savings,
            priority="high" if estimated_savings > 100000 else "medium",
            created_by="assessment_flow_automation"
        )
        db.add(recommendation)
        await db.commit()

        # Notify user
        await notify_decommission_recommendation(
            assessment.engagement_id,
            len(retire_assets),
            estimated_savings
        )
```

**Hook into Assessment Flow**:
```python
# In assessment_flow finalization
async def finalize_assessment_flow(flow_id: str):
    # ... existing finalization logic ...

    # Trigger decommission integration
    await on_assessment_complete(flow_id, db)
```

#### Implementation Steps
1. Create integration module
2. Implement `on_assessment_complete()` handler
3. Create `DecommissionRecommendation` model
4. Hook into assessment finalization
5. Add notification logic
6. Write integration test
7. Test with real assessment flow completion

#### Testing
```python
async def test_assessment_retire_triggers_decommission():
    # Create assessment with Retire assets
    assessment = await create_test_assessment(
        assets=[
            {"name": "Old System", "six_r_strategy": "Retire"},
            {"name": "Legacy App", "six_r_strategy": "Retire"}
        ]
    )

    # Complete assessment
    await finalize_assessment_flow(assessment.flow_id)

    # Verify decommission recommendation created
    recommendations = await get_decommission_recommendations(
        assessment.engagement_id
    )

    assert len(recommendations) == 1
    assert len(recommendations[0].system_ids) == 2
    assert recommendations[0].reason == "6R Assessment Recommendation - Retire Strategy"
```

#### References
- Solution Document: Section 8.1 (Assessment Flow Integration)
- Pattern: Discovery → Assessment integration

---

### Issue #19: Wave Execution Integration (Post-Migration Decommission)
**Labels**: `backend`, `integration`, `wave-execution`
**Story Points**: 8
**Assignee**: TBD
**Depends On**: #6

#### Description
Integrate decommission flow with Wave Execution to mark source systems eligible for decommission after successful cloud migration (with grace period).

#### Acceptance Criteria
- [ ] Wave completion handler marks source systems decommission-eligible
- [ ] Configurable grace period (default: 90 days)
- [ ] Update Asset table with `decommission_eligible` flag
- [ ] Update Asset table with `grace_period_end` timestamp
- [ ] Notification when systems become eligible
- [ ] Query endpoint for eligible systems
- [ ] Integration test covering migration → decommission flow
- [ ] Documentation updated

#### Technical Details

**File**: `backend/app/services/integrations/wave_decommission_integration.py`

```python
"""
Wave Execution → Decommission Flow Integration
Trigger: Successful cloud migration completion
"""

from datetime import datetime, timedelta

async def on_wave_migration_complete(
    wave_id: str,
    db: AsyncSession,
    grace_period_days: int = 90
):
    """Mark source systems eligible for decommission post-migration."""

    # Get wave and migrated assets
    wave = await get_wave(wave_id, db)
    migrated_assets = await db.execute(
        select(Asset).where(
            Asset.wave_id == wave_id,
            Asset.migration_status == "completed",
            Asset.client_account_id == wave.client_account_id,
            Asset.engagement_id == wave.engagement_id
        )
    )
    migrated_assets = migrated_assets.scalars().all()

    grace_period_end = datetime.utcnow() + timedelta(days=grace_period_days)

    for asset in migrated_assets:
        # Mark source system eligible for decommission
        source_system = await get_source_system(asset.source_system_id, db)
        if source_system:
            source_system.decommission_eligible = True
            source_system.grace_period_end = grace_period_end
            source_system.migration_completed_at = datetime.utcnow()

            logger.info(
                f"Marked system {source_system.id} eligible for decommission "
                f"after {grace_period_days}-day grace period"
            )

    await db.commit()

    # Notify about eligible systems
    await notify_decommission_eligible(
        wave.engagement_id,
        len(migrated_assets),
        grace_period_end
    )
```

**Hook into Wave Execution**:
```python
# In wave execution completion
async def complete_wave_execution(wave_id: str):
    # ... existing completion logic ...

    # Trigger decommission eligibility
    await on_wave_migration_complete(wave_id, db)
```

**Query for Eligible Systems**:
```python
@router.get("/eligible-systems")
async def get_eligible_systems(
    engagement_id: str = Header(..., alias="X-Engagement-ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get systems eligible for decommission."""

    eligible = await db.execute(
        select(Asset).where(
            Asset.engagement_id == UUID(engagement_id),
            or_(
                # Pre-migration retirement
                Asset.six_r_strategy == "Retire",
                # Post-migration decommission (grace period expired)
                and_(
                    Asset.decommission_eligible == True,
                    Asset.grace_period_end < datetime.utcnow()
                )
            )
        )
    )

    return eligible.scalars().all()
```

#### Implementation Steps
1. Create wave integration module
2. Implement `on_wave_migration_complete()` handler
3. Add `decommission_eligible` and `grace_period_end` to Asset model
4. Create Alembic migration for new columns
5. Hook into wave completion
6. Implement eligible systems query endpoint
7. Write integration test
8. Test with real wave execution

#### Testing
```python
async def test_wave_completion_marks_systems_eligible():
    # Create wave with assets
    wave = await create_test_wave(
        assets=[
            {"name": "On-Prem App", "migration_status": "completed"},
            {"name": "Virtual Server", "migration_status": "completed"}
        ]
    )

    # Complete wave
    await complete_wave_execution(wave.wave_id)

    # Verify systems marked eligible
    source_systems = await get_source_systems_for_wave(wave.wave_id)

    for system in source_systems:
        assert system.decommission_eligible == True
        assert system.grace_period_end is not None
        assert system.grace_period_end > datetime.utcnow()
```

#### References
- Solution Document: Section 8.2 (Wave Execution Integration)
- Grace Period Configuration: Environment variable `DECOMMISSION_GRACE_PERIOD_DAYS`

---

### Issue #20: E2E Testing with Playwright (Full Flow)
**Labels**: `testing`, `e2e`, `playwright`
**Story Points**: 13
**Assignee**: TBD
**Depends On**: #13-17

#### Description
Create comprehensive E2E tests for decommission flow using Playwright qa-playwright-tester agent, covering all 3 phases from initialization to completion.

#### Acceptance Criteria
- [ ] Test: Initialize decommission flow with system selection
- [ ] Test: Decommission planning phase execution
- [ ] Test: Data migration phase with archive jobs
- [ ] Test: System shutdown phase with validation
- [ ] Test: Export reports (PDF, Excel, JSON)
- [ ] Test: Pause and resume flow
- [ ] Test: Error handling and rollback
- [ ] All tests pass consistently
- [ ] Tests run in CI/CD pipeline
- [ ] Test coverage report generated

#### Technical Details

**File**: `tests/e2e/decommission/full-flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Decommission Flow - Full Journey', () => {
  test('should complete full decommission flow', async ({ page }) => {
    // 1. Navigate to decommission overview
    await page.goto('/decommission/overview');
    await expect(page.locator('h1:has-text("Decommission Overview")')).toBeVisible();

    // 2. Click Schedule Decommission
    await page.click('button:has-text("Schedule Decommission")');
    await expect(page.locator('[data-testid="init-modal"]')).toBeVisible();

    // 3. Select systems for decommission
    await page.check('[data-testid="system-checkbox-1"]');
    await page.check('[data-testid="system-checkbox-2"]');
    await page.fill('[data-testid="flow-name"]', 'E2E Test Decommission');

    // 4. Configure strategy
    await page.selectOption('[data-testid="priority"]', 'cost_savings');
    await page.selectOption('[data-testid="execution-mode"]', 'phased');
    await page.check('[data-testid="rollback-enabled"]');

    // 5. Initialize flow
    await page.click('button:has-text("Initialize")');
    await page.waitForSelector('[data-testid="flow-created-message"]');

    // 6. Navigate to Planning phase
    await page.click('a:has-text("Planning")');
    await expect(page.locator('h1:has-text("Decommission Planning")')).toBeVisible();

    // 7. Wait for AI analysis to complete
    await page.waitForSelector('[data-testid="dependency-analysis-complete"]', {
      timeout: 60000
    });
    await page.waitForSelector('[data-testid="risk-assessment-complete"]');
    await page.waitForSelector('[data-testid="cost-analysis-complete"]');

    // 8. Review and approve plan
    await page.click('[data-testid="review-plan-button"]');
    await expect(page.locator('[data-testid="plan-details"]')).toBeVisible();
    await page.click('button:has-text("Approve Plan")');

    // 9. Navigate to Data Migration phase
    await page.click('a:has-text("Data Migration")');
    await expect(page.locator('h1:has-text("Data Migration")')).toBeVisible();

    // 10. Wait for archive jobs to complete
    await page.waitForSelector('[data-testid="archive-job-completed"]', {
      timeout: 120000
    });

    // 11. Navigate to System Shutdown phase
    await page.click('a:has-text("System Shutdown")');
    await expect(page.locator('h1:has-text("System Shutdown")')).toBeVisible();

    // 12. Review safety checks
    await expect(page.locator('[data-testid="safety-check-backup"]')).toContainText('Passed');
    await expect(page.locator('[data-testid="safety-check-dependencies"]')).toContainText('Passed');

    // 13. Start execution
    await page.click('button:has-text("Start Execution")');
    await page.waitForSelector('[data-testid="execution-started"]');

    // 14. Wait for execution to complete
    await page.waitForSelector('[data-testid="execution-completed"]', {
      timeout: 180000
    });

    // 15. Verify validation checks passed
    await expect(page.locator('[data-testid="validation-status"]')).toContainText('All checks passed');

    // 16. Export report
    await page.click('button:has-text("Export Report")');
    await page.selectOption('[data-testid="export-format"]', 'pdf');

    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Download")');
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toContain('decommission-report');
    expect(download.suggestedFilename()).toContain('.pdf');

    // 17. Verify flow completed
    await page.goto('/decommission/overview');
    await expect(page.locator('[data-testid="flow-status"]')).toContainText('Completed');
  });

  test('should handle pause and resume', async ({ page }) => {
    // ... test pause/resume functionality
  });

  test('should handle rollback on failure', async ({ page }) => {
    // ... test error handling and rollback
  });
});
```

**Additional Test Files**:
- `tests/e2e/decommission/planning.spec.ts`
- `tests/e2e/decommission/data-migration.spec.ts`
- `tests/e2e/decommission/system-shutdown.spec.ts`
- `tests/e2e/decommission/error-handling.spec.ts`

#### Implementation Steps
1. Create E2E test directory structure
2. Write full flow test covering all phases
3. Write phase-specific tests
4. Add error handling tests
5. Configure Playwright in CI/CD
6. Run tests with Playwright agent: `/qa-test-flow decommission`
7. Generate coverage report
8. Document test scenarios

#### Testing
```bash
# Run all decommission E2E tests
npm run test:e2e:decommission

# Run with Playwright agent
/qa-test-flow decommission --test-objectives "Full decommission flow from initialization to completion"

# Run specific test
npx playwright test tests/e2e/decommission/full-flow.spec.ts

# Debug mode
npx playwright test --debug tests/e2e/decommission/full-flow.spec.ts
```

#### References
- Solution Document: Section 10 (Testing & Validation)
- Playwright Docs: https://playwright.dev/
- Pattern: `tests/e2e/assessment/`

---

## Phase 6: Documentation & Launch (Weeks 11-12)

### Issue #21: API Documentation and OpenAPI Spec
**Labels**: `documentation`, `api`, `backend`
**Story Points**: 5
**Assignee**: TBD
**Depends On**: #6-7

#### Description
Generate comprehensive API documentation for decommission flow endpoints using FastAPI's automatic OpenAPI generation. Add examples, schemas, and integration guide.

#### Acceptance Criteria
- [ ] OpenAPI spec generated at `/docs`
- [ ] All endpoints documented with descriptions
- [ ] Request/response examples for each endpoint
- [ ] Authentication requirements documented
- [ ] Rate limits and error codes documented
- [ ] Integration guide with code examples
- [ ] Postman collection exported
- [ ] Documentation published to wiki/docs site

#### Technical Details

**Files**:
- Auto-generated: `/docs` endpoint (FastAPI)
- Manual: `docs/api/DECOMMISSION_ENDPOINTS.md`
- Postman: `postman/decommission-flow.json`

**API Documentation Structure**:
```markdown
# Decommission Flow API Endpoints

## Authentication
All endpoints require Bearer token authentication.

## Base URL
`https://api.example.com/api/v1/decommission-flow`

## Endpoints

### POST /initialize
Initialize new decommission flow.

**Request:**
```json
{
  "selected_system_ids": ["uuid1", "uuid2"],
  "flow_name": "Q1 2025 Decommission",
  "decommission_strategy": {
    "priority": "cost_savings",
    "execution_mode": "phased",
    "rollback_enabled": true
  }
}
```

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "initialized",
  "current_phase": "decommission_planning",
  "next_phase": "data_migration",
  "selected_systems": ["uuid1", "uuid2"],
  "message": "Decommission flow initialized for 2 systems"
}
```

**Errors:**
- 400: Invalid request (missing required fields)
- 401: Unauthorized (invalid token)
- 403: Forbidden (insufficient permissions)
- 409: Conflict (systems already in active decommission)
- 500: Internal server error

### GET /{flow_id}/status
Get current status of decommission flow.

**Response:**
```json
{
  "flow_id": "550e8400-e29b-41d4-a716-446655440000",
  "master_flow_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "decommission_planning",
  "current_phase": "decommission_planning",
  "system_count": 2,
  "phase_progress": {
    "decommission_planning": "in_progress",
    "data_migration": "pending",
    "system_shutdown": "pending"
  },
  "metrics": {
    "systems_decommissioned": 0,
    "estimated_savings": 120000.00,
    "compliance_score": 98.5
  },
  "runtime_state": {},
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z"
}
```

... (continue for all endpoints)
```

**Integration Guide**:
```markdown
# Decommission Flow Integration Guide

## Quick Start

1. **Get Eligible Systems**
```bash
curl -X GET "https://api.example.com/api/v1/decommission-flow/eligible-systems" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID"
```

2. **Initialize Flow**
```bash
curl -X POST "https://api.example.com/api/v1/decommission-flow/initialize" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "selected_system_ids": ["uuid1", "uuid2"],
    "decommission_strategy": {"priority": "cost_savings"}
  }'
```

3. **Poll Status**
```bash
curl -X GET "https://api.example.com/api/v1/decommission-flow/$FLOW_ID/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Engagement-ID: $ENGAGEMENT_ID"
```

## Phase-Specific Operations
... (continue with examples)
```

#### Implementation Steps
1. Add detailed docstrings to all endpoints
2. Add OpenAPI examples to Pydantic schemas
3. Test `/docs` endpoint renders correctly
4. Write integration guide with examples
5. Create Postman collection
6. Export OpenAPI spec to `openapi.json`
7. Publish docs to wiki

#### Testing
- Verify `/docs` endpoint shows all decommission endpoints
- Test all curl examples from documentation
- Import Postman collection and run requests
- Verify OpenAPI spec validates

#### References
- FastAPI Docs: https://fastapi.tiangolo.com/tutorial/metadata/
- Solution Document: Section 5 (Backend API Architecture)

---

### Issue #22: User Guide and Runbook
**Labels**: `documentation`, `user-guide`
**Story Points**: 5
**Assignee**: TBD
**Depends On**: All implementation issues

#### Description
Create comprehensive user guide for decommission workflows and operational runbook for administrators. Includes step-by-step instructions, screenshots, troubleshooting, and best practices.

#### Acceptance Criteria
- [ ] User guide covering all decommission flow features
- [ ] Step-by-step walkthrough with screenshots
- [ ] Admin runbook for operations team
- [ ] Troubleshooting section with common issues
- [ ] Best practices for safe decommissioning
- [ ] Compliance checklist
- [ ] FAQ section
- [ ] Documentation published to wiki

#### Technical Details

**Files**:
- `docs/user-guide/DECOMMISSION_FLOW.md`
- `docs/runbooks/DECOMMISSION_OPERATIONS.md`

**User Guide Structure**:
```markdown
# Decommission Flow User Guide

## Overview
The Decommission Flow enables safe retirement of legacy systems with AI-powered planning, automated data retention, and comprehensive validation.

## Prerequisites
- Systems must be in one of these states:
  - Pre-migration: 6R strategy = "Retire"
  - Post-migration: Grace period expired (90 days)
- User must have `decommission.execute` permission

## Step 1: Identify Systems for Decommission

1. Navigate to **Decommission → Overview**
2. Click **AI Analysis** to get recommendations
3. Review eligible systems list
4. Verify estimated savings and compliance score

[Screenshot: Decommission Overview with Metrics]

## Step 2: Initialize Decommission Flow

1. Click **Schedule Decommission**
2. Select systems from eligible list
3. Configure decommission strategy:
   - **Priority**: cost_savings, risk_reduction, or compliance
   - **Execution Mode**: immediate, scheduled, or phased
   - **Rollback**: Enable for safe execution
4. Click **Initialize**

[Screenshot: Initialization Modal]

## Step 3: Planning Phase

AI agents analyze:
- **Dependency Analyzer**: Maps all system dependencies
- **Risk Assessor**: Evaluates decommission risks
- **Cost Analyst**: Calculates ROI and savings

### Review Planning Results
1. Navigate to **Planning** tab
2. Review dependency map
3. Review risk assessment
4. Review cost analysis
5. Click **Approve Plan** to proceed

[Screenshot: Planning Phase with Dependency Map]

## Step 4: Data Migration Phase

### Data Retention
- AI automatically assigns retention policies based on compliance
- Archive jobs execute with integrity verification
- Encryption applied per policy requirements

### Monitor Progress
1. Navigate to **Data Migration** tab
2. Monitor archive job progress
3. Verify integrity checks pass
4. Wait for phase completion

[Screenshot: Data Migration with Archive Jobs]

## Step 5: System Shutdown Phase

### Pre-Execution Safety Checks
- Data backup verified
- Dependencies resolved
- Rollback plan ready
- Business approval confirmed

### Execute Decommission
1. Navigate to **System Shutdown** tab
2. Review safety check status
3. Click **Start Execution**
4. Monitor execution progress
5. Verify validation checks pass

[Screenshot: System Shutdown with Safety Checks]

## Step 6: Export Reports

1. Click **Export Report**
2. Select format: PDF, Excel, or JSON
3. Download report for compliance audit

[Screenshot: Export Report Dialog]

## Troubleshooting

### Issue: Safety Check Failed
**Symptom**: Cannot start execution, safety check shows "Failed"
**Solution**:
1. Click safety check to see details
2. Resolve dependency or backup issue
3. Re-run validation
4. Retry execution

### Issue: Archive Job Stuck
**Symptom**: Archive job progress at 0% for >30 minutes
**Solution**:
1. Check network connectivity to archive storage
2. Verify storage capacity available
3. Check archive job logs for errors
4. Contact support if issue persists

... (continue with more troubleshooting)

## Best Practices

1. **Always Review Dependencies**: Never skip dependency analysis
2. **Test Rollback**: Verify rollback plan before execution
3. **Schedule During Maintenance Windows**: Plan for low-traffic periods
4. **Communicate with Stakeholders**: Notify all affected teams
5. **Keep Audit Trail**: Export reports for compliance

## Compliance Checklist

- [ ] Data retention policies assigned
- [ ] All data archived with encryption
- [ ] Integrity verification passed
- [ ] Access revocation confirmed
- [ ] Audit trail exported
- [ ] Stakeholder approval documented
- [ ] Compliance report generated
```

**Runbook Structure**:
```markdown
# Decommission Operations Runbook

## Monitoring

### Health Checks
```bash
# Check decommission flows status
curl -X GET "$API_BASE/decommission-flow/health" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Metrics to Monitor
- Active flows count (should be < 50)
- Average flow duration (target: < 7 days)
- Failure rate (target: < 5%)
- Compliance score (target: > 95%)

## Common Operations

### Pause All Active Flows (Emergency)
```bash
for flow_id in $(get_active_flows); do
  curl -X POST "$API_BASE/decommission-flow/$flow_id/pause" \
    -H "Authorization: Bearer $ADMIN_TOKEN"
done
```

### Rollback Failed Execution
```bash
curl -X POST "$API_BASE/decommission-flow/$FLOW_ID/rollback" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason": "Safety check failed"}'
```

### Cleanup Stuck Archive Jobs
```sql
-- Identify stuck jobs (>24 hours in progress)
SELECT * FROM migration.archive_jobs
WHERE status = 'in_progress'
  AND actual_start < NOW() - INTERVAL '24 hours';

-- Cancel stuck jobs
UPDATE migration.archive_jobs
SET status = 'failed',
    error_message = 'Timed out after 24 hours'
WHERE job_id = 'JOB_ID';
```

## Incident Response

### P1: Mass Failure (>10% flows failing)
1. Pause all new decommissions
2. Check database connectivity
3. Check agent pool health
4. Review error logs
5. Escalate to engineering if unresolved in 1 hour

### P2: Single Flow Failure
1. Review flow logs
2. Check phase-specific errors
3. Attempt rollback if safe
4. Re-initialize if rollback fails

... (continue with more operations)
```

#### Implementation Steps
1. Write user guide with screenshots
2. Write admin runbook with commands
3. Add troubleshooting scenarios
4. Create best practices checklist
5. Generate PDF versions
6. Publish to wiki/docs site
7. Train support team on runbook

#### Testing
- Walk through user guide steps manually
- Verify all commands in runbook work
- Test troubleshooting scenarios
- Get feedback from beta users

#### References
- Solution Document: All sections
- Pattern: `docs/user-guide/ASSESSMENT_FLOW.md`

---

## Summary

**Total Issues**: 22
**Total Story Points**: 185
**Estimated Duration**: 12 weeks
**Target Release**: v2.5.0

**Phase Breakdown**:
- Phase 0 (Prep): 1 issue, 3 SP, Week 1
- Phase 1 (Database): 3 issues, 29 SP, Weeks 1-2
- Phase 2 (Backend API): 3 issues, 31 SP, Weeks 3-4
- Phase 3 (Agents): 3 issues, 39 SP, Weeks 5-6
- Phase 4 (Frontend): 7 issues, 61 SP, Weeks 7-8
- Phase 5 (Integration): 3 issues, 29 SP, Weeks 9-10
- Phase 6 (Documentation): 2 issues, 10 SP, Weeks 11-12

**Dependencies**:
- All issues depend on Issue #1 (mock preservation)
- Frontend issues depend on backend API issues
- Integration issues depend on core implementation
- Documentation issues depend on all implementation

**Success Metrics**:
- Zero pre-commit violations
- 100% E2E test pass rate
- API response time < 2s
- Flow completion rate > 95%
- User satisfaction score > 4.5/5

---

**END OF MILESTONE DEFINITION**
