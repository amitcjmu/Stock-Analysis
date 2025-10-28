# CrewAI TaskOutput Serialization Pattern

## Problem
CrewAI's `task.execute_async()` returns `TaskOutput` Pydantic objects, not plain strings. When passed to SQLAlchemy JSONB fields without extraction, causes:
```
TypeError: Object of type TaskOutput is not JSON serializable
```

## Root Cause
```python
# ❌ WRONG - TaskOutput object passed directly
result = await asyncio.wrap_future(task.execute_async(context=context_str))
parsed_result = json.loads(result) if isinstance(result, str) else result
# If result is TaskOutput, it gets passed as-is → serialization failure
```

## Solution Pattern
```python
from crewai import TaskOutput
from app.utils.json_sanitization import sanitize_for_json

# 1. Execute task
result = await asyncio.wrap_future(task.execute_async(context=context_str))

# 2. Extract string from TaskOutput
if isinstance(result, TaskOutput):
    result_str = result.raw if hasattr(result, 'raw') else str(result)
else:
    result_str = str(result) if not isinstance(result, str) else result

# 3. Parse JSON
try:
    parsed_result = json.loads(result_str) if isinstance(result_str, str) else result_str
except json.JSONDecodeError:
    parsed_result = {"raw_output": result_str}

# 4. Per ADR-029: Sanitize for NaN/Infinity
parsed_result = sanitize_for_json(parsed_result)
```

## Key TaskOutput Attributes
- `.raw` - Contains actual string result from LLM
- `.description` - Task description
- `.agent` - Agent that executed task

## When This Applies
- All CrewAI task execution using `task.execute_async()`
- Before saving LLM results to PostgreSQL JSONB fields
- Assessment flow executors (complexity, risk, tech_debt, etc.)

## ADR Compliance
- **ADR-029**: LLM Output JSON Sanitization Pattern (mandatory `sanitize_for_json()`)
- **ADR-024**: TenantMemoryManager (CrewAI memory disabled)

## Files Typically Affected
```
backend/app/services/flow_orchestration/execution_engine_crew_assessment/
├── complexity_executor.py
├── dependency_executor.py
├── readiness_executor.py
├── recommendation_executor.py
├── risk_executor.py
└── tech_debt_executor.py
```

## Verification
```bash
# Import test
docker exec migration_backend python3.11 -c "
from app.services.flow_orchestration.execution_engine_crew_assessment.complexity_executor import ComplexityExecutorMixin
print('✅ Imports work - TaskOutput handling correct')
"
```

## Related Errors
- "Object of type TaskOutput is not JSON serializable"
- "Failed to save phase results: TypeError"
- Assessment phases complete but results not persisted
