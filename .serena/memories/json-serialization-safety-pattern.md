# JSON Serialization Safety Pattern for LLM-Generated Data

## Context
When LLM models generate numeric data (confidence scores, probabilities, etc.), they may produce `NaN` (Not a Number) or `Infinity` values that cannot be serialized to JSON by FastAPI/Pydantic.

## Problem Pattern
```python
# LLM generates data with problematic values
llm_response = {
    "confidence": float('nan'),  # ❌ Cannot serialize to JSON
    "score": float('inf'),       # ❌ Cannot serialize to JSON
}

# API endpoint tries to return this
return Response(**llm_response)  # RuntimeError: Unable to serialize Unknown to JSON
```

## Solution Pattern
Create a `sanitize_for_json()` utility function that recursively cleans data structures:

```python
import math
from typing import Any

def sanitize_for_json(data: Any) -> Any:
    """Recursively sanitize data for JSON serialization.

    Handles:
    - NaN → null
    - Infinity → null
    - datetime → ISO string
    - Non-serializable objects → string representation
    """
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif hasattr(data, 'isoformat'):  # datetime objects
        return data.isoformat()
    elif isinstance(data, (str, int, bool, type(None))):
        return data
    else:
        # Fallback: convert to string
        return str(data)
```

## Usage Pattern
Apply sanitization BEFORE Pydantic validation:

```python
from app.api.v1.endpoints.collection_serializers.core import sanitize_for_json

def build_response(llm_data):
    return ResponseModel(
        questions=sanitize_for_json(llm_data.questions),  # ✅ Safe
        scores=sanitize_for_json(llm_data.scores),        # ✅ Safe
    )
```

## When to Apply
✅ **Always sanitize LLM-generated data before API responses**
- Questionnaires with confidence scores
- Analysis results with probability scores
- Recommendations with ranking scores
- Any numeric data from AI models

## Where Implemented
- **File**: `backend/app/api/v1/endpoints/collection_serializers/core.py`
- **Function**: `sanitize_for_json()` (lines 232-265)
- **Applied**: `build_questionnaire_response()` (line 343)
- **Tests**: `tests/backend/unit/test_collection_serializers.py` (14 test cases)

## Issue Reference
- **Issue**: #682 - Questionnaire generation produces empty questionnaire
- **Root Cause**: LLM-generated confidence scores contained NaN/Infinity
- **Fix Commit**: 6bf50aede
- **Date Fixed**: 2025-10-22

## Key Lessons
1. **Never trust LLM numeric output** - Always sanitize before JSON serialization
2. **Defensive coding** - Handle edge cases at API boundaries
3. **Test comprehensively** - Cover NaN, Infinity, nested structures, edge cases
4. **Document patterns** - Make reusable utilities for common issues

## Reuse Checklist
When adding new LLM-powered features:
- [ ] Import `sanitize_for_json()` utility
- [ ] Apply to all numeric fields from LLM responses
- [ ] Add unit tests for NaN/Infinity handling
- [ ] Verify no RuntimeError in logs after deployment
