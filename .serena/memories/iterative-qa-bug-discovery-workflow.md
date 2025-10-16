# Iterative QA Bug Discovery Workflow

**Problem**: Manual testing catches surface issues but misses deeper bugs. Single-pass QA gives false confidence.

**Solution**: Multi-cycle QA testing where each cycle reveals progressively deeper issues.

## Workflow Pattern

```bash
# Cycle 1: Initial comprehensive testing
# - QA agent tests all UI flows
# - Captures browser console + backend logs
# Result: Finds 4 surface errors (P0, P1, P2)

# Cycle 2: Re-test after fixes
# - Previous bugs fixed
# - QA discovers fix was incomplete
# Result: Finds field mapping issue (P0 follow-up)

# Cycle 3: Final verification
# - All code fixes in place
# - QA discovers database schema mismatch
# Result: Finds missing columns (P0+ blocker)
```

## Real Example from PR #587

**Cycle 1 Findings**:
- P0: Pydantic validation error (list vs dict)
- P1: Missing TableCell import
- P2: forEach on non-array

**Cycle 2 Finding**:
- P0 follow-up: Field mapping `mandatory` → `is_mandatory` missing

**Cycle 3 Finding**:
- P0+ blocker: Database missing `supported_versions` column

## Key Insight

**Each fix reveals the next layer of problems**. Without iterative testing, Cycle 2 and 3 issues would have shipped to production.

## Implementation

```bash
# User's request
"Rather than manual testing, use playwright QA agent to test every
screen and link, capturing all errors. Then fix issues and re-test.
Iterate until all issues resolved."
```

## Why This Matters

- Surface fixes can mask deeper problems
- Comprehensive testing ≠ single-pass testing
- Production confidence requires iteration
- 3 cycles found 3 progressively deeper bugs

**Result**: Zero bugs missed, all architectural layers validated.
