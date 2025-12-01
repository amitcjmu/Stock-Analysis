# LLM Tracking Implementation - Key Learnings (2025-10-02)

## Insight 1: Dual LLM Tracking Architecture Pattern

**Problem**: Application uses two different LLM calling patterns - CrewAI agents (internal LiteLLM) and direct OpenAI client calls (Gemma 3). A single tracking mechanism won't capture both.

**Solution**: Implement complementary tracking mechanisms:

1. **LiteLLM Callback** (Automatic) - Captures CrewAI/Llama 4
```python
# app/services/litellm_tracking_callback.py
class LLMUsageCallback(CustomLogger):
    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        model = kwargs.get("model", "unknown")
        usage = getattr(response_obj, "usage", None)

        asyncio.create_task(self._log_usage(
            provider="deepinfra",
            model=model,
            input_tokens=getattr(usage, "prompt_tokens", 0),
            output_tokens=getattr(usage, "completion_tokens", 0),
            response_time_ms=int((end_time - start_time) * 1000),
            success=True,
        ))

# Install at app startup
setup_litellm_tracking()  # Sets litellm.callbacks = [LLMUsageCallback()]
```

2. **Manual Context Manager** - Captures Direct OpenAI Client
```python
# app/services/multi_model_service.py
async with self.llm_usage_tracker.track_llm_call(
    provider="deepinfra",
    model=model_config["model_name"],
    feature_context=task_type,
) as usage_log:
    completion = self.openai_client.chat.completions.create(...)
    usage_log.input_tokens = completion.usage.prompt_tokens
    usage_log.output_tokens = completion.usage.completion_tokens
```

**Key Insight**: LiteLLM callbacks ONLY hook `litellm.completion()` calls. Direct `openai.chat.completions.create()` calls are invisible to the callback.

**When to Use**: Anytime you have multiple LLM integration patterns (CrewAI + direct API, LangChain + custom, etc.)

---

## Insight 2: Migration Fail-Fast Pattern

**Problem**: Broad exception handling in migrations can mask critical database errors, leading to silent failures and incorrect migration state.

**Anti-Pattern**:
```python
def column_exists(table_name, column_name, schema="migration"):
    try:
        result = bind.execute(stmt, params).scalar()
        return bool(result)
    except Exception:
        return False  # ❌ Hides DB connection errors, permission issues, etc.
```

**Correct Pattern**:
```python
def column_exists(table_name, column_name, schema="migration"):
    """Check if column exists. Exceptions propagate to fail migration loudly."""
    result = bind.execute(stmt, params).scalar()
    return bool(result)  # ✅ Database errors cause migration to fail
```

**Rationale**: Migrations should fail fast and loudly on unexpected errors. Better to abort migration than proceed with incorrect state.

**Applied in**: `alembic/versions/078_add_updated_at_to_name_variants.py`

---

## Insight 3: Non-Blocking Pre-commit Hooks for Operational Checks

**Problem**: LLM tracking enforcement is an operational concern (cost visibility), not a code quality requirement. Blocking commits would frustrate developers for non-critical issues.

**Solution**: Use exit code 0 with clear warning messaging:

```python
# scripts/check_llm_calls.py
"""
IMPORTANT: This is a WARNING-ONLY check (exit code 0) - does NOT block commits.
LLM tracking is an operational concern, not a code quality requirement.
"""

if violations_found:
    print("⚠️  DIRECT LLM CALLS DETECTED (WARNING ONLY)")
    print("NOTE: This is a warning only - commit will NOT be blocked.")
    for file, violations in violations.items():
        print(f"\n  {file}:")
        for line_num, pattern in violations:
            print(f"    Line {line_num}: {pattern}")

    return 0  # ✅ Don't block commits - just warn
```

**When to Use**:
- Cost tracking/monitoring
- Deprecated API warnings
- Soft architectural guidelines
- Performance suggestions

**When NOT to Use**:
- Security vulnerabilities (should block)
- Breaking changes (should block)
- Code quality issues (should block)

---

## Insight 4: Python Constant Scope Bug Pattern

**Problem**: Constants defined at end of file but used earlier cause `NameError`.

**Bug Pattern**:
```python
# Line 220
if LLM_TRACKING_AVAILABLE:  # ❌ NameError - not defined yet
    ...

# Line 584
LLM_TRACKING_AVAILABLE = True  # Defined too late
```

**Fix**:
```python
# Line 15-17 (after imports)
from app.services.llm_usage_tracker import llm_tracker
LLM_TRACKING_AVAILABLE = True  # ✅ Define before usage

# Line 220
if LLM_TRACKING_AVAILABLE:  # Now works
    ...
```

**Best Practice**: Define all module-level constants immediately after imports, before any function/class definitions.

---

## Insight 5: Qodo Bot Review Response Pattern

**Problem**: Code review bots may suggest changes based on incomplete understanding of architecture.

**Solution**: Provide detailed technical justification with diagrams:

```markdown
## Response to "Remove Redundant Tracking"

Cannot implement - suggestion based on incorrect assumption:

### Why Both Mechanisms Are Required

#### Pattern 1: LiteLLM Callback (Automatic)
- **Captures**: CrewAI → litellm.completion() → DeepInfra (Llama 4)
- **Verification**: ✅ 328 tokens, $0.000181 logged

#### Pattern 2: Manual Tracking (Required)
- **Captures**: MultiModelService → OpenAI Client → DeepInfra (Gemma 3)
- **Why callback doesn't work**: `self.openai_client.chat.completions.create()`
  does NOT go through litellm, so callback never sees it
```

**Key**: Show code paths, verification results, and explain WHY the architecture exists.

---

## Files Modified in This Session

### New Files
- `app/services/litellm_tracking_callback.py` - LiteLLM callback for automatic tracking
- `alembic/versions/079_create_llm_usage_logs.py` - Database schema for LLM tracking
- `scripts/check_llm_calls.py` - Pre-commit hook (warning-only)
- `scripts/README_LLM_TRACKING.md` - Developer guide
- `QODO_REVIEW_RESPONSE.md` - Code review justifications

### Modified Files
- `app/services/multi_model_service.py` - Fixed LLM_TRACKING_AVAILABLE scope bug
- `app/api/v1/finops/finops_router.py` - Real model names from database
- `alembic/versions/078_add_updated_at_to_name_variants.py` - Removed broad exception
- `app/api/v1/api_tags.py` - Added ADMIN_LLM_USAGE canonical tag
- `CLAUDE.md` - Documented LLM tracking policy

---

## Testing Verification

**Llama 4 (CrewAI)**:
- ✅ Logged via LiteLLM callback
- ✅ 328 tokens, $0.000181 cost
- ✅ Display: "Deepinfra: Llama-4-Maverick-17B-128E-Instruct-FP8"

**Gemma 3 (Chat)**:
- ✅ Logged via manual tracking
- ✅ Context manager captures tokens/cost
- ✅ Display: Real model name from database

**Pre-commit**:
- ✅ Exit code 0 (non-blocking)
- ✅ Clear warning messages
- ✅ Detects direct LLM calls

---

## Key Takeaways for Future Development

1. **Always check LLM calling patterns** - Don't assume one tracking mechanism covers all use cases
2. **Let migrations fail** - Remove broad exception handling in schema changes
3. **Distinguish operational vs quality checks** - Use appropriate pre-commit exit codes
4. **Define constants early** - Module-level constants go right after imports
5. **Document architectural decisions** - Code reviews benefit from detailed technical explanations

## Related Documentation

- CLAUDE.md - LLM usage tracking policy (lines 96-156)
- backend/QODO_REVIEW_RESPONSE.md - Detailed code review responses
- scripts/README_LLM_TRACKING.md - Developer usage guide
