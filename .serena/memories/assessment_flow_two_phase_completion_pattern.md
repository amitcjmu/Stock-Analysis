# Assessment Flow Status Management - Two-Phase Completion Pattern

## Problem
Flow was prematurely marked as "completed" after agent execution finished, preventing user review/confirmation step. Users expect to review AI-generated recommendations before finalizing.

## Solution
Implement two-phase completion:
1. **Phase 1**: Agents complete → status stays `in_progress` → results ready for review
2. **Phase 2**: User confirms → status becomes `completed` → flow finalized

## Implementation

```python
# backend/app/api/v1/endpoints/assessment_flow_processors/continuation.py

# Keep flow in_progress until user clicks "Finalize Assessment" button
# Final phase (recommendation_generation) completes agent work,
# but flow status stays in_progress awaiting user confirmation
await assessment_repo.update_flow_status(
    flow_id,
    "in_progress",  # NOT "completed" - await user confirmation
)

if phase.value == "recommendation_generation":
    logger.info(
        "[ISSUE-999] 📋 Assessment flow {flow_id} recommendations ready "
        "- awaiting user finalization"
    )
```

## Workflow Pattern

```
Agent Execution → phase_results updated → status: in_progress
         ↓
User Reviews Data
         ↓
User Clicks Finalize → apps_ready_for_planning populated → status: completed
```

## When to Use
- Any workflow requiring user confirmation before completion
- AI-generated results that need human review
- Multi-step processes where users need to verify before proceeding
- Flows that transition to other workflows (e.g., Assessment → Planning)

## Anti-Pattern
❌ Auto-completing flows on agent finish without user review/confirmation step
❌ Marking flow as "completed" when agent tasks finish but user hasn't confirmed

## Related Files
- `backend/app/api/v1/endpoints/assessment_flow_processors/continuation.py`
- `backend/app/api/v1/master_flows/assessment/lifecycle_endpoints/flow_lifecycle.py` (finalize endpoint)
