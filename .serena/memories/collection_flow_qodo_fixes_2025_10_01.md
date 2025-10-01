# Session Learnings: Collection Flow Questionnaire Generation Fixes (2025-10-01)

## Insight 1: Foreign Key Constraint - Use Primary Key, Not Business UUID

**Problem**: FK constraint violations when using `flow.flow_id` (business UUID) instead of `flow.id` (database PK)

**Solution**: Always use the table's primary key (`id`) for foreign key references, not business identifier fields

**Code**:
```python
# ❌ WRONG - Uses business UUID
collection_flow_app = CollectionFlowApplication(
    collection_flow_id=collection_flow.flow_id,  # FK violation!
    asset_id=asset_id,
)

# ✅ CORRECT - Uses primary key
collection_flow_app = CollectionFlowApplication(
    collection_flow_id=collection_flow.id,  # PK for FK constraint
    asset_id=asset_id,
)
```

**Database Proof**:
```sql
-- FK constraint definition:
FOREIGN KEY (collection_flow_id) REFERENCES collection_flows(id)
-- NOT: REFERENCES collection_flows(flow_id)

-- Actual values are different:
SELECT id, flow_id FROM collection_flows WHERE flow_id = '<uuid>';
-- id:      46aed088-e188-41b0-9988-bd545c812170  (PK)
-- flow_id: 14c26790-54dd-4f44-b39e-5332f845d482  (Business UUID)
```

**Usage**: When creating records with FKs, always inspect schema constraints to verify which field is the PK target

---

## Insight 2: CrewAI Tool Validation - Match _run() Signature to args_schema

**Problem**: `ValidationError: Required function parameter 'X' not found in args_schema` when tool method signature doesn't match Pydantic schema

**Solution**: CrewAI validates that ALL parameters in `_run()` must be defined in `args_schema` BaseModel

**Code**:
```python
# ❌ WRONG - Signature mismatch
class QuestionnaireGenerationInput(BaseModel):
    data_gaps: Dict[str, Any] = Field(...)
    business_context: Dict[str, Any] = Field(...)

class QuestionnaireGenerationTool(BaseTool):
    args_schema: type[BaseModel] = QuestionnaireGenerationInput

    def _run(self, asset_analysis: Dict, gap_type: str, asset_context: Dict):
        # ERROR: asset_analysis, gap_type, asset_context not in schema!
        pass

# ✅ CORRECT - Signature matches schema
class QuestionnaireGenerationTool(BaseTool):
    args_schema: type[BaseModel] = QuestionnaireGenerationInput

    def _run(self, data_gaps: Dict[str, Any], business_context: Dict[str, Any] = None):
        return asyncio.run(self._arun(data_gaps, business_context or {}))
```

**Usage**: When CrewAI tools fail with ValidationError, compare `_run()` parameters with `args_schema` fields - they MUST match exactly

---

## Insight 3: Pre-commit File Length Enforcement - Modularize Before Commit

**Problem**: Commit blocked by pre-commit hook: "FILE LENGTH VIOLATIONS: file.py: 623 lines (exceeds 400 line limit)"

**Solution**: Split large files into focused modules using extraction pattern

**Code**:
```python
# BEFORE: generation.py (623 lines) - BLOCKED
class QuestionnaireGenerationTool(BaseTool):
    def _run(self): ...
    def _create_sections(self): ...
    def _build_questions(self): ...
    def _determine_field_type(self): ...
    # ... 600+ more lines

# AFTER: Modularized (all <400 lines) - PASSES
# generation.py (331 lines) - Main class with thin wrappers
from .section_builders import create_basic_info_section, create_category_sections
from .question_builders import generate_missing_field_question, generate_fallback_question

class QuestionnaireGenerationTool(BaseTool):
    def _run(self): return asyncio.run(self._arun(...))
    def _create_basic_info_section(self): return create_basic_info_section()
    def _generate_missing_field_question(self, ...): return generate_missing_field_question(...)

# section_builders.py (202 lines) - Section logic
def create_basic_info_section() -> dict: ...
def create_category_sections(attrs: dict) -> list: ...

# question_builders.py (284 lines) - Question generation
def generate_missing_field_question(asset_analysis, asset_context): ...
def generate_fallback_question(gap_type, asset_context): ...
```

**Pattern**:
1. Extract pure functions (no `self` references)
2. Keep main class as thin orchestration layer
3. Group related functionality by purpose
4. Maintain backward compatibility via wrapper methods

**Usage**: When pre-commit fails on file length, extract helpers to separate modules. Target: 250-350 lines per file

---

## Insight 4: Database Flush for Early FK Integrity Detection

**Problem**: FK violations discovered only at transaction commit, after complex operations

**Solution**: Use `await db.flush()` after FK updates to catch integrity errors early

**Code**:
```python
# ❌ WRONG - FK violation discovered at commit (line 500+)
collection_flow_app = CollectionFlowApplication(
    collection_flow_id=collection_flow.id,
    asset_id=asset_id,
)
db.add(collection_flow_app)

asset.collection_flow_id = collection_flow.id
asset.updated_at = datetime.now(timezone.utc)
# No db.add(asset) - change not persisted!
# No flush - integrity check deferred

# ... 200 lines of other operations ...
await db.commit()  # FK VIOLATION HERE - hard to trace!

# ✅ CORRECT - FK violation caught immediately
collection_flow_app = CollectionFlowApplication(
    collection_flow_id=collection_flow.id,
    asset_id=asset_id,
)
db.add(collection_flow_app)

asset.collection_flow_id = collection_flow.id
asset.updated_at = datetime.now(timezone.utc)
db.add(asset)  # Explicitly persist modified object

await db.flush()  # FK VIOLATION HERE - easy to trace!

# ... continue with other operations ...
```

**Usage**: After creating/updating records with FK relationships, call `await db.flush()` to validate integrity before continuing

---

## Insight 5: HTTP 422 for Validation Errors, Not 400

**Problem**: Frontend error handling expects 422 for validation errors, not 400

**Solution**: Use HTTP 422 (Unprocessable Entity) with stable `code` field for client-side error matching

**Code**:
```python
# ❌ WRONG - Generic 400
raise HTTPException(
    status_code=400,
    detail={
        "error": "Invalid endpoint",
        "message": "Asset selection must use /applications endpoint"
    }
)

# ✅ CORRECT - 422 with stable code
raise HTTPException(
    status_code=422,  # Validation error status
    detail={
        "code": "invalid_asset_selection_endpoint",  # Stable for frontend
        "error": "Invalid endpoint for asset selection",
        "message": "Asset selection must use dedicated /applications endpoint",
        "correct_endpoint": f"/api/v1/collection/flows/{flow_id}/applications",
    }
)
```

**Frontend Usage**:
```typescript
// Frontend can match on stable code
if (error.response?.status === 422 &&
    error.response?.data?.code === "invalid_asset_selection_endpoint") {
  // Show specific UI guidance
}
```

**Usage**: Use 422 for validation/business logic errors, 400 for malformed requests. Always include stable `code` field.

---

## Insight 6: React State Updates - Reset Dependent State on Trigger Change

**Problem**: Retry mechanism shows incorrect UI after flow change because `retryCount` not reset

**Solution**: Reset all dependent state when trigger value changes in useEffect

**Code**:
```typescript
// ❌ WRONG - retryCount persists across flows
useEffect(() => {
  setPollAttempts(0);
  setIsPolling(false);
  setError(null);
  // Missing: setRetryCount(0)
}, [flowId]);

// Later: Wrong retry UI shown for new flow!
const canRetry = retryCount < MAX_RETRY_ATTEMPTS && ...

// ✅ CORRECT - All dependent state reset
useEffect(() => {
  console.log('Flow ID changed, resetting polling state:', flowId);
  setPollAttempts(0);
  setRetryCount(0);  // Reset retry state on flow change
  setIsPolling(false);
  setError(null);
  setCompletionStatus(null);
  setStatusLine(null);
}, [flowId]);
```

**Usage**: When resetting state on trigger change, identify ALL dependent state variables and reset them together

---

## Insight 7: Conditional Metadata Fields - Prevent Type Mismatches

**Problem**: Backend receives `asset_id` as array when expecting string, causing type errors

**Solution**: Conditionally include metadata fields with type guards

**Code**:
```typescript
// ❌ WRONG - asset_id might be array or wrong type
const assetId = data?.selected_assets || data?.asset_id || null;
const submissionData = {
  form_metadata: {
    asset_id: assetId,  // Could be array! Type mismatch!
  }
};

// ✅ CORRECT - Type-safe conditional inclusion
let assetId: string | null = null;
if (questionnaireId !== "bootstrap_asset_selection" &&
    typeof data?.asset_id === "string") {
  assetId = data.asset_id;
}

const submissionData = {
  form_metadata: {
    ...(assetId ? { asset_id: assetId } : {}),  // Only include if valid string
  }
};
```

**Usage**: For optional metadata fields with type requirements, use type guards + conditional spread to prevent mismatches

---

## Insight 8: Exception Context Preservation for Debugging

**Problem**: Error logs show exception type but lose stack trace and causal chain

**Solution**: Use `exc_info=True` and `raise ... from` to preserve debugging context

**Code**:
```python
# ❌ WRONG - Loses stack trace
except Exception as generation_error:
    logger.error(f"Error: {type(generation_error).__name__}")
    raise CollectionFlowError(f"Generation failed: {type(generation_error).__name__}")

# ✅ CORRECT - Preserves full context
except Exception as generation_error:
    logger.error(
        f"Error: {type(generation_error).__name__}",
        exc_info=True,  # Include full stack trace
    )
    raise CollectionFlowError(
        f"Generation failed: {type(generation_error).__name__}: {str(generation_error)}"
    ) from generation_error  # Preserve exception chain
```

**Usage**: Always use `exc_info=True` in error logs and `raise ... from` to maintain exception causality for debugging

---

## PR Summary

**Commits**:
- 4878e1e2e: Collection Flow questionnaire generation with correct FK usage and UI fixes
- 1320ec873: Apply Qodo Bot PR feedback - 8 critical and high priority fixes

**Key Changes**:
- 53 files modified (+6,582/-1,493 lines)
- Fixed FK constraints, tool validation, UI navigation
- Modularized files for pre-commit compliance
- Strengthened database integrity checks
- Enhanced error handling and type safety

**PR**: #440 merged to main (27c9e395d)
