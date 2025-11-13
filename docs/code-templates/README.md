# Code Templates - MFO Pattern Reference

This directory contains **copy-paste templates** for common MFO operations to prevent recurring bugs.

## Why These Templates Exist

The MFO two-table pattern (ADR-006, ADR-012) causes **recurring confusion** between:
- **Master Flow ID**: Internal MFO routing
- **Child Flow ID**: User-facing identifier

**Historical Issues**: #962, #999, dependency-analysis-integration

Without templates, developers repeatedly make the same mistakes:
1. Passing child ID to `MFO.execute_phase()` → "Flow not found"
2. Querying `AssessmentFlow.flow_id` → AttributeError
3. Missing `flow_id` in `phase_input` → Results don't persist

## Available Templates

### 1. `mfo-execute-phase-pattern.py`

**Use when**: Creating ANY endpoint that executes MFO phases

**Prevents**:
- Master vs child flow ID confusion
- Missing persistence context
- Incorrect query patterns

**Copy this for**:
- Assessment flow phase execution
- Discovery flow phase execution
- Collection flow phase execution
- Any custom flow types

**Example usage**:
```bash
# Copy template and customize
cp docs/code-templates/mfo-execute-phase-pattern.py \
   backend/app/api/v1/endpoints/assessment_flow/dependency_endpoints.py

# Replace placeholders:
# - {FlowType} → AssessmentFlow
# - {phase_name} → dependency_analysis
# - {flow_type_str} → assessment
```

## Quick Reference: The Golden Rules

```python
# ✅ CORRECT PATTERN (always follow this)
@router.post("/execute/{flow_id}")  # URL receives CHILD ID
async def execute_something(flow_id: str, db, context):
    # 1. Query child table with child ID
    child_flow = await db.execute(
        select(AssessmentFlow).where(AssessmentFlow.id == UUID(flow_id))
    ).scalar_one_or_none()

    # 2. Extract master ID from child row
    master_flow_id = child_flow.master_flow_id

    # 3. Call MFO with master ID, pass child ID in phase_input
    await orchestrator.execute_phase(
        str(master_flow_id),  # ← MASTER
        "phase_name",
        {"flow_id": flow_id}  # ← CHILD
    )

    # 4. Return child ID to user
    return {"flow_id": flow_id}
```

## Additional Resources

- **Serena Memory**: `mfo_two_table_flow_id_pattern_critical` - Full documentation
- **CLAUDE.md**: Critical Architecture Patterns section
- **Example Files**:
  - `backend/app/api/v1/endpoints/assessment_flow/mfo_integration/create.py`
  - `backend/app/api/v1/endpoints/collection_flow/lifecycle.py`

## Validation Checklist

Before submitting PR with MFO code, verify:

- [ ] URL path receives child flow ID
- [ ] Query uses `{FlowType}.id` (not `.flow_id`)
- [ ] Extracted `master_flow_id` from child row
- [ ] Passed `master_flow_id` to MFO methods
- [ ] Included child `flow_id` in `phase_input`
- [ ] Returned child `flow_id` to user
- [ ] Used `get_current_context_dependency`
- [ ] Added proper error handling

## Future Improvements

### Proposed: Runtime Helper Function

```python
# app/core/mfo/flow_id_resolver.py (to be created)

async def resolve_master_flow_id(
    child_flow_id: str,
    flow_type: str,  # "assessment", "discovery", "collection"
    db: AsyncSession,
    context: RequestContext
) -> UUID:
    """
    Resolve master flow ID from child flow ID.
    One-liner replacement for Steps 1-2 of the pattern.
    """
    # Implementation in Serena memory
```

**Usage**:
```python
@router.post("/execute/{flow_id}")
async def execute_something(flow_id: str, db, context):
    # One-liner!
    master_flow_id = await resolve_master_flow_id(flow_id, "assessment", db, context)

    await orchestrator.execute_phase(
        str(master_flow_id),
        "phase_name",
        {"flow_id": flow_id}
    )
```

### Proposed: Type Safety with NewType

```python
from typing import NewType

MasterFlowID = NewType('MasterFlowID', UUID)
ChildFlowID = NewType('ChildFlowID', UUID)

def execute_phase(
    master_flow_id: MasterFlowID,  # Type checker enforces!
    phase_name: str,
    phase_input: dict
) -> dict:
    ...
```

## When in Doubt

1. **Read** the template comments carefully
2. **Copy** an existing endpoint verbatim
3. **Search** for `master_flow_id` in similar files
4. **Ask** in PR review if pattern is unclear

**Golden rule**: It's better to copy-paste working code than to reinvent and introduce bugs!
