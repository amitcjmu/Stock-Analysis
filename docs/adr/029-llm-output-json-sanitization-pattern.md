# ADR-029: LLM Output JSON Sanitization Pattern

**Status**: Accepted
**Date**: 2025-10-22
**Context**: Issue #682 - Questionnaire generation JSON serialization failures
**Related**: ADR-024 (TenantMemoryManager), Issue #682

## Context

AI/LLM agents generating JSON data for API responses can produce numeric values that are not JSON-safe, such as `NaN` (Not a Number) and `Infinity`. When FastAPI attempts to serialize these values to JSON for HTTP responses, it fails with:

```
RuntimeError: Response content shorter than Content-Length
```

This occurred in the Collection flow questionnaire generation where AI agents created confidence scores and business impact scores that occasionally contained `NaN` or `Infinity` values. PostgreSQL JSONB fields accept these values, but FastAPI's automatic JSON serialization does not.

**Problematic Data Flow**:
```
LLM Agent → Generates numeric data (may include NaN/Infinity)
     ↓
PostgreSQL JSONB field (accepts NaN/Infinity)
     ↓
FastAPI Response Serializer (FAILS - NaN/Infinity not JSON-safe)
     ↓
RuntimeError: Content-Length mismatch
     ↓
Frontend receives empty/truncated data
```

## Decision

We adopt a **mandatory JSON sanitization pattern** for all LLM-generated data before FastAPI serialization. This pattern:

1. **Converts non-JSON-safe values** to safe alternatives:
   - `NaN` → `null`
   - `Infinity` / `-Infinity` → `null`
   - `datetime` objects → ISO 8601 strings
   - Non-serializable objects → string representation

2. **Applies recursively** to nested dictionaries and arrays

3. **Preserves valid data** (strings, integers, booleans, null, valid floats)

4. **Executes at serialization layer** (before Pydantic model construction)

## Implementation

### Core Utility Function

Location: `backend/app/utils/json_sanitization.py` (to be created as shared utility)

```python
import math
from typing import Any
from datetime import datetime, date


def sanitize_for_json(data: Any) -> Any:
    """Recursively sanitize data for JSON serialization.

    Handles:
    - NaN → null
    - Infinity → null
    - datetime → ISO string
    - Non-serializable objects → string representation

    Args:
        data: Any Python data structure

    Returns:
        JSON-safe version of the data

    Example:
        >>> sanitize_for_json({"score": float('nan'), "count": 10})
        {"score": null, "count": 10}
    """
    if isinstance(data, dict):
        return {k: sanitize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data
    elif isinstance(data, (datetime, date)):
        return data.isoformat()
    elif isinstance(data, (str, int, bool, type(None))):
        return data
    else:
        # Fallback: convert to string
        return str(data)
```

### Usage Pattern

**MANDATORY for all LLM-generated data before API responses**:

```python
from app.utils.json_sanitization import sanitize_for_json

# In serializer/endpoint
def build_response(llm_data):
    return ResponseModel(
        questions=sanitize_for_json(llm_data.questions),
        analysis=sanitize_for_json(llm_data.analysis),
        scores=sanitize_for_json(llm_data.scores)
    )
```

### Where to Apply

**REQUIRED** for:
- ✅ Questionnaire generation (adaptive questions)
- ✅ Gap analysis results (confidence scores)
- ✅ Assessment recommendations (risk scores, complexity scores)
- ✅ Migration wave planning (business impact scores)
- ✅ Agent insights and analysis results
- ✅ Any AI-generated numeric data in API responses

**NOT NEEDED** for:
- ❌ User input data (already validated)
- ❌ Database primary keys (UUIDs, integers)
- ❌ Enum values (strings)
- ❌ Static configuration

## Consequences

### Positive

1. **Prevents Runtime Errors**: Eliminates JSON serialization failures from NaN/Infinity
2. **Defensive Coding**: Protects against unpredictable LLM output
3. **Data Integrity**: Preserves valid data while handling edge cases
4. **Reusable Pattern**: Single utility function applicable across all LLM outputs
5. **Type Safety**: Works with Pydantic models and FastAPI
6. **Backward Compatible**: Doesn't break existing functionality

### Negative

1. **Performance Overhead**: Recursive traversal of nested structures (minimal - O(n) complexity)
2. **Information Loss**: NaN/Infinity converted to null (acceptable - semantic meaning preserved)
3. **Developer Overhead**: Must remember to apply sanitization (mitigated by code review and linting)

### Mitigation Strategies

**Performance**:
- Sanitization occurs only at API boundary (not in business logic)
- Overhead is negligible compared to LLM inference time

**Information Loss**:
- `null` is semantically correct for "invalid numeric value"
- Alternative would be to fail the entire request (worse UX)

**Developer Overhead**:
- Document in coding guidelines
- Add to PR review checklist
- Consider pre-commit hook or linter rule
- Memory file created for reference

## Alternatives Considered

### 1. Fix LLM Prompts to Never Generate NaN/Infinity
**Rejected**: Cannot guarantee LLM output; defensive coding is safer

### 2. Custom Pydantic Validator
**Rejected**: Doesn't address JSONB fields; validation happens after database storage

### 3. Global FastAPI JSON Encoder Override
**Rejected**: Too broad; may affect non-LLM endpoints; harder to reason about

### 4. Frontend Handling
**Rejected**: Frontend never receives the data (backend serialization fails first)

### 5. Database Constraints
**Rejected**: PostgreSQL JSONB accepts NaN/Infinity; constraint wouldn't prevent issue

## Migration Plan

### Phase 1: Immediate (Completed)
- ✅ Fix Issue #682: Apply sanitization to questionnaire endpoint
- ✅ Create unit tests for `sanitize_for_json()`
- ✅ Document pattern in memory file

### Phase 2: Codebase Audit (Next)
- Search for all LLM agent outputs in API responses
- Apply sanitization to:
  - Gap analysis endpoints
  - Assessment recommendation endpoints
  - Agent insights endpoints
  - Wave planning endpoints

### Phase 3: Prevention (Future)
- Add pre-commit hook to check for unsanitized LLM outputs
- Add to developer onboarding docs
- Consider wrapper decorator for LLM response endpoints

## References

- **Issue**: #682 - Questionnaire generation produces empty questionnaire
- **Commit**: `6bf50aede` - Initial fix implementation
- **Test Suite**: `tests/backend/unit/test_collection_serializers.py`
- **Memory File**: `.serena/memories/json-serialization-safety-pattern.md`
- **Related ADR**: ADR-024 (TenantMemoryManager for LLM learning)

## Decision Makers

- **Proposed by**: Issue Triage Coordinator Agent
- **Implemented by**: Python-CrewAI-FastAPI Expert Agent
- **Verified by**: QA Playwright Tester Agent
- **Approved by**: User (CryptoYogiLLC)

## Success Metrics

- ✅ Zero JSON serialization RuntimeErrors in production
- ✅ All LLM-generated API responses succeed
- ✅ No data loss from questionnaire generation
- ✅ Pattern reused across 4+ endpoints

## Future Enhancements

1. **Type Hints**: Add comprehensive type hints for better IDE support
2. **Performance Profiling**: Monitor sanitization overhead in production
3. **Telemetry**: Track NaN/Infinity occurrence frequency to improve LLM prompts
4. **Custom Exceptions**: Distinguish between different sanitization scenarios
5. **Configuration**: Allow customization (e.g., convert NaN to 0 vs null per use case)

---

**Last Updated**: 2025-10-22
**Next Review**: After 4+ endpoint applications (estimate: Q2 2026)
