# Bug Fixes Session Summary - November 25, 2025

## Branch Information
**Current Branch**: `bugfix/collection-flow-improvements-nov-2025`
**Base Branch**: `main` (after PR #1126 merge of feature/1109-intelligent-gap-detection)
**Previous Branch**: Changes were on `feature/1127-pnpm-migration` (abandoned - pnpm not being implemented)

## Session Context
Continuation of ADR-037 Intelligent Gap Detection implementation with bug fixes for the Collection Flow.

## Bugs Fixed This Session

### Bug #25: Frontend Polling & Navigation Issues (COMPLETED)
**Problem**:
1. Excessive frontend polling throwing errors frequently
2. Users unable to navigate away from collection page during questionnaire generation
3. Modal dialog blocking with `onOpenChange={() => {}}` and `hideCloseButton`

**Root Cause**:
- Modal was configured to prevent closing
- No error threshold to stop polling on persistent failures

**Files Modified**:
1. `src/components/collection/QuestionnaireGenerationModal.tsx`:
   - Added `onCancel` prop to interface
   - Changed `onOpenChange={() => {}}` to `onOpenChange={(open) => !open && handleCancel()}`
   - Removed `hideCloseButton` attribute
   - Added `handleCancel()` function with interval cleanup
   - Added "Cancel and Navigate Away" button during generating state
   - Added X icon import from lucide-react

2. `src/hooks/collection/adaptive-form/usePolling.ts`:
   - Added `consecutiveErrors` counter initialized to 0
   - Added `MAX_CONSECUTIVE_ERRORS = 5` constant
   - Reset counter on successful status fetch
   - Stop polling after 5 consecutive errors with rejection

### Bug #26: Invalid Escape Sequences in LLM JSON Parsing (COMPLETED)
**Problem**:
Backend error: `Invalid \X escape sequence '.': line 36 column 83 (char 1418)`
LLMs return JSON with invalid escape sequences that break parsers.

**Root Cause**:
LLMs generate invalid JSON escapes like `\X`, `\x`, `\.` that neither `json.loads()` nor `dirtyjson.loads()` can handle.

**File Modified**:
`backend/app/services/collection/gap_analysis/section_question_generator/generator.py`:
- Added `_sanitize_escape_sequences()` method
- Called sanitization AFTER markdown stripping, BEFORE JSON parsing
- Preserves valid escapes (`\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`, `\t`, `\u`)
- Escapes invalid backslashes by doubling them

**Solution Pattern**:
```python
def _sanitize_escape_sequences(self, text: str) -> str:
    def fix_invalid_escape(match: re.Match) -> str:
        char = match.group(1)
        if char in '"\\\/bfnrtu':
            return match.group(0)  # Valid escape
        return '\\\\' + char  # Invalid - double the backslash
    return re.sub(r'\\(.)', fix_invalid_escape, text)
```

## Previously Fixed Bugs (Merged in PR #1126)

### Bug #12-14: Cascading IntelligentGap Parameter Bugs
- Pydantic model field mismatches across multiple files
- Fixed by ensuring consistent field names: `field_name`, `confidence_score`

### Bug #15: LLM JSON Parsing with Literal Ellipsis
- LLMs return literal `...` in JSON arrays which breaks parsing
- Fixed with preprocessing to remove/handle ellipsis

### Bug #19: multi_model_service Parameter Bug
- Method doesn't accept `client_account_id`/`engagement_id` parameters
- Fixed by removing these parameters from call site

### Bug #21: DataAwarenessAgent Batch Processing
- Batch size issues causing incomplete data maps
- Fixed batch handling logic

### Bug #22: No TRUE Gaps Flow Completion
- Flows with no TRUE gaps getting stuck instead of completing
- Fixed phase transition logic

### Bug #23: IntelligentGap Attribute Names
- Using wrong attribute names (`field_display_name` vs `field_name`)
- Fixed in prompt_builder.py

### Bug #24: multi_model_service Response Key
- Service returns `response` not `content` key
- Fixed: `response_data.get("response") or response_data.get("content", "{}")`

## Key Learnings

### Docker Container Management
- **Code changes only** → Use `docker-compose restart backend` (NOT rebuild)
- **Dependency changes** → Use `docker-compose up -d --build backend`
- Rebuilding for code-only changes wastes time

### LLM JSON Parsing Robustness
Order of operations for parsing LLM responses:
1. Strip markdown code blocks (````json ... ```)
2. Sanitize invalid escape sequences (Bug #26)
3. Try `json.loads()` first
4. Fallback to `dirtyjson.loads()` for malformed JSON
5. Sanitize NaN/Infinity values (ADR-029)

### Frontend Polling Best Practices
- Always add error threshold to stop endless polling
- Allow users to cancel/navigate away from long operations
- Reset error counters on successful operations

## Files Changed This Session (Uncommitted)
1. `src/components/collection/QuestionnaireGenerationModal.tsx`
2. `src/hooks/collection/adaptive-form/usePolling.ts`
3. `backend/app/services/collection/gap_analysis/section_question_generator/generator.py`
4. Multiple other backend files with improvements

## Deployment Status
Changes are UNCOMMITTED on `bugfix/collection-flow-improvements-nov-2025` branch.
Need to commit and create PR for these fixes.
