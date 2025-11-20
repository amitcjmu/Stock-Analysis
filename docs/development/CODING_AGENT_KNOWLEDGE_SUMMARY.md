# Coding Agent Knowledge Summary

> **Comprehensive distillation of 300+ Serena memories into actionable patterns for Claude Code agents**
>
> **Last Updated**: January 2025
>
> **Purpose**: Reference guide for recurring patterns, bug fixes, and architectural decisions. Read this BEFORE implementing features or fixing bugs.

---

## Table of Contents

- [Quick Reference: Top 10 Critical Patterns](#quick-reference-top-10-critical-patterns)
- [1. Critical Architecture Patterns](#1-critical-architecture-patterns)
- [2. Common Bug Patterns and Fixes](#2-common-bug-patterns-and-fixes)
- [3. Testing Patterns](#3-testing-patterns)
- [4. Security Patterns](#4-security-patterns)
- [5. Database Patterns](#5-database-patterns)
- [6. Agent Orchestration Patterns](#6-agent-orchestration-patterns)
- [7. Observability Patterns](#7-observability-patterns)
- [8. Development Workflow Patterns](#8-development-workflow-patterns)

---

## Quick Reference: Top 10 Critical Patterns

These are the MOST RECURRING bugs and patterns across all Serena memories. **Read these before ANY code changes.**

### 1. MFO Two-Table Flow ID Pattern ⚠️ CRITICAL

**The Problem**: MFO uses TWO different UUIDs per flow - confusing them causes "Flow not found" errors.

**The Rule**:
- **URL paths use Child Flow IDs** (user-facing: `/execute/{flow_id}`)
- **MFO methods use Master Flow IDs** (internal: `orchestrator.execute_phase(master_id, ...)`)
- **ALWAYS resolve master_flow_id before calling MFO**

```python
# ✅ CORRECT Pattern
@router.post("/execute/{flow_id}")  # Child ID from URL
async def execute_something(flow_id: str, db: AsyncSession, context: RequestContext):
    # Step 1: Query child flow table
    stmt = select(AssessmentFlow).where(
        AssessmentFlow.id == UUID(flow_id),  # Child ID
        AssessmentFlow.client_account_id == context.client_account_id,
        AssessmentFlow.engagement_id == context.engagement_id,
    )
    child_flow = (await db.execute(stmt)).scalar_one_or_none()

    if not child_flow or not child_flow.master_flow_id:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Step 2: Extract master flow ID
    master_flow_id = child_flow.master_flow_id

    # Step 3: Call MFO with MASTER ID, pass CHILD ID in phase_input
    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(master_flow_id),  # ← MASTER flow ID (MFO routing)
        "phase_name",
        {"flow_id": flow_id}  # ← CHILD flow ID (persistence)
    )

    return {"success": True, "flow_id": flow_id}
```

**Reference**: `.serena/memories/mfo_two_table_flow_id_pattern_critical.md`

---

### 2. API Request Body vs Query Parameters

**The Problem**: #1 recurring 422 error - FastAPI + Pydantic ONLY accept request bodies for POST/PUT/DELETE.

```typescript
// ❌ WRONG - Causes 422 errors
await apiCall(`/api/endpoint?param=value`, { method: 'POST' })

// ✅ CORRECT
await apiCall(`/api/endpoint`, {
  method: 'POST',
  body: JSON.stringify({ param: 'value' })
})
```

**Reference**: `/docs/guidelines/API_REQUEST_PATTERNS.md`, `.serena/memories/api_request_patterns_422_errors.md`

---

### 3. CrewAI Memory is DISABLED (ADR-024)

**The Rule**: NEVER set `memory=True` in agents or crews. Use `TenantMemoryManager` instead.

```python
# ❌ WRONG - Causes 401/422 errors
agent = create_agent(role="Mapper", memory=True)  # DON'T!

# ✅ CORRECT - Memory disabled by default
agent = create_agent(role="Mapper")  # memory=False is default

# ✅ CORRECT - Use TenantMemoryManager for learning
from app.services.crewai_flows.memory.tenant_memory_manager import TenantMemoryManager

memory_manager = TenantMemoryManager(crewai_service, db)
await memory_manager.store_learning(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    pattern_data={"source": "cust_name", "target": "customer_name"}
)
```

**Why**: CrewAI memory tries to use OpenAI embeddings with DeepInfra keys → validation failures.

**Reference**: ADR-024, `.serena/memories/adr024_crewai_memory_disabled_2025_10_02.md`

---

### 4. Multi-Tenant Query Scoping (SECURITY)

**The Rule**: ALWAYS include tenant context in ALL database queries.

```python
# ❌ WRONG - Security vulnerability!
stmt = select(DataImport).where(DataImport.id == UUID(data_import_id))

# ✅ CORRECT - Tenant-scoped
from sqlalchemy import and_

stmt = select(DataImport).where(
    and_(
        DataImport.id == UUID(data_import_id),
        DataImport.client_account_id == client_account_id,
        DataImport.engagement_id == engagement_id,
    )
)
```

**Reference**: `.serena/memories/cross_tenant_security_patterns.md`

---

### 5. Transaction Management: Flush vs Commit

**The Problem**: Adding `async with db.begin():` around repository calls causes nested transaction errors.

```python
# ❌ WRONG - Nested transaction error
async with db.begin():
    updated_flow = await repo.update_planning_flow(...)

# ✅ CORRECT - Repository flushes, caller commits
updated_flow = await repo.update_planning_flow(...)
await db.commit()
```

**Why**: Repository methods do `flush()` but NOT `commit()` - caller manages transaction boundaries.

**Reference**: `.serena/memories/repository-transaction-management-pattern.md`

---

### 6. SQLAlchemy IntegrityError Rollback

**The Problem**: After IntegrityError, session becomes invalid → cascading failures.

```python
# ✅ CORRECT - Immediate rollback
from sqlalchemy.exc import IntegrityError

try:
    created_asset = await create_method(...)
    return created_asset
except IntegrityError as ie:
    await session.rollback()  # CRITICAL: Prevent session invalidation

    # Differentiate error types
    error_msg = str(ie.orig).lower()
    if "unique constraint" in error_msg or "duplicate key" in error_msg:
        logger.warning(f"Race condition: {ie}")
        raise  # Caller can retry
    else:
        logger.error(f"Unrecoverable integrity error: {ie}")
        raise  # Don't retry
```

**Reference**: `.serena/memories/sqlalchemy-integrity-error-rollback-pattern.md`

---

### 7. Alembic Idempotent Migrations

**The Rule**: Use 3-digit prefix + PostgreSQL DO blocks with IF EXISTS checks.

```python
"""add_columns_to_table

Revision ID: 092_add_columns_to_table
Revises: 091_previous_migration
Create Date: 2025-01-12
"""

def upgrade() -> None:
    """IDEMPOTENT: Uses IF NOT EXISTS checks"""
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='my_table'
                AND column_name='new_column'
            ) THEN
                ALTER TABLE migration.my_table
                ADD COLUMN new_column TEXT;
            END IF;
        END $$;
    """)

def downgrade() -> None:
    """IDEMPOTENT: Uses IF EXISTS checks"""
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='my_table'
                AND column_name='new_column'
            ) THEN
                ALTER TABLE migration.my_table
                DROP COLUMN new_column;
            END IF;
        END $$;
    """)
```

**Reference**: CLAUDE.md lines 522-531, `.serena/memories/alembic-idempotent-migrations-pattern.md`

---

### 8. Frontend-Backend Schema Mismatch (NaN, Disabled Buttons)

**The Problem**: Frontend expects fields backend doesn't provide → NaN values, disabled buttons.

```python
# ✅ Backend: Add fields with defaults
class DataCleansingRecommendation(BaseModel):
    id: str
    title: str
    confidence: Optional[float] = 0.85  # Prevents NaN
    status: str = 'pending'  # Enables buttons
    implementation_steps: Optional[List[str]] = []
```

```typescript
// ✅ Frontend: Defensive null checks
<span>
  {rec.confidence !== undefined && rec.confidence !== null
    ? `${Math.round(rec.confidence * 100)}%`
    : 'N/A'} confidence
</span>

<Button disabled={rec.status !== 'pending'}>Apply</Button>
```

**Reference**: `.serena/memories/frontend_backend_schema_mismatch_patterns_2025_11.md`

---

### 9. UUID to JSONB Serialization

**The Problem**: PostgreSQL JSONB cannot store Python UUID objects directly.

```python
# ✅ CORRECT - Recursive UUID serialization
from uuid import UUID

def serialize_uuids_for_jsonb(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all UUID objects to strings for JSONB storage."""
    result = {}
    for key, value in data.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_uuids_for_jsonb(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_uuids_for_jsonb(item) if isinstance(item, dict)
                else str(item) if isinstance(item, UUID)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result

# Usage
conflict_record = AssetConflictResolution(
    new_asset_data=serialize_uuids_for_jsonb(conflict["new_asset_data"])
)
```

**Reference**: `.serena/memories/uuid_jsonb_serialization_pattern_2025_10.md`

---

### 10. Bug Investigation Workflow (MANDATORY)

**The Rule**: ALWAYS check Serena memories + reproduce BEFORE assuming it's a bug.

```bash
# Step 1: Check Serena memories FIRST
mcp__serena__list_memories
mcp__serena__read_memory <relevant_memory>

# Step 2: Reproduce with Playwright (never ask users)
Task: qa-playwright-tester -> reproduce exact scenario

# Step 3: Analyze backend logic
# Check if behavior is intentional (e.g., adaptive forms, intelligent filtering)

# Step 4: Present analysis BEFORE implementing
# Wait for user approval

# Step 5: If confirmed bug, fix with proper workflow
```

**Red Flags (Might Be Features, Not Bugs)**:
- 🚩 "Fewer items displayed" in adaptive/intelligent systems
- 🚩 "Different behavior per asset/user" in personalized systems
- 🚩 "Empty sections hidden" in smart UIs
- 🚩 "Questions vary by data quality" in gap-based collection

**Reference**: CLAUDE.md "Bug Investigation Workflow", `.serena/memories/bug_investigation_cannot_reproduce_workflow_2025_10.md`

---

## 1. Critical Architecture Patterns

### 1.1 Master Flow Orchestrator (MFO) Pattern

**Purpose**: Single source of truth for ALL workflow operations (ADR-006).

**Two-Table Architecture**:
```
Master Table: crewai_flow_state_extensions
- flow_id (PK)
- flow_type (discovery/assessment/collection/planning)
- flow_status (running/paused/completed)  ← High-level lifecycle

Child Table: {flow_type}_flows (e.g., assessment_flows)
- id (PK) = Same UUID as master flow_id
- master_flow_id (FK) → crewai_flow_state_extensions.flow_id
- status (initialized/running/completed)  ← Operational status
- current_phase
- phase_results (JSONB)
```

**Key Insight**: Frontend uses **child flow status** for decisions, MFO uses **master flow status** for routing (ADR-012).

**Reference**: ADR-006, ADR-012, `/docs/architecture/COLLECTION_FLOW_LAYERING_FIX.md`

---

### 1.2 Flow Execution Pattern Selection (ADR-025)

**Two patterns exist** - choose based on flow characteristics:

#### Child Service Pattern (Collection, Discovery, Decommission)
✅ Use when:
- Multi-phase data collection
- Questionnaire generation
- Auto-progression logic
- Complex state management

```python
# File: backend/app/services/child_flow_services/collection.py
class CollectionChildFlowService(BaseChildFlowService):
    async def execute_phase(self, flow_id: str, phase_name: str, phase_input: Dict):
        # Centralized phase routing, state abstraction, auto-progression
        ...
```

#### Direct Flow Pattern (Assessment)
✅ Use when:
- Analysis workflows
- Linear phase progression
- Simpler state management
- No questionnaire generation

```python
# File: backend/app/services/crewai_flows/unified_assessment_flow.py
# Direct CrewAI integration, simpler architecture
```

**Reference**: ADR-025, CLAUDE.md "Flow Execution Pattern Selection"

---

### 1.3 Seven-Layer Enterprise Architecture

**NOT over-engineering** - REQUIRED for enterprise resilience, multi-tenant isolation, and atomic transactions.

```
1. API Layer (FastAPI routes) - Request handling and validation
2. Service Layer (business logic) - Orchestration and workflow
3. Repository Layer (data access) - Database abstraction
4. Model Layer (SQLAlchemy/Pydantic) - Data structures
5. Cache Layer (Redis/in-memory) - Performance optimization
6. Queue Layer (async processing) - Background tasks
7. Integration Layer (external services) - Third-party APIs
```

**Reference**: CLAUDE.md "Seven-Layer Enterprise Architecture", `.serena/memories/architectural_patterns.md`

---

### 1.4 TenantMemoryManager (Enterprise Agent Memory)

**Rule**: CrewAI built-in memory is DISABLED (see Quick Reference #3). Use TenantMemoryManager for all agent learning.

```python
from app.services.crewai_flows.memory.tenant_memory_manager import (
    TenantMemoryManager,
    LearningScope
)

# Store agent learnings
memory_manager = TenantMemoryManager(crewai_service, db)
await memory_manager.store_learning(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,  # or CLIENT, GLOBAL
    pattern_type="field_mapping",
    pattern_data={
        "source_field": "cust_name",
        "target_field": "customer_name",
        "confidence": 0.95
    }
)

# Retrieve similar patterns before agent execution
patterns = await memory_manager.retrieve_similar_patterns(
    client_account_id=client_account_id,
    engagement_id=engagement_id,
    scope=LearningScope.ENGAGEMENT,
    pattern_type="field_mapping",
    query_context={"source_field": "customer"}
)
```

**Benefits over CrewAI Memory**:
- ✅ Multi-tenant isolation (engagement/client/global scopes)
- ✅ PostgreSQL + pgvector (native to stack, no external ChromaDB)
- ✅ Enterprise features: data classification, audit trails, encryption
- ✅ No 401/422 DeepInfra authentication errors

**Reference**: ADR-024, `/docs/development/TENANT_MEMORY_STRATEGY.md`

---

## 2. Common Bug Patterns and Fixes

### 2.1 API 422 Errors (Request Body vs Query Parameters)

**Symptom**: FastAPI returns 422 Unprocessable Entity on POST/PUT/DELETE requests.

**Root Cause**: Frontend sending query parameters instead of request body.

```typescript
// ❌ WRONG
const url = `/api/endpoint?param=value`;
await apiCall(url, { method: 'POST' });

// ✅ CORRECT
const url = `/api/endpoint`;
await apiCall(url, {
  method: 'POST',
  body: JSON.stringify({ param: 'value' })
});
```

**Reference**: See Quick Reference #2

---

### 2.2 Frontend NaN, Disabled Buttons

**Symptom**: UI shows "NaN%", buttons always grayed out.

**Root Cause**: Backend Pydantic model missing fields frontend expects.

**Fix Pattern**:

```python
# Backend: Add optional fields with defaults
class Recommendation(BaseModel):
    id: str
    title: str
    confidence: Optional[float] = 0.85  # Default prevents NaN
    status: str = 'pending'  # Default enables buttons
```

```typescript
// Frontend: Defensive null checks
{rec.confidence !== undefined && rec.confidence !== null
  ? `${Math.round(rec.confidence * 100)}%`
  : 'N/A'}

<Button disabled={rec.status !== 'pending' || !rec.status}>Apply</Button>
```

**Debugging Checklist**:
- [ ] Check browser Network tab → API response structure
- [ ] Compare JSON to TypeScript interface
- [ ] Find Pydantic model in backend
- [ ] Add missing field with sensible default
- [ ] Update TypeScript interface to match
- [ ] Add defensive null checks in UI

**Reference**: See Quick Reference #8

---

### 2.3 Async/Await Errors

**Symptom**: `"object dict can't be used in 'await' expression"`

**Root Cause**: Trying to await a synchronous function.

```python
# ❌ WRONG - Function is sync, not async
def get_data() -> dict:
    return {"data": "value"}

result = await get_data()  # ERROR!

# ✅ FIX 1 - Remove await
result = get_data()

# ✅ FIX 2 - Make function async if needed
async def get_data() -> dict:
    await some_async_operation()
    return {"data": "value"}
```

**Reference**: `.serena/memories/async_await_error_patterns.md`

---

### 2.4 Context Switching Race Conditions

**Symptom**: User A sees User B's data after rapid context switches.

**Root Cause**: Stale cached services or LRU-cached functions.

```python
# ❌ WRONG - Caches across tenants
@lru_cache(maxsize=1)
def get_tenant_data():
    return fetch_data()

# ✅ CORRECT - Fresh instances per request
def get_service(db: AsyncSession, context: RequestContext):
    return DiscoveryFlowService(db=db, context=context)
```

**Reference**: `.serena/memories/context-switching-race-condition-pattern.md`

---

### 2.5 Circular Import Errors in Alembic

**Symptom**: Migrations fail with circular import when importing models.

**Solution**: Use SQLAlchemy core (Table, Column) instead of ORM models in migrations.

```python
# ❌ WRONG - Imports ORM model
from app.models.asset import Asset

# ✅ CORRECT - Use table reflection or core constructs
from sqlalchemy import table, column, String, Integer

asset_table = table(
    'assets',
    column('id', String),
    column('name', String),
)
```

**Reference**: `.serena/memories/alembic_migration_gotchas.md`

---

## 3. Testing Patterns

### 3.1 QA Playwright Testing Pattern

**Rule**: NEVER ask users for manual testing. Use qa-playwright-tester agent.

**Agent Workflow**:
```typescript
// 1. Deploy agent with specific scenario
Task: qa-playwright-tester
Prompt: "
  Test scenario:
  1. Navigate to http://localhost:8081
  2. Login with demo@demo-corp.com / Demo123!
  3. Click 'Continue Flow' on flow ID: {specific-id}
  4. Verify:
     - Response time < 1 second
     - No JavaScript errors in console
     - Navigation works (no 404 errors)
     - User guidance displayed
"

// 2. Agent tests actual browser interactions
// 3. Provides screenshots and detailed reports
// 4. Catches routing errors, performance issues, UX problems
```

**Common Issues Found**:
- 404 routing errors (backend/frontend mismatch)
- Performance issues (operations > 1 second)
- Missing UI elements
- Console JavaScript errors

**Reference**: `.serena/memories/qa_playwright_testing_patterns.md`

---

### 3.2 Test Data UUID Requirements

**The Problem**: Tests using invalid placeholder UUIDs cause FK violations.

**Actual Demo UUIDs** (from `backend/seeding/constants.py`):
```python
DEMO_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")
DEMO_ENGAGEMENT_ID = UUID("22222222-2222-2222-2222-222222222222")
```

**Test Configuration**:
```typescript
tenantHeaders = {
  'X-Client-Account-ID': '11111111-1111-1111-1111-111111111111',
  'X-Engagement-ID': '22222222-2222-2222-2222-222222222222'
};
```

**Getting IDs from LocalStorage**:
```typescript
const localStorage = await page.evaluate(() => ({
  clientAccountId: localStorage.getItem('auth_client_id') || '11111111-1111-1111-1111-111111111111',
  engagementId: localStorage.getItem('engagementId') || '22222222-2222-2222-2222-222222222222'
}));
```

**Reference**: `.serena/memories/test_data_uuid_requirements.md`

---

### 3.3 E2E Testing Methodology

**Pattern**: Test complete user journeys, not just unit tests.

```typescript
// Example: Collection flow E2E test
test('Full collection flow journey', async ({ page }) => {
  // 1. Login
  await loginAsDemo(page);

  // 2. Create collection flow
  const flowId = await createCollectionFlow(page);

  // 3. Generate questionnaires
  await navigateToQuestionnaires(page, flowId);
  await waitForQuestionnaireGeneration(page);

  // 4. Submit responses
  await submitQuestionnaireResponses(page, flowId);

  // 5. Verify gap analysis
  await verifyGapAnalysis(page, flowId);

  // 6. Check flow completion
  await verifyFlowCompleted(page, flowId);
});
```

**Reference**: `.serena/memories/e2e_collection_assessment_testing_october_2025.md`

---

### 3.4 Iterative QA Bug Discovery Workflow

**Pattern**: QA agent finds bugs → Fix → QA agent validates → Repeat.

```bash
# Step 1: QA discovers issues
Task: qa-playwright-tester -> FINDS 3 BUGS

# Step 2: Fix bugs with SRE agent
Task: sre-precommit-enforcer -> FIX BUG 1, 2, 3

# Step 3: QA validates fixes
Task: qa-playwright-tester -> VALIDATE ALL FIXES

# If new bugs found, repeat from Step 2
```

**Benefits**:
- Catches regressions immediately
- Validates fixes work end-to-end
- Prevents shipping broken code

**Reference**: `.serena/memories/iterative-qa-bug-discovery-workflow.md`

---

## 4. Security Patterns

### 4.1 Multi-Tenant Query Scoping (CRITICAL)

**Rule**: ALWAYS include `client_account_id` and `engagement_id` in ALL database queries.

```python
# ✅ CORRECT - Tenant-scoped query
from sqlalchemy import select, and_

stmt = select(DataImport).where(
    and_(
        DataImport.id == UUID(data_import_id),
        DataImport.client_account_id == client_account_id,
        DataImport.engagement_id == engagement_id,
    )
)
```

**DELETE Operations** (Critical for cleanup):
```python
# ✅ CORRECT - Tenant-scoped delete
delete_stmt = delete(ImportFieldMapping).where(
    and_(
        ImportFieldMapping.data_import_id == data_import_id,
        ImportFieldMapping.client_account_id == client_account_id,
    )
)
```

**Tables Requiring Tenant Scoping**:
- DataImport
- ImportFieldMapping
- DiscoveryFlow, CollectionFlow, AssessmentFlow
- Asset
- FlowExecution
- CrewAIFlowStateExtension
- **ANY table with client_account_id and engagement_id fields**

**Reference**: See Quick Reference #4

---

### 4.2 SQL Injection Prevention (Enum Types)

**Problem**: String interpolation with PostgreSQL enums creates SQL injection vulnerabilities.

```python
# ❌ VULNERABLE - SQL Injection Risk!
query = query.where(
    text(f"pattern_type = '{pattern_type}'::patterntype")
)

# ✅ SECURE - Parameterized query
from sqlalchemy import text

query = query.where(
    text("pattern_type = :pattern_type::patterntype").bindparams(
        pattern_type=pattern_type
    )
)
```

**Alternative** (when enum properly mapped):
```python
# ✅ Direct column comparison
query = query.where(
    AgentDiscoveredPatterns.pattern_type == pattern_type
)
```

**Reference**: `.serena/memories/sql_injection_prevention_enum_types.md`

---

### 4.3 JWT Token Validation

**Rules**:
- Never trust unverified JWT payloads for security decisions
- Reject suspicious subjects: "system", "admin", "root", "service", "bot"
- Validate minimum subject length (≥3 characters)
- Check for service account patterns

**Authorization Header Normalization**:
```python
# ✅ Handle case variations and extra spaces
normalized_header = auth_header.strip()
if not normalized_header.lower().startswith("bearer "):
    return None
parts = normalized_header.split()
if len(parts) != 2 or not parts[1]:
    return None
token = parts[1]
```

**Reference**: `.serena/memories/security_best_practices.md`

---

### 4.4 Secure Error Logging

**Rule**: NEVER log raw exception messages (may contain sensitive data).

```python
# ❌ WRONG - May leak sensitive data
logger.error(f"Operation failed: {str(e)}")

# ✅ CORRECT - Log exception type only
from app.core.logging_utils import safe_log_format

logger.error(
    safe_log_format(
        "Operation failed: {error_type}",
        error_type=type(e).__name__
    )
)
```

**Frontend Debug Logging**:
```typescript
// ✅ Gate debug logs behind environment variable
const DEBUG_ENABLED = process.env.NODE_ENV !== 'production' &&
                      process.env.NEXT_PUBLIC_DEBUG_LOGS === 'true';

if (DEBUG_ENABLED) {
    const truncated = JSON.stringify(data).substring(0, 200) + '...[truncated]';
    console.log(message, truncated);
}
```

**Reference**: `.serena/memories/security_best_practices.md`

---

## 5. Database Patterns

### 5.1 Alembic Idempotent Migrations

**Rule**: Use 3-digit prefix + PostgreSQL DO blocks with IF EXISTS/NOT EXISTS checks.

**Template**:
```python
"""add_columns_to_table

Revision ID: 092_add_columns_to_table
Revises: 091_previous_migration
Create Date: 2025-01-12
"""
from alembic import op
import sqlalchemy as sa

revision = "092_add_columns_to_table"
down_revision = "091_previous_migration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """IDEMPOTENT: Uses IF NOT EXISTS checks"""
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='engagement_architecture_standards'
                AND column_name='supported_versions'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                ADD COLUMN supported_versions JSONB DEFAULT '{}'::jsonb;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """IDEMPOTENT: Uses IF EXISTS checks"""
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema='migration'
                AND table_name='engagement_architecture_standards'
                AND column_name='supported_versions'
            ) THEN
                ALTER TABLE migration.engagement_architecture_standards
                DROP COLUMN supported_versions;
            END IF;
        END $$;
    """)
```

**Key Requirements**:
1. **3-digit prefix**: `092_description.py` (NOT `228e0eae6242_description.py`)
2. **Revision chain**: `down_revision = "091_previous_migration"`
3. **Schema prefix**: Always use `migration.table_name`
4. **Test idempotency**: Run `upgrade head` → `downgrade -1` → `upgrade head`

**Reference**: See Quick Reference #7

---

### 5.2 Repository Transaction Management

**Rule**: Repository methods do `flush()` but NOT `commit()`. Caller manages transaction boundaries.

```python
# Repository method pattern
class BaseRepository:
    async def update_entity(self, entity_id: UUID, **updates):
        stmt = update(Entity).where(Entity.id == entity_id).values(**updates)
        await self.db.execute(stmt)
        await self.db.flush()  # ✅ Flush, don't commit

        updated = await self.get_entity_by_id(entity_id)
        return updated
        # Caller will commit
```

**Caller pattern**:
```python
# ❌ WRONG - Nested transaction error
async with db.begin():
    updated_flow = await repo.update_planning_flow(...)

# ✅ CORRECT - Let repository flush, caller commits
updated_flow = await repo.update_planning_flow(...)
await db.commit()
```

**Reference**: See Quick Reference #5

---

### 5.3 SQLAlchemy IntegrityError Rollback

**Rule**: Immediate rollback after IntegrityError to prevent session invalidation.

```python
from sqlalchemy.exc import IntegrityError

async def create_asset(...):
    try:
        created_asset = await create_method(...)
        return created_asset
    except IntegrityError as ie:
        await session.rollback()  # CRITICAL: Prevent session invalidation

        # Differentiate error types
        error_msg = str(ie.orig).lower() if hasattr(ie, "orig") else str(ie).lower()

        is_unique_violation = any(
            keyword in error_msg
            for keyword in ["unique constraint", "duplicate key", "duplicate entry"]
        )

        if is_unique_violation:
            # Race condition - can retry
            logger.warning(f"⚠️ Unique constraint violation (race condition): {ie}")
            raise  # Caller can retry
        else:
            # NOT NULL, foreign key, CHECK constraint - unrecoverable
            logger.error(f"❌ Unrecoverable IntegrityError: {ie}")
            raise  # Caller should NOT retry
```

**Reference**: See Quick Reference #6

---

### 5.4 UUID to JSONB Serialization

**Rule**: PostgreSQL JSONB cannot store Python UUID objects - convert to strings first.

```python
from typing import Dict, Any
from uuid import UUID

def serialize_uuids_for_jsonb(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all UUID objects to strings for JSONB storage."""
    result = {}
    for key, value in data.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, dict):
            result[key] = serialize_uuids_for_jsonb(value)
        elif isinstance(value, list):
            result[key] = [
                serialize_uuids_for_jsonb(item) if isinstance(item, dict)
                else str(item) if isinstance(item, UUID)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result
```

**Usage**:
```python
# ✅ Serialize before storing in JSONB column
conflict_record = AssetConflictResolution(
    client_account_id=UUID(client_account_id),  # Regular UUID column - OK
    new_asset_data=serialize_uuids_for_jsonb(conflict["new_asset_data"])  # JSONB - Serialize!
)
db_session.add(conflict_record)
```

**Reference**: See Quick Reference #9

---

### 5.5 SQLAlchemy Async Session Patterns

**Rule**: Use `async with` for atomic transactions.

```python
# ✅ Atomic transaction pattern
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

async with AsyncSession(engine) as session:
    async with session.begin():
        # All operations atomic
        await repo1.save(entity1)
        await repo2.save(entity2)
    # Auto-commit on success, rollback on exception
```

**Fresh Session in Background Workers**:
```python
# ❌ WRONG - Use request scope session in worker
async def worker(db: AsyncSession, ...):
    # Wrong - db session may be closed

# ✅ CORRECT - Create fresh session
from app.core.database import AsyncSessionLocal

async def worker(client_account_id: str, ...):
    async with AsyncSessionLocal() as db:
        # worker logic with fresh session
```

**Reference**: `.serena/memories/sqlalchemy_async_session_tracking_patterns.md`

---

## 6. Agent Orchestration Patterns

### 6.1 Multi-Agent Parallel Execution

**Rule**: Deploy agents in parallel when tasks are independent, sequentially when dependent.

**Parallel Pattern** (independent tasks):
```typescript
// All can run simultaneously
agents = [
    { type: "python-crewai-fastapi-expert", scope: "backend/app/api/" },
    { type: "nextjs-ui-architect", scope: "src/pages/" },
    { type: "docs-curator", scope: "docs/" }
];

// Execute all in parallel
// No file overlap between agents
```

**Sequential Pattern** (dependent tasks):
```bash
# Step 1: QA reproduces bug
Task: qa-playwright-tester -> REPRODUCTION_STATUS

# Step 2: SRE fixes (only if Step 1 approved)
Task: sre-precommit-enforcer -> IMPLEMENT_FIX

# Step 3: DevSecOps validates
Task: devsecops-linting-engineer -> VALIDATE_CHANGES

# Step 4: QA final validation
Task: qa-playwright-tester -> VALIDATE_FIX
```

**Critical Rules**:
1. **No file overlap** between parallel agents
2. **Explicit scope** in agent prompts
3. **Retry logic** for API limit errors
4. **Independent domains** (backend vs frontend vs docs)

**Reference**: `.serena/memories/multi_agent_orchestration_patterns.md`

---

### 6.2 Agent Task Delegation with Strict Instructions

**Problem**: Agents improvising beyond plan scope.

**Solution**: Strict prompt structure.

```markdown
IMPORTANT: First read these files:
1. /docs/analysis/Notes/coding-agent-guide.md
2. /.claude/agent_instructions.md

CRITICAL: STICK TO THE PLAN. Do NOT improvise or add features not in the plan.

Your scope is LIMITED to these files:
- backend/app/services/collection_flow/
- backend/app/repositories/collection_flow_repository.py

DO NOT modify any files outside this scope.

After completion, provide detailed summary following template in agent_instructions.md.
```

**Benefits**:
- Prevents agent hallucination
- Avoids scope creep
- Maintains architectural consistency

**Reference**: `.serena/memories/multi_agent_orchestration_patterns.md`

---

### 6.3 Issue Triage Before Implementation

**Pattern**: Deploy issue-triage-coordinator BEFORE implementing fixes.

```bash
# Step 1: Triage (systematic validation)
Task: issue-triage-coordinator
Prompt: "
  1. Check if issue already fixed (git log, GitHub comments)
  2. Verify bug exists (database query, Playwright test)
  3. Check Serena memories (architectural intent)
  4. Determine: FIX / ALREADY_FIXED / INVALID / CANNOT_REPRODUCE
"

# Step 2: Only fix if triage says FIX needed
# If ALREADY_FIXED or INVALID, close with comment
# If CANNOT_REPRODUCE, add enhanced logging and monitor
```

**Results**: 57% of bugs (4/7) didn't need new code (already fixed or invalid).

**Reference**: `.serena/memories/automated_bug_fix_multi_agent_workflow_2025_11.md`

---

## 7. Observability Patterns

### 7.1 LLM Usage Tracking (MANDATORY)

**Rule**: ALL LLM calls MUST use `multi_model_service.generate_response()` for automatic tracking.

```python
from app.services.multi_model_service import multi_model_service, TaskComplexity

# ✅ CORRECT - Automatic tracking to llm_usage_logs table
response = await multi_model_service.generate_response(
    prompt="Your prompt here",
    task_type="chat",  # or "field_mapping", "analysis", etc.
    complexity=TaskComplexity.SIMPLE  # or AGENTIC for complex tasks
)
```

**Benefits**:
- ✅ Automatic logging to `llm_usage_logs` with cost calculation
- ✅ Correct model selection (Gemma 3 for chat, Llama 4 for agentic)
- ✅ Token counting and request/response tracking
- ✅ Multi-tenant context (client_account_id, engagement_id)
- ✅ Performance metrics (response time, success rate)

**NEVER use direct LLM calls** (bypass tracking):
- ❌ `litellm.completion()` - Use `multi_model_service` instead
- ❌ `openai.chat.completions.create()` - Use `multi_model_service` instead
- ❌ `LLM().call()` - Use `multi_model_service` instead

**Automatic Tracking via LiteLLM Callback**:
- All LLM calls (including CrewAI) automatically tracked via LiteLLM callback
- Installed at app startup in `app/app_setup/lifecycle.py:116`
- Tracks: Llama 4 (CrewAI), Gemma 3 (OpenAI), and all LLM providers

**Reference**: CLAUDE.md "LLM Usage Tracking", `.serena/memories/llm_tracking_implementation_2025_10_02.md`

---

### 7.2 Agent Task Tracking (Manual Integration Required)

**MANDATORY for all CrewAI task execution** (enforced by pre-commit hooks):

```python
from app.services.crewai_flows.handlers.callback_handler_integration import (
    CallbackHandlerIntegration
)

# 1. Create callback handler with tenant context
callback_handler = CallbackHandlerIntegration.create_callback_handler(
    flow_id=str(master_flow.flow_id),
    context={
        "client_account_id": str(master_flow.client_account_id),
        "engagement_id": str(master_flow.engagement_id),
        "flow_type": "assessment",
        "phase": "readiness"
    }
)
callback_handler.setup_callbacks()

# 2. Create task
task = Task(
    description="Your task description",
    expected_output="Expected output format",
    agent=(agent._agent if hasattr(agent, "_agent") else agent)
)

# 3. Register task start BEFORE execution
callback_handler._step_callback({
    "type": "starting",
    "status": "starting",
    "agent": "readiness_assessor",
    "task": "readiness_assessment",
    "content": "Starting task description"
})

# 4. Execute task
future = task.execute_async(context=context_str)
result = await asyncio.wrap_future(future)

# 5. Mark completion with status
callback_handler._task_completion_callback({
    "agent": "readiness_assessor",
    "task_name": "readiness_assessment",
    "status": "completed" if result else "failed",
    "task_id": "readiness_task",
    "output": result
})
```

**Reference**: `/docs/guidelines/OBSERVABILITY_PATTERNS.md`

---

### 7.3 Grafana Dashboard Debugging

**Common Issues**:

#### Dashboard Shows "No Data"
**Root Cause**: Default time ranges don't match actual data timestamps.

**Fix**:
```json
// In Grafana dashboard JSON (e.g., llm-costs.json):
"time": {
  "from": "now-30d",  // Was: "now-24h" - too narrow
  "to": "now"
}
```

#### Negative Flow Durations
**Root Cause**: Child entity copying parent's old timestamps.

**Fix**:
```python
# ❌ WRONG - Copies old timestamps from parent
child_flow = ChildFlow(
    created_at=parent_flow.created_at,  # Old time
    updated_at=parent_flow.updated_at   # Even older!
)

# ✅ CORRECT - Let SQLAlchemy defaults work
child_flow = ChildFlow(
    # created_at and updated_at omitted
    # SQLAlchemy model has server_default=func.now()
)
```

**Reference**: `.serena/memories/observability-grafana-dashboard-debugging.md`

---

### 7.4 Viewing Observability Data

**Grafana Dashboards** (http://localhost:9999):
- **LLM Costs**: `/d/llm-costs/` - Cost tracking by model/provider
- **Agent Activity**: `/d/agent-activity/` - Agent performance and usage
- **CrewAI Flows**: `/d/crewai-flows/` - Flow execution metrics

**Database Tables**:
- `migration.llm_usage_logs` - All LLM API calls with costs
- `migration.agent_task_history` - CrewAI task execution tracking
- `migration.llm_model_pricing` - Cost per 1K tokens by model

**Frontend**:
- Navigate to `/finops/llm-costs` to see real-time usage and costs

**Reference**: CLAUDE.md "LLM Usage Tracking"

---

## 8. Development Workflow Patterns

### 8.1 Git Operations for Clean PR Creation

**Problem**: Temporary analysis files committed to PR.

**Solution**: Soft reset method.

```bash
# Step 1: Find parent commit (before your changes)
git log --oneline -5

# Step 2: Soft reset to parent (keeps changes in working tree)
git reset --soft <parent-commit-hash>

# Step 3: Unstage unwanted files
git restore --staged .claude/commands/fix-bugs.md
git restore --staged ISSUE_962_FIX_SUMMARY.md
git restore --staged TEST_REPORT_*.md

# Step 4: Verify only desired files staged
git status

# Step 5: Create clean commit
git commit -m "fix: Resolve multiple bug issues

Issues addressed:
- #964: React controlled component warning
- #963: Type annotation UUID migration
- #962: Database test data cleanup"

# Step 6: Force push (with safety check)
git push --force-with-lease origin <branch-name>
```

**Alternative for Multiple Commits**:
```bash
git rebase -i HEAD~3

# In editor, mark commits to edit:
# edit abc1234 First commit
# pick def5678 Second commit

# For each "edit" stop:
git reset HEAD~1  # Unstage everything
git add <only-wanted-files>
git commit -c ORIG_HEAD
git rebase --continue
```

**Reference**: `.serena/memories/git_operations_clean_pr_patterns.md`

---

### 8.2 Docker Command Patterns

**Critical Pattern**: All Docker commands use `-f config/docker/docker-compose.yml`.

```bash
# Start services
docker-compose -f config/docker/docker-compose.yml up -d

# View logs
docker-compose -f config/docker/docker-compose.yml logs -f [service]

# Execute commands in container
docker-compose -f config/docker/docker-compose.yml exec [service] [command]

# Database migrations
docker-compose -f config/docker/docker-compose.yml exec backend alembic upgrade head

# Database backup
docker-compose -f config/docker/docker-compose.yml exec postgres \
  pg_dump -U postgres -d migration_db > backup.sql
```

**Reference**: `.serena/memories/docker_command_patterns.md`

---

### 8.3 Pre-commit Troubleshooting

**Common Failures**:

#### Black Formatting with Syntax Errors
**Problem**: Black can't format files with syntax errors.
**Solution**: Fix syntax errors first, then run Black.

#### Flake8 Complexity Warnings (C901)
**Problem**: Functions exceed complexity threshold.
**Solution**: Refactor or use `--no-verify` if not critical (warning only).

#### File Length Violations (>400 lines)
**Problem**: Files exceed 400-line limit.
**Solution**: Modularize into separate files or plan refactoring PR.

**Emergency Commit Pattern**:
```bash
# When pre-existing issues block critical fixes
git commit --no-verify -m "fix: Critical production fix

[Detailed message]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Reference**: `.serena/memories/precommit_troubleshooting_2025_01.md`

---

### 8.4 Modularization Patterns

**Rule**: When files exceed 400 lines, convert to package with backward compatibility.

**Pattern**:
```
original_file.py → original_file/
                    ├── __init__.py (preserve public API)
                    ├── base.py (base classes)
                    ├── commands.py (write operations)
                    ├── queries.py (read operations)
                    └── utils.py (helper functions)
```

**Backward Compatibility**:
```python
# In __init__.py - maintain all public imports
from .base import BaseClass
from .commands import create_flow, update_flow
from .queries import get_flow, list_flows

__all__ = ['BaseClass', 'create_flow', 'update_flow', 'get_flow', 'list_flows']
```

**Successful Examples**:
- `azure_adapter.py` (1582→385 lines)
- `crewai_flow_service.py` (1561→39 lines)
- `collection_handlers.py` (1369→73 lines)

**Reference**: `.serena/memories/modularization_patterns.md`

---

### 8.5 Automated Bug Fix Workflow

**Pattern**: Sequential QA → SRE → DevSecOps → QA pipeline.

```bash
# Step 1: Triage
gh issue list --label bug --state open

# Step 2: QA Reproduction
Task: qa-playwright-tester -> APPROVED/NEEDS_INFO

# Step 3: SRE Implementation (only if approved)
Task: sre-precommit-enforcer -> FILES_CHANGED

# Step 4: DevSecOps Validation
Task: devsecops-linting-engineer -> PASSED/FAILED

# Step 5: QA Final Validation
Task: qa-playwright-tester -> APPROVED/NEEDS_REVISION

# If NEEDS_REVISION, loop back to Step 3

# Step 6: Batch Commits, Single PR
git checkout -b "fix/bug-batch-$(date +%Y%m%d-%H%M%S)"
git commit -m "fix: Bug #927 description"
git commit -m "fix: Bugs #875, #876 description"
git push -u origin <branch-name>
gh pr create --title "fix: Bug batch - Date"

# Step 7: Update Issues
gh issue comment <number> --body "✅ Issue Fixed..."
gh issue edit <number> --add-label "fixed-pending-review"
```

**Metrics from Real Session**:
- 7 bugs triaged
- 3 fixed, 4 closed (already fixed/invalid)
- 100% validation pass rate
- 0 agent failures

**Reference**: `.serena/memories/automated_bug_fix_multi_agent_workflow_2025_11.md`

---

### 8.6 Branch Lifecycle Management

**Pattern**: Create timestamped feature branches for batch fixes.

```bash
# Create feature branch
BRANCH="fix/bug-batch-$(date +%Y%m%d-%H%M%S)"
git checkout -b "$BRANCH"

# Fix multiple bugs, commit individually
git add <files_for_bug_1>
git commit -m "fix: Bug #1 description"

git add <files_for_bug_2>
git commit -m "fix: Bug #2 description"

# Push once with all commits
git push -u origin "$BRANCH"

# Create single PR covering all fixes
gh pr create --title "fix: Bug batch - Nov 7, 2025" --body "..."

# After merge, delete branch
git branch -d "$BRANCH"
git push origin --delete "$BRANCH"
```

**Reference**: `.serena/memories/branch_lifecycle_management.md`

---

## Cross-References to Detailed Documentation

### Architecture Decision Records (ADRs)
- **ADR-006**: Master Flow Orchestrator (`/docs/adr/006-master-flow-orchestrator.md`)
- **ADR-012**: Flow Status Management Separation (`/docs/adr/012-flow-status-management.md`)
- **ADR-015**: Persistent Multi-Tenant Agent Architecture (`/docs/adr/015-persistent-agents.md`)
- **ADR-019**: CrewAI DeepInfra Embeddings Monkey Patch (`/docs/adr/019-crewai-deepinfra-patch.md`)
- **ADR-024**: TenantMemoryManager Architecture (`/docs/adr/024-tenant-memory-manager-architecture.md`)
- **ADR-025**: Collection Flow Child Service Migration (`/docs/adr/025-collection-flow-child-service-migration.md`)

### Guidelines
- `/docs/guidelines/API_REQUEST_PATTERNS.md` - API request body patterns
- `/docs/guidelines/OBSERVABILITY_PATTERNS.md` - LLM and agent tracking
- `/docs/guidelines/ARCHITECTURAL_REVIEW_GUIDELINES.md` - Review patterns
- `/docs/guidelines/AUTOMATED_BUG_FIX_WORKFLOW.md` - Multi-agent bug fixing

### Development Guides
- `/docs/development/TENANT_MEMORY_STRATEGY.md` - TenantMemoryManager usage
- `/docs/analysis/Notes/coding-agent-guide.md` - Implementation patterns
- `/docs/analysis/Notes/000-lessons.md` - Critical architectural lessons
- `/.claude/agent_instructions.md` - Subagent requirements

### Serena Memories
All patterns in this document are derived from 300+ Serena memories. Access with:
```bash
mcp__serena__list_memories  # List all available memories
mcp__serena__read_memory <memory_name>  # Read specific memory
```

---

## Summary: Most Critical Patterns for New Agents

When starting work on ANY feature or bug fix:

1. ✅ **Read CLAUDE.md first** - Contains all mandatory patterns
2. ✅ **Check Serena memories** - Previous bugs/solutions documented
3. ✅ **Reproduce bugs with Playwright** - Never assume, always verify
4. ✅ **Use MFO two-table pattern** - Master vs child flow IDs
5. ✅ **Scope all queries with tenant context** - Security requirement
6. ✅ **Use request body for POST/PUT/DELETE** - NOT query parameters
7. ✅ **Never enable CrewAI memory** - Use TenantMemoryManager
8. ✅ **Rollback on IntegrityError** - Prevent session invalidation
9. ✅ **Make migrations idempotent** - 3-digit prefix + IF EXISTS checks
10. ✅ **Track all LLM usage** - Use multi_model_service

**When in doubt**:
- Check existing code patterns before adding new code
- Review git history for similar changes
- Ask user for clarification rather than assuming
- Present analysis BEFORE implementing fixes

---

**Document Status**: Active and Maintained
**Last Review**: January 2025
**Next Review**: As needed when new critical patterns emerge
**Maintainer**: Claude Code Documentation Curator Agent
