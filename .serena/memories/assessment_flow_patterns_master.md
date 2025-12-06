# Assessment Flow Patterns Master

**Last Updated**: 2025-12-05
**Version**: 1.1
**Consolidates**: 10 memories + 4 patterns (PR #1231)
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Dual State Architecture**: Pydantic (API/DB) vs In-Memory (CrewAI) - not duplication
> 2. **Two-Phase Completion**: Agents complete → in_progress → User confirms → completed
> 3. **MFO Two-Table Pattern**: master_flow_id (lifecycle) + child flow (operational)
> 4. **Readiness Transition**: Collection completion → Asset readiness → Assessment eligibility
> 5. **Direct Flow Pattern**: Assessment uses Direct Flow (not Child Service) per ADR-025
>
> **New patterns (December 2025):**
> - **Pattern 8**: Phase-Data Endpoint Extension - adding new phase handlers
> - **Pattern 9**: Schema-Resilient JSONB Field Detection - backward compatible field checks
> - **Pattern 10**: Custom ApiError - preserve HTTP response body for frontend error handling
> - **Pattern 11**: Pre-Commit Modularization Workflow - via linting agent delegation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Readiness Transition](#readiness-transition)
4. [Common Patterns](#common-patterns)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)
7. [Troubleshooting](#troubleshooting)
8. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Assessment Flow handles cloud readiness assessment and 6R migration recommendations. It analyzes collected data to generate architecture standards, tech debt analysis, dependency mapping, and 6R strategy decisions.

### When to Reference
- Implementing Assessment Flow endpoints
- Debugging state management issues
- Understanding Pydantic vs In-Memory model usage
- Fixing readiness transition bugs
- Integrating with Collection Flow

### Key Files
- `backend/app/api/v1/endpoints/assessment_flow/`
- `backend/app/services/crewai_flows/unified_assessment_flow.py`
- `backend/app/models/assessment_flow_state/` (Pydantic)
- `backend/app/models/assessment_flow/` (In-Memory)

---

## Architecture Patterns

### Pattern 1: Dual State Architecture

**CRITICAL**: Two `AssessmentFlowState` classes exist - this is INTENTIONAL.

| Model | Location | Type | Purpose |
|-------|----------|------|---------|
| Pydantic | `models/assessment_flow_state/` | BaseModel | API, DB, validation |
| In-Memory | `models/assessment_flow/` | Plain Python | CrewAI agent execution |

**Why Both Exist**:
1. **Performance**: Pydantic validation overhead during 100+ agent mutations
2. **Serialization**: CrewAI TaskOutput not JSON serializable
3. **Circular Imports**: Separate concerns prevent import cycles

**Architecture Flow**:
```
API Layer (Pydantic) → MFO → CrewAI (In-Memory) → Database (Pydantic)
```

**Import Rules**:
```python
# API/Database/Repository tests
from app.models.assessment_flow_state import AssessmentFlowState  # Pydantic

# CrewAI agents/helpers
from app.models.assessment_flow import AssessmentFlowState  # In-Memory
```

**Source**: `assessment-flow-dual-state-architecture.md`

---

### Pattern 2: Two-Phase Completion

**Problem**: Flow marked "completed" before user review.

**Solution**: Separate agent completion from user finalization.

```python
# Phase 1: Agent completes, stay in_progress
await assessment_repo.update_flow_status(
    flow_id,
    "in_progress",  # NOT "completed"
)
logger.info(f"Recommendations ready - awaiting user finalization")

# Phase 2: User clicks Finalize
if user_confirms:
    await assessment_repo.update_flow_status(flow_id, "completed")
```

**Workflow**:
```
Agent Execution → in_progress (review ready)
        ↓
User Reviews Data
        ↓
User Clicks Finalize → completed
```

**Source**: `assessment_flow_two_phase_completion_pattern.md`

---

### Pattern 3: MFO Two-Table Integration

**Two Tables**:
- `crewai_flow_state_extensions`: Master flow lifecycle (running/paused/completed)
- `assessment_flows`: Child flow operational state

**Creation Template**:
```python
async def create_assessment_flow_via_mfo(
    client_account_id: UUID,
    engagement_id: UUID,
    db: AsyncSession
) -> dict:
    flow_id = uuid4()

    async with db.begin():  # Atomic transaction
        # Step 1: Master flow (lifecycle)
        master_flow = CrewAIFlowStateExtensions(
            flow_id=flow_id,
            flow_type="assessment",
            flow_status="running",
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )
        db.add(master_flow)
        await db.flush()

        # Step 2: Child flow (operational)
        child_flow = AssessmentFlow(
            id=uuid4(),  # Different from flow_id!
            master_flow_id=flow_id,  # FK to master
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            status="initialized",
            current_phase="architecture_standards",
        )
        db.add(child_flow)

    return {"flow_id": str(flow_id), "status": "running"}
```

**Key Points**:
- Single `flow_id` UUID shared by master, different ID for child
- `master_flow_id` FK enforces relationship
- Frontend uses child flow status for UI decisions

**Source**: `assessment-flow-mfo-migration-patterns.md`

---

## Readiness Transition

### Pattern 4: Collection → Assessment Readiness

**Two Tracking Systems**:
1. **Collection Flow Level**: `collection_flows.assessment_ready` (Boolean)
2. **Asset Level**: `assets.assessment_readiness` ('ready'|'not_ready')

**Where Asset Readiness Gets Updated**:

| Location | Trigger | Sets Readiness |
|----------|---------|----------------|
| `questionnaire_submission.py` | User submits questionnaire | `ready` |
| `assessment_validation.py` | Collection flow complete | `ready` |
| `background_task.py` | No TRUE gaps found | `ready` |
| `readiness_gaps.py` | Refresh button clicked | Re-evaluates |

**Questionnaire States**:
```
pending → not_ready
ready → not_ready
in_progress → not_ready
completed → ready
failed + "No questionnaires" → ready  # Often missed!
failed + other error → not_ready
```

**Common Bug**: Asset stays "not_ready" after questionnaire completion.

**Root Causes**:
1. Missing commit after `_update_asset_readiness()`
2. GapAnalyzer doesn't check questionnaire completion
3. `save_type='save_progress'` vs `save_type='submit_complete'`

**Source**: `assessment-collection-flow-readiness-transition-patterns-2025-11.md`

---

## Common Patterns

### Pattern 5: Flow Phase Progression

Assessment Flow phases (in order):
1. `architecture_standards`
2. `tech_debt_analysis`
3. `dependency_analysis`
4. `sixr_decisions`
5. `recommendation_generation`
6. User accepts → `completed`
7. Export

### Pattern 6: hasattr vs Truthiness

**Problem**: Empty list `[]` treated as falsy.

```python
# WRONG - Bug: empty list falls through
apps = getattr(flow_state, "selected_apps", None) or []
if apps:  # False for []
    return len(apps)

# CORRECT - Check existence
if hasattr(flow_state, "selected_apps"):
    apps = getattr(flow_state, "selected_apps") or []
    return len(apps)  # Returns 0 for empty list
```

**Source**: `assessment-flow-gap-fixes-nov-2025.md`

### Pattern 7: Post-Deletion Import Cleanup

After deleting any module, run:

```bash
# 1. Search for direct imports
grep -r "from app.services.deleted_module" backend/

# 2. Check __init__.py re-exports
grep -r "from .deleted_module import" backend/app/**/__init__.py

# 3. Check Alembic migrations
grep -r "from app.models.DeletedModel" backend/alembic/

# 4. Verify startup
docker exec -it migration_backend python -m app.main
```

**Source**: `assessment-flow-mfo-migration-patterns.md`

---

### Pattern 8: Phase-Data Endpoint Extension (December 2025)

**Context**: Adding new phase handlers to `update_assessment_phase_data` endpoint.

**File**: `backend/app/api/v1/master_flows/assessment/lifecycle_endpoints/data_updates.py`

**Template for adding a new phase handler**:
```python
# Handle new_phase_name phase
elif phase == "new_phase_name":
    from app.models.assessment_flow import AssessmentFlow
    from uuid import UUID

    app_id = data.get("app_id")
    if not app_id:
        raise HTTPException(status_code=400, detail="app_id is required")

    # Validate UUID format
    try:
        flow_uuid = UUID(flow_id)
        app_uuid_str = str(UUID(app_id))
    except ValueError as uuid_err:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(uuid_err)}")

    # Get flow and update phase_results JSONB
    stmt = select(AssessmentFlow).where(
        AssessmentFlow.id == flow_uuid,
        AssessmentFlow.client_account_id == UUID(client_account_id),
        AssessmentFlow.engagement_id == UUID(engagement_id),
    )
    result = await db.execute(stmt)
    flow = result.scalar_one_or_none()

    if not flow:
        raise HTTPException(status_code=404, detail="Assessment flow not found")

    # Update phase_results with new data
    phase_results = flow.phase_results or {}
    # ... modify phase_results structure ...
    flow.phase_results = phase_results
    await db.commit()

    return sanitize_for_json({
        "flow_id": flow_id,
        "phase": phase,
        "status": "updated",
        "message": f"Phase {phase} updated successfully",
    })
```

**Key Points**:
- Update `supported` string in error message when adding new phase
- Always validate UUID format before database operations
- Use `sanitize_for_json()` for response serialization

**Source**: Issue #719 - six_r_decision phase handler

---

### Pattern 9: Schema-Resilient JSONB Field Detection (December 2025)

**Problem**: JSONB data may have different field names across versions (e.g., `six_r_strategy` vs `overall_strategy`).

**Solution**: Check multiple field names using helper function:

```python
# File: backend/app/repositories/assessment_data_repository/recommendation_queries.py

def has_strategy(app: Dict[str, Any]) -> bool:
    """Accept either 'six_r_strategy' or 'overall_strategy' to detect completed apps."""
    strat = app.get("six_r_strategy") or app.get("overall_strategy")
    return isinstance(strat, str) and len(strat.strip()) > 0

existing_app_ids = {
    str(app.get("application_id"))
    for app in applications
    if app.get("application_id") and has_strategy(app)
}
```

**When to Apply**:
- Reading phase_results JSONB from database
- Checking for completed/processed items
- Backward compatibility with older data formats

**Source**: Qodo Bot suggestion #4, PR #1231

---

### Pattern 10: Custom ApiError for HTTP Response Preservation (December 2025)

**Problem**: Frontend needs access to HTTP response body for detailed error handling (e.g., `apps_not_found` list in 409 responses).

**Solution**: Custom ApiError class in `src/services/ApiClient.ts`:

```typescript
export class ApiError extends Error {
  status: number;
  statusText: string;
  response: {
    data: Record<string, unknown>;
    status: number;
    statusText: string;
  };

  constructor(status: number, statusText: string, data: Record<string, unknown>) {
    super(`HTTP ${status}: ${statusText}`);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
    this.response = { data, status, statusText };
  }
}
```

**Frontend error handling**:
```typescript
catch (error: unknown) {
  const resp = (error as any)?.response || {};
  const status = resp?.status ?? (error as any)?.status;
  const payload = resp?.data ?? resp?.detail ?? (error as any)?.data ?? resp ?? error;

  if (status === 409 && payload?.apps_not_found?.length > 0) {
    // Handle data integrity error with missing apps
    setDataIntegrityError({
      hasError: true,
      missingApps: payload.apps_not_found,
      errorMessage: payload.message,
    });
  }
}
```

**Source**: Issue #719, Qodo Bot suggestion #3

---

### Pattern 11: Pre-Commit Modularization Workflow (December 2025)

**Problem**: Pre-commit hook fails with "file too long" (>400 lines).

**Solution**: Extract logical units into separate files via linting agent.

**Workflow**:
1. Implement feature in main file
2. Pre-commit fails with line count check
3. Delegate to `devsecops-linting-engineer` subagent:
   ```
   The file exceeds 400 lines. Please extract [logical_unit] into a separate file.
   ```
4. Agent creates new file with extracted logic + mixin pattern
5. Main file imports from extracted module
6. Pre-commit passes

**Example extraction**:
```python
# Before: recommendation_executor.py (408 lines)
# After:
#   recommendation_executor.py (380 lines)
#   recommendation_validator.py (50 lines) - contains ValidationMixin
```

**Source**: PR #1231 modularization of recommendation_executor.py

---

### Pattern 12: Stale Readiness Data Refresh (December 2025)

**Problem**: Pre-computed `application_asset_groups` in AssessmentFlow table contains stale `readiness_summary` cached at flow creation. UI shows "0 ready / 0 blocked" despite correct database values.

**Solution**: Refresh helper function:

```python
# backend/app/api/v1/master_flows/assessment/info_endpoints/readiness_utils.py
async def refresh_readiness_for_groups(
    db: AsyncSession,
    application_groups: list,
    client_account_id: Any,
    engagement_id: Any,
) -> list:
    """Refresh readiness_summary from current asset state."""
    all_asset_ids = set()
    for group in application_groups:
        all_asset_ids.update(group.get("asset_ids", []))

    # Query current state (CRITICAL: multi-tenant scoping)
    stmt = select(Asset).where(
        Asset.id.in_([UUID(aid) for aid in all_asset_ids]),
        Asset.client_account_id == UUID(client_account_id),
        Asset.engagement_id == UUID(engagement_id),
    )
    result = await db.execute(stmt)
    assets = {str(a.id): a for a in result.scalars().all()}

    for group in application_groups:
        ready = not_ready = 0
        for aid in group.get("asset_ids", []):
            asset = assets.get(str(aid))
            if asset and asset.assessment_readiness == "ready":
                ready += 1
            else:
                not_ready += 1
        group["readiness_summary"] = {"ready": ready, "not_ready": not_ready}
    return application_groups
```

**Related Fix - Explicit None Check for Zero Score**:
```python
# WRONG - 0.0 is falsy
overall_completeness = float(getattr(asset, "score", 0.85) or 0.85)

# CORRECT
score = getattr(asset, "assessment_readiness_score", None)
overall_completeness = float(score if score is not None else 0.85)
```

**Source**: PR #1215

---

## Anti-Patterns

### Don't: Auto-Complete on Agent Finish

```python
# WRONG - No user review step
if agent_completed:
    await update_status(flow_id, "completed")

# CORRECT - Two-phase completion
if agent_completed:
    await update_status(flow_id, "in_progress")  # Await user confirmation
```

### Don't: Use Wrong Model Type

```python
# WRONG - Pydantic in agent helpers (slow)
from app.models.assessment_flow_state import AssessmentFlowState

# CORRECT - In-Memory for agents
from app.models.assessment_flow import AssessmentFlowState
```

### Don't: Assume Empty List = None

```python
# WRONG
if selected_apps:  # False for []
    process(selected_apps)

# CORRECT
if selected_apps is not None:
    process(selected_apps)  # Works for []
```

### Don't: Delete Modules Without Import Cleanup

Always run the import cleanup checklist after `rm -rf` operations.

---

## Code Templates

### Template 1: Assessment Flow Endpoint

```python
@router.post("/{flow_id}/assessment/execute-phase")
async def execute_assessment_phase(
    flow_id: str,
    phase: str,
    db: AsyncSession = Depends(get_async_db),
    context: RequestContext = Depends(get_request_context),
):
    # Step 1: Get child flow by master_flow_id
    stmt = select(AssessmentFlow).where(
        AssessmentFlow.master_flow_id == UUID(flow_id),
        AssessmentFlow.client_account_id == context.client_account_id,
        AssessmentFlow.engagement_id == context.engagement_id,  # Required for multi-tenant isolation
    )
    result = await db.execute(stmt)
    child_flow = result.scalar_one_or_none()

    if not child_flow:
        raise HTTPException(404, "Assessment flow not found")

    # Step 2: Execute via MFO with master ID
    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(child_flow.master_flow_id),  # Master ID for MFO
        phase,
        {"flow_id": str(child_flow.id)}  # Child ID for persistence
    )

    return result
```

### Template 2: Decommission Integration

```python
@router.post("/{flow_id}/assessment/initiate-decommission")
async def initiate_decommission_from_assessment(
    flow_id: str,
    request_body: Dict[str, Any],
    db: AsyncSession = Depends(get_async_db),
):
    """Create decommission flow from Retire/Retain decisions."""
    app_ids = request_body.get("application_ids", [])

    # Validate apps have Retire strategy
    valid_strategies = ["retire", "retain"]
    # ... validation logic

    # Create decommission flow via MFO
    result = await create_decommission_via_mfo(
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        application_ids=app_ids,
        db=db
    )

    return {"decommission_flow_id": result["flow_id"]}
```

---

## Troubleshooting

### Issue: Tests skipped with "REPOSITORY_AVAILABLE = False"

**Cause**: Test imports In-Memory model instead of Pydantic.

**Fix**:
```python
# WRONG
from app.models.assessment_flow import AssessmentFlowState

# CORRECT
from app.models.assessment_flow_state import AssessmentFlowState
```

### Issue: Asset won't transition to "ready"

**Debug Queries**:
```sql
-- Check asset readiness
SELECT id, name, assessment_readiness, sixr_ready
FROM migration.assets
WHERE canonical_application_id = '<uuid>';

-- Check questionnaire status
SELECT asset_id, completion_status, description
FROM migration.adaptive_questionnaires
WHERE collection_flow_id = '<flow_id>';

-- Find stuck assets
SELECT a.id, a.assessment_readiness, aq.completion_status
FROM migration.assets a
JOIN migration.adaptive_questionnaires aq ON aq.asset_id = a.id
WHERE aq.completion_status = 'completed'
AND a.assessment_readiness = 'not_ready';
```

**Fix Checklist**:
1. Check if commit happened after `_update_asset_readiness()`
2. Check if questionnaire status is truly 'completed'
3. Check if failed with "No questionnaires" (should mark ready)
4. Use Refresh Readiness button to force re-evaluation

### Issue: ImportError after module deletion

**Solution**: Run post-deletion import cleanup checklist (Pattern 7).

---

## Consolidated Sources

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `assessment-flow-mfo-migration-patterns` | 2025-01 | MFO integration patterns |
| `assessment-flow-dual-state-architecture` | 2025-10 | Dual model architecture |
| `assessment_flow_two_phase_completion_pattern` | 2025-11 | Two-phase completion |
| `assessment-collection-flow-readiness-transition-patterns-2025-11` | 2025-11 | Readiness transition |
| `assessment-flow-gap-fixes-nov-2025` | 2025-11 | GAP fixes |
| `assessment_collection_integration_fix_1099_2025_11` | 2025-11 | Integration fixes |
| `assessment_flow_agent_execution_implementation_2025_10` | 2025-10 | Agent execution |
| `assessment-collection-flow-linking` | 2025-11 | Flow linking |
| `issue_661_vs_659_clarification_assessment_vs_collection` | 2025-11 | Issue clarification |
| `session-continuation-assessment-readiness-bugs-2025-11-25` | 2025-11 | Bug fixes |
| `assessment-readiness-stale-data-refresh-pattern-dec-2025` | 2025-12 | Stale readiness refresh |

**Archive Location**: `.serena/archive/assessment/`

---

## Related Documentation

| Resource | Location | Purpose |
|----------|----------|---------|
| ADR-006 | `/docs/adr/006-mfo-integration.md` | MFO architecture |
| ADR-025 | `/docs/adr/025-flow-pattern-selection.md` | Direct vs Child Service |
| Collection Patterns | `collection_flow_patterns_master.md` | Upstream flow |

---

## Search Keywords

assessment, 6r, readiness, dual_state, pydantic, in_memory, mfo, two_phase, collection_integration, stale_data, refresh_readiness
