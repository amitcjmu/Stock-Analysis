# Collection Flow Questionnaire Lifecycle State Machine

## Overview

Documents the complete lifecycle of questionnaires in Collection Flow, including state transitions and when asset readiness gets updated.

## Questionnaire State Machine

```
                    ┌─────────────────────────────────────────┐
                    │         QUESTIONNAIRE GENERATION        │
                    └─────────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
            ┌───────────┐      ┌───────────┐      ┌───────────┐
            │  pending  │      │   ready   │      │  failed   │
            │(generating)│      │(has Qs)   │      │           │
            └───────────┘      └───────────┘      └─────┬─────┘
                    │                  │                │
                    │                  │         ┌──────┴──────┐
                    │                  │         │             │
                    │                  │         ▼             ▼
                    │                  │   ┌─────────┐  ┌──────────┐
                    │                  │   │ No TRUE │  │  Actual  │
                    │                  │   │  gaps   │  │  Error   │
                    │                  │   └────┬────┘  └──────────┘
                    │                  │        │
                    │                  │        │ Asset READY
                    │                  │        │ (complete data)
                    │                  ▼        │
                    │           ┌───────────┐   │
                    └──────────►│in_progress│◄──┘
                                │(user doing)│
                                └─────┬─────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                         ▼            ▼            ▼
                  ┌───────────┐ ┌───────────┐ ┌───────────┐
                  │save_progress│submit_complete│  cancel  │
                  │(stay here)│ │(→completed)│ │(→cancelled)│
                  └───────────┘ └─────┬─────┘ └───────────┘
                                      │
                                      ▼
                               ┌───────────┐
                               │ completed │
                               │           │
                               └─────┬─────┘
                                     │
                                     ▼
                              Asset READY
                         (assessment_readiness='ready')
```

## State Definitions

| State | `completion_status` | Meaning | Asset Readiness Action |
|-------|---------------------|---------|------------------------|
| Generating | `pending` | Background task running | None |
| Ready | `ready` | Questions generated, awaiting user | None |
| In Progress | `in_progress` | User has started answering | None |
| Completed | `completed` | User submitted all answers | Set `ready` |
| Failed (no gaps) | `failed` + special description | No TRUE gaps found | Set `ready` |
| Failed (error) | `failed` + error description | Actual failure | None |
| Cancelled | `cancelled` | User cancelled flow | None |

## State Transitions

### Generation Phase (Background Task)

```python
# background_task.py
questionnaire.completion_status = "pending"  # Initial

# After IntelligentGapScanner runs:
if len(true_gaps) == 0:
    questionnaire.completion_status = "failed"
    questionnaire.description = "No questionnaires could be generated - no TRUE gaps found"
    # CRITICAL: Mark asset ready here!
    asset.assessment_readiness = "ready"
else:
    questionnaire.completion_status = "ready"
    questionnaire.questions = generated_questions
```

### User Interaction Phase

```python
# questionnaire_submission.py
if request_data.save_type == "save_progress":
    questionnaire.completion_status = "in_progress"
    # No readiness update

elif request_data.save_type == "submit_complete":
    questionnaire.completion_status = "completed"
    questionnaire.completed_at = datetime.utcnow()
    # Trigger readiness update
    await _update_asset_readiness(...)
```

## Critical: "No TRUE Gaps" Handling

When IntelligentGapScanner finds no gaps, the questionnaire "fails" but this is GOOD:

```python
# Detection patterns in description field
"No questionnaires could be generated"
"no TRUE gaps"
"generation failed"  # with 0 questions

# These ALL mean: Asset has complete data → Mark READY
```

## Frontend save_type Values

| Value | Trigger | Backend Action |
|-------|---------|----------------|
| `save_progress` | "Save Progress" button | Keep `in_progress`, no readiness update |
| `submit_complete` | "Submit" button | Set `completed`, update asset readiness |

## Database Schema

```sql
-- Questionnaire table
CREATE TABLE migration.adaptive_questionnaires (
    id UUID PRIMARY KEY,
    collection_flow_id INTEGER REFERENCES collection_flows(id),
    asset_id UUID REFERENCES assets(id),
    completion_status VARCHAR(50),  -- pending, ready, in_progress, completed, failed
    description TEXT,  -- Contains error messages or "No questionnaires..."
    questions JSONB,
    responses_collected JSONB,
    completed_at TIMESTAMP
);

-- Asset readiness fields
ALTER TABLE migration.assets ADD COLUMN assessment_readiness VARCHAR(50);
ALTER TABLE migration.assets ADD COLUMN sixr_ready VARCHAR(50);
```

## Debugging Stuck States

### Asset stuck in "not_ready" after questionnaire completed

```sql
-- Check questionnaire status
SELECT id, completion_status, description, completed_at
FROM migration.adaptive_questionnaires
WHERE asset_id = '<asset-uuid>';

-- If completed but asset not ready, the commit likely failed
-- Solution: Use "Refresh Readiness" button to force reconciliation
```

### Questionnaire stuck in "pending"

```sql
-- Check if background task completed
SELECT * FROM migration.adaptive_questionnaires
WHERE completion_status = 'pending'
AND created_at < NOW() - INTERVAL '5 minutes';

-- May need to manually trigger regeneration
```

### Multiple questionnaires for same asset

```sql
-- This is normal! Each section gets its own questionnaire (ADR-037)
SELECT id, section_id, completion_status
FROM migration.adaptive_questionnaires
WHERE asset_id = '<asset-uuid>'
ORDER BY created_at;

-- Asset is ready when ALL section questionnaires are completed
```

## Key Insight: Per-Section Generation (ADR-037)

As of November 2025, questionnaires are generated PER-SECTION, not per-asset:
- Asset may have 5-7 questionnaires (one per section with gaps)
- Asset is ready when ALL questionnaires are completed
- `_check_all_questionnaires_completed()` in `assessment_validation.py` handles this
