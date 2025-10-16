# SQLAlchemy UUID-to-String Join Casting

**Problem**: Joining UUID column to integer ID using `str()` causes incorrect SQL generation and type mismatches.

**Incorrect Pattern** ❌
```python
from sqlalchemy import select
from app.models import User, CrewAIFlowStateExtensions

stmt = (
    select(AssessmentFlow, User)
    .outerjoin(
        CrewAIFlowStateExtensions,
        AssessmentFlow.id == CrewAIFlowStateExtensions.flow_id,
    )
    .outerjoin(
        User,
        CrewAIFlowStateExtensions.user_id == str(User.id),  # ❌ Wrong!
    )
)
```

**Error**: Python `str()` converts at runtime but doesn't cast in SQL, causing type mismatch.

**Correct Pattern** ✅
```python
from sqlalchemy import select, cast, String

stmt = (
    select(AssessmentFlow, User)
    .outerjoin(
        CrewAIFlowStateExtensions,
        AssessmentFlow.id == CrewAIFlowStateExtensions.flow_id,
    )
    .outerjoin(
        User,
        CrewAIFlowStateExtensions.user_id == cast(User.id, String),  # ✅ Correct!
    )
)
```

**Generated SQL**:
```sql
-- With cast()
LEFT OUTER JOIN users ON crewai_flow_state_extensions.user_id = CAST(users.id AS VARCHAR)

-- With str() - type mismatch
LEFT OUTER JOIN users ON crewai_flow_state_extensions.user_id = users.id  -- Fails!
```

## When to Use

- Joining UUID/String columns to Integer IDs
- Cross-type comparisons in WHERE clauses
- Any SQLAlchemy expression needing type conversion

## Why This Matters

- Ensures correct SQL type casting
- Prevents join failures in production
- Database-side conversion (not Python-side)

**Fixed in**: PR #587 (Qodo Bot suggestion #2)
**File**: `backend/app/api/v1/master_flows/master_flows_assessment.py:80`
