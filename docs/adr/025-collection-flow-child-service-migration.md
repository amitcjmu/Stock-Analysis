# ADR-025: Collection Flow Child Service Migration

## Status
Approved (2025-10-07)

## Context

The Collection Flow is currently in a **hybrid architectural state** where different components use incompatible execution patterns, causing E2E failures and architectural inconsistency.

### Current Problem: Hybrid Architecture

#### Root Cause Analysis

1. **Gap Analysis Migrated** (PR #506, #508):
   - Service-based architecture with persistent agents
   - Uses `TenantScopedAgentPool` for agent reuse
   - No crew instantiation

2. **State Management Migrated** (PR #518):
   - `CollectionFlowStateService` handles lifecycle
   - Replaces direct model manipulation
   - Service-based pattern

3. **Flow Execution NOT Migrated**:
   - Still uses `crew_class=UnifiedCollectionFlow`
   - `UnifiedCollectionFlow` imports deleted `GapAnalysisAgent` (removed in PR #506)
   - Import fails → `COLLECTION_FLOW_AVAILABLE = False` → `crew_class = None`
   - Resume/Continue operations fail: "No crew_class registered"

#### Current Inconsistent State

```python
# collection_flow_config.py - BROKEN
try:
    from app.services.crewai_flows.unified_collection_flow import UnifiedCollectionFlow
    COLLECTION_FLOW_AVAILABLE = True
except ImportError:  # Always fails - GapAnalysisAgent deleted
    COLLECTION_FLOW_AVAILABLE = False
    UnifiedCollectionFlow = None

crew_class=(UnifiedCollectionFlow if COLLECTION_FLOW_AVAILABLE else None),  # Always None
```

**Result**: Collection flows cannot resume/continue execution because:
- `crew_class = None` (import fails)
- No `child_flow_service` registered (missing piece)
- Master Flow Orchestrator has no execution handler

### Problems with Hybrid State

#### 1. **E2E Failures**
- Flow creation succeeds but execution fails
- Resume/Continue operations return "No execution handler"
- Phase transitions don't trigger agent execution
- Placeholder `GapAnalysisAgent` was added (commit 9516b6ed3) - **wrong fix**

#### 2. **Architectural Inconsistency**
- Gap Analysis: ✅ Persistent agents
- State Management: ✅ Service-based
- Flow Execution: ❌ crew_class (broken)
- Pattern mismatch with Discovery flow (uses `child_flow_service`)

#### 3. **Maintenance Burden**
- `UnifiedCollectionFlow` exists but cannot be imported
- Fallback logic masks the real problem
- Temporary fixes (placeholders) enable wrong patterns

## Decision

**Migrate Collection Flow to `child_flow_service` pattern immediately**, matching Discovery flow architecture and completing the migration started in PRs #506, #508, #518.

### Core Changes

1. **Create `CollectionChildFlowService`**
   - Single execution path via persistent agents
   - Routes phases to appropriate handlers
   - Manages auto-progression logic
   - Follows Discovery pattern exactly

2. **Delete Legacy Code**
   - Remove `UnifiedCollectionFlow` (no deprecation window)
   - Revert `GapAnalysisAgent` placeholder (commit 9516b6ed3)
   - Remove `crew_class` from flow config

3. **Update Master Flow Orchestrator**
   - Check `child_flow_service` ONLY (no crew_class fallback)
   - Fail fast if no handler registered
   - Single execution path

### Implementation Pattern

```python
# CollectionChildFlowService - Single Execution Path
class CollectionChildFlowService(BaseChildFlowService):
    async def execute_phase(self, flow_id: str, phase_name: str, phase_input: Dict) -> Dict:
        child_flow = await self.repository.get_by_master_flow_id(UUID(flow_id))

        if phase_name == "gap_analysis":
            gap_service = GapAnalysisService(self.db, self.context)
            result = await gap_service.execute_gap_analysis(
                collection_flow_id=child_flow.id,  # UUID PK
                phase_input=phase_input
            )
            # Auto-progression in service, not UI
            await self._transition_phase_based_on_result(result)
            return result

        # ... other phases
```

### Configuration Update

```python
# collection_flow_config.py - AFTER
from app.services.child_flow_services import CollectionChildFlowService

FlowConfig(
    flow_type="collection",
    child_flow_service=CollectionChildFlowService,  # NEW: Single path
    # crew_class removed entirely
)
```

## Consequences

### Positive

1. **Architectural Consistency**
   - Collection matches Discovery pattern
   - All flows use `child_flow_service`
   - Persistent agents throughout

2. **Simplified Maintenance**
   - Single execution path
   - No fallback logic
   - No deprecated code retention

3. **Proper E2E Functionality**
   - Resume/Continue works
   - Phase transitions execute
   - No placeholder workarounds

4. **ADR Compliance**
   - ✅ ADR-006: Master Flow Orchestrator integration
   - ✅ ADR-012: Status vs phase separation
   - ✅ ADR-015: Persistent multi-tenant agents
   - ✅ ADR-024: TenantMemoryManager (not CrewAI memory)

### Negative

1. **Breaking Change**
   - Any in-flight collection flows using old pattern will fail
   - Mitigation: Minimal - pattern was already broken

2. **No Backward Compatibility**
   - Delete legacy immediately (no deprecation window)
   - Justification: Old pattern doesn't work anyway

3. **Implementation Time**
   - ~1 hour for 3 phases
   - Risk: Low (following proven Discovery pattern)

## Implementation

### Phase 1: Create CollectionChildFlowService (20 min)
- File: `backend/app/services/child_flow_services/collection.py`
- Pattern: Match Discovery service exactly
- Update: `__init__.py` exports

### Phase 2: Delete Legacy & Update Config (20 min)
- Delete: `UnifiedCollectionFlow.py` immediately
- Revert: `GapAnalysisAgent` placeholder (commit 9516b6ed3)
- Update: `collection_flow_config.py` (crew_class → child_flow_service)

### Phase 3: Update MFO Resume Logic (20 min)
- File: `backend/app/services/master_flow_orchestrator/operations/lifecycle_commands.py`
- Change: Check `child_flow_service` ONLY (remove crew_class fallback)
- Fail fast: Raise error if no handler

### Testing (4 minimal tests)
1. E2E: Submit gaps → 202; progress increments; DB upserts; phase advances
2. Validation: >200 gaps → 400
3. Idempotency: Second submission while running → 409
4. Upsert: Rerun after completion → no duplicates

## Alignment with ADRs

### ADR-006: Master Flow Orchestrator
- ✅ All collection flows register with `crewai_flow_state_extensions`
- ✅ Single source of truth for workflow operations
- ✅ `child_flow_service` provides execution handler

### ADR-012: Flow Status Management Separation
- ✅ Master flow: lifecycle states (running, paused, completed)
- ✅ Child flow: operational decisions (phases, UI state)
- ✅ Service maintains separation

### ADR-015: Persistent Multi-Tenant Agent Architecture
- ✅ Uses `TenantScopedAgentPool`
- ✅ Agents maintained per (client_account_id, engagement_id)
- ✅ No per-execution agent instantiation

### ADR-024: TenantMemoryManager Architecture
- ✅ CrewAI memory disabled (`memory=False`)
- ✅ Uses `TenantMemoryManager` for learning
- ✅ PostgreSQL + pgvector backend

## Alternatives Considered

### Alternative 1: Fix UnifiedCollectionFlow
**Rejected**: Would maintain two execution paths (crew_class + child_flow_service), increasing complexity and maintenance burden.

### Alternative 2: Deprecation Window
**Rejected**: Old pattern doesn't work (import fails), so there's nothing to deprecate gracefully. Delete immediately.

### Alternative 3: Keep Both Patterns
**Rejected**: Violates single responsibility and creates confusion about which pattern to use for new flows.

## References

- **Migration Plan**: `docs/development/collection_flow/COLLECTION_FLOW_MIGRATION_PLAN_SIMPLIFIED.md`
- **PR #506**: Lean Gap Analysis refactor (removed crews)
- **PR #508**: Two-Phase Gap Analysis (persistent agents)
- **PR #518**: Collection Flow Status Remediation (state service)
- **Discovery Pattern**: `backend/app/services/child_flow_services/discovery.py`
- **ADR-015**: Persistent Multi-Tenant Agent Architecture
- **ADR-024**: TenantMemoryManager Architecture

## Decision Date
2025-10-07

## Supersedes
- N/A (completes migration started in PRs #506, #508, #518)

## Superseded By
- N/A (active)

## Notes

### Critical ID Mapping
- `collection_flows.id` = UUID (Primary Key) - use for ALL FKs and persistence
- `collection_flows.flow_id` = UUID (Business ID) - use ONLY for MFO orchestrator calls

### Complexity Removed
- ❌ No deprecation shims/windows
- ❌ No feature flags
- ❌ No dual execution paths (crew_class + child_flow_service)
- ❌ No SSE/WebSockets for progress
- ❌ No per-asset concurrency
- ❌ No passing RequestContext to background tasks

### Pattern Principles
- **Simplicity**: Single execution path only
- **Explicitness**: Tenant scoping in every repository call
- **Fail-fast**: Error immediately if no execution handler
- **Sequential**: No parallel processing complexity
- **Minimal**: 4 tests cover critical paths

---

**Status**: Ready for implementation. All prerequisites complete. GPT5 reviewed and approved.
