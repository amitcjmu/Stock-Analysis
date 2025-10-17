# Session Prompts Guide

## Which Prompt Should I Use?

### For Starting Fresh E2E Testing
👉 **Use**: `NEXT_SESSION_PROMPT.md`
- **When**: You want to start E2E testing from scratch
- **Content**: Original comprehensive E2E testing plan
- **Status**: Covers all phases and initial setup

### For Completing Issue #2 Fix (Current Task)
👉 **Use**: `CONTINUE_ISSUE_2_FIX.md`
- **When**: You're continuing the Issue #2 fix (final 10% - migration only)
- **Content**: Complete migration template and commit instructions
- **Status**: 90% done, just need to create migration 095 and commit
- **Branch**: Commits to `feature/assessment-architecture-enrichment-pipeline` (no separate PR)
- **References**: Points to `NEXT_SESSION_PROMPT.md` for full context

## File Summary

| File | Purpose | Status | Size |
|------|---------|--------|------|
| `NEXT_SESSION_PROMPT.md` | Original E2E testing plan | Reference | 9.4K |
| `CONTINUE_ISSUE_2_FIX.md` | Complete Issue #2 migration | **START HERE** | 21K |
| `E2E_TESTING_ISSUES_TRACKER.md` | Issues found during testing | Live Document | Updated |
| `CANONICAL_APP_IMPLEMENTATION_SUMMARY.md` | Feature background | Reference | Complete |

## Quick Start for Next Agent

```bash
# 1. Read continuation prompt
cat /Users/chocka/CursorProjects/migrate-ui-orchestrator/docs/planning/CONTINUE_ISSUE_2_FIX.md

# 2. Create migration (template provided in file)
# Copy template to: backend/alembic/versions/095_update_application_architecture_overrides_schema.py

# 3. Run migration
cd backend && alembic upgrade head

# 4. Test and verify
# (Commands in CONTINUE_ISSUE_2_FIX.md)

# 5. Create PR
# (Full instructions in CONTINUE_ISSUE_2_FIX.md)
```

## Context Preserved

- ✅ Original prompt: `NEXT_SESSION_PROMPT.md` (unchanged)
- ✅ Continuation: `CONTINUE_ISSUE_2_FIX.md` (references original)
- ✅ Work completed: Frontend fix, backend repository fix
- ✅ Work remaining: Migration 095, update tracker, commit to feature branch
- ✅ Estimated time: 15-20 minutes

## PR Strategy

**IMPORTANT**: Issue #2 fixes are E2E testing fixes for the canonical application feature. They should be:
- ✅ Committed to current feature branch: `feature/assessment-architecture-enrichment-pipeline`
- ✅ Included in the main feature PR (not a separate PR)
- ✅ Part of the overall canonical application assessment flow implementation

This keeps all related work in one cohesive feature PR.

---

**Recommendation**: Start with `CONTINUE_ISSUE_2_FIX.md` - it has everything you need including the complete migration template!
