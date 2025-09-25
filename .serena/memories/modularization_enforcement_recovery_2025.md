# Modularization Enforcement & Recovery - September 2025

## Critical Insight: Pre-commit Modularization is Mandatory

**Problem**: Modularization commits made locally to pass pre-commit hooks can be lost when not pushed with PRs
**Root Cause**: Git's "not fully merged" warning indicates local commits not in the merged branch

### Recovery Process for Lost Modularization Commits

```bash
# 1. Check reflog for lost commit
git reflog -10

# 2. Cherry-pick the modularization commit
git cherry-pick <commit-hash>

# 3. Verify modularization is complete
ls backend/app/api/v1/endpoints/collection_crud_queries/
ls backend/app/api/v1/endpoints/collection_serializers/

# 4. Confirm original files deleted
ls -la *.py 2>&1 | grep "No such file"
```

## File Modularization Pattern (400-line limit)

### Structure for collection_crud_queries.py (529 lines → 3 modules)
```python
collection_crud_queries/
├── __init__.py       # Backward compatibility exports
├── status.py         # 126 lines - Basic operations
├── analysis.py       # 329 lines - Gap analysis
└── lists.py          # 106 lines - Bulk retrieval
```

### Backward Compatibility in __init__.py
```python
# Import all public functions
from .status import get_collection_status
from .analysis import get_gap_analysis, get_readiness
from .lists import list_collection_flows

# Export for backward compatibility
__all__ = [
    "get_collection_status",
    "get_gap_analysis",
    "get_readiness",
    "list_collection_flows",
]
```

## Enum Migration Safety Pattern

**Problem**: PostgreSQL enum changes can fail if old values exist
**Solution**: Remap values BEFORE changing enum type

```sql
-- CRITICAL: Remap old values first
ALTER TABLE migration.collection_flows
ALTER COLUMN status TYPE text;

UPDATE migration.collection_flows
SET status = 'asset_selection'
WHERE status IN ('platform_detection', 'automated_collection');

-- Then create new enum
CREATE TYPE collectionflowstatus_new AS ENUM (...);
```

## Target Gaps Extraction with Fallback

**Problem**: Missing target_gaps attribute causes API failures
**Solution**: Graceful fallback with logging

```python
# Handle backward compatibility
target_gaps = []
if hasattr(questionnaire, "target_gaps") and questionnaire.target_gaps is not None:
    target_gaps = questionnaire.target_gaps
else:
    logger.debug(f"Questionnaire {questionnaire.id} missing target_gaps, extracting from questions")
    seen_gaps = set()
    for question in (questionnaire.questions or []):
        if isinstance(question, dict):
            question_gaps = question.get("target_gaps", [])
            for gap in question_gaps:
                if gap not in seen_gaps:
                    target_gaps.append(gap)
                    seen_gaps.add(gap)
```

## Key Lesson: Always Push Modularization

**Never** commit without modularization when pre-commit enforces file length limits
**Always** include modularization commits in PRs to prevent loss
**Verify** with `pre-commit run --all-files` before pushing
