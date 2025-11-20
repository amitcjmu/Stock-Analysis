# MFO Two-Table Pattern: Master vs Child Flow IDs - CRITICAL REFERENCE

**Last Updated**: January 2025
**Severity**: CRITICAL - Recurring bug pattern across multiple features
**Issue Tags**: #962, #999, dependency-analysis

## THE PROBLEM: Why This Confusion Keeps Happening

The **Master Flow Orchestrator (MFO)** uses a two-table pattern (ADR-006, ADR-012) that creates **two different UUIDs** for every flow:

1. **Master Flow ID**: Internal MFO routing (stored in `crewai_flow_state_extensions.flow_id`)
2. **Child Flow ID**: User-facing identifier (stored in `{flow_type}_flows.id`)

**The term "flow_id" is OVERLOADED** - it means different things in different contexts, leading to recurring bugs.

---

## THE PATTERN (MANDATORY FOR ALL FLOW TYPES)

### Two-Table Architecture

```python
# Master Table (MFO lifecycle management)
crewai_flow_state_extensions:
  - flow_id (PK, UUID)          # ← MASTER FLOW ID
  - flow_type (discovery/assessment/collection)
  - flow_status (running/paused/completed)

# Child Table (Operational state - per flow type)
assessment_flows:  # or discovery_flows, collection_flows
  - id (PK, UUID)               # ← CHILD FLOW ID (same value as master flow_id)
  - master_flow_id (FK)         # ← References crewai_flow_state_extensions.flow_id
  - status (initialized/running/completed)
  - current_phase
  - phase_results (JSONB)
```

**Key Insight**: `AssessmentFlow.id == MasterFlow.flow_id` (same UUID value), but different column names!

---

## COMMON MISTAKE PATTERNS

### ❌ WRONG Pattern (Causes Silent Failures)

```python
# Example: Execute endpoint receiving child flow ID in URL
@router.post("/execute/{flow_id}")
async def execute_something(flow_id: str, db: AsyncSession):
    orchestrator = MasterFlowOrchestrator(db, context)

    # ❌ BUG: Passing child ID to MFO (expects master ID!)
    result = await orchestrator.execute_phase(
        flow_id,  # ← This is child ID from URL
        "some_phase",
        {"flow_id": flow_id}
    )
    # MFO will query: SELECT * FROM crewai_flow_state_extensions WHERE flow_id = child_uuid
    # Result: No master flow found OR wrong master flow → execution fails
```

**Why This Happens**:
- URL receives child ID (user-facing: `/execute/abc-123`)
- MFO expects master ID (internal routing)
- No type system to catch the mistake
- No runtime validation to fail early

---

## ✅ CORRECT Pattern (MANDATORY TEMPLATE)

```python
# Example: Execute endpoint receiving child flow ID in URL
@router.post("/execute/{flow_id}")
async def execute_something(
    flow_id: str,  # ← Child flow ID from URL
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
):
    """
    CRITICAL PATTERN: Always resolve master_flow_id before calling MFO.

    flow_id in URL path = child flow ID (AssessmentFlow.id)
    MFO.execute_phase() = expects master flow ID
    phase_input["flow_id"] = child flow ID (for persistence)
    """
    from uuid import UUID

    # Step 1: Query child flow table using child ID
    stmt = select(AssessmentFlow).where(
        and_(
            AssessmentFlow.id == UUID(flow_id),  # ← Query by child ID
            AssessmentFlow.client_account_id == context.client_account_id,
            AssessmentFlow.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    child_flow = result.scalar_one_or_none()

    if not child_flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    if not child_flow.master_flow_id:
        raise HTTPException(status_code=400, detail="Flow not registered with MFO")

    # Step 2: Extract master flow ID from child row
    master_flow_id = child_flow.master_flow_id

    # Step 3: Call MFO with MASTER ID, pass CHILD ID in phase_input
    orchestrator = MasterFlowOrchestrator(db, context)
    result = await orchestrator.execute_phase(
        str(master_flow_id),  # ← MASTER flow ID (MFO routing)
        "some_phase",
        {
            "flow_id": flow_id,  # ← CHILD flow ID (persistence)
            "other_data": "..."
        }
    )

    return {
        "success": True,
        "flow_id": flow_id,  # Return child ID (user expects this)
        "master_flow_id": str(master_flow_id),  # For debugging
        "result": result
    }
```

---

## THE GOLDEN RULES

### Rule 1: URL Paths Always Use Child Flow IDs
```python
# ✅ User-facing URLs use child ID
GET  /api/v1/assessment-flow/{flow_id}/status
POST /api/v1/assessment-flow/{flow_id}/execute
PUT  /api/v1/assessment-flow/{flow_id}/update

# The {flow_id} parameter = child flow ID (AssessmentFlow.id)
```

### Rule 2: MFO Methods Always Expect Master Flow IDs
```python
# ✅ MFO operates on master flows
orchestrator.create_flow()         # Returns master_flow_id
orchestrator.execute_phase(master_flow_id, ...)
orchestrator.pause_flow(master_flow_id)
orchestrator.resume_flow(master_flow_id)
```

### Rule 3: Persistence Uses Child Flow IDs
```python
# ✅ Save results to child table using child ID
stmt = update(AssessmentFlow).where(
    AssessmentFlow.id == UUID(child_flow_id)  # From phase_input
).values(
    phase_results = {...}
)
```

### Rule 4: Always Resolve Master ID from Child ID Before MFO Calls
```python
# ✅ MANDATORY PATTERN
child_flow = await db.execute(
    select(AssessmentFlow).where(AssessmentFlow.id == UUID(flow_id))
).scalar_one_or_none()

master_flow_id = child_flow.master_flow_id  # Extract FK

await orchestrator.execute_phase(
    str(master_flow_id),  # Master ID
    "phase_name",
    {"flow_id": flow_id}  # Child ID in context
)
```

---

## VALIDATION CHECKLIST

Before implementing ANY endpoint that calls MFO, ask:

- [ ] Does the URL receive child flow ID or master flow ID? (Usually child)
- [ ] Am I querying the correct table? (`AssessmentFlow.id`, not `flow_id`)
- [ ] Did I extract `master_flow_id` from the child row?
- [ ] Am I passing `master_flow_id` to MFO methods?
- [ ] Am I including child `flow_id` in `phase_input` for persistence?
- [ ] Did I return the child `flow_id` to the user (not master)?

---

## WHERE TO FIND EXAMPLES IN CODEBASE

### Existing Implementations (Copy These!)

1. **Assessment Flow Creation**:
   - `backend/app/api/v1/endpoints/assessment_flow/mfo_integration/create.py`
   - Shows master + child creation in single transaction

2. **Collection Flow Management**:
   - `backend/app/api/v1/endpoints/collection_flow/lifecycle.py`
   - Shows master ID resolution pattern

3. **Discovery Flow Execution**:
   - `backend/app/services/master_flow_orchestrator.py`
   - Shows how MFO uses master IDs internally

### Search Commands

```bash
# Find examples of master_flow_id extraction
grep -r "master_flow_id" backend/app/api/v1/endpoints/ --include="*.py" -A 5 -B 5

# Find MFO execute_phase calls
grep -r "execute_phase" backend/app/api/v1/endpoints/ --include="*.py" -A 10
```

---

## WHY THIS PATTERN EXISTS (ADR References)

### ADR-006: Master Flow Orchestrator
- **Purpose**: Single source of truth for ALL workflow operations
- **Design**: Two-table pattern separates lifecycle (master) from operational state (child)
- **Rationale**: Enables cross-flow coordination, pause/resume, and atomic state management

### ADR-012: Flow Status Management Separation
- **Master Table**: High-level lifecycle (`running`, `paused`, `completed`)
- **Child Table**: Operational decisions (phases, validations, UI state)
- **Rationale**: Frontend uses child status for decisions, MFO uses master for routing

### Why Two IDs?
1. **User Facing**: Child ID is stable across pause/resume, user-friendly
2. **Internal**: Master ID enables MFO to manage flow lifecycle independently
3. **Persistence**: Child table stores domain-specific data (phase_results, etc.)
4. **Flexibility**: Can change child table schema without affecting MFO core

---

## DEBUGGING TIPS

### Symptom 1: "Flow not found" errors
**Cause**: Passing child ID to MFO (it's querying master table with child UUID)
**Fix**: Extract `master_flow_id` before calling MFO

### Symptom 2: Phase results not persisting
**Cause**: `phase_input` missing child `flow_id`
**Fix**: Include `{"flow_id": child_flow_id}` in phase_input

### Symptom 3: Wrong flow gets executed
**Cause**: UUID collision (child ID matches different master ID)
**Fix**: Always validate `master_flow_id` is not None before using

### Symptom 4: AttributeError on AssessmentFlow.flow_id
**Cause**: Querying non-existent column (ORM uses `.id`, not `.flow_id`)
**Fix**: Use `AssessmentFlow.id` for primary key queries

---

## FUTURE IMPROVEMENTS (Proposed)

### 1. Type Safety (Python 3.10+)
```python
from typing import NewType

MasterFlowID = NewType('MasterFlowID', UUID)
ChildFlowID = NewType('ChildFlowID', UUID)

def execute_phase(
    master_flow_id: MasterFlowID,  # Type system enforces correctness!
    phase_name: str,
    phase_input: dict
) -> dict:
    ...
```

### 2. Runtime Validation Helper
```python
# backend/app/core/mfo/flow_id_resolver.py

async def resolve_master_flow_id(
    child_flow_id: str,
    flow_type: str,  # "assessment", "discovery", "collection"
    db: AsyncSession,
    context: RequestContext
) -> UUID:
    """
    Resolve master flow ID from child flow ID.
    Raises HTTPException if not found or invalid.
    """
    model_map = {
        "assessment": AssessmentFlow,
        "discovery": DiscoveryFlow,
        "collection": CollectionFlow,
    }

    model = model_map.get(flow_type)
    if not model:
        raise ValueError(f"Unknown flow type: {flow_type}")

    stmt = select(model).where(
        and_(
            model.id == UUID(child_flow_id),
            model.client_account_id == context.client_account_id,
            model.engagement_id == context.engagement_id,
        )
    )
    result = await db.execute(stmt)
    child_flow = result.scalar_one_or_none()

    if not child_flow:
        raise HTTPException(status_code=404, detail=f"{flow_type.title()} flow not found")

    if not child_flow.master_flow_id:
        raise HTTPException(status_code=400, detail="Flow not registered with MFO")

    return child_flow.master_flow_id
```

**Usage**:
```python
@router.post("/execute/{flow_id}")
async def execute_something(flow_id: str, db: AsyncSession, context: RequestContext):
    # One-liner resolution with validation!
    master_flow_id = await resolve_master_flow_id(flow_id, "assessment", db, context)

    await orchestrator.execute_phase(
        str(master_flow_id),
        "phase_name",
        {"flow_id": flow_id}
    )
```

### 3. Code Templates Directory
```
docs/code-templates/
  ├── mfo-execute-phase-pattern.py
  ├── mfo-create-flow-pattern.py
  └── mfo-query-flow-pattern.py
```

---

## ENFORCEMENT

### Pre-Commit Hook (Proposed)
```python
# Detect MFO calls without master_flow_id resolution
if re.search(r'execute_phase\(\s*flow_id', code):
    raise PreCommitError(
        "CRITICAL: MFO execute_phase() receives flow_id directly. "
        "Must resolve master_flow_id first. "
        "See: docs/memories/mfo_two_table_flow_id_pattern_critical.md"
    )
```

### Code Review Checklist
- [ ] All MFO calls use master flow ID
- [ ] Child flow ID extracted from URL/request
- [ ] `master_flow_id` resolved from child table
- [ ] `phase_input` includes child `flow_id`
- [ ] Response returns child `flow_id` to user

---

## SUMMARY

**ALWAYS remember**:
- **URLs use child IDs** (user-facing)
- **MFO uses master IDs** (internal routing)
- **Persistence uses child IDs** (from phase_input)
- **ALWAYS resolve master_flow_id before calling MFO**

**When in doubt**: Copy an existing endpoint pattern verbatim, then modify.

**Golden Reference Files**:
1. `backend/app/api/v1/endpoints/assessment_flow/mfo_integration/create.py`
2. `backend/app/api/v1/endpoints/collection_flow/lifecycle.py`
3. This memory document!
