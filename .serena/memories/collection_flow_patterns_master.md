# Collection Flow Patterns Master

**Last Updated**: 2025-11-30
**Version**: 1.0
**Consolidates**: 35 memories
**Status**: Active

---

## Quick Reference

> **Top 5 patterns to know:**
> 1. **Child Service Pattern**: Use `CollectionChildFlowService` for phase routing (ADR-025)
> 2. **Status vs Phase**: `status` = lifecycle (running/paused), `phase` = operational progress (ADR-012)
> 3. **Dual UUID Lookup**: Query both `id` (PK) and `flow_id` (business ID) columns
> 4. **MFO Registration**: Always register with master flow before child operations
> 5. **Status Filter Exclusion**: COMPLETED flows must remain queryable for transitions

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Patterns](#architecture-patterns)
3. [Common Patterns](#common-patterns)
4. [Bug Fix Patterns](#bug-fix-patterns)
5. [Anti-Patterns](#anti-patterns)
6. [Code Templates](#code-templates)
7. [Troubleshooting](#troubleshooting)
8. [Related Documentation](#related-documentation)
9. [Consolidated Sources](#consolidated-sources)

---

## Overview

### What This Covers
Collection Flow is the data gathering workflow that collects migration-relevant information about assets through gap analysis, questionnaire generation, and adaptive forms. This master memory consolidates all patterns, bug fixes, and architectural decisions for Collection Flow development.

### When to Reference
- Implementing any Collection Flow endpoint
- Debugging Collection Flow state issues
- Adding new phases to Collection Flow
- Integrating with MFO (Master Flow Orchestrator)
- Handling Collection → Assessment transitions

### Key Files in Codebase
- `backend/app/api/v1/endpoints/collection_flow/lifecycle.py`
- `backend/app/services/child_flow_services/collection_child_flow_service.py`
- `backend/app/api/v1/endpoints/collection_crud_queries/status.py`
- `backend/app/api/v1/endpoints/collection_crud_questionnaires/`
- `src/pages/collection/` (frontend)

---

## Architecture Patterns

### Pattern 1: Child Service Pattern (ADR-025)

**When to use**: ALL Collection Flow operations requiring phase routing.

**Architecture**:
```
MFO (Master) → CollectionChildFlowService → Phase Handler → CrewAI Agent
                      ↓
               Phase Routing Table
               Phase State Management
               Auto-Progression Logic
```

**Implementation**:
```python
# backend/app/services/child_flow_services/collection_child_flow_service.py
from app.services.child_flow_services.base_child_flow_service import BaseChildFlowService

class CollectionChildFlowService(BaseChildFlowService):
    """Child service for Collection Flow with phase routing."""

    PHASE_HANDLERS = {
        "asset_selection": AssetSelectionHandler,
        "gap_analysis": GapAnalysisHandler,
        "questionnaire_generation": QuestionnaireGenerationHandler,
        "manual_collection": ManualCollectionHandler,
        "synthesis": SynthesisHandler,
        "finalization": FinalizationHandler,
    }

    async def execute_phase(
        self,
        phase: str,
        phase_input: Dict[str, Any],
    ) -> PhaseResult:
        handler = self.PHASE_HANDLERS.get(phase)
        if not handler:
            raise ValueError(f"Unknown phase: {phase}")
        return await handler(self.db, self.context).execute(phase_input)
```

**Key Rule**: NEVER use deprecated `crew_class` attribute. Use `CollectionChildFlowService` for ALL phase routing.

**Source**: Consolidated from `collection_flow_child_service_migration_pattern_2025_10`

---

### Pattern 2: MFO Two-Table Pattern

**Problem**: Collection Flow uses two tables with different UUIDs that must be properly resolved.

**Tables**:
- `crewai_flow_state_extensions` - Master flow lifecycle (flow_id = master ID)
- `collection_flows` - Child flow operations (id = child PK, flow_id = business ID)

**Solution**:
```python
@router.post("/execute/{flow_id}")  # ← Child ID from URL
async def execute_collection_phase(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
):
    # Step 1: Query child flow using BOTH id and flow_id columns
    flow_uuid = UUID(flow_id)
    stmt = select(CollectionFlow).where(
        (CollectionFlow.id == flow_uuid) | (CollectionFlow.flow_id == flow_uuid),
        CollectionFlow.client_account_id == context.client_account_id,
        CollectionFlow.engagement_id == context.engagement_id,
    )
    result = await db.execute(stmt)
    child_flow = result.scalar_one_or_none()

    if not child_flow or not child_flow.master_flow_id:
        raise HTTPException(status_code=404, detail="Flow not found")

    # Step 2: Call MFO with MASTER ID
    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(child_flow.master_flow_id),  # ← MASTER flow ID
        "phase_name",
        {"flow_id": str(child_flow.id)}  # ← CHILD flow ID for persistence
    )
```

**Source**: Consolidated from `collection-flow-id-resolver-fix`, `mfo_two_table_flow_id_pattern_critical`

---

### Pattern 3: Status vs Phase Separation (ADR-012)

**Critical Rule**: NEVER mix `status` and `phase` values.

| Field | Purpose | Valid Values |
|-------|---------|--------------|
| `status` | Lifecycle state | running, paused, completed, cancelled, failed |
| `current_phase` | Operational progress | asset_selection, gap_analysis, questionnaire_generation, manual_collection, synthesis, finalization |

**Wrong**:
```python
# ❌ "completed" is a STATUS, not a PHASE
return AgentDecision(next_phase="completed")
```

**Correct**:
```python
# ✅ Use actual phase names
return AgentDecision(
    next_phase="synthesis",  # MFO maps to "finalization" for child flows
    confidence=0.95
)
```

**Database Fix** (if already corrupted):
```sql
UPDATE migration.collection_flows
SET current_phase = 'finalization'
WHERE current_phase = 'completed';
```

**Source**: Consolidated from `adr-012-collection-flow-status-remediation`, `collection_flow_phase_status_fixes_2025_10`

---

## Common Patterns

### Pattern 4: Status Filter Exclusion

**Problem**: COMPLETED flows must remain queryable for assessment transitions.

**Solution**: Separate exclusion lists with parameter control:
```python
async def get_collection_flow(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
    include_completed: bool = True,  # Default allows transition queries
) -> CollectionFlowResponse:
    excluded_statuses = [
        CollectionFlowStatus.CANCELLED.value,  # Always exclude
        CollectionFlowStatus.FAILED.value,      # Always exclude
    ]
    if not include_completed:
        excluded_statuses.append(CollectionFlowStatus.COMPLETED.value)

    result = await db.execute(
        select(CollectionFlow).where(
            (CollectionFlow.flow_id == flow_uuid) | (CollectionFlow.id == flow_uuid),
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.status.notin_(excluded_statuses),
        )
    )
```

**Usage**:
- Assessment transition: `include_completed=True` (default)
- Active flow lists: `include_completed=False`

**Source**: Consolidated from `collection_flow_status_filter_exclusion_pattern_2025_11`

---

### Pattern 5: Questionnaire State Machine

**Flow**: `initialized` → `generating` → `generated` → `ready` → `in_progress` → `completed`

```python
# backend/app/services/questionnaire_lifecycle_service.py
class QuestionnaireLifecycleService:
    VALID_TRANSITIONS = {
        "initialized": ["generating"],
        "generating": ["generated", "failed"],
        "generated": ["ready"],
        "ready": ["in_progress"],
        "in_progress": ["completed", "paused"],
        "completed": [],  # Terminal state
        "failed": ["initialized"],  # Allow retry
    }

    async def transition(self, current: str, target: str) -> bool:
        if target not in self.VALID_TRANSITIONS.get(current, []):
            raise InvalidTransitionError(f"Cannot transition from {current} to {target}")
        return True
```

**Source**: Consolidated from `collection-flow-questionnaire-lifecycle-state-machine-2025-11`

---

### Pattern 6: Dual-Source Assessment Validation

**Problem**: Assessment validation failed because it only checked questionnaire responses, not pre-existing asset fields.

**Solution**: Check BOTH sources:
```python
# Step 1: Check questionnaire responses
has_field_from_questionnaire = any(
    qid in collected_question_ids
    for qid in required_questions
)

# Step 2: ALSO check asset fields directly
for asset in selected_assets:
    if asset.criticality or asset.custom_attributes.get("business_criticality"):
        has_field_from_assets = True

# Step 3: Combine
has_required_field = has_field_from_questionnaire or has_field_from_assets
```

**Key Principle**: Gap analysis only collects MISSING data. Pre-existing asset fields satisfy requirements.

**Source**: Consolidated from `collection_flow_phase_status_fixes_2025_10`

---

### Pattern 7: Multi-Tenant Gap Analysis

**All queries MUST include tenant scoping**:
```python
async def get_gaps(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> List[CollectionGap]:
    return await db.execute(
        select(CollectionGap).where(
            CollectionGap.collection_flow_id == UUID(flow_id),
            CollectionGap.client_account_id == context.client_account_id,  # Required
            CollectionGap.engagement_id == context.engagement_id,          # Required
        )
    )
```

**Source**: Consolidated from `collection_gap_analysis_comprehensive_implementation_2025_24`

---

## Bug Fix Patterns

### Bug: 404 on Form Submission After Completion

**Date Fixed**: November 2025
**Symptoms**: Form submission returned 404 for completed flows
**Root Cause**: Status filter excluded COMPLETED flows

**Fix**: See Pattern 4 (Status Filter Exclusion) - use `include_completed=True` for transition endpoints.

**Source**: `collection_flow_status_filter_exclusion_pattern_2025_11`

---

### Bug: Agent Decision Sets Invalid Phase

**Date Fixed**: October 2025
**Symptoms**: Database shows `current_phase = 'completed'`
**Root Cause**: Agent returned `next_phase="completed"` (status value, not phase name)

**Fix**: See Pattern 3 (Status vs Phase Separation) - always use MFO phase names.

**Source**: `collection_flow_phase_status_fixes_2025_10`

---

### Bug: Questionnaire Shows Only Basic Info Section

**Date Fixed**: September 2025
**Symptoms**: 155 questions generated but only 1 section displayed
**Root Cause**: Missing `_arun()` async method in tool class

**Fix**:
```python
# backend/app/services/ai_analysis/questionnaire_generator/tools/generation.py
class QuestionnaireGenerationTool(BaseTool):
    async def _arun(
        self,
        data_gaps: Dict[str, Any],
        business_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        # Generate all 5 sections
        sections = [
            self._generate_basic_info_section(data_gaps),
            self._generate_critical_fields_section(data_gaps),
            self._generate_data_quality_section(data_gaps),
            self._generate_unmapped_section(data_gaps),
            self._generate_technical_section(data_gaps),
        ]
        return {"status": "success", "questionnaires": sections}
```

**Source**: `collection_questionnaire_generation_fix_complete_2025_30`

---

### Bug: Cancelled Flow Shows Partial UI

**Date Fixed**: October 2025
**Issue #**: 799
**Symptoms**: Accessing cancelled flow via URL showed gaps but no continue button
**Root Cause**: `get_collection_flow()` lacked status filtering

**Fix**: Add status filter to exclude CANCELLED/FAILED flows:
```python
CollectionFlow.status.notin_([
    CollectionFlowStatus.CANCELLED.value,
    CollectionFlowStatus.FAILED.value,
])
```

**Source**: `collection_flow_error_handling_cancelled_flows_2025_10`

---

### Bug: TenantScopedAgentPool Initialization

**Date Fixed**: January 2025
**Symptoms**: `'dict' object has no attribute 'get_or_create_agent'`
**Root Cause**: Using return value (None) instead of class reference

**Fix**:
```python
# ❌ WRONG
self._modular_executor.agent_pool = await TenantScopedAgentPool.initialize_tenant_pool(...)

# ✅ CORRECT
await TenantScopedAgentPool.initialize_tenant_pool(...)
self._modular_executor.agent_pool = TenantScopedAgentPool  # Use class reference
```

**Source**: `collection_assessment_transition_fixes`

---

## Anti-Patterns

### Don't: Mix Status and Phase Values

**Why it's bad**: Breaks ADR-012 compliance, causes routing failures

**Wrong**:
```python
flow.current_phase = "completed"  # "completed" is a status!
```

**Right**:
```python
flow.current_phase = "finalization"
flow.status = CollectionFlowStatus.COMPLETED.value
```

---

### Don't: Query Single UUID Column

**Why it's bad**: Misses flows with different `id` vs `flow_id` values

**Wrong**:
```python
.where(CollectionFlow.flow_id == flow_uuid)
```

**Right**:
```python
.where(
    (CollectionFlow.id == flow_uuid) | (CollectionFlow.flow_id == flow_uuid)
)
```

---

### Don't: Use `crew_class` for Phase Routing

**Why it's bad**: Deprecated pattern, use Child Service Pattern

**Wrong**:
```python
flow_config = {"crew_class": "CollectionAnalysisCrew"}
```

**Right**:
```python
# Use CollectionChildFlowService.PHASE_HANDLERS
service = CollectionChildFlowService(db, context)
await service.execute_phase("gap_analysis", phase_input)
```

---

### Don't: Mutate React Query Cache

**Why it's bad**: Causes stale data, unexpected re-renders

**Wrong**:
```typescript
const sorted = cachedData.sort((a, b) => ...);
```

**Right**:
```typescript
const sorted = [...cachedData].sort((a, b) => ...);
```

---

## Code Templates

### Template 1: Collection Flow Endpoint

```python
@router.post("/{flow_id}/execute-phase")
async def execute_collection_phase(
    flow_id: str,
    phase: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
):
    """Execute a collection flow phase."""
    # 1. Resolve child flow with dual UUID lookup
    flow_uuid = UUID(flow_id)
    stmt = select(CollectionFlow).where(
        (CollectionFlow.id == flow_uuid) | (CollectionFlow.flow_id == flow_uuid),
        CollectionFlow.client_account_id == context.client_account_id,
        CollectionFlow.engagement_id == context.engagement_id,
        CollectionFlow.status.notin_([
            CollectionFlowStatus.CANCELLED.value,
            CollectionFlowStatus.FAILED.value,
        ]),
    )
    result = await db.execute(stmt)
    child_flow = result.scalar_one_or_none()

    if not child_flow:
        raise HTTPException(status_code=404, detail="Collection flow not found")

    # 2. Use Child Service Pattern for phase execution
    service = CollectionChildFlowService(db, context)
    phase_result = await service.execute_phase(
        phase,
        {"flow_id": str(child_flow.id)}
    )

    return {"success": True, "result": phase_result}
```

---

### Template 2: Idempotent Migration

```python
"""Add column to collection_flows."""
from alembic import op
import sqlalchemy as sa

revision = "XXX"
down_revision = "YYY"

def column_exists(table: str, column: str, schema: str = "migration") -> bool:
    bind = op.get_bind()
    result = bind.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = :schema
            AND table_name = :table
            AND column_name = :column
        )
    """), {"schema": schema, "table": table, "column": column}).scalar()
    return bool(result)

def upgrade():
    if not column_exists("collection_flows", "new_column"):
        op.add_column(
            "collection_flows",
            sa.Column("new_column", sa.Text(), nullable=True),
            schema="migration"
        )

def downgrade():
    if column_exists("collection_flows", "new_column"):
        op.drop_column("collection_flows", "new_column", schema="migration")
```

---

## Troubleshooting

### Issue: Flow stuck at 0% progress

**Symptoms**: Progress bar shows 0%, cannot continue

**Diagnosis**:
```sql
SELECT id, flow_id, status, current_phase, progress
FROM migration.collection_flows
WHERE id = 'your-flow-id';
```

**Common Causes**:
1. `current_phase` has invalid value (status instead of phase)
2. MFO registration missing
3. Phase handler threw exception

**Solution**: Check backend logs, verify phase name is valid, re-register with MFO if needed.

---

### Issue: Assessment validation fails despite complete data

**Symptoms**: "Assessment not ready" even with all fields populated

**Diagnosis**:
```sql
-- Check questionnaire responses
SELECT COUNT(*) FROM migration.collection_questionnaire_responses
WHERE collection_flow_id = 'your-flow-id';

-- Check asset fields
SELECT id, criticality, environment, custom_attributes
FROM migration.assets
WHERE id IN (SELECT asset_id FROM migration.collection_flow_applications WHERE flow_id = 'your-flow-id');
```

**Solution**: Implement dual-source validation (Pattern 6) - check both questionnaire AND asset fields.

---

### Issue: 404 when accessing completed flow for assessment

**Symptoms**: Just-completed flow returns 404

**Solution**: Ensure endpoint uses `include_completed=True` (Pattern 4).

---

## Related Documentation

| Resource | Location | Purpose |
|----------|----------|---------|
| ADR-012 | `/docs/adr/012-flow-status-phase-separation.md` | Status vs phase separation |
| ADR-025 | `/docs/adr/025-collection-flow-child-service-migration.md` | Child service pattern |
| MFO Pattern | `.serena/memories/mfo_two_table_flow_id_pattern_critical.md` | Two-table UUID resolution |
| API Guidelines | `/docs/guidelines/API_REQUEST_PATTERNS.md` | Request body vs query params |

---

## Consolidated Sources

This master memory consolidates the following original memories:

| Original Memory | Date | Key Contribution |
|-----------------|------|------------------|
| `collection_flow_child_service_migration_pattern_2025_10` | 2025-10 | Child Service Pattern |
| `collection-flow-questionnaire-lifecycle-state-machine-2025-11` | 2025-11 | State machine |
| `collection_flow_comprehensive_fixes_2025_09_30` | 2025-09 | FK fixes, ADR-012 |
| `collection-flow-mfo-registration-fix` | 2025-10 | Bridge pattern |
| `collection_gap_analysis_comprehensive_implementation_2025_24` | 2025-10 | Multi-tenant gaps |
| `collection-flow-id-resolver-fix` | 2025-11 | Dual UUID lookup |
| `adr-012-collection-flow-status-remediation` | 2025-10 | Status vs phase |
| `collection_flow_phase_status_fixes_2025_10` | 2025-10 | Phase/status confusion |
| `collection_flow_status_filter_exclusion_pattern_2025_11` | 2025-11 | Status filter pattern |
| `collection_assessment_transition_fixes` | 2025-01 | Transition bugs |
| `collection_questionnaire_generation_fix_complete_2025_30` | 2025-09 | Questionnaire fixes |
| `collection_flow_error_handling_cancelled_flows_2025_10` | 2025-10 | Error handling |
| `collection_flow_alternate_entry_fixes_2025_27` | 2025-10 | Alternate entry |
| `collection_flow_architecture_issues_2025_10` | 2025-10 | Architecture |
| `collection_flow_diagnostic_fixes_2025_09` | 2025-09 | Diagnostics |
| `collection_flow_fixes_2025_09` | 2025-09 | General fixes |
| `collection_flow_qodo_fixes_2025_10_01` | 2025-10 | Qodo review fixes |
| `collection_flow_resume_errors_fix_2025_23` | 2025-10 | Resume errors |
| `collection_gap_analysis_lean_refactor_2025_10` | 2025-10 | Lean refactor |
| `collection_gaps_phase2_implementation` | 2025-09 | Phase 2 impl |
| `collection_gaps_qodo_bot_fixes_2025_21` | 2025-10 | Qodo fixes |
| `collection_questionnaire_empty_sections_fix_2025_30` | 2025-09 | Empty sections |
| `collection_questionnaire_generation_fix` | 2025-09 | Generation fix |
| `collection_questionnaire_id_fixes_2025_29` | 2025-09 | ID fixes |
| `collection-assessment-transition-fk-fix` | 2025-10 | FK fix |
| `collection-flow-qa-bug-fix-workflow-682-692` | 2025-11 | QA workflow |

**Archive Location**: `.serena/archive/collection/`

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-30 | Initial consolidation of 35 memories | Claude Code |

---

## Search Keywords

collection, flow, gap_analysis, questionnaire, phase, status, mfo, child_service, assessment_transition, dual_uuid, tenant_scoping, adr-012, adr-025
